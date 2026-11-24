# Provisional: for each traced building dropped before 1969 (end 'assumed') with ground under the Agnes level,
# the share of its footprint (shrunk 2 m) that is dark on the 1974 orthophoto (tar roofs and shadow read dark;
# pavement, gravel lots and light roofs read light). A screening number only, not a verdict.
import sys, json, rasterio, numpy as np
from rasterio.warp import transform
from rasterio.features import rasterize
from shapely.geometry import Polygon
tif, ids_path, lost_path = sys.argv[1:4]
dx, dy = 2, -14
r = rasterio.open(tif); band = r.read().mean(0)
ids = {x['id'] for x in json.load(open(ids_path))}
out = []
for f in json.load(open(lost_path))['features']:
    p = f['properties']
    if p['id'] not in ids: continue
    ring = f['geometry']['coordinates'][0]
    X, Y = transform('EPSG:4326', r.crs, [c[0] for c in ring], [c[1] for c in ring])
    poly = Polygon([(x + dx, y + dy) for x, y in zip(X, Y)]).buffer(-2)
    if poly.is_empty or poly.area < 8: out.append((p['id'], None)); continue
    m = rasterize([poly], out_shape=band.shape, transform=r.transform).astype(bool)
    v = band[m]
    out.append((p['id'], float((v < 110).mean()), float(np.median(v)), round(poly.area)))
vals = [o for o in out if o[1] is not None]
print('n', len(out), 'measurable', len(vals))
for t in (0.5, 0.7):
    print(f'share with >= {t:.0%} of footprint dark:', sum(1 for o in vals if o[1] >= t), 'of', len(vals))
print('mostly light (<20% dark):', sum(1 for o in vals if o[1] < 0.2))
json.dump(out, open(sys.argv[4], 'w'))
