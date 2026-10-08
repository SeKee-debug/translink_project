# Loads TransLink's GTFS static files into the static schema. Run from the project root:
#   python -m ingestion.load_static data/gtfs_static/2026-10-06
#
# All three tables are replaced in one transaction: either every file loads, or nothing changes.
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import psycopg

from ingestion.config import ConfigError, load_settings

logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

# Order matters: routes before trips, because of the trips.route_id foreign key
FILES = [
    ("routes", "routes.txt"),
    ("stops", "stops.txt"),
    ("trips", "trips.txt"),
]


def read_header(path: Path) -> list[str]:
    # utf-8-sig strips a byte-order mark if there is one, so the first column
    # isn't silently named "\ufeffroute_id"
    with open(path, encoding="utf-8-sig") as f:
        return f.readline().strip().split(",")


def copy_file(cur: psycopg.Cursor, table: str, path: Path) -> int:
    """COPY one CSV file into static.<table>. Returns the number of rows loaded."""
    # COPY matches by position, so name the columns from the file's own header. If TransLink
    # adds a column the table doesn't have, this fails loudly instead of shifting data.
    # Table and column names come from this code and TransLink's header, never user input.
    cols = ", ".join(read_header(path))
    with cur.copy(f"COPY static.{table} ({cols}) FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                copy.write(chunk)
    return cur.rowcount


def load_static(conn: psycopg.Connection, folder: Path) -> None:
    for _, filename in FILES:
        if not (folder / filename).is_file():
            raise FileNotFoundError(f"{folder / filename} not found")

    try:
        with conn.cursor() as cur:
            # One statement for all three, so the foreign key doesn't block emptying routes
            cur.execute("TRUNCATE static.trips, static.routes, static.stops")
            for table, filename in FILES:
                rows = copy_file(cur, table, folder / filename)
                logger.info("Loaded %d rows into static.%s from %s", rows, table, filename)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Load GTFS static files into the static schema.")
    parser.add_argument("folder", type=Path, help="folder containing routes.txt, stops.txt, trips.txt")
    args = parser.parse_args()

    LOG_DIR.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_DIR / "load_static.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
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

    logger.info("Loading GTFS static files from %s", args.folder)
    with psycopg.connect(settings.database_url) as conn:
        load_static(conn, args.folder)
    logger.info("Done: static schema replaced in one transaction")


if __name__ == "__main__":
    main()
