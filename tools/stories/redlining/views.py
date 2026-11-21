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
        save(raster(b, box, 5600, tmp), 'built-close', a.full)
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
        save(out, 'pair', a.full)
    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == '__main__':
    main()
