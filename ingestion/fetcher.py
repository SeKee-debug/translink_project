import logging
from datetime import datetime, timezone

import requests

from ingestion.config import Settings
from ingestion.models import RawFetch

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """A failed fetch. The message never contains the URL, because the URL contains the API key."""


def fetch_feed(settings: Settings) -> RawFetch:
    try:
        resp = requests.get(
            settings.feed_url,
            params={"apikey": settings.translink_api_key},
            headers={"User-Agent": settings.user_agent},
            timeout=settings.http_timeout_seconds,
        )
        fetched_at = datetime.now(timezone.utc)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise FetchError(f"TransLink returned HTTP {exc.response.status_code}") from None
    except requests.RequestException as exc:
        raise FetchError(f"Request to TransLink failed: {type(exc).__name__}") from None

    logger.info("Fetched feed: %d bytes, HTTP %d", len(resp.content), resp.status_code)
    return RawFetch(content=resp.content, fetched_at=fetched_at)
