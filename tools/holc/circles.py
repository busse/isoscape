"""Find the printed area-label circles on the scan, and make a numbered contact sheet of them.

    python3 -I circles.py <scan.jpg> <circles.json> <sheet.png>

Circles are found with OpenCV's Hough transform on a quarter-size gray copy (radius 70 to 115
px at full size), then kept only where the ring is dark and the inside mostly light. The sheet
shows each circle's crop with its index, for reading the printed label into labels.json.
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None


def find(gray):
    q = cv2.resize(gray, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    q = cv2.GaussianBlur(q, (3, 3), 0)
    cs = cv2.HoughCircles(q, cv2.HOUGH_GRADIENT, dp=1, minDist=30, param1=120, param2=28,
                          minRadius=17, maxRadius=29)
    out = []
    if cs is None:
        return out
    for x, y, r in cs[0]:
        X, Y, R = x * 4, y * 4, r * 4
        th = np.linspace(0, 2 * np.pi, 180, endpoint=False)
        ring = []
        for dr in (-6, -3, 0, 3, 6):
            px = np.clip((X + (R + dr) * np.cos(th)).astype(int), 0, gray.shape[1] - 1)
            py = np.clip((Y + (R + dr) * np.sin(th)).astype(int), 0, gray.shape[0] - 1)
            ring.append(gray[py, px])
        ring = np.min(np.stack(ring), 0)
        dark = float((ring < 110).mean())
        if dark < 0.8:
            continue
        out.append({'x': round(float(X)), 'y': round(float(Y)), 'r': round(float(R)), 'ring_dark': round(dark, 2)})
    out.sort(key=lambda c: (c['y'] // 400, c['x']))
    return out


if __name__ == '__main__':
    src, js, sheet = sys.argv[1:4]
    im = Image.open(src).convert('RGB')
    gray = np.asarray(im.convert('L'))
    cs = find(gray)
    for i, c in enumerate(cs):
        c['i'] = i
    json.dump(cs, open(js, 'w'), indent=1)
    t, cols = 220, 10
    rows = (len(cs) + cols - 1) // cols
    S = Image.new('RGB', (cols * t, rows * (t + 20)), 'white')
    d = ImageDraw.Draw(S)
    for i, c in enumerate(cs):
        R = int(c['r'] * 1.3)
        cr = im.crop((c['x'] - R, c['y'] - R, c['x'] + R, c['y'] + R)).resize((t - 10, t - 10))
        S.paste(cr, ((i % cols) * t + 5, (i // cols) * (t + 20) + 20))
        d.text(((i % cols) * t + 5, (i // cols) * (t + 20) + 4), f"#{i} ({c['x']},{c['y']})", fill='red')
    S.save(sheet)
    print(len(cs), 'circles')
