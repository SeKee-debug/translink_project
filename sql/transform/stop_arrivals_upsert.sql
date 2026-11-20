-- stop_arrivals_upsert.sql
-- Applies one batch of raw snapshots to analytics.stop_arrivals. ingestion/transform.py runs this,
-- passes in %(snapshot_ids)s, and does it in the same transaction as ticking the batch off in
-- analytics.processed_snapshots.
--
-- ASSUMPTION: batches go oldest first, and each one only once. The WHERE at the bottom skips any
-- batch that's older than what's already stored, so if a batch came out of order its sightings would
-- never get counted in times_seen / first_seen_at. The runner makes sure the order is right.

WITH batch AS (
    SELECT snapshot_id, feed_timestamp, payload
    FROM raw.feed_snapshots
    WHERE snapshot_id = ANY(%(snapshot_ids)s)
),
trips AS (
    -- One row per trip. Cancelled trips never actually ran, so they don't have arrivals.
    -- The spec says that if the trip status is missing, it counts as SCHEDULED.
    SELECT b.feed_timestamp, e -> 'trip_update' AS tu
    FROM batch b, jsonb_array_elements(b.payload -> 'entity') AS e
    WHERE COALESCE(e -> 'trip_update' -> 'trip' ->> 'schedule_relationship', 'SCHEDULED') = 'SCHEDULED'
),
flat AS (
    -- One row per stop per trip per snapshot
    SELECT to_date(t.tu -> 'trip' ->> 'start_date', 'YYYYMMDD')   AS service_date,
           t.tu -> 'trip' ->> 'trip_id'                           AS trip_id,
           (su ->> 'stop_sequence')::int                          AS stop_sequence,
           -- route_id is optional in GTFS-Realtime, so if it's missing we use the static schedule's
           COALESCE(t.tu -> 'trip' ->> 'route_id', st.route_id)   AS route_id,
           su ->> 'stop_id'                                       AS stop_id,
           su ->> 'schedule_relationship'                         AS status,
           to_timestamp((su -> 'arrival' ->> 'time')::bigint)     AS arrival_time,
           (su -> 'arrival' ->> 'delay')::int                     AS arrival_delay_s,
           t.feed_timestamp
    FROM trips t
    CROSS JOIN LATERAL jsonb_array_elements(t.tu -> 'stop_time_update') AS su
    LEFT JOIN static.trips st ON st.trip_id = t.tu -> 'trip' ->> 'trip_id'
),
newest AS (
    -- One row per key, the newest sighting in this batch. An upsert can't update the same key twice
    -- in one statement, so the duplicates have to be sorted out here first.
    SELECT DISTINCT ON (service_date, trip_id, stop_sequence) *
    FROM flat
    ORDER BY service_date, trip_id, stop_sequence, feed_timestamp DESC
),
stats AS (
    -- Counts distinct snapshot times instead of rows. If a trip shows up twice in one snapshot
    -- (we've seen this with two vehicles on one trip), that should still be one sighting.
    SELECT service_date, trip_id, stop_sequence,
           MIN(feed_timestamp)            AS first_seen_at,
           COUNT(DISTINCT feed_timestamp) AS times_seen
    FROM flat
    GROUP BY service_date, trip_id, stop_sequence
)
INSERT INTO analytics.stop_arrivals AS sa
    (service_date, trip_id, stop_sequence, route_id, stop_id, status,
     arrival_time, arrival_delay_s, first_seen_at, last_seen_at, times_seen)
SELECT n.service_date, n.trip_id, n.stop_sequence, n.route_id, n.stop_id, n.status,
       n.arrival_time, n.arrival_delay_s, s.first_seen_at, n.feed_timestamp, s.times_seen
FROM newest n
JOIN stats s USING (service_date, trip_id, stop_sequence)
-- sa is the row that's already stored, EXCLUDED is this batch's row for the same key
ON CONFLICT (service_date, trip_id, stop_sequence) DO UPDATE SET
    route_id        = EXCLUDED.route_id,                              -- newer prediction wins
    stop_id         = EXCLUDED.stop_id,
    status          = EXCLUDED.status,
    arrival_time    = EXCLUDED.arrival_time,
    arrival_delay_s = EXCLUDED.arrival_delay_s,
    first_seen_at   = LEAST(sa.first_seen_at, EXCLUDED.first_seen_at),  -- keep the earliest
    last_seen_at    = EXCLUDED.last_seen_at,
    times_seen      = sa.times_seen + EXCLUDED.times_seen               -- running total
-- Only apply data that's newer. Running a batch again doesn't change anything, so times_seen can't double.
WHERE EXCLUDED.last_seen_at > sa.last_seen_at;
