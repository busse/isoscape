# Overlay a 0.1-mile by 1-ft grid on HA-410 Figure 1 (300 dpi render) to read points by eye.
import sys
from PIL import Image, ImageDraw
src, out, m0, m1, e0, e1, scale = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8])
im = Image.open(src).convert('RGB')
px = lambda mi: 77 + (109.0 - mi) * 170.8
py = lambda ft: 1483.5 - (ft - 20.0) * 17.16
box = (int(px(m0)), int(py(e1)), int(px(m1)), int(py(e0)))
c = im.crop(box); c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
d = ImageDraw.Draw(c)
X = lambda mi: (px(mi) - box[0]) * scale; Y = lambda ft: (py(ft) - box[1]) * scale
mi = round(m0, 1)
while mi >= m1 - 1e-9:
    w = 2 if abs(mi * 2 - round(mi * 2)) < 1e-6 else 1
    d.line([(X(mi), 0), (X(mi), c.height)], fill=(255, 0, 0) if w == 2 else (255, 150, 150), width=1)
    if w == 2: d.text((X(mi) + 2, 2), f"{mi:.1f}", fill=(200, 0, 0))
    mi = round(mi - 0.1, 1)
ft = int(e0)
while ft <= e1:
    w = ft % 5 == 0
    d.line([(0, Y(ft)), (c.width, Y(ft))], fill=(0, 0, 255) if w else (150, 150, 255), width=1)
    if w: d.text((2, Y(ft) - 12), f"{ft}", fill=(0, 0, 200))
    ft += 1
c.save(out)
print(c.size)
