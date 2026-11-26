"""Before and after pictures for the period city: for each plate built into two folders, the
full plate side by side, and crops at named places (lon/lat, a width in SVG units), each pair
labeled, saved as JPEG under about 2 MB.

    python3 tools/floods/period/crops.py <before-dir> <after-dir> <out-dir> [label-before] [label-after]
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PLACES = {
    'shockoe': [('bottom', (-77.4282, 37.5322), 1100), ('testblock', (-77.4266, 37.5345), 240)],
    'manchester': [('flats', (-77.4335, 37.5222), 1100)],
}


def locate(region, pts):
    out = subprocess.run(['node', 'bin/isoscape.js', 'locate', region, '--', *[f'{x},{y}' for x, y in pts]], cwd=ROOT, capture_output=True, text=True).stdout
    return [(p['x'], p['y']) for p in json.loads(out)]


def viewbox(svg):
    head = open(svg, 'rb').read(600).decode('utf8', 'replace')
    return [float(v) for v in re.search(r'viewBox="([^"]+)"', head).group(1).split()]


def crop(png, svg, cx, cy, w, aspect=0.62):
    vb = viewbox(svg)
    im = Image.open(png)
    k = im.width / vb[2]
    h = w * aspect
    box = (round((cx - w / 2 - vb[0]) * k), round((cy - h / 2 - vb[1]) * k), round((cx + w / 2 - vb[0]) * k), round((cy + h / 2 - vb[1]) * k))
    return im.crop(box).convert('RGB')


def vector_crop(svg, cx, cy, w, px=1100, aspect=0.62):
    """A close-up drawn from the SVG itself (its viewBox narrowed), not cut from the PNG."""
    import tempfile
    h = w * aspect
    text = open(svg, encoding='utf8').read()
    text = re.sub(r'viewBox="[^"]+"', f'viewBox="{cx - w / 2} {cy - h / 2} {w} {h}"', text, count=1)
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'c.svg'), os.path.join(d, 'c.png')
        open(a, 'w', encoding='utf8').write(text)
        subprocess.run(['rsvg-convert', '-w', str(px), '-o', b, a], check=True)
        return Image.open(b).convert('RGB')


def pair(a, b, la, lb, width):
    a = a.resize((width, round(a.height * width / a.width)), Image.LANCZOS)
    b = b.resize((width, round(b.height * width / b.width)), Image.LANCZOS)
    W = Image.new('RGB', (2 * width + 12, max(a.height, b.height) + 34), (255, 255, 255))
    W.paste(a, (0, 34)); W.paste(b, (width + 12, 34))
    d = ImageDraw.Draw(W)
    try:
        f = ImageFont.truetype('DejaVuSans.ttf', 20)
    except OSError:
        f = ImageFont.load_default()
    d.text((6, 6), la, fill=(0, 0, 0), font=f); d.text((width + 18, 6), lb, fill=(0, 0, 0), font=f)
    return W


def save(img, path):
    q = 88
    while True:
        img.save(path, quality=q, optimize=True)
        if os.path.getsize(path) < 1_900_000 or q <= 50:
            return
        q -= 8


def main(before, after, out, la='before (d2)', lb='after (period city from evidence)'):
    os.makedirs(out, exist_ok=True)
    for png in sorted(f for f in os.listdir(after) if f.endswith('.png')):
        name = png[:-4]
        area = 'shockoe' if 'shockoe' in name else 'manchester'
        A = os.path.join(before, png); B = os.path.join(after, png)
        if not os.path.exists(A):
            continue
        sa, sb = A[:-4] + '.svg', B[:-4] + '.svg'
        save(pair(Image.open(A).convert('RGB'), Image.open(B).convert('RGB'), la, lb, 1500), os.path.join(out, f'{name}-full.jpg'))
        places = PLACES[area]
        xy = locate(f'richmond-floods-{area}', [p[1] for p in places])
        for (tag, _, w), (cx, cy) in zip(places, xy):
            if w > 500:
                save(pair(crop(A, sa, cx, cy, w), crop(B, sb, cx, cy, w), la, lb, 1400), os.path.join(out, f'{name}-{tag}.jpg'))
            else:
                save(pair(vector_crop(sa, cx, cy, w), vector_crop(sb, cx, cy, w), la, lb, 1100), os.path.join(out, f'{name}-{tag}.jpg'))
        print(name)


if __name__ == '__main__':
    main(*sys.argv[1:])
