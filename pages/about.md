---
title: About, credits and licenses
order: 90
summary: What isoscape is, whose data it draws, and what to credit when you share a picture.
---

# About, credits and licenses

isoscape makes isometric dot-and-line views of real places from open map data. It is a
sibling of [dotscene](https://github.com/busse/dotscene). The two share a visual language,
but dotscene is for drawing a scene by hand, and isoscape *surveys* one: you choose a frame on
the world, and the data decides the rest. [How it's made](how-its-made.md) explains each step.

## How it was made

isoscape was built, and the shop is run, in chats with Claude, Anthropic's AI, using
Claude Opus 5.5, directed and reviewed by Chris Busse. Claude wrote the code, traced the
historic buildings, laid out the prints, and set up the shop. Chris Busse draws the maps with
isoscape, in code, from open data; nothing is drawn by hand. The historic years are
machine-traced sketches.

## Try it yourself

Open a chat with Claude (we used Claude Opus 5.5) and say:

> Use the GitHub repo busse/isoscape to make an isometric map of *your place*.

It takes a few minutes. Terrain works anywhere: from USGS lidar in the US, from national
mapping agencies in France, Switzerland and Japan, and from the European Space Agency's 30 m
Copernicus model everywhere else. [Landmarks around the world](world-landmarks.md) shows one
of each.

## Contact

isoscape is by Chris Busse.

- Website: [fullbacklog.com](https://fullbacklog.com) (Substack)
- LinkedIn: [linkedin.com/in/chrisbusse](https://linkedin.com/in/chrisbusse)
- Threads: [@busse](https://www.threads.net/@busse)
- Instagram: [@busse](https://www.instagram.com/busse)

## Visitor statistics

This site uses Google Analytics to count visits: which pages and maps are opened, and which
site sent the visitor. It sets cookies to do that. Links to the shop carry a tag naming the page
they were clicked on. A copy of the explorer you build yourself has no analytics unless you add
an `analytics` entry to `isoscape.config.json`.

## Inspiration

isoscape began as an attempt to draw Richmond the way [Isometric SF](https://isometricsf.com)
draws San Francisco: Justin Chavez's isometric pixel-art map of the city. His write-up,
[how it was made](https://www.justinchavez.com/blog/isometric-sf-how/), set out the idea
this project follows: an isometric city view drawn from open map data. isoscape's code and
drawing style are its own, but the idea came from his work.

## Data

**OpenStreetMap.** Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors, available under the [Open Database License
(ODbL)](https://opendatacommons.org/licenses/odbl/). The cached `data/*/osm.json` files are
OSM data and carry that license. A rendered picture is a *produced work*. You may use it, but
it must credit OpenStreetMap wherever it is shown. Every SVG isoscape writes carries the
credit in its description, and every page shows it.

**Historic scenes are sketches.** Their lost buildings are traced by machine from Sanborn
fire-insurance maps, so outlines and heights are approximate. They show the city's shape, not
a building-by-building survey.

**Elevation.** In the US, from the [USGS 3D Elevation Program
(3DEP)](https://www.usgs.gov/3d-elevation-program), served by the National Map. It is in the
public domain. The USGS asks for, but does not require, a credit. `data/*/dem.bin.gz` is a
resampled copy.

**Elevation outside the US.** Each of these allows commercial use, and each asks for a credit:

| Source | License | Credit to carry |
|---|---|---|
| [IGN RGE ALTI®](https://geoservices.ign.fr/rgealti) (France) | Licence Ouverte 2.0 (Etalab) | RGE ALTI® © IGN |
| [swisstopo swissALTI3D](https://www.swisstopo.admin.ch/en/height-model-swissalti3d) (Switzerland) | swisstopo free geodata (OGD) terms | swissALTI3D © Federal Office of Topography swisstopo |
| [GSI elevation tiles](https://maps.gsi.go.jp/development/ichiran.html) (Japan) | GSI content terms (compatible with CC BY 4.0) | GSI elevation tiles, processed (地理院タイル（標高タイル）を加工して作成) |
| [Copernicus DEM GLO-30](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) (worldwide) | Copernicus WorldDEM-30 license | produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved |
| [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (worldwide) | each source's own; see [Tilezen's attribution list](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) | Terrain Tiles (Mapzen/Tilezen); SRTM courtesy of the U.S. Geological Survey; ETOPO1 courtesy of NOAA |

`isoscape sources` prints the same list. Every map names its own source in its caption.

**Building footprints (some regions).** [Microsoft Global ML Building
Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints), under the ODbL like OSM.
A view that uses them should credit Microsoft as well.

**Land cover (some regions).** The [National Land Cover Database](https://www.mrlc.gov/)
(NLCD 2021) from the USGS and the Multi-Resolution Land Characteristics Consortium. It is in
the public domain.

**Fire-insurance maps (dated series).** Sanborn Fire Insurance Maps of Richmond, as digitized
by the [Library of Congress](https://www.loc.gov/collections/sanborn-maps/). The editions used
were published long enough ago to be out of US copyright. Check each item's rights statement
on the Library's site before reusing the scans. The traced footprints in `history/sanborn/`
are derived from them, and are free to reuse under CC0: see [Data](data.md) for those and
the other datasets made for these maps, with their licenses.

**Years built (dated series).** The Richmond series uses the City of Richmond's *Year of
Construction* layer, published on the city's ArcGIS open data service. Check the city's terms
before redistributing `data/*/yearbuilt.json`. The curated history in `history/` cites its
sources item by item.

## Sharing a picture

Put this line with the picture. Drop the second part for a view drawn without terrain, and
outside the US use that source's credit from the table above instead of USGS 3DEP:

> Map data © OpenStreetMap contributors (ODbL) · Elevation: USGS 3DEP

and, where a region draws on them, add: · Building footprints: Microsoft (ODbL) · Land cover: NLCD 2021

Say what is estimated as well as what is measured. Many building heights are guesses, deck
heights are rules of thumb, and rapids are inferred from the lidar (see
[Measured, inferred, guessed](how-its-made.md#measured-inferred-guessed)). A view used in
planning or teaching should not be read as a survey.

## Code

isoscape is written in TypeScript and runs directly on Node 22.18 or newer, with no runtime
dependencies and no build step. `package.json` declares the MIT license. `CLAUDE.md` sets out the conventions for changing the code, and the README covers
commands, region configs and adding a page like this one.
