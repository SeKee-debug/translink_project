-- 006_analysis_days.sql
-- Which weekday evenings go into the analysis, and why. The decision lives here, so queries
-- (and Power BI) just join to this table instead of typing a list of dates every time.
--
-- The rule: a weekday evening is included if it covers at least 90% of the 3:30-7:25 PM window
-- (235 minutes) and has no gap longer than 10 minutes.
--
-- Usage in later queries:
--   JOIN analytics.analysis_days d USING (service_date) WHERE d.included
--
-- Safe to run again. When I collect a new day, I add a row below and re-run the file. Days that
-- are already in the table just get their included/reason updated.

CREATE TABLE IF NOT EXISTS analytics.analysis_days (
    service_date  DATE     PRIMARY KEY,
    included      BOOLEAN  NOT NULL,
    reason        TEXT     NOT NULL
);

INSERT INTO analytics.analysis_days (service_date, included, reason) VALUES
    ('2026-09-30', true,  '94% of window, starts 15:45, no gaps over 2 min'),
    ('2026-10-01', false, '83% of window, 32-min gap 17:35-18:07 during peak (plus 9-min gap 17:09-17:18)'),
    ('2026-10-06', false, '77% of window, 37-min gap 18:21-18:58 during peak, stops at 19:07'),
    ('2026-10-07', true,  '97% of window, one 8-min gap 17:41-17:49'),
    ('2026-10-20', true,  '100% of window, no gaps over 2 min'),
    ('2026-10-21', false, '29% of window, only starts at 18:16 after connection errors'),
    ('2026-11-19', true,  '95% of window, 15:37-19:19, no gaps over 2 min')
ON CONFLICT (service_date) DO UPDATE SET
    included = EXCLUDED.included,
    reason   = EXCLUDED.reason;
