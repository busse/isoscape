"""Block panels for the look at one evidence image: the image enlarged around a 200 m square,
with every inventory footprint whose center falls in it drawn and numbered (the numbers of the
contact sheets), outlined by the current call (green present, red gone, yellow unclear; traced
footprints solid, today's undated buildings dotted). On the 1974 halftone a building reads by
its block's pattern more than on its own, so its calls are looked at here.

    python3 tools/floods/period/panels.py <area> <image> <score.json> <index.json> <outdir> [looked.json]
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import Crop, streets

SIDE, MARGIN, PXM = 300.0, 25.0, 2.6  # meters, meters, output pixels per meter
COL = {'present': (40, 200, 60), 'gone': (235, 40, 40), 'unclear': (255, 200, 0)}


def main(area, key, score_path, index_path, outdir, looked_path=None):
    sc = json.load(open(score_path))
    idx = {r['id']: r for r in json.load(open(index_path))}
    looked = json.load(open(looked_path)) if looked_path and os.path.exists(looked_path) else {}
    crop = Crop(area, key)
    pxm = 1.0 / (crop.px * crop.ground)
    os.makedirs(outdir, exist_ok=True)
    cells = {}
    for b in sc['buildings']:
        lo = [p[0] for p in b['ring']]; la = [p[1] for p in b['ring']]
        c, r = crop.pixel(lo, la)
        cx, cy = np.mean(c) / pxm, np.mean(r) / pxm  # meters from the crop's corner
        cells.setdefault((int(cx // SIDE), int(cy // SIDE)), []).append((b, c, r))
    font = ImageFont.load_default()
    rgb = crop.img.convert('RGB')
    allx = [p[0] for b in sc['buildings'] for p in b['ring']]; ally = [p[1] for b in sc['buildings'] for p in b['ring']]
    street_lines = streets((min(allx) - 0.003, min(ally) - 0.003, max(allx) + 0.003, max(ally) + 0.003))
    made = []
    for (i, j), items in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        x0 = (i * SIDE - MARGIN) * pxm; y0 = (j * SIDE - MARGIN) * pxm
        x1 = ((i + 1) * SIDE + MARGIN) * pxm; y1 = ((j + 1) * SIDE + MARGIN) * pxm
        k = PXM / pxm
        img = rgb.crop((int(x0), int(y0), int(x1), int(y1)))
        img = img.resize((round(img.width * k), round(img.height * k)), Image.BICUBIC)
        d = ImageDraw.Draw(img)
        # Today's street center lines, thin, for the registration's sake.
        for _, slo, sla in street_lines:
            sc_, sr_ = crop.pixel(slo, sla)
            d.line([((x - int(x0)) * k, (y - int(y0)) * k) for x, y in zip(sc_, sr_)], fill=(90, 200, 255), width=1)
        for b, c, r in items:
            call = looked.get(b['id'], {}).get(key, idx[b['id']]['proposed'][key])
            pts = [((x - int(x0)) * k, (y - int(y0)) * k) for x, y in zip(c, r)]
            col = COL[call]
            if b['kind'] == 'traced':
                d.line(pts + [pts[0]], fill=col, width=2)
            else:
                for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                    n = max(1, int(np.hypot(bx - ax, by - ay) / 6))
                    for t in range(0, n, 2):
                        d.line([(ax + (bx - ax) * t / n, ay + (by - ay) * t / n), (ax + (bx - ax) * (t + 1) / n, ay + (by - ay) * (t + 1) / n)], fill=col, width=2)
            mx, my = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
            label = str(idx[b['id']]['n'])
            d.rectangle([mx - 2, my - 6, mx + 6 * len(label) + 1, my + 6], fill=(0, 0, 0))
            d.text((mx, my - 6), label, fill=col, font=font)
        d.text((4, 4), f'{area} {key} panel {i},{j}', fill=(255, 255, 0), font=font)
        path = os.path.join(outdir, f'{area}-{key}-panel-{j:02d}-{i:02d}.jpg')
        img.save(path, quality=80)
        made.append(path)
    print(len(made), 'panels')


if __name__ == '__main__':
    main(*sys.argv[1:])
