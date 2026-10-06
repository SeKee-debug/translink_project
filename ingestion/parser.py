import logging
from datetime import datetime, timezone

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
from google.transit import gtfs_realtime_pb2

from ingestion.models import FeedSnapshot, RawFetch

logger = logging.getLogger(__name__)


class ParseError(ValueError):
    """The fetched bytes are not a usable GTFS-Realtime feed."""


def parse_feed(raw: RawFetch) -> FeedSnapshot:
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(raw.content)
    except DecodeError as exc:
        # e.g. a gateway maintenance page served with HTTP 200; HTML starts with b'<'
        raise ParseError(
            f"Response is not a GTFS-Realtime feed ({len(raw.content)} bytes, "
            f"starts with {raw.content[:40]!r})"
        ) from exc

    # Protobuf reads a missing timestamp as 0 (1970-01-01); catch it before the DB CHECK does
    if feed.header.timestamp == 0:
        raise ParseError("Feed header has no timestamp")

    feed_timestamp = datetime.fromtimestamp(feed.header.timestamp, tz=timezone.utc)

    snapshot = FeedSnapshot(
        fetched_at=raw.fetched_at,
        feed_timestamp=feed_timestamp,
        payload=MessageToDict(feed, preserving_proto_field_name=True),
        payload_bytes=len(raw.content),
        entity_count=len(feed.entity),
    )
    logger.info(
        "Parsed feed: timestamp=%s, entities=%d",
        snapshot.feed_timestamp.isoformat(),
        snapshot.entity_count,
    )
    return snapshot
