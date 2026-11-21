"""The island's edge: the count's polygons cut to where the 1952 sheets were traced.

    python3 island.py highway-footprint.geojson history/sanborn/jackson-ward-1952.geojson island.geojson

The corridor polygon runs east past the line of 8th Street into the I-95/I-64 ramp loop, where
no 1952 sheet was traced, so an island cut by it alone shows a bare loop of ground there, as if
nothing had stood on it. Each polygon is intersected with the traced sheets' coverage outline (the
edition file's `coverage` record), so the island ends where the tracing ends. The buildings are
the same: every counted building lies inside the coverage. Written as lon/lat GeoJSON, with the
names "paved-traced" and "corridor-traced"."""
import json, sys
from shapely.geometry import shape, mapping

fp, ed, out = sys.argv[1:4]
cov = [shape(f['geometry']) for f in json.load(open(ed))['features'] if f['properties'].get('coverage')]
assert len(cov) == 1, 'expected one coverage outline in the edition file'
feats = []
for f in json.load(open(fp))['features']:
    g = shape(f['geometry']).intersection(cov[0].buffer(0))
    feats.append({'type': 'Feature', 'properties': {'name': f['properties']['name'] + '-traced',
                  'note': f"The {f['properties']['name']} polygon of highway-footprint.geojson cut to the traced 1952 sheets' coverage (island.py)."},
                  'geometry': mapping(g)})
    print(f['properties']['name'], round(shape(f['geometry']).area * 1e10), '->', round(g.area * 1e10), '(deg2 x 1e10)')
json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w'))
