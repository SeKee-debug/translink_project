# Starts the collector. Run it from the project folder:
#   python -m ingestion.main           polls every POLL_INTERVAL_SECONDS during the collection window
#   python -m ingestion.main --once    does one round right now (ignores the window) and exits
import argparse
import logging
import time
from datetime import datetime
from datetime import time as dtime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg

from ingestion.budget import DailyBudget
from ingestion.config import ConfigError, Settings, load_settings
from ingestion.fetcher import FetchError, fetch_feed
from ingestion.parser import ParseError, parse_feed
from ingestion.repository import save_snapshot

logger = logging.getLogger(__name__)

# TransLink puts out a new version of the feed about every 15 s
POLL_INTERVAL_SECONDS = 15
# How often to check the clock again while we're outside the window
WINDOW_CHECK_SECONDS = 60
VANCOUVER = ZoneInfo("America/Vancouver")

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def in_window(now: dtime, start: dtime, end: dtime) -> bool:
    """The start counts as inside and the end doesn't, so 15:30:00 is in the window and 19:25:00 isn't."""
    return start <= now < end


def run_once(conn: psycopg.Connection, settings: Settings) -> bool:
    """Does one round of fetch, parse, save. Returns True if a new snapshot got saved."""
    raw = fetch_feed(settings)
    snapshot = parse_feed(raw)
    return save_snapshot(conn, snapshot)


def run_forever(settings: Settings, once: bool = False) -> None:
    conn: psycopg.Connection | None = None
    budget = DailyBudget(settings.daily_request_cap, VANCOUVER)
    was_in_window: bool | None = None
    try:
        while True:
            started = time.monotonic()

            # --once is just for testing by hand, so it runs right away no matter what time it is
            if not once:
                inside = in_window(
                    datetime.now(VANCOUVER).time(), settings.collect_start, settings.collect_end
                )
                # Only log when we go in or out of the window, not on every check
                if inside != was_in_window:
                    if inside:
                        logger.info(
                            "Entered collection window (%s-%s)",
                            settings.collect_start.strftime("%H:%M"),
                            settings.collect_end.strftime("%H:%M"),
                        )
                    else:
                        logger.info(
                            "Outside collection window, waiting until %s",
                            settings.collect_start.strftime("%H:%M"),
                        )
                        # Close the connection overnight. If the laptop sleeps, it dies without
                        # us knowing, and then the first insert the next day would fail.
                        if conn is not None:
                            conn.close()
                            conn = None
                            logger.info("Closed database connection until the next window")
                    was_in_window = inside
                if not inside:
                    time.sleep(WINDOW_CHECK_SECONDS)
                    continue

            try:
                if conn is None or conn.closed:
                    conn = psycopg.connect(settings.database_url)
                    logger.info("Connected to database")
                if once or budget.try_consume():
                    run_once(conn, settings)
            except (FetchError, ParseError) as exc:
                # These happen sometimes and are usually temporary, so skip this round and try again
                logger.error("Skipping this round: %s", exc)
            except psycopg.Error as exc:
                # Something went wrong with the database. Throw the connection away so the next round makes a new one
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

            # Sleep for whatever's left of the interval so each round starts on time
            elapsed = time.monotonic() - started
            time.sleep(max(0.0, POLL_INTERVAL_SECONDS - elapsed))
    finally:
        if conn is not None:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect TransLink GTFS-Realtime snapshots.")
    parser.add_argument("--once", action="store_true", help="run a single round now, then exit")
    args = parser.parse_args()

    # Every log line goes to the terminal and to logs/ingestion.log.
    # The file rotates at 5 MB and keeps 5 old copies, so it never takes up more than 30 MB.
    LOG_DIR.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_DIR / "ingestion.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
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
        "Starting pipeline (every %d s, window %s-%s Vancouver, cap %d/day)%s",
        POLL_INTERVAL_SECONDS,
        settings.collect_start.strftime("%H:%M"),
        settings.collect_end.strftime("%H:%M"),
        settings.daily_request_cap,
        " [--once]" if args.once else "",
    )
    try:
        run_forever(settings, once=args.once)
    except KeyboardInterrupt:
        logger.info("Stopped by user")


if __name__ == "__main__":
    main()
