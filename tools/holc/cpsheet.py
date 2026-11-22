"""Contact sheets for reading control points: for each candidate corner (lon, lat, label), a crop
of the scan centered where the current fit puts it, with a 50 px grid labeled in scan pixels.

    python3 -I cpsheet.py <scan.jpg> <georef.json> <candidates.json> <out prefix> [half=300] [osm.json] [per=4]

With osm.json, today's OSM streets are drawn over each crop through the current fit: the two
streets of the corner in red and blue, the others in thin gray, to tell which printed line is
which street. The fit only places the overlay; the corner is read off the printed lines.
"""
import json
import sys

import os
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import georef

Image.MAX_IMAGE_PIXELS = None

if __name__ == '__main__':
    scan, gj, cj, pre = sys.argv[1:5]
    half = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    osm = sys.argv[6] if len(sys.argv) > 6 else None
    per = int(sys.argv[7]) if len(sys.argv) > 7 else 4
    ways = []
    if osm:
        import corners
        import numpy as np
        ways = corners.load(osm)
    t = json.load(open(gj))['transform']
    cand = json.load(open(cj))
    cand_names = {}
    if cand and len(cand[0]) > 3:
        cand_names = {c[2]: (c[3].split('|'), c[4].split('|')) for c in cand}
        cand = [c[:3] for c in cand]
    im = Image.open(scan).convert('RGB')
    tiles = []
    for lon, lat, lab in cand:
        x, y = georef.to_m([lon], [lat])
        u, v = georef.inverse(t, [[x[0], y[0]]])[0]
        u, v = int(round(u)), int(round(v))
        c = im.crop((u - half, v - half, u + half, v + half))
        if ways:
            dc = ImageDraw.Draw(c)
            a, b = [q.strip().lower() for q in lab.split('|')[0].split(' & ')] if ' & ' in lab else ('', '')
            names = cand_names.get(lab, ())
            for n, g in ways:
                xs, ys = g.xy
                if abs(np.mean(xs) - lon) > 0.02 or abs(np.mean(ys) - lat) > 0.02:
                    continue
                mx, my = georef.to_m(list(xs), list(ys))
                uv = georef.inverse(t, np.stack([mx, my], 1), guess=(u, v))
                pts = [(p[0] - (u - half), p[1] - (v - half)) for p in uv]
                col, w = (150, 150, 150), 1
                if names and n in names[0]:
                    col, w = (255, 0, 0), 2
                elif names and n in names[1]:
                    col, w = (0, 0, 255), 2
                dc.line(pts, fill=col, width=w)
        pad = 34
        T = Image.new('RGB', (c.width + pad, c.height + pad + 18), 'white')
        T.paste(c, (pad, pad + 18))
        d = ImageDraw.Draw(T)
        d.text((2, 2), f'{lab}  pred ({u},{v})', fill='red')
        for g in range((u - half) // 50 * 50 + 50, u + half, 50):
            px = pad + g - (u - half)
            d.line([(px, pad + 18), (px, T.height)], fill=(0, 150, 255) if g % 100 else (255, 0, 0), width=1)
            if g % 100 == 0:
                d.text((px - 12, 20), str(g), fill='black')
        for g in range((v - half) // 50 * 50 + 50, v + half, 50):
            py = pad + 18 + g - (v - half)
            d.line([(pad, py), (T.width, py)], fill=(0, 150, 255) if g % 100 else (255, 0, 0), width=1)
            if g % 100 == 0:
                d.text((0, py - 5), str(g), fill='black')
        tiles.append(T)
    for k in range(0, len(tiles), per):
        g = tiles[k:k + per]
        S = Image.new('RGB', (sum(t.width for t in g), g[0].height), 'white')
        x = 0
        for t in g:
            S.paste(t, (x, 0))
            x += t.width
        S.save(f'{pre}{k // per}.png')
    print(len(tiles), 'tiles')
