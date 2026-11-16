---
title: How it's made
order: 10
summary: The whole pipeline, from OpenStreetMap and lidar to the drawing. What is measured, what is inferred, what is guessed.
---

# How it's made

isoscape draws a real place as an isometric dot-and-line picture: inked edges, a dot on every
visible corner, flat fills. Nothing in it is drawn by hand. Every line comes from two open
datasets, OpenStreetMap and the USGS 3D Elevation Program, and the code decides where it
goes.

This page follows the pipeline from the download to the finished SVG. It also says, for every
part of the picture, whether it was **measured**, **inferred** from a measurement, or
**guessed**. They look the same on the page, and they are not.

Each build in the explorer also has its own **How this view was made** tab under the picture.
It gives that view's frame, sources and counts, and links back to the sections here.

![The pipeline: fetch from OpenStreetMap and 3DEP into a local cache, then parse, camera, terrain, scene, order, draw, archive and explorer](pipeline.svg)

Where to start:

- **Lidar and GIS:** [Terrain](#terrain), [Rivers](#rivers), [Rapids](#rapids) and
  [Shoreline](#shoreline).
- **Urban planning:** [Buildings](#buildings), [Bridges](#bridges) and
  [Measured, inferred, guessed](#measured-inferred-guessed).
- **Art and illustration:** [Camera](#camera), [Drawing](#drawing) and
  [Paint order](#paint-order).
- **History:** [Time](#time) covers the dated series: what is measured, what is curated, and
  what a series cannot show.
- **Development:** every section names the file that does the work. The
  [archive and explorer](#archive-and-explorer) section covers the build loop.

## Measured, inferred, guessed

| Part of the picture | Comes from | How sure |
|---|---|---|
| Building footprints, roads, rail, parks, water outlines | OpenStreetMap | Mapped by volunteers, mostly traced from aerial imagery. Usually good, sometimes stale |
| Extra footprints (where a region asks) | Microsoft's ML building footprints | Traced by a model from imagery. Good outlines, sometimes merged or missing |
| Building heights | OSM `height`, else Microsoft's model, else `building:levels`, else a guess | Mixed. In downtown Richmond about 40% are guesses; around Gwynn's Island, a little over half. Each build reports its own split |
| Woods, wetlands, fields, crops (where a region asks) | USGS National Land Cover Database (NLCD 2021) | Classified from satellite imagery at 30 m. Right in the large, coarse at the edges |
| Ground elevation | USGS 3DEP bare-earth model in the US; elsewhere a national or global model (IGN, swisstopo, GSI, Copernicus, Terrain Tiles) | Measured. 1 m lidar where 3DEP has flown; from 1 m to 30 m abroad, by source |
| River surface | The lowest lidar returns over mapped water, smoothed | Inferred |
| Exposed rock and rapids | Height above, and fall of, that surface | Inferred |
| Shoreline (with terrain) | Mapped water, corrected against the lidar | Inferred |
| Bridge deck heights | A per-region rule by name, else a default per OSM layer | Rule of thumb |
| Camera bearing | Snapped to the street grid, or set in the region | Chosen |

## Inputs

**OpenStreetMap.** `fetch` asks the Overpass API for everything the renderer can draw:
buildings and building parts, water and waterways, roads, railways, parks, woods and other
land cover, islands, coastline and car parks. Large areas are fetched in tiles of at most
1.6 km a side, because Overpass refuses or times out on big requests. Four public mirrors are
tried in turn. Each tile is cached as it arrives, so an interrupted fetch picks up where it
stopped. The merged answer is saved as `data/<region>/osm.json`.

**Elevation.** In the US, the ground comes from the [USGS 3D Elevation Program
(3DEP)](https://www.usgs.gov/3d-elevation-program), the default source. Its seamless bare-earth model is served by
the National Map's `exportImage` service, which returns the best data available for each
place: 1 m lidar where it has been flown, coarser models elsewhere. Bare earth means
buildings and trees have been removed. isoscape requests uncompressed 32-bit float GeoTIFFs
in tiles of at most 1,500 pixels a side, at 1 m per pixel unless the region sets
`demResolution`. The tiles are stitched together and stored as `data/<region>/dem.bin.gz`:
gzipped 16-bit integers in centimeters, so heights are kept to the nearest centimeter.

The service keeps its pixels square in degrees. A tile sized in meters is not square in
degrees away from the equator, so the service widens it north and south about its center
and fills the same number of pixels: the image covers more ground than was asked for. Each
tile is read on the box it really covers and resampled onto the box asked for. Until
November 2026 this was missed, and the ground in every 3DEP map sat squeezed north–south by
the cosine of the latitude (0.79 in Richmond, 0.73 at Crater Lake): up to a few hundred
meters off at a tile's edge, with a step where two tiles met. Water outlines then lay on
banks and cliffs, which read as rock and as false falls. Files fetched before the fix are
put right as they load.

Outside the US, a region names another source in `terrain.source`; `isoscape sources` lists
them with their credits and licenses, and [Landmarks around the world](world-landmarks.md)
shows one map for each. `ign` (France, 1 m) is cut to order like 3DEP, by IGN's WMS server,
as raw 32-bit heights. The rest are published in fixed pieces that isoscape downloads and
resamples onto its own grid. `swisstopo` (Switzerland, 2 m) comes as one-kilometer squares in
the Swiss grid, found through swisstopo's STAC catalog and converted with swisstopo's
published formulas, good to about a meter. `gsi` (Japan) comes as web-map tiles with heights
packed into their colors: 5 m lidar first, then 5 m photogrammetry, then the 10 m national
model. `copernicus` (worldwide, 30 m) comes as one-degree squares of cloud-optimized GeoTIFF,
read with Deflate and the floating-point predictor. `terrain-tiles` (worldwide) is a mosaic
of open models in web-map tiles. Copernicus is a *surface* model, so forest and roofs are in
its heights. `terrain.fillFrom` names a second source for whatever the first leaves empty,
which is how the Matterhorn's Italian face is filled from Copernicus. The default
`demResolution` is 1 m, or the source's own spacing where that is coarser (30 m for
Copernicus and Terrain Tiles). The cache records which source it came from.

3DEP sometimes fills a gap in its coverage with a large negative number. One patch near
Shockoe Bottom reads −88 m. Any sample below −5 m is treated as missing, along with a
three-pixel rim around it, and filled from its neighbors.

The download covers the frame's circumscribed circle plus a 60 m margin. The camera can turn
after the data arrives (see [Camera](#camera)), and the data still covers the frame. **Builds
never touch the network**, so a build can be repeated exactly.

**Building footprints, beyond OSM.** OSM is thorough in cities and thin in the country.
Around Gwynn's Island it maps 417 buildings, while Microsoft's
[Global ML Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints)
find over 6,000. A region can list `"microsoft"` in `sources.buildings`. `fetch` then
downloads the dataset's parts for the region's zoom-9 quadkeys, keeps the footprints whose
centers fall in the region, and stores them in `data/<region>/footprints.json`. The model
estimates a height for many of them, and that height is kept.

**Land cover.** Rural OSM rarely maps woods and fields. A region with `sources.landcover:
"nlcd"` gets the [National Land Cover Database](https://www.mrlc.gov/) (NLCD 2021) through
the MRLC's map service. That's a 30 m classification of the whole country: forest, wetland,
pasture, crops, scrub and so on. The map image comes back with each class in its legend
color, and each color is matched back to its class. The result is stored in
`data/<region>/landcover.bin.gz`.

Code: `src/osm.ts`, `src/dem.ts`, `src/dem-sources.ts`, `src/rasters.ts`, `src/footprints.ts`, `src/landcover.ts`.

## Region

A place is one JSON file in `regions/`. It sets the center (longitude, latitude), the frame's
width and depth in meters, the camera's bearing and whether it may snap, the scale in pixels
per meter, the tilt, the terrain settings, rules for bridge decks, and the palette. The
README's "Region config" section lists every key.

Positions are converted to local meters east and north of the center. This simple
equirectangular approximation is accurate to a fraction of a meter across a city-sized frame.

Code: `src/region.ts`.

## Camera

The camera is **orthographic**: no perspective, so a building is the same size near and far,
and lengths across the picture can be measured with a ruler. It looks down at a fixed tilt.
The region sets `squash`, the sine of that tilt:

- Ground across the picture is drawn at full scale (`scale` pixels per meter).
- Ground running into the picture is drawn at `squash` of its length. At 0.5 the tilt is 30°,
  the classic 2:1 view of isometric games.
- Heights are drawn at the cosine of the tilt (0.87 at 30°), times any `exaggeration`.

The frame is a rectangle on the ground, square to the camera, so it lands on the screen as a
plain rectangle. That suits a panorama.

**Snap.** Seen from due north, most street grids sit at an awkward angle. With `snap` on,
isoscape measures the dominant direction of every building edge in the frame (weighted by
length, folded so that edges at 0°, 90°, 180° and 270° all count for the same grid). The camera
then turns by up to 45° to put that grid on the picture's diagonals. Downtown Richmond snaps to
a bearing of −8.7°. Set `"snap": false` to keep the bearing you gave.

Code: `src/view.ts`, `chooseBearing` in `src/scene.ts`.

## Ground

Each OSM area is classified by its tags as water, island, park or grass, wood, marsh, sand,
bare rock, parking or cemetery, and drawn as a flat fill in that order. Cover that lies
mostly over water (the trees on a river island) is drawn over the water; the rest is drawn
under it, so a park mapped around a lake, as Central Park is around the Lake, does not paint
the lake over as lawn. Rivers are drawn from
their mapped area, never from their center line. Canals, streams and ditches are drawn as
ribbons of a typical width.

**Roads and rail** become ribbons. A road's width comes from its `width` tag if it has one,
otherwise from its class: 14 m for a motorway, 7 m for a residential street, 1.8 m for a
footway. Tunnels are left out. Railways are 3.2 m ribbons with dashed ties. Weirs and dams
are drawn as white crests.

**Land cover from NLCD**, where a region uses it, goes down first, between the bare ground
and OSM's own areas. Each 30 m class is resampled onto the terrain grid and grouped as woods,
evergreen woods, swamp, marsh, field, crop, scrub or barren. Each group's edge is traced
smoothly through the grid, the same way as the shoreline, so the blocks don't show as
squares. OSM's parks, woods and marshes are drawn on top of it, so mapped detail wins.

Code: `src/classify.ts`, `buildScene` in `src/scene.ts`, cover in `paintStrip` in `src/render.ts`.

## Coastline

OSM does not map the sea, or tidal water like the Chesapeake Bay, as water polygons. It maps
the coastline as lines with the land always on their left. isoscape joins those lines into
chains and cuts them where they cross the frame. It closes each piece of land by walking the
frame's edge, and the water is the frame minus the land. The result can be wrong if the
coastline near the frame is broken or mis-tagged.

Code: `src/coast.ts`.

## Terrain

With terrain turned on, the elevation is resampled onto a regular grid in the camera's
coordinates, every 5 m by default (`cell`). A light blur removes the curbs, rubble and noise
that 1 m lidar records and a 5 m grid would turn into speckle.

The scene's height at any point is its elevation above the lowest point in the frame (the
**datum**), times `terrain.exaggeration`. The sample regions draw hills 2.5–4× taller than
life, so the landform reads from a distance. **Buildings and bridges keep their true heights** on top
of the exaggerated ground, so a 2.5× hill does not stretch the towers standing on it.

Contours are computed from the true elevation; the hillshade from the drawn, exaggerated
surface, so it matches the shape you see:

- **Hillshade.** The ground is lit from the left and a little toward the camera. The light is
  worked out at every grid node, from the surface smoothed once over its neighbors (a 3×3
  blur), so it changes smoothly from node to node. The shading is then drawn as nested bands,
  two to each of 12 steps lighter or darker (24 each way), whose edges are traced with
  marching squares between the nodes. Each band adds a thin wash on top of the one it sits
  in, so the ground shows smooth, soft shading rather than 5 m squares, and no two shades
  meet edge to edge. The shading stops at the traced shoreline and is not drawn on the river.
- **Contours.** Marching squares every 2 m by default (`contour`), with every fifth line
  heavier (`majorEvery`). There are no contours over water.

Code: `src/terrain.ts`, `paintStrip` in `src/render.ts`.

## Rivers

Lidar over a river is not the river. 3DEP's bare-earth surfaces are mostly hydro-flattened,
level across the water and stepping down along it. But OSM's water outline never matches
them to the meter, and rocks, ledges and overlapped banks stand above the water. Draped
naively, the river would climb its own banks.

So the river's surface is **recovered**. At each water point on the grid, it is taken as a
low value (the 15th percentile) of the elevations of all water points within 30 m. It is then
smoothed along the water. The river ends up level across its width and falling along its
course, steeply only where it really drops.

- Water points standing **more than 1 m above that surface**, at least two grid cells (10 m
  at the default 5 m grid) from shore, are drawn as **exposed rock**. These are the boulder fields of the falls.
  Where a hydro-flattened river steps down, the water just above the step stands clear of a
  surface read partly below it; so a rock must also stand more than 1 m above a low value (the
  15th percentile) of the water within 30 m that is level with it or further up the channel. Otherwise every step would be drawn
  as a line of boulders.
- **Only a river gets rocks and rapids.** Water mapped as a river (`water=river`, `rapids` or
  `stream`, or `waterway=riverbank`), or plain `natural=water` with a river or stream line
  running through it, is a river. A lake, pond, reservoir, basin, treatment works, canal,
  dock, pool or fountain, and the sea, are still water: they get neither.
- Nothing is drawn as rock **on ground painted over the river** (a bed of bare rock, a wooded
  island the water outline left in), or **within 20 m of a mapped weir or dam**: the lidar
  sees the dam standing clear of the water, but it is drawn as a crest, not as boulders.
- Near the shore, mapped "water" standing more than 1 m above the surface is treated as bank.
  It is **given back to the land** at its own height.

- Where the elevation source has **no heights** (3DEP leaves much of San Francisco Bay
  empty), the gap is filled in from the shore around it. That fill is a guess, not a surface,
  so no rock is read within 30 m of it, and no fall is read on it or from it.

Both are inferences: a gravel bar mapped as water or a misplaced outline can produce false
rock. Flat regions skip all of this and draw OSM's outlines as they are.

Code: `settleWater` in `src/terrain.ts`.

## Rapids

A rapid is where the recovered water surface **falls quickly along the river**. 3DEP's water
is hydro-flattened: level from bank to bank, stepping down along the river by a meter or
less at a time, with long level reaches between the steps. Measured across a few cells, the
fall is all at the step lines and nil between them, which is not how a river runs.

So the fall is measured **along the channel, over a reach**. First, every point of a river
gets its distance up the channel: the shortest path through the river's own water from where
it rises out of its lowest pool (the water within 5 cm of its lowest level; in Richmond, the tidal James below the Mayo Bridge). Then, at
each water point at least two grid cells from shore, the surface heights of the river around
it, within 200 m and from 50 m below it to 200 m above it along the channel, are fitted
against that distance. The slope of the fit is the fall. This spreads each step's drop over
the 200 m below it, where the water runs white, and reads the pool above a dam as calm to
within 50 m of its crest. Where the fall exceeds `terrain.rapids` (0.004 by default, 4 m per
km), the point reads as a rapid. For comparison, the James falls about 32 m (105 feet)
through Richmond, a little over 3 m per km on average, and its level pools fall about 1 m
per km.

Each rapid point gets short white strokes across the current, **as thick as the fall**: a
stroke in about one point in seven just over the threshold, rising to one in most points and
two in some at four times it (16 m per km), with a faint wash of froth that fades in over the steepest.
The strokes are placed by a hash of the point's position, not at random, so the same data
always draws the same marks. No rapid is drawn on ground painted over the river. Weirs
mapped in OSM are drawn separately.

Rapids are **inferred, not observed**. They show where the lidar surface falls, which is
usually where the water is white, but river level on the day of the survey, where the
hydro-flattening put its steps, or a dam can all mislead it. Until November 2026 the fall was
measured across 40 m against a threshold of 3.5 m per 100 m; once the elevation was put where
it belongs, nothing on the James fell that steeply, and the rapids drawn before had mostly
come from water outlines lying on banks. The build's tab reports how many points were read
as rapids.

Code: `channelFall` and `riverFall` in `src/terrain.ts`, `paintStrip` in `src/render.ts`.

## Shoreline

With terrain, the water's edge is traced from the lidar-corrected water grid (marching squares
over a lightly smoothed mask), not from OSM's outline. Open water is drawn at the river's
surface; a grid cell that is part water and part bank is draped on the ground, so the water
meets the bank at the bank's own height. Where the outline overlaps a steep bank, the bank
slopes into the water instead of the water climbing the bank. Each strip draws the ground it
laps toward the camera from that ground's own grid cells, so its shore there is the same as
the next strip's and the shoreline has no teeth at the strip lines.

Code: `paintStrip` in `src/render.ts`.

## Buildings

Every OSM building that lies **wholly inside the frame** and covers at least
`minBuildingArea` (12 m² by default) becomes a prism. Walls are drawn on the sides facing the
camera, and the roof goes on top. Courtyards work. Wall shading follows which way each wall
faces, with the light from the left. Roof color follows the building's type: homes,
commerce, industry or civic. Where a building is mapped as Simple 3D Buildings parts
(`building:part`), the parts are drawn instead of the outline if the parts that reach the
ground cover at least half of it. Many outlines carry parts only for a crown, a tower or
rooftop works; such an outline is drawn whole, and its parts only above its roof. Parts that
are only roofs (`building:part=roof`) never replace the outline: it stays as their podium. A
building is drawn whole or not at all, so parts whose outline the frame cuts are left out
too. Nothing stands on air: a part raised off the ground (`min_height`) that nothing beside
it holds up, and that is not mapped as a bridge, reaches down to the roof under it or to the
ground (a crown whose shaft is missing from the data, or too small to draw). A bridge tower's
parts (`tower:type=bridge`) are often mapped from the top of the pier up, with the pier left
out, so the lowest of them (no tower part within 40 m starts lower) reach down to the ground
or water; struts between the legs keep their height. Open canopies (`building=roof`) are left
out.

Two shapes are not prisms. A **lattice tower** (`tower:construction=lattice`, such as the
Eiffel Tower) is drawn whole as a spire on its outline, in 16 stacked tapering pieces, in a
darker iron tone. The outline is first cleared of corners within 3% of √area of their
neighbors' line (about 3 m on the Eiffel Tower), so the small jogs where a leg meets an arch
don't run up the tower as slivers, and dots go only at the corners of its foot that face the
camera. Its width follows the Eiffel Tower's curve: e^(−3.3·t) of the base at
height fraction t, so 0.56 at the first platform and 0.32 at the second, running out to a
mast over the top sixth. The parts mapped inside it are dropped. A **curved roof shell with
no height** (a roof part shaped `round`, `spherical` or `circular`, such as the Sydney Opera
House's sails) is drawn as a sail rising to a point, 1.6 × √area meters above its podium.
That height is an approximation, not a survey.

**Footprints from Microsoft's model** fill in where OSM has none. Wherever an OSM building
and a footprint overlap, OSM wins and the footprint is dropped. A footprint is dropped if its
center lies in an OSM building, or if it holds an OSM building's center. A footprint whose
center is on water is dropped too: there the model has found a boat, a pier head or a
boathouse it cannot tell from a house. Buildings mapped in OSM on water, such as boathouses,
stay.

**Heights** are taken from the first of these that the building has:

1. a `height` tag, from a survey or a mapper's estimate (a whole building tagged under 2 m,
   or with a height that can't be read, is taken as having none: Los Angeles County's import
   gives hundreds of hillside houses 0.4 m);
2. **an estimate from Microsoft's model**, for its own footprints, where it made one;
3. `building:levels`, at 3.4 m a floor, plus half a floor for each roof level;
4. **a guess** from the building's type and size: 3.2 m for a shed or anything under 40 m²,
   8 m for a house, 10 m for a terrace, 16 m for apartments or a hotel, 13 m for an office
   (24 m over 1,500 m²), 11 m for industry, 16 m for a church, and 8–14 m by footprint for
   anything else.

Each build counts how many heights came from each source. A view with many guesses has the
right footprints and plausible but invented skylines. Joining real heights from lidar (the
first-return surface minus bare earth) is the top item on the roadmap.

On a slope, a building stands on the **lowest** ground under it, so its walls never float.
The ground is drawn steeper than life but buildings keep their true heights, so the roof is
set by the **true** slope, not the drawn one: it sits at the building's height above the
lowest ground plus half the true fall across the footprint (the drawn fall divided by the
exaggeration). On the downhill side the building shows what it would on the real hill, and
the rest of the drawn relief goes into the hill on its uphill side, so a two-story house on a
steep street stays a two-story house. On flat ground nothing changes. The parts of one
building all count their heights from the level of its outline, and buildings traced from
fire-insurance maps and lost landmarks are seated the same way.

Code: `buildingHeights` in `src/classify.ts`, `extrude` and `spire` in `src/scene.ts`.

## Bridges

OSM splits one bridge into many ways, at every change of lanes, name or junction. Ramping
each piece down to the ground would turn a viaduct into a roller coaster. So bridge ways that
share an end, a layer and a kind (road or rail) are joined into chains first. A chain only
ramps down at an end that touches no other bridge. Bridges that touch form a network,
anchored to the ground at those ends, and no deck stands higher than a 70 m ramp from the
nearest anchor allows, measured along the network: a viaduct that forks into short ways that
each come down a few meters on ramps down to the fork, not standing at full height over a fan
of steep stubs. An end that joins another bridge (a ramp onto a viaduct of another layer, a
link at a fork) meets the higher of the decks there and eases to its own height over 70 m, so
the two arrive at one height. Where a deck comes down to
the ground, its side stops at the ground instead of hanging below it.

**Deck height is a rule of thumb.** OSM rarely records it. A region can name a height for a
bridge, for example `{ "match": "Manchester", "deck": 24 }`. Otherwise the deck sits
`bridgeDeck` meters (7 by default) above the ground for each OSM `layer`. The deck is a taut
line over whatever it crosses: never closer to the ground than its clearance, rising in
straight runs, and easing down over 70 m at a free end. The ramp keeps that length on a short
bridge, so a bridge shorter than two ramps never reaches full height: a 30 m footbridge over a
canal rises well under a meter above its banks, where a 7 m tent would read as a stub floating
in the air. Piers drop to the real ground or water every 38 m where the deck is more than 3 m
up, or to the roof of a building under the deck, never down through it. A span that lies
inside a building and below its roof (a garage ramp, a walkway's landing) is left out: the
building hides it.

Each bridge is cut into spans of at most 22 m, so a long bridge can pass in front of one
building and behind another. Bridges are cut at the edges of the frame.

**A suspension bridge** (`bridge:structure=suspension`) whose towers are mapped as parts
(`tower:type=bridge`) gets its two main cables, drawn as plain lines. The parts standing
within 25 m of the bridge's line make its towers, and the parts either side of the widest gap
across the line are a tower's two legs. Each cable runs from an anchorage on the deck at one
end of the bridge, over the tops of the legs, to the other end: a parabola between towers
that sags to 2 m over the deck at mid-span, and a slighter one down to each anchorage.
Suspenders, tower detail and arches are not drawn.

Code: `chainBridges` and `bridgePieces` in `src/scene.ts`.

## Paint order

The drawing has no depth buffer. Things are painted back to front, and the order is the hard
part. Sorting by a single depth per object fails as soon as a long warehouse sits beside a
small house. So the order is decided **pairwise**, only between objects whose boxes overlap
on screen:

- If their footprints can be separated by a line, the one on the camera's side of that line
  is in front.
- If the footprints overlap (stacked building parts), the one entirely above is in front.
- Two bridge spans that run side by side (within about 14 degrees of parallel, the two
  carriageways of a viaduct or a pair of tracks): the one whose line is nearer the camera is
  in front, or the upper one where one runs right over the other. By centers alone, two
  overlapping decks alternate span by span and read as a ladder.
- Otherwise the nearer center wins.

A topological sort turns these pairwise results into one order. The rare cycle, from concave
footprints that interlock, is broken by depth.

Code: `src/order.ts`.

## Drawing

**The ground is painted in strips**, two grid rows deep (10 m at the default cell size), from
the back of the frame to the front. A landscape hides parts of itself: a bank that falls away
from the camera hides the water behind it. Each strip drapes everything that lies on it over
the terrain: bare ground, parks, water, roads, rail, hillshade, contours, rocks and rapids.
Each building or bridge is painted straight after the strip that holds its front edge, so a
hill in front of it covers it and the ground behind it does not.

The next strip's parks, roads and cover lap 0.6 m back over a strip's near edge, so a strip's
hillshade and contours are shifted the same way: each runs from just past its near edge
(0.6 m plus the width of the edge strokes, about 1.1 m at the sample scale) to the same
distance past its far edge. The ground in that lap is then shaded once, by the strip that
painted it last, and no light streak shows along the strip lines. Where two strips' shading
meets, both trace the same points, so there is no hairline between them.

The front of the plate is a **slab**, a true cross-section of the ground along the near edge,
with water where the cut crosses the river.

**The SVG is compact.** Coordinates are rounded to a tenth of a pixel and written relative to
the previous point. Draped edges are simplified to a quarter pixel, and the soft edges of
hillshade bands to half a pixel: a point is dropped only while the line that replaces it
passes within that distance of every point it stands for. (Until November 2026 each point
was tested against its two neighbors alone, so a long, gently curving edge could drift
several pixels off; across open water, where nothing covers the strips, the gaps showed as
white stripes.) Each dot is a zero-length
line with round caps. Even so, a big region can produce a file of 25–45 MB. The `--png` option
renders a raster with `rsvg-convert`. Colors and line weights come from a palette (`paper`
or `night`).

Code: `src/render.ts`, `src/palette.ts`.

## Time

A region with a `time` section is drawn as a **series**: one scene for each year (epoch) in its
history file, built with `isoscape series <region>`. The downtown Richmond series runs from
the 1737 town plan to today. Each scene combines two kinds of evidence, and the explorer says
which is which.

**Measured: buildings standing today, by the year each was built.** A building appears in
every scene from its year on. The year comes from:

1. a curated year, for a few landmarks whose records are known to be wrong or missing (the
   Capitol, St. John's Church, the Old Stone House and so on), each with a source. A curated
   year can also end: the Capitol's central block (OSM's middle building part) is drawn alone
   from 1788, and its full outline, with the wings of 1904–06, from 1906;
2. else OpenStreetMap's `start_date` tag;
3. else the city assessor's *year built* for the parcel under the building's center.

The assessor records one year per parcel, the year of its main building. Up to four buildings
on a lot (a row split in OSM, a house and its shed) all take that year. With more buildings,
only one clearly larger than the rest takes it. A parcel with eight or more (a campus, Capitol
Square) gives its year to none of them. Buildings with no year appear only in today's scene.

**Curated: what is gone or was different.** A short list per series, each item with its
years and sources: a filled canal basin, a burned district, a buried creek, demolished
landmarks drawn from published dimensions in a red-brown tone (a burned shell in ash gray), and
the town plan, which limits the earliest scene's streets to the original grid. Positions come
from today's street grid. They are not surveyed.

**Traced: buildings from fire-insurance maps.** The Sanborn Map Company drew every building
in a city's business district for insurers, block by block. Each building appears as a
footprint colored by material: pink brick, yellow frame, blue stone, gray iron. The Library of
Congress has Richmond editions from 1886 to 1925 online. isoscape traces them:

1. **Georeference.** Each sheet is placed on the ground by a rotation and shift: at one scale
   per edition, two or three named street corners read off the sheet are enough. A third
   corner checks the first two. The block outlines from the city's GIS are drawn over each
   sheet to confirm the fit (`tools/sanborn/rigid.py`, `ovmosaic.py`).
2. **Trace.** The colored fills are separated from the paper and the printed lines, read for
   material, closed over the lettering, and traced as polygons. Near-rectangles are squared
   up, and outlines and thin strips (river banks, rails) are dropped (`extract.py`).
3. **Follow through time.** A traced footprint mostly covered by a building standing today is
   taken to be that building, or its replacement on the same footprint, and today's data
   already draws it. The rest are **lost buildings**. Each is drawn from the first edition
   that shows it, though it may be older. It is drawn until it is known to be gone, in this
   order of preference: a later edition that maps the spot without it; the year the building
   on its site today went up; the opening of an expressway through it. Failing all of those,
   it is *assumed* gone by 1960, when clearing for parking and highways began
   (`lifespans.py`).
4. **Clean.** A last pass drops slivers, any footprint more than 8 times longer than it is
   wide and under 12 m wide, or over 100 m long and under 8 m wide on average: on the sheets these are rail viaducts, track-side sheds and street
   edges, and extruded they would stand as walls. It then smooths each outline to within 1.5 m,
   so pixel stair-steps do not draw as striped walls. It also drops sprawls (over 2,000 m² and
   filling under 45% of their convex hull: river shading, not buildings) and merges footprints
   traced in two editions that overlap by more than 85%, keeping the earlier start and the later
   end (`clean.py`: 68 dropped, 170 merged).

The historic buildings are sketches, not a survey. A machine traced them from scans of
fire-insurance maps, so outlines are approximate, heights are guessed from material, and some
buildings are missing, misplaced or merged. The 1924 overview ("congested district") sheet is
the least precise source. The historic scenes show the city's shape and density, not each
building exactly.

Traced buildings keep the maps' colors, so they read apart from today's. Their heights are
guessed from their material (brick and stone three stories, frame two): the story counts
printed on the sheets are not read yet; later editions add olive-brown for fire-proof
construction, drawn six stories. The explorer counts, for each scene, how many traced
buildings stand and how each one's end date was found.

Five editions are traced: **1886**; **1895** and **1905** (sheets read by eye); **1924–25**, whose first volume opens with a single
"congested district" map of the whole business district (fitted with a rubber sheet
through sixteen street corners, each snapped to the city's block outlines); and
**1950–52**, a corrected reprint whose sheets were matched feature by feature to their
1924–25 versions where those were fitted, and read by eye otherwise. Each later edition turns
"assumed" end dates into ones read from a map.

**Era rules** date everything else that OSM maps: the first rule matching a feature's name,
`ref` or tags decides the spans in which it existed. Interstates appear from 1958, the
Downtown Expressway from 1976, the river viaducts from 1901, today's Mayo Bridge from 1913 (its
earlier wooden spans are not drawn). The James River and Kanawha Canal appears from 1800 until
the railroad took it over, and again from the Canal Walk of 1999. Interchange ramps follow the
interstate and parking aisles and driveways follow surface parking (1950); both dates are
approximate. A feature no rule matches is drawn in every year, so the Richmond series ends its
rules with catch-alls: the street grid, streams and the river are drawn in every year, and
anything else with no dated rule (parks, cemeteries, dams and weirs, piers, basins, paths) is
drawn only today, since nothing says when it was made. Each catch-all names what still needs a
source.

In every scene after the first, buildings **new since the previous scene** have gold roofs.

**Streets before the houses.** A series can say that minor streets (tertiary and smaller,
service roads and paths) are drawn only where a building of the year stands within so many
meters of them: 75 m in the 1925 streetcar scene, 60 m in the downtown series. Each street is
walked every half that distance and kept if any building (standing today and built by then,
traced from a Sanborn sheet and still standing, or a curated landmark) has a corner within one
grid cell of a step. A suburb whose streets were laid out but not yet built on shows its main
roads only. The downtown series holds its main roads to the same test, because before the
first Sanborn map (1886) the only record of how far the town reached is what still stands. A
street of a town plan (Mayo's grid of 1737) is kept in every year from the plan on, houses or
not, though not the plan's service roads. Today's scene keeps all of today's streets.

**Streetcar lines.** A curated `streetcar` item is a line drawn as a bold red ribbon down the
street, 9 m wide, with a car every 900 m along it: 14 m long and 3.6 m tall like a 1920s
double-truck car, but 5.4 m wide (about twice a real car's width) so its pale roof reads
against the line. A series can scale both up so they read across a whole city: the 1925 scene
draws them three times life size (27 m lines, 42 m cars). The lines come from
`tools/streetcars/build.py`, which reads each line as a list of street corners (from the
1925 plate of the city's early transit routes and the sources cited per line), finds each
corner in OpenStreetMap, and follows the streets between them, preferring the streets the two
corners name (any other street costs six times as much per meter). Two streets that meet
without sharing a node take their closest points, up to 150 m apart. A run over a viaduct
since torn down is drawn straight. Vanished pleasure grounds (a fairground) take a sandy tint of
their own, and a racetrack is a closed dirt-colored ribbon. `--streetcar-scale` overrides the
series' scale for one build: the single-stop prints of the streetcar series use 1.5, so the
lines read thinner up close.

The fair grounds are traced from sheet 468 of the 1924–25 Sanborn atlas (100 feet to the inch,
0.403 m per pixel of the scan, north up, fixed at Hermitage Road and Sherwood Avenue): the
outline follows the Boulevard and Hermitage Road to the tip where they meet, the one-mile
track's south turn (a radius of 83 m) is taken off the sheet with its straights parallel to
the Boulevard, and the north turn is drawn to make up the mile. Thirty-six of the fair's buildings
come from the same sheet. A curated *site* (the fair grounds while the fair stood, a station's
loop of tracks) clears today's streets, lots and buildings from within it.

## One building, close up

Broad Street Station in 1943 is modeled from parts
(`tools/stations/broad_street.py`): wings, center pavilion, porch, six columns and two piers,
entablature, drum and a dome (a quarter circle in ten steps), each with a height above its
seat, and the concourse seated on the high side of the ground so it bridges the tracks. A part
can rest on another: the columns and piers stand on the porch and the entablature on the
columns, so on the sloping forecourt all six columns share one base and one top. The
station's own colors live in the palette's `parts`: limestone, the dome's tile, the iron and
roofing of the platform canopies, ramp houses, and the trains. Nine tracks follow the
surviving platforms through the station and the USGS quadrangles of 1934 and 1956 around the
loop, gathering into four and then two within 110 m of each end. Canopies are cut into 12 m
pieces, each on a column, 8 m wide and 5.4 m up; trains are a steam engine (18 m, with a
cab), its tender (11 m) and 26 m heavyweight cars, 1 m apart. At 1.5 pixels per meter or
closer, track is drawn with its ties (0.25 m every 0.67 m) and its two rails, 1.44 m apart.
A series can draw track wider than life (`railScale`, or `--rail-scale` for one build) and in
the ties' darker tone, so a network reads across a city: the wide railroad map uses four
times. Curated labels name places on the map; the single-place prints of a set leave them
out.

## Sets: a map framed by its places

`tools/sets/set.py` frames a big map with up to fourteen
numbered boxes (the 1925 streetcars use one per stop), each 1,800 m of ground across, cut from
the scene of its own year and rasterized from the vector at the pixels it fills, with a note
written from the sources stored beside it. The same tool makes the map alone, a print per box
(2,100 m across), canvas files with 1.5 in of mirrored wrap, and the box's page in the explorer.
`isoscape locate` tells it where each box falls in the picture. A set is one file,
`sets/<name>.json`; "Making a set" in the README walks through one.

**What the series cannot show:**

- **Survivorship.** Only buildings standing today are measured. Downtown Richmond in 1900 had
  far more buildings than the 1900 scene, because most of them were torn down later. The
  scenes show what survives, plus the few curated losses.
- **Heaped years.** Assessors often round: in this data, many buildings are dated to exactly
  1900 or 1910. Read the decades loosely.
- **Today's ground.** The elevation is today's lidar, so the I-95 cut through Shockoe Valley
  is there in 1737. Curated water is laid flat at the lowest ground beneath it.
- **The jump to today.** Undated buildings appear only in today's scene, so the last step of a
  series adds many more buildings than really went up in that interval.

Code: `src/history.ts`; the history file is `history/<series>.json`; the tracing tools are in
`tools/sanborn/` (Python: NumPy, SciPy, OpenCV, Shapely), and their output is
`history/sanborn/`.

## Plates and the title block

Every print and canvas carries a small title block in its bottom-right corner, like the corner
of a drafting sheet: the isoscape cube, the maker, the piece's place in the catalog (collection,
set and piece), its plate number, version, the year it was drawn, the point the view was drawn
around and the direction it faces. On a 36 × 24 in sheet it is 1,690 × 239 pixels at 300 dpi,
about 5.6 × 0.8 in; smaller sheets scale it by the square root of their long side over 36 in
(so 4.6 in across on a 24 × 18), which keeps it legible. Its right edge lines up with the art,
and it sits as low as the art's side margin allows, with clear paper around it a third of its
height wide. Where the foot of a sheet is full (the two set sheets) it sits in the header
instead, and only if no place fits at full size is it shrunk, in steps of a tenth. On a canvas it
goes on the face, never the wrap. The plates themselves are listed in `catalog/plates.json`.

## Archive and explorer

Every build is kept under `out/builds/<timestamp>-<name>/` as the SVG, a thumbnail and a
`meta.json`. The meta file records:

- the region's settings;
- the camera bearing used;
- every count the build measured (features, ground areas, buildings by height source, bridge
  spans, rapid cells, contour segments, strips);
- the build's time and file size;
- the git commit, its subject, and whether `src/` or `regions/` had uncommitted changes;
- an optional `--note` saying what the build was trying;
- for a dated scene, its year, the year before it in the series, and the curated features
  drawn in it, with their sources.

`backfill` builds an older commit's code against today's cached data, so the archive can
include outputs from before it existed.

After every build, `out/index.html` is rewritten: this explorer. It is a single file with the
build list and these pages embedded in it, so it opens from disk with no server. The pages are
Markdown files in `pages/`. To add one, see the README.

Beside it go plain pages that need no script, for search engines and link previews: each of
these pages as `p/<slug>.html`, each map as `m/<region>.html` (and each year of a dated series
as `m/<region>-<year>.html`) with its picture and this same "How this view was made" text, and a
`sitemap.xml` listing them all.

Code: `src/archive.ts`, `src/explorer.ts`, `src/pages.ts`, `src/story.ts`, `src/static-pages.ts`.

## Credits

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available
under the Open Database License. Elevation from the [USGS 3D Elevation
Program](https://www.usgs.gov/3d-elevation-program), public domain, and outside the US from
the sources credited on [Landmarks around the world](world-landmarks.md). Years built for the
Richmond series from the City of Richmond's open data. Fire-insurance maps from the Library
of Congress Sanborn Maps Collection. See [About](about.md) for what that means when you use
or share a picture.

Inspired by [Isometric SF](https://isometricsf.com), Justin Chavez's isometric pixel-art map
of San Francisco ([how it was made](https://www.justinchavez.com/blog/isometric-sf-how/)).
