# Richmond's floods over time: outline of the editorial

Draft 1, November 25, 2026. Drafted with Claude (Opus 5.5) for Chris Busse from the series' research
and its final-draft (rc3) renders. Stage: outline and first full draft together, at the owner's
request ("Move the content work forward and let me defer the publication shape until I read the
editorial"). Nothing here is published; the page is `unlisted: true`.

**Reader.** Someone who has never heard of any of this, and someone who lived through Agnes or
Gaston, or knows the hydrology. The first should finish knowing why the same blocks flooded again
and again, what the wall changed and what happened in 2004; the second should find nothing careless.

**Voice.** The house story voice (Jackson Ward, redlining): plain, measured, every fact cited
inline to a Sources entry. People died in these floods; the page says so where the sources do,
with numbers and places, and no more.

## Sections, their argument and their pictures

| # | Section | Argument (one or two sentences) | Pictures |
|---|---|---|---|
| 0 | Title, deck, hero, About notice | The page opens on a map: the 1972 flood with a divider to the same city dry. The About notice says who made it and how, as the house notice does. | Fig. 1, compare: 1972 plate and its dry twin |
| 1 | The answer (lede, no heading) | The James flooded the same low ground from 1771 to 1985; since 1994 a wall has kept the river out of Shockoe Bottom and the Manchester flats; on August 30, 2004 the Bottom flooded from rain while the river stayed low. One paragraph says what the drawings are: water at one surveyed height on today's lidar ground, on the city of each year. | none |
| 2 | How to read the drawings | One close picture carries the whole key: the blue-grey by depth, the river's own light blue, the depth gauge, cream buildings of the year, grey dashed ones not ascertained, the hatch for a range, the dry twin. | Fig. 2, the 17th Street Market box, 1972 |
| 3 | Why Shockoe Bottom and the Manchester flats flood | The Bottom is the valley of a creek now buried in a pipe, opening onto the James where the river is tidal and nearly level below the falls; one height per flood serves the whole reach. The levels table. The strip shows the same blocks in every flood. | Fig. 3, the market box in eight plates; table of levels and counts |
| 4 | 1771, as an estimate | The highest flood on record rests on diary accounts of a stage on a gauge that did not yet exist; drawn at about 38 ft with a hatch, on today's ground, with the six buildings of the town of about 1788 the history can place. | Fig. 4, 1771 plate |
| 5 | March 1936 | The first flood here with surveyed marks; industrial and business sections flooded. | Fig. 5, 1936 plate |
| 6 | Camille, August 1969 | The best mapped flood (USGS HA-410): its water up the valley to about Main Street Station and across the Manchester flats. | Fig. 6, 1969 plate |
| 7 | Agnes, June 1972 | The record of the gauge era, 35.5 ft; the sign at Dock and Pear; what the city lost; 226 of 1,173 buildings shown standing in water, and what "shown" means. | Fig. 7, compare: 17th and Dock flooded and dry |
| 8 | November 1985 | Third highest at the Locks; the next year Congress authorized the wall. An earlier creek-mouth levee existed and is not drawn. | Fig. 8, 1985 plate |
| 9 | The floodwall | Who built it, when, for how much, where it runs, what it protects (750 acres), its 19 closures, the 41 ft overtopping stage; its surveyed top is not public. A divider shows the 1972 height on the 1972 city and on today's city behind the wall. | Fig. 9, compare: 1972 plate and the 1972 height on today's city |
| 10 | The wall's tests, Fran 1996 and November 2020 | The highest water since the wall stood about 18 ft below the overtopping stage; which gates closed, as far as news and the city record. | Figs. 10 and 11, the 1996 and 2020 plates |
| 11 | Manchester at the 1972 height | Without the wall 527 acres and 246 of 412 buildings would stand in water at the 1972 height; with it, 41.5 acres outside the wall, plus 212.8 acres whose protection the data cannot show. | Fig. 12, compare: with the wall and without it |
| 12 | August 30, 2004 | The rain: about 10 inches on the 12 square miles that drain to the Bottom, most between 2 and 9 p.m.; the gates open, the James low; the bowl and its spill level from our own lidar test; depths are reports, so the drawing shows a middle figure with a hatch; eight deaths in the Richmond area; the lawsuit in one neutral sentence; what was built after. | Fig. 13 Gaston plate; Fig. 14 rain map; Fig. 15 rain by hour; Fig. 16 the bowl explainer; Fig. 17 the market close up |
| 13 | What the drawings cannot show | Plain limits: no flow or timing; levels at one gauge carried level; the wall's top; the Manchester levee; buildings not ascertained; the old creek-mouth levee; the Mayo Bridge rise; Gaston's depths. | none |
| 14 | How this page was made | Drawn by Chris with isoscape, built with Claude; text drafted with Claude; the independent inspection and fact check of the sheets as plain fact; no outside review. | none |
| 15 | Corrections and changes; Sources | House pattern. Sources as H4 entries, each with URL or file and page and the date read. | none |

## Pictures

All are crops or compositions of the rc3 renders (`figures.py`): plates rendered from their SVGs in
one shared frame per area so compare pairs align, box crops round `tools/floods/d3/boxes.json`
boxes, the market strip across eight plates, the rain panel cropped from the rc3 Gaston sheet, the
rain branch's plan map (its working title cut off, since it named the storm by its peak strength)
and its explainer.

Pictures I wish existed (none made):
- A section along 17th Street from Franklin to the river, water against building heights, for
  1972 and 2004 (the d1 notes name `src/section.ts`; it would be the truest picture of depth).
- A photograph pair: the Dock and Pear high-water sign beside the 1972 plate's water at that spot.
- The 1969 USGS mapped extent (HA-410) traced over the 1969 plate, to show where the bathtub
  fill and the surveyed extent agree and differ.
- The Manchester flats on a period city (no traces exist south of the river).

## Open questions for the owner (with recommendations)

1. **Title.** Three in `three-titles.md`. Recommend the first.
2. **The hero.** The 1972 compare at the top (recommended) or the Gaston plate. Agnes is the flood
   most readers have heard of and the one the wall answers.
3. **The earlier creek-mouth levee.** FEMA's study says a levee at Shockoe Creek's mouth gave
   limited protection before the wall, was overtopped in 1972 and lost its pumping in 1969. The
   plates for 1936, 1969 and 1985 do not draw it (its line, height and date are not in our
   sources). Recommend the caveat as written now, and a research item to find it before
   publication.
4. **Outside review.** You said on November 23 you would not engage third parties for this. The
   page says no outside review was done. Recommend keeping that sentence and, if you later want
   one, people from Shockoe Bottom's businesses and Manchester, and a hydrologist.
5. **The 2009 lawsuit.** One neutral sentence (what was alleged; no outcome found). Recommend
   keeping it: readers who were there will know of it, and leaving it out would read as avoiding it.
