"""Split the scan into regions bounded by the map's heavy lines, and give each region a grade.

    python3 -I segment.py <scan.jpg> <out.npz> [<preview.png>]

1. Every pixel is classed as ink (gray < INK), or by nearest color among the legend's four
   swatches and the bare paper (sampled from the scan itself, in CIE Lab).
2. Heavy lines (area boundaries, label circles) are what survives an opening of the ink with an
   ellipse HEAVY px across; street lines, lettering and most hatching are thinner and drop out.
3. For each grade, its pixels are cleaned (opening OPEN, closing CLOSE, which fills lettering
   and thin street lines), cut along the heavy lines, and split into connected pieces.
Writes the piece label image (int32, 0 = none) with each piece's grade and pixel count.
"""
import sys

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
INK = 105          # gray level below which a pixel is ink
HEAVY = 17         # px; boundaries are ~19-24 px wide at 400 ppi, hatching ~12-15
CLOSE = 19         # px; fills lettering, street lines and the sparse-settlement hatching inside a tint
OPEN = 5
MIN_PX = 1500      # px; smaller pieces are speckle (about 0.35 ha)
SWATCH = {'A': (940, 5045), 'B': (940, 5197), 'C': (940, 5350), 'D': (940, 5500), 'paper': (1500, 6400)}
CLASSES = ['paper', 'A', 'B', 'C', 'D']


def main(src, out, preview=None):
    rgb = np.asarray(Image.open(src).convert('RGB'))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    cent = {}
    for k, (x, y) in SWATCH.items():
        patch = cv2.cvtColor(np.ascontiguousarray(rgb[y - 15:y + 15, x - 40:x + 40]), cv2.COLOR_RGB2LAB)
        cent[k] = np.median(patch.reshape(-1, 3), 0).astype(np.float32)
        print(k, cent[k])
    ink = gray < INK
    # class by nearest center, weighting chroma (a, b) above lightness; in bands of rows
    w = np.array([0.5, 1.0, 1.0], np.float32)
    C = np.stack([cent[k] for k in CLASSES]) * w
    cls = np.zeros(gray.shape, np.uint8)
    for y0 in range(0, gray.shape[0], 256):
        lab = cv2.cvtColor(np.ascontiguousarray(rgb[y0:y0 + 256]), cv2.COLOR_RGB2LAB).astype(np.float32) * w
        d = ((lab[:, :, None, :] - C[None, None]) ** 2).sum(-1)
        cls[y0:y0 + 256] = np.argmin(d, -1)
    cls[ink] = 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (HEAVY, HEAVY))
    heavy = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_OPEN, k)
    heavy = cv2.dilate(heavy, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    # pieces: per grade, fill lettering and thin lines (closing), drop speckle (opening),
    # cut along the heavy lines, then take connected parts of at least MIN_PX
    lbl = np.zeros(gray.shape, np.int32)
    grades, sizes = [0], [0]
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (CLOSE, CLOSE))
    ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (OPEN, OPEN))
    for gi, g in enumerate('ABCD', start=1):
        m = (cls == gi).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, ko)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kc)
        m[heavy > 0] = 0
        n, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        for j in range(1, n):
            if st[j, cv2.CC_STAT_AREA] < MIN_PX:
                continue
            lbl[cc == j] = len(grades)
            grades.append(gi)
            sizes.append(int(st[j, cv2.CC_STAT_AREA]))
        print(g, 'pieces so far', len(grades) - 1)
    np.savez_compressed(out, lbl=lbl, grade=np.array(grades, np.int8), size=np.array(sizes), heavy=heavy.astype(bool),
                        paper=(cls == 0))
    if preview:
        rng = np.random.default_rng(1)
        pal = np.array([[235, 235, 230], [90, 170, 80], [80, 150, 210], [230, 210, 60], [220, 90, 100]], np.int16)
        cols = np.clip(pal[np.array(grades)] + rng.integers(-35, 35, (len(grades), 3)), 0, 255).astype(np.uint8)
        cols[0] = (235, 235, 230)
        img = cols[lbl]
        img[heavy > 0] = 0
        Image.fromarray(img).resize((rgb.shape[1] // 4, rgb.shape[0] // 4), Image.NEAREST).save(preview)


if __name__ == '__main__':
    main(*sys.argv[1:])
