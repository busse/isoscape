#!/usr/bin/env python3
"""Framed-canvas files from a composed print: each face size the store sells, plus 1.5 in of
mirrored wrap per side for the canvas's sides, at 300 dpi (Printful's canvas print files).

The same files tools/sets/set.py writes for a set's prints (`write_canvas`), for a print made by
compose.py: the face is the whole print resized (Lanczos), the wrap is its edge mirrored, and the
file is saved at quality 92 (lower only if it would pass the store's 15 MB ceiling).

    python3 tools/print/canvas.py <print.jpg> <out-dir> 18x12 30x20 36x24

Writes <out-dir>/<stem>_canvas-<w>x<h>.jpg, where <stem> is the print's name before _<size>.jpg.
"""
import argparse, os, re
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
WRAP = 1.5                  # inches of mirrored image around each face (as set.py and stamp.py)
DPI = 300
MAX_BYTES = 15_000_000      # the store's upload ceiling for a print file


def canvas_name(print_name, w, h):
    stem = re.match(r'(.+?)_\d+x\d+\.jpg$', print_name).group(1)
    return f'{stem}_canvas-{w}x{h}.jpg'


def write(print_path, out_dir, sizes):
    base = Image.open(print_path).convert('RGB')
    wrap_px = int(WRAP * DPI)
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for fw, fh in sizes:
        face = np.asarray(base.resize((fw * DPI, fh * DPI), Image.LANCZOS))
        img = Image.fromarray(np.pad(face, ((wrap_px, wrap_px), (wrap_px, wrap_px), (0, 0)), mode='symmetric'))
        p = os.path.join(out_dir, canvas_name(os.path.basename(print_path), fw, fh))
        for q in (92, 88, 84, 80, 76):
            img.save(p, quality=q, dpi=(DPI, DPI), optimize=True)
            if os.path.getsize(p) <= MAX_BYTES: break
        print(os.path.basename(p), img.size, f'{os.path.getsize(p) / 1e6:.1f} MB q{q}', flush=True)
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('print'); ap.add_argument('out'); ap.add_argument('sizes', nargs='+', help='face sizes in inches, WxH')
    a = ap.parse_args()
    write(a.print, a.out, [tuple(map(int, s.split('x'))) for s in a.sizes])


if __name__ == '__main__':
    main()
