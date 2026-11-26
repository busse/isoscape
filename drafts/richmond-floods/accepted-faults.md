# Richmond's floods over time: accepted faults (final draft rc3, 1.0.0-rc3)

Faults seen only up close (above 100% of the 300 dpi print file, or only when flipping a plate
against its dry twin), accepted under CLAUDE.md "Stages" so later inspections do not report
them again. Each was looked at; its crop is in `accepted-faults/`. Pixel boxes are on the full
print file of the Shockoe Agnes sheet (`richmond-floods-shockoe-1972-1.0.0-rc2.png`,
9600 x 7200; re-verified on the rc2 files, crops `rc2-*`) where the fault falls on it; otherwise the plate and its SVG coordinates are
given (the sheet's `.maps.json` turns SVG units into sheet pixels). Written with Claude,
November 25, 2026; rc2 and rc3 updates the same day (rc3: every grade re-read; item 6 regraded B, close-up only; items 7 and 8 added). Nothing here is in CLAUDE.md "Known limits".

| # | Grade | Where | What | Crop |
|---|---|---|---|---|
| 1 | B | 12 distinct pairs over the Shockoe plates (2 to 4 a plate, 7 on 1936), the same 12 as rc1 (the painted-over check, `tools/floods/d3/occlusion.ts`, re-run on the final rc2 plates) | Something painted over a nearer item, all slivers under about 1.5 mm at print size: traced buildings against traced or today's buildings at sub-meter overlaps (5); a courtyard building's pieces (r20688391/r20688390); two OSM buildings drawn one over the other in the same tone (w1456058032 over r19918536, w266954827 over r11269673), not visible; the rail viaduct w38232584 over Main Street Station's shed w113030476; I-95's ramp over a building's corner (agnes-today); an x-ray band of a traced building on a bridge deck (1936). Manchester: none. | `rc2-01-residual-painted-over-pairs.jpg` (rc1: `01-…`) |
| 2 | B | Shockoe 1996, 2020, Gaston and today's-wall plates: SVG (133.7, 31.2), (669.6, 55.1), (-21.3, 623.5); on the rc2 2020 sheet near (5111, 2341) | Floodwall joints at sharp bends: a piece's top band laps 1.5 to 2.5 m over the next. | `rc2-02-wall-joint-2020.jpg` |
| 3 | B (Chris to decide the threshold) | Every Shockoe plate before 2004; on the rc2 1972 sheet the largest, sanborn-1924-2219, at (4764, 1927), inside box 1 beside the 17th and Main gauge | Traced footprints that today's buildings cover by less than half are drawn (the approved rule leaves out half or more); the larger ones read as a pink roof running under a cream one. 1972: 70 of 322 traced footprints are 5% or more under today's, 39 are 25% or more, 20 are 40% or more. | `rc2-03-traced-partly-under-today-1972.jpg` (rc1: `03-…`) |
| 4 | B | Dry twins (1972: SVG (13.2, -202.9), (9.2, -193.6), (-211.5, 145); rc2 sheet (4832, 1804), (4823, 1826), (4312, 2609)) | A building the water tops is left out of the flood plate (and counted as topped) but drawn on its dry twin: 3 on the 1972 pair, so the twin is not exactly the same city when flipped. | `rc2-04-topped-near-17th-and-main-1972.jpg`; `04-twin-draws-topped-buildings.jpg` |
| 6 | B | Manchester Fran and 2020 sheet, the 2020 panel, a creek mouth at its left edge, (4850, 1650, 5150, 1800) | Where the not-known ground meets a small creek mouth the river's own shore line ends in a short hook about 5 mm long at print size, and the cross-hatch runs over part of the creek's water. | `rc2-06-creek-mouth-hook-2020-panel.jpg` |
| 7 | B | Shockoe 2020 sheet, the falls above the Mayo Bridge, rc3 sheet near (755 to 1449, 2847 to 3309) | Short ink hooks, under about 3 mm at print size, where the shore line of two small islands in the falls meets the water drawn at the river's own surface. Seen only up close; the rc2 recheck lists it as close-up only. | `rc3-07-falls-island-hooks-2020.jpg` |
| 8 | B | Gaston sheet, Dock Street, rc3 sheet (4339 to 5611, 2084 to 2569) | The hatched band's dashed outer edge, traced between 5 m grid nodes, can fall up to one grid cell (about 1.5 mm at print size) on the river side of the wall's foot, where the pool held on the city side meets low ground beyond the wall. No water and no hatch are drawn there. | `rc3-08-gaston-band-edge-at-wall-foot.jpg` |

Item 5 of rc1 (the Mayo Bridge's deck drawn above the 1972 water) is withdrawn: rc2 draws a
deck piece whose middle lies below the flood's level under the water (how-its-made, Floods), and
on 1972 all 18 of its pieces are under. Its old crop stays as `05-mayo-bridge-deck.jpg`.

## Noted, not faults

- **Two counts of buildings in water**: the captions count every building whose corners or
  center lie under the flood, topped ones included (scene stats); the box counts
  (`boxcounts.ts`) count drawn buildings, so a plate's total differs by a few (1972: 226 and
  224). Both are in `counts.json`.
