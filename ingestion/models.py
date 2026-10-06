from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawFetch:
    content: bytes
    fetched_at: datetime  # UTC, recorded the moment the response arrived


@dataclass(frozen=True)
class FeedSnapshot:
    fetched_at: datetime
    feed_timestamp: datetime
    payload: dict[str, Any]
    payload_bytes: int
    entity_count: int