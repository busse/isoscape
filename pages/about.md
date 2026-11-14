---
title: About, credits and licences
order: 90
summary: What isoscape is, whose data it draws, and what to credit when you share a picture.
---

# About, credits and licences

isoscape makes isometric dot-and-line views of real places from open map data. It is a
sibling of [dotscene](https://github.com/busse/dotscene). The two share a visual language,
but dotscene is for drawing a scene by hand, and isoscape *surveys* one: you choose a frame on
the world, and the data decides the rest. [How it's made](how-its-made.md) explains each step.

## Contact

isoscape is by Chris Busse.

- Website: [fullbacklog.com](https://fullbacklog.com) (Substack)
- LinkedIn: [linkedin.com/in/chrisbusse](https://linkedin.com/in/chrisbusse)
- Threads: [@busse](https://www.threads.net/@busse)
- Instagram: [@busse](https://www.instagram.com/busse)

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
OSM data and carry that licence. A rendered picture is a *produced work*. You may use it, but
it must credit OpenStreetMap wherever it is shown. Every SVG isoscape writes carries the
credit in its description, and every page shows it.

**Elevation.** From the [USGS 3D Elevation Program
(3DEP)](https://www.usgs.gov/3d-elevation-program), served by the National Map. It is in the
public domain. The USGS asks for, but does not require, a credit. `data/*/dem.bin.gz` is a
resampled copy.

**Building footprints (some regions).** [Microsoft Global ML Building
Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints), under the ODbL like OSM.
A view that uses them should credit Microsoft as well.

**Land cover (some regions).** The [National Land Cover Database](https://www.mrlc.gov/)
(NLCD 2021) from the USGS and the Multi-Resolution Land Characteristics Consortium. It is in
the public domain.

**Fire-insurance maps (dated series).** Sanborn Fire Insurance Maps of Richmond, as digitised
by the [Library of Congress](https://www.loc.gov/collections/sanborn-maps/). The editions used
were published long enough ago to be out of US copyright. Check each item's rights statement
on the Library's site before reusing the scans. The traced footprints in `history/sanborn/`
are derived from them.

**Years built (dated series).** The Richmond series uses the City of Richmond's *Year of
Construction* layer, published on the city's ArcGIS open data service. Check the city's terms
before redistributing `data/*/yearbuilt.json`. The curated history in `history/` cites its
sources item by item.

## Sharing a picture

Put this line with the picture. Drop the second part for a view drawn without terrain:

> Map data © OpenStreetMap contributors (ODbL) · Elevation: USGS 3DEP

and, where a region draws on them, add: · Building footprints: Microsoft (ODbL) · Land cover: NLCD 2021

Say what is estimated as well as what is measured. Many building heights are guesses, deck
heights are rules of thumb, and rapids are inferred from the lidar (see
[Measured, inferred, guessed](how-its-made.md#measured-inferred-guessed)). A view used in
planning or teaching should not be read as a survey.

## Code

isoscape is written in TypeScript and runs directly on Node 22.18 or newer, with no runtime
dependencies and no build step. `package.json` declares the MIT licence. `CLAUDE.md` sets out the conventions for changing the code, and the README covers
commands, region configs and adding a page like this one.
