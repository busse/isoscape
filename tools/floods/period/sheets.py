"""Contact sheets for the look-over: one row cell per building, its footprint (today's outline,
or the traced Sanborn outline) over each evidence image from 1974 to 2021, outlined in the color
of the current call (green present, red gone, yellow unclear). Also proposes the automatic
calls as one change date per building, which the look then confirms or corrects (looked.json).

    python3 tools/floods/period/sheets.py <area> <score.json> <sanborn.json> <outdir> [looked.json]

The machine's proposal (`propose`):
* today's undated building: present in 2021 (it is on today's map); going back, present in
  each earlier photo while its patch still looks like the next photo's (correlation >= LIKE);
  1974 by its own measure (score.py). The first photo that does not hold is unclear.
* traced building gone today: 1974 by its own measure; later photos gone while they look like
  the next one and the next is gone; else unclear.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon
from common import Crop

IMAGES = ['1974', '1999', '2002', '2017', '2021']
LIKE = 0.35
TILE, PER_ROW, ROWS = 92, 3, 16
COL = {'present': (40, 200, 60), 'gone': (235, 40, 40), 'unclear': (255, 200, 0)}


def propose(b, call74=None):
    """call74: the 1974 call after the look, where there is one."""
    calls = {}
    im = b['images']
    if b['kind'] == 'today':
        calls['2021'] = 'present'
        state = 'present'
        for k in ['2017', '2002', '1999']:
            s = im[k].get('same_as_next')
            if state == 'present' and s is not None and s >= LIKE:
                calls[k] = 'present'
            else:
                calls[k] = 'unclear'
                state = 'unclear'
        calls['1974'] = im['1974']['auto'] if call74 is None else call74
    else:
        calls['1974'] = im['1974']['auto'] if call74 is None else call74
        state = 'gone'
        calls['2021'] = 'gone'
        for k in ['2017', '2002', '1999']:
            s = im[k].get('same_as_next')
            if state == 'gone' and s is not None and s >= LIKE:
                calls[k] = 'gone'
            else:
                calls[k] = 'unclear'
                state = 'unclear'
        if calls['1974'] == 'gone':  # gone in 1974 stays gone
            for k in ['1999', '2002', '2017']:
                calls[k] = 'gone'
    return calls


def tile(crop, ring, color):
    lo = [p[0] for p in ring]; la = [p[1] for p in ring]
    c, r = crop.pixel(lo, la)
    pxm = 1.0 / (crop.px * crop.ground)
    cx, cy = (min(c) + max(c)) / 2, (min(r) + max(r)) / 2
    half = max(max(c) - min(c), max(r) - min(r)) / 2 + 12 * pxm
    box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
    img = crop.img.convert('RGB').crop(box).resize((TILE, TILE), Image.BILINEAR)
    k = TILE / (box[2] - box[0])
    d = ImageDraw.Draw(img)
    pts = [((x - box[0]) * k, (y - box[1]) * k) for x, y in zip(c, r)]
    d.line(pts + [pts[0]], fill=color, width=1)
    return img


def main(area, score_path, sanborn_path, outdir, looked_path=None, mode='all'):
    """mode `all`: every building, 1974 to 2021. mode `modern`: the round for the later photos,
    1999 to 2021 only, larger, and only the buildings whose later calls matter: every undated
    building of today, and traced buildings not already called gone in 1974."""
    sc = json.load(open(score_path))
    sb = json.load(open(sanborn_path)) if os.path.exists(sanborn_path) else {}
    looked = json.load(open(looked_path)) if looked_path and os.path.exists(looked_path) else {}
    crops = {k: Crop(area, k) for k in IMAGES}
    os.makedirs(outdir, exist_ok=True)
    blds = sc['buildings']
    global TILE, PER_ROW
    cols = IMAGES
    numbers = {b['id']: n + 1 for n, b in enumerate(blds)}
    if mode == 'modern':
        cols = IMAGES[1:]
        TILE, PER_ROW = 104, 4
        def call74(b):
            return looked.get(b['id'], {}).get('1974', propose(b)['1974'])
        blds = [b for b in blds if b['kind'] == 'today' or call74(b) != 'gone']
    # Sheets go traced first (by id), then today's (by id); numbering is per area.
    per = PER_ROW * ROWS
    font = ImageFont.load_default()
    index = []
    for s0 in range(0, len(blds), per):
        chunk = blds[s0:s0 + per]
        cw = len(cols) * (TILE + 2) + 8
        W = PER_ROW * cw + 10
        H = ROWS * (TILE + 14) + 30
        sheet = Image.new('RGB', (W, H), (250, 248, 240))
        d = ImageDraw.Draw(sheet)
        d.text((6, 6), f'{area} {mode} sheet {s0 // per + 1}. Columns {", ".join(cols)}. Outline: green present, red gone, yellow unclear.', fill=(0, 0, 0), font=font)
        for n, b in enumerate(chunk):
            c74 = looked.get(b['id'], {}).get('1974')
            calls = dict(propose(b, c74))
            calls.update({k: v for k, v in looked.get(b['id'], {}).items() if k in IMAGES})
            x0 = (n % PER_ROW) * cw + 6
            y0 = (n // PER_ROW) * (TILE + 14) + 24
            sbn = sb.get(b['id'])
            tag = '' if b['kind'] == 'traced' else ' S' + ('+' if sbn and sbn[-1]['call'] == 'present' else '-' if sbn else '?')
            d.text((x0, y0), f"{numbers[b['id']]} {b['kind'][0]} {b['id'].replace('sanborn-', '')}{tag}", fill=(0, 0, 0), font=font)
            for i, k in enumerate(cols):
                sheet.paste(tile(crops[k], b['ring'], COL[calls[k]]), (x0 + i * (TILE + 2), y0 + 11))
            index.append(dict(n=numbers[b['id']], id=b['id'], kind=b['kind'], sheet=s0 // per + 1, proposed=propose(b, looked.get(b['id'], {}).get('1974'))))
        sheet.save(os.path.join(outdir, f'{area}-{mode}-sheet-{s0 // per + 1:02d}.png'), optimize=True)
    json.dump(index, open(os.path.join(outdir, f'{area}-{mode}-index.json'), 'w'))
    print(len(blds), 'buildings,', (len(blds) + per - 1) // per, 'sheets')


if __name__ == '__main__':
    main(*sys.argv[1:])
