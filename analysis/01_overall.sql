-- 01_overall.sql
-- How late are buses overall in the weekday 3:30-7:25 PM window?
-- median_s is what a typical bus looks like. p90_s is a bad bus, since 9 out of 10 arrivals are
-- better than it. If avg_s is way bigger than median_s, it means a few really late buses are
-- dragging the average up, which is why I go by the median.
-- I'm counting "on time" as anywhere from 1 min early to 3 min late (-60 to +180 s).

SELECT COUNT(*)                                                                      AS n,
       ROUND(AVG(arrival_delay_s))                                                   AS avg_s,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS median_s,
       ROUND(percentile_cont(0.9) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS p90_s,
       ROUND(100.0 * AVG((arrival_delay_s BETWEEN -60 AND 180)::int), 1)            AS on_time_pct
FROM analytics.analysis_arrivals
WHERE is_trusted;
