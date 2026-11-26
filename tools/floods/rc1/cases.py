"""Floods series rc1: a contact sheet of cases to look at, each a crop of its plate's SVG around
the point given, labeled.

    python3 tools/floods/rc1/cases.py order <occlusion.json> <area> <plates-dir> <out.jpg>
    python3 tools/floods/rc1/cases.py covered <covered.json> <area> <plates-dir> <out.jpg> [n]

`order`: every distinct pair the painted-over check (tools/floods/d3/occlusion.ts) still lists
as `order`, on the first plate it is found on (a 60 by 40 unit window at 10 px a unit, the
point ringed). `covered`: the n traced footprints (default 24) with the most area under
today's buildings on each plate of covered.json (tools/floods/rc1/covered.ts), with their share.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'd3'))
import render_boxes as RB  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
RED = (200, 30, 30)


def tile(svg, at, w, h, px, label):
    im = RB.crop(svg, at[0], at[1], w, h, px)
    d = ImageDraw.Draw(im)
    cx, cy, r = im.width / 2, im.height / 2, im.width / 14
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED, width=2)
    t = Image.new('RGB', (im.width, im.height + 44), 'white')
    t.paste(im, (0, 44))
    dd = ImageDraw.Draw(t)
    for j, ln in enumerate(label.split('\n')[:2]):
        dd.text((4, 2 + j * 20), ln, fill=(20, 20, 20), font=FONT)
    return t


def grid(tiles, cols, title, out):
    tw, th = tiles[0].width, max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    s = Image.new('RGB', (cols * (tw + 8), rows * (th + 8) + 40), 'white')
    ImageDraw.Draw(s).text((6, 10), title, fill=(20, 20, 20), font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * (tw + 8), 40 + (i // cols) * (th + 8)))
    q = 88
    s.save(out, quality=q)
    while os.path.getsize(out) > 1_950_000 and q > 50:
        q -= 8; s.save(out, quality=q)
    print(out, len(tiles), 'cases', s.size)


def main(kind, src, area, plates, out, n='24'):
    data = json.load(open(src))
    region = f'richmond-floods-{area}'
    tiles = []
    if kind == 'order':
        seen = {}
        for p, v in data.items():
            for c in v['cases']:
                if c['kind'] != 'order':
                    continue
                k = (c['over'], c['under'])
                seen.setdefault(k, (p, c, []))[2].append(p)
        for (over, under), (p, c, ps) in seen.items():
            fl, yr = p.split(':')
            svg = os.path.join(plates, f'{region}-{yr}-flood-{fl}.svg')
            tiles.append(tile(svg, c['at'], 60, 40, 600, f"{c['kinds']}: {over} over {under}\nby {c['by']} m, {c['area']} sq units; {len(ps)} plate(s), first {p}"))
        title = f'{area}: every painted-over case still listed (rc1), {len(tiles)} distinct pairs'
    else:
        for p, v in data.items():
            fl, yr = p.split(':')
            svg = os.path.join(plates, f'{region}-{yr}-flood-{fl}.svg')
            for r in v['rows'][:int(n)]:
                tiles.append(tile(svg, r['at'], 80, 54, 600, f"{p} {r['id']}\n{round(r['share'] * 100)}% under today's buildings, {r['m2']} m²"))
        title = f"{area}: traced footprints still partly under today's buildings (under half: drawn), largest first"
    grid(tiles, 4, title, out)


if __name__ == '__main__':
    main(*sys.argv[1:])
