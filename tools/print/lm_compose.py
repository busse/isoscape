#!/usr/bin/env python3
"""Landmark print files: one 24x36 (3:2) file per landmark, under MAX bytes so the browser upload
(3.8 MB cap) can take it. Crops each scene to its drawn content, keeps the landmark central.
Usage: lm_compose.py <list.json> <svg-dir> <out-dir> [slug...]"""
import io, json, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C
Image.MAX_IMAGE_PIXELS = None
MAX = 15_000_000
CREDIT = 'isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  Elevation: USGS 3DEP'

def content_box(svg, zoom=True):
    s = open(svg, encoding='utf-8').read(3000)
    vb = list(map(float, re.search(r'viewBox="([^"]+)"', s).group(1).split()))
    with tempfile.TemporaryDirectory() as t:
        src = open(svg, encoding='utf-8').read()
        src = re.sub(r'<g class="caption".*?</g>', '', src, flags=re.S)
        p = os.path.join(t, 'a.svg'); open(p, 'w', encoding='utf-8').write(src)
        C.svg_to_png(p, os.path.join(t, 'a.png'), 800)
        a = np.asarray(Image.open(os.path.join(t, 'a.png')).convert('RGBA'))
    mask = a[..., 3] > 20
    ys, xs = np.where(mask)
    k = vb[2] / a.shape[1]
    x0, x1 = vb[0] + xs.min() * k, vb[0] + (xs.max() + 1) * k
    y0, y1 = vb[1] + ys.min() * k, vb[1] + (ys.max() + 1) * k
    rgb = a[..., :3].astype(int)
    # trim the slab face: bottom rows that are mostly the slab's flat tan
    slab = (np.abs(rgb - np.array([203, 191, 165])).sum(-1) < 40) & mask
    r = int(ys.max()) - 4   # skip the outline at the very bottom
    while r > ys.min() and mask[r].sum() > 0 and slab[r].sum() > 0.35 * mask[r].sum(): r -= 1
    y1 = vb[1] + (r + 1) * k
    y1 -= (y1 - y0) * 0.01
    water = (rgb[..., 2] > rgb[..., 0] + 25) & mask
    land = mask & ~water
    if zoom and land.sum() < 0.25 * mask.sum():   # mostly water: zoom to the land, with room around it
        ly, lx = np.where(land)
        cx, cy = vb[0] + lx.mean() * k, vb[1] + ly.mean() * k
        lw = (np.percentile(lx, 97) - np.percentile(lx, 3)) * k; lh = (np.percentile(ly, 97) - np.percentile(ly, 3)) * k
        w = max(lw * 1.9, lh * 1.9 * 1.5, (x1 - x0) * 0.35); h = w / 1.5
        bx0, by0 = max(x0, cx - w / 2), max(y0, cy - h / 2)
        bx1, by1 = min(x1, cx + w / 2), min(y1, cy + h / 2)
        return [bx0, by0, bx1 - bx0, by1 - by0]
    return [x0, y0, x1 - x0, y1 - y0]

def make(slug, title, place, svg, out_dir, landscape=True, zoom=True, anchor=None):
    """zoom=False keeps the whole scene even when it is mostly water (a frame drawn to hold shore and
    water together); anchor='left' or 'top' keeps that edge when the panel crops the scene; a number 0-1 is the share of a vertical crop taken from the top."""
    box = content_box(svg, zoom)
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] * 0.55
    PANEL = 1.73   # the 36x24 layout's map panel, width / height
    if anchor == 'left': cx = box[0] + min(box[2], box[3] * PANEL) / 2
    if anchor == 'top': anchor = 0.0
    if isinstance(anchor, float):   # share of the cropped height taken from the top (0 keeps the top edge)
        vis = min(box[3], box[2] / PANEL); cy = box[1] + anchor * (box[3] - vis) + vis / 2
    design = {'title': title, 'subtitle': place, 'region': slug, 'panels': [{'build': slug}], 'margin': 0.045, 'band': 0.1}
    regions = {slug: {'box': box, 'focus': [cx, cy]}}
    C.CREDIT = CREDIT
    size = (36, 24) if landscape else (24, 36)
    for dpi, q in ((165, 92), (165, 86), (150, 86), (150, 80)):   # 24x36 at 165 dpi = 23.5 MP, under Shopify's 25 MP image cap
        img = C.compose(design, size, {slug: svg}, regions, dpi)
        buf = io.BytesIO(); img.save(buf, 'JPEG', quality=q, dpi=(dpi, dpi), optimize=True)
        if buf.tell() <= MAX: break
    fn = os.path.join(out_dir, f'lm-{slug}_{size[0]}x{size[1]}.jpg')
    open(fn, 'wb').write(buf.getvalue())
    return fn, img.size, dpi, q, buf.tell()

if __name__ == '__main__':
    L = {x[0]: x for x in json.load(open(sys.argv[1]))}
    svg_dir, out = sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    for slug in (sys.argv[4:] or L):
        svg = os.path.join(svg_dir, f'lm-{slug}.svg')
        if not os.path.exists(svg): print('no svg', slug); continue
        print(*make(slug, L[slug][1], L[slug][2], svg, out), flush=True)

def make_canvas(print_path, out_dir, key, dpi=150):
    """Framed-canvas files (face + 1.5 in mirrored wrap per side) from the print file; 27x39 in at 150 dpi = 23.7 MP."""
    base = Image.open(print_path).convert('RGB'); out = []
    wrap = int(1.5 * dpi)
    for fw, fh in ((18, 12), (30, 20), (36, 24)):
        face = np.asarray(base.resize((fw * dpi, fh * dpi), Image.LANCZOS))
        arr = np.pad(face, ((wrap, wrap), (wrap, wrap), (0, 0)), mode='symmetric')
        fn = os.path.join(out_dir, f'{key}_canvas-{fw}x{fh}.jpg')
        Image.fromarray(arr).save(fn, quality=90, dpi=(dpi, dpi)); out.append(fn)
    return out
