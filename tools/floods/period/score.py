"""Score every building of an area's inventory on its evidence images, and make an automatic
presence call (present / gone / unclear) for each. The calls are corrected by looking at the
contact sheets (sheets.py, looked.json); this file is only the machine's first pass.

    python3 tools/floods/period/score.py <area> <inventory.json> <out.json>

Two measures:

* **Alone** (every image; the only one for 1974): inside the footprint, shrunk SHRINK m (2 m
  on the 1974 halftone, 1 m on later photos), against a ring 3 to 9 m outside it. On the 1974
  print a roof reads as a dark mass (tar roofs, and the building's own shadow) and an open lot
  or pavement reads light: `dark` is the share of the inside darker than DARK (on a 0-255 scale,
  the photo's own median as the midpoint), `contrast` is the ring's mean less the inside's.
* **Same as the next image** (1999 to 2017, each against the image after it, 2021 against
  today's map): the normalized correlation of the footprint's patch (with 3 m around it)
  between the two photos, best over shifts of up to 3 m. A building that is there in both, or
  a lot open in both, looks the same; a change shows as a low correlation. Today's state is
  known from the map: an undated building of today stands; a traced building gone today does
  not (no building today covers half of it).

Automatic calls, by image:
* 1974: present when dark >= 0.55 and contrast >= 8; gone when dark <= 0.25 and contrast <= 0;
  else unclear. Unmeasurable (under 25 m² after shrinking) is unclear.
* later photos: the next image's state carried back when correlation >= SAME; unclear
  (a possible change, to be looked at) when below.
"""
import json, sys
import numpy as np
from shapely.geometry import Polygon
from PIL import Image, ImageDraw
from common import Crop

IMAGES = ['1974', '1999', '2002', '2017', '2021']
SHRINK = {'1974': 2.0}
DARK = 0.80  # share of the image's median gray below which a pixel counts as dark (1974)
SAME = 0.55
MIN_AREA = 25.0


def poly_px(crop, ring, reg=None):
    lo = [p[0] for p in ring]; la = [p[1] for p in ring]
    c, r = crop.pixel(lo, la, reg=reg)
    return Polygon(list(zip(c, r))).buffer(0)


def mask(shape, poly):
    H, W = shape
    x0, y0, x1, y1 = [int(v) for v in poly.bounds]
    x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
    x1, y1 = min(W, x1 + 2), min(H, y1 + 2)
    if x1 <= x0 or y1 <= y0:
        return None, None
    im = Image.new('L', (x1 - x0, y1 - y0), 0)
    geoms = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    d = ImageDraw.Draw(im)
    for g in geoms:
        if g.is_empty:
            continue
        d.polygon([(x - x0, y - y0) for x, y in g.exterior.coords], fill=1)
        for h in g.interiors:
            d.polygon([(x - x0, y - y0) for x, y in h.coords], fill=0)
    return np.asarray(im, bool), (x0, y0, x1, y1)


def region_vals(img, poly):
    if poly.is_empty:
        return np.array([])
    m, box = mask(img.shape[:2], poly)
    if m is None:
        return np.array([])
    x0, y0, x1, y1 = box
    return img[y0:y1, x0:x1][m]


def alone(crop, ring, key):
    pxm = 1.0 / (crop.px * crop.ground)
    p = poly_px(crop, ring)
    inner = p.buffer(-SHRINK.get(key, 1.0) * pxm)
    outer = p.buffer(9 * pxm).difference(p.buffer(3 * pxm))
    area = inner.area / pxm ** 2
    vin = region_vals(crop.gray, inner)
    vout = region_vals(crop.gray, outer)
    if len(vin) == 0 or area < MIN_AREA:
        return dict(area=round(area, 1), measurable=False)
    med = crop.median
    return dict(area=round(area, 1), measurable=True, dark=round(float((vin < DARK * med).mean()), 3),
                inside=round(float(vin.mean()), 1), ring=round(float(vout.mean()), 1) if len(vout) else None,
                contrast=round(float(vout.mean() - vin.mean()), 1) if len(vout) else 0.0, std=round(float(vin.std()), 1))


def same(a, b, ring):
    """Best normalized correlation of the footprint's patch (3 m around it) between crops a and b
    (same pixel size), over shifts of up to 3 pixels in b."""
    pa = poly_px(a, ring).buffer(3 / (a.px * a.ground))
    if pa.is_empty:
        return None
    m, box = mask(a.gray.shape, pa)
    if m is None or m.shape[0] < 4 or m.shape[1] < 4:
        return None
    x0, y0, x1, y1 = box
    va = a.gray[y0:y1, x0:x1][m].astype(np.float64)
    if va.std() < 1:
        return None
    # A pixel of a maps to b through the footprint's own center, each with its registration.
    lo = np.mean([p[0] for p in ring]); la = np.mean([p[1] for p in ring])
    ca, ra = a.pixel(lo, la); cb, rb = b.pixel(lo, la)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    k = a.px / b.px
    best = None
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            bx = np.round((xs - ca) * k + cb + dx).astype(int)
            by = np.round((ys - ra) * k + rb + dy).astype(int)
            if bx.min() < 0 or by.min() < 0 or bx.max() >= b.gray.shape[1] or by.max() >= b.gray.shape[0]:
                return None
            vb = b.gray[by, bx][m].astype(np.float64)
            if vb.std() < 1:
                continue
            c = float(np.corrcoef(va, vb)[0, 1])
            best = c if best is None else max(best, c)
    return None if best is None else round(best, 3)


def main(area, inv_path, out_path):
    from pyproj import Transformer
    inv = json.load(open(inv_path))
    crops = {}
    for k in IMAGES:
        c = Crop(area, k)
        c.median = float(np.median(c.gray))
        c.back = Transformer.from_crs(c.meta['crs'], 'EPSG:4326', always_xy=True)
        crops[k] = c
    out = {'area': area, 'images': {k: {kk: v for kk, v in c.meta.items() if kk not in ('registration',)} | {'registration': {kk: v for kk, v in c.meta.get('registration', {}).items() if kk != 'points'}} for k, c in crops.items()}, 'buildings': []}
    items = [('traced', b) for b in inv['traced']] + [('today', b) for b in inv['undated']]
    for n, (kind, b) in enumerate(items):
        rec = {'id': b['id'], 'kind': kind, 'ring': b['ring'], 'images': {}}
        for k in IMAGES:
            rec['images'][k] = {'alone': alone(crops[k], b['ring'], k)}
        for i, k in enumerate(IMAGES[1:-1], 1):
            rec['images'][k]['same_as_next'] = same(crops[k], crops[IMAGES[i + 1]], b['ring'])
        # Automatic calls, from today backward.
        state = 'present' if kind == 'today' else 'gone'
        rec['images']['2021']['auto'] = 'unclear'
        nxt = None
        for k in reversed(IMAGES):
            im = rec['images'][k]
            if k == '1974':
                a = im['alone']
                if not a['measurable']:
                    im['auto'] = 'unclear'
                elif a['dark'] >= 0.55 and a['contrast'] >= 8:
                    im['auto'] = 'present'
                elif a['dark'] <= 0.25 and a['contrast'] <= 0:
                    im['auto'] = 'gone'
                else:
                    im['auto'] = 'unclear'
                continue
            if k == '2021':
                # Against today's map: the map's state, unless the photo argues (looked at on the sheet).
                im['auto'] = state
                nxt = state
                continue
            s = im.get('same_as_next')
            im['auto'] = nxt if (s is not None and s >= SAME and nxt in ('present', 'gone')) else 'unclear'
            nxt = im['auto']
        out['buildings'].append(rec)
        if n % 100 == 0:
            print(n, '/', len(items), file=sys.stderr)
    json.dump(out, open(out_path, 'w'))
    from collections import Counter
    for k in IMAGES:
        print(area, k, Counter((r['kind'], r['images'][k]['auto']) for r in out['buildings']))


if __name__ == '__main__':
    main(*sys.argv[1:])
