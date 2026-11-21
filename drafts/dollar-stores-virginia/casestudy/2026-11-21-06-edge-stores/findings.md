# Why are the edge stores where they are? (November 21, 12:40-12:59)

Research draft made with Claude. The reasons and their tests were written first, in
`hypotheses.md` (12:45). Every number below was read back from `data/`.

## Scope

- Every Virginia town and city was scored: 227 places.
- 23 places are joined to larger urban areas and left out.
- Within 8 km of the other 204, there are 359 Dollar General stores, as follows:

| Where | Dollar General stores |
|---|---|
| In town | 264 |
| At the edge (score 1 to 2) | 34 |
| In another named place | 20 |
| Between places | 41 |

- That covers 359 of the 505 Virginia Dollar General stores in SNAP. The rest are more than
  8 km from any town or city's limits.
- **The edge is a small share.** The edge band holds 11 percent of Dollar General stores near
  a town (34 of 311 within score 3). Random main-road frontage falls there 25 percent of the
  time. Dollar General is still more often at the edge than supermarkets (4 percent), Family
  Dollar (3 percent) or chain pharmacies (1 percent).
- Following Chris's direction, the rest of this note is about the 34.

## The reasons, as tested

Each reason compares the 34 edge Dollar General stores with 1,920 random points on main roads
in the same edge band of the same towns.

| Reason | Edge Dollar General | Random sites | Result |
|---|---|---|---|
| Within 250 m of a junction of two US or state routes | 7 of 34 (21%) | 5% | more often, about four times |
| On a US or state route that crosses the town's edge | 13 of 34 (38%) | 24% | more often, just |
| Outside the town's legal limits | 22 of 34 (65%) | 86% | less often |
| Site under 10% paved in 2001 and 20%+ in 2021 | 1 of 34 | 2% | can't tell |
| Share of people within 5 km by road who live outside town | 55% | 53% | can't tell |
| Opposite side of town from the nearest supermarket | 6 of 34 (18%) | 25% | can't tell |
| Authorized for SNAP after 2005 | 25 of 34 (74%) | in-town stores: 122 of 264 (46%) | newer |

- **The sensitivity band 0.75 to 2** (88 stores) gives the same verdicts: crossroads 22
  percent against 6, road into town 36 percent against 27, outside the limits 49 percent
  against 76.

## Towns and cities behave differently

This split was not in the hypotheses. Treat it as a lead to confirm.

| | Edge Dollar General | Junction | Road into town | Outside limits |
|---|---|---|---|---|
| In towns | 18 | 33% (random 7%) | 56% (random 30%) | 39% (random 82%) |
| In cities | 16 | 6% (random 2%) | 19% (random 14%) | 94% (random 91%) |

- **Towns.** The edge Dollar General stores sit on the main road into town, at the crossroads,
  and mostly just inside the town line.
- **Cities.** A city's edge is suburban frontage, and the stores there look like any other
  site on it.

## What this says, and what it cannot

- **The town edge.** In towns, the edge store is where the main roads meet as you come in,
  and usually still inside the town.
- **Cheap land.** Being outside the limits is not the pattern. That argues against "cheaper
  county land beyond the town line", but it does not prove anything about land prices,
  which are not in the data.
- **What being inside the limits might mean.** It could reflect town water and sewer, town
  zoning or annexation. None of these is in the data yet. Town water and sewer service areas
  would be the next source to find.
- **Built on open land.** The test cannot tell. The SNAP points sit on or near the road, so the
  3 x 3 pixels around them were already partly paved in 2001: the median edge site was 36
  percent paved in 2001, against 12 percent for random points. A parcel-level look (building
  footprints with dates) would be needed.
- **Intent.** Nothing here says why a company chose a site.

## Fixes and rounds

- **features.py, run 1.** 10 of 48 chain stores had no one within 5 km. They had snapped to
  stray fragments of road. Fixed by snapping to the main connected network only, and rerun.
  The run-1 file is kept as `data/edge_points-run1-snapping-bug.csv`.
- **Gallery.**
  - r1 showed matplotlib's "Easting/Northing" axis labels on every tile.
  - r2 removed them.
- **Reasons chart.**
  - r1's title said "Cheaper land outside the limits, no sign of it", which the data cannot
    say.
  - r2's title states the junction result and store age. The "road into town" result is
    marked "just".
