#!/usr/bin/env python3
"""Contact sheets of a story PDF, to look at every page before it goes out.

    python3 tools/pdf/look.py <file.pdf> --out DIR [--sample 1,12,40] [--phone-width 390]

Writes DIR/<name>-sheet-1.jpg … (every page small, 60 to a sheet, numbered), DIR/<name>-page-N.png
for each sampled page at full size (150 dpi), and with --phone-width, DIR/<name>-phone-N.png: the
sampled pages at that width in pixels, as a phone shows them fitted to its screen. Needs
pdftoppm (poppler-utils) and ImageMagick's montage. Page rasters are made in a scratch folder
and removed.
"""
import argparse
import glob
import os
import shutil
import subprocess
import tempfile


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--out', required=True)
    ap.add_argument('--sample', default='')
    ap.add_argument('--phone-width', type=int, default=0)
    ap.add_argument('--per-sheet', type=int, default=60)
    a = ap.parse_args()
    name = os.path.splitext(os.path.basename(a.pdf))[0]
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='look-')
    try:
        subprocess.run(['pdftoppm', '-scale-to', '300', '-jpeg', a.pdf, os.path.join(tmp, 'p')], check=True)
        pages = sorted(glob.glob(os.path.join(tmp, 'p-*.jpg')))
        cols = 12 if a.per_sheet >= 60 else 10
        for i in range(0, len(pages), a.per_sheet):
            chunk = pages[i:i + a.per_sheet]
            labelled = []
            for k, p in enumerate(chunk):
                labelled += ['-label', str(i + k + 1), p]
            subprocess.run(['montage', *labelled, '-tile', f'{cols}x', '-geometry', '+6+6', '-pointsize', '14',
                            '-background', '#9a9a9a', '-quality', '82', os.path.join(a.out, f'{name}-sheet-{i // a.per_sheet + 1}.jpg')], check=True)
        for n in [int(x) for x in a.sample.split(',') if x.strip()]:
            subprocess.run(['pdftoppm', '-r', '150', '-f', str(n), '-l', str(n), '-singlefile', '-png', a.pdf,
                            os.path.join(a.out, f'{name}-page-{n}')], check=True)
            if a.phone_width:
                subprocess.run(['pdftoppm', '-scale-to-x', str(a.phone_width), '-scale-to-y', '-1', '-f', str(n), '-l', str(n),
                                '-singlefile', '-png', a.pdf, os.path.join(a.out, f'{name}-phone-{n}')], check=True)
        print(f'{a.pdf}: {len(pages)} pages, sheets in {a.out}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
