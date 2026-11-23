#!/usr/bin/env python3
"""The guide's 1952-and-today pictures, with the streets named on them (labels.py): one pair for
each vantage point, and the whole ward in 1952 and today as the guide's centerpiece.

    python3 tools/stories/jackson-ward-guide/pairs.py [--work DIR] [--full DIR] [--only ward,1,2,...]

The scenes are the story's own (tools/stories/jackson-ward/views.py: `jackson-ward --year 1952`
and `--year 2026`, built once into --work), rasterized in the shared frame views.py gives the
year views, so a crop is the same box in both. The 1952 half carries the story's hatch over the
blocks no sheet was traced for (views.untraced), as the story's own 1952 view does.

Each vantage point's pair is a box about 280 m across, centered a little beyond the point (the
views look north), the point's place found by `isoscape locate`; its number in a disc where you
stand. Stop 2 of the old guide's lesson stands: a box is moved up the picture until no point of a
later street listed in LATER is in it (Maggie L. Walker Place near where 2nd Street ends). The
Coliseum's point has no pair (NO_PAIR says why).

Writes pages/jackson-ward-guide-pair-<n>.webp (1200 px wide), and the centerpiece
pages/jackson-ward-guide-ward.webp (1600 px) with its -large copy (3200 px); with --full, PNGs
for review; pairs.json says what each picture is and which names it could not place.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'stories', 'jackson-ward'))
import views  # noqa: E402  (the story's view machinery; nothing in it is changed)
import labels as LB  # noqa: E402
from common import load, to_m  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402

BOX_W, BOX_H = 560, 330     # SVG units (2 per meter): about 280 m across
AHEAD = 40                  # units: the box's center sits this far up the picture from the point
Z = 1200 / BOX_W            # raster zoom, so each half is 1200 px wide
PX = 38                     # label type in the 1200 px pair (about 11 px on a 350 px phone column)
WARD_W = 3200               # the centerpiece's large copy, px
WARD_PX = 30                # its label type
SCENES = (('s1952', 1952, '1952'), ('s2026', 2026, 'Today'))
PLACE = {
    'belvidere-extension': 'W. Leigh St. at Brook Rd.',
    'gilpin-edge': 'Chamberlayne Ave. at Charity St.',
    'chamberlayne-bridge': 'Chamberlayne Pkwy. bridge',
    'sixth-mount-zion': 'W. Duval St., Sixth Mount Zion',
    'second-leigh': 'Second St. at Leigh St.',
    'first-bridge': 'North 1st St. bridge',
    'second-trench': 'Second St. at Duval St.',
    'bates-street': 'Second St. at Bates St.',
    'fifth-bridge': 'North 5th St. bridge',
}
UNTRACED = 'No buildings traced here:\nonly those standing today\nare drawn'
LATER = {'second-trench': [6037438]}
MARGIN = 8
NO_PAIR = {
    'coliseum': 'The Coliseum stands just past the near edge of the story\'s views, so their picture of today leaves it out '
                '(isoscape draws only buildings wholly inside the frame). A view framed further south was tried: the 1952 '
                'tracing stops partway across the Coliseum\'s site, and in Navy Hill the 1952 picture would draw today\'s '
                'streets, some laid out later, so this place has no picture of 1952.',
}

views.YEARS = tuple(s for s, _, _ in SCENES)
_FULL = {}


def full(work, scene, z):
    k = (scene, z)
    if k not in _FULL:
        im = Image.open(views.raster(work, scene, z)).convert('RGB')
        if scene == 's1952':
            im = views.untraced(im, work, scene, 1952, z, UNTRACED)
        _FULL[k] = im
    return _FULL[k]


def corner(work):
    (fx, fy, fw, fh), _ = views.frame(work)
    return fx, fy, fw, fh


def crop(work, scene, z, svg_box):
    fx, fy, _, _ = corner(work)
    x, y, w, h = svg_box
    return full(work, scene, z).crop((round((x - fx) * z), round((y - fy) * z), round((x - fx + w) * z), round((y - fy + h) * z)))


def marker(im, px, py, n, scale):
    d = ImageDraw.Draw(im)
    r = round(30 * scale)
    d.ellipse((px - r, py - r, px + r, py + r), fill=views.INK, outline=views.PAPER, width=max(3, round(5 * scale)))
    f = views.font(round(36 * scale))
    d.text((px, py), str(n), fill=views.PAPER, font=f, anchor='mm')


def band(im, n, year, place):
    """The half's label, in a paper band across its top: the number, the year large, the place."""
    d = ImageDraw.Draw(im)
    pad, yr, r = 18, 84, 34
    fy = views.font(yr)
    ps = 52
    room = im.width - (pad + 2 * r + 16 + d.textlength(year, font=fy) + 22 + pad)
    while ps > 40 and d.textlength(place, font=views.font(ps, bold=False)) > room:
        ps -= 2
    fp = views.font(ps, bold=False)
    assert d.textlength(place, font=fp) <= room, f'label does not fit: {place}'
    h = yr + 2 * pad - 6
    d.rectangle((0, 0, im.width, h), fill=views.PAPER)
    x = pad
    if n is not None:
        d.ellipse((pad, h / 2 - r, pad + 2 * r, h / 2 + r), fill=views.INK)
        d.text((pad + r, h / 2), str(n), fill=views.PAPER, font=views.font(44), anchor='mm')
        x = pad + 2 * r + 16
    d.text((x, h / 2), year, fill=views.INK, font=fy, anchor='lm')
    x += d.textlength(year, font=fy) + 22
    d.text((x, h / 2 + 4), place, fill=views.INK, font=fp, anchor='lm')
    return h


def later_top(work, ways, bx):
    """The highest point (smallest y, SVG units) of the given OSM ways inside the box's width."""
    ys = []
    for e in json.load(open(os.path.join(ROOT, 'data/richmond-streetcars/osm.json')))['elements']:
        if e['type'] == 'way' and e['id'] in ways:
            pts = []
            for a, b in zip(e['geometry'][:-1], e['geometry'][1:]):
                for t in [i / 20 for i in range(21)]:
                    pts.append(to_m(a['lon'] + (b['lon'] - a['lon']) * t, a['lat'] + (b['lat'] - a['lat']) * t))
            for x, y in LB.locate(work, 2026, pts):
                if bx[0] <= x <= bx[0] + bx[2] and y >= bx[1]:
                    ys.append(y)
    return min(ys) if ys else None


def draw_labels(im, placed, yoff=0):
    p = LB.Placer.__new__(LB.Placer)
    for t in placed:
        c, ang, s, italic, color = t[:5]
        LB.Placer.draw(p, im, (c[0], c[1] + yoff), ang, s, italic, PX_NOW[0], color, t[5] if len(t) > 5 else None)


PX_NOW = [PX]


def stack(halves, gap_div=120):
    gap = round(halves[0].width / gap_div)
    out = Image.new('RGB', (halves[0].width, sum(h.height for h in halves) + gap), views.PAPER)
    out.paste(halves[0], (0, 0))
    out.paste(halves[1], (0, halves[0].height + gap))
    return out


def frame_poly():
    corners = json.load(open(os.path.join(ROOT, 'out/stories/jackson-ward/data.json')))['corners']
    return Polygon([to_m(*c) for c in corners])


def pair(work, v, data, full_dir):
    sx, sy = LB.locate(work, 2026, [tuple(v['xy'])])[0]
    bx = (sx - BOX_W / 2, sy - BOX_H / 2 - AHEAD, BOX_W, BOX_H)
    if v['key'] in LATER:
        top = later_top(work, LATER[v['key']], bx)
        if top is not None and top < bx[1] + BOX_H:
            bx = (bx[0], top - MARGIN - BOX_H, BOX_W, BOX_H)
        assert bx[1] + 40 < sy < bx[1] + BOX_H - 30, f"point {v['n']}'s disc would leave its picture"
    band_h = 84 + 2 * 18 - 6
    halves, keep = [], [box(0, 0, 1200, band_h + 6)]
    spots = {}
    for scene, year, word in SCENES:
        x, y = LB.locate(work, year, [tuple(v['xy'])])[0]
        spots[year] = ((x - bx[0]) * Z, (y - bx[1]) * Z)
    keep += [Point(*spots[yr]).buffer(44) for yr in spots]
    PX_NOW[0] = PX
    placed, left, _ = LB.label_pair(work, bx, Z, PX, keep, frame_poly(), data)
    for scene, year, word in SCENES:
        im = crop(work, scene, Z, bx)
        draw_labels(im, placed[year])
        marker(im, *spots[year], v['n'], 1)
        band(im, v['n'], word, PLACE[v['key']])
        halves.append(im)
    out = stack(halves)
    name = f"jackson-ward-guide-pair-{v['n']}"
    out.save(os.path.join(ROOT, 'pages', name + '.webp'), quality=84, method=6)
    if full_dir:
        out.save(os.path.join(full_dir, name + '.png'), optimize=True)
    names = {yr: [p[2] for p in placed[yr]] for yr in placed}
    print('wrote', name, out.size, 'named 1952:', len(names[1952]), 'today:', len(names[2026]), 'left off:', left)
    italic = sorted({p[2] for p in placed[1952] if p[3]})
    return {'file': name + '.webp', 'box_svg': [round(t, 1) for t in bx], 'named': names, 'italic_1952': italic, 'left_off': left}


def ward(work, data, full_dir, width=WARD_W, px=WARD_PX, name='jackson-ward-guide-ward', page=True):
    """The whole ward, 1952 above and today below, with the streets named."""
    fx, fy, fw, fh = corner(work)
    z = round(width / fw, 4)
    bx = (fx, fy, fw, fh)
    PX_NOW[0] = px
    band_h = round(px * 3.6)
    keep = [box(0, 0, width, band_h + 6)]
    placed, left, _ = LB.label_pair(work, bx, z, px, keep, frame_poly(), data)
    halves = []
    for scene, year, word in SCENES:
        im = crop(work, scene, z, bx)
        draw_labels(im, placed[year])
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, im.width, band_h), fill=views.PAPER)
        fyr = views.font(round(px * 2.6))
        d.text((px * 0.6, band_h / 2), word, fill=views.INK, font=fyr, anchor='lm')
        sub = 'Jackson Ward, seen from the south, with the streets named'
        d.text((px * 0.6 + d.textlength(word, font=fyr) + px, band_h / 2 + px * 0.15), sub, fill=views.INK,
               font=views.font(round(px * 1.3), bold=False), anchor='lm')
        halves.append(im)
    out = stack(halves)
    if page:
        out.save(os.path.join(ROOT, 'pages', name + '-large.webp'), quality=84, method=6)
        out.resize((width // 2, round(out.height / 2)), Image.LANCZOS).save(os.path.join(ROOT, 'pages', name + '.webp'), quality=86, method=6)
    else:
        out.save(os.path.join(ROOT, 'out/stories/jackson-ward-guide', name + '.png'), optimize=True)
    if full_dir:
        out.save(os.path.join(full_dir, name + '.png'), optimize=True)
    names = {yr: sorted({p[2] for p in placed[yr]}) for yr in placed}
    italic = sorted({p[2] for p in placed[1952] if p[3]})
    print('wrote', name, out.size, 'named 1952:', len(names[1952]), 'today:', len(names[2026]), 'left off:', left)
    return {'file': name + '.webp', 'named': names, 'italic_1952': italic, 'left_off': left}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', default='/tmp/jw-views')
    ap.add_argument('--full', default=None)
    ap.add_argument('--only', default=None)
    a = ap.parse_args()
    if a.full:
        os.makedirs(a.full, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)
    for s, _, _ in SCENES:
        views.build(a.work, s)
    data = LB.load_data(frame_poly())
    LB.warm(a.work, data)
    V = load('vantage.json')['points']
    only = set(a.only.split(',')) if a.only else None
    made = json.load(open(os.path.join(HERE, 'pairs.json'))) if os.path.exists(os.path.join(HERE, 'pairs.json')) and only else {}
    if not only or 'ward' in only:
        made['ward'] = ward(a.work, data, a.full)
    if not only or 'sheet' in only:
        made['ward-sheet'] = ward(a.work, data, a.full, width=2400, px=36, name='jackson-ward-guide-ward-sheet', page=False)
    for v in V:
        if only and str(v['n']) not in only:
            continue
        if v['key'] in NO_PAIR:
            made[str(v['n'])] = {'file': None, 'why': NO_PAIR[v['key']]}
            continue
        made[str(v['n'])] = pair(a.work, v, data, a.full)
    json.dump(made, open(os.path.join(HERE, 'pairs.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
