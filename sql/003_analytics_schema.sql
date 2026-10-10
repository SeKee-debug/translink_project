-- 003_analytics_schema.sql
-- Analytics layer: one row per bus serving one stop on one service day, holding the LAST
-- prediction seen before the stop dropped out of the feed (our estimate of the actual arrival).
-- Built from raw.feed_snapshots by upsert: a row is only overwritten by a newer snapshot,
-- so re-processing old snapshots never changes the result.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.stop_arrivals (
    -- Key: the same trip_id runs every weekday (so add the date), and a loop route can
    -- visit the same stop twice in one trip (so use stop_sequence, not stop_id)
    service_date     DATE         NOT NULL,   -- trip.start_date: Vancouver service day, kept after midnight
    trip_id          TEXT         NOT NULL,
    stop_sequence    INTEGER      NOT NULL,

    route_id         TEXT         NOT NULL,   -- copied from the feed so analysis can skip static.trips
    stop_id          TEXT         NOT NULL,

    status           TEXT         NOT NULL
                     CHECK (status IN ('SCHEDULED', 'SKIPPED')),   -- as last seen

    -- NULL when the last status is SKIPPED: a skipped stop has no arrival block at all
    arrival_time     TIMESTAMPTZ,
    arrival_delay_s  INTEGER,

    first_seen_at    TIMESTAMPTZ  NOT NULL,   -- feed_timestamp of the first snapshot listing this stop
    -- feed_timestamp of the snapshot these values came from. arrival_time - last_seen_at shows
    -- how far ahead our last glimpse was, i.e. how trustworthy the arrival estimate is
    last_seen_at     TIMESTAMPTZ  NOT NULL,
    times_seen       INTEGER      NOT NULL CHECK (times_seen >= 1),

    CONSTRAINT stop_arrivals_pkey PRIMARY KEY (service_date, trip_id, stop_sequence),
    CONSTRAINT stop_arrivals_seen_order CHECK (first_seen_at <= last_seen_at),
    -- Time and delay are always missing together (only for SKIPPED stops); never store one without the other
    CONSTRAINT stop_arrivals_arrival_pair
        CHECK ((arrival_time IS NULL) = (arrival_delay_s IS NULL)),
    -- A SCHEDULED stop must have an arrival time. True in the data so far; if TransLink ever sends a
    -- SCHEDULED stop with only a departure, the transform fails loudly and we revisit this rule.
    -- Nothing is lost when it does: raw keeps collecting, and the transform can be re-run.
    CONSTRAINT stop_arrivals_scheduled_has_time
        CHECK (status = 'SKIPPED' OR arrival_time IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS stop_arrivals_route_date_idx
    ON analytics.stop_arrivals (route_id, service_date);
