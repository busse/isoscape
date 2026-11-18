---
title: Data
order: 92
summary: The datasets made for these maps, free to download: Richmond's lost buildings, the Sanborn traces, the streetcar lines and the dated history.
---

# Data

Drawing these maps meant making datasets that didn't exist before. This page lists them, with
what each one holds, how approximate it is and its license, so anyone can reuse them. Each
link opens the file as it stands at one fixed commit of the repo, so it will not change under
you. The current versions are in the same paths on
[GitHub](https://github.com/busse/isoscape).

I made all of these with isoscape, the tool I built with Claude and draw the maps with (see
the [artist statement](artist-statement.md)). The tracing and the dates were worked out in
code, with Claude, under my direction. Nothing here was traced by hand, and none of it is a
survey.

## Licenses in short

- **CC0** ([public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/)):
  the Sanborn traces and Richmond's lost buildings. They are made from public-domain maps, so I
  give them away with no conditions. A credit is welcome but not required.
- **ODbL** ([Open Database License](https://opendatacommons.org/licenses/odbl/)): anything
  whose coordinates come from OpenStreetMap. That covers the georeferencing control points,
  the streetcar lines and the dated history files. OSM's license requires this. Credit
  "© OpenStreetMap contributors", and share what you build from these files under the ODbL too.

The maps themselves are licensed separately (CC BY-NC 4.0); see
[About, credits and licenses](about.md).

## Richmond's lost buildings

[`history/sanborn/lost.geojson`](https://github.com/busse/isoscape/blob/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/history/sanborn/lost.geojson)
(GeoJSON, 1.2 MB) · CC0

2,492 footprints of buildings in downtown Richmond that the Sanborn maps show and that are no
longer standing. Each carries:

- `from`: the first edition it appears in. It may be older; the map cannot say.
- `to`: the first year it is known to be gone, and `end`, the evidence for that year: `map` (a
  later edition maps the spot without it; 1,503 buildings), `rebuilt` (the year built of what
  stands there today; 66), `highway` (an expressway opened through it; 84), or `assumed` (839).
  An assumed `to` is 1960, the start of the era that cleared most of downtown for parking.
  Treat it as a placeholder, not a date.
- `material` (brick, frame, iron, fireproof, stone, special), read from the map's colors,
  `storeys` (assumed from the material), and the `edition` and `sheet` it was traced from.

**How approximate.** A building counts as lost when today's buildings cover less than half of
its traced footprint, so one rebuilt on the same footprint counts as standing. Positions are
only as good as each sheet's fit (below), which rests on two or three corners and is not
measured further here. Shapes cleaning took for something other than a building (long thin
strips such as viaducts and sheds along tracks, and big sprawls that were river shading) were
dropped, and their ids are in `clean-dropped.json` beside the file. Two traces of one building
in two editions are merged into one. `storeys` is not read from the map; it is assumed from
the material.

## Sanborn traces by edition

[`history/sanborn/`](https://github.com/busse/isoscape/tree/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/history/sanborn)
(GeoJSON, 0.7–1.5 MB each) · CC0

Every building footprint traced from five editions of the Sanborn Fire Insurance Maps of
Richmond in the [Library of Congress](https://www.loc.gov/collections/sanborn-maps/): 1886
(1,192), 1895 (1,214), 1905 (1,545), 1924–25 (2,330) and 1950 (1,542). Each footprint keeps
its edition, sheet, material (from the map's colors), storeys and area in square meters.

**How approximate.** Each sheet was fitted to the ground by a rigid fit to two or three
street corners (a third corner flags a misread). The buildings were then traced in code from
the colored fills, split along the printed party walls. Storeys are assumed from the material
(brick 3, frame 2, iron 4, fireproof 6). The traces cover only
the sheets that were fitted (some edge sheets are left out), and shapes the cleaning dropped
are not in them.

## Georeferencing control points

[`tools/sanborn/cps*.json`](https://github.com/busse/isoscape/tree/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/tools/sanborn)
(JSON, 8 files, 358 points) · ODbL

The street corners that tie each Library of Congress sheet to the ground: for each sheet, the
pixel on the scan, the longitude and latitude, and the corner's name ("5th & Marshall"). They
are in editions 1886, 1895, 1905, 1924, 1925 and 1952, with a separate set for the 1924
central business district. With them, anyone can georeference the same scans again.

**How approximate.** Each coordinate is today's OpenStreetMap intersection of the two named
streets, which is why these are ODbL. Where a street has moved since the map was drawn, the
corner is where it is now.

## Richmond's streetcars, 1925

[`tools/streetcars/routes.json`](https://github.com/busse/isoscape/blob/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/tools/streetcars/routes.json)
and [`stops.json`](https://github.com/busse/isoscape/blob/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/tools/streetcars/stops.json)
(JSON) · ODbL

The 16 car lines of 1925 as a list of named corners, and the 14 stops and attractions on the
[streetcars map](streetcars.md), each with its sources. They follow Harland Bartholomew &
Associates' plate "Early Transit Routes, 1888 & 1925" (City Planning Commission, 1943). The
placed lines, as drawn on the map, are in `history/richmond-streetcars.json` (below).

**How approximate.** The plate is a small diagram, so each line was read as a list of corners,
and the track between them follows today's streets: the shortest path over OpenStreetMap's
street graph, kept to the named street. Where no street follows a line today (its own
right-of-way, a viaduct since torn down), it runs straight between two points. Lines are drawn
down the middle of divided roads and smoothed at corners.

## Dated, sourced history

[`history/*.json`](https://github.com/busse/isoscape/tree/36f384219e7acfd5fbabb27f387c8b38dcdf1f13/history)
(JSON, 6 files) · ODbL

The curated history behind the dated maps: downtown Richmond through time, the streetcars,
Broad Street Station and its rail lines, and Main Street Station. These files hold dated
outlines, epochs and era rules, each citing its source or stating plainly that it is
approximate. Each file opens with a `method` note on how it was put together.

**How approximate.** As each item's own source says. Outlines are placed from today's
OpenStreetMap street intersections and the dimensions the sources give; they are not surveyed.
