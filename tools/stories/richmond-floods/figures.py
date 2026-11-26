#!/usr/bin/env python3
"""Write the pictures of the floods story page (pages/richmond-floods-*.webp) from the final-draft
(rc3) plates, sheets and rain charts. Nothing here draws: every picture is a crop or a plain
composition of a render the series already made.

    python3 tools/stories/richmond-floods/figures.py [--plates DIR] [--sheets DIR] [--rain DIR]

--plates  the rc3 plate SVGs, as tools/floods/d3/plates.sh builds them (default /tmp/rc2/plates,
          where the rc3 round built them; rebuild with plates.sh if it is gone)
--sheets  the rc3 sheets at 300 dpi (default /mnt/user-data/outputs/floods/rc3/full)
--rain    the rain branch's figures (default /mnt/user-data/outputs/floods/rain)
--isoscape  where to run `isoscape locate` (default this checkout; it needs data/richmond-i195-rocketts)

A plate is rendered from its SVG with the caption group taken out and one viewBox per area, so a
plate and its twin (or the same frame in another year) line up pixel for pixel for a compare
figure. Box crops narrow the viewBox round a box of tools/floods/d3/boxes.json, as
tools/floods/d3/render_boxes.py does, with the map's small type set smaller to fit. Each picture is
written at 1600 px (inlined or linked by the page) and, for the plates, 3200 px as `-large` for the
lightbox. `figures.json` beside this script lists every output with its inputs and their sha256.
Made with Claude.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PAGES = os.path.join(ROOT, 'pages')
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
PAPER = (244, 241, 234)   # the sheets' paper, sampled from the rc3 proofs
INK = (44, 43, 51)
ACCENT = (155, 58, 44)
# One viewBox per area, wide enough for every plate's own fitted box (rc3 maps.json), so pairs align.
VIEW = {
    'shockoe': (-1998.7, -706.0, 3996.14, 1380.0),
    'manchester': (-1611.0, -718.0, 3443.0, 1400.0),
}
TEXT_SCALE = 0.62
MANIFEST = []
ISO = ROOT   # where `node bin/isoscape.js locate` runs (an isoscape checkout with the data cache)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def render(svg, box, width, small_text=False):
    s = open(svg, encoding='utf8').read()
    s = re.sub(r'<g class="caption".*?</g>', '', s, flags=re.S)
    if small_text:
        s = re.sub(r'font-size="([0-9.]+)"', lambda m: f'font-size="{float(m.group(1)) * (TEXT_SCALE if float(m.group(1)) < 30 else 0.35):.1f}"', s)
    x, y, w, h = box
    s = re.sub(r'viewBox="[^"]+"', f'viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}"', s, count=1)
    s = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r'\1', s, count=2)
    with tempfile.TemporaryDirectory() as t:
        a, b = os.path.join(t, 'p.svg'), os.path.join(t, 'p.png')
        open(a, 'w', encoding='utf8').write(s)
        subprocess.run(['rsvg-convert', '-w', str(width), '-b', '#%02x%02x%02x' % PAPER, '-o', b, a], check=True)
        return Image.open(b).convert('RGB')


def save(img, name, inputs, large=None):
    out = os.path.join(PAGES, name)
    small = img.copy()
    if small.width > 1600:
        small = small.resize((1600, round(small.height * 1600 / small.width)), Image.LANCZOS)
    small.save(out, 'WEBP', quality=82, method=6)
    rec = {'file': f'pages/{name}', 'size': list(small.size), 'inputs': [{'path': p, 'sha256': sha(p)} for p in inputs]}
    if large is not None:
        lg = large if large.width <= 3200 else large.resize((3200, round(large.height * 3200 / large.width)), Image.LANCZOS)
        ln = name.replace('.webp', '-large.webp')
        lg.save(os.path.join(PAGES, ln), 'WEBP', quality=80, method=6)
        rec['large'] = f'pages/{ln}'
    MANIFEST.append(rec)
    print('wrote', out, small.size)


def locate(year, pts):
    out = subprocess.run(['node', 'bin/isoscape.js', 'locate', 'richmond-floods-shockoe', '--year', str(year), '--',
                          *[f'{a},{b}' for a, b in pts]], cwd=ISO, capture_output=True, text=True, check=True).stdout
    return [(p['x'], p['y']) for p in json.loads(out)]


def font(size, bold=False):
    return ImageFont.truetype(SERIF_B if bold else SERIF, size)


def label_above(img, lines, pad=14):
    """The picture with lines of text set above it on the paper (title bold, then plain)."""
    fs = [font(30, True)] + [font(24)] * (len(lines) - 1)
    hs = [f.getbbox('Ag')[3] + 8 for f in fs]
    top = pad + sum(hs) + 6
    out = Image.new('RGB', (img.width, img.height + top), PAPER)
    d = ImageDraw.Draw(out)
    y = pad
    for i, (t, f, h) in enumerate(zip(lines, fs, hs)):
        d.text((4, y), t, font=f, fill=ACCENT if i == len(lines) - 1 and i > 0 else INK)
        y += h
    out.paste(img, (0, top))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plates', default='/tmp/rc2/plates')
    ap.add_argument('--sheets', default='/mnt/user-data/outputs/floods/rc3/full')
    ap.add_argument('--rain', default='/mnt/user-data/outputs/floods/rain')
    ap.add_argument('--isoscape', default=ROOT, help='a checkout with the richmond-i195-rocketts cache, for locate (default: this one)')
    a = ap.parse_args()
    global ISO
    ISO = a.isoscape
    P = lambda n: os.path.join(a.plates, n + '.svg')  # noqa: E731

    # The opening pair: the 1972 plate and its twin, cut to the valley so it reads on a phone.
    hero = (-1150.0, -706.0, 2000.0, 1250.0)
    for k, n in (('1972', 'richmond-floods-shockoe-1972-flood-1972'), ('1972-dry', 'richmond-floods-shockoe-1972-flood-1972-dry')):
        img = render(P(n), hero, 3200)
        save(img, f'richmond-floods-hero-{k}.webp', [P(n)], large=img)
    # Whole plates, one shared frame per area, at 3200 px.
    plates = {
        '1972': 'richmond-floods-shockoe-1972-flood-1972',
        '1972-dry': 'richmond-floods-shockoe-1972-flood-1972-dry',
        '1771': 'richmond-floods-shockoe-1788-flood-1771',
        '1936': 'richmond-floods-shockoe-1936-flood-1936',
        '1969': 'richmond-floods-shockoe-1969-flood-1969',
        '1985': 'richmond-floods-shockoe-1985-flood-1985',
        '1996': 'richmond-floods-shockoe-1996-flood-1996',
        '2020': 'richmond-floods-shockoe-2020-flood-2020',
        'gaston': 'richmond-floods-shockoe-2004-flood-gaston-b',
        'today-wall': 'richmond-floods-shockoe-2026-flood-agnes-today',
    }
    for k, n in plates.items():
        if k == '1972-dry':
            continue  # the page shows the twin only in the opening pair, the strip and the 17th and Dock pair
        img = render(P(n), VIEW['shockoe'], 3200)
        save(img, f'richmond-floods-{k}.webp', [P(n)], large=img)
        if k == '1972':
            # The link preview: 1200 x 630 from the middle of the 1972 plate.
            w = img.width
            c = img.crop((int(w * 0.25), int(img.height * 0.08), int(w * 0.25) + 1520, int(img.height * 0.08) + 798))
            c.resize((1200, 630), Image.LANCZOS).save(os.path.join(PAGES, 'richmond-floods-social.jpg'), quality=86)
            MANIFEST.append({'file': 'pages/richmond-floods-social.jpg', 'inputs': [{'path': P(n), 'sha256': sha(P(n))}]})
    for k, n in {'manchester-wall': 'richmond-floods-manchester-2026-flood-agnes-today',
                 'manchester-nowall': 'richmond-floods-manchester-2026-flood-agnes-today-nowall'}.items():
        img = render(P(n), VIEW['manchester'], 3200)
        save(img, f'richmond-floods-{k}.webp', [P(n)], large=img)

    # How to read: the 17th Street Market box on the 1972 plate, larger than the sheet's box.
    boxes = json.load(open(os.path.join(ROOT, 'tools/floods/d3/boxes.json')))['shockoe']
    bx = {b['id']: b for b in boxes['boxes']}
    (mx, my), = locate(1972, [bx['market']['at']])
    w, h = 420, 196
    img = render(P(plates['1972']), (mx - w / 2, my - h / 2, w, h), 1600, small_text=True)
    save(img, 'richmond-floods-read.webp', [P(plates['1972'])])
    # 17th and Dock, flooded and dry (a compare pair).
    (dx, dy), = locate(1972, [bx['dock']['at']])
    for k in ('1972', '1972-dry'):
        img = render(P(plates[k]), (dx - w / 2, dy - h / 2, w, h), 1600, small_text=True)
        save(img, f'richmond-floods-dock-{k}.webp', [P(plates[k])])
    # Gaston: the market and 17th Street, close.
    (gx, gy), = locate(2004, [bx['market']['at']])
    img = render(P(plates['gaston']), (gx - w / 2, gy - h / 2 - 20, w, h), 1600, small_text=True)
    save(img, 'richmond-floods-gaston-market.webp', [P(plates['gaston'])])

    # The same blocks in every flood: the market box on each plate, four across, two rows.
    counts = json.load(open(os.path.join(ROOT, 'drafts/richmond-floods/counts.json')))['rc3']['boxes']['shockoe']
    tiles = [('1936', 1936, 'March 1936'), ('1969', 1969, 'Camille, August 1969'), ('1972', 1972, 'Agnes, June 1972'),
             ('1985', 1985, 'November 1985'), ('1996', 1996, 'Fran, September 1996'), ('gaston', 2004, "Gaston's rain, August 2004"),
             ('2020', 2020, 'November 2020'), ('1972-dry', 1972, 'June 1972, no water (the twin)')]
    key = {'1936': '1936:1936', '1969': '1969:1969', '1972': '1972:1972', '1985': '1985:1985', '1996': '1996:1996',
           'gaston': 'gaston-b:2004', '2020': '2020:2020', '1972-dry': '1972-dry:1972'}
    tw, th = 340, 165
    cells = []
    for k, yr, title in tiles:
        (cx, cy), = locate(yr, [bx['market']['at']])
        im = render(P(plates[k]), (cx - tw / 2, cy - th / 2, tw, th), 790, small_text=True)
        d = counts[key[k]]['market']['depthFt']
        if k in ('1996', '2020'):
            sub = 'dry behind the wall'
        elif k == '1972-dry':
            sub = 'the same city, dry'
        elif k == 'gaston':
            sub = f'about {round(d)} ft at 17th and Main, as drawn'
        else:
            sub = f'{round(d)} ft deep at 17th and Main'
        cells.append(label_above(im, [title, sub]))
    cw, ch = cells[0].size
    gap = 16
    # Two across, four down: readable on a phone, where a row of four is not.
    grid = Image.new('RGB', (cw * 2 + gap, ch * 4 + gap * 3), PAPER)
    for i, c in enumerate(cells):
        grid.paste(c, ((i % 2) * (cw + gap), (i // 2) * (ch + gap)))
    save(grid, 'richmond-floods-strip.webp', [P(plates[k]) for k, _, _ in tiles], large=grid)

    # Gaston's rain: the rc3 sheet's rain panel, and the rain branch's plan map and explainer.
    sheet = os.path.join(a.sheets, 'richmond-floods-shockoe-2004-1.0.0-rc3.jpg')
    s = Image.open(sheet).convert('RGB')
    panel = s.crop((6330, 5330, 9480, 6830))
    save(panel, 'richmond-floods-rain-hours.webp', [sheet])
    pm = os.path.join(a.rain, 'a-plan-map.png')
    im = Image.open(pm).convert('RGB')
    # Its working title named the storm by its peak strength; the page's caption names it, so the
    # title line is cut off and the subtitle, legend and map kept.
    im = im.crop((0, 106, im.width, im.height))
    pad = Image.new('RGB', (im.width, im.height + 30), PAPER)
    pad.paste(im, (0, 30))
    im = pad
    save(im, 'richmond-floods-rain-map.webp', [pm])
    ex = os.path.join(a.rain, 'e-explainer.png')
    save(Image.open(ex).convert('RGB'), 'richmond-floods-bowl.webp', [ex])

    json.dump({'about': 'Pictures of pages/richmond-floods.md, written by figures.py from the rc3 renders.', 'files': MANIFEST},
              open(os.path.join(HERE, 'figures.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
