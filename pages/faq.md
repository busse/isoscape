---
title: Questions and answers
order: 95
summary: Short answers about how the maps are made, what Claude does and what the code does, what is measured and what is guessed, the prints, and making your own.
social: faq-social.jpg
unlisted: true
schema: FAQPage
---

# Questions and answers

Short answers to the questions people ask about isoscape. Each one links to the longer
explanation, mostly in [How it's made](how-its-made.md). Every answer here has its own link:
the address of its heading.

*Drafted with Claude; see the [artist statement](artist-statement.md).*

## Claude and the code

### Does Claude handle the projection, or the map geometry too?

Claude wrote the code that does both, under my direction, and the projection is the smallest
part of it. The geometry itself comes from open data, not from Claude.

**The geometry comes from data.** Streets, water and building outlines come from
OpenStreetMap. The ground comes from USGS 3DEP lidar (or a national elevation model outside
the US). The dates of Richmond's standing buildings come from the city's year-built records,
and its lost buildings are traced from Sanborn fire-insurance maps in the Library of Congress.
On Gwynn's Island, buildings that OpenStreetMap lacks come from Microsoft's ML building
footprints. [What is measured](#what-is-measured-what-is-inferred-and-what-is-guessed), below,
shows which of these are measured and which are inferred or guessed.

**The code turns that data into the drawing.** Claude wrote the code, under my direction, and
the code does far more than project. It reads what each tag means, guesses heights where none
are mapped, finds the river's surface and its rapids in the lidar, raises bridges, decides
what hides what, and paints the ground in strips from far to near. The projection itself is
one small step: [the camera](how-its-made.md#camera), about 90 lines of some 14,000.

![From data to drawing: fetch from OpenStreetMap and elevation into a local cache, then eight build steps, read, classify, the year, camera, terrain, scene, order and draw, each with its module; the camera step, view.ts, is marked as the projection, about 90 lines of some 14,000](pipeline.svg)

The code is deterministic: the same data and the same commit give the same SVG, byte for byte.
`build` never touches the network; only `fetch` does. So I draw the maps with isoscape, in
code, and no step of a build asks Claude, or any other model, anything.

### Is any of this AI-generated imagery?

No. No image model draws anything. Every line in a map is computed from the data by the code,
and you can rebuild any map from its commit and its data and get the same file.

Models and judgment do touch the *data* in a few places, and I want to be exact about them:

- **Microsoft's building footprints** were traced from aerial imagery by Microsoft's model.
  isoscape uses them only where a region asks for them (Gwynn's Island), only where
  OpenStreetMap has no building, and with the model's height where it gave one.
- **Land cover** on Gwynn's Island (woods, fields, wetlands) is the USGS National Land Cover
  Database, classified from satellite imagery at 30 m.
- **Placing the Sanborn sheets.** To fit each scanned sheet to the ground, Claude read two or
  three named street corners off it, from labeled contact sheets, and matched them to
  OpenStreetMap's intersections. A third corner checks the first two, and the city's block
  outlines are drawn over every sheet to confirm the fit. A sheet whose fit is known to be wrong
  is left out. The tracing itself is image processing (separating the maps' colored fills),
  not a model.
- **The curated history**: lost landmarks, the dates of tall buildings, the rules that date
  roads, rail and water. Claude wrote these into the history files from published sources, and
  every item cites its source or says plainly that it is approximate.

[Measured, inferred, guessed](how-its-made.md#measured-inferred-guessed) and
[Time](how-its-made.md#time) have the details.

### What do I do, and what does Claude do?

I'm the artist: I decide what to draw and how it should look, set the rules and the limits,
look at what comes back, and decide what to keep. Claude writes and changes the code, runs the
builds and the checks, and reports what changed, with pictures, always under my direction. The
code computes the drawing.

![Who does what: three lanes. Chris Busse, the artist, decides what to draw, sets the rules and limits, looks at every result and decides what to keep. Claude, under his direction, writes and changes the code, runs builds, tests and checks, and reports with pictures. isoscape, the code, computes the drawing from open data, the same every time. Arrows run down (asks; runs a build) and back up (shows the result; SVG, counts, warnings)](faq-who-does-what.svg)

Most of my part is writing down what a good map should look like and throwing out the ones
that aren't. The rules live in the repo, in `CLAUDE.md`, so they hold from one session to the
next. I say more about working this way in the [artist statement](artist-statement.md).

### What happens when something is wrong?

It is fixed in the code, and the map is drawn again. A published print is never changed in
place: it is redrawn as the next version, and the [Changes](changes.md) page says what changed,
when, and in which version. Version 4 of the Richmond prints, for example, corrected a missing
span of the Mayo Bridge in 1925 and left out traced buildings that had landed in the river.

## Measured, inferred, guessed

### What is measured, what is inferred, and what is guessed?

![Where the geometry comes from: OpenStreetMap gives streets, rail, water, parks and building outlines (measured), heights where tagged (measured) and other heights (guessed). USGS 3DEP lidar gives the ground (measured) and the river surface, rocks, rapids and shoreline (inferred). Microsoft footprints and NLCD land cover, on Gwynn's Island, are inferred. City year-built records give the year each standing building went up (measured). Sanborn maps give lost buildings (inferred) and their heights from material (guessed). Bridge deck heights are rules in the code (guessed)](faq-sources.svg)

- **Measured:** the ground (1 m lidar in Richmond), and everything OpenStreetMap maps: streets,
  rail, water, outlines, and heights where mappers tagged them.
- **Inferred from a measurement:** the river's surface, the exposed rock and the rapids (from
  the lidar), the shoreline (mapped water checked against the lidar), and the outlines traced
  from Sanborn maps.
- **Guessed:** building heights with no tag, from the building's type and size. In downtown
  Richmond about 40% of heights are guesses; around Gwynn's Island, a little over half. Bridge
  deck heights are rules of thumb, and every traced historic building's height is assumed from
  its material.

Each map in the explorer says, under "How this view was made", how many of its heights came
from each source.

### Why do some buildings look the wrong height?

Because many heights are guesses. A building with no `height` or `building:levels` tag gets
one from its type and size: 8 m for a house, 16 m for apartments, 13 m for an office, and so on
([Buildings](how-its-made.md#buildings)). The footprints are right; the skyline is plausible,
not surveyed.

## The historic years

### How accurate are the historic years?

They are sketches of the city's shape and density, not a survey of each building. A dated
Richmond map combines:

- buildings standing today, each shown from the year it was built (a curated date, else
  OpenStreetMap's, else the assessor's);
- buildings since lost, traced by machine from the 1886, 1895, 1905, 1924–25 and 1950–52
  Sanborn maps, with their heights assumed from their material;
- a short list of curated features (a filled canal basin, a burned district, demolished
  landmarks), each with its sources;
- rules, each with a source or marked approximate, that date roads, rail and water.

What they cannot show: the many buildings that were lost and never traced, assessors' rounded
years, and the ground, which is today's lidar in every year. Traced buildings that could not
have stood where they fall (in the river, under a viaduct, or buried in a later embankment) are
left out whole, never trimmed: in 1925, 27 on water, 61 on viaducts or track and 62 buried.
[Time](how-its-made.md#time) has the whole method, and [Changes](changes.md) lists every
correction.

## How a map gets made

### How does a map get made, step by step?

1. A region file, `regions/<name>.json`, names a center, a width and a depth in meters.
2. `fetch` downloads OpenStreetMap and the elevation into a local cache. It is the only step
   that uses the network.
3. `build` draws the SVG from the cache, every time the same way (the diagram above).
4. I look at it: the whole picture and close crops, in the explorer, compared with the last
   build.
5. For a print, the scene is composed with its title, credit line and title block, recorded,
   and checked (below).

```sh
node bin/isoscape.js fetch richmond-downtown
node bin/isoscape.js build richmond-downtown-topo --png
```

Every build lands in the explorer, `out/index.html`, with the commit it was built from.

### Why isometric, and why dots and lines?

An isometric view lets you take in a whole neighborhood at once. The dots and lines are the
visual language of [dotscene](https://github.com/busse/dotscene), my other project: inked
edges, a dot on every corner, flat fills. The idea of an isometric city drawn from open map data
came from Justin Chavez's [Isometric SF](https://isometricsf.com).

## Making your own

### Can I make my own map? What do I need?

Yes. isoscape is free and open source (MIT). You need Node 22.18 or newer, and nothing else to
draw a map: there are no runtime dependencies and no build step. `rsvg-convert` makes PNGs. Then
write a region file for your place, `fetch`, and `build`. Terrain works anywhere: USGS lidar in
the US, national models in France, Switzerland and Japan, and Copernicus elsewhere. The
[README](https://github.com/busse/isoscape) has the commands and the region settings. A map
you make is yours; credit OpenStreetMap wherever it is shown ([About](about.md#sharing-a-picture)).

### How do I use it with Claude or another coding agent?

Open a chat with Claude and say: "Use the GitHub repo busse/isoscape to make an isometric map of
*your place*." Claude clones the repo, writes the region file, fetches the data and builds the
map. It takes a few minutes.

![Using it with an agent: you say what to draw and look at the picture; Claude, in the app or a terminal, reads CLAUDE.md and AGENTS.md and follows the loop; the repo holds the region file, fetch, build with --png, the explorer at out/index.html, npm test and typecheck, and the visual check](faq-agent.svg)

The repo tells an agent how to work in it. `CLAUDE.md` is the working contract: the
conventions, where to change what, the known limits, and the loop. `AGENTS.md` holds notes for
agents helping someone use isoscape; Codex, Cursor and other agents that read `AGENTS.md` get
them too, and `GEMINI.md` points Gemini to it. The loop is the
part that matters most: never judge a change from the numbers alone; build it, look at the
picture, compare it with the last build, then keep it or undo it.

A good request names the place, says what you want to see, and asks for a picture back. "Make
the river bluer" is fine; so is "the bridge in the middle ends in the air, fix it". Then look at
what comes back, and say what is wrong.

### How is the codebase kept in order when an AI writes most of it?

By rules written down in the repo, and checks that enforce them:

- **Types.** `npm run typecheck` runs the TypeScript compiler over everything, limited to
  syntax Node can run directly (no enums, no namespaces).
- **Tests.** `npm test` runs about 170 tests, among them that every link in these pages lands
  on a real section. The tools in Python have their own.
- **The visual check.** Before any change to shared drawing code is published, seven watched
  views behind the sold prints are built and compared, crop by crop, with an approved baseline.
  A crop fails if more than 0.02% of its pixels change. The baseline is approved again only
  after a person has looked at every change.
- **One place for each thing.** Every color and line weight is in `palette.ts`; nothing else
  may name one. `build` never touches the network. One bad OpenStreetMap tag must never break a
  build.
- **Pages say what the code does.** How it's made gives the real numbers, and a change to one
  in the code changes the page in the same commit.
- **Release records.** Every design for sale has a record: the commit, every input by SHA-256,
  and a frozen copy of its data. `check.py --rebuild` rebuilds each scene from that commit and
  data and checks it comes out byte for byte the same.
- **Plates and versions.** A design's plate number is permanent and never reused; a fix is a
  new version, never an edit in place, and the Changes page lists it.

Every build is also archived with its commit, so any two can be compared side by side.

### What data does it use, and under what licenses?

- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, under the
  Open Database License (ODbL).
- Elevation in the US from the USGS 3D Elevation Program, public domain; elsewhere from IGN,
  swisstopo, GSI, Copernicus or Terrain Tiles, each with its own credit.
- Land cover from the National Land Cover Database (NLCD 2021), public domain.
- Building footprints, where a region uses them, from Microsoft's Global ML Building
  Footprints, under the ODbL.
- Sanborn fire-insurance maps of Richmond, as digitized by the Library of Congress.
- Years built from the City of Richmond's open data.

The code is MIT-licensed. My published maps are © Chris Busse under CC BY-NC 4.0: share and
adapt them with credit, but not for sale. [About](about.md#data) has every credit in full.

## Prints

### What am I buying when I buy a print?

A print of one of my maps, made to order from a print file that is drawn, composed and recorded
as described above. Prints are in the holiday shop at [chrisbusse.com](https://chrisbusse.com/),
open through December 31, 2026; buying one supports the project.

![From drawing to print: build the scenes, look at them at print size with the visual check, compose the print, set the title block with plate and version, write the release record, run the rebuild check, and print to order through the shop; a fault found after release goes round again as the next version, and the Changes page says what changed](faq-print.svg)

### What does the title block on a print mean?

It is the small block in the bottom-right corner, like the corner of a drafting sheet: the
isoscape cube, the maker, where the piece sits in the catalog (collection, set and piece), its
plate number, its version, the year it was drawn, the point the view was drawn around and the
direction it faces ([Plates and the title block](how-its-made.md#plates-and-the-title-block)).

The **plate** (RVA·01, for Richmond in 1925) is permanent and never reused. The **version**
goes up each time the design is redrawn.

### What happens if a map I bought is corrected later?

The plate stays the same and the version goes up: a print ordered after the change is made from
the new version, and the version is on the print. The [Changes](changes.md) page lists every
correction, dated, with the version.
