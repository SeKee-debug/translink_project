-- 05_r2_by_hour.sql
-- Is R2 latest during the peak hours?
-- I checked this because R2 dropped from #2 to #6 once I added the partial days (Oct 1 and Oct 6),
-- and both of those are missing chunks of 5:30-7 PM. If R2 is worst in exactly those hours, then
-- missing them would make it look better than it really is.
-- You get one row per hour of arrival. If median_s is highest at 17 and 18, that backs up the peak idea.
-- With 3 evenings it does: 192 s at 15:00, up to 365 s at 18:00. But Oct 20 was also about twice as
-- late as Nov 19 at every hour, so there's day-to-day variation on top of the peak.

SELECT arrival_hour,
       COUNT(*)                                                                      AS n,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)  AS median_s
FROM analytics.analysis_arrivals
WHERE is_trusted AND route_short_name = 'R2'
GROUP BY arrival_hour
ORDER BY arrival_hour;
