# Redlining story: datasets, licenses and credits

Every dataset the story's pictures and numbers use, where it came from, when, and on what terms.
Drafted with Claude for Chris Busse, November 21, 2026. Nothing here is for sale, and nothing
built from the Mapping Inequality polygons may be sold (see below).

## Used

The owner chose, on November 22, 2026, to build the story from the outlines redrawn from the
public-domain scan (`outlines.py`: `USE = 'nara-redraw'`). The lab's polygons are kept, outside
git, only to compare with.

| Dataset | Where it is | Fetched | License / terms | Used for | Sold work? |
|---|---|---|---|---|---|
| HOLC 1937 Richmond map, redrawn | `history/holc/richmond-1937-redrawn.geojson` (committed), made by `tools/holc/` from FRASER's copy of the National Archives scan, `rg195_holc_Richmond_VA.pdf` (SHA-256 `ecaab528…0281e`), georeferenced to 33 OpenStreetMap street corners | Nov. 22, 2026 | Scan: public domain (federal record). Control points from OpenStreetMap (ODbL). | The tinted ground, labels, every area and length by grade | Yes, as far as the data goes (credit OSM for the corners) |
| Unnumbered pieces | `tools/stories/redlining/unnumbered.json`, applied by `outlines.load()` | Nov. 22, 2026 | The story's own record | Four tinted pieces the map prints no number on (a B block at Rodney, Wythe and Bethlehem Roads; D blocks on Canal and Byrd Streets and by Monroe Park; a thin D strip along C10) are split off their nearest areas: they keep their grade and count in the totals by grade, and in no area's own figures (the owner's decision, Nov. 22, 2026). The redraw's GeoJSON is not edited. A fifth, a C patch under 1 ha joined to C10's outline, cannot be split without editing geometry and stays in C10; no per-area number for C8 or C10 is used. | — |
| HOLC area descriptions, scan | FRASER `ad_RichmondVA.pdf`, https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf | Nov. 22, 2026 (read by the planning session) | Public domain | The D11.5 quotation (p. 47, field 6d), checked on the scan | Yes |
| HOLC area descriptions, scan, rechecked for the fact check | as above; local copy SHA-256 `e56e4432…600ab` (matches compare.md) | Nov. 22, 2026 (d4) | Public domain | D4 field 14 reads "Same as Oak Park, D2." (p. 40; the Lab's transcription has "D3"); D10 6c "25 years and older" (p. 46); D3, D8, D9 remarks and D6, D11 inhabitants fields reread for capitals and punctuation | Yes |
| HOLC map scan, title block, rechecked | `rg195_holc_Richmond_VA.pdf`, SHA-256 `ecaab528…0281e` | Nov. 22, 2026 (d4) | Public domain | The HOLC's title "Residential Security Map"; the base map's title "City of Richmond, Virginia and Environs", Department of Public Works, 1923, revised to Aug. 1, 1936 | Yes |
| VCU Libraries, "Interstate Highways" | https://gallery.library.vcu.edu/exhibits/show/mcv-aerial-photography/interstate-highways | opened Nov. 22, 2026 (d4) | Cited, not reused | The Turnpike's opening (July 1, 1958), the Authority (1955), who selected the path | — |
| Mapping Inequality, Richmond 1937 polygons (48 graded areas and one ungraded "Industrial and Commercial" area) | `data/holc/richmond-1937.geojson`, **not committed** (see below). From https://dsl.richmond.edu/panorama/redlining/static/citiesData/VARichmond1937/geojson.json, SHA-256 `8fe7b5cf91cdd7591eeec07c2b053404ad7bc746d62c1b7f061959ce6a49014e`, 57,196 bytes, Last-Modified Aug. 19, 2024 | Nov. 21, 2026 | The DSL's data page: "The georectified rasters and spatial data are available under a CC-BY-NC license", linked to **CC BY-NC 2.5**; "They can be used for pretty much anything that is not commercial with just a citation for Mapping Inequality." (Older credits elsewhere read CC BY-NC-SA 4.0.) | Comparison with the redrawn set only (no longer drawn) | **No.** Free, noncommercial story only, with credit. Prints or a book need the DSL's permission or polygons re-digitized from the public-domain scan. |
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

- On every image (from `outlines.py`): "Grades: Home Owners' Loan Corporation, 1937 (National
  Archives, RG 195, via FRASER); outlines redrawn with Claude from the public-domain scan,
  positioned with OpenStreetMap street corners (ODbL)."
- In the text, Mapping Inequality is credited as the project that digitized and published these
  maps, whose digitization checked the redraw and whose transcriptions were consulted.
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
