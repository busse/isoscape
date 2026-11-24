# Read the scanned 1998 FIS James River profile panel 03P (PDF p. 29) at 200 dpi.
import sys
from PIL import Image
import numpy as np
im = np.array(Image.open('/home/claude/floods-research/check/evidence/fis1998_p29_panel03P-29.png').convert('L')) < 128
H, W = im.shape
X0, PXK = 137.5, 198.2           # x pixel of 545,000 ft; pixels per 1,000 ft
Y0, PXF = 1294.0, 10.12          # y pixel of 0 ft NGVD29; pixels per foot
ft = lambda px: 545000 + (px - X0) / PXK * 1000
px = lambda f: X0 + (f - 545000) / 1000 * PXK
el = lambda y: (Y0 - y) / PXF
def leaders():
    out = []
    for x in range(140, 2510):
        c = im[300:800, x]
        if c.sum() > 120 and im[1300:1490, x].sum() < 150:  # long dark run in label zone, not a full grid line
            out.append(x)
    return out
def column(fx, half=1):
    x = int(round(px(fx)))
    c = im[700:1300, x-half:x+half+1].all(1)  # dark across the strip
    runs = []; y = 0
    while y < len(c):
        if c[y]:
            s = y
            while y < len(c) and c[y]: y += 1
            runs.append((s + 700, y - s + 0))
        y += 1
    return [(round(el(s + (n - 1) / 2), 2), n) for s, n in runs]
if __name__ == '__main__':
    if sys.argv[1] == 'leaders':
        L = leaders(); g = []
        for x in L:
            if g and x - g[-1][-1] <= 2: g[-1].append(x)
            else: g.append([x])
        for a in g: print(round(ft(sum(a)/len(a))), len(a))
    else:
        for f in map(float, sys.argv[1:]): print(int(f), column(f))
