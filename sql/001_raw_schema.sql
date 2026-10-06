-- 001_raw_schema.sql
-- Raw layer: one row per fetch of the TransLink GTFS-Realtime feed, stored exactly as received.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.feed_snapshots (
    snapshot_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Our clock: when the fetcher received the feed. Python passes the time the
    -- response arrived; now() (insert time) is only a fallback.
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- TransLink's clock: feed.header.timestamp, when they generated the snapshot.
    -- A missing header timestamp parses as 0 (1970-01-01), so reject implausible values.
    feed_timestamp  TIMESTAMPTZ NOT NULL
                    CONSTRAINT feed_snapshots_feed_timestamp_check
                    CHECK (feed_timestamp >= '2020-01-01 00:00:00+00'),

    -- MessageToDict(feed), the full feed
    payload         JSONB       NOT NULL,

    -- len(resp.content): size of the protobuf as received, not of the JSONB
    payload_bytes   INTEGER     NOT NULL CHECK (payload_bytes >= 0),
    entity_count    INTEGER     NOT NULL CHECK (entity_count >= 0),

    -- The same snapshot fetched twice has the same feed_timestamp.
    -- Python inserts with ON CONFLICT (feed_timestamp) DO NOTHING.
    CONSTRAINT feed_snapshots_feed_timestamp_key UNIQUE (feed_timestamp)
);

-- No separate index: the UNIQUE constraint above already creates a B-tree index on
-- feed_timestamp, which serves range queries such as "all snapshots between 4 and 6 PM".
