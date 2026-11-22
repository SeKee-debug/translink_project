-- 007_analysis_arrivals_view.sql
-- The rows the analysis actually uses. Same columns as analytics.arrivals_enriched, with two filters:
--
--   1. Only included days (analytics.analysis_days, see 006).
--   2. Only 3:30-7:25 PM Vancouver time (15:30 up to but not including 19:25). That's the collection
--      window. Some days (like Sep 30, collected 14:39-20:15) have extra hours, and without this
--      filter those days would count a bigger slice of the day than the others.
--
-- The time used for the filter is the arrival time if there is one, otherwise last_seen_at.
-- SKIPPED stops have no arrival time, so filtering on arrival time alone would quietly drop all of
-- them, and I want to keep them for counting skips later.
--
-- is_trusted is NOT filtered here on purpose. Delay questions add WHERE is_trusted themselves,
-- while skip questions need the SKIPPED rows (which are never trusted).
--
-- Note: a.* gets expanded into a fixed column list when the view is created, so if 005 ever gets
-- new columns, this file has to be run again to pick them up.

CREATE OR REPLACE VIEW analytics.analysis_arrivals AS
SELECT a.*
FROM analytics.arrivals_enriched a
JOIN analytics.analysis_days d USING (service_date)
WHERE d.included
  AND (COALESCE(a.arrival_time, a.last_seen_at) AT TIME ZONE 'America/Vancouver')::time >= '15:30'
  AND (COALESCE(a.arrival_time, a.last_seen_at) AT TIME ZONE 'America/Vancouver')::time <  '19:25';
