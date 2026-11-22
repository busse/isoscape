"""Draw today's streets over the scan through a fit, for looking at the georeferencing.

    python3 -I checkfit.py <scan.jpg> <osm.json> <georef.json> <out.png> x y w h [maxw]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import georef  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
KEEP = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk'}

if __name__ == '__main__':
    scan, osm, gj, out = sys.argv[1:5]
    x, y, w, h = map(int, sys.argv[5:9])
    maxw = int(sys.argv[9]) if len(sys.argv) > 9 else 1400
    G = json.load(open(gj))
    t = G['transform']
    im = Image.open(scan).convert('RGB').crop((x, y, x + w, y + h))
    s = min(1.0, maxw / w)
    im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    data = json.load(open(osm))
    c = georef.apply(t, [[x + w / 2, y + h / 2]])[0]
    R = max(w, h) * 1.7
    for e in data['elements']:
        tg = e.get('tags', {})
        if e['type'] != 'way' or tg.get('highway') not in KEEP:
            continue
        g = [p for p in (e.get('geometry') or []) if p]
        mx, my = georef.to_m([p['lon'] for p in g], [p['lat'] for p in g])
        if len(mx) < 2 or np.min(np.hypot(mx - c[0], my - c[1])) > R:
            continue
        uv = georef.inverse(t, np.c_[mx, my], guess=(x + w / 2, y + h / 2))
        d.line([((u - x) * s, (v - y) * s) for u, v in uv], fill=(255, 0, 180), width=2)
    for p in G.get('points', []):
        u, v = p[0], p[1]
        if x <= u < x + w and y <= v < y + h:
            q = georef.inverse(t, np.c_[georef.to_m([p[2]], [p[3]])])[0]
            d.ellipse([((u - x) * s - 6, (v - y) * s - 6), ((u - x) * s + 6, (v - y) * s + 6)], outline=(0, 120, 255), width=3)
            d.line([((u - x) * s, (v - y) * s), ((q[0] - x) * s, (q[1] - y) * s)], fill=(0, 120, 255), width=3)
    im.save(out)
