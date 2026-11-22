-- 06_by_hour.sql
-- When in the evening are buses latest across the whole network? I wanted to know if there's a
-- 5-6 PM peak like R2 has, or if delay just builds up and stays high until the window ends.
-- There's one row per hour of arrival (15 = 3 PM up to 19 = 7 PM). The 15 row only covers 15:30-15:59
-- and the 19 row only covers 19:00-19:24, so those two have a smaller n than the rest.

SELECT arrival_hour,
       COUNT(*)                                                                      AS n,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS median_s,
       ROUND(percentile_cont(0.9) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS p90_s,
       ROUND(100.0 * AVG((arrival_delay_s BETWEEN -60 AND 180)::int), 1)            AS on_time_pct
FROM analytics.analysis_arrivals
WHERE is_trusted
GROUP BY arrival_hour
ORDER BY arrival_hour;
