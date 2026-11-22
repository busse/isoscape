# Final-draft inspection: viz-dollar-stores-virginia-poster 1.0.0-rc1

Saved by the making session from the inspector's returned text (its Write was refused for
subagents), November 22, 2026. The text below is the inspector's, unchanged except this note.

- **Inspector.** Independent Fable agent (Claude Fable 5.2). It did not make the poster.
- **Date.** November 22, 2026. Commit 6ffef55, branch viz/dollar-stores-virginia.
- **Print file.** `dollar-stores-virginia-poster-1.0.0-rc1.pdf`, 24 x 36 in. Looked at on
  `rc1-150dpi.png` (3600 x 5400 px): the whole sheet at 1,500 px across (`whole-1500.png`), then
  15 tiles of 1200 x 1080 px at 100%.
- **Checklist.** README "The final-draft inspection".
  - Item 5 (plate block) skipped: the poster is not for sale and has no plate or title block.
  - `accepted_faults` is empty.
  - Nothing from "Known limits" is reported.
- **Nothing was edited.** Only the crops were written.

## Verdict: fix

One A finding and five C findings block release. All are small text or label changes; none
needs a new calculation.

## Findings

Pixel boxes are x0, y0, x1, y1 on the 150 dpi raster.

| Grade | Box | Finding | Crop |
|---|---|---|---|
| A | 2535, 150, 3450, 600 | Locator: region numbers 2 and 4 sit outside Virginia (2 in the blank where West Virginia would be, 4 above Maryland), and 1 sits on the state line. Seen on the whole-sheet view. The step 15 log says the numbers were moved inside their regions; they are not. | `A1-locator-numbers.png` |
| C | 150, 4620, 1140, 4800 | Chart 1 note: "about 33% of those within twice the distance to the edge". Test C5 is run on stores within three times the edge distance (A at or below 3; 1,575 stores, 234 in the band = 15%, 517.6 expected = 33%). Within twice the distance there are 1,432 stores and the share would be 16%. "Twice" should be "three times". | `C1-chart1-note-twice.png` |
| C | 150, 5020, 1500, 5210 | "A separate review, also run with Claude, redid every calculation from scratch." Overstated. `fable-check.md` says the checker recomputed the primary test table from the row-level data (`points.csv.gz`, the features the first run had already measured) and rebuilt the junction distances for the primary places. It did not redo the edge measurement, the road matching or the traffic ranks, its tie-break gave 232 edge stores against the 234 printed, and the poster's own numbers (2,078, 1,198, 183, 463, 50%, the Virginia grid) were computed after it finished. Suggested: "A separate review, also run with Claude, recomputed the main test results with its own code." | `C2-redid-every-calculation.png` |
| C | 3067, 1040, 3450, 1512; 1900, 2135, 2283, 2607; 150, 2682, 533, 3154; 3067, 2682, 3450, 3154; 150, 3230, 533, 3702 | Five captions say "no traffic count" (Independence, North Shore, Amherst, Lake of the Woods, New Baltimore). The source says something narrower: no HPMS section lies within 60 m of the store's point. Each tile draws a counted road at or beside the square: US 58 at 126 m (7,791), VA 122 at 65 m (11,769), US 29 Business at 76 m (5,156), VA 3 at 257 m (14,040), Route 600 at 198 m (3,225). The caption reads as "the road has no count", and the map contradicts it. Suggested: "set back from the counted road" or "no count within 200 ft". | `C3-no-traffic-count-*.png` (5) |
| C | 1317, 2135, 1700, 2607 | Union Hall: "905 vehicles a day · busiest road in". The 905 is Route 942, the nearest section (3 m). The store is at the corner with Route 616, 37 m away, which carries 6,025 and is drawn heavier on the same tile. "Busiest road in" beside 905, with a busier road at the same corner, reads as wrong. Check which road ranks first here and print that road's count, or drop the rank on this tile. | `C4-union-hall-905.png` |
| C | 1850, 5020, 3460, 5210 | "Things like zoning and water and sewer lines would matter, and neither is included." No source says they would matter. `findings.md` lists "whether zoning or water and sewer matter" under not measured. Suggested: "Zoning and water and sewer lines may matter. Neither is in the data." | `C5-would-matter.png` |
| B | 733, 1030, 1320, 1140 (example; 17 tiles) | Caption phrase "busiest road in" and "2nd-busiest road in" reads as a sentence cut off before a place name. Suggested: "busiest road into town". Honaker's and Hillsville's captions also run about 0.6 in past their tile's right edge (no collision). | `B1-busiest-road-in-caption.png` |
| B | 1290, 4230, 2450, 4600 | Chart 2: each row's label sits closer to the marks of the row above than to its own; the first row's open circle nearly touches the second label. | `B2-chart2-crowding.png` |
| B | 2484, 2682, 2867, 3154 | Mineral: the town arrow is drawn over the other-dollar-store square and the grocery diamond. Lake of the Woods: a grocery diamond is hidden under the store square (3067, 2682, 3450, 3154). Honaker: arrow touches the other store's square. | `B3-markers-under-arrow-mineral.png` |
| B | 150, 5035, 1000, 5075 | "the spot where most of a town's people live". The center is the population-weighted mean of 2020 block centroids (`measure.py`), which is the average position of residents. Suggested: "the middle of where a town's people live". | `C2-redid-every-calculation.png` (same paragraph) |
| B | 150, 470, 3320, 830 | Deck: "Those 234 tend to be on the busier roads coming in." Supported by C6 (1.3 times the traffic) and by C1 on the frozen test (39% against 32%). The record calls C1 "not robust" (fails three sensitivity checks) and `findings.md` lists "on the busiest road in" as not supported as a headline. The deck leads the argument with it and chart 2's second row shows it without that caution. Not wrong as printed; consider leading with the junction result. | `B5-deck.png` |
| B | 150, 5120, 1490, 5200 | "'Small town' here means an incorporated place with fewer than 25,000 people." The rule also requires that the place is not joined to a larger urban area (plan v2, Units). That rule is why four Virginia edge stores (Chamberlayne, Bensley, Innsbrook, Fort Lee) are not in the grid that says "every". Suggested: add "that is not part of a bigger urban area". | `C2-redid-every-calculation.png` (same paragraph) |
| B | 150, 4715, 1125, 4790 | Filler: "The edge actually has fewer Dollar Generals than chance would give it." Drop "actually". Also "Things like" in the right-hand paragraph. | `C1-chart1-note-twice.png` |
| B | 1850, 5160, 2780, 5200 | Contrast pattern: "A yellow square marks a location only. It is not a judgment of any store or town." Suggested: "A yellow square says where a store is and nothing about the store or the town." | `C5-would-matter.png` |
| B | 2490, 4650, 3460, 4800 | "the records only go back to 2005". `sources.md` says the file starts in 2005, but 80 of the 4,628 Dollar General rows carry authorization years 2000 to 2003 and 1,204 carry 2004. Suggested: "the file starts in 2005". | `B8-snap-note.png` |

B count: 9.

## Item 4, text size

Sizes are true points at 24 x 36 in (from `poster.py`):

- Tile captions: 7.6 pt.
- Sources line: 9 pt.
- Region bars: 9.5 pt.
- Locator key: 10 pt.
- Axis labels: 10.5 pt.
- Notes: 11 pt and up.

Nothing is under 6 pt. Pass.

## Item 3, arm's length

Apart from the locator numbers, nothing at arm's length:

- No text cut off and no overlapping blocks.
- No blank patch or stray mark.
- No misspelling found.
- The 30 tiles, legend, three charts and two bottom paragraphs sit clear of each other.

## Writing rules

- American English throughout.
- No em dashes, rule-of-three lists or colon punchlines.
- One contrast pattern and two fillers, listed above as B.
- The copy otherwise reads plainly. The phrases that still sound machine-written are the
  two-sentence disclaimer ("marks a location only. It is not...") and "Only 15% did."

## Facts checked

Recomputed from `conf_all/tests.csv`, `dg_classes.csv` and `stores_dedup.csv.gz` unless another
source is named. Every fact was checked; the exceptions are the findings above (Union Hall's
traffic, the five "no traffic count" captions, "within twice", "redid every calculation",
"would matter") and the B notes on C1's fragility, the joined rule, the center's wording and
"the records only go back to 2005".

Two record notes:

- `findings.md` says "462" and "about 180", from the first run's class file. The case-study
  copy of `dg_classes.csv` was replaced with the stable-tie file during this inspection and now
  matches.
- `sources.md` logs the Virginia downloads; the six states' block, place, HPMS, NLCD and OSM
  downloads are not listed there.
