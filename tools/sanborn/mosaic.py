"""Contact sheets for picking control points by eye: each sheet scaled down with a labeled
pixel grid (in the 25% scan's own pixels), four to an image."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, files = sys.argv[1], sys.argv[2:]
TW = 760
tiles = []
for f in files:
    im = Image.open(f).convert('RGB')
    s = TW / im.width
    t = im.resize((TW, int(im.height * s)))
    d = ImageDraw.Draw(t)
    for g in range(0, max(im.width, im.height), 200):
        x = g * s
        d.line([(x, 0), (x, t.height)], fill=(0, 140, 255), width=1)
        d.line([(0, x), (t.width, x)], fill=(0, 140, 255), width=1)
        d.text((x + 2, 2), str(g), fill=(0, 90, 220))
        d.text((2, x + 2), str(g), fill=(0, 90, 220))
    d.text((TW - 160, t.height - 14), f.split('/')[-1], fill=(220, 0, 0))
    tiles.append(t)
H = max(t.height for t in tiles)
cols = 2
rows = (len(tiles) + 1) // 2
M = Image.new('RGB', (TW * cols, H * rows), 'white')
for i, t in enumerate(tiles):
    M.paste(t, ((i % cols) * TW, (i // cols) * H))
M.save(out, quality=88)
