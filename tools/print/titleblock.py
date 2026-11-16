"""The title block: a small ruled block in a print's bottom-right corner that names the piece.

It reads as a drafting sheet's title block and as a catalog label: the isoscape cube and maker,
the piece's place in the taxonomy (collection › set › piece), its plate number from
catalog/plates.json, and its version, year, location and facing. It is drawn with Pillow so it
comes out the same wherever it runs, in the print's own fonts and palette.

  block(info, u)            the block as an RGBA image; u = 1 is the size proofed on a 36x24 at
                            300 dpi (about 4.3 x 0.6 in)
  find_spot(sheet, w, h, …) where a w x h block fits in the sheet's bottom-right corner
  stamp(sheet, info, …)     both: returns the stamped sheet and where the block went

info: {collection, set, piece, plate, version, drawn, location, facing} and, optionally, kind
(what sort of piece it is: "Map", "Landmark", "Building cutaway"). A block without a kind is
drawn exactly as before; with one, the maker's two lines move up and the kind is set beneath
them, one line at KIND_SIZE on the baseline of the lower row's values.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = {k: os.path.join(HERE, 'fonts', f'libre-baskerville-latin-{v}.woff') for k, v in
        {'bold': '700-normal', 'regular': '400-normal', 'italic': '400-italic'}.items()}
# The print palette (compose.py, palette.ts paper and ink); the cube's faces are the brand mark's.
PAPER, INK, DIM, FACE, STONE = (244, 241, 234), (44, 43, 51), (106, 101, 112), (236, 231, 220), (195, 187, 172)

# Layout in units of u (u = 1: one 300 dpi pixel on the 36x24 proof).
H = 184
CUBE_W, NAME_W = 110, 300
TOP = [('Collection › Set › Piece', 'taxonomy', 660), ('Plate', 'plate', 230)]
LOW = [('Version', 'version', 150), ('Drawn', 'drawn', 150), ('Location', 'location', 360), ('Facing', 'facing', 230)]
WIDTH = CUBE_W + NAME_W + sum(w for *_, w in TOP)
# The kind's line: 28 units is 7.1 pt on the smallest sheet stamped (24 in long at 300 dpi,
# u = 1.06), and "Building cutaway" at that size fits the name cell with room to spare.
KIND_SIZE = 28


def _font(kind, size):
    return ImageFont.truetype(FONT[kind], max(1, round(size)))


def _spaced(d, x, y, text, font, fill, spacing):
    """Text with letter-spacing, left-aligned at x, baseline y."""
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor='ls')
        x += d.textlength(ch, font=font) + spacing


def _fit(d, text, kind, size, width):
    f = _font(kind, size)
    while size > 6 and d.textlength(text, font=f) > width:
        size *= 0.96; f = _font(kind, size)
    return f


def taxonomy(info):
    return f'{info["collection"]} › {info["set"]} › {info["piece"]}'


def check_glyphs(text):
    """Raise if the print face lacks a character (Pillow would draw an empty box)."""
    from fontTools.ttLib import TTFont
    cmap = check_glyphs.cmap = getattr(check_glyphs, 'cmap', None) or TTFont(FONT['regular']).getBestCmap()
    missing = sorted({c for c in text if ord(c) not in cmap})
    if missing:
        raise ValueError(f'the print face has no glyph for {missing!r} in {text!r}')


def block(info, u=1.0):
    """The title block for one print, as an RGBA image with a paper ground."""
    for v in list(info.values()) + [taxonomy(info)]:
        check_glyphs(str(v))
    W, Hh = round(WIDTH * u), round(H * u)
    im = Image.new('RGBA', (W, Hh), PAPER + (255,))
    d = ImageDraw.Draw(im)
    rule, hair = max(1, round(2.2 * u)), max(1, round(1.1 * u))
    c0, c1, mid = CUBE_W * u, (CUBE_W + NAME_W) * u, Hh / 2
    d.rectangle((0, 0, W - 1, Hh - 1), outline=INK, width=rule)
    for x0, y0, x1, y1 in [(c0, 0, c0, Hh), (c1, 0, c1, Hh), (c1, mid, W, mid)]:
        d.line((x0, y0, x1, y1), fill=INK, width=hair)
    # the cube as a small outline: top, left wall, right wall
    k, cx, cy = 80 * u / 86, c0 / 2, 52 * u
    P = lambda a, b: (cx + (a - 60) * k, cy + (b - 18) * k)
    sw = max(1, round(2.2 * u))
    d.polygon([P(20, 41), P(60, 64), P(60, 104), P(20, 81)], fill=FACE)
    d.polygon([P(100, 41), P(60, 64), P(60, 104), P(100, 81)], fill=STONE)
    for path in ([P(60, 18), P(100, 41), P(60, 64), P(20, 41), P(60, 18)],
                 [P(20, 41), P(20, 81), P(60, 104), P(100, 81), P(100, 41)], [P(60, 64), P(60, 104)]):
        d.line(path, fill=INK, width=sw, joint='curve')
    # maker, and the kind of piece beneath it when there is one
    kind = info.get('kind')
    _spaced(d, c0 + 22 * u, (70 if kind else 88) * u, 'isoscape', _font('bold', 36 * u), INK, 1 * u)
    d.text((c0 + 22 * u, (108 if kind else 128) * u), 'drawn by Chris Busse', font=_font('italic', 22 * u), fill=INK, anchor='ls')
    if kind:                    # on the baseline of the lower row's values
        d.text((c0 + 22 * u, (H / 2 + 74) * u), kind, font=_fit(d, kind, 'regular', KIND_SIZE * u, (NAME_W - 36) * u), fill=INK, anchor='ls')
    # two rows of labeled cells
    vals = dict(info, taxonomy=taxonomy(info), plate=info['plate'].replace('-', '·'))
    lab = _font('regular', 17 * u)
    for row, y0 in [(TOP, 0), (LOW, mid)]:
        x = c1
        for i, (label, key, w) in enumerate(row):
            if i:
                d.line((x, y0, x, y0 + mid), fill=INK, width=hair)
            _spaced(d, x + 18 * u, y0 + 34 * u, label.upper(), lab, DIM, 3 * u)
            v = str(vals[key])
            d.text((x + 18 * u, y0 + 74 * u), v, font=_fit(d, v, 'regular', 24 * u, (w - 36) * u), fill=INK, anchor='ls')
            x += w * u
    return im


def content_mask(sheet, face=None, step=4, tol=14):
    """Boolean array (one cell per `step` px) marking what is not bare paper."""
    x0, y0, x1, y1 = face or (0, 0, sheet.width, sheet.height)
    small = sheet.crop((x0, y0, x1, y1)).convert('RGB').resize(((x1 - x0) // step, (y1 - y0) // step), Image.BOX)
    a = np.asarray(small).astype(int)
    paper = a[2, a.shape[1] // 2]                 # the top margin, mid-width: always bare paper
    return np.abs(a - paper).max(axis=2) > tol


def find_spot(sheet, bw, bh, face=None, pad=None, step=4, where='foot'):
    """Top-left (x, y) for a bw x bh block, or None if it won't fit.

    The block's right edge lines up with the right edge of the art (the rows that run across at
    least 80% of the sheet: the map, the rows of boxes, the rules) and it never touches anything
    already printed, keeping `pad` of clear paper around it.
      foot: in the band below the art, as low as the art's side margin allows (the same margin
            below as at the side). Every layout but the set sheets.
      head: in the header above the art, its bottom just over the header rule, its top no higher
            than the first line of the title; slid left of anything already at the right (a line
            key). For set sheets, whose foot is full of notes.
      corner: in the bottom-right corner beside the art, not below it: right-aligned with the
            rightmost thing printed, as low as that side margin allows, clear of everything.
            For a sheet with a column of notes beside its art (the cutaway sheet), where no row
            runs across the sheet. Only when asked for: stamp() does not try it by default."""
    x0, y0, x1, y1 = face or (0, 0, sheet.width, sheet.height)
    mask = content_mask(sheet, face, step)
    h, w = mask.shape
    if where == 'corner':
        cols = np.nonzero(mask.any(axis=0))[0]
        if not len(cols):
            return None
        right = int(cols.max()) + 1
        pad = pad if pad is not None else bh * 0.35
        p, bws, bhs = int(pad / step) + 1, -(-bw // step), -(-bh // step)
        xs = right - bws
        if xs - p < 0:
            return None
        free = ~mask[:, xs - p:min(w, right + p)].any(axis=1)
        for yb in range(h - (w - right), max(bhs + p, h // 2), -1):     # the lower half only
            if free[yb - bhs - p:min(h, yb + p)].all():
                return x0 + xs * step + (bws * step - bw), y0 + (yb - bhs) * step
        return None
    rows = mask.sum(axis=1)
    wide = rows > 0.8 * w                              # the art and rules, not a long line of text
    if not wide.any():
        return None
    right = int(np.nonzero(mask[wide].any(axis=0))[0].max()) + 1
    first, art_top, art_bottom = int(np.nonzero(rows)[0].min()), int(np.nonzero(wide)[0].min()), int(np.nonzero(wide)[0].max())
    pad = pad if pad is not None else bh * 0.35
    p, bws, bhs = int(pad / step) + 1, -(-bw // step), -(-bh // step)
    side = w - right                                   # the art's side margin
    if where == 'foot':                                # as low as the side margin allows
        spans = [(right - bws, range(h - side, art_bottom + bhs + p, -1))]
    else:                                              # right-aligned, else slid left past a key
        spans = [(xs, range(art_top - p // 2, first + bhs - 1, -1)) for xs in range(right - bws, 0, -2)]
    for xs, ys in spans:
        if xs - p < 0:
            continue
        free = ~mask[:, max(0, xs - p):min(w, xs + bws + p)].any(axis=1)
        for yb in ys:                                  # yb: the row just below the block
            lo, hi = (yb - bhs - p, min(h, yb + p)) if where == 'foot' else (yb - bhs, min(h, yb + p // 2))
            if lo >= 0 and free[lo:hi].all():
                return x0 + xs * step + (bws * step - bw) * (xs == right - bws), y0 + (yb - bhs) * step
    return None


def stamp(sheet, info, u, face=None, shrink=(1.0, 0.9, 0.8, 0.7, 0.6), where=('foot', 'head')):
    """Stamp the block on a copy of `sheet`; returns (sheet, (x, y, w, h, u)). Tries smaller sizes
    if the corner is too full; raises if nothing fits."""
    for s in shrink:                    # full size in the header beats a shrunken block in the foot
        b = block(info, u * s)
        for place in where:
            at = find_spot(sheet, b.width, b.height, face, where=place)
            if at:
                out = sheet.convert('RGB').copy()
                out.paste(b.convert('RGB'), at)
                return out, (at[0], at[1], b.width, b.height, round(u * s, 4), place)
    raise ValueError('no room for the title block')
