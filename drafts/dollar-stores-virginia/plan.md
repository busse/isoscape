# Plan: why does it seem there's a Dollar General on the edge of town? (Virginia)

Drafted with Claude, November 21, 2026. Stage: research. For Chris to review before any build.

## 1. Data we can get

| Need | Source | Checked today | License |
|---|---|---|---|
| Store points, three chains, with authorization dates | USDA SNAP Retailer Locator historical file, 2005-2025 | Downloaded. 505 Dollar General, 208 Family Dollar, 200 Dollar Tree active in VA | Public domain |
| Comparison retail (supermarkets, grocery, pharmacies that take SNAP, convenience/gas) | Same file, by store type | Yes, 901 supermarkets, 819 super stores, 9,285 convenience | Public domain |
| Cross-check of store points; roads; buildings | OpenStreetMap (Geofabrik VA extract) | Overpass busy today | ODbL, credit OSM |
| Town limits, CDPs, urban areas | Census TIGER/Line 2024 places, 2020 Urban Areas | Server reachable | Public domain |
| Town population | Census Vintage 2024 estimates | Downloaded: 189 towns, 38 cities | Public domain |
| Income, poverty, no-car households, density | ACS 2020-2024 5-year, block group (bulk files) | API needs a free key; bulk files do not | Public domain |
| Rural/urban class | USDA RUCA codes; Food Access Research Atlas | Not yet | Public domain |
| Traffic on approach roads | VDOT traffic volume (ADT) | Fields fine | Restricted: "official business of the Commonwealth". Analysis only until VDOT says yes |
| Land cost | VGIN parcels: outlines only. Values per locality | Outlines only | Proxy: distance to center and lot size. Weak, and said so |
| Company's own words | DG 10-K FY2024 and 2025 annual report | Planning session's figures (499 VA stores) agree with SNAP's 505 | Quoted once, cited |

## 2. Measuring "edge of town"

Lead measure (A), **relative radius**: center = population-weighted center of the town's 2020
blocks. Edge = where building density falls below a set threshold along the bearing to the
store (Census urban area or OSM/Microsoft buildings). Score = store distance / edge distance.
0 is the center, 1 the edge, above 1 outside.

Second label (B), **legal and census lines**: inside or outside incorporated limits, and inside
or outside the 2020 urban area. Easy to read on a map.

Optional (C), **along the approach road**: network distance from the center on the nearest
US or state route.

Comparison: the same score for supermarkets, pharmacies and convenience stores in the same
towns, and for a null model of random points on primary/secondary road frontage within 2x
the edge radius. The poster's claim is the difference between these, with an interval.

## 3. Towns for the grid (by rule)

Pool: Virginia's 189 incorporated towns and 38 independent cities, plus the largest CDPs
used as county seats. Strata: 5 regions (Southwest, Valley, Southside, Northern Neck +
Eastern Shore + Middle Peninsula, urban crescent) x 4 size bands (under 1k, 1k-2.5k,
2.5k-10k, 10k-50k). One seeded random draw per cell gives 20. A town with no dollar store
stays in and is drawn empty. The rule and seed print on the poster.

Illustrative only, the draw replaces it: Pennington Gap, Marion, Chilhowie (SW); Luray,
Woodstock, Elkton (Valley); South Hill, Chase City, Blackstone (Southside); Warsaw, Exmore,
Tappahannock (NN/ES); Ashland, Smithfield, Warrenton (crescent).

All of Virginia goes in a second panel: every store as a dot on its score.

## 4. Rough poster layouts (24 x 36 in, portrait)

```
A  GRID-FIRST            B  ISO HERO + GRID        C  ARGUMENT COLUMN
+-------------------+    +-------------------+    +-------------------+
| TITLE / question  |    | TITLE             |    | TITLE      |  1   |
+---+---+---+---+---+    |  [isometric hero  |    +------------+ is it|
|   |   |   |   |   |    |   one town, its   |    | 4x4 grid   | true?|
+---+---+---+---+---+    |   approach road]  |    | plan view  |------|
|  5 x 4 plan-view  |    +---+---+---+---+---+    |            |  2   |
|  town maps, same  |    | 5 x 3 plan grid   |    |            | vs   |
|  scale, rings at  |    +---+---+---+---+---+    |            | what?|
|  0 / 1 / 2 edge   |    | is it true | vs  |    +------------+------|
+---+---+---+---+---+    | chart      | what|    | VA dots    |  3   |
| charts: 3 across  |    +-----------+-----+    | panel      | why? |
| honesty panel     |    | why charts|honest|   | honesty    |      |
+-------------------+    +-------------------+    +-------------------+
```

Marks: a yellow square with a black border for Dollar General, a yellow circle and a yellow
triangle for the other two chains, each named in the legend. No logos.

## 5. Estimate (unit: one agent session on one line of work)

Data assembly 1-2; edge measure on 3 test towns 1; full analysis and null model 2;
grid maps 2-3; charts 1-2; poster rough draft 1-2; explorer page 1-2; fact check 1.
Total about 10-15 sessions. Actuals go in effort.md.

## 6. Decisions (Chris, November 21, 2026)

- Chains: Dollar General, Family Dollar and Dollar Tree, shown apart.
- Edge of town: test measures A and B on three real towns first; Chris picks after seeing them.
- Two versions: an "editorial reporting" poster (layout A, grid of plan-view maps first, with
  the charts and honesty panel) and a "simplified artistic" version, denser, with fewer and
  coarser elements per town.
- Still open: grid count for each version, poster size and whether either is for the shop,
  change over time.
