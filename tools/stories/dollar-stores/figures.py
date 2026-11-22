#!/usr/bin/env python3
"""Write the story page's pictures into pages/ from the poster's vector PDF.

    python3 tools/stories/dollar-stores/figures.py <poster.pdf>

Writes dollar-stores-poster.webp (+ -large), dollar-stores-tiles.webp (+ -large),
dollar-stores-charts.webp (+ -large) and dollar-stores-social.jpg (1200 x 630, maps only).
Crops are in inches on the 24 x 36 in sheet. Made with Claude.
"""
import io
import os
import sys

import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'pages'))
CROPS = {  # name: (x0, y0, x1, y1) in inches, normal width px, large width px
    'poster': ((0, 0, 24, 36), 1400, 3600),
    'tiles': ((0.8, 6.6, 23.2, 13.97), 1600, 3600),
    'charts': ((0.8, 26.05, 23.2, 32.6), 1600, 3600),
}


def render(doc, box, width):
    x0, y0, x1, y1 = box
    zoom = width / ((x1 - x0) * 72)
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=pymupdf.Rect(x0 * 72, y0 * 72, x1 * 72, y1 * 72))
    return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')


def main():
    doc = pymupdf.open(sys.argv[1])
    for name, (box, w, wl) in CROPS.items():
        render(doc, box, w).save(f'{PAGES}/dollar-stores-{name}.webp', quality=82, method=6)
        render(doc, box, wl).save(f'{PAGES}/dollar-stores-{name}-large.webp', quality=80, method=6)
    # link preview: the first two maps of the grid with their captions, no other sheet text
    render(doc, (0.97, 6.93, 7.47, 10.342), 1200).resize((1200, 630)).save(f'{PAGES}/dollar-stores-social.jpg', quality=88)
    for f in sorted(os.listdir(PAGES)):
        if f.startswith('dollar-stores-'):
            print(f, os.path.getsize(f'{PAGES}/{f}'))


if __name__ == '__main__':
    main()
