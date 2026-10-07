import os
from dataclasses import dataclass
from datetime import time

from dotenv import load_dotenv

DEFAULT_FEED_URL = "https://gtfsapi.translink.ca/v3/gtfsrealtime"
DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0
USER_AGENT_BASE = "translink-delay-pipeline/0.1"

# Evening rush, America/Vancouver time. 3 h 55 min at one poll per 15 s = 940 requests,
# under the cap of 950, which is under TransLink's limit of 1,000 requests per day.
DEFAULT_COLLECT_START = "15:30"
DEFAULT_COLLECT_END = "19:25"
DEFAULT_DAILY_REQUEST_CAP = 950


class ConfigError(Exception):
    """A required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    translink_api_key: str
    feed_url: str
    http_timeout_seconds: float
    user_agent: str
    database_url : str
    collect_start: time
    collect_end: time
    daily_request_cap: int

    def __repr__(self) -> str:
        return (
            f"Settings(translink_api_key='***', feed_url={self.feed_url!r}, "
            f"http_timeout_seconds={self.http_timeout_seconds}, "
            f"user_agent = {self.user_agent}, "
            f"database_url='***', "
            f"collect_start={self.collect_start}, collect_end={self.collect_end}, "
            f"daily_request_cap={self.daily_request_cap})"
        )


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.environ.get("TRANSLINK_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "TRANSLINK_API_KEY is not set. Add it to the .env file in the project root."
        )

    feed_url = os.environ.get("FEED_URL", DEFAULT_FEED_URL).strip()

    raw_timeout = os.environ.get("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS))
    try:
        timeout = float(raw_timeout)
    except ValueError:
        raise ConfigError(f"HTTP_TIMEOUT_SECONDS must be a number, got {raw_timeout!r}") from None


    contact = os.environ.get("CONTACT_EMAIL", "").strip()
    user_agent = f"{USER_AGENT_BASE} ({contact})" if contact else USER_AGENT_BASE
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise ConfigError(
            "DATABASE_URL is not set. Add it to .env, e.g. "
            "postgresql://postgres:PASSWORD@localhost:5432/translink_data"
        )

    # Collection window, as HH:MM in America/Vancouver time
    raw_start = os.environ.get("COLLECT_START", DEFAULT_COLLECT_START).strip()
    raw_end = os.environ.get("COLLECT_END", DEFAULT_COLLECT_END).strip()
    try:
        collect_start = time.fromisoformat(raw_start)
        collect_end = time.fromisoformat(raw_end)
    except ValueError:
        raise ConfigError(
            f"COLLECT_START and COLLECT_END must look like HH:MM, got {raw_start!r} and {raw_end!r}"
        ) from None
    if collect_start >= collect_end:
        # A window that crosses midnight (e.g. 22:00-02:00) isn't supported
        raise ConfigError(
            f"COLLECT_START ({raw_start}) must be earlier than COLLECT_END ({raw_end})"
        )

    raw_cap = os.environ.get("DAILY_REQUEST_CAP", str(DEFAULT_DAILY_REQUEST_CAP)).strip()
    try:
        daily_request_cap = int(raw_cap)
    except ValueError:
        raise ConfigError(f"DAILY_REQUEST_CAP must be a whole number, got {raw_cap!r}") from None
    if daily_request_cap <= 0:
        raise ConfigError(f"DAILY_REQUEST_CAP must be greater than 0, got {daily_request_cap}")

    return Settings(
        translink_api_key=api_key,
        feed_url=feed_url,
        http_timeout_seconds=timeout,
        user_agent=user_agent,
        database_url=database_url,
        collect_start=collect_start,
        collect_end=collect_end,
        daily_request_cap=daily_request_cap,
    )
