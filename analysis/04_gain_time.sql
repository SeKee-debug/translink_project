-- 04_gain_time.sql
-- Where do buses gain the most time? Basically, where does the timetable give a stretch more time
-- than buses actually need? It's the same query as 03_lose_time.sql, just sorted the other way so the
-- most negative change_s comes first.
--
-- Again, before_s and after_s tell you what's going on. If buses show up late and leave about on time,
-- the extra time is soaking up delay and the buffer is doing its job. If they're already on time or early
-- and get even earlier, the timetable is too generous there and could probably be tightened. Early buses
-- aren't harmless either, since anyone who planned around the timetable can miss them.
-- This is where the bridges show up (Lions Gate on the North Shore routes, Burrard on Route 2).
-- I kept the same first stop / last stop / neighbour filters as 03, for the same reasons.

WITH last_stop AS (
    SELECT service_date, trip_id, MAX(stop_sequence) AS last_seq
    FROM analytics.stop_arrivals
    GROUP BY service_date, trip_id
),
t AS (
    SELECT a.route_short_name, a.service_date, a.trip_id, a.stop_sequence, a.stop_id, a.stop_name,
           a.arrival_delay_s, l.last_seq,
           LAG(a.stop_sequence)   OVER w AS prev_seq,
           LAG(a.stop_id)         OVER w AS prev_stop_id,
           LAG(a.stop_name)       OVER w AS prev_stop_name,
           LAG(a.arrival_delay_s) OVER w AS prev_delay
    FROM analytics.analysis_arrivals a
    JOIN last_stop l USING (service_date, trip_id)
    WHERE a.is_trusted
    WINDOW w AS (PARTITION BY a.service_date, a.trip_id ORDER BY a.stop_sequence)
)
SELECT route_short_name,
       MIN(prev_stop_name) || '  ->  ' || MIN(stop_name)                                          AS stretch,
       COUNT(*)                                                                                    AS n,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY prev_delay)::numeric)                    AS before_s,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s)::numeric)               AS after_s,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY arrival_delay_s - prev_delay)::numeric)  AS change_s
FROM t
WHERE prev_seq = stop_sequence - 1
  AND prev_seq > 1
  AND stop_sequence < last_seq
GROUP BY route_short_name, prev_stop_id, stop_id
HAVING COUNT(*) >= 30
ORDER BY change_s ASC
LIMIT 15;
