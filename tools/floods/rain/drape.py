#!/usr/bin/env python3
"""Write the GeoJSON that isoscape drapes on the ground for the Gaston rain view (treatment i).

    python3 tools/floods/rain/drape.py

data/bands-1in.geojson (the storm-total bands, one inch apart from 7 to 12: the view's ground all lies in 7 to 13 inches) plus the Shockoe Creek watershed as a thin ring
(value "outline", drawn in the palette's mark line by src/tint-tones.ts), smoothed for display:
the outline is buffered out and back by 40 m and simplified to 10 m, which takes out the
grid's stair steps without moving the line more than a few tens of meters.
Read by history/gaston-2004.json (switch "rain"); build with
    node bin/isoscape.js build richmond-gaston-rain --with rain --year 2004 --png --width 3400
"""
import json
import math
import os

from shapely.geometry import shape, mapping

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
M = 1 / (111320 * math.cos(math.radians(37.55)))  # degrees of longitude per meter, about

b = json.load(open(os.path.join(D, "bands-1in.geojson")))
ws = shape(json.load(open(os.path.join(D, "watershed.geojson")))["features"][0]["geometry"])
smooth = ws.buffer(40 * M).buffer(-80 * M).buffer(40 * M).simplify(10 * M)
ring = smooth.buffer(18 * M).difference(smooth.buffer(-18 * M))
b["features"].append({"type": "Feature", "properties": {"label": "outline", "note": "Shockoe Creek surface watershed, a 36 m ring, smoothed for display (watershed.py, drape.py)"},
                      "geometry": mapping(ring)})
b["name"] = "gaston-2004-iso-drape"
json.dump(b, open(os.path.join(D, "iso-drape.geojson"), "w"))
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "Shockoe Creek surface watershed, smoothed for display"}, "geometry": mapping(smooth)}]},
          open(os.path.join(D, "watershed-display.geojson"), "w"))
print("features", len(b["features"]), "area change", round((smooth.area - ws.area) / ws.area * 100, 2), "%")
