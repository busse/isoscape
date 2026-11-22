#!/usr/bin/env python3
"""The redlining story's region views, from two builds of richmond-1937, cropped and laid out.

    node bin/isoscape.js build richmond-1937 --year 1937 --with grades --no-archive --out <work>/g1937
    node bin/isoscape.js build richmond-1937 --year 2026 --with built  --no-archive --out <work>/b2026
    python3 tools/stories/redlining/views.py --work <work> [--full DIR] [--only name,name]

Each view rasterizes a build's SVG with rsvg-convert inside a box (SVG units) by rewriting the
SVG's viewBox, so a crop is drawn at its own resolution and never cut from a huge raster. The
two years share one frame: their viewBoxes differ by a few units (taller buildings today), so
full views are drawn in the union of the two, and line up pixel for pixel for the page's
compare slider. Writes pages/redlining-<name>.webp (1600 px wide) and -large.webp (3200 px)
and, with --full, a PNG of each under 8,000 px for review.

Boxes are placed from lon/lat with the region's own projection (bearing 0: x = east meters ×
scale, y = −north meters × scale × squash), raised by a margin for the ground's height.
Colors are read from src/palette.ts, never typed here.
"""
import argparse
import json
import math
import os
import re
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


P = palette()
REG = json.load(open(os.path.join(ROOT, 'regions/richmond-1937.json')))
import sys  # noqa: E402
sys.path.insert(0, HERE)
from outlines import CREDIT, load as load_outlines  # noqa: E402  the one switch: outlines.py
from areas import NAMES, D_AREAS, slug  # noqa: E402
LEGEND = ['A "Best"', 'B "Still Desirable"', 'C "Definitely Declining"', 'D "Hazardous"']
KEY_TITLE = "The Home Owners' Loan Corporation's (HOLC's) grades, 1937, in its own words"
BASE_CREDIT = 'Map data © OpenStreetMap contributors (ODbL); elevation USGS 3DEP; drawn by Chris Busse with isoscape'


def to_svg(lon, lat):
    lon0, lat0 = REG['center']
    e = (lon - lon0) * 111320 * math.cos(math.radians(lat0))
    n = (lat - lat0) * 111132
    return e * REG['scale'], -n * REG['scale'] * REG['squash']


def box_at(lon, lat, ground_w, aspect=0.62, lift=40):
    """A box `ground_w` meters across centered on lon/lat, `aspect` high for its width, raised `lift` units."""
    x, y = to_svg(lon, lat)
    w = ground_w * REG['scale']
    h = w * aspect
    return (x - w / 2, y - h / 2 - lift, w, h)


def view_box(svg):
    with open(svg, 'rb') as fh:
        head = fh.read(600).decode('utf8', 'replace')
    return tuple(float(v) for v in re.search(r'viewBox="([^"]+)"', head).group(1).split())


def raster(svg, box, width, out):
    """`svg` drawn inside `box` (x, y, w, h), `width` px wide, on the paper's sky color."""
    with open(svg, 'rb') as fh:
        data = fh.read()
    head, rest = data[:600].decode('utf8'), data[600:]
    head = re.sub(r'viewBox="[^"]+"', 'viewBox="%.2f %.2f %.2f %.2f"' % box, head, count=1)
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False, dir=os.path.dirname(out)) as t:
        t.write(head.encode('utf8'))
        t.write(rest)
        tmp = t.name
    try:
        subprocess.run(['rsvg-convert', '-w', str(width), '-b', P['sky'], '-o', out, tmp], check=True)
    finally:
        os.remove(tmp)
    return Image.open(out).convert('RGB')


def font(size, bold=False):
    for name in (['DejaVuSerif-Bold.ttf'] if bold else ['DejaVuSerif.ttf']):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def save(img, name, full):
    pages = os.path.join(ROOT, 'pages')
    for w, suffix in ((1600, ''), (3200, '-large')):
        if img.width < w and suffix:
            continue
        im = img if img.width <= w else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        im.save(os.path.join(pages, f'redlining-{name}{suffix}.webp'), quality=82, method=6)
    if full:
        im = img if img.width < 8000 else img.resize((7900, round(img.height * 7900 / img.width)), Image.LANCZOS)
        im.save(os.path.join(full, f'redlining-{name}.png'))
    print(f'redlining-{name}: {img.width}×{img.height}')


def labeled(img, text):
    d = ImageDraw.Draw(img)
    f = font(max(28, img.width // 34), bold=True)
    d.rectangle((0, 0, img.width, f.size * 1.7), fill=P['sky'])
    d.text((f.size * 0.6, f.size * 0.3), text, fill=P['ink'], font=f)
    return img


def keyed(img, title, sub=None, extra=0):
    """`img` with a band above it: a title that says what the picture is, the four grades' key
    (swatch and the HOLC's own name for each), and a credit line below the picture, so the
    picture reads on its own wherever it is shown."""
    u = max(16, img.width // 90)
    tf, sf, kf, cf = font(round(u * 1.7), bold=True), font(round(u * 1.15)), font(round(u * 1.1)), font(round(u * 0.8))
    d0 = ImageDraw.Draw(img)
    def wrap(text, f):
        rows, cur = [], ''
        for w_ in text.split(' '):
            t = (cur + ' ' + w_).strip()
            if d0.textlength(t, font=f) > img.width - 2 * u and cur:
                rows.append(cur); cur = w_
            else:
                cur = t
        return rows + [cur]
    lines = [(r, tf) for r in wrap(title, tf)] + ([(r, sf) for r in wrap(sub, sf)] if sub else [])
    head = sum(f.size * 1.35 for _, f in lines) + u * 0.8 + extra
    key_h = kf.size * 1.6 + u * 0.6
    credit = CREDIT + '. ' + BASE_CREDIT + '.'
    words, rows, cur = credit.split(' '), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d0.textlength(t, font=cf) > img.width - 2 * u and cur:
            rows.append(cur); cur = w_
        else:
            cur = t
    rows.append(cur)
    foot = len(rows) * cf.size * 1.35 + u * 0.9
    out = Image.new('RGB', (img.width, round(head + key_h + img.height + foot)), P['sky'])
    d = ImageDraw.Draw(out)
    y = u * 0.6
    for text, f in lines:
        d.text((u, y), text, fill=P['ink'], font=f); y += f.size * 1.35
    y = head
    d.text((u, y), KEY_TITLE + ':', fill=P['ink'], font=kf)
    x = u + d.textlength(KEY_TITLE + ':  ', font=kf)
    sw = kf.size * 1.3
    if x + sum(sw * 1.4 + d.textlength(l, font=kf) + u * 1.2 for l in LEGEND) > img.width:
        y += kf.size * 1.5; x = u
        out2 = Image.new('RGB', (out.width, out.height + round(kf.size * 1.5)), P['sky']); out2.paste(out, (0, 0)); out = out2; d = ImageDraw.Draw(out)
    for tone, label in zip(P['tint']['tones'], LEGEND):
        d.rectangle((x, y + kf.size * 0.05, x + sw, y + kf.size * 1.1), fill=tone, outline=P['ink'])
        x += sw * 1.35
        d.text((x, y), label, fill=P['ink'], font=kf)
        x += d.textlength(label, font=kf) + u * 1.2
    top = round(y + key_h - u * 0.2)
    out = out.crop((0, 0, out.width, top + img.height + round(foot)))
    d = ImageDraw.Draw(out)
    out.paste(img, (0, top))
    d.rectangle((0, top, img.width - 1, top + img.height - 1), outline=P['ink'], width=max(1, u // 10))
    y = top + img.height + u * 0.45
    for r in rows:
        d.text((u, y), r, fill=P['ink'], font=cf); y += cf.size * 1.35
    return out


def area_box(label, margin=1.18, aspect=0.62, min_ground=1100):
    """A view box that holds one graded area whole: its bounds, a margin, at least `min_ground` m."""
    from shapely.geometry import shape
    g = [f for f in load_outlines(ROOT)['features'] if (f['properties'].get('label') or '').strip() == label][0]
    x0, y0, x1, y1 = shape(g['geometry']).bounds
    kx = 111320 * math.cos(math.radians(REG['center'][1]))
    w_m, d_m = (x1 - x0) * kx * margin, (y1 - y0) * 111132 * margin
    ground = max(min_ground, w_m, d_m * REG['squash'] / aspect)
    return box_at((x0 + x1) / 2, (y0 + y1) / 2, ground, aspect=aspect, lift=45), round(ground)


def clamp(box, within):
    """`box` moved (not resized) to lie inside `within`, so no close view runs off the plate."""
    x, y, w, h = box
    X, Y, W, H = within
    x = min(max(x, X), X + W - w)
    y = min(max(y, Y), Y + H - h)
    return (x, y, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--full')
    ap.add_argument('--only')
    a = ap.parse_args()
    only = set(a.only.split(',')) if a.only else None
    g = os.path.join(a.work, 'g1937', 'richmond-1937-1937.svg')
    b = os.path.join(a.work, 'b2026', 'richmond-1937-2026.svg')
    vg, vb = view_box(g), view_box(b)
    x0, y0 = min(vg[0], vb[0]), min(vg[1], vb[1])
    x1, y1 = max(vg[0] + vg[2], vb[0] + vb[2]), max(vg[1] + vg[3], vb[1] + vb[3])
    union = (x0, y0, x1 - x0, y1 - y0)
    tmp = os.path.join(a.work, 'r.png')
    want = lambda n: only is None or n in only  # noqa: E731

    if want('grades-1937'):
        save(raster(g, union, 7900, tmp), 'grades-1937', a.full)
    if want('built-2026'):
        save(raster(b, union, 7900, tmp), 'built-2026', a.full)
    # What was built on D land, close: D1 (Jackson Ward, Gilpin), D5 (Church Hill North) and D8
    # (Randolph) with the interstates and the Downtown Expressway.
    if want('built-close'):
        box = box_at(-77.437, 37.548, 6200, aspect=0.5, lift=60)
        save(keyed(raster(b, box, 5600, tmp), 'Richmond today, with the 1937 grades under it: I-95, I-64 and the Downtown Expressway (black) across D1, D5 and D8',
                   'Looking north. The Downtown Expressway crosses D8 at left; the Turnpike, now I-95 and I-64, crosses D1 at center and runs along D5 at right.'), 'built-close', a.full)
    # Side by side at one scale: A5 (Windsor Farms) and D1 (Jackson Ward and Gilpin), the same
    # ground width, 1937 and today.
    if want('pair'):
        ground = 2600
        cells = []
        for svg, year in ((g, '1937'), (b, 'today')):
            row = []
            for (lon, lat), name in (((-77.5005, 37.5520), 'A5, Windsor Farms'), ((-77.4395, 37.5540), 'D1, Jackson Ward and Gilpin')):
                im = raster(svg, box_at(lon, lat, ground, aspect=0.55, lift=45), 2400, tmp)
                row.append(labeled(im, f'{name}, {year}'))
            cells.append(row)
        gap = 24
        w = cells[0][0].width * 2 + gap
        h = cells[0][0].height * 2 + gap
        out = Image.new('RGB', (w, h), P['sky'])
        for r, row in enumerate(cells):
            for c, im in enumerate(row):
                out.paste(im, (c * (im.width + gap), r * (im.height + gap)))
        save(keyed(out, 'An A area and a D area at the same scale: Windsor Farms (A5) and Jackson Ward (D1), 1937 and today',
                   'Each panel is 2.6 km of ground across, looking north.'), 'pair', a.full)
    # The worked example: A5 and D1 each whole, 1937 and today, in one box per area so each pair
    # makes a compare slider.
    for label, title in (('A5', 'Windsor Farms'), ('D1', 'Jackson Ward, Apostle Town and Navy Hill')):
        box, ground = area_box(label)
        box = clamp(box, union)
        if not (want(f'example-{label.lower()}-1937') or want(f'example-{label.lower()}-today')):
            continue
        made = {}
        for svg, year, when in ((g, '1937', 'in 1937'), (b, 'today', 'today')):
            grade = label[0]
            how = {('A5', '1937'): ' Buildings: those standing today that the city dates to 1937 or before.',
                   ('D1', '1937'): ' Buildings: those standing today that the city dates to 1937 or before, and in Jackson Ward those on the 1925 and 1952 Sanborn maps; most others then standing are gone and not drawn.'}.get((label, year), " Today's buildings and streets; limited-access highways in black.")
            im = raster(svg, box, 3200, tmp)
            # One band for both years: the slider shows one picture's left and the other's right,
            # so a band that differed would read as one broken line.
            how = {'A5': ' 1937: buildings standing today that the city dates to 1937 or before. Today: OpenStreetMap; limited-access highways in black.',
                   'D1': ' 1937: buildings standing today that the city dates to 1937 or before, and those on the 1925 and 1952 Sanborn maps; most others then standing are gone and not drawn. Today: OpenStreetMap; highways in black.'}[label]
            args = (f'{label}, {title}, in 1937 and today: an area the HOLC graded {grade}', f'About {ground / 1000:.1f} km of ground across, looking north.' + how)
            made[year] = (im, args, keyed(im, *args))
        # The two years open in one compare slider, so their pictures must sit at the same height:
        # the shorter band gets the difference.
        tall = max(v[2].height for v in made.values())
        for year, (im, args, out) in made.items():
            if out.height < tall:
                out = keyed(im, *args, extra=tall - out.height)
            save(out, f'example-{label.lower()}-{year}', a.full)
    # The twelve D areas, one close view each, today, with the grades under them.
    for label in D_AREAS:
        name = f'd-{slug(label)}'
        if want(name) or want('d-all'):
            box, ground = area_box(label)
            im = raster(b, clamp(box, union), 2400, tmp)
            save(keyed(im, f'{label}, {NAMES[label]}: graded D in 1937, seen today',
                       f'About {ground / 1000:.1f} km of ground across, looking north. Interstates and the Downtown Expressway in black.'), name, a.full)
    # The twelve together, four by three, as one figure the page shows as a grid.
    if want('d-grid') or want('d-all'):
        cells = [Image.open(os.path.join(ROOT, 'pages', f'redlining-d-{slug(l)}.webp')).convert('RGB') for l in D_AREAS]
        cw, gap = 1600, 30
        ch = max(round(c.height * cw / c.width) for c in cells)
        grid = Image.new('RGB', (4 * cw + 3 * gap, 3 * ch + 2 * gap), P['sky'])
        for i, c in enumerate(cells):
            grid.paste(c.resize((cw, round(c.height * cw / c.width)), Image.LANCZOS), ((i % 4) * (cw + gap), (i // 4) * (ch + gap)))
        save(grid, 'd-grid', a.full)
    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == '__main__':
    main()
