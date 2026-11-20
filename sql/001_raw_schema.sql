-- 001_raw_schema.sql
-- Raw layer. Each row is one fetch of TransLink's GTFS-Realtime feed, saved exactly how it came in.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.feed_snapshots (
    snapshot_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Our clock, so when the fetcher got the feed. Python sends the time the response arrived.
    -- now() (the insert time) is only there as a backup.
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- TransLink's clock (feed.header.timestamp), so when they made the snapshot. If the
    -- timestamp is missing it comes through as 0 (1970-01-01), so anything that early is rejected.
    feed_timestamp  TIMESTAMPTZ NOT NULL
                    CONSTRAINT feed_snapshots_feed_timestamp_check
                    CHECK (feed_timestamp >= '2020-01-01 00:00:00+00'),

    -- The whole feed, converted with MessageToDict(feed)
    payload         JSONB       NOT NULL,

    -- len(resp.content), so the size of the protobuf we downloaded, not the JSONB
    payload_bytes   INTEGER     NOT NULL CHECK (payload_bytes >= 0),
    entity_count    INTEGER     NOT NULL CHECK (entity_count >= 0),

    -- If we fetch the same snapshot twice it has the same feed_timestamp, so Python
    -- inserts with ON CONFLICT (feed_timestamp) DO NOTHING.
    CONSTRAINT feed_snapshots_feed_timestamp_key UNIQUE (feed_timestamp)
);

-- No extra index needed. The UNIQUE constraint already makes a B-tree index on feed_timestamp,
-- and that works for range queries like "all snapshots between 4 and 6 PM".
