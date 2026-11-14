import json, sys
import numpy as np
from PIL import Image
from ref import blocks
from register import overlay
geo, imgfmt, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
sheets = sys.argv[4:]
pts = blocks('../../data/sanborn/blocks.json', 1.0)
tiles = []
for sh in sheets:
    im = np.asarray(Image.open(imgfmt.format(sh=int(sh) if sh.isdigit() else sh)).convert('RGB')).astype(np.int16)
    overlay(im, pts, geo[sh]['params'], '/tmp/t.png', width=640, thick=2, grid=True)
    tiles.append(Image.open('/tmp/t.png').copy())
W = max(t.width for t in tiles); H = max(t.height for t in tiles)
M = Image.new('RGB', (W * 2, H * ((len(tiles) + 1) // 2)), 'white')
for i, t in enumerate(tiles): M.paste(t, ((i % 2) * W, (i // 2) * H))
M.save(out, quality=85)
