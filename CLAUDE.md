# isoscape — working contract

Read README.md for what this is. This file is the rules for changing it. Notes for agents helping
someone use isoscape (the reference site and the shop) are in AGENTS.md:

@AGENTS.md

## Conventions

- **View meters.** Everything after `view.toView` is in meters on the view plane: E′ across the
  frame (left → right), N′ into it (near → far). The camera looks along +N′, so *nearer means
  smaller N′*. Screen y grows downward. Don't introduce a second coordinate system.
- **Ring orientation.** Building outers are counter-clockwise and holes clockwise, in view
  meters, so the outward normal of edge a→b is (dy, −dx) for both. A wall is visible when that
  normal has a negative N′ component.
- **Palettes hold every color and line weight.** No hex values outside `palette.ts`.
- **No runtime dependencies.** Node ≥ 22.18 runs the TypeScript directly, so keep to erasable
  syntax: no enums, no namespaces, no parameter properties. `npm run typecheck` enforces it.
- **The cache is the source.** `build` never touches the network. Only `fetch` does.
- **Two heights.** `terrain.elevation(p)` is meters above sea level, used for contours, slopes
  and rapids. `terrain.z(p)` is scene height: (elevation − datum) × exaggeration, used for
  drawing. Building heights and bridge clearances are true meters added to scene z.
- **Strip seams.** Strips lap toward the camera only (by up to 8 m), into ground the next strip
  repaints, so no seam shows at any zoom and no lap covers a standing item. Never lap away from
  the camera.
- **Say how the work was done.** Chris is the artist and draws the maps. isoscape is the tool
  he draws with, built with Claude; Claude works in it under his direction (see
  `pages/artist-statement.md` and his talk). So "I drew", "I traced" and "drawn by Chris
  Busse" in his voice are right. What is never right is claiming manual work: nothing is drawn,
  traced, modeled or set "by hand", and machine work is never "hand-drawn". Where it helps,
  say the work was done with Claude or in code. Anything Claude drafts for publication says so,
  and may point to the artist statement.
- **Pages say what the code does.** `pages/how-its-made.md` describes the pipeline with real
  numbers (thresholds, defaults, distances). When you change one of those in the code, change
  the page in the same commit.
- **Ground paints in strips, far to near,** and items slot in after the strip holding their
  near edge (`flushTo` in `render.ts`). Anything new on the ground goes into `paintStrip`,
  clipped to the strip, densified and draped, never painted as one whole polygon.

## The loop

Never judge a change from the numbers alone. Look at it:

```sh
node bin/isoscape.js build <region> --png --width 3400
# then view out/<region>.png, or crop it: magick out/<region>.png -crop 1200x800+X+Y crop.png
node bin/isoscape.js info <region>     # counts and height sources
npm test && npm run typecheck
```

Before publishing any change to shared drawing code, run `npm run check:visual` and look at
`out/check/index.html` (see "Visual check" in the README).

Every build lands in the explorer (`out/index.html`). When iterating, pass
`--note "<what changed>"` so the explorer says what each build was for, and compare against
the previous one (`C`) before judging. Use `--no-archive` for throwaway checks.

## Where to change what

| To change | Edit |
|---|---|
| what is fetched | `overpassQuery` in `osm.ts` |
| what a tag means (ground kind, road width, height guess) | `classify.ts` |
| camera, snap | `view.ts`, `chooseBearing` in `scene.ts` |
| how a building or bridge is drawn | `extrude` / `bridgePieces` in `scene.ts` |
| what occludes what | `compare` in `order.ts` |
| SVG structure, layers, the viewer page | `render.ts` |
| colors, weights, dot size | `palette.ts` |
| elevation fetch and storage | `dem.ts` |
| an elevation source (URL, decoding, reprojection, credit) | `dem-sources.ts`; TIFF decoding in `rasters.ts` |
| lattice towers, roof shells | `spire`, `isLatticeTower`, `isShellRoof` in `scene.ts` |
| height grid, river surface, rocks, rapids, contours | `terrain.ts` |
| hillshade light, rapids marks, strip painting | `paintStrip` in `render.ts` |
| a place | `regions/<name>.json` |
| the build archive, git stamping, thumbnails | `archive.ts` |
| the explorer page | `explorer.ts` |
| a content page (How it's made, About, a new one) | `pages/<slug>.md`; see "Adding a page" in the README |
| how pages are loaded and linked; the Markdown subset | `pages.ts`, `markdown.ts` |
| the per-build "How this view was made" text | `makeStory` in `story.ts`, shared by the explorer and the static map pages (it links to `pages/how-its-made.md` section ids) |
| the static pages for search engines (`p/`, `m/`, `sitemap.xml`), their URLs, head tags and JSON-LD | `static-pages.ts`; shared CSS from `explorer.ts`; "Static pages and search" in the README |
| building an old commit into the archive | `backfill.ts` |
| dated series: year built, era rules, curated history | `history.ts`, `asOf` in `scene.ts`, `history/<series>.json` |
| ground put back before a later cut or fill | `ground` in `history/<series>.json`; `restoreGround`, `lowerGround` in `terrain.ts` |
| tracing fire-insurance maps (georeference, trace, lifespans) | `tools/sanborn/*.py` → `history/sanborn/` |
| a set: a big map framed by numbered boxes, its prints and page | `sets/<name>.json`, `tools/sets/set.py`; "Making a set" in the README |
| one building modeled close up (parts, tracks, canopies, trains) | `tools/stations/<name>.py` → `history/<name>.json`; `src/parts.ts` |
| a cutaway: the cut plane, sections, plan, flat section, its sheet | `cutaway` in `regions/<name>.json`; `src/cutaway.ts`, `src/cutaway-scene.ts`, `src/section.ts`; `cutaways/<name>.json`, `tools/cutaway/sheet.py`; "Cutaways" in the README |
| release records: what each sold design was made from, and how to remake it | `tools/release/` → `releases/` |
| plate numbers, the taxonomy, the printed title block | `catalog/plates.json`, `tools/release/plates.py`, `tools/print/titleblock.py`, `tools/release/stamp.py`; "Plates" in the README |
| a published piece corrected or redrawn | `pages/changes.md` (and the store's `changes_page.py`): every change, dated, with the piece's version |
| the visual check: watched views, crops, tolerance, its report | `tools/check/views.json`, `tools/check/visual.py`; baseline in `tools/check/baseline/` |
| placing streetcar lines from named corners | `tools/streetcars/build.py` (routes in `tools/streetcars/routes.json`) |

## Release records

Every design for sale must stay revisitable. Publishing or redrawing one is not done until
`tools/release/record.py <store> <design> --release` has written its record and
`tools/release/check.py <store> <design> --rebuild` passes; commit `releases/`. Never change a
published print in place: redraw it as the next version (`-vN` files, catalog `version`,
`pages/changes.md`). See "Release records" in the README.

## Known limits

- The hillshade is drawn as 24 nested bands each way, traced between 5 m grid nodes, so at
  extreme zoom a band's edge shows as a faint step in shade, and its bends as short straight
  runs.
- Rapids come from the lidar's water surface, read along the channel over 200 m and only
  10 m or more from shore, so they sit where the hydro-flattening put its steps (on the James
  the north channel beside Belle Isle reads level, its drop all at the dam below). A polygon
  far off from the real channel can still produce false falls.
- Big regions make big SVGs (the I-195 to Rocketts view is about 36 MB; at 25 MB it took a
  browser 10–20 s to open). Use the `--png` render for quick looks.
- One bad OSM tag must never break a build: parse every numeric tag defensively (one
  building's `building:min_level` is "federal").
- Bridge ways that fork at a junction ramp at the fork if no other bridge way touches it.
- Skyways (footbridges up to 80 m with an end at a building) are not drawn: OSM rarely gives
  their floor. Side-by-side ways of one street are grouped into one deck (`groupDecks`), but only
  where they run within 15 m of each other their whole length; a sidewalk that turns off its
  street partway keeps its own profile and can sit a little apart in height.
- Buildings must sit wholly inside the frame to be drawn. Bridges are cut at the plate's
  edges.
- A dated series shows only surviving buildings plus what is curated in `history/`; every
  curated item and era rule must cite a source (or say plainly that it is approximate).
  Traced Sanborn buildings that fall on water, within 12 m of a viaduct's center line, on a
  track, or under ground more than 3 m above their floor near a later road (8 m anywhere) are
  left out whole, not trimmed; their heights are assumed from their material.
- Ground put back before a later work (`ground` in a history file) is an estimate: inside its
  outline the lidar is replaced by a membrane from the rim and the streets that crossed at grade,
  or narrow banks are taken down (25 m opening). Relief smaller than the outline's width (a
  knoll, a ravine head) is lost; in Jackson Ward the error is about 1.5 m mid-trench, 3 m at its
  ends, and the I-95 bench on the Shockoe Valley side and the Leigh Street cut are kept as measured.
- Outside the US, terrain is only as fine as its source: Copernicus is a 30 m *surface* model
  (trees and roofs included), and Terrain Tiles is 30 m SRTM in much of the world. Every source
  must carry its credit and license in `dem-sources.ts`; the maps, explorer and prints use them.
- Concave footprints that interlock can form an ordering cycle, which is broken by depth.
- With terrain, water mapped as an area narrower than a grid cell, with no grid node inside it,
  is not drawn; where the lidar finds mapped water more than 1.5 m above the river, or a bar
  in midstream, the shore there follows the 5 m grid (smoothed) rather than the outline.
