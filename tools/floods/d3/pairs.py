"""Floods series d3: every big plate beside its dry twin (and Manchester's headline beside the
same without the wall), one JPEG under 2 MB each, and a contact sheet of every plate per area.

    python3 tools/floods/d3/pairs.py <plates-dir> <out-dir>
"""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
F = lambda px: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', px)


def save(img, path):
    q = 88
    img.save(path, quality=q, optimize=True)
    while os.path.getsize(path) > 1_900_000 and q > 50:
        q -= 8; img.save(path, quality=q, optimize=True)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    plates = sorted(p for p in glob.glob(os.path.join(src, '*.png')) if not p.endswith('-dry.png'))
    for p in plates:
        twins = [p[:-4] + '-dry.png'] + ([p.replace('agnes-today.png', 'agnes-today-nowall.png')] if p.endswith('manchester-2026-flood-agnes-today.png') else [])
        for t, lab in zip(twins, ['dry twin: the same city with no flood', 'without the wall']):
            if not os.path.exists(t):
                continue
            a, b = Image.open(p).convert('RGB'), Image.open(t).convert('RGB')
            w = 1700
            a = a.resize((w, round(a.height * w / a.width)), Image.LANCZOS); b = b.resize((w, round(b.height * w / b.width)), Image.LANCZOS)
            img = Image.new('RGB', (2 * w + 16, max(a.height, b.height) + 40), 'white')
            d = ImageDraw.Draw(img)
            d.text((6, 6), 'the plate', font=F(24), fill=(40, 40, 40)); d.text((w + 22, 6), lab, font=F(24), fill=(40, 40, 40))
            img.paste(a, (0, 40)); img.paste(b, (w + 16, 40))
            name = os.path.basename(p)[:-4] + ('-pair-dry' if lab.startswith('dry twin') else '-pair-nowall') + '.jpg'
            save(img, os.path.join(out, name))
            print(name)
    for area in ('shockoe', 'manchester'):
        ps = sorted(glob.glob(os.path.join(src, f'richmond-floods-{area}-*.png')))
        if not ps:
            continue
        tw, cols = 760, 3
        tiles = []
        for p in ps:
            im = Image.open(p).convert('RGB'); im = im.resize((tw, round(im.height * tw / im.width)), Image.LANCZOS)
            t = Image.new('RGB', (tw, im.height + 26), 'white'); t.paste(im, (0, 26))
            ImageDraw.Draw(t).text((4, 4), os.path.basename(p)[len(f'richmond-floods-{area}-'):-4], font=F(17), fill=(40, 40, 40))
            tiles.append(t)
        th = max(t.height for t in tiles)
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * (tw + 10), rows * (th + 10) + 50), 'white')
        ImageDraw.Draw(sheet).text((6, 10), f'{area}: every plate (FINAL DRAFT rc3, 1.0.0-rc3)', font=F(26), fill=(40, 40, 40))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * (tw + 10), 50 + (i // cols) * (th + 10)))
        save(sheet, os.path.join(out, f'{area}-contact-sheet.jpg'))
        print(area, 'contact sheet', len(tiles))


if __name__ == '__main__':
    main(*sys.argv[1:])
