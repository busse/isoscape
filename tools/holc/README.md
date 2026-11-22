# Redrawing the 1937 HOLC map of Richmond from the public-domain scan

Code for redrawing the 48 graded areas of the Home Owners' Loan Corporation's "Residential
Security Map" of Richmond (April 3, 1937). The input is the National Archives scan as FRASER
serves it, and today's street grid from OpenStreetMap. Everything is done in code: color
segmentation, machine-read control points, a least-squares fit. Nothing is traced by hand. The
work was done with Claude for Chris Busse, November 2026. Mapping Inequality's polygons and
control points were not used as input. They are read only by `compare.py` and `pictures.py`,
to compare the result with them.

## Inputs (not in git)

| What | Where it came from | SHA-256 |
|---|---|---|
| Map scan, 9832 x 7841 px at 400 ppi, one JPEG inside a PDF (16,810,085 bytes) | https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/rg195_holc_Richmond_VA.pdf (FRASER item "Redline Map for Richmond, Virginia", NARA RG 195), fetched Nov. 22, 2026 | `ecaab52838423e1fcb0ae3346fe7d565d030820ecb15c2fbf6a4be3458f0281e` |
| Second copy of the map, 7232 x 5532 px at 300 ppi (7,205,593 bytes), not used | https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/map_RichmondVA.pdf | `d5a18f249dd5eee35dc70ea19f89952cf9692c6d1effda29b5e0cc4e28bafa29` |
| Area descriptions, 48 pages at 1220 x 2038 px (20,733,404 bytes) | https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf | `e56e4432896d46c62887de6b24a18c68d62e187d1d926a2e7850a194979600ab` |
| OpenStreetMap | `data/richmond-streetcars/osm.json` (shared cache, fetched Nov. 16, 2026) | |

Get the scan's JPEG out with `pdfimages -j rg195_holc_Richmond_VA.pdf rg195` (this gives
`rg195-000.jpg`). Keep downloads in their own folder, and run the scripts with `python3 -I`.

## Scripts, in order

1. `circles.py <scan> circles.json <sheet.png>` finds the printed label circles (Hough transform)
   and draws a numbered contact sheet. The labels printed in them, and the arrow tips of the
   labels set outside their areas, were read off the scan into `labels.json`.
2. `segment.py <scan> seg.npz [preview.png]` classes each pixel as ink, paper, or one of the
   four grade tints. The tints are sampled from the map's own legend swatches, and the nearest
   color is chosen in Lab. Heavy lines (the area boundaries) are what survives an opening of
   17 px. Each grade's tint is cleaned, cut along the heavy lines, and split into pieces.
3. `assign.py seg.npz labels.json areas_px.json [scan preview.png]` names each piece from
   `labels.json`, by its own label or arrow tip, then by contact, then by nearness. It splits a
   piece that holds two labels along the darkest line between them (a watershed). It joins each
   area's pieces, fills holes, and grows neighbors together 14 px, to the middle of the shared
   printed line. Every piece that is not named by its own label is listed for review.
4. `corners.py <osm.json> "street A" "street B" ...` gives OSM intersections. The 42 candidates
   are in `corners.json`.
5. `globalfit.py <scan> <osm.json> <rough georef> <out>` does a coarse fit of the whole street
   grid to the printed ink. It is used only to start step 6.
6. `snapcp.py <scan> <osm.json> <georef> corners.json cps.json 30` reads each corner's place on
   the scan by sliding today's streets around it onto the printed lines. A corner is kept only
   if most of its streets land on ink and the best shift beats every other shift clearly. 33 of
   the 42 were kept.
7. `georef.py cps.json georef.json` fits similarity, affine, and second-order transforms and
   reports the RMS, the largest residual and the leave-one-out error in meters. The affine fit
   is used. `checkfit.py` draws OSM over the scan through a fit, for checking it by eye.
8. `togeo.py areas_px.json georef.json <out.geojson> <scan sha256> labels.json` writes the
   GeoJSON in WGS84. The committed copy is `history/holc/richmond-1937-redrawn.geojson`.
9. `compare.py <redrawn> <other> per-area.csv summary.json` and `pictures.py ...` compare the
   redraw with another set and draw the comparison.

Python 3 with NumPy, SciPy, OpenCV, Pillow and Shapely, as in `tools/sanborn/`. A full run
takes about two minutes.

## Provenance and credit

The redrawn outlines derive only from the public-domain scan (a U.S. federal record, NARA
RG 195, City Survey Files) and from OpenStreetMap street positions, which were used for the
georeferencing. Credit: "Map data (c) OpenStreetMap contributors, ODbL 1.0." The GeoJSON's
`metadata` says the same.
