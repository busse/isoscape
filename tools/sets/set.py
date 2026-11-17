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
        # The plate's front face (the slab, and the water in its cut) is drawn between the sky's
        # rectangle and the ground: measured without it, the drawn plate is the ground alone, so
        # no window or map frame takes in the tan band below the ground's front edge.
        self.ground_src = re.sub(r'(<rect [^\n]*/>\n)(?:<path (?:class="i" )?fill="[^"]+" d="[^"]*"/>\n)+(?=<defs><clipPath id="above">)', r'\1', self.src, count=1)
        self._content = None

    def render(self, box, w, h, src=None):
        """The window `box` (x, y, w, h in SVG units) at w x h px."""
        x, y, bw, bh = box
        svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{x:.2f} {y:.2f} {bw:.2f} {bh:.2f}"', src or self.src, count=1)
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
            a = np.asarray(self.render(self.vb, w, h, self.ground_src)).astype(int)
            bg = np.array(Image.new('RGB', (1, 1), PAPER).getpixel((0, 0)))
            ys, xs = np.where(np.abs(a - bg).sum(-1) > 12)
            k = self.vb[2] / w
            self._content = (self.vb[0] + xs.min() * k, self.vb[1] + ys.min() * k,
                             (xs.max() - xs.min() + 1) * k, (ys.max() - ys.min() + 1) * k)
        return self._content

    def covered(self):
        """The part of the plate drawn edge to edge (SVG units): rows and columns where the drawing
        reaches, so a window kept inside it shows no paper at the plate's edges. Something drawn
        past the ground's edge (a bridge cut at the edge) does not widen it, and the slab's side is
        not counted at all (see ground_src)."""
        if getattr(self, '_covered', None) is None:
            w = 3200
            h = round(w * self.vb[3] / self.vb[2])
            a = np.asarray(self.render(self.vb, w, h, self.ground_src)).astype(int)
            bg = np.array(Image.new('RGB', (1, 1), PAPER).getpixel((0, 0)))
            ink = np.abs(a - bg).sum(-1) > 3
            # Rows nearly all drawn give the sides; within the sides, the columns give the top
            # and bottom; then the sides again over the rows between those, until it settles.
            rows = np.where(ink.mean(1) > 0.9)[0]
            y0, y1 = rows.min(), rows.max()
            x0, x1 = 0, ink.shape[1] - 1
            for _ in range(6):
                band = ink[y0:y1 + 1]
                full = [r for r in band if r.mean() > 0.9]
                nx0 = max(r.argmax() for r in full)
                nx1 = min(len(r) - 1 - r[::-1].argmax() for r in full)
                cols = ink[:, nx0:nx1 + 1].T
                ny0 = max(c.argmax() for c in cols)
                ny1 = min(len(c) - 1 - c[::-1].argmax() for c in cols)
                if (nx0, nx1, ny0, ny1) == (x0, x1, y0, y1): break
                x0, x1, y0, y1 = nx0, nx1, ny0, ny1
            k = self.vb[2] / w
            self._covered = (self.vb[0] + (x0 + 1) * k, self.vb[1] + (y0 + 1) * k, (x1 - x0 - 1) * k, (y1 - y0 - 1) * k)
        return self._covered

    def window(self, centre, ground_w, aspect):
        """A window `ground_w` meters across, centered on an SVG point, kept on the plate. A window
        larger than the plate drawn edge to edge is made smaller to fit, never let past its edge."""
        cx0, cy0, cw, ch = self.covered()
        w = min(ground_w * self.scale, cw, ch * aspect)
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


# Every line of text prints at MIN_PT or more at the smallest size each product is sold at: a
# 24 x 18 stop print is also sold at 16 x 12, the 32 x 24 sheet at 24 x 18, the 36 x 24 map at
# 18 x 12 (CANVAS). SMALLEST is that size as a share of the file's.
MIN_PT = C.CREDIT_MIN_PT
SMALLEST = {kind: min(max(f) for f in faces) / max(faces[-1]) for kind, faces in CANVAS.items()}


def least(kind, dpi):
    """The least type size (px, the font's em) a product's text may have."""
    return dpi * MIN_PT / 72 / SMALLEST[kind]


def corner(kind, dpi):
    """(w, h) px kept clear at the bottom right for the title block stamped later (stamp.py), as
    large as it comes on any face cut from the file (a canvas face's block is relatively larger)."""
    import titleblock
    long_in = max(CANVAS[kind][-1])
    faces = [long_in] + [max(f) for f in CANVAS[kind]]
    u = max(round(1.3 * (f / 36) ** 0.5 * dpi / 300, 4) * long_in / f for f in faces)
    return C.block_reserve(long_in, dpi, 1.0, faces), titleblock.H * u * 1.45


def wrap(d, text, f, max_w):
    """Words wrapped to max_w, the lines as even as they can be: no word left alone on a line."""
    return C.balanced(d, text, f, max_w) if text.strip() else []


def foot_lines(d, S, f, fi, max_w):
    """The note (what is approximate), the ground note (in italics) and the credit, wrapped to
    max_w: the credit breaks only between its parts where it can."""
    out = [(ln, f) for ln in wrap(d, S.cfg.get('note', ''), f, max_w)]
    out += [(ln, fi) for ln in wrap(d, S.cfg.get('ground_note', ''), fi, max_w)]
    for ln in C.wrap(d, S.cfg['credit'], f, max_w):
        out += [(x, f) for x in (wrap(d, ln, f, max_w) if d.textlength(ln, font=f) > max_w else [ln])]
    return out


def marker(d, x, y, n, r, least_px=0):
    """A numbered ring. Two digits are set smaller to sit inside it, the ring grown if the
    number would otherwise print under the least size."""
    t = str(n)
    share = 1.1 if len(t) == 1 else 0.82
    r = max(r, least_px / share)
    d.ellipse((x - r, y - r, x + r, y + r), fill=PAPER, outline=ACCENT, width=max(2, round(r * 0.18)))
    f = font('bold', r * share)
    l, t0, rr, b0 = d.textbbox((0, 0), t, font=f)
    d.text((x - (l + rr) / 2, y - (t0 + b0) / 2), t, font=f, fill=INK)
    return r


def spread(points, r, gap=1.15, rounds=200):
    """Marker centers moved apart so no two rings overlap: each pair closer than 2r·gap is pushed
    apart along the line between them, a little each round."""
    pts = [list(p) for p in points]
    need = 2 * r * gap
    for _ in range(rounds):
        moved = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx, dy = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
                dd = (dx * dx + dy * dy) ** 0.5
                if dd >= need: continue
                if dd < 1e-6: dx, dy, dd = 1.0, 0.0, 1.0
                push = (need - dd) / 2 + 0.5
                pts[i][0] -= dx / dd * push; pts[i][1] -= dy / dd * push
                pts[j][0] += dx / dd * push; pts[j][1] += dy / dd * push
                moved = True
        if not moved: break
    return pts


def paste_map(img, d, S, scene, pts, box, x, y, w, h, r, least_px=0):
    """The scene's window `box` drawn into (x, y, w, h), with a numbered marker at each box.
    Markers that would overlap are moved apart, each with a leader to its place."""
    img.paste(scene.render(box, round(w), round(h)), (round(x), round(y)))
    k = w / box[2]
    share = 0.82 if any(s['n'] >= 10 for s in S.boxes) else 1.1
    r = max(r, least_px / share)
    places = []
    for s in S.boxes:
        px, py = pts['map'][s['id']]
        if not (box[0] <= px <= box[0] + box[2] and box[1] <= py <= box[1] + box[3]):
            raise SystemExit(f"stop {s['n']} ({s['id']}) falls outside the big map")
        places.append((s, x + (px - box[0]) * k, y + (py - box[1]) * k))
    # A box may set its marker off its place (`badge`: [dx, dy] in marker radii, screen
    # directions), with a leader back to it, so the markers do not hide what they name.
    moved = spread([(px + s.get('badge', [0, 0])[0] * r, py + s.get('badge', [0, 0])[1] * r) for s, px, py in places], r)
    # Kept inside the frame.
    moved = [(min(max(mx, x + r * 1.2), x + w - r * 1.2), min(max(my, y + r * 1.2), y + h - r * 1.2)) for mx, my in moved]
    for (s, px, py), (mx, my) in zip(places, moved):
        if abs(mx - px) + abs(my - py) > r * 0.3:
            d.line((px, py, mx, my), fill=ACCENT, width=max(2, round(r * 0.14)))
            d.ellipse((px - r * 0.18, py - r * 0.18, px + r * 0.18, py + r * 0.18), fill=ACCENT)
    for (s, _, _), (mx, my) in zip(places, moved):
        marker(d, mx, my, s['n'], r)


def map_box(scene, aspect, marks=(), top_share=0.55, pad=0.03):
    """The plate drawn edge to edge (no paper, no slab) cut to `aspect`, trimming top and bottom
    (or the sides) as needed: by `top_share` of the cut from the top, moved if that would leave a
    stop's marker (`marks`, SVG points) outside or within `pad` of the edge."""
    x, y, w, h = scene.covered()
    if w / h < aspect:
        nh = w / aspect
        ny = y + (h - nh) * top_share
        if marks:
            lo, hi = min(p[1] for p in marks), max(p[1] for p in marks)
            # As much room around the outermost markers as the cut allows, up to `pad` of it.
            room = min(nh * pad, max(0.0, (nh - (hi - lo)) / 2))
            lo, hi = lo - room, hi + room
            ny = min(max(ny, hi - nh), lo)
            ny = min(max(ny, y), y + h - nh)
        return (x, ny, w, nh)
    nw = h * aspect
    nx = x + (w - nw) / 2
    if marks:
        lo, hi = min(p[0] for p in marks), max(p[0] for p in marks)
        room = min(nw * pad, max(0.0, (nw - (hi - lo)) / 2))
        lo, hi = lo - room, hi + room
        nx = min(max(nx, hi - nw), lo)
        nx = min(max(nx, x), x + w - nw)
    return (nx, y, nw, h)


def frame_order(n):
    """Cells around a 5 x 4 grid, clockwise from the top left, for up to 14 boxes."""
    ring = [(c, 0) for c in range(5)] + [(4, 1), (4, 2)] + [(c, 3) for c in range(4, -1, -1)] + [(0, 2), (0, 1)]
    if n > len(ring): raise SystemExit(f'a menu frames at most {len(ring)} boxes; this set has {n}')
    return ring[:n]


# Menu type, inches at 32 x 24 (each at least least('menu')): box titles, subtitles, notes.
MENU_TYPE = {'title': 0.17, 'sub': 0.135, 'note': 0.135, 'foot': 0.13}


def menu_layout(dpi, foot_in=0.5):
    """The menu's grid at `dpi`: sheet size, margin, gutter, title band, foot, cell size, and the
    big map's box (the middle three by two cells)."""
    I = lambda v: v * dpi
    W, H = round(I(32)), round(I(24))
    m, g, head, foot = I(0.75), I(0.26), I(1.35), I(foot_in)
    cw = (W - 2 * m - 4 * g) / 5
    ch = (H - 2 * m - head - foot - 3 * g) / 4
    top = m + head
    mx, my = m + (cw + g), top + (ch + g)
    return {'W': W, 'H': H, 'm': m, 'g': g, 'head': head, 'foot': foot, 'cw': cw, 'ch': ch, 'top': top,
            'map': (mx, my, 3 * cw + 2 * g, 2 * ch + g)}


def menu_foot(S, dpi):
    """The menu's foot lines and its height in inches."""
    I = lambda v: v * dpi
    size = max(I(MENU_TYPE['foot']), least('menu', dpi))
    d = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    rw, _ = corner('menu', dpi)
    lines = foot_lines(d, S, font('regular', size), font('italic', size), I(32) - 2 * I(0.75))
    return lines, size, (len(lines) * size * 1.4 + I(0.12)) / dpi


def compose_menu(dpi, S, sc, pts):
    I = lambda v: v * dpi
    lines, fsize, foot_in = menu_foot(S, dpi)
    L = menu_layout(dpi, foot_in)
    W, H, m, g, head, foot, cw, ch = (L[k] for k in ('W', 'H', 'm', 'g', 'head', 'foot', 'cw', 'ch'))
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.text((m, m - I(0.05)), S.cfg['title'], font=font('bold', I(0.5)), fill=INK)
    d.text((m, m + I(0.64)), S.cfg.get('subtitle', ''), font=font('italic', I(0.19)), fill=DIM)
    rule = m + head - I(0.22)
    d.line((m, rule, W - m, rule), fill=INK, width=max(1, round(I(0.012))))
    # The key: up to sixteen names in four columns at the right of the title band. Every line is
    # drawn in one color, so the key is a plain list of names, without swatches that could not
    # tell one line from another.
    items = S.key_items()[:16]
    if items:
        nf = font('regular', max(I(0.135), least('menu', dpi)))
        hf = font('italic', max(I(0.135), least('menu', dpi)))
        cols = 4
        colw = [max(d.textlength(n, font=nf) for n in items[c * 4:(c + 1) * 4]) for c in range((len(items) + 3) // 4)]
        kx = W - m - sum(colw) - I(0.35) * (len(colw) - 1)
        d.text((kx - I(0.25) - d.textlength(S.cfg.get('key_heading', 'The lines:'), font=hf), m), S.cfg.get('key_heading', 'The lines:'), font=hf, fill=ACCENT)
        x = kx
        for c, cwid in enumerate(colw):
            for i, name in enumerate(items[c * 4:(c + 1) * 4]):
                d.text((x, m + i * I(0.24)), name, font=nf, fill=INK)
            x += cwid + I(0.35)
    top = m + head
    cell = lambda c, r: (m + c * (cw + g), top + r * (ch + g))
    # Each picture is as tall as the longest note leaves room for, no taller than BOX_ASPECT.
    ih = min(cw / BOX_ASPECT, ch - I(0.1) - max(box_text_height(d, S, s, cw, dpi) for s in S.boxes))
    aspect = cw / ih
    for s, (c, r) in zip(S.boxes, frame_order(len(S.boxes))):
        x, y = cell(c, r)
        # A set whose big map is drawn bolder than life (wide track, big cars) can draw its menu
        # boxes from the fine scenes too: `"fine_menu": true`.
        scene = sc.get(s, fine=bool(S.cfg.get('fine_menu')))
        img.paste(scene.render(scene.window(pts['box'][s['id']], s.get('ground', S.ground['menu']), aspect), round(cw), round(ih)), (round(x), round(y)))
        d.rectangle((x, y, x + cw, y + ih), outline=INK, width=max(1, round(I(0.01))))
        box_text(d, S, s, x, y + ih + I(0.1), cw, ch - ih - I(0.1), dpi)
    mx, my, mw, mh = L['map']
    big = sc.get()
    paste_map(img, d, S, big, pts, map_box(big, mw / mh, list(pts['map'].values())), mx, my, mw, mh, I(0.12), least('menu', dpi))
    d.rectangle((mx, my, mx + mw, my + mh), outline=INK, width=max(1, round(I(0.01))))
    y = H - m - foot + I(0.1)
    for ln, f in lines:
        d.text((m, y), ln, font=f, fill=DIM); y += fsize * 1.4
    return img


def box_text_height(d, S, s, w, dpi):
    """Room (px) the number, title, subtitle and note of a menu box need under its picture."""
    I = lambda v: v * dpi
    lp = least('menu', dpi)
    r = max(I(0.15), lp / 0.82)
    sz, ns = max(I(MENU_TYPE['sub']), lp), max(I(MENU_TYPE['note']), lp)
    n = len(wrap(d, s['note'], font('regular', ns), w))
    return 2 * r + I(0.06) + sz * 1.45 + ns * 1.42 * (n - 1) + ns * 1.15


def box_text(d, S, s, x, y, w, h, dpi):
    """Number, title, subtitle and note under a menu box. A note that does not fit is an error."""
    I = lambda v: v * dpi
    lp = least('menu', dpi)
    r = marker(d, x + I(0.15), y + I(0.15), s['n'], I(0.15), lp)
    d.text((x + 2 * r + I(0.08), y - I(0.01)), s['title'], font=font('bold', I(MENU_TYPE['title'])), fill=INK)
    sz = max(I(MENU_TYPE['sub']), lp)
    d.text((x, y + 2 * r + I(0.04)), S.sub(s), font=font('italic', sz), fill=ACCENT)
    ns = max(I(MENU_TYPE['note']), lp)
    nf = font('regular', ns)
    ny, lh = y + 2 * r + I(0.06) + sz * 1.45, ns * 1.42
    lines = wrap(d, s['note'], nf, w)
    if ny + lh * (len(lines) - 1) + ns * 1.15 > y + h + I(0.02):
        raise SystemExit(f"box {s['n']} ({s['id']}): its note needs {len(lines)} lines and does not fit under its picture")
    for ln in lines:
        d.text((x, ny), ln, font=nf, fill=INK); ny += lh


def stop_list(d, S, kf, nf, max_w):
    """The stops as entries 'n Title', the number in bold, wrapped between entries only."""
    gap = d.textlength('\u2003\u2003', font=kf)
    rows, cur, cw = [], [], 0
    for s in S.boxes:
        num, name = str(s['n']), s['title']
        ew = d.textlength(num + ' ', font=nf) + d.textlength(name, font=kf)
        if cur and cw + gap + ew > max_w:
            rows.append(cur); cur, cw = [], 0
        cur.append((num, name)); cw += (gap if len(cur) > 1 else 0) + ew
    if cur: rows.append(cur)
    return rows, gap


def compose_map(dpi, S, sc, pts):
    I = lambda v: v * dpi
    W, H = round(I(36)), round(I(24))
    m = I(0.75)
    lp = least('map', dpi)
    rw, rh = corner('map', dpi)
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    ks = max(I(0.2), lp)
    kf, knf = font('regular', ks), font('bold', ks)
    rows, gap = stop_list(d0, S, kf, knf, W - 2 * m - rw)
    fs = lp
    foot = foot_lines(d0, S, font('regular', fs), font('italic', fs), W - 2 * m - rw)
    sub_s = max(I(0.19), lp)
    band = I(0.3) + I(0.63) + sub_s * 1.5 + I(0.12) + len(rows) * ks * 1.45 + I(0.12) + len(foot) * fs * 1.4
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mw, mh = W - 2 * m, H - 2 * m - band
    big = sc.get()
    paste_map(img, d, S, big, pts, map_box(big, mw / mh, list(pts['map'].values())), m, m, mw, mh, I(0.13), lp)
    d.rectangle((m, m, m + mw, m + mh), outline=INK, width=max(1, round(I(0.01))))
    by = m + mh + I(0.3)
    d.text((m, by), S.cfg['title'], font=font('bold', I(0.48)), fill=INK)
    d.text((m, by + I(0.63)), S.cfg.get('subtitle', ''), font=font('italic', sub_s), fill=DIM)
    ky = by + I(0.63) + sub_s * 1.5 + I(0.12)
    for row in rows:
        x = m
        for num, name in row:
            d.text((x, ky), num + ' ', font=knf, fill=ACCENT); x += d.textlength(num + ' ', font=knf)
            d.text((x, ky), name, font=kf, fill=INK); x += d.textlength(name, font=kf) + gap
        ky += ks * 1.45
    ky += I(0.12)
    for ln, f in foot:
        d.text((m, ky), ln, font=f, fill=DIM); ky += fs * 1.4
    if ky > H - I(0.2): raise SystemExit('the map band runs off the sheet')
    return img


def compose_box(dpi, S, sc, s, pt):
    I = lambda v: v * dpi
    W, H = round(I(24)), round(I(18))
    m = I(0.75)
    lp = least('box', dpi)
    rw, rh = corner('box', dpi)
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
    for ln in wrap(d, s['note'], nf, min(iw * 0.8, iw - rw)):
        d.text((m, ny), ln, font=nf, fill=INK); ny += I(0.235) * 1.5
    # The credit and the ground note, set at the least size, bottom-aligned, clear of the corner.
    f, fi = font('regular', lp), font('italic', lp)
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = [(ln, fi) for ln in wrap(d0, S.cfg.get('ground_note', ''), fi, iw - rw)]
    for ln in C.wrap(d0, S.cfg['credit'], f, iw - rw):
        lines += [(x, f) for x in (wrap(d0, ln, f, iw - rw) if d0.textlength(ln, font=f) > iw - rw else [ln])]
    cy = H - I(0.45) - len(lines) * lp * 1.4
    if cy < ny + I(0.1): raise SystemExit(f"box {s['n']} ({s['id']}): its note runs into the credit")
    for ln, ff in lines:
        d.text((m, cy), ln, font=ff, fill=DIM); cy += lp * 1.4
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


def social(menu, dest):
    """A set's link preview, 1200 x 630, from its menu print: the big map whole, in its frame line,
    on paper widened to 1.91:1 (the map is a little narrower). Trimming it instead would cut
    through the markers and labels at its edges, and the whole menu is too small to read."""
    L = menu_layout(menu.size[0] / 32)
    sw, sh = C.SOCIAL
    x, y, w, h = L['map']
    pad = L['g'] / 2
    art = menu.crop((round(x - pad), round(y - pad), round(x + w + pad), round(y + h + pad)))
    cw, ch = art.size
    if cw / ch < sw / sh:
        sheet = Image.new('RGB', (round(ch * sw / sh), ch), PAPER)
        sheet.paste(art, ((sheet.size[0] - cw) // 2, 0))
    else:
        fx, fy, fw, fh = C.fit((0, 0, cw, ch), sw / sh)
        sheet = art.crop((round(fx), round(fy), round(fx + fw), round(fy + fh)))
    sheet.resize((sw, sh), Image.LANCZOS).save(dest, quality=86, optimize=True)


def write_page(S, pts):
    """pages/<slug>.md, from the same boxes and sources as the prints. Its images, <slug>-menu.jpg
    and <slug>-social.jpg (see `social`), are made from the menu print beside it."""
    P = S.cfg['page']
    slug = P['slug']
    region, year = S.scene_of()
    ref = S.ref(region, year)
    out = ['---', f"title: {P['title']}", f"order: {P.get('order', 50)}", f"summary: {P['summary']}",
           f'social: {slug}-social.jpg', '---', '', f"# {P['title']}", '', P['intro'], '',
           f"![{P.get('image_alt', P['title'])}]({slug}-menu.jpg)", '',
           # No word of the shop here: the explorer adds the page's shop button while the page's
           # slug (or its maps) are in shop.onSale in isoscape.config.json, the one list of what sells.
           f"[Open the map]({SITE}#{ref}) to pan and zoom, or jump to a {P.get('noun', 'place')} below.",
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
        social(im, os.path.join(ROOT, 'pages', f'{slug}-social.jpg'))
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
