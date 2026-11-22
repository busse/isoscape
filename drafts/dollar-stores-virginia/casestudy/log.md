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

## Step 4: Mathews and Middlesex, store first (11:53-11:59)

Folder: `2026-11-21-04-mathews-middlesex/`, with `notes.md`.

- **The request.** Chris asked to include Mathews and Middlesex specifically, and spitballed
  "find DGs, infer centroid of why they are there".
- **How it was read.** Start from the stores. Find who lives nearest each Dollar General by
  road, and where those people's center is.
- **The two counties in the grid.** Added as the owner's choice, apart from the seeded 20.
  Neither has a town the rule could draw (Urbanna has no Dollar General).
- **What it found.**
  - The three oldest stores (2005-07) are in the villages, beside the grocery.
  - The four newer ones (2014-25) are between villages on the state routes, 5 to 13 km from
    a grocery.
  - All seven are near route junctions. The junction test needs a cleaner rule.
- **Rounds.** The map took three. The Hartfield label is left as a listed fault because of
  the round budget.

## Step 5: the editorial 20, first full pass (12:02-12:26)

Folder: `2026-11-21-05-editorial-20/`, with `findings.md`.

- **Data.**
  - NLCD for 20 windows.
  - Overpass was at capacity again, after half the towns. Switched to Geofabrik's Virginia
    extract (430 MB, too big to bring across). Filtered it on the Mac to roads and the three
    chains (67 MB).
  - Checked the extract against Overpass on Chase City: 299 against 298 road ways.
- **Rules.** The first run showed two cases the measure had no rule for: tiny towns with no
  built-up core (Scottsburg) and towns swallowed by a metro (Vinton). Wrote rules for both
  before reading any store results.
- **Results.**
  - 40 percent of Dollar General stores are beyond their town, against 11 percent of
    supermarkets.
  - Dollar General is no more often in the edge band than road frontage is.
  - The five stores between places were all authorized 2016-24. In town, 8 of 12 date to
    2004-05.
- **Rounds.** Contact sheet in 2, pooled chart in 2. The first chart title overstated the
  result and was rewritten.
- **Open.** Two calls are still waiting on Chris: the region grouping, and the Hartfield label
  round.

## Step 6: why are the edge stores where they are? (12:40-12:59)

Folder: `2026-11-21-06-edge-stores/`, with `hypotheses.md` (written first) and `findings.md`.

- **Chris's direction (12:40).** He left the region grouping to Claude. He approved round 4
  for the Hartfield label, which is done. He asked to focus the editorial on the edge stores:
  "why are the edge ones where they are?"
- **Hypotheses first.** Seven reasons and their tests were written at 12:45, before any edge
  store statewide was scored.
- **Scope.**
  - Scored all 227 Virginia towns and cities. NLCD 2001 and 2021 were fetched on the Mac in
    parallel and brought across as two archives.
  - 34 Dollar General stores sit at the edge band.
- **Results.**
  - Edge Dollar General stores are four times as likely as random edge sites to sit at a
    junction of state routes.
  - They are a little more likely to be on the road into town.
  - They are less likely to be outside the town limits.
  - They are newer than in-town stores.
  - Open land, rural reach and the far side from the supermarket: the data cannot tell.
  - Split after the fact into towns and cities: in towns the pattern is strong (18 stores).
- **Fixes.**
  - A snapping bug in the 5 km reach was fixed and rerun; the run-1 output is kept.
  - The first chart title overstated what the data says about land, and was rewritten.

## Step 7: traffic counts, a licensed source (13:03)

- **The question.** Chris asked: "Is there any data on traffic census to help shake this?"
- **The source.**
  - FHWA's HPMS 2024 "Spatial All Sections" on data.transportation.gov (dataset 42um-tgh5).
  - License: Public Domain U.S. Government, read from the dataset's own metadata.
  - It has 519,074 Virginia road sections with AADT, local roads included.
  - It was reached from the Mac and queried by state (stateid 51).
- **What it replaces.** VDOT's own layer, whose terms limit use to the Commonwealth's
  official business.
- **Not yet fetched or used.** The test is proposed to Chris in the reply.

## Step 7 (continued): traffic tests and the heat map (13:06-13:24)

Folder: `2026-11-21-07-traffic/`, with `hypotheses.md` (13:08, before fetching) and
`findings.md`.

- **Chris (13:06).** "Yes, this is an interesting thread to pull at and maybe heat map".
- **Data.**
  - Fetched HPMS 2024 for Virginia from data.transportation.gov: 262,439 sections with
    traffic, in six pages.
  - Fetched FHWA's 2012, 2014, 2015 and 2016 Virginia files. 2014 and 2015 needed resumed
    downloads.
  - The 2016 file is truncated at the source, so 2016 stores use 2015.
- **Results.**
  - Edge Dollar General stores sit on roads about twice as busy as other edge sites, as do
    convenience stores and supermarkets.
  - In towns, 13 of 18 are on one of the two busiest roads in, against 47 percent of random
    sites. This was stated before, and held.
  - The roads were already busy when the stores came.
- **Rounds.**
  - Heat-map gallery in 2, after its validator fix (the light end of the ramp was too faint).
  - Chart in 2.

## Step 8: editorial lines steelmanned (15:41)

Folder: `2026-11-21-08-editorial-lines/`. Chris asked, in chat, for the possible editorial
lines and their data viz, each argued at its strongest. Six lines are set out in
`steelman.md`, with the evidence, the viz and the weak spot for each, and a suggested
combination.

## Step 9: more coverage, an independent review, and the replication plan (15:44 onward)

Folder: `2026-11-21-09-replication/`.

- **Chris (15:44).** "I believe the sample is too weak a link to declare editorial coverage.
  Get more/total coverage of data then let's analyze more deeply. Consider if we should use
  Fable."
- **Chris's choices.**
  - Virginia in full: its 461 CDPs added as held-out set A.
  - Replication in NC, TN, KY, WV, MD and SC as held-out set B.
  - An independent Fable agent to review the plan and later the findings.
- **Plan v1 (15:58).** Frozen before any held-out result was read.
- **Fable review (about 16:05).** "Not ready to run as frozen." It found seven must-fixes:
  - The discovery numbers were quoted on the wrong unit.
  - The wording was absolute while the tests were relative.
  - The test needed to be place-conditional with a cluster bootstrap.
  - The junction rule was Virginia-only.
  - Edge-following roads counted as crossings.
  - C5 was partly made by the stores' own pavement.
  - Some code would break or reuse stores outside Virginia.
  It also found that Virginia's own C1 does not clear under the fairer test.
- **Plan v2 (16:15).** Adopts all seven must-fixes; the should-fixes become stated
  sensitivities. The route-number prefixes were tabulated from OSM for each state first,
  which involves no outcomes.
- **Chris (16:16).** "Keep in mind that our goal is to answer the 'Why?' first and foremost,
  then visualize it, but we need to bias toward the town edge angle because it is so
  noticeable to drivers who drive the state highways through many of these towns." Taken as
  the frame for the findings and the visuals: the driver's view along state highways through
  towns. The frozen tests stay as they are. C1 and C2 already ask the driver's question.
- **Data fetched.** For the six states: TIGER places and 2020 blocks, Geofabrik extracts
  (md5 checked, then filtered on the Mac one at a time after two ran out of memory together),
  and HPMS 2024 (counts match the API's totals).
- **Fixes on the way.**
  - The first CDP OSM cut ran out of memory and wrote nothing; it now runs in batches of 60.
  - prep.py now takes a state and GEOIDs, because Virginia has duplicate CDP names.
- **Chris (16:22).** "It is okay to take a bit of artistic license if needed." Taken as license
  over form: a schematic "drive in" strip, simplified roads, a composite labeled as
  illustrative. The facts and numbers stay exact.
- **A fix to C1 after v2, found on discovery data only.**
  - The first version of the M5 crossing rule tested each HPMS section alone. Sections are
    short, so it missed most crossings: Virginia C1 read 5 of 21 against 5.4 expected.
  - Fixed to test each whole road (its sections merged). Virginia C1 then reads 12 of 21
    against 8.4 expected, interval −0.03 to +0.38. That matches the Fable review's own
    estimate.
  - The run-1 output is kept as `conf_disc_run1_section_bug` in the working folder (not in
    git).
  - No held-out place had been read.
- **Other fixes.**
  - Three CDPs with no population raised GEOS errors. The center now falls back to the
    place's interior point, and degenerate geometry is repaired.
  - run_measure.py now logs a failing place and goes on.
- **Disk.** Space on the cloud workspace ran low. Deleted Claude's own temporary copies: the
  unzipped HPMS history (already analyzed) and duplicate Census zips. Each state's OSM cuts,
  NLCD tiles and block files are removed once the state is scored. The sources stay on the
  Mac.
- **Speed (about 17:40).** Maryland took about an hour, which put the six states at 6 to 7
  hours.
  - From West Virginia on, each place draws 1,500 random road points instead of 4,000. That
    still leaves hundreds in each place's edge band. It changes the precision of p_i, not
    any test.
  - The ray re-entry count (S6) is computed for stores only, since only stores use it.
  - Maryland and the Virginia CDPs keep 4,000.
- **Driver's view (exploratory, not a frozen test).** `drive_in.py` asks, for each road
  crossing into a place, which store a driver passes first. Debugged on discovery data only;
  it will be run on the held-out data after the frozen tests, and labeled exploratory.
- **The run (17:00-20:11).**
  - All six states were scored one at a time, cleaning each state's working files as it
    went. NLCD was fetched in parallel on the Mac; partial downloads were caught by a TIFF
    check and fetched again.
  - No place failed in the six states. Three Virginia CDPs failed before the fixes and were
    rerun.
- **The bootstrap (20:11-20:20).** It was too slow as first written (it rebuilt tables 10,000
  times per test). It was replaced by an equivalent per-place-totals version and checked on
  discovery: identical results, after one fix to C4's place list.
- **The frozen tests ran once on all data at 20:20.** Primary (234 edge Dollar General stores,
  203 small places in six states):
  - C1 to C6 all hold.
  - C2 (junctions) is the robust result: 17 percent against 6 percent.
  - C1 (top-two road in) holds but is small and fragile: 39 against 32 percent, and it cannot
    tell in two sensitivities.
  - 77 percent of edge stores are outside the town limits, so Virginia's "just inside" does
    not carry over.
  - Convenience stores show the same pattern, so the finding is "edge retail on the road in".
- **Draft findings** are in `findings-draft.md`. They went to an independent Fable agent for
  checking before anything is shown as a finding.
- **Row-level data.**
  - The full points file (4.6 million rows, 330 MB) is too big to keep. It can be rebuilt
    from the scripts and the raw files on the Mac.
  - The stores with all their features (187,464 rows, 14.6 MB) are kept on the Mac as
    `isoscape-work/dollar-stores/casestudy/2026-11-21-09-replication/stores-with-features.csv.gz`.
- **Independent check (Fable, about 20:45).** The frozen table reproduces; C2 is solid. It
  also found problems (`fable-check.md`):
  - C1 is fragile.
  - The driver's view denominator was wrong ("4 in 10" was really 6 in 100), and the script
    does not truly measure "first store passed".
  - Ties among stores were broken by chance.
  - S5 was not run.
  - C4 measures SNAP authorization year, not opening year.
  - West Virginia's 0 of 19 junctions is real, with 0.3 expected.
- **What was done about it.**
  - Ties now go to the larger place, by a stable sort. Rerun: verdicts unchanged.
  - The first run is kept as `data/tests-run1-unstable-ties.csv`.
  - `findings.md` adopts the checker's corrected answer to "Why?".
- **The answer (findings.md).**
  - Most Dollar General stores are not at the edge.
  - The edge ones sit at highway junctions, like convenience stores.
  - They carry newer SNAP authorizations.
  - "Busiest road in" and "just inside the line" do not hold up as headlines.

## Step 10: the editorial poster, rough draft (22:15-22:25)

Folder: `2026-11-21-10-poster-rough/`, with `notes.md`.

- **Chris (22:15).** "go".
- **The draft.**
  - The 30 Virginia edge stores, every one, as traffic heat-map squares.
  - Three charts from the six-state replication.
  - An honesty panel.
- **Rounds.** Three. Every number is computed from the test outputs. The board has a new
  print entry, `viz-dollar-stores-virginia-poster`, at rough draft.

## Step 11: the editorial poster, working draft d1 (November 22, 08:02-08:40)

Folder: `2026-11-22-11-poster-d1/`, with `notes.md`, five rounds and the rough draft's script.

- **Chris (08:02).** "continue with your thoughts. don't make the text copy read like AI wrote
  it. Use a freshman college level educational writing style". Read as "worth pursuing".
- **What changed.**
  - The grid is grouped by the five regions, west to east, with a locator map in the header.
  - The type is Libre Baskerville, the prints' own face.
  - The bottom gap is closed.
  - All text is rewritten in a plain teaching voice.
- **Errors found and fixed.**
  - The rough deck put the six-state counts in Virginia.
  - It said edge stores "are found" at highway junctions, when 17 percent are.
- **Rounds.** Five, all layout. Board: `viz-dollar-stores-virginia-poster` at working draft,
  `1.0.0-d1`.
- **Proofs (08:52).** An 11x17 PDF of the PNG, then a four-page vector proof (whole poster, three bands at 69%) so the captions can be read.

## Step 12: Hartfield tile and the SNAP question (November 22, 10:20)

Folder: `2026-11-22-12-hartfield-and-snap/`.

- **Hartfield.** A trial tile was drawn the grid's way. Hartfield has no Census place, so the rule
  scores the store as "farther out" from Deltaville. On the tile it is a crossroads store
  (VA 33 junction, 6,402 vehicles a day) with almost no town-density housing around it.
- **SNAP.**
  - Store-level redemptions are confidential (*FMI v. Argus Leader*, 2019).
  - The 2009 adoption wave (Byrne et al. 2025) barely touches Dollar General's approval years.
  - Filings tie SNAP to sales, not siting.
  - The question to Chris is whether to run an ACS test of SNAP households near the stores
    (correlation only).

## Step 13: SNAP households near the stores (November 22, 10:27-11:05)

Folder: `2026-11-22-13-snap/`, holding hypotheses.md (written before any number), findings.md,
snap_tests.csv, snap_by_period.csv and run.log.

- **Chris (10:27).** "Set aside Hartfield for now. Continue with snap research. Also, is there
  store level data before 2019?"
- **Store-level data.** None was ever released.
  - USDA refused the 2011 request.
  - Congress barred disclosure in 2018.
  - The Supreme Court held the data confidential in 2019.
- **ACS test (B22010, block groups, 3 km area-weighted).**
  - Edge Dollar Generals: 16.4% of nearby households get SNAP, against 16.4% at random roadside
    spots on the same edges (cannot tell, within about 0.7 points).
  - In town: the same.
  - SNAP does not explain where in a town the store sits.
- **Dead ends.** Two code errors and a memory stop (see run.log).

## Step 14: which towns get Dollar Generals (November 22, 10:45-11:00)

Folder: `2026-11-22-14-snap-towns/`, holding hypotheses.md (before any number), findings.md,
towns_tests.csv, towns_thirds.csv, towns.csv.gz and run.log.

- **Chris (10:45).** "Yes".
- **Result.** In 1,460 small places in six states, towns with more SNAP households have more
  Dollar Generals per household (1.13x per 10 points, 1.10 to 1.17). They also have more
  groceries (1.17x) and convenience stores (1.21x).
- **So** the link is general to food stores, not special to Dollar General.
- **Poster.** No change proposed.

## Step 15: poster working draft d2 (November 22, 11:25-11:50)

Folder: `2026-11-22-15-poster-d2/`.

- **Chris (11:25).** The d1 copy still shows signs of AI writing, for example the "How we did
  this, and what..." heading.
- **Copy.** All of it was rewritten: no paired headings, no matching question set, no tidy
  closing line, plain verbs.
- **Captions.** The two Martinsville tiles now name the side of town.
- **Locator.** Region numbers moved inside their regions.
- **Rounds.** Two layout passes. Board: `1.0.0-d2`, round 2.
