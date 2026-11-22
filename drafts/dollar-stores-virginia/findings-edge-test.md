# Edge-of-town test: Marion, South Hill, Chase City

Research draft made with Claude, November 21, 2026. Three towns chosen to test the measure,
not as a sample. Ten Dollar General stores, one Family Dollar and two Dollar Tree stores sit
within 8 km of these three towns' limits. Nothing here is a finding about Virginia.

## What the maps show

- Six of the ten Dollar General stores sit inside the built-up area on the loose edge (score
  A at or below 1). Four sit far beyond it (A from 3.1 to 6.0), on US and state routes 8 to
  9 km from the town's center. One of them, on Lee Highway east of Marion, is off the map's
  16 km square. None falls in the fringe band from 1 to 2.
- Supermarkets and pharmacies are all inside the town limits. Convenience stores spread out
  more like the Dollar General stores: 8 inside the loose edge, 5 in the fringe, 9 beyond.
- So in these towns the picture is "in town, or out on the road between towns". The edge
  itself is empty. Twenty towns will say whether that holds.

## What the test says about the measures

1. **Strict edge (425 homes per sq mi) fails in Marion.** Its built-up piece is 5.2 km2 and
   leaves out the North Main Street strip, so Food City, Food Lion, Ingles, Walmart and CVS
   all score 2.8 to 5.2, "beyond the edge". Homes thin out where shops begin; a housing-only
   edge calls every commercial strip "outside town".
2. **Loose edge (200 homes per sq mi) reads right in all three.** Marion's strip falls inside
   (groceries 0.4 to 0.6). South Hill's I-85 interchange cluster (Walmart, Dollar Tree)
   still scores 1.4 to 1.5, which matches how it looks on the ground: a highway cluster just
   outside the old town.
3. **The Census itself adds commercial land.** Its 2020 urban areas start from blocks with
   425 homes per square mile or 20 percent impervious cover, then fill with blocks at 200.
   Adding impervious cover (NLCD, public domain) to the loose edge would bring commercial
   strips in by the Census's own rule. Recommended.
4. **Measure B is clear on a map but coarse.** It sorts stores into inside the limits (5 of
   10 Dollar General), urban area outside the limits (2), and outside both (3). Chase City
   (2,053 people) has no urban area at all, so B is only "inside or outside the limits"
   there. Virginia's limits also include empty land: South Hill's limits are 25.6 km2 around
   a 9.9 km2 built-up area.
5. **The random-road comparison needs a tighter window.** Over the full 8 km square, 80
   percent of main-road frontage scores beyond 2, so the comparison mostly says "stores are
   in towns". To test edge against center, the next run compares within score 3 of each
   town, and gives the "between towns" stores their own class.
6. **Data checks.** Every Dollar General, Family Dollar and Dollar Tree mapped in
   OpenStreetMap here lies within 76 m of its SNAP point, except one at 448 m in South Hill
   (to check). OSM has 7 of the 13 chain stores; SNAP stays the primary source.

## Proposal

Lead with A on the loose edge plus impervious cover, drawn as a blue built-up outline. Draw
the town limits as the black line (B) on every map. Report three classes in the charts: in
town (A at or below 1), fringe (1 to 2), between towns (above 2).

## Sources

- Stores: USDA FNS, SNAP Retailer Locator historical data 2005-2025, stores with no end date.
- Census 2020 blocks (housing units, population, land area); TIGER/Line 2024 places; 2020
  urban areas.
- Thresholds: Census Bureau, "Redefining Urban Areas following the 2020 Census" (December
  2022): 425 housing units per square mile for the initial core, 200 to fill in the rest.
  Impervious-surface rule: 2020 criteria as summarized by the Census Bureau's state data
  center presentations; the Federal Register notice (87 FR 16706, March 24, 2022) to be
  opened before publication.
- Roads and the OSM store check: © OpenStreetMap contributors (ODbL), Overpass API, data as
  of 2026-11-21 16:28-16:30 UTC.
