# Draw today's OSM street center lines (from the isoscape cache) over an orthophoto crop, with an optional shift in meters (dx east, dy north).
import sys, json, rasterio
from rasterio.warp import transform
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
import numpy as np
tif, osm, out, w, s, e, n, k = sys.argv[1], sys.argv[2], sys.argv[3], *map(float, sys.argv[4:8]), int(sys.argv[8])
dx, dy = (float(sys.argv[9]), float(sys.argv[10])) if len(sys.argv) > 10 else (0, 0)
r = rasterio.open(tif)
xs, ys = transform('EPSG:4326', r.crs, [w, e, w, e], [s, s, n, n])
win = from_bounds(min(xs), min(ys), max(xs), max(ys), r.transform)
img = Image.fromarray(np.moveaxis(r.read(window=win), 0, -1)).convert('RGB')
img = img.resize((img.width * k, img.height * k), Image.LANCZOS)
wt = r.window_transform(win); d = ImageDraw.Draw(img)
for el in json.load(open(osm))['elements']:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('highway') not in ('primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk') or not el.get('geometry'): continue
    lo = [g['lon'] for g in el['geometry']]; la = [g['lat'] for g in el['geometry']]
    if max(lo) < w or min(lo) > e or max(la) < s or min(la) > n: continue
    X, Y = transform('EPSG:4326', r.crs, lo, la)
    px = [~wt * (x + dx, y + dy) for x, y in zip(X, Y)]
    d.line([(c * k, rr * k) for c, rr in px], fill=(255, 0, 255), width=2)
img.save(out, optimize=True); print(out)
