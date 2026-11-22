-- 02_route_ranking.sql
-- Which routes are the most delayed in the evening rush?
-- Routes are sorted by median delay, latest first. Before I believe a route near the top, I check
-- two things. Is n comfortably over the cutoff, or only just? And is p90_s huge next to median_s?
-- If it is, a few extreme rows (maybe stale entries) could be what's putting it there.
-- The HAVING COUNT(*) >= 500 drops routes with so few arrivals that one bad trip could put them on top.

SELECT route_short_name,
       route_long_name,
       COUNT(*)                                                                      AS n,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS median_s,
       ROUND(percentile_cont(0.9) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS p90_s,
       ROUND(100.0 * AVG((arrival_delay_s BETWEEN -60 AND 180)::int), 1)            AS on_time_pct
FROM analytics.analysis_arrivals
WHERE is_trusted
GROUP BY route_short_name, route_long_name
HAVING COUNT(*) >= 500
ORDER BY median_s DESC
LIMIT 15;
