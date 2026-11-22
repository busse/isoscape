# The editorial 20: first full pass (November 21, 12:02-12:26)

Research draft made with Claude. Counts are from the tables in `data/`; every number below
was read back from them. 16 of the 20 drawn towns stand on their own. Four (Troutville,
Vinton, Dumfries, Fredericksburg) are joined to larger urban areas by the rule below, and are
reported apart.

## The answer so far

- **Dollar General is out of town far more often than a supermarket.** In the 16
  free-standing towns, 10 of 25 Dollar General stores score above 2 (40 percent, 95 percent
  interval 23 to 59). That compares with 11 of 99 supermarkets and groceries (11 percent,
  6 to 19) and 4 of 37 chain pharmacies.
- **It is not piled up at the edge.** Of the 17 Dollar General stores scoring 3 or less,
  3 are in the fringe band from 1 to 2 (18 percent, 6 to 41). Random points on the same
  towns' main roads fall there 31 percent of the time. Supermarkets: 3 of 90.
- **Where the out-of-town stores are.**
  - Five are inside another Census place: Onley, Rich Creek and Pearisburg (towns), and
    Motley and Mappsville (CDPs). These are mostly in-town stores of a neighboring place,
    not stray stores.
  - Five are in no Census place at all. All five were authorized for SNAP from 2016 to 2024.
- **Older stores are in town.** Of the 12 Dollar General stores in town, 8 carry 2004 or 2005
  dates (already authorized when the file begins). This matches Mathews and Middlesex.
- **The pattern so far:** the chain's older stores sit in towns, and its newer stores fill in
  the country between them. "Edge of town" may be how the between-places stores look from a
  car on the road into town.

## Rules added before reading store results

- **Tiny towns.** A town whose built-up area is under 1 km2 takes its legal limits as part of
  its edge. This applies to Scottsburg (127 people), Hallwood and Ivor.
- **Joined towns.** A town whose built-up area is more than 5 times its limits, and over
  30 km2, is joined to a larger urban area and has no edge of its own. This applies to
  Troutville (Roanoke), Vinton (Roanoke), Dumfries (Washington's suburbs) and
  Fredericksburg. Winchester (4.2 times) and Leesburg (3.2 times) stay in.
- **Double counting.** A store seen from two towns' windows is counted once, at its lowest
  score.

## Limits

- 25 Dollar General stores is a small number. The intervals are wide.
- Charlottesville and Leesburg have no Dollar General within their windows.
- **Windows.** Each town's window is 8 km around its limits. A store more than 8 km out is
  not seen from that town.
- **Projection.** All towns are measured in UTM zone 17N. In eastern Virginia that stretches
  distances by under half a percent; scores are ratios, so they hardly move.
- **Roads.** Roads now come from Geofabrik's Virginia extract, because Overpass was at
  capacity. On Chase City the two sources agree (298 and 299 road ways).

## Rounds

- **Contact sheet.**
  - r1: the title collided with the column headers, and Scottsburg's edge had been saved
    before the tiny-town rule applied.
  - r2: both fixed.
- **Pooled chart.**
  - r1: the count labels sat under the random-road ticks, the legend line ran under the
    axis, and the title said "rarely at its edge", which the interval does not support.
  - r2: labels moved to a fixed column, the legend went under the panel title, and the title
    now says "no more often at its edge than road frontage".
