# Replication plan, v2 (after the independent review), frozen before any held-out place is read

- **v1.** Frozen at 15:58. Kept as `plan-v1-as-frozen.md`.
- **The review.** An independent Fable agent reviewed v1 (`fable-review.md`) and found the
  plan "not ready to run as frozen".
- **v2.** Written with Claude at 16:15, adopting every must-fix and turning the should-fixes
  into stated sensitivity checks.
- **Held out.** At 16:15 no held-out result had been read. The Virginia CDPs were being
  scored; no other state had been scored.

## Data held out from discovery

- **Discovery.** Virginia's 227 incorporated places.
- **Held out, set A.** Virginia's 461 CDPs.
- **Held out, set B.** North Carolina, Tennessee, Kentucky, West Virginia, Maryland and South
  Carolina: every incorporated place and every CDP.
- **Assignment.** Stores are pooled across everything and counted once, at the place where
  their score A is lowest.
  - A store whose lowest-A place is a Virginia incorporated place belongs to discovery. It is
    never counted as held out.
  - A store within 8 km of any Virginia incorporated place is excluded from set B (M7).

## Units

- **Small incorporated place (the confirmatory unit).**
  - Incorporated (TIGER FUNCSTAT A).
  - Under 25,000 people inside its limits in 2020.
  - Not joined to a larger urban area (5 times its limits and over 30 km²).
- **Large incorporated place.** 25,000 or more people. A comparison only.
- **CDP.** Reported as its own class. CDPs have no legal limits, so C3 does not apply.
- **Sensitivities.**
  - Under 10,000 people. That threshold was picked while looking at Virginia, which is why it
    is only a sensitivity (M1).
  - Places whose center lies in a 2020 urban area of 50,000 or more that they do not
    dominate (S5).

## Measures (fixed)

- **Score A.** The lead edge: 200 or more homes per square mile, or 20 percent or more non-road
  impervious cover, closed over 400 m. The tiny-town rule applies. The window is 8 km.
- **Margin.** A store or random point within 30 m of the built-up edge line is in neither
  the town nor the band (M5).
- **Edge band.** A from 1 to 2, outside the 30 m margin.
- **Crossing roads (C1).**
  - An HPMS 2024 section crosses the edge only if it has length both inside the built-up area
    shrunk by 30 m and outside it grown by 30 m (M5).
  - A road is identified by route signing plus route number, or by its name when there is no
    number (S4).
  - Each road is ranked by its highest AADT at a crossing.
- **Store to road.** Each store or random point takes the nearest HPMS section within 60 m.
- **Junction (C2).** A node where ways carrying two or more different route numbers meet, with
  network degree 3 or more, within 250 m (M4). Only the route numbers below count, as
  tabulated from OSM before the run:

| State | Counts | Does not count |
|---|---|---|
| Virginia | I, US, VA | SR (secondary routes 600 and up) |
| North Carolina | I, US, NC | SR (secondary roads) |
| Tennessee | I, US, TN, SR | (OSM tags many Tennessee state routes "SR n"; these are state routes, not county roads) |
| Kentucky | I, US, KY numbered under 1000 | KY 1000 and up (rural secondary system) |
| West Virginia | I, US, WV | CR (county routes) |
| Maryland | I, US, MD | |
| South Carolina | I, US, SC | S- (secondary) |

  The rule follows the state of the way's place. For neighboring states' route numbers in
  border windows, the same rule applies by their prefix.

## Tests (the place-conditional form, M3)

- **Per store.**
  - x_i = 1 if the store meets the claim, 0 if not.
  - p_i = the share of *all* random main-road points (null.csv) in the same place's edge band,
    outside the margin, that meet the claim.
- **Statistic.** D = mean(x_i − p_i) over the edge Dollar General stores of the unit.
- **Interval.** 95 percent, by cluster bootstrap over places (10,000 resamples, seed
  20261121).
- **Verdict.** "Holds" if the interval is above 0. "Against" if below 0. Otherwise the data
  cannot tell.

| # | Claim | x_i | Direction |
|---|---|---|---|
| C1 | On one of the two busiest roads crossing into town | matched section's road ranks 1 or 2 | D > 0 |
| C2 | Near a junction of numbered state or US routes | within 250 m | D > 0 |
| C3 | Inside the town's legal limits | inside (incorporated only) | D > 0 |
| C4 | Newer than in-town stores | authorized after 2005; compared with in-town Dollar General stores of the same unit, cluster bootstrap of the difference in shares | edge > in town |
| C5 | The edge is not crowded | among Dollar General stores with A at or below 3, share in the band, against the random share; cluster bootstrap. Must give the same verdict on the lead edge and the loose edge (homes only) (M6) | D < 0 |
| C6 | The road past is busier | log AADT of the store minus the place's mean log AADT of band random points; cluster bootstrap | D > 0 |

- **Primary.** C1 and C2 must both hold for "the road in" to be the line.
- **C1 is fragile.** Virginia's own C1, recut this way, does not clear: 13 against 8.7
  expected, interval −0.01 to +0.45 (review). C1 may fail on held-out data.
- **Comparison stated in advance (S7).** The same C1, C2 and C6 for edge convenience stores.
  If convenience stores show the same, the finding is "edge retail on the road in", not
  something particular to Dollar General.

## Wording gates (M2)

- **"Most", "usually", "mostly".** Allowed only when the lower end of the stores' own share
  interval (Wilson) is above 50 percent.
- **Otherwise.** The copy says "more often than other sites on the same roads" and gives the
  share.

## Sensitivities (reported, not gates)

- **Geocode error (S1).** Drop stores within 100 m of the edge line. Also the band 0.75 to 2.
- **Road match (S2).** A 100 m match. Match rates by state.
- **Bearing (S3).** p_i from random points in the same A bin (1 to 1.25, 1.25 to 1.5, 1.5 to 2).
- **Crossing side (S4).** C1 using only crossings within 90 degrees of the store's bearing.
- **Metro suburbs (S5).** Exclude the places described under Units.
- **Odd shapes (S6).** Places where the center fell in a gap, or where rays re-enter the
  built-up area, are listed and dropped.

## Discovery recut (Virginia's incorporated places, small-place rule; for reference, not a test)

| | Edge Dollar General | Share | Random | From |
|---|---|---|---|---|
| Under 25,000 | 23 | C1 61%, C2 26%, C3 outside 52% | 40%, 6%, 85% | review (Wilson vs pooled); to be recomputed by the new script before the run |

## What decides the line

- **C1 and C2 both hold on set B:** "the road in", worded by the gates.
- **Only C2 holds:** "near a junction, more often than other sites". C1 is dropped.
- **Neither holds:** line 2 ("it's the drive, not the map") leads, if C5 holds on both edges.
- **Set A (Virginia CDPs) disagrees with set B:** the poster says which kind of place the
  finding is about.
