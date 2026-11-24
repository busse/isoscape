# Overlay traced Sanborn footprints (lost.geojson) on the 1974 orthophoto GeoTIFF for a lon/lat box.
# red = standing in 1952 but dropped before 1969 (end 'assumed'); yellow = dropped by 'highway'; cyan = still drawn in 1972.
import sys, json, rasterio
from rasterio.warp import transform
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
import numpy as np
tif, lost, out, w, s, e, n, k = sys.argv[1], sys.argv[2], sys.argv[3], *map(float, sys.argv[4:8]), int(sys.argv[8])
dx, dy = (float(sys.argv[9]), float(sys.argv[10])) if len(sys.argv) > 10 else (0, 0)  # shift fitted by fitshift.py
r = rasterio.open(tif)
xs, ys = transform('EPSG:4326', r.crs, [w, e, w, e], [s, s, n, n])
win = from_bounds(min(xs), min(ys), max(xs), max(ys), r.transform)
a = r.read(window=win)
img = Image.fromarray(np.moveaxis(a, 0, -1)).convert('RGB')
img = img.resize((img.width * k, img.height * k), Image.LANCZOS)
wt = r.window_transform(win)
d = ImageDraw.Draw(img)
for f in json.load(open(lost))['features']:
    p = f['properties']
    if not (p['from'] <= 1952 < p['to']): continue
    ring = f['geometry']['coordinates'][0]
    lo = [c[0] for c in ring]; la = [c[1] for c in ring]
    if max(lo) < w or min(lo) > e or max(la) < s or min(la) > n: continue
    X, Y = transform('EPSG:4326', r.crs, lo, la)
    px = [(~wt * (x + dx, y + dy)) for x, y in zip(X, Y)]
    px = [(c * k, rr * k) for c, rr in px]
    col = (255, 40, 40) if p['to'] <= 1969 and p['end'] == 'assumed' else (255, 210, 0) if p['to'] <= 1972 else (0, 220, 255)
    d.line(px + [px[0]], fill=col, width=2)
img.save(out, optimize=True); print(out, img.size)
