# Temporary smoke test for step 3a. Run from the project root:
#   python -m ingestion.try_3a
import logging

from ingestion.config import ConfigError, load_settings
from ingestion.fetcher import fetch_feed
from ingestion.parser import parse_feed

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # The entry point, not config.py, decides that a bad config ends the program
    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(1) from None

    raw = fetch_feed(settings)
    snapshot = parse_feed(raw)

    logger.info("fetched_at:     %s", snapshot.fetched_at)
    logger.info("feed_timestamp: %s", snapshot.feed_timestamp)
    logger.info("lag:            %s", snapshot.fetched_at - snapshot.feed_timestamp)
    logger.info("payload_bytes:  %d", snapshot.payload_bytes)
    logger.info("entity_count:   %d", snapshot.entity_count)
    logger.info("header:         %s", snapshot.payload["header"])


if __name__ == "__main__":
    main()
