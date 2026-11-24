# Find the shift (meters, raster CRS) that puts today's OSM street center lines on the brightest pavement of the orthophoto.
import sys, json, rasterio, numpy as np
from rasterio.warp import transform
from rasterio.windows import from_bounds
tif, osm, w, s, e, n = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
r = rasterio.open(tif)
xs, ys = transform('EPSG:4326', r.crs, [w, e, w, e], [s, s, n, n])
win = from_bounds(min(xs), min(ys), max(xs), max(ys), r.transform)
a = r.read(window=win).mean(0); wt = r.window_transform(win)
pts = []
for el in json.load(open(osm))['elements']:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('highway') not in ('primary', 'secondary', 'tertiary', 'residential') or not el.get('geometry'): continue
    lo = np.array([g['lon'] for g in el['geometry']]); la = np.array([g['lat'] for g in el['geometry']])
    for i in range(len(lo) - 1):
        for f in np.linspace(0, 1, 20):
            x, y = lo[i] + f * (lo[i+1] - lo[i]), la[i] + f * (la[i+1] - la[i])
            if w < x < e and s < y < n: pts.append((x, y))
X, Y = transform('EPSG:4326', r.crs, [p[0] for p in pts], [p[1] for p in pts])
X = np.array(X); Y = np.array(Y)
best = []
for dx in range(-60, 61, 2):
    for dy in range(-60, 61, 2):
        c, rr = ~wt * (X + dx, Y + dy)
        c = np.round(c).astype(int); rr = np.round(rr).astype(int)
        ok = (c >= 0) & (rr >= 0) & (c < a.shape[1]) & (rr < a.shape[0])
        best.append((a[rr[ok], c[ok]].mean(), dx, dy))
best.sort(reverse=True)
print('n points', len(pts), 'zero-shift', [b for b in best if b[1] == 0 and b[2] == 0][0][0])
print('top', best[:6])
