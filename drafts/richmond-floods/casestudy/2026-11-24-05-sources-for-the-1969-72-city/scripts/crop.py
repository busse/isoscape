# Crop a georeferenced raster to a lon/lat box (NAD27 lon/lat, close enough to WGS84 at this scale: ~10-20 m shift noted)
import sys, rasterio
from rasterio.warp import transform
from rasterio.windows import from_bounds
from PIL import Image
import numpy as np
src, out, w, s, e, n = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
r = rasterio.open(src)
xs, ys = transform('EPSG:4326', r.crs, [w, e, w, e], [s, s, n, n])
win = from_bounds(min(xs), min(ys), max(xs), max(ys), r.transform)
a = r.read(window=win)
img = Image.fromarray(np.moveaxis(a, 0, -1)) if a.shape[0] == 3 else Image.fromarray(a[0])
if scale != 1.0:
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
img.save(out, optimize=True)
print(out, img.size, 'res m/px', r.res[0] / scale)
