# Redlining story: datasets, licenses and credits

Every dataset the story's pictures and numbers use, where it came from, when, and on what terms.
Drafted with Claude for Chris Busse, November 21, 2026. Nothing here is for sale, and nothing
built from the Mapping Inequality polygons may be sold (see below).

## Used

| Dataset | Where it is | Fetched | License / terms | Used for | Sold work? |
|---|---|---|---|---|---|
| Mapping Inequality, Richmond 1937 polygons (48 graded areas and one ungraded "Industrial and Commercial" area) | `data/holc/richmond-1937.geojson`, **not committed** (see below). From https://dsl.richmond.edu/panorama/redlining/static/citiesData/VARichmond1937/geojson.json, SHA-256 `8fe7b5cf91cdd7591eeec07c2b053404ad7bc746d62c1b7f061959ce6a49014e`, 57,196 bytes, Last-Modified Aug. 19, 2024 | Nov. 21, 2026 | The DSL's data page: "The georectified rasters and spatial data are available under a CC-BY-NC license", linked to **CC BY-NC 2.5**; "They can be used for pretty much anything that is not commercial with just a citation for Mapping Inequality." (Older credits elsewhere read CC BY-NC-SA 4.0.) | The tinted ground, labels, every area and length by grade | **No.** Free, noncommercial story only, with credit. Prints or a book need the DSL's permission or polygons re-digitized from the public-domain scan. |
| HOLC area descriptions, transcribed | `data/holc/richmond-1937-descriptions.json`, **not committed**: the 48 Richmond records of https://raw.githubusercontent.com/americanpanorama/HOLC_Area_Description_Data/master/ad_data.json, SHA-256 of the extract `8b4934aa9d6f55c946e20a039c5651fa73d2f5593976375dd83500fd40f380a8` | Nov. 21, 2026 | No license on the repository. The text is a federal record (public domain); the transcription is the DSL's work. | Short attributed quotations, each to be checked against the scan before publication | Quote from the scan, cite the transcription. |
| HOLC map and area-description scans | National Archives, RG 195, City Survey Files, https://catalog.archives.gov/id/720357 ; FRASER | not fetched | **Public domain** (federal work; the DSL: "The scans of maps and area descriptions are in the public domain") | To be shown and quoted in a working draft | Yes |
| OpenStreetMap | `data/richmond-streetcars/osm.json` (shared cache) | Nov. 16, 2026 | ODbL 1.0, © OpenStreetMap contributors | Streets, highways (motorway lengths), buildings, water, parks | As in every isoscape map |
| USGS 3D Elevation Program, 5 m | `data/richmond-streetcars/dem.bin.gz` | Nov. 16, 2026 | Public domain | Terrain and hillshade | Yes |
| City of Richmond, Year_of_Construction parcels | `data/richmond-streetcars/yearbuilt.json` (53,049 parcels) | Nov. 16, 2026 | Published by the City on its public ArcGIS service; terms not found (open question in the brief). Already used in published isoscape work. | Which of today's buildings stood in 1937; counts by grade | As now. Year only; no owner fields are fetched. |
| Sanborn fire-insurance maps, Jackson Ward 1952, as traced | `history/sanborn/jackson-ward-1952.geojson`, `jackson-ward-lost.geojson` | in repo | Library of Congress scans, public domain; the trace is isoscape's | The survival check (how many 1952 outlines stand today) | Yes |

**Why the polygons are not committed.** The repo also builds work that is sold. Keeping
CC BY-NC data out of it means nothing NC can drift into a print by accident. Anyone can
fetch the same file from the URL above and check its SHA-256; `history.py`, `measure.py`
and the builds read it from `data/holc/`.

## Credit lines

- On the page and every image: "Grades: Home Owners' Loan Corporation, 1937 (National Archives,
  RG 195), as digitized by Mapping Inequality."
- In sources, the citation the DSL asks for: Nelson, Robert K., LaDale Winling, et al. "Mapping
  Inequality: Redlining in New Deal America." Edited by Robert K. Nelson. *American Panorama: An
  Atlas of United States History*, 2023. https://dsl.richmond.edu/panorama/redlining. For an
  online article the DSL says "Courtesy of Mapping Inequality" or "Source: Mapping Inequality"
  is fine, and "Mapping Inequality, public domain image" for the scans.
- Map data © OpenStreetMap contributors (ODbL); elevation USGS 3DEP; year built, City of Richmond.

## Not used

| Dataset | Why not |
|---|---|
| Science Museum of Virginia / Hoffman 2017 heat rasters (OSF `f9nhg`) | **No license stated.** Not used in anything published until the Science Museum allows it. |
| Meier & Mitchell, Historic Redlining Indicator (openICPSR) | No license stated ("distributed as received"); not needed. |
| City of Richmond parcels with assessed value and owner | Not fetched in this round. If used later: values in aggregate only, never owner names. |
| VCU life-expectancy map, *Planned Destruction*, NYT 2020 graphics | Copyrighted visual work: cited and linked, never reused. |
