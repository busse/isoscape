# isoscape

Isometric dot-and-line views of real places, built from open map data.

A sibling of [dotscene](https://github.com/busse/dotscene): the same visual language (inked
edges, a dot on every corner, flat fills), but driven by geography instead of hand-placed
points. Where dotscene is for authoring a scene, isoscape is for *surveying* one. You give it a
frame on the world, and it fetches OpenStreetMap, extrudes every building, raises the bridges,
sorts it all back to front and writes an SVG and a pan-and-zoom page.

The first region is downtown Richmond, VA, from Tredegar to the Mayo Bridge, in two
versions: a flat plate, and one shaped by real elevation. Richmond sits on the Fall Line,
where the James drops off the Piedmont onto the coastal plain. Through this slice the river
falls about 10 m through boulder fields and rapids to the head of tide at the Mayo Bridge,
under bluffs that rise 50 m to downtown, Oregon Hill and Church Hill.

![Downtown Richmond and the James River on the Fall Line, isometric with terrain](docs/richmond-downtown-topo.png)

```sh
node bin/isoscape.js fetch richmond-downtown        # OSM + elevation → data/richmond-downtown/
node bin/isoscape.js build richmond-downtown-topo   # → out/richmond-downtown-topo.{svg,html}
node bin/isoscape.js build richmond-downtown        # the flat version
node bin/isoscape.js build richmond-downtown-topo --palette night --png
```

Node 22.18 or newer. No runtime dependencies and no build step: Node strips the TypeScript
types itself. `--png` shells out to `rsvg-convert` (`brew install librsvg`).

## Commands

| | |
|---|---|
| `isoscape regions` | list the region configs in `regions/` |
| `isoscape query <region>` | print the Overpass query a fetch would send |
| `isoscape fetch <region>` | download OSM data (`osm.json`) and elevation (`dem.bin.gz`) into `data/<region>/`; `--osm-only`, `--dem-only` |
| `isoscape info <region>` | the chosen bearing, feature counts, and where building heights came from |
| `isoscape build <region>` | write `out/<region>.svg` and `out/<region>.html` |

`build` flags: `--palette <paper\|night>`, `--png`, `--width <px>` (PNG width), `--out <dir>`.

Overpass is often at capacity. `fetch` retries across four mirrors with backoff. If it still
fails, run `isoscape query <region>`, paste the query into
[overpass-turbo](https://overpass-turbo.eu), export the raw JSON, and save it as
`data/<region>/osm.json`.

## How it works

```
regions/<name>.json ─► fetch ─► data/<name>/osm.json
                                     │
                    parseOsm (osm.ts): polygons, multipolygons, lines, in lon/lat
                                     │
         chooseBearing (scene.ts): snap the camera so the street grid sits on the diagonals
                                     │
     buildScene: ground polygons · road/rail ribbons · extruded buildings · bridge spans
                                     │
              paintOrder (order.ts): pairwise occlusion → topological sort
                                     │
                     renderSvg (render.ts) ─► out/<name>.svg, .html, .png
```

**The camera** (`view.ts`) is orthographic, tilted down, and always looks along +N′ ("view
north"). Ground across the frame is drawn at full `scale`. Ground into the frame is
foreshortened by `squash`, the sine of the tilt (0.5 is a 30° tilt). Height is drawn at the
cosine of the tilt. The frame is a rectangle in view metres, so it lands on screen as a plain
rectangle, which suits a panorama.

**Snap.** A camera facing due north sees most street grids at an odd angle. With `snap`, the
dominant orientation of the building edges is measured (length-weighted, folded mod 90°), and
the camera turns by up to 45° so that grid runs along the isometric diagonals. Downtown
Richmond snaps to a bearing of −8.7°.

**Buildings** (`extrude` in `scene.ts`) are prisms: a wall on every footprint edge that faces
the camera, painted far to near, then the roof. Courtyards (inner rings) work. Wall tone
follows the wall's normal, with light from the left. Heights come from OSM `height`, then
`building:levels`, then a guess from the building's type and size; `isoscape info` reports the
mix. OSM Simple 3D Buildings parts (`building:part`) replace their outline when present.

**Bridges.** OSM splits a bridge into many ways, so connected bridge ways (same layer and
kind) are chained first. Only ends that touch no other bridge way ramp down to the ground.
Deck height comes from a per-region rule matched on the name, else `bridgeDeck × layer`.
Each chain is cut into ~22 m spans so it can interleave with buildings in the paint order.
Piers drop every 38 m.

**Paint order** (`order.ts`). A single depth key is wrong as soon as a long warehouse sits
beside a small house. So order is decided pairwise, only between items whose screen boxes
overlap. If the footprints are separable, the one on the camera's side of the separating
line is in front. If they overlap, a part entirely above the other is in front. Otherwise
centroid depth decides. A topological sort turns those facts into one order, and the rare
cycle is broken by depth.

**Terrain** (`dem.ts`, `terrain.ts`). Elevation comes from USGS 3DEP, the National Map's
seamless bare-earth model, which is 1 m lidar across Richmond. `fetch` asks its
`exportImage` service for an uncompressed float GeoTIFF over the region. A minimal reader
parses it, and it is stored as gzipped int16 centimetres (about 4 MB for this slice). The
build resamples it onto a 5 m grid in view metres and blurs it lightly to lose the lidar
grit. Elevation above the frame's lowest point, times `terrain.exaggeration`, becomes scene
height. Buildings and bridge clearances add true metres on top, so the hills are
exaggerated but the towers are not.

**The river.** Lidar over mapped water is not the water: rocks, ledges and overlapped banks
stand above it. The surface at each water node is taken as a low percentile of the wet ground
within 25 m, then smoothed along the water. Anything a metre or more above that surface is
drawn as exposed rock, which gives the boulder fields. The water drapes on the surface, so
it lies level across the river and falls along it. **Rapids** are drawn where that surface
falls faster than `terrain.rapids` (m/m) measured over 40 m: white strokes across the
current, with froth where it drops hardest. OSM weirs are drawn as white crests.

**Ground with relief paints in strips.** A height field hides itself: a bank falling away from
the camera covers the water behind it. So the ground is painted in 10 m strips across the
frame, far to near. Each strip drapes everything on it over the terrain: bare ground, parks,
water, islands, roads, rail, hillshade (lit from the left and slightly toward the camera),
contours (2 m, heavier every 10 m) and rapids. Each building or bridge paints straight after
the strip holding its near edge, so a hill in front of it covers it and ground behind it
does not. Buildings sit on the lowest ground under their footprint, so on a slope the
downhill wall shows full height. Bridge decks are a taut line over whatever they cross:
the upper hull of the ground plus clearance, ramping down only at ends that meet the ground.
Piers drop to the real ground or water. The slab's front face is a true cross-section of
the valley, with water where the cut crosses the river. A region without `terrain` gets the
same pipeline on a flat plate.

## Region config

```jsonc
{
  "title": "Richmond, VA — Tredegar to the Mayo Bridge",
  "center": [-77.4400, 37.5338],  // lon, lat
  "width": 1700,                  // metres across the frame
  "depth": 950,                   // metres into the frame
  "bearing": 0,                   // direction the camera faces; 0 = north is up
  "snap": true,                   // turn ≤45° to put the street grid on the diagonals
  "scale": 2.4,                   // px per metre across the frame
  "squash": 0.5,                  // sine of the tilt
  "exaggeration": 1.0,            // vertical exaggeration
  "slab": 16,                     // ground slab thickness, metres
  "palette": "paper",             // paper | night
  "bridgeDeck": 7,                // default deck height per OSM layer
  "bridges": [{ "match": "Manchester", "deck": 24 }],
  "minBuildingArea": 12,          // m²
  "dots": "all",                  // all | roof | none
  "data": "richmond-downtown",    // optional: share another region's cached data
  "terrain": {                    // optional: relief from data/<region>/dem.bin.gz
    "exaggeration": 2.5,          // vertical exaggeration of the ground only
    "cell": 5,                    // grid spacing, metres
    "contour": 2,                 // contour interval, metres (0 for none)
    "majorEvery": 5,              // every 5th contour heavier
    "rapids": 0.035               // water-surface fall (m/m over 40 m) that reads as rapids
  }
}
```

The fetch covers the frame's circumscribed circle, so a snapped camera never looks past the
data.

## Roadmap

1. **Lidar heights.** About 40% of downtown heights are guesses. 3DEP's bare-earth model is
   in place; the first-return surface model minus it, sampled per footprint, gives real
   heights.
2. **Corridors.** A region shaped by a GeoJSON polygon instead of a rectangle: the river plus
   a ~300 m buffer on its north bank, clipped to the city line. That is the full
   west-to-east Richmond strip. It may also mean "unrolling" the river so distance along the
   centreline becomes screen x.
3. **Tiles.** Build once, then crop viewBoxes into tiles and rasterise a zoom pyramid for a
   web map. There are no seams to hide: one projection, one paint order.
4. **Levels of detail.** Drop dots and minor edges at low zoom.
5. **Hand-drawn landmarks.** Override the Belle Isle footbridge under the Lee Bridge, the
   Potterfield bridge and the Triple Crossing with authored figures.
6. **Trees.** Scatter crowns over wooded areas and cemeteries.

## Data

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available
under the Open Database License. The cached `data/*/osm.json` files carry that licence, and
every rendered SVG and page carries the attribution. Elevation is from the
[USGS 3D Elevation Program](https://www.usgs.gov/3d-elevation-program), public domain;
`data/*/dem.bin.gz` is a resampled copy.
