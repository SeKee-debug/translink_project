-- 003_analytics_schema.sql
-- Analytics layer. One row per bus serving one stop on one service day. It holds the LAST
-- prediction we saw before the stop dropped out of the feed, which is our guess at the real arrival.
-- It's built from raw.feed_snapshots with an upsert, and a row only gets overwritten by a newer
-- snapshot, so processing old snapshots again doesn't change anything.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.stop_arrivals (
    -- The key. The same trip_id runs every weekday, so the date has to be in it. A loop route can
    -- also hit the same stop twice in one trip, so it uses stop_sequence instead of stop_id.
    service_date     DATE         NOT NULL,   -- trip.start_date, the Vancouver service day (stays the same after midnight)
    trip_id          TEXT         NOT NULL,
    stop_sequence    INTEGER      NOT NULL,

    route_id         TEXT         NOT NULL,   -- copied from the feed so the analysis doesn't need static.trips
    stop_id          TEXT         NOT NULL,

    status           TEXT         NOT NULL
                     CHECK (status IN ('SCHEDULED', 'SKIPPED')),   -- as last seen

    -- NULL when the last status is SKIPPED, since a skipped stop doesn't have an arrival block
    arrival_time     TIMESTAMPTZ,
    arrival_delay_s  INTEGER,

    first_seen_at    TIMESTAMPTZ  NOT NULL,   -- feed_timestamp of the first snapshot listing this stop
    -- feed_timestamp of the snapshot these values came from. arrival_time - last_seen_at tells us
    -- how far ahead our last look was, which is basically how much we can trust the arrival time.
    last_seen_at     TIMESTAMPTZ  NOT NULL,
    times_seen       INTEGER      NOT NULL CHECK (times_seen >= 1),

    CONSTRAINT stop_arrivals_pkey PRIMARY KEY (service_date, trip_id, stop_sequence),
    CONSTRAINT stop_arrivals_seen_order CHECK (first_seen_at <= last_seen_at),
    -- Time and delay are always missing together (only on SKIPPED stops), so never store one without the other
    CONSTRAINT stop_arrivals_arrival_pair
        CHECK ((arrival_time IS NULL) = (arrival_delay_s IS NULL)),
    -- A SCHEDULED stop has to have an arrival time. That's been true in the data so far. If TransLink
    -- ever sends a SCHEDULED stop with only a departure, the transform fails and we rethink this rule.
    -- We don't lose anything when that happens, since raw keeps collecting and the transform can run again.
    CONSTRAINT stop_arrivals_scheduled_has_time
        CHECK (status = 'SKIPPED' OR arrival_time IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS stop_arrivals_route_date_idx
    ON analytics.stop_arrivals (route_id, service_date);
