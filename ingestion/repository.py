import logging

import psycopg
from psycopg.types.json import Jsonb

from ingestion.models import FeedSnapshot

logger = logging.getLogger(__name__)

INSERT_SNAPSHOT_SQL = """
    INSERT INTO raw.feed_snapshots
        (fetched_at, feed_timestamp, payload, payload_bytes, entity_count)
    VALUES
        (%(fetched_at)s, %(feed_timestamp)s, %(payload)s, %(payload_bytes)s, %(entity_count)s)
    ON CONFLICT (feed_timestamp) DO NOTHING
    RETURNING snapshot_id
"""


def save_snapshot(conn: psycopg.Connection, snapshot: FeedSnapshot) -> bool:
    """Insert one snapshot. Returns True if a row was inserted, False if it was a duplicate."""
    params = {
        "fetched_at": snapshot.fetched_at,
        "feed_timestamp": snapshot.feed_timestamp,
        "payload": Jsonb(snapshot.payload),
        "payload_bytes": snapshot.payload_bytes,
        "entity_count": snapshot.entity_count,
    }

    try:
        with conn.cursor() as cur:
            cur.execute(INSERT_SNAPSHOT_SQL, params)
            row = cur.fetchone()
        conn.commit()
    except Exception:
        # A failed statement leaves the transaction aborted; roll back so the
        # connection can be used for the next snapshot
        conn.rollback()
        raise

    if row is None:
        logger.info(
            "Duplicate snapshot skipped: feed_timestamp=%s", snapshot.feed_timestamp.isoformat()
        )
        return False

    logger.info(
        "Saved snapshot %d: feed_timestamp=%s, entities=%d",
        row[0],
        snapshot.feed_timestamp.isoformat(),
        snapshot.entity_count,
    )
    return True
