"""Cut the streets, rail and buildings around Jackson Ward out of the streetcars region's OSM
cache (data/richmond-streetcars/osm.json, about 100 MB) into osm-jw.json, for corner.py,
footprint.py and the overlays. Not committed: it is OSM data (ODbL), rebuilt from the cache.

    python3 osmcut.py ../../../data/richmond-streetcars/osm.json osm-jw.json"""
import json, sys
d = json.load(open(sys.argv[1]))
out = []
for e in d['elements']:
    if e['type'] != 'way' or 'geometry' not in e: continue
    t = e.get('tags', {})
    if not (t.get('highway') or t.get('railway') or t.get('building')): continue
    g = [(p['lon'], p['lat']) for p in e['geometry'] if p]
    if not g or not any(-77.462 < x < -77.418 and 37.538 < y < 37.566 for x, y in g): continue
    keep = ('highway', 'name', 'railway', 'building', 'lanes', 'bridge', 'layer', 'oneway', 'ref', 'tunnel', 'service', 'amenity', 'start_date', 'old_name')
    out.append({'id': e['id'], 'tags': {k: t[k] for k in t if k in keep}, 'g': g})
json.dump(out, open(sys.argv[2], 'w'))
print(len(out))
