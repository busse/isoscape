#!/usr/bin/env python3
"""The guide's 1952-and-today pairs: for each stop, the same frame cut from the story's 1952
view and its view of today, stacked, each labeled inside the picture with its year and place.

    python3 tools/stories/jackson-ward-guide/pairs.py [--work DIR] [--full DIR]

The scenes are the story's own (tools/stories/jackson-ward/views.py: `jackson-ward --year 1952`
and `--year 2026`, built once into --work with that script's `build`). The two SVGs share one
drawing space; views.py's `framed` sets both to one viewBox, so a crop is the same box in both,
cut from rasters made by views.py's `raster`. The 1952 half carries the story's hatch over the
blocks no sheet was traced for (views.py's `untraced`), as the story's own 1952 view does. A stop's place on the picture comes from views.py's `_fit` (the
affine from the ground to the drawing, fitted on the traced buildings, good to a few meters),
and the box is centered a little beyond the stop, toward the far edge, since the views look
north. Writes pages/jackson-ward-guide-pair-<n>.webp (1200 px wide) and, with --full, a PNG
of each for review. A stop the views cannot show (NO_PAIR: the Coliseum) gets no pair, and pairs.json
says why.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'stories', 'jackson-ward'))
import views  # noqa: E402  (the story's view machinery; nothing in it is changed)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

BOX_W, BOX_H = 560, 330     # SVG units (2 per meter): about 280 m across
AHEAD = 40                  # units: the box's center sits this far up the picture from the stop
Z = 1200 / BOX_W            # raster zoom, so each half is 1200 px wide
SCENES = (('s1952', '1952'), ('s2026', 'Today'))
# The short place name each half carries in its label; the stop's full title goes in the caption.
PLACE = {
    'second-leigh': 'Second St. at Leigh St.',
    'second-trench': 'Second St. at Duval St.',
    'sixth-mount-zion': 'Sixth Mount Zion',
    'chamberlayne-bridge': 'Chamberlayne Pkwy. bridge',
    'gilpin-edge': 'Chamberlayne Ave. at Charity St.',
    'bates-street': 'Second St. at Bates St.',
    'first-bridge': 'North 1st St. bridge',
}
UNTRACED = 'No buildings traced here:\nonly those standing today\nare drawn'
# Stops with no pair, and why (said in route.json's stop and on the page).
NO_PAIR = {
    'coliseum': 'The Coliseum stands at the near edge of the story\'s views, so their picture of today leaves it out '
                '(isoscape draws only buildings wholly inside the frame), and the 1952 sheets were not traced for its blocks.',
}

views.YEARS = tuple(s for s, _ in SCENES)   # the shared frame of just these two scenes


def place(work, lon, lat):
    """A point's place in the reference scene's drawing, in SVG units from its viewBox corner."""
    A = views._fit(views.build(work, views.REF))
    x, y = views.to_m(lon, lat)
    p = np.array([float(x), float(y), 1.0]) @ A
    return float(p[0]), float(p[1])


_FULL = {}


def full(work, scene):
    """The whole scene in the shared frame at zoom Z; the 1952 one with the story's hatch over
    the blocks no sheet was traced for (views.untraced), as on the story page."""
    if scene not in _FULL:
        im = Image.open(views.raster(work, scene, Z)).convert('RGB')
        if scene == 's1952':
            im = views.untraced(im, work, scene, 1952, Z, UNTRACED)
        _FULL[scene] = im
    return _FULL[scene]


def marker(im, px, py, n, scale):
    d = ImageDraw.Draw(im)
    r = round(30 * scale)
    d.ellipse((px - r, py - r, px + r, py + r), fill=views.INK, outline=views.PAPER, width=max(3, round(5 * scale)))
    f = views.font(round(36 * scale))
    tw, th = d.textbbox((0, 0), str(n), font=f)[2:]
    d.text((px - tw / 2, py - th / 2 - round(2 * scale)), str(n), fill=views.PAPER, font=f)


def label(im, n, year, place):
    """The half's label, in a paper band across its top: the stop's number in a disc, the year
    large, then the short place name. Sized for the pair shown about 350 px wide on a phone
    (the image is 1200 px), so the year reads at about 25 px and the place at 15 px or more;
    the place is made smaller only to fit, never under 13 px on the phone, and never cut."""
    d = ImageDraw.Draw(im)
    pad, yr = 18, 84
    fy = views.font(yr)
    r = 34
    ps = 52
    room = im.width - (pad + 2 * r + 16 + d.textlength(year, font=fy) + 22 + pad)
    while ps > 44 and d.textlength(place, font=views.font(ps, bold=False)) > room:
        ps -= 2
    fp = views.font(ps, bold=False)
    assert d.textlength(place, font=fp) <= room, f'label does not fit: {place}'
    band = yr + 2 * pad - 6
    d.rectangle((0, 0, im.width, band), fill=views.PAPER)
    cx, cy = pad + r, band / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=views.INK)
    d.text((cx, cy), str(n), fill=views.PAPER, font=views.font(44), anchor='mm')
    x = pad + 2 * r + 16
    d.text((x, cy), year, fill=views.INK, font=fy, anchor='lm')
    x += d.textlength(year, font=fy) + 22
    d.text((x, cy + 4), place, fill=views.INK, font=fp, anchor='lm')
    return band


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', default='/tmp/jw-views')
    ap.add_argument('--full', default=None)
    a = ap.parse_args()
    route = json.load(open(os.path.join(HERE, 'route.json')))
    off = views.frame(a.work)[1]
    made = {}
    for st in route['stops']:
        if st['key'] in NO_PAIR:
            made[st['n']] = {'file': None, 'why': NO_PAIR[st['key']]}
            print('no pair for stop', st['n'])
            continue
        sx, sy = place(a.work, st['lon'], st['lat'])
        box = (sx - BOX_W / 2, sy - BOX_H / 2 - AHEAD, BOX_W, BOX_H)
        halves = []
        for scene, word in SCENES:
            im = full(a.work, scene).crop(
                (round((box[0] + off[0]) * Z), round((box[1] + off[1]) * Z), round((box[0] + off[0] + BOX_W) * Z), round((box[1] + off[1] + BOX_H) * Z)))
            marker(im, (sx - box[0]) * Z, (sy - box[1]) * Z, st['n'], im.width / 1200)
            label(im, st['n'], word, PLACE[st['key']])
            halves.append(im)
        gap = round(halves[0].width / 120)
        out = Image.new('RGB', (halves[0].width, sum(h.height for h in halves) + gap), views.PAPER)
        out.paste(halves[0], (0, 0))
        out.paste(halves[1], (0, halves[0].height + gap))
        name = f'jackson-ward-guide-pair-{st["n"]}'
        out.save(os.path.join(ROOT, 'pages', name + '.webp'), quality=84, method=6)
        if a.full:
            os.makedirs(a.full, exist_ok=True)
            out.save(os.path.join(a.full, name + '.png'), optimize=True)
        made[st['n']] = {'file': name + '.webp', 'box_svg_units': [round(v, 1) for v in box]}
        print('wrote', name, out.size)
    json.dump(made, open(os.path.join(HERE, 'pairs.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
