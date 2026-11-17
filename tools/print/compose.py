#!/usr/bin/env python3
"""Compose print-ready files from isoscape builds.

Each design in a spec is one or more panels (a build's SVG, cropped to a region of the scene)
laid out on a sheet at an exact Printful size, at 300 dpi, with a paper margin, a title band
and the credit line every print must carry (OpenStreetMap is ODbL: produced works must credit
it). The art is vector, so each panel is rasterized straight to the pixels it fills.

A design with a "note" prints it in italics under the credit line: what the print does not show
as it was (in a dated view of Richmond, that the ground is today's).

Every line of a derived credit (and its note) prints at CREDIT_MIN_PT or more at the smallest
size the sheet is sold at (spec "serves": a 24x36 file is also printed as an 8x12, a third of its
size). Where the band's own credit size cannot reach that, the credit and note are set at that
size, right-aligned in a column between the title and the corner kept for the title block (as wide
as the block comes to on any face stamped from the sheet), on as many lines as they need. Where a
long subtitle leaves that column too short for them, they go on wide lines instead, from the end
of the title to the art's right edge, above the title block's corner (as tall as the block comes
to on any face) and the subtitle; the art is not moved or cropped. Sheets that already meet it
are composed exactly as before.

A design with "contain": true shows its region whole, letterboxed in the panel area, instead of
cropping it to the panel's shape (for very long views on a panorama sheet).

The credit line names exactly the sources the design's builds drew from: each build's SVG
carries them in its data-credits attribute (`sceneCredits` in src/credits.ts: OpenStreetMap,
the elevation source, land cover, building footprints, year-built records, Sanborn maps, each
only when the scene used it), and the line is "isoscape by Chris Busse" and their union, in
order. Only a build made before builds carried credits falls back to the design's "credit" or
the old default line, so a sold print can still be remade exactly as it was.

Usage: compose.py <spec.json> <builds-dir> <out-dir> [--only <design>] [--dpi 300] [--proof]
--proof writes 1/6-scale JPEGs instead, for checking layouts quickly.
"""
import html, json, os, re, subprocess, sys, tempfile, argparse
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = {k: os.path.join(HERE, 'fonts', f'libre-baskerville-latin-{v}.woff') for k, v in
        {'bold': '700-normal', 'regular': '400-normal', 'italic': '400-italic'}.items()}
PAPER, INK, DIM = '#f4f1ea', '#2c2b33', '#6a6570'
BYLINE = 'isoscape by Chris Busse'
# The line every print carried before builds named their own sources: only for remaking a print
# from a build made before then (see `design_credit`). lm_compose.py sets CREDIT for its own prints.
LEGACY_CREDIT = ('isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  '
                 'Elevation: USGS 3DEP  ·  Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress')
CREDIT = LEGACY_CREDIT
# Set while composing a design whose credit was derived from its builds: only such a line may
# wrap to two lines instead of shrinking below CREDIT_MIN_PT (a sold print remakes unchanged).
CREDIT_DERIVED = False
CREDIT_MIN_PT = 7


def smallest_scale(spec, size):
    """The smallest size a sheet of `size` (inches) is sold at, as a fraction of it: a 24x36 is
    also sold as an 8x12 print (spec "serves"), so 1/3. A sheet not listed is sold only as itself."""
    key = 'x'.join(f'{v:g}' for v in sorted(size))
    sold = [s for sizes in (spec.get('serves') or {}).get(key, {}).values() for s in sizes]
    return min([1.0] + [max(int(a) for a in s.split('x')) / max(size) for s in sold])


def stamped_faces(spec, size):
    """Long sides (inches) of every face cut from a sheet that gets its own title block: the
    sheet, and each framed-canvas face made from it (canvas.py; spec "serves")."""
    key = 'x'.join(f'{v:g}' for v in sorted(size))
    canv = (spec.get('serves') or {}).get(key, {}).get('Framed Canvas', [])
    return [max(size)] + [max(int(a) for a in s.split('x')) for s in canv]


def block_reserve(long_in, dpi, scale=1.0, faces=()):
    """Width kept clear at the bottom right, in the sheet's pixels, for the title block stamped
    later (stamp.py size_u, titleblock.WIDTH) with its clear margin: the largest it comes to on
    any face stamped from this sheet (a block on an 18x12 canvas face is relatively larger)."""
    import titleblock
    best = 0
    for f in list(faces) or [long_in]:
        u = round(1.3 * (f / 36) ** 0.5 * dpi / 300, 4) * scale * long_in / f
        best = max(best, titleblock.WIDTH * u + titleblock.H * u * 0.5)
    return best


def build_credits(svg_path):
    """The sources a build drew from, from its SVG's data-credits attribute; None for an older build."""
    with open(svg_path, encoding='utf-8') as f:
        head = f.read(8192)
    m = re.search(r'<svg\b[^>]*?\sdata-credits="([^"]*)"', head)
    return json.loads(html.unescape(m.group(1))) if m else None


def design_credit(design, builds):
    """The credit line for a design: the byline and every source its panels' builds used, once each."""
    parts, legacy = [], []
    for p in design['panels']:
        got = build_credits(builds[p['build']])
        if got is None: legacy.append(p['build']); continue
        parts += [c for c in got if c not in parts]
    if legacy:
        print(f"warning: {', '.join(sorted(set(legacy)))} carry no credits (built before builds named their sources); "
              'using the design\'s "credit" or the old default line. Rebuild to derive it.', file=sys.stderr)
        return design.get('credit', LEGACY_CREDIT)
    return '  ·  '.join([BYLINE] + parts)


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


def compose(design, size, builds, regions, dpi, scale=1.0, min_scale=1.0, faces=()):
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
    tband = title_band(design, W, H)
    tf = text_fit(d, design['title'], FONT['bold'], round(tband * 0.42), area_w * 0.62)
    d.text((m, by + tband * 0.18), design['title'], font=tf, fill=INK)
    sf = text_fit(d, design.get('subtitle', ''), FONT['italic'], round(tband * 0.2), area_w * 0.62)
    d.text((m, by + tband * 0.18 + tf.size * 1.25), design.get('subtitle', ''), font=sf, fill=DIM)
    cf = text_fit(d, CREDIT, FONT['regular'], round(band * 0.085), area_w * 0.36)
    least = dpi * scale * CREDIT_MIN_PT / 72 / min_scale      # CREDIT_MIN_PT at the smallest size sold
    if CREDIT_DERIVED and min_scale < 1 and cf.size < least and not two_lines_reach(d, band, area_w, least):
        # Even two lines at the band's credit size would print below CREDIT_MIN_PT at the smallest
        # size this sheet is sold at (a 24x36 is also an 8x12): set the credit and note at that
        # minimum, in a column between the title and the title block's corner, on as many lines
        # as they need.
        credit_column(d, design, W, H, m, by, band, dpi, scale, least, sf, faces)
        d.line((m, by + band * 0.08, W - m, by + band * 0.08), fill=INK, width=max(1, round(short * 0.0012)))
        return sheet
    if CREDIT_DERIVED and cf.size < dpi * scale * CREDIT_MIN_PT / 72:
        # A long derived line (many sources) wraps onto two lines rather than shrink past legibility.
        size = round(band * 0.085)
        while size > cf.size:
            f = ImageFont.truetype(FONT['regular'], size)
            if len(wrap(d, CREDIT, f, area_w * 0.36)) <= 2: cf = f; break
            size = int(size * 0.94)
    lines = wrap(d, CREDIT, cf, area_w * 0.36)
    ly = by + band * 0.22
    for ln in lines:
        d.text((W - m - d.textlength(ln, font=cf), ly), ln, font=cf, fill=DIM); ly += cf.size * 1.45
    if design.get('note'):
        # What the print does not show as it was (a dated view's ground is today's), under the credit.
        nf = ImageFont.truetype(FONT['italic'], cf.size)
        ly += cf.size * 0.35
        for ln in wrap_words(d, design['note'], nf, area_w * 0.36):
            d.text((W - m - d.textlength(ln, font=nf), ly), ln, font=nf, fill=DIM); ly += cf.size * 1.45
    d.line((m, by + band * 0.08, W - m, by + band * 0.08), fill=INK, width=max(1, round(short * 0.0012)))
    return sheet


def title_band(design, W, H):
    """The band height the title and subtitle are sized for: the design's "titleBand", else its
    band. A design that sets its credit below the subtitle (`credit_below`) needs a taller band
    for it without a taller title."""
    return round(min(W, H) * design.get('titleBand', design.get('band', 0.11)))


def two_lines_reach(d, band, area_w, least):
    """Whether the credit fits on two lines of the band's column at `least` px or more."""
    size = round(band * 0.085)
    if size < least: return False
    return len(wrap(d, CREDIT, ImageFont.truetype(FONT['regular'], size), area_w * 0.36)) <= 2


def credit_column(d, design, W, H, m, by, band, dpi, scale, least, sf, faces):
    """The credit (and the design's note, in italics) at `least` px, rounded up, right-aligned in
    the column from the end of the title and subtitle to the title block's reserved corner."""
    size = int(-(-least // 1))
    cf, nf = ImageFont.truetype(FONT['regular'], size), ImageFont.truetype(FONT['italic'], size)
    tf = text_fit(d, design['title'], FONT['bold'], round(title_band(design, W, H) * 0.42), (W - 2 * m) * 0.62)
    left = m + max(d.textlength(design['title'], font=tf), d.textlength(design.get('subtitle', ''), font=sf)) + band * 0.5
    right = W - m - block_reserve(max(W, H) / (dpi * scale), dpi, scale, faces)
    lines, note = credit_lines(d, design, cf, nf, right - left)
    ly, lead = by + band * 0.15, size * 1.35
    if design.get('credit') == 'below':
        # A design that asks for it (a portrait sheet whose title fills the band's width) sets the
        # credit and note under the subtitle, left-aligned, as wide as the title block's corner allows.
        return credit_below(d, design, W, H, m, by, band, size, cf, nf, tf, sf, right)
    if ly + lead * (len(lines) + len(note) - 1) + size * 1.1 + (size * 0.35 if note else 0) > H - m:
        # A long subtitle leaves too narrow a column: set the credit on wide lines instead.
        return credit_wide(d, design, W, H, m, by, band, dpi, scale, size, cf, nf, tf, sf, faces)
    for i, (ln, f) in enumerate(lines + note):
        if note and i == len(lines): ly += size * 0.35
        d.text((right - d.textlength(ln, font=f), ly), ln, font=f, fill=DIM); ly += lead


def credit_lines(d, design, cf, nf, col):
    """The credit wrapped between its sources (a source wider than the column wrapped between
    words, balanced) and the note balanced, each as (line, font), for a column `col` px wide."""
    lines = []
    for ln in [x for x in wrap(d, CREDIT, cf, col) if x]:
        lines += [(w, cf) for w in (balanced(d, ln, cf, col) if d.textlength(ln, font=cf) > col else [ln])]
    note = [(w, nf) for w in balanced(d, design['note'], nf, col)] if design.get('note') else []
    return lines, note


def block_top(H, m, long_in, dpi, scale, faces):
    """The lowest any printed thing may reach above the bottom-right corner, in the sheet's
    pixels: above the tallest title block stamped on any face from this sheet, as stamp.py puts
    it (titleblock.find_spot: its foot as low as the side margin allows, with 0.35 of its height
    of clear paper kept round it, searched in 4-pixel cells), less one more cell."""
    import titleblock
    best = H
    for f in list(faces) or [long_in]:
        k = scale * long_in / f                               # one face pixel, in sheet pixels
        bh = round(titleblock.H * round(1.3 * (f / 36) ** 0.5 * dpi / 300, 4))
        clear = 4 * (-(-bh // 4) + int(bh * 0.35 / 4) + 1 + 1)
        best = min(best, H - m - clear * k)
    return best


def credit_below(d, design, W, H, m, by, band, size, cf, nf, tf, sf, right):
    """The credit (and note) at `size` px under the subtitle, left-aligned at the margin, on lines
    as wide as from the margin to the title block's reserved corner (`right`): for a design with
    "credit": "below" (Then & Now, a portrait sheet whose title spans the band). The band must be
    tall enough to hold them (the design's "band")."""
    lines, note = credit_lines(d, design, cf, nf, right - m)
    lead = size * 1.35
    ly = by + title_band(design, W, H) * 0.18 + tf.size * 1.25 + sf.size * 1.25 + size * 0.4
    if ly + lead * (len(lines) + len(note) - 1) + size * 1.1 + (size * 0.35 if note else 0) > H - m:
        raise ValueError(f"{design['title']}: the credit at {size} px needs a taller band")
    for i, (ln, f) in enumerate(lines + note):
        if note and i == len(lines): ly += size * 0.35
        d.text((m, ly), ln, font=f, fill=DIM); ly += lead


def credit_wide(d, design, W, H, m, by, band, dpi, scale, size, cf, nf, tf, sf, faces):
    """The credit (and note) at `size` px on wide lines, right-aligned to the art's right edge,
    from the end of the title to the margin, above the title block's corner and the subtitle:
    for a subtitle so long that the column beside it is too narrow (Gwynn's Island). The art and
    the title are where they always are; the lines start where the column's would, or higher if
    they must to clear the block, but their tops never nearer the rule than a quarter of their size."""
    title_end = m + d.textlength(design['title'], font=tf) + band * 0.5
    lines, note = credit_lines(d, design, cf, nf, W - m - title_end)
    lead = size * 1.35
    asc, desc = cf.getmetrics()
    depth = lead * (len(lines) + len(note) - 1) + asc + desc + (size * 0.35 if note else 0)
    sub_top = by + band * 0.18 + tf.size * 1.25 + sf.getbbox('M')[1]
    floor = min(block_top(H, m, max(W, H) / (dpi * scale), dpi, scale, faces), sub_top - size * 0.5)
    ly = min(by + band * 0.15, floor - depth)
    rule_foot = by + band * 0.08 + max(1, round(min(W, H) * 0.0012)) / 2
    if ly + cf.getbbox(lines[0][0])[1] < rule_foot + size * 0.25:
        raise ValueError(f"{design['title']}: the credit at {size} px needs more room than the band has")
    right = W - m
    for i, (ln, f) in enumerate(lines + note):
        if note and i == len(lines): ly += size * 0.35
        d.text((right - d.textlength(ln, font=f), ly), ln, font=f, fill=DIM); ly += lead


def balanced(d, text, font, max_w):
    """Words wrapped into as few lines as fit max_w, as even in length as they can be (no word
    left alone on a last line)."""
    n, lo, hi = len(wrap_words(d, text, font, max_w)), 0.0, max_w
    while hi - lo > 4:
        mid = (lo + hi) / 2
        if len(wrap_words(d, text, font, mid)) <= n: hi = mid
        else: lo = mid
    return wrap_words(d, text, font, hi)


def wrap_words(d, text, font, max_w):
    lines, cur = [], ''
    for w in text.split():
        t = w if not cur else cur + ' ' + w
        if d.textlength(t, font=font) <= max_w: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]


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
            global CREDIT, CREDIT_DERIVED
            saved = CREDIT; CREDIT = design_credit(design, builds)
            CREDIT_DERIVED = CREDIT.startswith(BYLINE + '  ·  ') and all(build_credits(builds[p['build']]) is not None for p in design['panels'])
            img = compose(design, (w, h), builds, spec['regions'], o.dpi, 1 / 6 if o.proof else 1.0,
                          smallest_scale(spec, (w, h)), stamped_faces(spec, (w, h)))
            CREDIT = saved; CREDIT_DERIVED = False
            fn = os.path.join(o.out, f"{name}_{w:g}x{h:g}{'_proof' if o.proof else ''}.jpg")
            img.save(fn, quality=80 if o.proof else 93, dpi=(o.dpi, o.dpi), subsampling=0 if not o.proof else 2)
            print(fn, img.size)


if __name__ == '__main__':
    main()
