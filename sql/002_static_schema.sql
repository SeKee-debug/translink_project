-- 002_static_schema.sql
-- Static layer: TransLink's GTFS static files (routes, trips, stops), loaded as given.
-- Columns mirror each file's header, in the same names and order.
-- Type rules: IDs and codes are TEXT (never do math on them, and leading zeros must survive),
-- fixed GTFS code lists are SMALLINT, coordinates are DOUBLE PRECISION.

CREATE SCHEMA IF NOT EXISTS static;

CREATE TABLE IF NOT EXISTS static.routes (
    route_id          TEXT      PRIMARY KEY,
    agency_id         TEXT,
    route_short_name  TEXT,                -- '033': TEXT keeps the leading zero
    route_long_name   TEXT,
    route_desc        TEXT,
    route_type        SMALLINT  NOT NULL,  -- GTFS code: 3 = bus
    route_url         TEXT,
    route_color       TEXT,
    route_text_color  TEXT
);

CREATE TABLE IF NOT EXISTS static.stops (
    stop_id              TEXT              PRIMARY KEY,  -- what the realtime feed uses
    stop_code            TEXT,                           -- the 5-digit number on the bus-stop sign
    stop_name            TEXT              NOT NULL,
    stop_desc            TEXT,
    stop_lat             DOUBLE PRECISION,
    stop_lon             DOUBLE PRECISION,
    zone_id              TEXT,
    stop_url             TEXT,
    location_type        SMALLINT,                       -- GTFS code: 0 = stop, 1 = station, 2 = entrance
    -- Points to another row in this same table (a station). No foreign key: it would force
    -- stations to be loaded before their stops, and the file isn't in that order.
    parent_station       TEXT,
    wheelchair_boarding  SMALLINT                        -- GTFS code: 0 = unknown, 1 = yes, 2 = no
);

CREATE TABLE IF NOT EXISTS static.trips (
    route_id               TEXT      NOT NULL REFERENCES static.routes (route_id),
    service_id             TEXT,                 -- which days the trip runs (calendar.txt)
    trip_id                TEXT      PRIMARY KEY,
    trip_headsign          TEXT,                 -- e.g. '2 Macdonald/To Burrard Station'
    trip_short_name        TEXT,
    direction_id           SMALLINT,             -- GTFS code: 0 or 1
    block_id               TEXT,                 -- trips run back to back by the same vehicle
    shape_id               TEXT,
    wheelchair_accessible  SMALLINT,             -- GTFS code: 0 = unknown, 1 = yes, 2 = no
    bikes_allowed          SMALLINT              -- GTFS code: 0 = unknown, 1 = yes, 2 = no
);
