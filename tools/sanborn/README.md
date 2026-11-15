# Tracing Sanborn fire-insurance maps

Python 3 with NumPy, SciPy, OpenCV (`opencv-python-headless`), Pillow and Shapely. Run from
this folder. Scans are cached outside the repo (`~/work/sanborn`); the outputs go to
`../../history/sanborn/`.

1. `python3 fetch_sheets.py <item> 25 [sheet suffixes…]`: download an edition's sheets at 25%
   from the Library of Congress (`item` is the `sanborn09064_NNN` number, run in a folder
   holding `item_NNN.json` from `https://www.loc.gov/item/sanborn09064_NNN/?fo=json`).
2. `python3 arcgis.py CityBlock <bbox> ../../data/sanborn/blocks.json`: the city's block
   outlines, for checking fits.
3. Read two or three named street corners off each sheet (`mosaic.py` makes labeled contact
   sheets) into `cps<edition>.json` as `[u, v, lon, lat, label]`; corners come from OSM
   intersections.
4. `python3 rigid.py cps<edition>.json <meters per pixel> georef.json`: fit each sheet; a
   third corner flags misreads. `ovmosaic.py` draws the city's blocks over sheets to check.
5. `python3 extract.py <edition> georef.json "<scan path with {sh:04d}>" ../../history/sanborn/<edition>.geojson <skip,sheets> keep<edition>.json`
6. `node dates.ts` (from the repo root: `node tools/sanborn/dates.ts`), then
   `python3 lifespans.py ../../history/sanborn/lost.geojson ../../data/sanborn/buildings.json ../../data/sanborn/motorways.json ../../history/sanborn/<edition>.geojson…`
   with the editions in order.

The 1886 edition used a scale of 0.2014 m per pixel at 25%. Sheets 14, 25–27, 29 and 31 were
left out: outside the frame, or (14) not yet fitted.
