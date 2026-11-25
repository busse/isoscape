"""Draw a trace (and optionally today's street corners) over its scan, to check the trace by eye."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '..')
from geo import to_m, w2i
geo, scan, trace, sheet, out = sys.argv[1:6]
p = json.load(open(geo))[sheet]['params']
im = Image.open(scan).convert('RGB'); d = ImageDraw.Draw(im, 'RGBA')
C = {'brick': (200, 0, 0), 'frame': (0, 120, 0), 'stone': (0, 0, 200), 'iron': (60, 60, 60), 'special': (120, 0, 160), 'fireproof': (150, 90, 0)}
for f in json.load(open(trace))['features']:
    pr = f['properties']
    if pr.get('coverage') or str(pr.get('sheet')) != sheet: continue
    r = np.asarray(f['geometry']['coordinates'][0]); x, y = to_m(r[:, 0], r[:, 1])
    uv = w2i(p, np.stack([x, y], 1))
    d.polygon([tuple(q) for q in uv], outline=C[pr['material']] + (255,), width=3)
if len(sys.argv) > 6:
    for lab, (lon, lat) in json.load(open(sys.argv[6])).items():
        x, y = to_m([lon], [lat]); u, v = w2i(p, np.stack([x, y], 1))[0]
        d.ellipse([u - 14, v - 14, u + 14, v + 14], outline=(0, 90, 255, 255), width=4)
im.save(out, quality=85)
