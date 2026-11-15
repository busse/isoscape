#!/usr/bin/env python3
"""The streetcar "menu": the 1925 system map framed by numbered boxes, one per stop or
attraction, each a close view cut from the same map with its title, line and a sourced note.

Three kinds of print come out of one master render:
  menu       the big map framed by every box (40 x 30 in)
  map        the big map alone, with its title band (36 x 24 in)
  box <id>   one stop on its own (24 x 18 in), for each stop in stops.json

Run from the repo root, after `isoscape build richmond-streetcars --year 1925`:
  python3 tools/streetcars/menu.py master            # render the master PNG (slow: ~90 s)
  python3 tools/streetcars/menu.py menu  [--dpi 100]
  python3 tools/streetcars/menu.py map   [--dpi 100]
  python3 tools/streetcars/menu.py boxes [--dpi 100] [id ...]
Output goes to out/streetcars/.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'print'))
import compose as C  # noqa: E402

REGION, YEAR = 'richmond-streetcars', 1925
SVG = os.path.join(ROOT, 'out', f'{REGION}-{YEAR}.svg')
OUT = os.path.join(ROOT, 'out', 'streetcars')
MASTER = os.path.join(OUT, 'master.png')
MASTER_W = 13600            # px across the whole SVG: about 1 px per ground metre
BOX_GROUND = 1800           # metres of ground across a box
TRAM = '#b8362c'            # palette.ts paper.tram: the lines' red
PAPER, INK, DIM = C.PAPER, C.INK, C.DIM
CREDIT = ('isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  Elevation: USGS 3DEP  ·  '
          'Buildings dated from City of Richmond assessor records and traced from Sanborn maps (Library of Congress)  ·  '
          'Lines from the 1925 transit plate of the City Planning Commission (Harland Bartholomew & Associates, 1943)')
TITLE = "Richmond's Streetcars, 1925"
SUBTITLE = 'The city the trolley built: sixteen car lines and the places they served'


def font(kind, px):
    return ImageFont.truetype(C.FONT[kind], max(6, round(px)))


def region_scale():
    return json.load(open(os.path.join(ROOT, 'regions', f'{REGION}.json')))['scale']


def viewbox():
    head = open(SVG, encoding='utf-8').read(400)
    return list(map(float, re.search(r'viewBox="([^"]+)"', head).group(1).split()))


def render_master():
    os.makedirs(OUT, exist_ok=True)
    src = open(SVG, encoding='utf-8').read()
    src = re.sub(r'<g class="caption".*?</g>', '', src, flags=re.S)
    tmp = os.path.join(OUT, 'master.svg')
    open(tmp, 'w', encoding='utf-8').write(src)
    C.svg_to_png(tmp, MASTER, MASTER_W)
    os.remove(tmp)
    print('master', Image.open(MASTER).size)


def stops():
    return json.load(open(os.path.join(HERE, 'stops.json')))['stops']


def locate(points):
    """SVG coordinates of lon/lat points, from the scene itself (`isoscape locate`)."""
    args = [f'{lon},{lat}' for lon, lat in points]
    r = subprocess.run(['node', 'bin/isoscape.js', 'locate', REGION, '--year', str(YEAR), '--', *args],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    return [(p['x'], p['y']) for p in json.loads(r.stdout)]


class Master:
    def __init__(self):
        self.img = Image.open(MASTER).convert('RGB')
        self.vb = viewbox()
        self.k = self.img.size[0] / self.vb[2]          # px per SVG unit
        a = np.asarray(self.img.resize((self.img.size[0] // 8, self.img.size[1] // 8)))
        bg = a[2, 2].astype(int)
        mask = np.abs(a.astype(int) - bg).sum(-1) > 12
        ys, xs = np.where(mask)
        self.content = (xs.min() * 8, ys.min() * 8, (xs.max() + 1) * 8, (ys.max() + 1) * 8)

    def px(self, x, y):
        return ((x - self.vb[0]) * self.k, (y - self.vb[1]) * self.k)

    def crop(self, centre, ground_w, aspect, size):
        """A box `ground_w` metres across, centred on an SVG point, resized to `size`."""
        w = ground_w * region_scale() * self.k
        h = w / aspect
        cx, cy = self.px(*centre)
        x0 = min(max(cx - w / 2, 0), self.img.size[0] - w)
        y0 = min(max(cy - h / 2, 0), self.img.size[1] - h)
        return self.img.crop((round(x0), round(y0), round(x0 + w), round(y0 + h))).resize(size, Image.LANCZOS)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= max_w: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def marker(d, x, y, n, r):
    d.ellipse((x - r, y - r, x + r, y + r), fill=PAPER, outline=TRAM, width=max(2, round(r * 0.18)))
    f = font('bold', r * 1.15)
    t = str(n)
    d.text((x - d.textlength(t, font=f) / 2, y - r * 0.62), t, font=f, fill=INK)


def text_block(d, s, x, y, w, h, scale):
    """Number, title, line, note: the words under a box."""
    r = 0.17 * scale
    marker(d, x + r, y + r * 1.05, s['n'], r)
    tf = font('bold', 0.215 * scale)
    d.text((x + 2 * r + 0.1 * scale, y + r * 0.2), s['title'], font=tf, fill=INK)
    lf = font('italic', 0.13 * scale)
    ly = y + 2.35 * r
    d.text((x, ly), s['line'], font=lf, fill=TRAM)
    nf = font('regular', 0.118 * scale)
    ny = ly + 0.26 * scale
    lh = nf.size * 1.48
    for ln in wrap(d, s['note'], nf, w):
        if ny + lh > y + h: break
        d.text((x, ny), ln, font=nf, fill=INK); ny += lh


def compose_menu(dpi):
    M, S = Master(), stops()
    pts = dict(zip([s['id'] for s in S], locate([s['at'] for s in S])))
    W, H = 40 * dpi, 30 * dpi
    m, g = 1.1 * dpi, 0.38 * dpi
    head, foot = 1.75 * dpi, 0.55 * dpi
    cw = (W - 2 * m - 4 * g) / 5
    ch = (H - 2 * m - head - foot - 3 * g) / 4
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # Title band.
    tf = font('bold', 0.62 * dpi)
    d.text((m, m), TITLE, font=tf, fill=INK)
    sf = font('italic', 0.27 * dpi)
    d.text((m, m + 0.82 * dpi), SUBTITLE, font=sf, fill=DIM)
    d.line((m, m + head - 0.32 * dpi, W - m, m + head - 0.32 * dpi), fill=INK, width=max(1, dpi // 50))
    top = m + head
    cell = lambda c, r: (m + c * (cw + g), top + r * (ch + g))
    # Clockwise from the top left: five along the top, two down the right, five back along the
    # bottom, two up the left.
    order = [(c, 0) for c in range(5)] + [(4, 1), (4, 2)] + [(c, 3) for c in range(4, -1, -1)] + [(0, 2), (0, 1)]
    img_h = cw * 9 / 16
    for s, (c, r) in zip(sorted(S, key=lambda s: s['n']), order):
        x, y = cell(c, r)
        box = M.crop(pts[s['id']], BOX_GROUND, 16 / 9, (round(cw), round(img_h)))
        img.paste(box, (round(x), round(y)))
        d.rectangle((x, y, x + cw, y + img_h), outline=INK, width=max(1, dpi // 60))
        text_block(d, s, x, y + img_h + 0.14 * dpi, cw, ch - img_h - 0.14 * dpi, dpi)
    # The map: the middle three columns by two rows, letterboxed, with a key of the lines beside.
    mx, my = cell(1, 1)
    mw, mh = 3 * cw + 2 * g, 2 * ch + g
    x0, y0, x1, y1 = M.content
    aspect = (x1 - x0) / (y1 - y0)
    key_w = 2.9 * dpi
    fw = min(mw - key_w - g, mh * aspect)
    fh = fw / aspect
    fx, fy = mx + key_w + g + (mw - key_w - g - fw) / 2, my + (mh - fh) / 2
    big = M.img.crop((x0, y0, x1, y1)).resize((round(fw), round(fh)), Image.LANCZOS)
    img.paste(big, (round(fx), round(fy)))
    sc = fw / (x1 - x0)
    for s in S:
        px, py = M.px(*pts[s['id']])
        marker(d, fx + (px - x0) * sc, fy + (py - y0) * sc, s['n'], 0.14 * dpi)
    draw_key(d, mx, my, key_w, mh, dpi)
    # Credit.
    cf = font('regular', 0.105 * dpi)
    cy = H - m - foot + 0.2 * dpi
    for ln in wrap(d, CREDIT, cf, W - 2 * m):
        d.text((m, cy), ln, font=cf, fill=DIM); cy += cf.size * 1.4
    return img


def draw_key(d, x, y, w, h, dpi):
    routes = json.load(open(os.path.join(HERE, 'routes.json')))['routes']
    hf = font('bold', 0.2 * dpi)
    d.text((x, y), 'The lines in 1925', font=hf, fill=INK)
    nf, rf = font('regular', 0.125 * dpi), font('italic', 0.105 * dpi)
    yy = y + 0.42 * dpi
    for r in routes:
        d.line((x, yy + 0.09 * dpi, x + 0.3 * dpi, yy + 0.09 * dpi), fill=TRAM, width=max(2, round(0.06 * dpi)))
        d.text((x + 0.42 * dpi, yy), r['name'], font=nf, fill=INK)
        yy += nf.size * 1.25
        for ln in wrap(d, r['route'], rf, w - 0.42 * dpi)[:2]:
            d.text((x + 0.42 * dpi, yy), ln, font=rf, fill=DIM); yy += rf.size * 1.3
        yy += 0.07 * dpi
        if yy > y + h - 0.6 * dpi: break
    note = ('Lines are placed on today\'s streets from the 1925 plate and the sources cited for each; '
            'some ends are approximate. Buildings are those standing by 1925. Cars and lines are drawn three times life size.')
    yy = max(yy + 0.1 * dpi, y + h - 1.1 * dpi)
    for ln in wrap(d, note, rf, w):
        d.text((x, yy), ln, font=rf, fill=DIM); yy += rf.size * 1.35


def compose_map(dpi):
    M = Master()
    S = stops()
    pts = dict(zip([s['id'] for s in S], locate([s['at'] for s in S])))
    W, H = 36 * dpi, 24 * dpi
    m, band = 0.9 * dpi, 1.5 * dpi
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = M.content
    aspect = (x1 - x0) / (y1 - y0)
    aw, ah = W - 2 * m, H - 2 * m - band
    fw = min(aw, ah * aspect); fh = fw / aspect
    fx, fy = m + (aw - fw) / 2, m
    img.paste(M.img.crop((x0, y0, x1, y1)).resize((round(fw), round(fh)), Image.LANCZOS), (round(fx), round(fy)))
    sc = fw / (x1 - x0)
    for s in S:
        px, py = M.px(*pts[s['id']])
        marker(d, fx + (px - x0) * sc, fy + (py - y0) * sc, s['n'], 0.13 * dpi)
    by = H - m - band + 0.3 * dpi
    d.text((m, by), TITLE, font=font('bold', 0.5 * dpi), fill=INK)
    d.text((m, by + 0.68 * dpi), SUBTITLE, font=font('italic', 0.22 * dpi), fill=DIM)
    names = '   '.join(f"{s['n']} {s['title']}" for s in sorted(S, key=lambda s: s['n']))
    kf = font('regular', 0.12 * dpi)
    ky = by + 1.02 * dpi
    for ln in wrap(d, names, kf, W - 2 * m):
        d.text((m, ky), ln, font=kf, fill=INK); ky += kf.size * 1.4
    cf = font('regular', 0.085 * dpi)
    cy = H - 0.55 * dpi
    for ln in wrap(d, CREDIT, cf, W - 2 * m):
        d.text((m, cy), ln, font=cf, fill=DIM); cy += cf.size * 1.35
    return img


def compose_box(dpi, s, pt, M):
    W, H = 24 * dpi, 18 * dpi
    m = 0.8 * dpi
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    iw = W - 2 * m
    ih = iw * 9 / 16
    pic = M.crop(pt, BOX_GROUND * 1.2, 16 / 9, (round(iw), round(ih)))
    img.paste(pic, (round(m), round(m)))
    d.rectangle((m, m, m + iw, m + ih), outline=INK, width=max(1, dpi // 60))
    ty = m + ih + 0.35 * dpi
    r = 0.3 * dpi
    marker(d, m + r, ty + r, s['n'], r)
    d.text((m + 2 * r + 0.2 * dpi, ty - 0.02 * dpi), s['title'], font=font('bold', 0.5 * dpi), fill=INK)
    d.text((m + 2 * r + 0.2 * dpi, ty + 0.68 * dpi), f"{s['line']}  ·  Richmond's streetcars, 1925", font=font('italic', 0.2 * dpi), fill=TRAM)
    nf = font('regular', 0.2 * dpi)
    ny = ty + 1.15 * dpi
    for ln in wrap(d, s['note'], nf, iw * 0.78):
        d.text((m, ny), ln, font=nf, fill=INK); ny += nf.size * 1.5
    cf = font('regular', 0.075 * dpi)
    cy = H - 0.5 * dpi
    for ln in wrap(d, CREDIT, cf, W - 2 * m):
        d.text((m, cy), ln, font=cf, fill=DIM); cy += cf.size * 1.35
    return img


def save(img, name, dpi):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f'{name}-{dpi}dpi.jpg')
    img.save(p, quality=90, dpi=(dpi, dpi))
    print(p, img.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['master', 'menu', 'map', 'boxes'])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--dpi', type=int, default=100)
    a = ap.parse_args()
    if a.what == 'master': render_master()
    elif a.what == 'menu': save(compose_menu(a.dpi), 'menu', a.dpi)
    elif a.what == 'map': save(compose_map(a.dpi), 'map', a.dpi)
    else:
        M, S = Master(), [s for s in stops() if not a.ids or s['id'] in a.ids]
        for s, pt in zip(S, locate([s['at'] for s in S])):
            save(compose_box(a.dpi, s, pt, M), f"box-{s['n']:02d}-{s['id']}", a.dpi)


if __name__ == '__main__':
    main()
