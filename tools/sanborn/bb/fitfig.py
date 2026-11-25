"""The fit, drawn: each street corner read off the sheet (red cross) and where today's corner
lands after the fit (blue ring), with the miss in meters."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '..')
from geo import to_m, w2i
geo, scan, sheet, out = sys.argv[1:5]; box = [int(v) for v in sys.argv[5].split(',')]
g = json.load(open(geo))[sheet]; osm = json.load(open('osm_corners.json'))
im = Image.open(scan).convert('RGB'); d = ImageDraw.Draw(im)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
for c in g['corners']:
    u, v = c['u'], c['v']; lon, lat = osm[c['label']]
    x, y = to_m([lon], [lat]); U, V = w2i(g['params'], np.stack([x, y], 1))[0]
    d.line([(u - 22, v - 22), (u + 22, v + 22)], fill=(220, 0, 0), width=7); d.line([(u - 22, v + 22), (u + 22, v - 22)], fill=(220, 0, 0), width=7)
    d.ellipse([U - 30, V - 30, U + 30, V + 30], outline=(0, 80, 230), width=7)
    t = f"{c['miss_m']:.1f} m"; tw = d.textlength(t, font=f)
    # labels near the sheet's right edge go to the left; Munford's goes above Broad
    ox, oy = 40, 30
    d.rectangle([u + ox, v + oy, u + ox + tw + 12, v + oy + 54], fill=(255, 255, 255)); d.text((u + ox + 6, v + oy + 4), t, fill=(0, 0, 0), font=f)
im.crop(box).save(out, quality=88)
