"""Today's street center lines (OpenStreetMap) over a fitted Sanborn sheet, for callout A."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '..')
from geo import to_m, w2i
geo, scan, osm, sheet, out = sys.argv[1:6]; box = [int(v) for v in sys.argv[6].split(',')]
names = {'North Belvidere Street': (0, 90, 255), 'Smith Street': (230, 120, 0), 'South Belvidere Street': (0, 90, 255)}
p = json.load(open(geo))[sheet]['params']
im = Image.open(scan).convert('RGB'); d = ImageDraw.Draw(im, 'RGBA')
for e in json.load(open(osm))['elements']:
    t = e.get('tags', {})
    if e.get('type') != 'way' or t.get('name') not in names or 'geometry' not in e: continue
    g = np.array([[q['lon'], q['lat']] for q in e['geometry']]); x, y = to_m(g[:, 0], g[:, 1])
    uv = w2i(p, np.stack([x, y], 1)); d.line([tuple(q) for q in uv], fill=names[t['name']] + (230,), width=9)
c = im.crop(box); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
dc = ImageDraw.Draw(c)
dc.rectangle([10, 10, 760, 110], fill=(255, 255, 255, 230)); dc.text((24, 18), 'blue: North Belvidere St. today', fill=(0, 70, 220), font=f); dc.text((24, 62), 'orange: Smith St. today', fill=(210, 100, 0), font=f)
c.save(out, quality=88)
