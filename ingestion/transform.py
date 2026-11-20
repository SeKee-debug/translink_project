# Takes the raw snapshots and applies them to analytics.stop_arrivals, one batch at a time, oldest
# first. Run it from the project folder:
#   python -m ingestion.transform                                  processes everything that's left
#   python -m ingestion.transform --batch-size 5 --max-batches 1   one small batch, for testing
#
# Each batch is its own transaction. It picks the next unprocessed snapshots, upserts their stops,
# and ticks them off in analytics.processed_snapshots. If it crashes or you hit Ctrl+C, only the
# current batch gets rolled back, so every snapshot gets applied exactly once.
import argparse
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg

from ingestion.config import ConfigError, load_settings

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_DIR / "logs"
LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
UPSERT_SQL = (PROJECT_DIR / "sql" / "transform" / "stop_arrivals_upsert.sql").read_text(encoding="utf-8")

# Anti-join that grabs the snapshots that aren't ticked off yet. They have to go oldest first,
# because the upsert only applies data that's newer than what's already stored.
NEXT_BATCH_SQL = """
    SELECT s.snapshot_id
    FROM raw.feed_snapshots s
    LEFT JOIN analytics.processed_snapshots p USING (snapshot_id)
    WHERE p.snapshot_id IS NULL
    ORDER BY s.feed_timestamp
    LIMIT %(batch_size)s
"""

MARK_PROCESSED_SQL = """
    INSERT INTO analytics.processed_snapshots (snapshot_id)
    SELECT unnest(%(snapshot_ids)s::bigint[])
"""


def process_batch(conn: psycopg.Connection, batch_size: int) -> tuple[list[int], int] | None:
    """Runs the next batch in one transaction. Returns (snapshot ids, rows written), or None when there's nothing left."""
    with conn.transaction():
        with conn.cursor() as cur:
            ids = [row[0] for row in cur.execute(NEXT_BATCH_SQL, {"batch_size": batch_size})]
            if not ids:
                return None
            cur.execute(UPSERT_SQL, {"snapshot_ids": ids})
            # This counts inserted and updated rows. Keys skipped by the "only if newer" check don't count.
            rows_written = cur.rowcount
            cur.execute(MARK_PROCESSED_SQL, {"snapshot_ids": ids})
    return ids, rows_written


def run(conn: psycopg.Connection, batch_size: int, max_batches: int | None) -> None:
    batches = snapshots = rows = 0
    started = time.monotonic()
    try:
        while max_batches is None or batches < max_batches:
            batch_started = time.monotonic()
            result = process_batch(conn, batch_size)
            if result is None:
                logger.info("Nothing left to process")
                break
            ids, written = result
            batches += 1
            snapshots += len(ids)
            rows += written
            logger.info(
                "Batch %d: snapshots %d-%d (%d), %s rows written, %.1f s",
                batches, min(ids), max(ids), len(ids), f"{written:,}", time.monotonic() - batch_started,
            )
    finally:
        # This still runs after Ctrl+C. The batches that already committed are saved either way.
        logger.info(
            "Summary: %d batches, %d snapshots, %s rows written, %.1f s total",
            batches, snapshots, f"{rows:,}", time.monotonic() - started,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply raw snapshots to analytics.stop_arrivals.")
    parser.add_argument("--batch-size", type=int, default=20, help="snapshots per transaction (default 20)")
    parser.add_argument("--max-batches", type=int, default=None, help="stop after this many batches (default: no limit)")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.max_batches is not None and args.max_batches < 1:
        parser.error("--max-batches must be at least 1")

    LOG_DIR.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_DIR / "transform.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(), file_handler],
    )

    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(1) from None

    logger.info(
        "Starting transform (batch size %d, %s)",
        args.batch_size,
        f"max {args.max_batches} batches" if args.max_batches else "until done",
    )
    # With autocommit on, each conn.transaction() block becomes its own BEGIN ... COMMIT
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        try:
            run(conn, args.batch_size, args.max_batches)
        except KeyboardInterrupt:
            logger.info("Stopped by user")


if __name__ == "__main__":
    main()
