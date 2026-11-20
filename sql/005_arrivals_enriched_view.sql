-- 005_arrivals_enriched_view.sql
-- A view of analytics.stop_arrivals that's ready for analysis. It has every stored column, plus how
-- much we can trust each arrival, the local time, and route/trip/stop names from the static schedule.
-- A view doesn't store any data. It's basically a saved query, so it always matches the current tables.

CREATE OR REPLACE VIEW analytics.arrivals_enriched AS
SELECT
    a.service_date,
    a.trip_id,
    a.stop_sequence,
    a.route_id,
    a.stop_id,
    a.status,
    a.arrival_time,
    a.arrival_delay_s,
    a.first_seen_at,
    a.last_seen_at,
    a.times_seen,

    -- How long before the arrival we last saw this stop. Smaller means the arrival time is closer
    -- to what really happened. It's NULL for SKIPPED stops since they have no arrival.
    EXTRACT(EPOCH FROM a.arrival_time - a.last_seen_at)          AS lead_s,

    -- Trusted means a real arrival that we last saw within a minute of it (before or after). This is
    -- never NULL, because SKIPPED rows fail the status check before the NULL arrival_time gets compared.
    (a.status = 'SCHEDULED'
     AND a.arrival_time - a.last_seen_at >= INTERVAL '-60 seconds'
     AND a.arrival_time - a.last_seen_at <= INTERVAL '60 seconds') AS is_trusted,

    -- Local time uses Postgres's own time zone rules (BC is on UTC-7 all year starting in 2026)
    a.arrival_time AT TIME ZONE 'America/Vancouver'                 AS arrival_local,
    EXTRACT(HOUR FROM a.arrival_time AT TIME ZONE 'America/Vancouver')::int AS arrival_hour,
    EXTRACT(ISODOW FROM a.service_date)::int                       AS day_of_week,  -- 1 = Monday ... 7 = Sunday

    -- Names. These are LEFT JOINs, so a trip or stop that's missing from the static files still keeps its row, just with NULL names
    r.route_short_name,
    r.route_long_name,
    t.trip_headsign,
    t.direction_id,
    s.stop_code,
    s.stop_name,
    s.stop_lat,
    s.stop_lon
FROM analytics.stop_arrivals a
LEFT JOIN static.routes r ON r.route_id = a.route_id
LEFT JOIN static.trips  t ON t.trip_id  = a.trip_id
LEFT JOIN static.stops  s ON s.stop_id  = a.stop_id;
