# Case-study log: the Virginia dollar-store visualization

Kept with Claude at Chris's request (November 21, 2026), so the development of this piece can
be told later. Each step has a dated folder beside this log with what was shown or looked at.
Times are Eastern. Estimates against actuals are in `../effort.md`.

## How the piece started

The planning session (Fable) wrote `ISO-TEST/handoff/dollar-stores-virginia/HANDOFF.md` on
November 21 and handed the work to a separate Opus 5.5 session. Chris's question, in his
words: "Why does it always seem like there's a Dollar General on the edge of town?" He asked
for a poster with a grid of town maps, the data behind the "why", and yellow-and-black marks
for the stores. The handoff told the new session to treat it as a question that could come
out "partly" or "no".

## Step 1: the plan (11:12-11:25)

Folder: `2026-11-21-01-plan/`.

- Read the handoff, CLAUDE.md, and the README's "Stages and the board" and "Adding a page".
  Made the branch `viz/dollar-stores-virginia`.
- Checked the data before planning around it:
  - Downloaded the USDA SNAP retailer file. It counts 505 Dollar General stores still
    authorized in Virginia, close to the 499 in the company's 10-K.
  - Found the file starts in 2005, not the 1990s as the handoff said. 188 of those stores
    carry 2004-05 dates, so opening years only mean something from 2006.
  - The Census Data API now asks for a key; the bulk files on www2.census.gov do not.
  - Overpass refused the request at first (no user agent, then at capacity).
  - VDOT's traffic data is licensed for "official business of the Commonwealth".
  - The statewide parcel layer has outlines but no values.
- Showed Chris a one-page plan (`plan-as-first-shown.md`) with three ASCII poster layouts,
  then asked multiple-choice questions.
- Chris's answers:
  - All three chains, shown apart.
  - Test the edge measures on three towns before choosing.
  - Layout A, the grid of flat maps first.
  - Asked for two versions that the plan had not offered: an "editorial reporting" poster
    and a "simplified artistic" one, "denser and reduced element resolution".
- A second round of questions settled the rest:
  - The artistic version shows every town and city (227 tiles).
  - The editorial version shows 20 towns.
  - One chart of opening years; the maps show today.
  - 24 x 36 in, editorial only for now.
- Result: `plan-after-decisions.md`.

## Step 2: the edge-of-town test (11:25-11:45)

Folder: `2026-11-21-02-edge-test/`.

- Test towns, chosen for shape and not as a sample:
  - Marion: a long valley town on I-81.
  - South Hill: the I-85 / US 58 crossroads.
  - Chase City: 2,053 people, no Census urban area.
- Data:
  - On the Mac: TIGER places, 2020 blocks, urban areas, Overpass extracts for three windows.
  - In the cloud workspace: the processing, because the Mac's Linux shell has no geo
    libraries.
- Measures:
  - A: distance from the population-weighted center divided by the distance to the built-up
    edge on the same bearing. Two settings of the built-up edge: strict at 425 homes per
    square mile and loose at 200, both the Census's own 2020 thresholds.
  - B: inside the town limits, inside the urban area, or outside both.
- Dead ends and fixes along the way:
  - The town-name slug turned "Chase City town" into "chase" twice: first a string replace,
    then a suffix strip that took off " city" as if it were an independent city. Fixed by
    using the Census NAME field.
  - OSM building coverage was too thin to draw an edge from (186 buildings in the Chase City
    window). Census blocks were used instead.
  - The first strict-only run put Marion's groceries, Walmart and CVS "beyond the edge".
    That led to the second, loose setting, and later to the proposal to add impervious cover
    the way the Census does.
- Render rounds (each looked at before the next):
  - Map round 1 (Marion viewed):
    - matplotlib's "Northing/Easting [metre]" axis labels showed.
    - The lightest density class washed over the whole countryside.
    - The footnote sat above the legend.
    - Fixed all three. The round-1 image was overwritten; this is why the standing rule
      below exists.
  - Chart round 1:
    - The two x-axis labels overlapped.
    - The bottom row label and the footnote were cut off.
    - Fixed with one shared axis label, a two-line footnote and a shorter row label.
  - Chart round 2: the row label was still clipped. Shortened to "Random main-road points".
- Facts checked against what was opened:
  - The 425 and 200 thresholds, against the Census Bureau's December 2022 note.
  - Every count in the findings, against the score tables.
  - Three numbers in the first draft of the findings were wrong and corrected before
    delivery:
    - An off-map store was double counted.
    - The OSM count was 7, not 6.
    - The grocery score range starts at 2.8, not 3.
- What it found in three towns:
  - Six of ten Dollar General stores are inside the built-up area.
  - Four are 8 to 9 km out, between towns.
  - None sits at the edge.
- Chris's answer (11:45): go ahead with the loose edge plus impervious cover and the seeded
  draw; keep everything for this case study, as a standing rule.

## Standing rule (Chris, November 21, 2026)

Preserve all work as it goes, for case studies: every render and chart that was shown or
looked at, every round (never overwritten), notes, questions with answers, decisions, dead
ends and timings. Written into CLAUDE.md as "Keep the case-study record".

## Step 3: the lead edge and the editorial draw (11:45-11:52)

Folder: `2026-11-21-03-lead-edge-and-draw/`, with its own `notes.md`.

- **The record.**
  - Set up this case-study record. Wrote the standing rule into CLAUDE.md.
  - Unpushed commits are kept on the Mac as a git bundle, because the cloud workspace does
    not last: `ISO-TEST/isoscape-work/dollar-stores/viz-dollar-stores-virginia.bundle`.
- **Impervious cover, round 1.**
  - NLCD 2021 impervious chained Marion's built-up area 10 km along I-81. Kept as round 1.
- **Impervious cover, round 2.**
  - Non-road impervious only, using NLCD's descriptor class 24, which the NLCD legend
    confirms.
  - All supermarkets and pharmacies are now in town.
  - Dollar General splits the same way as before: six in town, four between towns, none at
    the edge.
- **Regions.**
  - Regions are groups of planning district commissions, from the VAPDC directory.
  - The central Piedmont, missing from the handoff's five regions, was joined to Southside.
    To show Chris.
- **The draw.**
  - Seeded draw of 20 towns.
  - One empty cell, the coastal region at 10,000 or more, was filled statewide by the rule
    written before the draw: Leesburg.
