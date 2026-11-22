"""Pictures of the comparison: both sets over the scan, and over today's street grid with the
differences colored; and close-ups of chosen areas.

    python3 -I pictures.py <scan.jpg> <georef.json> <osm.json> <redrawn.geojson> <other.geojson> <out dir> <label,label,...>

Writes compare.png (two panels: over the scan; over the streets) and enlarge-<label>.png for
each label given (the same two views, close up). Colors: redrawn outline magenta, the other set
cyan; on the street panel, land only in the redrawn set magenta, only in the other set cyan,
in both a pale tint by grade.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import georef  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
MAG = (230, 0, 160)
CYA = (0, 170, 220)
TINT = {'A': (196, 224, 186), 'B': (190, 212, 232), 'C': (238, 232, 170), 'D': (238, 196, 200)}
KEEP = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk', 'motorway'}


def font(n):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def load(p):
    out = {}
    for f in json.load(open(p))['features']:
        lab = (f['properties'].get('label') or '').strip()
        if f['properties'].get('grade') in TINT:
            out[lab] = {'grade': f['properties']['grade'], 'g': shape(f['geometry']).buffer(0)}
    return out


def to_m(g):
    from shapely import transform
    return transform(g, lambda c: np.c_[georef.to_m(c[:, 0], c[:, 1])])


def rings(g):
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type != 'Polygon':
            continue
        yield np.array(p.exterior.coords)
        for h in p.interiors:
            yield np.array(h.coords)


def polys(g):
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type == 'Polygon':
            yield p


class View:
    """Ground meters -> picture pixels, by way of either the scan (through the fit) or a plain
    north-up plane."""
    def __init__(self, t, box, scale, scan_mode):
        self.t, self.box, self.s, self.scan = t, box, scale, scan_mode

    def px(self, xy):
        xy = np.asarray(xy, float)
        if self.scan:
            uv = georef.inverse(self.t, xy, guess=((self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2))
            return (uv - [self.box[0], self.box[1]]) * self.s
        return np.c_[(xy[:, 0] - self.box[0]) * self.s, (self.box[3] - xy[:, 1]) * self.s]


def draw_scan(scan_im, t, box_px, width, R, M, labels_at=None):
    x0, y0, x1, y1 = box_px
    s = width / (x1 - x0)
    im = scan_im.crop((x0, y0, x1, y1)).resize((width, int((y1 - y0) * s)), Image.LANCZOS)
    im = Image.blend(im, Image.new('RGB', im.size, 'white'), 0.25)
    d = ImageDraw.Draw(im)
    v = View(t, (x0, y0, x1, y1), s, True)
    lw = max(2, int(round(width / 900)))
    for S, col in ((M, CYA), (R, MAG)):
        for a in S.values():
            for r in rings(a['gm']):
                d.line([tuple(p) for p in v.px(r)], fill=col, width=lw)
    return im, v


def fill(im, v, p, col):
    """Fill polygon p (with its holes left unpainted) through a mask, so a hole never wipes
    what is under it."""
    m = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(m)
    d.polygon([tuple(q) for q in v.px(np.array(p.exterior.coords))], fill=255)
    for h in p.interiors:
        d.polygon([tuple(q) for q in v.px(np.array(h.coords))], fill=0)
    im.paste(col, (0, 0), m)


def draw_ground(osm_lines, box_m, width, R, M, title_labels=True):
    x0, y0, x1, y1 = box_m
    s = width / (x1 - x0)
    H = int((y1 - y0) * s)
    im = Image.new('RGB', (width, H), 'white')
    d = ImageDraw.Draw(im)
    v = View(None, box_m, s, False)
    # tint where both agree, then the differences
    for lab, a in M.items():
        r = R.get(lab)
        if not r:
            continue
        both = a['gm'].intersection(r['gm'])
        for p in polys(both):
            fill(im, v, p, TINT[a['grade']])
    allr = unary_union([a['gm'] for a in R.values()])
    allm = unary_union([a['gm'] for a in M.values()])
    for g, col in ((allr.difference(allm), MAG), (allm.difference(allr), CYA)):
        for p in polys(g):
            if p.area < 50:
                continue
            fill(im, v, p, col)
    # where both sets cover the land but give it different areas (a piece named differently)
    for lab, a in R.items():
        for lab2, b in M.items():
            if lab2 == lab or a['grade'] != b['grade']:
                continue
            x = a['gm'].intersection(b['gm'])
            if x.area < 2000:
                continue
            for p in polys(x):
                fill(im, v, p, (255, 150, 0))
    for ln in osm_lines:
        if ln[:, 0].max() < x0 or ln[:, 0].min() > x1 or ln[:, 1].max() < y0 or ln[:, 1].min() > y1:
            continue
        d.line([tuple(q) for q in v.px(ln)], fill=(120, 120, 120), width=1)
    lw = max(1, int(round(width / 1400)))
    for S, col in ((M, CYA), (R, MAG)):
        for a in S.values():
            for r in rings(a['gm']):
                d.line([tuple(q) for q in v.px(r)], fill=col, width=lw)
    if title_labels:
        f = font(max(12, width // 110))
        for lab, a in R.items():
            p = a['gm'].representative_point() if a['gm'].geom_type == 'Polygon' else max(a['gm'].geoms, key=lambda q: q.area).representative_point()
            q = v.px([[p.x, p.y]])[0]
            d.text(tuple(q), lab, fill='black', font=f, anchor='mm', stroke_width=2, stroke_fill='white')
    return im, v


def legend(im, lines, size=22):
    d = ImageDraw.Draw(im)
    f = font(size)
    y = 10
    for col, txt in lines:
        if col:
            d.rectangle([10, y + 4, 34, y + size], fill=col)
        d.text((44, y), txt, fill='black', font=f)
        y += size + 8


def osm_lines(osm):
    d = json.load(open(osm))
    out = []
    for e in d['elements']:
        tg = e.get('tags', {})
        if e['type'] != 'way' or tg.get('highway') not in KEEP:
            continue
        g = [p for p in (e.get('geometry') or []) if p]
        if len(g) < 2:
            continue
        x, y = georef.to_m([p['lon'] for p in g], [p['lat'] for p in g])
        out.append(np.c_[x, y])
    return out


def bounds_m(gs, pad):
    b = unary_union(gs).bounds
    return (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)


def main(scan, gj, osm, rp, mp, outdir, labels):
    t = json.load(open(gj))['transform']
    R, M = load(rp), load(mp)
    for S in (R, M):
        for a in S.values():
            a['gm'] = to_m(a['g'])
    scan_im = Image.open(scan).convert('RGB')
    lines = osm_lines(osm)
    # the whole map
    frame = (440, 500, 9390, 7370)
    W = 2400
    a_im, _ = draw_scan(scan_im, t, frame, W, R, M)
    gb = bounds_m([a['gm'] for a in R.values()] + [a['gm'] for a in M.values()], 300)
    b_im, _ = draw_ground(lines, gb, W, R, M)
    head = 60
    out = Image.new('RGB', (W, head + a_im.height + head + b_im.height), 'white')
    d = ImageDraw.Draw(out)
    f = font(30)
    d.text((14, 14), 'Over the 1937 scan (NARA RG 195, via FRASER): redrawn (magenta), Mapping Inequality (cyan)', fill='black', font=f)
    out.paste(a_im, (0, head))
    d.text((14, head + a_im.height + 14), "Over today's streets (OSM): land only in the redrawn set (magenta), only in Mapping Inequality's (cyan), in both under another area's name (orange)", fill='black', font=font(26))
    out.paste(b_im, (0, 2 * head + a_im.height))
    out.save(os.path.join(outdir, 'compare.png'))
    # close-ups
    for lab in [x for x in labels.split(',') if x]:
        gs = [S[lab]['gm'] for S in (R, M) if lab in S]
        bm = bounds_m(gs, 150)
        corners = np.array([[bm[0], bm[1]], [bm[2], bm[1]], [bm[2], bm[3]], [bm[0], bm[3]]])
        uv = georef.inverse(t, corners)
        bp = (int(uv[:, 0].min()), int(uv[:, 1].min()), int(uv[:, 0].max()), int(uv[:, 1].max()))
        w = 1100
        s_im, _ = draw_scan(scan_im, t, bp, w, {lab: R[lab]} if lab in R else {}, {lab: M[lab]} if lab in M else {})
        # on the ground: the area itself and its neighbors of the same grade, so a piece named
        # differently shows
        near = lambda S: {k: a for k, a in S.items() if a['gm'].intersects(Polygon_box(bm))}
        g_im, _ = draw_ground(lines, bm, w, near(R), near(M))
        H = max(s_im.height, g_im.height)
        o = Image.new('RGB', (2 * w + 20, H + 50), 'white')
        d = ImageDraw.Draw(o)
        rr, mm = R.get(lab), M.get(lab)
        iou = rr['gm'].intersection(mm['gm']).area / rr['gm'].union(mm['gm']).area if rr and mm else 0
        d.text((10, 10), f'{lab}: over the scan (left), over today\'s streets (right). IoU {iou:.2f}. Magenta redrawn, cyan Mapping Inequality, orange: land named for another area', fill='black', font=font(20))
        o.paste(s_im, (0, 50))
        o.paste(g_im, (w + 20, 50))
        o.save(os.path.join(outdir, f'enlarge-{lab}.png'))


def Polygon_box(b):
    from shapely.geometry import box
    return box(*b)


if __name__ == '__main__':
    main(*sys.argv[1:])
