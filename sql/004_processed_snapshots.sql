-- 004_processed_snapshots.sql
-- Checklist of raw snapshots already applied to analytics.stop_arrivals. Each snapshot is
-- applied exactly once, oldest first, so times_seen and first_seen_at stay correct.

CREATE TABLE IF NOT EXISTS analytics.processed_snapshots (
    -- PRIMARY KEY: a snapshot can be ticked off only once.
    -- ON DELETE CASCADE: when old raw snapshots are deleted (retention), their ticks go too;
    -- without it, this foreign key would block those deletes.
    snapshot_id   BIGINT       PRIMARY KEY
                  REFERENCES raw.feed_snapshots (snapshot_id) ON DELETE CASCADE,
    processed_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
