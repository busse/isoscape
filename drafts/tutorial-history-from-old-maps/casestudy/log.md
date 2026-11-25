# Case-study log: Tutorial 2, a neighborhood's history from old maps

Kept with Claude under Chris's standing rule (November 21, 2026). Times are Eastern.

## Step 1: the plan (November 25, 09:57-10:20)

Folder: `2026-11-25-01-plan/`.

- Chris: "Plan a tutorial for how to make something like the two Jackson Ward stories."
- Read the two story pages, their `tools/stories/` folders, the README's "Stories" stages and
  `tools/sanborn/README.md`. The existing Sanborn traces cover downtown (1886-1950) and Jackson
  Ward (1925, 1952); Broad and Belvidere lies just west of them.
- Plan shown in chat; questions put as multiple choice. Chris's answers:
  - The two stories: Jackson Ward before I-95, and Redlining in Richmond, 1937.
  - Example: a new small example made fresh, with Jackson Ward as the showcase.
  - Place: another Richmond block; "present me some that you think would be good, to choose
    from. VCU is always a dynamic, if applicable to this context". Four were offered (Broad and
    Belvidere; Carver at the Siegel Center; Oregon Hill's edge; the MCV campus in Court End).
    Chris chose Broad and Belvidere.
  - Scope: one page.

## Step 2: research (November 25, 10:07-10:45)

Folder: `2026-11-25-02-research/` (brief.md and the key-map crop); scans and downloads on the
Mac in `ISO-TEST/isoscape-work/tutorial-history-from-old-maps/research/`.

- Chris: "yes" (start research).
- Vol. 3's index has no Broad Street, so the corners aren't in the Jackson Ward volume. Vol. 2
  is the East End. The vol. 1 key map (1924) put the corners on sheets 33 and 34.
- Both editions' sheets 33 and 34 fetched from LoC at 25%. An auto row in 1924 and 1952.
- Assessor parcels (July 1, 2026) and OSM for today. Overpass returned 502 twice, so the
  intersection was read from the cached `richmond-streetcars` OSM.
- Found two published claims that disagree with the records (four corners; train station).
  They are teaching cases, to be checked before any use.

## Step 3: the outline (November 25, 10:19-10:35)

Folder: `2026-11-25-03-outline/`.

- Chris: "Write it. Also, the inconsistencies you find could be good callouts for the tutorial
  and how to consider handling them."
- The outline adds section 8, "When the sources disagree", with the three disagreements found
  in research (Smith/Belvidere, "all four corners", the train station) and how each is handled.
- Chris: don't make Tutorial 1 a prerequisite. The outline now repeats what it borrows (the chat's needs, the five questions) and links Tutorial 1 as optional.

## Step 4: making the example and the page (November 25, 11:13-13:40)

Folder: `2026-11-25-04-make/`. Scans on the Mac in `ISO-TEST/isoscape-work/tutorial-history-from-old-maps/research/`.

- Chris: "yes, continue and be aware another session did a lot of work modifying and migrating
  explorer to isoscape.chrisbusse.com". Rebased the branch on main e7074e4 and read the new
  "Publishing the site" (Cloudflare Pages, the `cloudflare` branch).
- **Fit.** Read 11 street corners off sheets 33 and 34 (50% scans) and fitted each sheet with a
  similarity (`tools/sanborn/bb/fit.py`). The first fit missed by up to 8.4 m on Broad, because
  OSM draws West Broad as two one-way carriageways. Using the midpoint of both brought sheet 33
  to a mean of 2.3 m (worst 4.7 m) and sheet 34 to 0.7 m. The 1952 sheets were placed with
  `follow.py` (673 and 469 ORB inliers).
- **A mistake, and its repair.** The first region file pointed `data` at `richmond-streetcars`,
  so `fetch` rewrote that shared cache on the Mac: its osm.json went from 103 MB to 1 MB, and
  its dem.bin.gz was replaced. Both were restored byte for byte from `ISO-TEST/isoscape-data.git`
  (blobs 58619180 and 40ff989b; the hashes were checked after). The stray tile and dem-tiles were
  moved to `isoscape-work/tutorial-history-from-old-maps/_to_delete/`. The region now has its
  own cache, `data/broad-belvidere/`. Lesson: never fetch for a region whose `data` names
  another view's cache.
- **Trace faults, found by looking at overlays and renders:** a page margin traced as a 1,409 m²
  frame building (fixed with keep frames per sheet); pale pink corrections missed on the 1952
  sheets (`material.py` now reads strongly red, non-yellow pixels as brick: 138 → 183
  buildings); the ICA hiding the 1924 garage (`lifespans.py --respect-years`); a garage followed
  into a small shed (`--strict-link`); and the CoStar Center undated (a curated date of 2025 from
  VCU News in `history/broad-belvidere.json`). The two lifespans options are documented in
  tools/sanborn/README.md and how-its-made.md.
- **Callouts resolved:** A, drawing today's N. Belvidere over the fitted 1924 sheet shows it cut
  through 600–608 W. Broad west of Smith Street, sometime after 1952. B is reported as each
  source says it, with dates. C, the 1905 sheet 61 shows the RF&P's Elba Station on the ICA
  block, and the Richmond Railroad Museum's history agrees.
- Builds: `broad-belvidere` 1924, 1952 and 2026 (archived). Page: `pages/history-from-old-maps.md`.
  Nav entry under "Stories and tutorials", region in the Tutorials section. Tests 266/266 and
  typecheck pass; previews.py 364 pages OK; desktop and 390 px phone have no sideways scroll.
- Local preview unpacked to `ISO-TEST/_preview/tutorial-2/`.

## Step 5: the Start here prompt (November 25, 11:43-11:50)

- Chris: "I want a very noticable, they can't miss it, copy and paste prompt to get them going
  specifically with isoscape. This section will fail if they don't mention isoscape."
- Added a prompt card to the page format: a fenced block with the language `prompt` renders as a
  bordered card headed "Copy this prompt into your chat" with a Copy button (`src/markdown.ts`,
  CSS in `PROSE_CSS`, `src/prompt.ts` for the button in the explorer and the static pages; a
  markdown test). Checked in a browser: Copy puts the 830-character prompt on the clipboard from
  both the explorer and the static page.
- The page now opens with "Start here" and that card, with isoscape and its repository in the
  first line. Section 1 points back to it and explains why the line matters. "Make your own"
  repeats the same card.

## Step 6: shipped (November 25, 11:49-12:10)

- Chris: "yes and then ship it all" (a Start here card on Tutorial 1 too, then publish).
- Tutorial 1 got the same prompt card. main fast-forwarded to b041bf2. The site was rebuilt
  into a sparse checkout of `cloudflare` (no SVGs checked out). `cloudflare.py` was run for the
  extensionless addresses, and `_routes.json` was restored from the branch, since a sparse
  checkout can't see the R2 files. 0 deletions in the commit. Pushed `cloudflare` bd6ed04;
  forwarding pages for the new addresses went to `gh-pages` 6b9c403. Live check: previews.py
  361 pages OK, and the new page, its share image and the 1924 SVG all answer 200.
- browser.mjs on the sparse copy failed only on SVGs absent from the sparse checkout (expected).
