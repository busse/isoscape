#!/usr/bin/env python3
"""The Jackson Ward story's region views: every scene image on the page, built from the branch's
own history and drawn with isoscape, then cropped and, where the page numbers buildings, marked.

    python3 tools/stories/jackson-ward/views.py [--work DIR] [--full DIR] [--only name,name]

Builds each scene it needs once (`node bin/isoscape.js build jackson-ward --year Y [--with S]
--no-archive --out <work>/<scene>`), rasterizes the SVG with rsvg-convert at the zoom each view
asks for, crops it, and writes pages/jackson-ward-<name>.webp (1600 px wide, for the page),
pages/jackson-ward-<name>-large.webp (3200 px wide, opened in the page's lightbox) for views
drawn wider than 2,400 px, and, with --full, a full-size PNG of each (under 8,000 px) for review.
`--large-from DIR` writes only the large copies, from full-size PNGs already in DIR. Pairs and triples are stacked
with the year in the corner.

The year views (1925, 1952, 1959, today) share one frame. isoscape fits each build's viewBox to
what it draws, and today's reaches 7.2 units higher (a taller building at the far edge) and 0.1
lower, so each year's SVG is rasterized in the union of the four, widened to whole units
(`frame`). Every year view, and every crop of one, is then the same size and lines up pixel for
pixel with the others: the page's compare sliders need that, and the stacked views get it too.
Crop boxes are given from the 1952 view's own top left corner, as before.

Numbered views (Second Street) mark every building the sheets name (tools/sanborn/jw/named.csv
for 1952, named1925.csv for 1925) whose point falls in the crop: the drawn building holding the
point is found (a traced outline, or today's OSM outline where the scene draws one there), and
the marker stands over the top of its roof. Numbers run from the top of the picture down. The
key is written beside the image as JSON (<name>-key.json) for the page's table.

Colors (markers, labels) are read from src/palette.ts, never typed here.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'sanborn'))
from geo import to_m  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


P = palette()
INK, PAPER = P['ink'], P['sky']

# The scenes: name -> (year, switch or None)
SCENES = {
    's1925': (1925, None), 's1952': (1952, None), 's1959': (1959, None), 's2026': (2026, None),
    'count': (1952, 'count'), 'streets1952': (1952, 'streets'), 'streets2026': (2026, 'streets'),
    'island': (1952, 'island-corridor'),
}

# Boxes in SVG units (x, y, w, h) at zoom 1; rasterized at `z`. Second Street from Broad Street
# (the frame's near edge) to past Leigh; Apostle Town (Gilpin Court) along the railroad.
SECOND = (1400, 880, 950, 535)
APOSTLE = (1380, 320, 1150, 340)

# view name -> recipe
VIEWS = {
    'state-1925': dict(scene='s1925'),
    'state-1952': dict(scene='s1952'),
    'state-1959': dict(scene='s1959'),
    'state-2026': dict(scene='s2026'),
    'count-1952': dict(scene='count'),
    'streets-1952': dict(scene='streets1952'),
    'streets-2026': dict(scene='streets2026'),
    'island': dict(scene='island'),
    'second-street-1952': dict(scene='s1952', box=SECOND, z=4, names='named.csv', edition=1952),
    'second-street-1925': dict(scene='s1925', box=SECOND, z=4, names='named1925.csv', edition=1925),
    # Second Street unnumbered, for the page's compare slider (1925 against 1952).
    'second-street-1925-plain': dict(scene='s1925', box=SECOND, z=4),
    'second-street-1952-plain': dict(scene='s1952', box=SECOND, z=4),
    'apostle-town': dict(stack=[('s1925', APOSTLE, 3, '1925'), ('s1952', APOSTLE, 3, '1952'), ('s2026', APOSTLE, 3, 'today')]),
}


# The scenes drawn in one shared frame (the year views); see `frame`.
YEARS = ('s1925', 's1952', 's1959', 's2026')
REF = 's1952'  # crop boxes are measured from this scene's own viewBox corner


def viewbox(svg):
    with open(svg) as f:
        head = f.read(4000)
    return [float(v) for v in re.search(r'viewBox="([^"]+)"', head).group(1).split()]


_FRAME = {}


def frame(work):
    """The year views' shared viewBox, and how far (whole SVG units) it reaches left of and
    above the reference scene's: (x, y, w, h), (dx, dy)."""
    if 'f' not in _FRAME:
        import math
        boxes = {s: viewbox(build(work, s)) for s in YEARS}
        rx, ry, rw, rh = boxes[REF]
        dx = math.ceil(max(rx - b[0] for b in boxes.values()) - 1e-6)
        dy = math.ceil(max(ry - b[1] for b in boxes.values()) - 1e-6)
        dr = math.ceil(max(b[0] + b[2] - (rx + rw) for b in boxes.values()) - 1e-6)
        db = math.ceil(max(b[1] + b[3] - (ry + rh) for b in boxes.values()) - 1e-6)
        _FRAME['f'] = ((rx - dx, ry - dy, rw + dx + dr, rh + dy + db), (dx, dy))
    return _FRAME['f']


def fmt(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')


def framed(work, scene):
    """The scene's SVG with its viewBox, and the paper behind it, set to the shared frame."""
    svg = build(work, scene)
    out = svg[:-4] + '-framed.svg'
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(svg):
        (fx, fy, fw, fh), _ = frame(work)
        vb = viewbox(svg)
        s = open(svg).read()
        old = ' '.join(fmt(v) for v in vb)
        new = ' '.join(fmt(v) for v in (fx, fy, fw, fh))
        assert s.count(f'viewBox="{old}"') >= 1, (svg, old)
        s = s.replace(f'viewBox="{old}"', f'viewBox="{new}"', 1)
        paper = f'<rect x="{fmt(vb[0])}" y="{fmt(vb[1])}" width="{fmt(vb[2])}" height="{fmt(vb[3])}"'
        assert paper in s, (svg, paper)
        s = s.replace(paper, f'<rect x="{fmt(fx)}" y="{fmt(fy)}" width="{fmt(fw)}" height="{fmt(fh)}"', 1)
        open(out, 'w').write(s)
    return out


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def build(work, scene):
    year, switch = SCENES[scene]
    out = os.path.join(work, scene)
    svg = os.path.join(out, f'jackson-ward-{year}.svg')
    if not os.path.exists(svg):
        cmd = ['node', 'bin/isoscape.js', 'build', 'jackson-ward', '--year', str(year), '--no-archive', '--out', out]
        if switch:
            cmd += ['--with', switch]
        run(cmd)
    return svg


def raster(work, scene, z):
    svg = framed(work, scene) if scene in YEARS else build(work, scene)
    png = svg[:-4] + f'-z{z}.png'
    if not os.path.exists(png) or os.path.getmtime(png) < os.path.getmtime(svg):
        subprocess.run(['rsvg-convert', '-z', str(z), svg, '-o', png], check=True)
    return png


def crop(png, box, z, offset=(0, 0)):
    """Cut `box` (SVG units from the reference corner) out of a raster at zoom `z` whose own
    corner lies `offset` units left of and above that corner."""
    im = Image.open(png).convert('RGB')
    if box is None:
        return im
    x, y, w, h = box
    x, y = x + offset[0], y + offset[1]
    return im.crop((round(x * z), round(y * z), round((x + w) * z), round((y + h) * z)))


def cut(work, scene, box, z):
    """A crop of a scene's raster, placed by the shared frame for the year views."""
    return crop(raster(work, scene, z), box, z, frame(work)[1] if scene in YEARS else (0, 0))


def font(size, bold=True):
    for f in ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def corner_label(im, text, scale=1.0):
    d = ImageDraw.Draw(im)
    f = font(round(44 * scale))
    pad = round(14 * scale)
    tw, th = d.textbbox((0, 0), text, font=f)[2:]
    d.rectangle((0, 0, tw + 2 * pad, th + 2 * pad), fill=PAPER)
    d.text((pad, pad - round(4 * scale)), text, fill=INK, font=f)
    return im


# ---- finding a named building in the drawn SVG ----------------------------------------------

def svg_roofs(svg):
    """data-id -> (mean x, min y) of the group's corner dots, in SVG units."""
    s = open(svg).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    out = {}
    for m in re.finditer(r'<g data-id="([^"]+)">(.*?)</g>', s, re.S):
        pts = [(float(a), float(b)) for a, b in re.findall(r'M(-?(?:\d+\.?\d*|\.\d+))[ ,]?(-?(?:\d+\.?\d*|\.\d+))h0', m.group(2))]
        if pts:
            p = np.array(pts)
            out[m.group(1)] = (float(p[:, 0].mean()) - vb[0], float(p[:, 1].min()) - vb[1])
    return out


def footprints():
    """(data-id prefix, shapely polygon in meters) for every traced outline and OSM building."""
    from shapely.geometry import Polygon, shape
    from shapely.ops import transform
    tm = lambda x, y, z=None: to_m(x, y)  # noqa: E731
    out = []
    for f in ('history/sanborn/jackson-ward-lost.geojson', 'history/sanborn/jackson-ward-1925-lost.geojson', 'history/sanborn/lost.geojson'):
        for ft in json.load(open(os.path.join(ROOT, f)))['features']:
            try:
                out.append(('traced:' + ft['properties']['id'], transform(tm, shape(ft['geometry'])).buffer(0)))
            except Exception:
                continue
    osm = json.load(open(os.path.join(ROOT, 'data/richmond-streetcars/osm.json')))['elements']
    for e in osm:
        if e['type'] == 'way' and 'building' in e.get('tags', {}) and len(e.get('geometry', [])) > 3:
            g = e['geometry']
            x, y = to_m([q['lon'] for q in g], [q['lat'] for q in g])
            if abs(x.mean()) > 4000 or abs(y.mean()) > 4000:
                continue
            out.append((f"w{e['id']}", Polygon(list(zip(x, y))).buffer(0)))
    return out


_FP = None


def find_roof(roofs, lon, lat):
    global _FP
    from shapely.geometry import Point
    if _FP is None:
        _FP = footprints()
    x, y = to_m(lon, lat)
    pt = Point(float(x), float(y))
    hits = []
    for pid, poly in _FP:
        if poly.contains(pt):
            for k, v in roofs.items():
                if k == pid or k.startswith(pid + '.'):
                    hits.append((poly.area, v))
    if not hits:
        return None
    hits.sort()
    return hits[0][1]


def numbered(im, svg, box, z, names, edition):
    roofs = svg_roofs(svg)
    x0, y0, w, h = box
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, 'tools/sanborn/jw', names))):
        if int(r['edition']) != edition:
            continue
        p = find_roof(roofs, float(r['lon']), float(r['lat']))
        if p is None:
            continue
        if not (x0 + 6 < p[0] < x0 + w - 6 and y0 + 26 < p[1] < y0 + h - 4):
            continue
        rows.append(dict(name=r['name'], stories=r['stories'], sheet=r['sheet'], x=p[0], y=p[1]))
    # one marker per drawn roof (several labels can name parts of one building)
    seen, uniq = {}, []
    for r in rows:
        k = (round(r['x'], 1), round(r['y'], 1))
        if k in seen:
            if r['name'] not in seen[k]['name']:
                seen[k]['name'] += '; ' + r['name']
            continue
        seen[k] = r
        uniq.append(r)
    uniq.sort(key=lambda r: (round(r['y'] / 40), r['x']))
    d = ImageDraw.Draw(im)
    f = font(round(9 * z))
    rad, stem = round(7.6 * z), round(17 * z)
    for i, r in enumerate(uniq, 1):
        r['n'] = i
        cx, cy = (r['x'] - x0) * z, (r['y'] - y0) * z
        top = cy - stem
        d.line((cx, cy, cx, top + rad), fill=INK, width=max(2, round(0.75 * z)))
        d.ellipse((cx - rad, top - rad, cx + rad, top + rad), fill=PAPER, outline=INK, width=max(2, round(0.75 * z)))
        t = str(i)
        tw, th = d.textbbox((0, 0), t, font=f)[2:]
        d.text((cx - tw / 2, top - th / 2 - round(0.7 * z)), t, fill=INK, font=f)
    return im, [dict(n=r['n'], name=r['name'], stories=r['stories'], sheet=r['sheet']) for r in uniq]


LARGE = 3200       # the lightbox's copy, px wide
LARGE_FROM = 2400  # only views drawn at least this wide get one


def save_large(im, name):
    if im.width < LARGE_FROM:
        return
    w = min(LARGE, im.width)
    big = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
    big.convert('RGB').save(os.path.join(ROOT, 'pages', f'jackson-ward-{name}-large.webp'), quality=80, method=6)


def save(im, name, full, keep=None):
    if full:
        im.save(os.path.join(full, f'jackson-ward-{name}.png'), optimize=True)
    save_large(im, name)
    w = 1600
    small = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
    small.save(os.path.join(ROOT, 'pages', f'jackson-ward-{name}.webp'), quality=84, method=6)
    if keep is not None:
        json.dump(keep, open(os.path.join(HERE, f'{name}-key.json'), 'w'), indent=1, ensure_ascii=False)
    print('wrote', name, im.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', default='/tmp/jw-views')
    ap.add_argument('--full', default=None)
    ap.add_argument('--only', default=None)
    ap.add_argument('--large-from', default=None)
    a = ap.parse_args()
    if a.large_from:
        for name in VIEWS:
            f = os.path.join(a.large_from, f'jackson-ward-{name}.png')
            if os.path.exists(f) and (not a.only or name in a.only.split(',')):
                save_large(Image.open(f), name)
                print('wrote large', name)
        return
    os.makedirs(a.work, exist_ok=True)
    if a.full:
        os.makedirs(a.full, exist_ok=True)
    for name, v in VIEWS.items():
        if a.only and name not in a.only.split(','):
            continue
        if 'stack' in v:
            ims = []
            for scene, box, z, lab in v['stack']:
                im = cut(a.work, scene, box, z)
                ims.append(corner_label(im, lab, scale=im.width / 3000))
            W = max(i.width for i in ims)
            gap = round(W / 150)
            out = Image.new('RGB', (W, sum(i.height for i in ims) + gap * (len(ims) - 1)), PAPER)
            y = 0
            for i in ims:
                out.paste(i, (0, y))
                y += i.height + gap
            if out.height > 7900:
                k = 7900 / out.height
                out = out.resize((round(out.width * k), 7900), Image.LANCZOS)
            save(out, name, a.full)
        elif 'box' in v:
            z = v['z']
            im = cut(a.work, v['scene'], v['box'], z)
            if 'names' in v:
                im, key = numbered(im, build(a.work, v['scene']), v['box'], z, v['names'], v['edition'])
                save(im, name, a.full, key)
            else:
                save(im, name, a.full)
        else:
            im = Image.open(raster(a.work, v['scene'], 2)).convert('RGB')
            save(im, name, a.full)
    # the link preview: the 1952 view, cropped to 1.91:1 around the corridor, 1200 x 630
    if not a.only:
        im = Image.open(raster(a.work, 's1952', 2)).convert('RGB')
        w = round(im.height * 0.86 * 1.905)
        h = round(im.height * 0.86)
        x0 = (im.width - w) // 2
        y0 = round(im.height * 0.07)
        im.crop((x0, y0, x0 + w, y0 + h)).resize((1200, 630), Image.LANCZOS).save(os.path.join(ROOT, 'pages', 'jackson-ward-social.jpg'), quality=84)
        print('wrote social')


if __name__ == '__main__':
    main()
