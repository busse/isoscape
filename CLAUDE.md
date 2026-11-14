# isoscape — working contract

Read README.md for what this is. This file is the rules for changing it.

## Conventions

- **View metres.** Everything after `view.toView` is in metres on the view plane: E′ across the
  frame (left → right), N′ into it (near → far). The camera looks along +N′, so *nearer means
  smaller N′*. Screen y grows downward. Don't introduce a second coordinate system.
- **Ring orientation.** Building outers are counter-clockwise and holes clockwise, in view
  metres, so the outward normal of edge a→b is (dy, −dx) for both. A wall is visible when that
  normal has a negative N′ component.
- **Palettes hold every colour and line weight.** No hex values outside `palette.ts`.
- **No runtime dependencies.** Node ≥ 22.18 runs the TypeScript directly, so keep to erasable
  syntax: no enums, no namespaces, no parameter properties. `npm run typecheck` enforces it.
- **The cache is the source.** `build` never touches the network. Only `fetch` does.
- **Two heights.** `terrain.elevation(p)` is metres above sea level, used for contours, slopes
  and rapids. `terrain.z(p)` is scene height: (elevation − datum) × exaggeration, used for
  drawing. Building heights and bridge clearances are true metres added to scene z.
- **Strip seams.** Strips lap toward the camera only (by up to 8 m), into ground the next strip
  repaints, so no seam shows at any zoom and no lap covers a standing item. Never lap away from
  the camera.
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
| colours, weights, dot size | `palette.ts` |
| elevation fetch and storage | `dem.ts` |
| height grid, river surface, rocks, rapids, contours | `terrain.ts` |
| hillshade light, rapids marks, strip painting | `paintStrip` in `render.ts` |
| a place | `regions/<name>.json` |
| the build archive, git stamping, thumbnails | `archive.ts` |
| the explorer page | `explorer.ts` |
| a content page (How it's made, About, a new one) | `pages/<slug>.md`; see "Adding a page" in the README |
| how pages are loaded and linked; the Markdown subset | `pages.ts`, `markdown.ts` |
| the per-build "How this view was made" text | `story` in `explorer.ts` (it links to `pages/how-its-made.md` section ids) |
| building an old commit into the archive | `backfill.ts` |
| dated series: year built, era rules, curated history | `history.ts`, `asOf` in `scene.ts`, `history/<series>.json` |
| tracing fire-insurance maps (georeference, trace, lifespans) | `tools/sanborn/*.py` → `history/sanborn/` |

## Known limits

- The hillshade is quantised per 5 m cell, so very steep ground can look stepped.
- Rapids come from the lidar's water surface, read only 10 m or more from shore; a polygon
  far off from the real channel can still produce false falls.
- Big regions make big SVGs (the I-195 to Rocketts view is 25 MB and takes a browser 10–20 s
  to open). Use the `--png` render for quick looks.
- One bad OSM tag must never break a build: parse every numeric tag defensively (one
  building's `building:min_level` is "federal").
- Bridge ways that fork at a junction ramp at the fork if no other bridge way touches it.
- Buildings must sit wholly inside the frame to be drawn. Bridges are cut at the plate's
  edges.
- A dated series shows only surviving buildings plus what is curated in `history/`; every
  curated item and era rule must cite a source (or say plainly that it is approximate).
- Concave footprints that interlock can form an ordering cycle, which is broken by depth.
