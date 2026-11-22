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
from areas import D_AREAS, slug  # noqa: E402
from areas import KEY_LABELS as LEGEND, KEY_TITLE, KEY_SOURCE, title as area_title  # noqa: E402
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


def raster(svg, box, width, out, label_px=None, caption=None):
    """`svg` drawn inside `box` (x, y, w, h), `width` px wide, on the paper's sky color. With
    `label_px`, the map's area labels are redrawn `label_px` pixels tall whatever the box's
    scale, so every close view labels its areas at one size relative to the picture."""
    with open(svg, 'rb') as fh:
        data = fh.read()
    if caption is not None:
        data = relaid_caption(data, caption)
    if label_px is not None:
        size = label_px * box[2] / width
        def relabel(m):
            g = re.sub(rb'stroke-width="[0-9.]+"', b'stroke-width="%.2f"' % (size * 0.22), m.group(0), count=1)
            return re.sub(rb'font-size="[0-9.]+"', b'font-size="%.2f"' % size, g)
        data = re.sub(rb'<g class="labels".*?</g>', relabel, data, count=1, flags=re.S)
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
    credit = CREDIT + '. ' + KEY_SOURCE + '. ' + BASE_CREDIT + '.'
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


# Public housing the page names, marked where HUD's records place them (the OSM cache has no
# outlines named for them): the address, found among OSM's address points on the same street.
# Gilpin Court: 1000 St Paul Street (no 1000 in OSM; placed at the street's south end, below the
# 1103 address point, so approximate). Mosby Court: 1909 Accommodation Street (between OSM's
# 1907 and 1911). SVG points from `isoscape locate richmond-1937` (the same in 1937 and 2026).
HOUSING = [('Gilpin Court, public housing opened 1943 (approximate)', 1227.1, -45.0), ('Mosby Court, public housing opened 1962', 1881.4, 114.5)]
# What the band under each view says of the marks; Gilpin's is approximate wherever it shows.
NOTE = {'Gilpin Court': "Gilpin Court is marked approximately at the address in HUD's record (circle)",
        'Mosby Court': "Mosby Court is marked at the address in HUD's record (circle)"}
HOUSING_NOTE = " Circles mark Mosby Court at the address in HUD's record and Gilpin Court approximately at its address."


def marked(img, box, places=HOUSING):
    """`img` (drawn from `box`) with each place inside it marked: a ring and its name, haloed."""
    x, y, w, h = box
    k = img.width / w
    d = ImageDraw.Draw(img)
    u = max(14, img.width // 110)
    f = font(round(u * 1.5), bold=True)
    hit = False
    for name, sx, sy in places:
        px, py = (sx - x) * k, (sy - y) * k
        if not (u * 2 < px < img.width - u * 2 and u * 2 < py < img.height - u * 2):
            continue
        hit = True
        r = u * 1.1
        d.ellipse((px - r, py - r, px + r, py + r), outline=P['sky'], width=max(3, u // 3))
        d.ellipse((px - r, py - r, px + r, py + r), outline=P['ink'], width=max(2, u // 6))
        tw = d.textlength(name, font=f)
        tx = px + r * 1.4 if px + r * 1.4 + tw < img.width - u else px - r * 1.4 - tw
        d.text((tx, py - f.size * 0.6), name, font=f, fill=P['ink'], stroke_width=max(2, u // 4), stroke_fill=P['sky'])
    return img, hit


def relaid_caption(data, side):
    """The scene's caption (year, title, key and source line) laid out again in a block about two
    fifths of the frame wide, at the `side` ('left' or 'right') of the frame, so the two pictures
    of a compare slider each keep their caption whole at their own outer edge. The key goes in two
    columns and the source line wraps. Widths are estimated at 0.46 em a character (Georgia)."""
    m = re.search(rb'<g class="caption"[^>]*>(.*?)</g>', data, flags=re.S)
    vb = [float(v) for v in re.search(rb'viewBox="([^"]+)"', data[:600]).group(1).split()]
    texts = re.findall(rb'<text x="([-0-9.]+)" y="([-0-9.]+)" font-size="([0-9.]+)"([^>]*)>(.*?)</text>', m.group(1))
    rects = re.findall(rb'<rect [^>]*fill="(#[0-9a-f]{6})"[^>]*/>', m.group(1))
    year, sub, ktitle = texts[0], texts[1], texts[2]
    labels, source = texts[3:7], texts[7]
    x0 = float(year[0])
    em = lambda fs, t: 0.46 * fs * len(t.decode())  # noqa: E731
    fs_k, fs_s = float(ktitle[2]), float(source[2])
    col = max(em(fs_k, l[4]) for l in labels) + fs_k * 2.4
    # The source line, wrapped.
    # The whole credit, as under every other picture: the grade names' note in full and the base
    # credit (the reader's read, d5: these two travel alone from the lightbox).
    text = source[4].decode() + '. ' + BASE_CREDIT + '.'

    words, rows, cur = text.split(' '), [], ''
    room = vb[2] * 0.56
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if em(fs_s, t.encode()) > room and cur:
            rows.append(cur); cur = w_
        else:
            cur = t
    rows.append(cur)
    width = max(2 * col, em(fs_k, ktitle[4]), max(em(fs_s, r.encode()) for r in rows), em(float(year[2]), year[4]) + em(float(sub[2]), sub[4]) + 60)
    left = x0 if side == 'left' else vb[0] + vb[2] - (x0 - vb[0]) - width
    dx = left - x0
    out = []
    y = float(year[1])
    out.append(b'<text x="%.1f" y="%.1f" font-size="%s"%s>%s</text>' % (float(year[0]) + dx, y, year[2], year[3], year[4]))
    out.append(b'<text x="%.1f" y="%.1f" font-size="%s"%s>%s</text>' % (float(sub[0]) + dx, y, sub[2], sub[3], sub[4]))
    # The key rises into the room under the title, so the full credit (up to four lines) still
    # ends above the map.
    y = float(ktitle[1]) - fs_k * 1.7
    out.append(b'<text x="%.1f" y="%.1f" font-size="%s"%s>%s</text>' % (left, y, ktitle[2], ktitle[3], ktitle[4]))
    for i, (lab, fill) in enumerate(zip(labels, rects)):
        cx, cy = left + (i % 2) * col, y + fs_k * 1.25 * (1 + i // 2)
        out.append(b'<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="0.6"/>' % (cx, cy - fs_k * 0.85, fs_k * 1.6, fs_k, fill, P['ink'].encode()))
        out.append(b'<text x="%.1f" y="%.1f" font-size="%s"%s>%s</text>' % (cx + fs_k * 2.0, cy, lab[2], lab[3], lab[4]))
    y += fs_k * 1.25 * 2 + fs_s * 1.3
    for r in rows:
        out.append(b'<text x="%.1f" y="%.1f" font-size="%s"%s>%s</text>' % (left, y, source[2], source[3], r.encode()))
        y += fs_s * 1.3
    head = data[:m.start(1)]
    return head + b'\n' + b'\n'.join(out) + b'\n' + data[m.end(1):]


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
        save(raster(g, union, 7900, tmp, caption='left'), 'grades-1937', a.full)
    if want('built-2026'):
        save(raster(b, union, 7900, tmp, caption='right'), 'built-2026', a.full)
    # What was built on D land, close: D1 (Jackson Ward, Gilpin), D5 (Church Hill North) and D8
    # (Randolph) with the interstates and the Downtown Expressway.
    if want('built-close'):
        box = box_at(-77.437, 37.548, 6200, aspect=0.5, lift=60)
        im, hit = marked(raster(b, box, 5600, tmp), box)
        save(keyed(im, 'Richmond today, with the 1937 grades under it: I-95, I-64 and the Downtown Expressway (black) across D1, D5 and D8',
                   'Looking north. The Downtown Expressway crosses D8 at left; I-95 and I-64 cross D1 at center; I-64 runs along D5 at right.' + (HOUSING_NOTE if hit else '')), 'built-close', a.full)
    # Side by side at one scale: A5 (Windsor Farms) and D1 (Jackson Ward and Gilpin), the same
    # ground width, 1937 and today.
    if want('pair'):
        ground = 2600
        cells = []
        for svg, year in ((g, '1937'), (b, 'today')):
            row = []
            for (lon, lat), name in (((-77.5005, 37.5520), area_title('A5')), ((-77.4395, 37.5540), area_title('D1'))):
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
        save(keyed(out, f"An A area and a D area at the same scale: {area_title('A5')} and {area_title('D1')}, 1937 and today",
                   'Each panel is 2.6 km of ground across, looking north. 1937: only buildings that still stand, plus Jackson Ward\'s Sanborn blocks; most others then standing are gone and not drawn.'), 'pair', a.full)
    # The worked example: A5 and D1 each whole, 1937 and today, in one box per area so each pair
    # makes a compare slider.
    for label in ('A5', 'D1'):
        box, ground = area_box(label)
        box = clamp(box, union)
        if not (want(f'example-{label.lower()}-1937') or want(f'example-{label.lower()}-today')):
            continue
        made = {}
        for svg, year, when in ((g, '1937', 'in 1937'), (b, 'today', 'today')):
            grade = label[0]
            how = {('A5', '1937'): ' Buildings: those standing today that the city dates to 1937 or before.',
                   ('D1', '1937'): ' Buildings: those standing today that the city dates to 1937 or before, and in Jackson Ward those on the 1925 and 1952 Sanborn maps; most others then standing are gone and not drawn.'}.get((label, year), " Today's buildings and streets; limited-access highways in black.")
            im = raster(svg, box, 3200, tmp, label_px=58)
            hit = False
            if year == 'today' and label == 'D1':
                im, hit = marked(im, box, HOUSING[:1])
            # One band for both years: the slider shows one picture's left and the other's right,
            # so a band that differed would read as one broken line.
            how = {'A5': ' 1937: buildings standing today that the city dates to 1937 or before. Today: OpenStreetMap; limited-access highways in black.',
                   'D1': ' 1937: buildings standing today that the city dates to 1937 or before, and those on the 1925 and 1952 Sanborn maps; most others then standing are gone and not drawn. Today: OpenStreetMap; highways in black.'}[label]
            if label == 'D1':
                how += ' Today, ' + NOTE['Gilpin Court'] + '.'
            args = (f'{area_title(label)}, in 1937 and today: an area the HOLC graded {grade}', f'About {ground / 1000:.1f} km of ground across, looking north.' + how)
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
            box = clamp(box, union)
            im = raster(b, box, 2400, tmp, label_px=46)
            hit = False
            one = {'D1': 0, 'D5': 1}.get(label)
            note = ''
            if one is not None:
                im, hit = marked(im, box, HOUSING[one:one + 1])
                court = HOUSING[one][0].split(',')[0]
                note = f" {NOTE[court]}." if hit else ''
            save(keyed(im, f'{area_title(label)}: graded D in 1937, seen today',
                       f'About {ground / 1000:.1f} km of ground across, looking north. Interstates and the Downtown Expressway in black.' + note), name, a.full)
    # The link preview (front matter `social:`): 1200 × 630, a band naming the year and whose
    # grades these are, with the key, over the 1937 citywide view cropped to the D areas around
    # downtown, so the picture reads at the size a preview shows.
    if want('social'):
        social(a.full)
    if os.path.exists(tmp):
        os.remove(tmp)


def social(full):
    src = Image.open(os.path.join(ROOT, 'pages', 'redlining-grades-1937-large.webp')).convert('RGB')
    W, H, band = 1200, 630, 172
    # The crop: the view's middle, where D1, D5, D6, D8 and the river sit (fractions of the image).
    cw = round(src.width * 0.46)
    ch = round(cw * (H - band) / W)
    cx, cy = round(src.width * 0.60), round(src.height * 0.56)
    crop = src.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)).resize((W, H - band), Image.LANCZOS)
    out = Image.new('RGB', (W, H), P['sky'])
    out.paste(crop, (0, band))
    d = ImageDraw.Draw(out)
    d.text((24, 16), "Richmond, 1937: the federal HOLC's grades", fill=P['ink'], font=font(40, bold=True))
    d.text((24, 66), 'drawn on the ground they graded', fill=P['ink'], font=font(26))
    kf = font(20)
    for i, (tone, label) in enumerate(zip(P['tint']['tones'], LEGEND)):
        x, y = 24 + (i % 2) * 470, 108 + (i // 2) * 30
        d.rectangle((x, y + 3, x + 26, y + 23), fill=tone, outline=P['ink'])
        d.text((x + 34, y), label, fill=P['ink'], font=kf)
    d.line((0, band - 1, W, band - 1), fill=P['ink'], width=2)
    path = os.path.join(ROOT, 'pages', 'redlining-social.jpg')
    out.save(path, quality=86)
    if full:
        out.save(os.path.join(full, 'redlining-social.png'))
    print(f'redlining-social: {out.width}×{out.height}')


if __name__ == '__main__':
    main()
