# Putting back the 1969 to 1972 city: method options

Read-only work, November 24, 2026. Counts come from the `wt-floods` worktree (commit a82a447,
"Floods d1 round four") and its caches; the scripts are in `scripts/`. Sources are in
`sources.md`.

## Why the plates look half empty

A dated scene draws (1) buildings standing today, by the assessor's year built, (2) traced
Sanborn buildings that are gone today, each with a lifespan, and (3) curated items. For the
Shockoe Bottom area of `tools/floods/coverage.ts` (14th to about 25th Street, Broad Street to
the river), the d1 coverage file (`drafts/richmond-floods/casestudy/2026-11-23-26-plates-d1/coverage-by-area.json`)
gives:

| Year | Today's buildings | Traced | Total |
|---|---|---|---|
| 1936 | 121 | 177 | 298 |
| 1969 | 137 | 16 | 153 |
| 1972 | 137 | 16 | 153 |
| 2026 | 268 | 0 | 268 |

The traced count falls from 177 to 16 between 1936 and 1969. That fall is the drop rule, not
the record.

## The current drop rule, exactly

`tools/sanborn/lifespans.py` (`ASSUMED_END = 1960`):

1. A traced footprint covered 50% or more by a building standing today is taken to be that
   building (or its replacement on the same footprint) and is not drawn from the trace.
2. Every other traced footprint is a lost building. It is followed through later editions: a
   later footprint overlapping it by at least half of the smaller one is the same building.
3. Its `from` is the first edition that shows it. Its `to` is the first year it is known gone,
   in this order:
   - **map**: a later edition whose coverage contains its center does not show it: `to` = that
     edition's year;
   - **rebuilt**: a building standing today covers more than 20% of it and was built after the
     last edition that shows it: `to` = the earliest such year built;
   - **highway**: an expressway (18 m buffer on each side of its line) crosses it and opened
     after its last edition: `to` = the opening year;
   - **assumed**: otherwise `to = max(1960, lastSeen + 1)`.
4. `alive(from, to, year)` in `src/history.ts` draws it when `from <= year < to`.

So a building last seen on the 1950 or 1952 sheets, with no rebuild or highway on its spot,
gets `to = 1960` and is not drawn in 1969 or 1972. In `history/sanborn/lost.geojson`, 514
footprints are (lastSeen 1950, to 1960, assumed) and 308 are (lastSeen 1924, to 1960,
assumed); the second group are footprints no 1950 to 1952 coverage polygon contains (outside
the traced 1950 to 1952 sheets, which miss vol. 1 sheets 14, 16, 20, 23 and 24; not mapped
here). The rule is stated in `pages/how-its-made.md` ("assumed gone by 1960, when
clearing for parking and highways began"); a change to it changes that page in the same commit.

## How many buildings this hides

`scripts/count_dropped.ts`, read only: traced buildings standing in 1952 and not drawn in 1969,
less the footprints `clean.py` drops, with the ground at each center read from the 2 m cache
against the Agnes level (10.82 m NAVD88 at the Locks, +0.4 m west of the Mayo Bridge; ground
only, no connectivity test). Output in `scripts/dropped-counts.json`, the ids in
`scripts/dropped-below-agnes.json`.

| Area (coverage.ts) | Standing 1952, not drawn 1969 | of which assumed | highway | On ground under the Agnes level | of which assumed |
|---|---|---|---|---|---|
| Shockoe Bottom | 111 | 97 | 14 | 80 | 68 |
| Shockoe Slip and downtown (all of it, not only the frame) | 55 | 55 | 0 | 30 | 30 |
| Church Hill foot and Rocketts | 317 | 314 | 0 | 8 | 8 |
| North of Broad Street | 317 | 287 | 23 | 6 | 5 |
| Manchester | 0 | | | 0 | |

The 14 highway ends in Shockoe Bottom are I-95 (1958) and are right. The 68 assumed ends under
the Agnes level are the ones in question.

**A screening pass on the 1974 orthophoto** (`scripts/darkness.py`, provisional): for the 111
assumed-ended footprints under the Agnes level in all areas, after the fitted shift and a 2 m
inward buffer, 80 were large enough to measure. 39 of the 80 are at least half dark on the
photo (a roof or a shadow there in 1974), 26 at least 70% dark, and 31 are mostly light (under
20% dark: pavement, a gravel lot, or a light roof). Light roofs and the halftone make this a
screen, not a verdict, but it says the 1960 rule removes a good share of buildings that were
still there in 1974.

**Blocks**: of today's city blocks (`data/sanborn/blocks.json`) in the Shockoe Bottom area,
41 in all, 28 have their center on ground under the Agnes level and 6 more have only an edge
under it (`scripts/blocks.ts`).

## The options

### (a) Trace footprints from one aerial per year

Trace every building from the 1974 orthophoto, heights by rule (storeys from material and
size, or a flat default), for both 1969 and 1972.

- For: one source for both areas; it shows the city as it was within two to five years.
- Against: the photo cannot split joined buildings, so a block face becomes one long
  footprint; the outline is good to 3 to 5 m at best; no heights; no material; it is 1974, so
  it misses what Agnes's damage cleared between 1972 and 1974. The scan is a printed halftone:
  color-fill tracing (`extract.py`) does not apply; outlines would have to be drawn from the
  photo in code with a segmentation pass and checked block by block.
- Effort for Shockoe Bottom: 34 blocks under or at the edge of the Agnes level, about 10 to 15
  masses each, so 350 to 500 outlines, with no good automatic way in. Days, and the result
  would read cruder than the Sanborn traces next to it.

### (b) Carry the 1950 to 1952 traces forward, subtract what the photo shows gone

Keep the Sanborn footprints (outlines, storeys, material) and change only their end year:
a building last seen in 1950 to 1952 with an "assumed" end is drawn until the photo shows its
spot cleared.

- For: cheap. The footprints, heights and materials already exist; the work is one yes/no per
  building (about 70 in Shockoe Bottom's flood area, about 100 with Shockoe Slip and the
  edges). The 1974 photo is good at exactly this question. It matches how the history already
  works (an end year with stated evidence), so the end could be recorded as `photo` evidence
  with the photo cited.
- Against: anything built 1952 to 1969 and gone by today is still missing (likely few in the
  Bottom, which was declining); a building gone by 1974 may have stood in 1972 (flood damage),
  so "gone in 1974" has to become "gone by 1974, end year uncertain": draw it in 1969 and 1972
  only if a second source says so (the 1980 NR inventory cannot, since it lists vacant lots;
  the 1968 photorevision frames are behind the EarthExplorer login); it covers only where the
  1950 to 1952 sheets were traced, so the missing vol. 1 sheets (14, 16, 20, 23, 24) leave
  holes, as does Manchester.
- How, in code: a per-footprint decision file (id, verdict present / gone / unsure, the photo
  cited), read by `lifespans.py` or by the floods series' history, giving `to = 1975` (present
  in 1974) or keeping 1960 (gone). The "assumed 1960" rule elsewhere stays as it is, so sold
  pieces do not change.
- Effort for Shockoe Bottom: the overlay script exists (`scripts/overlay.py`); review of about
  70 to 100 footprints with the overlay, a few hours including the registration check;
  a rebuild of the two plates.

### (c) Both

(b) first, then (a) only for blocks the photo shows built up where no trace exists (new
buildings 1952 to 1972, or the missing sheets). Probably a handful of blocks.

### Manchester

There are no traces south of the river. The path is the same pipeline the north bank had:
fetch the South Richmond 1952 sheets (LOC sanborn09064_021; the flats are on sheets 1, 2, 4 and
their neighbors, about 8 to 12 sheets by the index), fit them with `rigid.py`, trace them with
`extract.py`, run `lifespans.py`, then apply (b) with the 1974 photo (which needs its own
registration there). Separately, the year-built cache stops at about 37.5204 N, leaving 325 of
the 413 buildings in today's Manchester view undated; that needs a wider `fetch` of the
assessor's parcels, not research.

## Recommendation and the one-block test

Test **(b)** first. It is a fraction of the work, keeps the better Sanborn outlines, and the
photo is strong at the one question it asks.

**Test block: North 17th to North 18th Street, East Franklin to East Grace Street** (center
about 37.5345 N, -77.4266), with the block across 17th Street toward the market for contrast.
Why: it has the densest cluster of dropped footprints in the Bottom (7 dropped, all from 1952
sheet 22, three and four storeys), its ground is under the Agnes level, and the overlay
(`samples/testblock-ortho1974-with-1950-traces-shifted.png`) already shows both outcomes: long
footprints on dark roofed masses (present in 1974) and footprints on open ground (cleared).

Steps for the test:

1. Fit the 1974 orthophoto to the street corners (the fitted +2 m E, -14 m N shift is a start;
   check three corners as the Sanborn fits do).
2. For each of the block's dropped footprints, mark present / gone / unsure on the overlay,
   with the GeoPDF at 600 dpi for the close look; record the verdicts in a small file.
3. Check each verdict against the 1983 NR inventory for the block's addresses (a building there
   in 1980 and dated before 1972 confirms "present"), and against any City planning slide or
   HABS photo of the block.
4. Build the 1972 plate with the new ends for that block only, and compare with the d1 plate
   (Compare, `C`) at plate view and close up.
5. Time it. If one block takes under half an hour, the Shockoe flood area is a day's work.

## What the owner may want to fetch himself (optional)

All public; none needs anyone contacted, but some need his own login or card:

- **EarthExplorer** (his own USGS login): the aerial single frames behind the 1968 and 1974
  photorevisions of the Richmond quad, at 400 dpi (free). A 1968 frame over Shockoe and
  Manchester would date losses before Agnes, which the 1974 photo cannot.
- **Library of Virginia card**: ProQuest Digital Sanborn or FIMo, to see whether a Richmond
  state later than 1952 exists online.
- Large files, if he wants them on the Mac: the 1974 orthophoto GeoPDF (22 MB) and GeoTIFF
  (14 MB), and the 1983 NR PDF (31 MB). URLs in `sources.md`. They were downloaded here only
  to /tmp and deleted after use.
