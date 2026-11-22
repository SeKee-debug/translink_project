# TransLink bus delays

I collected TransLink's live bus predictions (GTFS-Realtime) on weekday evenings and stored them in PostgreSQL to figure out which Metro Vancouver bus routes run late, and where on the route the time gets lost.

## Findings

Route 254 (British Properties / Park Royal) is the most consistently late route, about 6 minutes late at the median with only 15% of arrivals on time. The worst real bottleneck is R4 on W 41st Ave, where buses lose about 6.5 minutes on a single stretch. Both the Lions Gate and Burrard bridges are padded for the evening rush out of downtown, so buses going the other way arrive downtown early, 4 to 6 minutes early over Lions Gate. Across the network, the 5 to 6 PM peak barely changes a typical bus but makes the worst trips a lot worse.

These results come from 3 weekday evenings (Wed Oct 7, Tue Oct 20 and Thu Nov 19, 2026), from 3:30 to 7:25 PM. That isn't a lot of data yet, so treat everything here as preliminary. I'm still collecting, and the plan is to rerun all of this once I have around 10 evenings.

### Overview

There are 464,695 trusted arrivals in the analysis window (95.3% of the arrival rows in that window). The median bus was 73 seconds late. The 90th percentile was 465 s, so about 1 in 10 arrivals was more than about 7¾ minutes late. Only 50.4% of arrivals were on time, which I defined as anywhere from 1 minute early to 3 minutes late.

The average delay is 130 s, almost double the median. A few very late buses pull the average up. The worst trusted row is a route 14 bus on Oct 20 listed as 12,211 s late (about 3 hours 20 minutes), which is almost certainly a data problem and not a real delay. A row like that moves the average but barely touches the median, so I use the median everywhere.

### Most delayed routes

| Route | Median delay | On time | Trusted arrivals |
|---|---|---|---|
| 254 British Properties / Park Royal | 352 s | 14.9% | 1,045 |
| R2 Marine-Willingdon | 293 s | 25.8% | 2,736 |
| 129 Patterson Stn / Holdom Stn | 289 s | 35.1% | 3,210 |
| 105 New West Stn / Uptown | 285 s | 32.2% | 979 |
| 028 Boundary | 257 s | 38.9% | 2,605 |

Only routes with at least 500 trusted arrivals are ranked (183 of 205 routes).

Route 254 is the clearest result. It's #1 no matter which days I include, and it's late by about the same amount every evening (around 350 s on each of the 3 days). Only about 15% of its arrivals are on time.

I also reran the ranking with the two partial days (Oct 1 and Oct 6) added. 105, 129 and 028 stay in the top 5, so I think those results hold up too.

R2 is harder to pin down. It's #2 with the 3 clean days but drops to #6 once the partial days are added. Looking at it by hour explains most of it. R2 gets later through the evening, from a median of 192 s between 3:30 and 4 PM to 365 s at 6 PM, and the partial days are missing exactly that part of the evening (around 5:30 to 7 PM). It also changes a lot from day to day: Oct 20 was about twice as late as Nov 19 in every hour.

### Where buses lose time

For this I compared each pair of neighbouring stops: the delay at the second stop minus the delay at the first. A positive number means the bus lost time on that stretch compared with the timetable.

The worst real bottleneck I found is R4 eastbound on W 41st Ave, between Carnarvon St and East Blvd. Buses lose a median of 394 s (about 6.5 minutes) on that one stretch, over 152 trips. They arrive at Carnarvon about 1¾ minutes early and reach East Blvd about 4½ minutes late.

Not every big loss is traffic, though. Early buses are told to wait at some stops until their scheduled time, and in the data that looks the same as losing time. To tell them apart, I looked at the delay before and after each stretch. Holding can only bring an early bus up to 0, never past it. So if a bus is early before and right around 0 after, it's holding. If it ends up clearly late, it's traffic. Six of the top 15 stretches were holding, for example R3 on Lougheed Hwy (-285 s before, -58 s after) and both 503 stretches into Langley Centre (exactly 0 after).

Some of the real congestion is on the way into busy exchanges. R2 is already about 4.5 minutes late before Brentwood Station and loses another 4 minutes getting in. It's the same story going into Lonsdale Quay.

I left out stretches that leave a trip's first stop or arrive at its last stop. Before a trip starts, its first stop just shows the timetable (delay 0), and buses tend to sit at the last stop. This turned out to matter. Routes 155 and 101 both looked like they lost about 5 minutes between 6th Ave and Marine Way, which seemed like two routes confirming each other. It turned out that stop is just the last one for both of them.

### Bridges

Bridges show up as places where buses gain time, meaning the timetable gives them more time than they need. Both the Lions Gate and Burrard bridges are padded for the evening peak direction, which is out of downtown. These numbers are for the stretch between the stops on either side of the bridge, so they include a bit more than the bridge itself. For Lions Gate, the W Georgia @ Denman to Marine Dr stretch also covers the Stanley Park Causeway.

On Lions Gate, buses on routes 240, 241, 246 and 250 heading out of downtown reach the bridge 5 to 9 minutes late and come out the other side anywhere from about 3 minutes early to 2½ minutes late. So the extra time is doing its job. Going into downtown it's different. Buses come off the bridge 4 to 6 minutes early.

Burrard shows the same pattern on Route 2, just smaller. Heading out of downtown, a late bus catches up (+200 s before the bridge, +83 s after). Heading in, it's already early before the bridge and gets even earlier (-84 s to -177 s). The ordinary stretch on Cornwall right next to it only changes by 13 s. I first noticed this in week one on a single bus (-129 s over the bridge), and now it holds over 91 and 104 trips.

Being early isn't harmless. If a bus reaches a stop 4 minutes ahead of the timetable and doesn't wait, anyone who planned around the timetable misses it. I think the into-downtown timetable could probably be tightened on weekday evenings, but that's based on 3 evenings.

### Time of day

Across the whole network, the evening peak is pretty mild for a typical bus. The median goes from 58 s at 4 PM to 83 s at 5 PM and 82 s at 6 PM, so it's only about 25 s worse. The bad trips feel it more. The 90th percentile climbs from 422 s at 4 PM to 502 s at 6 PM, and it's still 477 s at 7 PM. The on-time rate barely moves (49 to 53% all evening). All 3 days have the same shape, lowest at 4 PM and highest at 5 or 6 PM.

One thing I can't explain yet is that 3:30 to 4 PM is a bit later than 4 to 5 PM on every day (a 72 s median vs 58 s). I had two ideas: school dismissal around 3 PM, or the timetable switching to longer peak running times at 4 PM. A bit more than half the routes improve at 4 PM (91 of 158), but only by a typical 9 s. Most of the network-wide drop comes from about 30 routes, many of them suburban (Delbrook, Rocklin, Steveston, South Delta). That points more toward something route-specific, like schools, than a network-wide timetable change. I haven't checked which routes serve schools, though, so it's still open.

### Data and limitations

I collected TransLink's GTFS-Realtime trip updates from Sept 28 to Nov 19, 2026, on my laptop. The first week was testing, before I added the collection window and the daily cap, so the hours were all over the place and a few days went over 1,000 requests. After that I collected weekday evenings from 3:30 to 7:25 PM every 15 seconds. That's 940 requests a day, under TransLink's limit of 1,000. In total there are 11,364 snapshots and 1,894,709 arrival rows (one per bus, per stop, per day).

An arrival counts as trusted when the last prediction I saw was made within 60 seconds of the arrival. Inside the analysis window, 95.3% of arrivals are trusted. It's lower over whole days, because buses still on the road when collection stops have stops I never saw up close.

A day goes into the analysis if it's a weekday on the regular weekday schedule, covers at least 90% of the 3:30 to 7:25 PM window, and has no gap longer than 10 minutes. I checked 7 weekday evenings and 3 passed:

- Sep 30 was a holiday (Truth and Reconciliation Day) and TransLink ran the Sunday schedule.
- Oct 1 and Oct 6 have 32- and 37-minute gaps right in the peak.
- Oct 21 only starts at 6:16 PM.

The decisions are stored in a table (`analytics.analysis_days`) with a reason for each day.

Known limitations:

- 3 evenings is a small sample. One bad day (weather or an incident) can still move the results, so they're preliminary.
- The laptop collected nothing while it was asleep, which is why there's no data from Oct 22 to Nov 18.
- On some days up to 14% of polls got a snapshot TransLink hadn't updated yet (on Nov 19, 123 of about 893). These are skipped as duplicates.
- Cancelled trips are left out. A trip that gets cancelled after some of its stops were already recorded isn't handled yet.
- "Delay" means the last prediction before the bus reached the stop, not a measured arrival. For trusted rows, that prediction was made within a minute of the arrival.
- The trusted filter doesn't catch every bad prediction. "Trusted" only means the last prediction was made close to the arrival, not that it's definitely right. The route 14 row above passed it.
