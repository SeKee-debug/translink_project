-- 004_processed_snapshots.sql
-- Checklist of the raw snapshots that have already been applied to analytics.stop_arrivals.
-- Each snapshot gets applied once, oldest first, so times_seen and first_seen_at stay right.

CREATE TABLE IF NOT EXISTS analytics.processed_snapshots (
    -- PRIMARY KEY so a snapshot can only be ticked off once.
    -- ON DELETE CASCADE so that when old raw snapshots get deleted later, their ticks go with them.
    -- Without it the foreign key would block those deletes.
    snapshot_id   BIGINT       PRIMARY KEY
                  REFERENCES raw.feed_snapshots (snapshot_id) ON DELETE CASCADE,
    processed_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
