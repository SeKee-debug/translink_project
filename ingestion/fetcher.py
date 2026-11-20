import logging
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from ingestion.config import Settings
from ingestion.models import RawFetch

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Raised when a fetch fails. The message should never include the API key."""


def _redact(text: str, secret: str) -> str:
    # requests puts the whole URL in its error messages, and the URL has the key in it.
    # The key can show up as-is or URL-encoded, so this blanks out both.
    return text.replace(secret, "***").replace(quote(secret, safe=""), "***")


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
        # Keep the actual reason (DNS failure, refused connection, timeout, etc.) so I can tell
        # from the log why a day failed. Just with the key taken out.
        detail = _redact(str(exc), settings.translink_api_key)
        raise FetchError(f"Request to TransLink failed: {type(exc).__name__}: {detail}") from None

    logger.info("Fetched feed: %d bytes, HTTP %d", len(resp.content), resp.status_code)
    return RawFetch(content=resp.content, fetched_at=fetched_at)
