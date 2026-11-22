-- 03_lose_time.sql
-- Where on a route do buses lose the most time?
-- For every pair of stops next to each other, change_s is the delay at the second stop minus the
-- delay at the first one. If it's positive, the bus lost time on that stretch compared with the timetable.
--
-- change_s alone can fool you, so I look at before_s and after_s too. If the bus is around on time or
-- already late before, and a lot later after, that's traffic (a real bottleneck). If it's clearly early
-- before (below -30 s) and right around 0 after, it's probably holding, meaning an early bus waited at a
-- timepoint on purpose. Holding can only bring a bus up to 0, never past it. So if after_s is clearly
-- late, holding can't be the whole story.
--
-- Some stretches are left out on purpose. Before a trip starts, its first stop just shows the timetable
-- with a delay of 0, so a stretch leaving stop 1 mostly tells you how late the bus started. Buses also sit
-- at the last stop of a trip, so that one says pretty much nothing about the road. And if a stop in the
-- middle was untrusted or skipped, the pair would cover two stretches, so I only keep real neighbours.
--
-- last_stop reads from stop_arrivals instead of the analysis view. The view cuts arrivals after 19:25,
-- so a trip that ends at 19:40 would look like it ends earlier than it actually does.

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
WHERE prev_seq = stop_sequence - 1   -- the two stops have to be right next to each other
  AND prev_seq > 1                   -- skip stretches leaving the first stop
  AND stop_sequence < last_seq       -- skip stretches ending at the last stop
GROUP BY route_short_name, prev_stop_id, stop_id
HAVING COUNT(*) >= 30                -- need at least 30 trips over a stretch to count it
ORDER BY change_s DESC
LIMIT 15;
