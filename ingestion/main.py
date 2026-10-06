# Entry point for the ingestion pipeline. Run from the project root:
#   python -m ingestion.main           poll every POLL_INTERVAL_SECONDS until Ctrl+C
#   python -m ingestion.main --once    run a single round, then exit
import argparse
import logging
import time

import psycopg

from ingestion.config import ConfigError, Settings, load_settings
from ingestion.fetcher import FetchError, fetch_feed
from ingestion.parser import ParseError, parse_feed
from ingestion.repository import save_snapshot

logger = logging.getLogger(__name__)

# TransLink regenerates the feed every 30 s; polling twice as often means no version is missed
POLL_INTERVAL_SECONDS = 15


def run_once(conn: psycopg.Connection, settings: Settings) -> bool:
    """One round of fetch -> parse -> save. Returns True if a new snapshot was saved."""
    raw = fetch_feed(settings)
    snapshot = parse_feed(raw)
    return save_snapshot(conn, snapshot)


def run_forever(settings: Settings, once: bool = False) -> None:
    conn: psycopg.Connection | None = None
    try:
        while True:
            started = time.monotonic()

            try:
                if conn is None or conn.closed:
                    conn = psycopg.connect(settings.database_url)
                    logger.info("Connected to database")
                run_once(conn, settings)
            except (FetchError, ParseError) as exc:
                # Expected, temporary problems: skip this round, try again next time
                logger.error("Skipping this round: %s", exc)
            except psycopg.Error as exc:
                # Database problem: drop the connection so the next round reconnects
                logger.error(
                    "Database error (%s): %s", type(exc).__name__, str(exc).splitlines()[0]
                )
                if conn is not None:
                    conn.close()
                conn = None
            except Exception:
                logger.exception("Unexpected error in this round")

            if once:
                return

            # Sleep for the rest of the interval, so rounds start on schedule
            elapsed = time.monotonic() - started
            time.sleep(max(0.0, POLL_INTERVAL_SECONDS - elapsed))
    finally:
        if conn is not None:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect TransLink GTFS-Realtime snapshots.")
    parser.add_argument("--once", action="store_true", help="run a single round, then exit")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(1) from None

    logger.info(
        "Starting pipeline (every %d s)%s",
        POLL_INTERVAL_SECONDS,
        " [--once]" if args.once else "",
    )
    try:
        run_forever(settings, once=args.once)
    except KeyboardInterrupt:
        logger.info("Stopped by user")


if __name__ == "__main__":
    main()
