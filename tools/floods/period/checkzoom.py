"""Today's streets (magenta) over each evidence crop at its registration, at a few places, for a look.
    python3 tools/floods/period/checkzoom.py <out.png>"""
import sys
from PIL import Image, ImageDraw
from common import Crop, streets
PLACES = [('shockoe', '17th and Main', (-77.4300, 37.5318, -77.4255, 37.5348)),
          ('shockoe', 'Tobacco Row', (-77.4235, 37.5262, -77.4190, 37.5292)),
          ('manchester', 'Hull and 7th', (-77.4400, 37.5215, -77.4355, 37.5245))]
rows = []
for area, name, (w, s, e, n) in PLACES:
    tiles = []
    for k in ['1974', '1999', '2002', '2017', '2021']:
        c = Crop(area, k)
        c0, r0 = c.pixel(w, n); c1, r1 = c.pixel(e, s)
        img = c.img.convert('RGB').crop((int(c0), int(r0), int(c1), int(r1)))
        d = ImageDraw.Draw(img)
        for _, lo, la in streets((w, s, e, n)):
            cc, rr = c.pixel(lo, la)
            d.line([(x - int(c0), y - int(r0)) for x, y in zip(cc, rr)], fill=(255, 0, 200), width=1)
        img = img.resize((360, round(360 * img.height / img.width)))
        ImageDraw.Draw(img).text((4, 4), f'{name} {k}', fill=(255, 255, 0))
        tiles.append(img)
    rows.append(tiles)
H = max(t.height for r in rows for t in r)
W = Image.new('RGB', (5 * 364, len(rows) * (H + 4)), 'white')
for j, r in enumerate(rows):
    for i, t in enumerate(r):
        W.paste(t, (i * 364, j * (H + 4)))
W.save(sys.argv[1])
