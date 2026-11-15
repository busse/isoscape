#!/usr/bin/env python3
"""The streetcar "menu": the 1925 system map framed by numbered boxes, one per stop or
attraction, each a close view of the same scene with its title, line and a sourced note.

Products, each a print file at 300 dpi:
  menu        the big map framed by every box, 32 x 24 in (Printful's 24 x 32, landscape)
  map         the big map alone, with its title band and stop list, 36 x 24 in
  box <id>    one stop on its own, 24 x 18 in (Printful's 18 x 24, landscape)

Two steps, because the scene needs the cached data and the drawing needs a fast SVG renderer:

1. Where the data is (after `isoscape build richmond-streetcars --year 1925 --out
   out/streetcars/big`, and the same with `--streetcar-scale 1.5 --out out/streetcars/fine`
   for the single stops, whose lines read better thinner up close):
     python3 tools/streetcars/menu.py points        # writes out/streetcars/points.json
2. Anywhere with rsvg-convert, with the two SVGs and points.json alongside:
     python3 tools/streetcars/menu.py menu|map|boxes [ids...] [--dpi 300] [--dir out/streetcars]

Every box is rasterized straight from the vector at the pixels it fills.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'print'))
import compose as C  # noqa: E402

REGION, YEAR = 'richmond-streetcars', 1925
SVG_NAME = f'{REGION}-{YEAR}.svg'
MENU_GROUND = 1800          # meters of ground across a box on the menu
BOX_GROUND = 2100           # meters across a single-stop print
BOX_ASPECT = 1.6            # menu boxes, width / height
MAX_BYTES = 15_000_000      # the store's upload ceiling for a print file
TRAM = '#b8362c'            # palette.ts paper.tram: the lines' red
PAPER, INK, DIM = C.PAPER, C.INK, C.DIM

TITLE = "Richmond's Streetcars, 1925"
SUBTITLE = 'Sixteen car lines and the places they ran to, in the city that gave the world the electric streetcar'
NOTE = ("Lines follow today's streets, placed from the City Planning Commission's plate of the 1925 routes and the "
        'sources cited for each; some ends are approximate. Buildings are those standing by 1925.')
CREDIT = ('isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  Elevation: USGS 3DEP  ·  '
          'Buildings dated from City of Richmond assessor records and traced from Sanborn maps (Library of Congress)  ·  '
          'Routes after Harland Bartholomew & Associates for the City Planning Commission, plate 53 (1943)')


def font(kind, px):
    return ImageFont.truetype(C.FONT[kind], max(6, round(px)))


def stops():
    return sorted(json.load(open(os.path.join(HERE, 'stops.json')))['stops'], key=lambda s: s['n'])


def routes():
    return json.load(open(os.path.join(HERE, 'routes.json')))['routes']


# ---- step 1: where the stops fall in the scene ------------------------------------------------

def write_points(out_dir):
    S = stops()
    args = [f"{s['at'][0]},{s['at'][1]}" for s in S]
    r = subprocess.run(['node', 'bin/isoscape.js', 'locate', REGION, '--year', str(YEAR), '--', *args],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    pts = {s['id']: [p['x'], p['y']] for s, p in zip(S, json.loads(r.stdout))}
    os.makedirs(out_dir, exist_ok=True)
    json.dump(pts, open(os.path.join(out_dir, 'points.json'), 'w'), indent=1)
    print('points', len(pts))


# ---- step 2: drawing --------------------------------------------------------------------------

class Scene:
    """One built SVG: its viewBox, and windows of it rendered to pixels."""

    def __init__(self, path):
        src = open(path, encoding='utf-8').read()
        self.src = re.sub(r'<g class="caption".*?</g>', '', src, flags=re.S)
        m = re.search(r'viewBox="([^"]+)"', self.src)
        self.vb = list(map(float, m.group(1).split()))
        self.scale = json.load(open(os.path.join(ROOT, 'regions', f'{REGION}.json')))['scale']
        self._content = None

    def render(self, box, w, h):
        """The window `box` (x, y, w, h in SVG units) at w x h px."""
        x, y, bw, bh = box
        svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{x:.2f} {y:.2f} {bw:.2f} {bh:.2f}"', self.src, count=1)
        svg = svg.replace('<svg ', f'<svg width="{w}" height="{h}" preserveAspectRatio="none" ', 1)
        with tempfile.TemporaryDirectory() as t:
            p, o = os.path.join(t, 'a.svg'), os.path.join(t, 'a.png')
            open(p, 'w', encoding='utf-8').write(svg)
            if shutil.which('rsvg-convert'):
                subprocess.run(['rsvg-convert', '-w', str(w), '-h', str(h), '-b', PAPER, p, '-o', o], check=True)
            else:
                C.svg_to_png(p, o, w, h, PAPER)
            return Image.open(o).convert('RGB')

    def content(self):
        """The drawn plate, without the paper around it (SVG units)."""
        if self._content is None:
            w = 1600
            h = round(w * self.vb[3] / self.vb[2])
            a = np.asarray(self.render(self.vb, w, h)).astype(int)
            bg = np.array(Image.new('RGB', (1, 1), PAPER).getpixel((0, 0)))
            ys, xs = np.where(np.abs(a - bg).sum(-1) > 12)
            k = self.vb[2] / w
            self._content = (self.vb[0] + xs.min() * k, self.vb[1] + ys.min() * k,
                             (xs.max() - xs.min() + 1) * k, (ys.max() - ys.min() + 1) * k)
        return self._content

    def window(self, center, ground_w, aspect):
        """A window `ground_w` meters across, centered on an SVG point, kept on the plate."""
        cx0, cy0, cw, ch = self.content()
        w = ground_w * self.scale
        h = w / aspect
        x = min(max(center[0] - w / 2, cx0), cx0 + cw - w)
        y = min(max(center[1] - h / 2, cy0), cy0 + ch - h)
        return (x, y, w, h)


def wrap(d, text, f, max_w):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= max_w: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def marker(d, x, y, n, r):
    d.ellipse((x - r, y - r, x + r, y + r), fill=PAPER, outline=TRAM, width=max(2, round(r * 0.18)))
    f = font('bold', r * 1.1)
    t = str(n)
    d.text((x - d.textlength(t, font=f) / 2, y - r * 0.6), t, font=f, fill=INK)


def credit_lines(d, text, x, y, w, size):
    f = font('regular', size)
    for ln in wrap(d, text, f, w):
        d.text((x, y), ln, font=f, fill=DIM); y += size * 1.4
    return y


def paste_map(img, d, scene, pts, box, x, y, w, h, r):
    """The scene's window `box` drawn into (x, y, w, h), with a numbered marker at each stop."""
    img.paste(scene.render(box, round(w), round(h)), (round(x), round(y)))
    k = w / box[2]
    for s in stops():
        px, py = pts[s['id']]
        if box[0] <= px <= box[0] + box[2] and box[1] <= py <= box[1] + box[3]:
            marker(d, x + (px - box[0]) * k, y + (py - box[1]) * k, s['n'], r)


def map_box(scene, aspect, top_share=0.55):
    """The whole plate cut to `aspect`, trimming top and bottom (or the sides) as needed."""
    x, y, w, h = scene.content()
    if w / h < aspect:
        nh = w / aspect
        return (x, y + (h - nh) * top_share, w, nh)
    nw = h * aspect
    return (x + (w - nw) / 2, y, nw, h)


def compose_menu(dpi, big, pts):
    I = lambda v: v * dpi
    W, H = round(I(32)), round(I(24))
    m, g, head, foot = I(0.75), I(0.26), I(1.35), I(0.5)
    cw = (W - 2 * m - 4 * g) / 5
    ch = (H - 2 * m - head - foot - 3 * g) / 4
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.text((m, m - I(0.05)), TITLE, font=font('bold', I(0.5)), fill=INK)
    d.text((m, m + I(0.64)), SUBTITLE, font=font('italic', I(0.19)), fill=DIM)
    rule = m + head - I(0.22)
    d.line((m, rule, W - m, rule), fill=INK, width=max(1, round(I(0.012))))
    # The line key, four columns of four, at the right of the title band.
    kx, kw = W - m - I(15.2), I(15.2)
    nf = font('regular', I(0.135))
    for i, r in enumerate(routes()):
        x, y = kx + (i // 4) * kw / 4, m + (i % 4) * I(0.255)
        d.line((x, y + I(0.085), x + I(0.28), y + I(0.085)), fill=TRAM, width=max(2, round(I(0.06))))
        d.text((x + I(0.38), y), r['name'], font=nf, fill=INK)
    top = m + head
    cell = lambda c, r: (m + c * (cw + g), top + r * (ch + g))
    # Clockwise from the top left: five along the top, two down the right, five back along the
    # bottom, two up the left.
    order = [(c, 0) for c in range(5)] + [(4, 1), (4, 2)] + [(c, 3) for c in range(4, -1, -1)] + [(0, 2), (0, 1)]
    ih = cw / BOX_ASPECT
    for s, (c, r) in zip(stops(), order):
        x, y = cell(c, r)
        img.paste(big.render(big.window(pts[s['id']], MENU_GROUND, BOX_ASPECT), round(cw), round(ih)), (round(x), round(y)))
        d.rectangle((x, y, x + cw, y + ih), outline=INK, width=max(1, round(I(0.01))))
        box_text(d, s, x, y + ih + I(0.1), cw, ch - ih - I(0.1), dpi)
    mx, my = cell(1, 1)
    mw, mh = 3 * cw + 2 * g, 2 * ch + g
    paste_map(img, d, big, pts, map_box(big, mw / mh), mx, my, mw, mh, I(0.12))
    d.rectangle((mx, my, mx + mw, my + mh), outline=INK, width=max(1, round(I(0.01))))
    credit_lines(d, NOTE + '  ' + CREDIT, m, H - m - foot + I(0.12), W - 2 * m, I(0.085))
    return img


def box_text(d, s, x, y, w, h, dpi):
    """Number, title, line and note under a menu box."""
    I = lambda v: v * dpi
    r = I(0.13)
    marker(d, x + r, y + r, s['n'], r)
    d.text((x + 2 * r + I(0.08), y - I(0.01)), s['title'], font=font('bold', I(0.17)), fill=INK)
    d.text((x, y + 2 * r + I(0.04)), s['line'], font=font('italic', I(0.105)), fill=TRAM)
    nf = font('regular', I(0.104))
    ny, lh = y + 2 * r + I(0.24), I(0.104) * 1.45
    for ln in wrap(d, s['note'], nf, w):
        if ny + lh > y + h + I(0.02): break
        d.text((x, ny), ln, font=nf, fill=INK); ny += lh


def compose_map(dpi, big, pts):
    I = lambda v: v * dpi
    W, H = round(I(36)), round(I(24))
    m, band = I(0.75), I(1.75)
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mw, mh = W - 2 * m, H - 2 * m - band
    paste_map(img, d, big, pts, map_box(big, mw / mh), m, m, mw, mh, I(0.13))
    d.rectangle((m, m, m + mw, m + mh), outline=INK, width=max(1, round(I(0.01))))
    by = m + mh + I(0.3)
    d.text((m, by), TITLE, font=font('bold', I(0.48)), fill=INK)
    d.text((m, by + I(0.63)), SUBTITLE, font=font('italic', I(0.19)), fill=DIM)
    nb = ' '
    names = '   '.join(str(s['n']) + nb + s['title'].replace(' ', nb) for s in stops())
    kf = font('regular', I(0.15))
    ky = by + I(0.98)
    for ln in wrap(d, names, kf, mw):
        d.text((m, ky), ln, font=kf, fill=INK); ky += I(0.15) * 1.4
    credit_lines(d, NOTE + '  ' + CREDIT, m, H - m + I(0.12), mw, I(0.075))
    return img


def compose_box(dpi, fine, s, pt):
    I = lambda v: v * dpi
    W, H = round(I(24)), round(I(18))
    m = I(0.75)
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    iw = W - 2 * m
    ih = I(12.6)
    img.paste(fine.render(fine.window(pt, BOX_GROUND, iw / ih), round(iw), round(ih)), (round(m), round(m)))
    d.rectangle((m, m, m + iw, m + ih), outline=INK, width=max(1, round(I(0.01))))
    ty = m + ih + I(0.35)
    r = I(0.3)
    marker(d, m + r, ty + r, s['n'], r)
    tx = m + 2 * r + I(0.22)
    d.text((tx, ty - I(0.04)), s['title'], font=font('bold', I(0.5)), fill=INK)
    d.text((tx, ty + I(0.66)), f"{s['line']}  ·  Richmond's streetcars, 1925", font=font('italic', I(0.2)), fill=TRAM)
    nf = font('regular', I(0.235))
    ny = ty + I(1.2)
    for ln in wrap(d, s['note'], nf, iw * 0.8):
        d.text((m, ny), ln, font=nf, fill=INK); ny += I(0.235) * 1.5
    credit_lines(d, CREDIT, m, H - I(0.55), iw, I(0.075))
    return img


def save(img, out_dir, name, dpi):
    os.makedirs(out_dir, exist_ok=True)
    w_in, h_in = round(img.size[0] / dpi), round(img.size[1] / dpi)
    p = os.path.join(out_dir, f'{name}_{w_in}x{h_in}.jpg')
    for q in (94, 90, 86, 82, 78):
        img.save(p, quality=q, dpi=(dpi, dpi), optimize=True)
        if os.path.getsize(p) <= MAX_BYTES: break
    print(p, img.size, f'{os.path.getsize(p) / 1e6:.1f} MB q{q}')


SITE = 'https://busse.github.io/isoscape/'
BUILD = f'{REGION}:{YEAR}'


def write_page(pts):
    """pages/streetcars.md, from the same stops, lines and sources as the prints."""
    out = ['---', "title: Richmond's streetcars, 1925", 'order: 45',
           'summary: The 1925 car lines and fourteen places they ran to, drawn from a 1943 planning plate and the buildings standing then.',
           'social: streetcars-social.jpg', '---', '', "# Richmond's streetcars, 1925", '',
           "In May 1888 Frank Sprague's electric cars began running on Richmond's hills, the first big electric",
           'street railway that worked, and the city grew out along the lines. This map draws the system as it',
           'stood in 1925: sixteen car lines over the buildings then standing, with fourteen places the cars',
           'ran to framed around it, from the suburbs they made to the trolley parks at the ends of the line.', '',
           '![The 1925 map, framed by its fourteen stops](streetcars-menu.jpg)', '',
           f'[Open the map]({SITE}#{BUILD}) to pan and zoom, or jump to a stop below.', '', '## The stops', '']
    for s in stops():
        x, y = pts[s['id']]
        out += [f"### {s['n']}. {s['title']}", '', f"*{s['line']}*", '', s['note'], '',
                f"[See it on the map]({SITE}#{BUILD}@{x:.0f},{y:.0f},6) · Sources: " +
                ' '.join(f'[{k + 1}]({u})' for k, u in enumerate(s['sources'])), '']
    out += ['## The lines', '', 'Each line follows the streets its sources name, placed on today\'s streets. Where a',
            'source is silent, the ends are approximate.', '', '| Line | Route | Ran |', '|---|---|---|']
    for r in routes():
        out.append(f"| {r['name']} | {r['route']} | {r['from']}–{r['to']} |")
    out += ['', '## How it was drawn', '',
            "The routes come from plate 53 of Harland Bartholomew & Associates' 1943 report to the City",
            "Planning Commission, *Early Transit Routes, 1888 & 1925*, with the details from the sources",
            'listed for each line. Buildings are the ones standing today that the city assessor dates to',
            '1925 or before, plus those traced from Sanborn fire-insurance maps downtown; small streets are',
            'drawn only where a house of the year stood nearby. Henrico County keeps no such dates online,',
            'so the suburbs across the 1925 county line look emptier than they were. On the big map, lines',
            'and cars are drawn three times life size; on the single-stop prints, one and a half.', '',
            'More in [How it\'s made](how-its-made.md#time).', '']
    open(os.path.join(ROOT, 'pages', 'streetcars.md'), 'w').write('\n'.join(out))
    print('pages/streetcars.md')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['points', 'menu', 'map', 'boxes', 'page'])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--dpi', type=int, default=300)
    ap.add_argument('--dir', default=os.path.join(ROOT, 'out', 'streetcars'))
    a = ap.parse_args()
    if a.what == 'points': return write_points(a.dir)
    pts = json.load(open(os.path.join(a.dir, 'points.json')))
    if a.what == 'page': return write_page(pts)
    out = os.path.join(a.dir, 'print' if a.dpi >= 300 else f'proof-{a.dpi}')
    if a.what in ('menu', 'map'):
        big = Scene(os.path.join(a.dir, 'big', SVG_NAME))
        img = compose_menu(a.dpi, big, pts) if a.what == 'menu' else compose_map(a.dpi, big, pts)
        save(img, out, f'streetcars-1925-{a.what}', a.dpi)
    else:
        fine = Scene(os.path.join(a.dir, 'fine', SVG_NAME))
        for s in stops():
            if a.ids and s['id'] not in a.ids: continue
            save(compose_box(a.dpi, fine, s, pts[s['id']]), out, f"streetcars-1925-{s['n']:02d}-{s['id']}", a.dpi)


if __name__ == '__main__':
    main()
