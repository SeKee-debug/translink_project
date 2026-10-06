import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_FEED_URL = "https://gtfsapi.translink.ca/v3/gtfsrealtime"
DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0
USER_AGENT_BASE = "translink-delay-pipeline/0.1"


class ConfigError(Exception):
    """A required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    translink_api_key: str
    feed_url: str
    http_timeout_seconds: float
    user_agent: str
    database_url : str

    def __repr__(self) -> str:
        # Keep the key out of logs and tracebacks
        return (
            f"Settings(translink_api_key='***', feed_url={self.feed_url!r}, "
            f"http_timeout_seconds={self.http_timeout_seconds}, "
            f"user_agent = {self.user_agent}, "
            f"database_url='***')"
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

    # Identify the program honestly, with a way for TransLink to contact us if set
    contact = os.environ.get("CONTACT_EMAIL", "").strip()
    user_agent = f"{USER_AGENT_BASE} ({contact})" if contact else USER_AGENT_BASE
    database_url = os.environ.get("DATABASE_URL").strip()

    return Settings(
        translink_api_key=api_key,
        feed_url=feed_url,
        http_timeout_seconds=timeout,
        user_agent=user_agent,
        database_url=database_url
    )
