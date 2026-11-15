#!/usr/bin/env python3
"""A set: one big map framed by numbered boxes, each a close view of a place (or of the same place
in another year) with a title, a subtitle and a short sourced note, laid out like a menu. The
same files make every product: the framed menu, the map alone, one print per box, canvas
versions, and a page for the explorer. A set is described by sets/<name>.json; see
"Making a set" in the README, and sets/streetcars-1925.json for a worked example.

Products, each a print file at 300 dpi:
  menu        the big map framed by every box, 32 x 24 in (Printful's 24 x 32, landscape)
  map         the big map alone, with a title band and the box list, 36 x 24 in
  boxes       one print per box, 24 x 18 in (Printful's 18 x 24, landscape)
  canvas      framed-canvas files for each, at the sizes the store sells (1.5 in mirrored wrap)
  page        pages/<page.slug>.md, the explorer page with every box, its note and sources

Two places, because the scene needs the cached data and the drawing wants a fast SVG renderer:

1. Where the region's data is cached:
     python3 tools/sets/set.py <set> prepare     # builds each scene's SVG, and points.json
2. Anywhere with rsvg-convert (or cairosvg), with out/sets/<set>/ copied alongside:
     python3 tools/sets/set.py <set> menu|map|boxes [ids...]|canvas|page [--dpi 300]
Output goes to out/sets/<set>/: scenes/, points.json, print/ (300 dpi) or proof-<dpi>/.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'print'))
import compose as C  # noqa: E402

BOX_ASPECT = 1.6            # menu boxes, width / height
MAX_BYTES = 15_000_000      # the store's upload ceiling for a print file
CANVAS = {'menu': ((24, 18), (32, 24)), 'map': ((18, 12), (30, 20), (36, 24)), 'box': ((16, 12), (24, 18))}
CANVAS_DPI = 300
WRAP = 1.5                  # inches of mirrored image around each canvas face, for its sides
SITE = 'https://busse.github.io/isoscape/'
PAPER, INK, DIM = C.PAPER, C.INK, C.DIM
ACCENT = '#b8362c'          # palette.ts paper.tram: markers, rules and subtitles


def font(kind, px):
    return ImageFont.truetype(C.FONT[kind], max(6, round(px)))


class Set:
    def __init__(self, name, out_dir=None):
        self.name = name
        self.cfg = json.load(open(os.path.join(ROOT, 'sets', f'{name}.json')))
        self.dir = out_dir or os.path.join(ROOT, 'out', 'sets', name)
        b = self.cfg['boxes']
        boxes = json.load(open(os.path.join(ROOT, b)))['stops'] if isinstance(b, str) else b
        self.boxes = sorted(boxes, key=lambda s: s['n'])
        self.map = self.cfg['map']
        self.ground = {'menu': 1800, 'box': 2100, **self.cfg.get('ground', {})}

    def sub(self, s):
        return s.get('subtitle') or s.get('line') or ''

    def scene_of(self, s=None):
        """(region, year) a box is drawn from: its own, else the big map's."""
        s = s or {}
        return s.get('region', self.map['region']), s.get('year', self.map.get('year'))

    def ref(self, region, year):
        return f'{region}:{year}' if year is not None else region

    def svg(self, region, year, fine=False):
        n = f'{region}-{year}' if year is not None else region
        return os.path.join(self.dir, 'scenes', n + ('-fine' if fine else '') + '.svg')

    def key_items(self):
        k = self.cfg.get('key')
        if not k: return []
        items = json.load(open(os.path.join(ROOT, k['from'])))[k['list']] if 'from' in k else k['items']
        return [i[k.get('name', 'name')] if isinstance(i, dict) else i for i in items]


# ---- step 1: scenes and where the boxes fall in them ------------------------------------------

def prepare(S):
    os.makedirs(os.path.join(S.dir, 'scenes'), exist_ok=True)
    scenes = {S.scene_of()} | {S.scene_of(s) for s in S.boxes}
    fine = S.cfg.get('fine')
    for region, year in sorted(scenes, key=str):
        for is_fine in ([False, True] if fine else [False]):
            with tempfile.TemporaryDirectory() as t:
                cmd = ['node', 'bin/isoscape.js', 'build', region, '--no-archive', '--out', t] + \
                      (['--year', str(year)] if year is not None else []) + (fine if is_fine else [])
                subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
                src = os.path.join(t, (f'{region}-{year}' if year is not None else region) + '.svg')
                shutil.move(src, S.svg(region, year, is_fine))
            print('scene', os.path.basename(S.svg(region, year, is_fine)))
    pts = {'map': {}, 'box': {}}
    for which in ('map', 'box'):
        groups = {}
        for s in S.boxes: groups.setdefault(S.scene_of() if which == 'map' else S.scene_of(s), []).append(s)
        for (region, year), ss in groups.items():
            args = [f"{s['at'][0]},{s['at'][1]}" for s in ss]
            r = subprocess.run(['node', 'bin/isoscape.js', 'locate', region] + (['--year', str(year)] if year is not None else []) + ['--', *args],
                               cwd=ROOT, capture_output=True, text=True, check=True)
            for s, p in zip(ss, json.loads(r.stdout)): pts[which][s['id']] = [p['x'], p['y']]
    json.dump(pts, open(os.path.join(S.dir, 'points.json'), 'w'), indent=1)
    print('points', len(pts['box']))


# ---- step 2: drawing --------------------------------------------------------------------------

class Scene:
    """One built SVG: its viewBox, and windows of it rendered to pixels."""

    def __init__(self, path, region, labels=True):
        src = open(path, encoding='utf-8').read()
        self.src = re.sub(r'<g class="caption".*?</g>', '', src, flags=re.S)
        # Map labels name the lines on the big map; a close view of one place goes without them.
        if not labels: self.src = re.sub(r'<g class="labels".*?</g>', '', self.src, flags=re.S)
        self.vb = list(map(float, re.search(r'viewBox="([^"]+)"', self.src).group(1).split()))
        self.scale = json.load(open(os.path.join(ROOT, 'regions', f'{region}.json')))['scale']
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

    def window(self, centre, ground_w, aspect):
        """A window `ground_w` meters across, centered on an SVG point, kept on the plate."""
        cx0, cy0, cw, ch = self.content()
        w = ground_w * self.scale
        h = w / aspect
        x = min(max(centre[0] - w / 2, cx0), cx0 + cw - w)
        y = min(max(centre[1] - h / 2, cy0), cy0 + ch - h)
        return (x, y, w, h)


class Scenes:
    def __init__(self, S):
        self.S, self.cache = S, {}

    def get(self, s=None, fine=False):
        region, year = self.S.scene_of(s)
        fine = fine and bool(self.S.cfg.get('fine'))
        k = (region, year, fine)
        if k not in self.cache: self.cache[k] = Scene(self.S.svg(region, year, fine), region, labels=not fine)
        return self.cache[k]


def wrap(d, text, f, max_w):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= max_w: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def marker(d, x, y, n, r):
    d.ellipse((x - r, y - r, x + r, y + r), fill=PAPER, outline=ACCENT, width=max(2, round(r * 0.18)))
    f = font('bold', r * 1.1)
    t = str(n)
    d.text((x - d.textlength(t, font=f) / 2, y - r * 0.6), t, font=f, fill=INK)


def credit_lines(d, text, x, y, w, size):
    f = font('regular', size)
    for ln in wrap(d, text, f, w):
        d.text((x, y), ln, font=f, fill=DIM); y += size * 1.4
    return y


def paste_map(img, d, S, scene, pts, box, x, y, w, h, r):
    """The scene's window `box` drawn into (x, y, w, h), with a numbered marker at each box."""
    img.paste(scene.render(box, round(w), round(h)), (round(x), round(y)))
    k = w / box[2]
    for s in S.boxes:
        px, py = pts['map'][s['id']]
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


def frame_order(n):
    """Cells around a 5 x 4 grid, clockwise from the top left, for up to 14 boxes."""
    ring = [(c, 0) for c in range(5)] + [(4, 1), (4, 2)] + [(c, 3) for c in range(4, -1, -1)] + [(0, 2), (0, 1)]
    if n > len(ring): raise SystemExit(f'a menu frames at most {len(ring)} boxes; this set has {n}')
    return ring[:n]


def compose_menu(dpi, S, sc, pts):
    I = lambda v: v * dpi
    W, H = round(I(32)), round(I(24))
    m, g, head, foot = I(0.75), I(0.26), I(1.35), I(0.5)
    cw = (W - 2 * m - 4 * g) / 5
    ch = (H - 2 * m - head - foot - 3 * g) / 4
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.text((m, m - I(0.05)), S.cfg['title'], font=font('bold', I(0.5)), fill=INK)
    d.text((m, m + I(0.64)), S.cfg.get('subtitle', ''), font=font('italic', I(0.19)), fill=DIM)
    rule = m + head - I(0.22)
    d.line((m, rule, W - m, rule), fill=INK, width=max(1, round(I(0.012))))
    # The key (up to sixteen names, four columns of four) at the right of the title band.
    kx, kw = W - m - I(15.2), I(15.2)
    nf = font('regular', I(0.135))
    for i, name in enumerate(S.key_items()[:16]):
        x, y = kx + (i // 4) * kw / 4, m + (i % 4) * I(0.255)
        d.line((x, y + I(0.085), x + I(0.28), y + I(0.085)), fill=ACCENT, width=max(2, round(I(0.06))))
        d.text((x + I(0.38), y), name, font=nf, fill=INK)
    top = m + head
    cell = lambda c, r: (m + c * (cw + g), top + r * (ch + g))
    ih = cw / BOX_ASPECT
    for s, (c, r) in zip(S.boxes, frame_order(len(S.boxes))):
        x, y = cell(c, r)
        # A set whose big map is drawn bolder than life (wide track, big cars) can draw its menu
        # boxes from the fine scenes too: `"fine_menu": true`.
        scene = sc.get(s, fine=bool(S.cfg.get('fine_menu')))
        img.paste(scene.render(scene.window(pts['box'][s['id']], s.get('ground', S.ground['menu']), BOX_ASPECT), round(cw), round(ih)), (round(x), round(y)))
        d.rectangle((x, y, x + cw, y + ih), outline=INK, width=max(1, round(I(0.01))))
        box_text(d, S, s, x, y + ih + I(0.1), cw, ch - ih - I(0.1), dpi)
    mx, my = cell(1, 1)
    mw, mh = 3 * cw + 2 * g, 2 * ch + g
    big = sc.get()
    paste_map(img, d, S, big, pts, map_box(big, mw / mh), mx, my, mw, mh, I(0.12))
    d.rectangle((mx, my, mx + mw, my + mh), outline=INK, width=max(1, round(I(0.01))))
    credit_lines(d, S.cfg.get('note', '') + '  ' + S.cfg['credit'], m, H - m - foot + I(0.12), W - 2 * m, I(0.085))
    return img


def box_text(d, S, s, x, y, w, h, dpi):
    """Number, title, subtitle and note under a menu box."""
    I = lambda v: v * dpi
    r = I(0.13)
    marker(d, x + r, y + r, s['n'], r)
    d.text((x + 2 * r + I(0.08), y - I(0.01)), s['title'], font=font('bold', I(0.17)), fill=INK)
    d.text((x, y + 2 * r + I(0.04)), S.sub(s), font=font('italic', I(0.105)), fill=ACCENT)
    nf = font('regular', I(0.104))
    ny, lh = y + 2 * r + I(0.24), I(0.104) * 1.45
    for ln in wrap(d, s['note'], nf, w):
        if ny + lh > y + h + I(0.02): break
        d.text((x, ny), ln, font=nf, fill=INK); ny += lh


def compose_map(dpi, S, sc, pts):
    I = lambda v: v * dpi
    W, H = round(I(36)), round(I(24))
    m, band = I(0.75), I(1.75)
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mw, mh = W - 2 * m, H - 2 * m - band
    big = sc.get()
    paste_map(img, d, S, big, pts, map_box(big, mw / mh), m, m, mw, mh, I(0.13))
    d.rectangle((m, m, m + mw, m + mh), outline=INK, width=max(1, round(I(0.01))))
    by = m + mh + I(0.3)
    d.text((m, by), S.cfg['title'], font=font('bold', I(0.48)), fill=INK)
    d.text((m, by + I(0.63)), S.cfg.get('subtitle', ''), font=font('italic', I(0.19)), fill=DIM)
    nb = ' '
    names = '   '.join(str(s['n']) + nb + s['title'].replace(' ', nb) for s in S.boxes)
    kf = font('regular', I(0.15))
    ky = by + I(0.98)
    for ln in wrap(d, names, kf, mw):
        d.text((m, ky), ln, font=kf, fill=INK); ky += I(0.15) * 1.4
    credit_lines(d, S.cfg.get('note', '') + '  ' + S.cfg['credit'], m, H - m + I(0.12), mw, I(0.075))
    return img


def compose_box(dpi, S, sc, s, pt):
    I = lambda v: v * dpi
    W, H = round(I(24)), round(I(18))
    m = I(0.75)
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    iw, ih = W - 2 * m, I(12.6)
    scene = sc.get(s, fine=True)
    img.paste(scene.render(scene.window(pt, s.get('ground', S.ground['box']), iw / ih), round(iw), round(ih)), (round(m), round(m)))
    d.rectangle((m, m, m + iw, m + ih), outline=INK, width=max(1, round(I(0.01))))
    ty = m + ih + I(0.35)
    r = I(0.3)
    marker(d, m + r, ty + r, s['n'], r)
    tx = m + 2 * r + I(0.22)
    d.text((tx, ty - I(0.04)), s['title'], font=font('bold', I(0.5)), fill=INK)
    d.text((tx, ty + I(0.66)), f"{S.sub(s)}  ·  {S.cfg.get('box_label', S.cfg['title'])}", font=font('italic', I(0.2)), fill=ACCENT)
    nf = font('regular', I(0.235))
    ny = ty + I(1.2)
    for ln in wrap(d, s['note'], nf, iw * 0.8):
        d.text((m, ny), ln, font=nf, fill=INK); ny += I(0.235) * 1.5
    credit_lines(d, S.cfg['credit'], m, H - I(0.55), iw, I(0.075))
    return img


def save(img, out_dir, name, dpi):
    os.makedirs(out_dir, exist_ok=True)
    w_in, h_in = round(img.size[0] / dpi), round(img.size[1] / dpi)
    p = os.path.join(out_dir, f'{name}_{w_in}x{h_in}.jpg')
    for q in (94, 90, 86, 82, 78):
        img.save(p, quality=q, dpi=(dpi, dpi), optimize=True)
        if os.path.getsize(p) <= MAX_BYTES: break
    print(p, img.size, f'{os.path.getsize(p) / 1e6:.1f} MB q{q}')


def write_canvas(S, print_dir):
    """Framed-canvas files beside each print: each face size the store sells, plus 1.5 in of
    mirrored wrap per side, at 300 dpi (Printful's canvas print files)."""
    out = os.path.join(print_dir, 'canvas')
    os.makedirs(out, exist_ok=True)
    pat = re.compile(rf'({re.escape(S.cfg["slug"])}-(menu|map|\d\d-[a-z0-9-]+))_\d+x\d+\.jpg$')
    for f in sorted(os.listdir(print_dir)):
        m = pat.match(f)
        if not m: continue
        kind = m.group(2) if m.group(2) in ('menu', 'map') else 'box'
        base = Image.open(os.path.join(print_dir, f)).convert('RGB')
        wrap_px = int(WRAP * CANVAS_DPI)
        for fw, fh in CANVAS[kind]:
            face = np.asarray(base.resize((fw * CANVAS_DPI, fh * CANVAS_DPI), Image.LANCZOS))
            img = Image.fromarray(np.pad(face, ((wrap_px, wrap_px), (wrap_px, wrap_px), (0, 0)), mode='symmetric'))
            p = os.path.join(out, f'{m.group(1)}_canvas-{fw}x{fh}.jpg')
            for q in (92, 88, 84, 80, 76):
                img.save(p, quality=q, dpi=(CANVAS_DPI, CANVAS_DPI), optimize=True)
                if os.path.getsize(p) <= MAX_BYTES: break
            print(os.path.basename(p), img.size, f'{os.path.getsize(p) / 1e6:.1f} MB')


def write_page(S, pts):
    """pages/<slug>.md, from the same boxes and sources as the prints. Its images, <slug>-menu.jpg
    and <slug>-social.jpg, are made from the menu print beside it."""
    P = S.cfg['page']
    slug = P['slug']
    region, year = S.scene_of()
    ref = S.ref(region, year)
    out = ['---', f"title: {P['title']}", f"order: {P.get('order', 50)}", f"summary: {P['summary']}",
           f'social: {slug}-social.jpg', '---', '', f"# {P['title']}", '', P['intro'], '',
           f"![{P.get('image_alt', P['title'])}]({slug}-menu.jpg)", '',
           f"[Open the map]({SITE}#{ref}) to pan and zoom, or jump to a {P.get('noun', 'place')} below." +
           (f" Prints of the whole set, the map alone and each {P.get('noun', 'place')} are in the [shop]({P['shop']})." if P.get('shop') else ''),
           '', f"## {P.get('boxes_heading', 'The places')}", '']
    for s in S.boxes:
        x, y = pts['box'][s['id']]
        bref = S.ref(*S.scene_of(s))
        out += [f"### {s['n']}. {s['title']}", '', f'*{S.sub(s)}*', '', s['note'], '',
                f"[See it on the map]({SITE}#{bref}@{x:.0f},{y:.0f},6) · Sources: " +
                ' '.join(f'[{k + 1}]({u})' for k, u in enumerate(s['sources'])), '']
    t = P.get('table')
    if t:
        rows = json.load(open(os.path.join(ROOT, t['from'])))[t['list']]
        out += [f"## {t['heading']}", '', t.get('intro', ''), '',
                '| ' + ' | '.join(c[0] for c in t['columns']) + ' |', '|' + '---|' * len(t['columns'])]
        for r in rows:
            out.append('| ' + ' | '.join(c[1].format(**r) if '{' in c[1] else str(r[c[1]]) for c in t['columns']) + ' |')
        out.append('')
    out += ['## How it was drawn', '', P['how'], '', "More in [How it's made](how-its-made.md#time).", '']
    open(os.path.join(ROOT, 'pages', f'{slug}.md'), 'w').write('\n'.join(out))
    menu = os.path.join(S.dir, 'print', f"{S.cfg['slug']}-menu_32x24.jpg")
    if os.path.exists(menu):
        im = Image.open(menu)
        im.resize((1800, 1350), Image.LANCZOS).save(os.path.join(ROOT, 'pages', f'{slug}-menu.jpg'), quality=84, optimize=True)
        w = im.size[0]
        im.crop((0, 0, w, round(w / 1.905))).resize((1200, 630), Image.LANCZOS).save(os.path.join(ROOT, 'pages', f'{slug}-social.jpg'), quality=86, optimize=True)
    print(f'pages/{slug}.md')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('set')
    ap.add_argument('what', choices=['prepare', 'menu', 'map', 'boxes', 'canvas', 'page'])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--dpi', type=int, default=300)
    ap.add_argument('--dir')
    a = ap.parse_args()
    S = Set(a.set, a.dir)
    if a.what == 'prepare': return prepare(S)
    pts = json.load(open(os.path.join(S.dir, 'points.json')))
    out = os.path.join(S.dir, 'print' if a.dpi >= 300 else f'proof-{a.dpi}')
    slug = S.cfg['slug']
    if a.what == 'canvas': return write_canvas(S, os.path.join(S.dir, 'print'))
    if a.what == 'page': return write_page(S, pts)
    sc = Scenes(S)
    if a.what == 'menu': save(compose_menu(a.dpi, S, sc, pts), out, f'{slug}-menu', a.dpi)
    elif a.what == 'map': save(compose_map(a.dpi, S, sc, pts), out, f'{slug}-map', a.dpi)
    else:
        for s in S.boxes:
            if a.ids and s['id'] not in a.ids: continue
            save(compose_box(a.dpi, S, sc, s, pts['box'][s['id']]), out, f"{slug}-{s['n']:02d}-{s['id']}", a.dpi)


if __name__ == '__main__':
    main()
