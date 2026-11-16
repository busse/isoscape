#!/usr/bin/env python3
"""Compose print-ready files from isoscape builds.

Each design in a spec is one or more panels (a build's SVG, cropped to a region of the scene)
laid out on a sheet at an exact Printful size, at 300 dpi, with a paper margin, a title band
and the credit line every print must carry (OpenStreetMap is ODbL: produced works must credit
it). The art is vector, so each panel is rasterized straight to the pixels it fills.

A design with "contain": true shows its region whole, letterboxed in the panel area, instead of
cropping it to the panel's shape (for very long views on a panorama sheet). "credit" overrides the
credit line (a modern view has no Sanborn maps).

Usage: compose.py <spec.json> <builds-dir> <out-dir> [--only <design>] [--dpi 300] [--proof]
--proof writes 1/6-scale JPEGs instead, for checking layouts quickly.
"""
import json, os, re, subprocess, sys, tempfile, argparse
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = {k: os.path.join(HERE, 'fonts', f'libre-baskerville-latin-{v}.woff') for k, v in
        {'bold': '700-normal', 'regular': '400-normal', 'italic': '400-italic'}.items()}
PAPER, INK, DIM = '#f4f1ea', '#2c2b33', '#6a6570'
CREDIT = ('isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  '
          'Elevation: USGS 3DEP  ·  Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress')


def latest_builds(builds_dir):
    """region-name -> newest build dir (ids sort by time)."""
    out = {}
    for d in sorted(os.listdir(builds_dir)):
        m = re.match(r'\d{8}-\d{6}-(.+)$', d)
        if m and os.path.exists(os.path.join(builds_dir, d, 'image.svg')):
            out[m.group(1)] = os.path.join(builds_dir, d, 'image.svg')
    return out


def fit(region, aspect, focus=None):
    """Largest crop of `region` (x, y, w, h) with width/height = aspect, centered on focus."""
    x, y, w, h = region
    cx, cy = focus or (x + w / 2, y + h / 2)
    if w / h > aspect:
        w2, h2 = h * aspect, h
    else:
        w2, h2 = w, w / aspect
    nx = min(max(cx - w2 / 2, x), x + w - w2)
    ny = min(max(cy - h2 / 2, y), y + h - h2)
    return nx, ny, w2, h2


SOCIAL = (1200, 630)    # a link preview: Open Graph's and X's large card, 1.91:1


import shutil
def svg_to_png(src, png, width, height=None, background=None):
    """rsvg-convert when installed, else cairosvg (pip install cairosvg)."""
    if shutil.which('rsvg-convert'):
        cmd = ['rsvg-convert', '-w', str(width)] + (['-h', str(height)] if height else []) + (['-b', background] if background else []) + [src, '-o', png]
        subprocess.run(cmd, check=True)
    else:
        import cairosvg
        cairosvg.svg2png(url=src, write_to=png, output_width=width, output_height=height, background_color=background, unsafe=True)

def raster(svg_path, vb, px_w, px_h):
    s = open(svg_path, encoding='utf-8').read()
    s = re.sub(r'viewBox="[^"]+"', 'viewBox="%.2f %.2f %.2f %.2f"' % vb, s, count=1)
    s = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r'\1', s, count=1)
    s = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r'\1', s, count=1)
    s = re.sub(r'<g class="caption".*?</g>', '', s, flags=re.S)
    with tempfile.TemporaryDirectory() as t:
        src, png = os.path.join(t, 'a.svg'), os.path.join(t, 'a.png')
        open(src, 'w', encoding='utf-8').write(s)
        svg_to_png(src, png, px_w, px_h, PAPER)
        return Image.open(png).convert('RGB')


def text_fit(draw, text, font_path, size, max_w):
    while size > 6:
        f = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=f) <= max_w: return f
        size = int(size * 0.94)
    return ImageFont.truetype(font_path, size)


def compose(design, size, builds, regions, dpi, scale=1.0):
    W_in, H_in = size
    W, H = round(W_in * dpi * scale), round(H_in * dpi * scale)
    short = min(W, H)
    m = round(short * design.get('margin', 0.05))
    band = round(short * design.get('band', 0.11))
    sheet = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    rows, cols = design.get('grid', [1, 1])
    gap = round(short * design.get('gap', 0.012))
    label_h = round(short * 0.03) if design.get('labels') else 0
    area_w, area_h = W - 2 * m, H - 2 * m - band
    cw = (area_w - gap * (cols - 1)) / cols
    ch = (area_h - gap * (rows - 1)) / rows - label_h
    panels = design['panels']
    for k, p in enumerate(panels):
        r, c = divmod(k, cols)
        x0 = round(m + c * (cw + gap)); y0 = round(m + r * (ch + label_h + gap))
        reg = regions[p.get('region', design.get('region'))]
        if design.get('contain'):
            # The whole region, not a crop: a very long view stays whole and sits centered in its area.
            ra = reg['box'][2] / reg['box'][3]
            if ra > cw / ch:
                nh = cw / ra; y0 = round(y0 + (ch - nh) / 2); ch = nh
            else:
                nw = ch * ra; x0 = round(x0 + (cw - nw) / 2); cw = nw
        vb = fit(reg['box'], cw / ch, reg.get('focus'))
        img = raster(builds[p['build']], vb, round(cw), round(ch))
        sheet.paste(img, (x0, y0))
        d.rectangle((x0, y0, x0 + round(cw) - 1, y0 + round(ch) - 1), outline='#d8d2c4', width=max(1, round(short * 0.0006)))
        if label_h:
            f = ImageFont.truetype(FONT['bold'], round(label_h * 0.72))
            d.text((x0, y0 + round(ch) + label_h * 0.12), p['label'], font=f, fill=INK)
            if p.get('sub'):
                fi = ImageFont.truetype(FONT['italic'], round(label_h * 0.5))
                tx = x0 + d.textlength(p['label'], font=f) + label_h * 0.4
                d.text((tx, y0 + round(ch) + label_h * 0.3), p['sub'], font=fi, fill=DIM)
    # title band
    by = H - m - band
    tf = text_fit(d, design['title'], FONT['bold'], round(band * 0.42), area_w * 0.62)
    d.text((m, by + band * 0.18), design['title'], font=tf, fill=INK)
    sf = text_fit(d, design.get('subtitle', ''), FONT['italic'], round(band * 0.2), area_w * 0.62)
    d.text((m, by + band * 0.18 + tf.size * 1.25), design.get('subtitle', ''), font=sf, fill=DIM)
    cf = text_fit(d, CREDIT, FONT['regular'], round(band * 0.085), area_w * 0.36)
    lines = wrap(d, CREDIT, cf, area_w * 0.36)
    ly = by + band * 0.22
    for ln in lines:
        d.text((W - m - d.textlength(ln, font=cf), ly), ln, font=cf, fill=DIM); ly += cf.size * 1.45
    d.line((m, by + band * 0.08, W - m, by + band * 0.08), fill=INK, width=max(1, round(short * 0.0012)))
    return sheet


def wrap(d, text, font, max_w):
    parts, lines, cur = text.split('  ·  '), [], ''
    for p in parts:
        t = p if not cur else cur + '  ·  ' + p
        if d.textlength(t, font=font) <= max_w: cur = t
        else: lines.append(cur); cur = p
    return lines + [cur]


def main():
    a = argparse.ArgumentParser()
    a.add_argument('spec'); a.add_argument('builds'); a.add_argument('out')
    a.add_argument('--only'); a.add_argument('--dpi', type=int, default=300); a.add_argument('--proof', action='store_true')
    o = a.parse_args()
    spec = json.load(open(o.spec))
    builds = latest_builds(o.builds)
    os.makedirs(o.out, exist_ok=True)
    for name, design in spec['designs'].items():
        if o.only and o.only != name: continue
        for size in design['sizes']:
            w, h = size if design.get('orientation', 'landscape') == 'portrait' else (max(size), min(size))
            if design.get('orientation') == 'portrait': w, h = min(size), max(size)
            global CREDIT
            saved = CREDIT; CREDIT = design.get('credit', CREDIT)
            img = compose(design, (w, h), builds, spec['regions'], o.dpi, 1 / 6 if o.proof else 1.0)
            CREDIT = saved
            fn = os.path.join(o.out, f"{name}_{w:g}x{h:g}{'_proof' if o.proof else ''}.jpg")
            img.save(fn, quality=80 if o.proof else 93, dpi=(o.dpi, o.dpi), subsampling=0 if not o.proof else 2)
            print(fn, img.size)


if __name__ == '__main__':
    main()
