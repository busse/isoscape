import json, sys, urllib.request, urllib.parse
layer, bbox, out = sys.argv[1], sys.argv[2], sys.argv[3]
where = sys.argv[4] if len(sys.argv) > 4 else '1=1'
fields = sys.argv[5] if len(sys.argv) > 5 else '*'
feats = []
off = 0
while True:
    q = urllib.parse.urlencode(dict(where=where, geometry=bbox, geometryType='esriGeometryEnvelope', inSR=4326, spatialRel='esriSpatialRelIntersects',
        outFields=fields, outSR=4326, returnGeometry='true', geometryPrecision=7, resultOffset=off, resultRecordCount=2000, f='geojson'))
    url = f'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/{layer}/FeatureServer/0/query?{q}'
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'isoscape/0.1'}), timeout=120))
    fs = d.get('features', [])
    feats += fs; off += len(fs)
    if len(fs) < 2000: break
json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w'))
print(layer, len(feats))
