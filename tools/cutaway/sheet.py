#!/usr/bin/env python3
"""A cutaway sheet: the isometric cutaway large, the flat section of the same cut beneath it,
numbered callouts in a column beside them, a key to how sure each part is, sources and credits.

    python3 tools/cutaway/sheet.py cutaways/broad-street-1943.json [--out <dir>] [--png 3200] [--print] [--page]

It builds the region (isoscape build <region> --year <year> --no-archive), which writes the
cutaway, its flat section and where each part is drawn in both (*.anchors.json), then lays the
sheet out at 32 x 24 in, 300 dpi (9,600 x 7,200 units), the set-sheet size, as one SVG with both
drawings inline. A callout names a drawn part (or a place) in either drawing; its badge is that
part's confidence, from the history file, unless the callout says otherwise: a solid disc for a
part drawn from a plan, section or survey map, a ring for one placed from written accounts, a
dashed ring for one that is approximate.

--print also makes the print files, into <out>/print/: the sheet rasterized from the vector at
300 dpi at each size in PRINTS (both 4:3, the set sheet's sizes), with the plate's title block
(tools/print/titleblock.py, the fields from tools/release/plates.py for the spec's `design`)
set in the bottom-right corner below the callout column, at the size stamp.py gives a sheet of
that length. Each is named <design>_<w>x<h>.jpg (version 1 has no -vN suffix) and logged, with
the block's fields, placement and every file's SHA-256, in print/prints.json. No canvas files:
a canvas's 1.5 in of mirrored wrap would carry the title, the credit line and the column's text,
all within 1.5 in of the sheet's edges, mirrored round its sides.

--page writes the sheet's page in the explorer, pages/<page.slug>.md, from the same callouts,
key, sources and notes as the sheet, with its two images (<slug>-sheet.jpg, <slug>-social.jpg)
made from the 32 x 24 print. Like a set's page, it says nothing of the shop: the explorer adds
its shop button while shop.onSale in isoscape.config.json, the one list of what sells, has an
entry for the page's slug (e.g. "broad-street-cutaway": "<product URL>").
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'print'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'release'))
import compose as C  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
PRINTS = ((32, 24), (24, 18))   # inches; 300 dpi
MAX_BYTES = 15_000_000           # the store's upload ceiling for a print file (tools/sets/set.py)

W, H = 9600, 7200            # 32 x 24 in at 300 dpi
BODY = 54                    # callout text: 13 pt at 32 x 24 in, 9.7 pt at 24 x 18 in
M = 330                      # margin
INK, PAPER, DIM = C.INK, C.PAPER, C.DIM
SERIF = "'Libre Baskerville', Baskerville, Georgia, serif"
SANS = 'Helvetica, Arial, sans-serif'
COL_X = 7600                 # the callout column
ART_R = COL_X - 200          # the drawings' right edge


def font(kind, px):
    return ImageFont.truetype(C.FONT[kind], max(6, round(px)))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def wrap(text, kind, px, width):
    f = font(kind, px)
    lines, cur = [], ''
    for w in text.split():
        trial = (cur + ' ' + w).strip()
        if f.getlength(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def text(x, y, s, px, kind='regular', fill=INK, anchor='start', family=SERIF, spacing=None):
    weight = 'bold' if kind == 'bold' else 'normal'
    style = 'italic' if kind == 'italic' else 'normal'
    ls = '' if spacing is None else f' letter-spacing="{spacing}"'
    return f'<text x="{x:.0f}" y="{y:.0f}" font-family="{family}" font-size="{px:.0f}" font-weight="{weight}" font-style="{style}" fill="{fill}" text-anchor="{anchor}"{ls}>{esc(s)}</text>'


def badge(x, y, n, conf, r=44):
    """A numbered badge: solid (drawn), ring (written) or dashed ring (approximate)."""
    sw = r * 0.16
    label = '' if n is None else str(n)
    if conf == 'drawn':
        circle = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{INK}" stroke="{PAPER}" stroke-width="{sw * 0.8:.1f}"/>'
        fill = PAPER
    elif conf == 'written':
        circle = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r - sw / 2:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="{sw:.1f}"/>'
        fill = INK
    else:
        dash = r * 0.42
        circle = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r - sw / 2:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="{sw:.1f}" stroke-dasharray="{dash:.1f} {dash * 0.6:.1f}"/>'
        fill = INK
    num = '' if not label else text(x, y + r * 0.36, label, r * (1.0 if len(label) == 1 else 0.86), 'bold', fill, 'middle', SANS)
    return circle + num


HALO = [False]   # set from the spec: leaders get a paper halo, to read on a dark plate
LAST = [None]    # where the column, the key and the notes ended, for a caller checking the layout


def leader(x0, y0, x1, y1, r=0):
    """A thin leader from (x0, y0), less r at that end, to a small dot at (x1, y1): the
    wayfinding labels' leaders, drawn the same. On a dark plate (`halo` in the spec) each
    leader and dot is drawn over a paper-colored halo."""
    d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1
    sx, sy = x0 + (x1 - x0) * r / d, y0 + (y1 - y0) * r / d
    halo = (f'<path d="M{sx:.0f} {sy:.0f}L{x1:.0f} {y1:.0f}" fill="none" stroke="{PAPER}" stroke-width="15" stroke-linecap="round"/>'
            f'<circle cx="{x1:.0f}" cy="{y1:.0f}" r="20" fill="{PAPER}"/>') if HALO[0] else ''
    return (halo + f'<path d="M{sx:.0f} {sy:.0f}L{x1:.0f} {y1:.0f}" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<circle cx="{x1:.0f}" cy="{y1:.0f}" r="13" fill="{INK}" stroke="{PAPER}" stroke-width="3"/>')


def badge_at(px, py, off, n, conf, r):
    """A callout's badge on a drawing at the part's point (px, py), or, where the callout gives
    `badge: [dx, dy]` (sheet units), moved off the part by that much into clear space, with a
    leader back to a dot on the part, so the badge never hides what it names."""
    if not off:
        return badge(px, py, n, conf, r)
    bx, by = px + off[0], py + off[1]
    return leader(bx, by, px, py, r) + badge(bx, by, n, conf, r)


def figure(x, y, h, shapes, fill, facing=1):
    """The traveler glyph (the build's own shapes, in meters, feet at 0), feet at (x, y), h tall."""
    k = h / 1.75
    return '<g>' + ''.join('<path fill="{}" d="M{}Z"/>'.format(fill, 'L'.join(f'{x + px * k * facing:.1f} {y - py * k:.1f}' for px, py in poly)) for poly in shapes) + '</g>'


def theme_colors(name):
    """A sheet theme's accents, from src/palette.ts (SHEET_THEMES): the one place colors live."""
    r = subprocess.run(['node', '--input-type=module', '-e', "import('./src/palette.ts').then((m) => console.log(JSON.stringify(m.SHEET_THEMES)))"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(r.stdout)[name]


def holly(x, y, k, green, red, flip=1, vflip=1):
    """A sprig of holly for a holiday sheet's corner: two spiked leaves and three berries, `k`
    units to a leaf's length, pointing away from the corner (flip -1 mirrors it across, vflip
    -1 turns it upside down, for the foot of the sheet). Decoration only."""
    import math

    def leaf(cx, cy, ang):
        # A holly leaf: a long oval whose edge runs out to a spine at each of seven lobes.
        pts = []
        for i in range(15):
            t = i / 14
            w = 0.27 * k * math.sin(math.pi * t) ** 0.7 * (1.0 if i % 2 else 0.6)
            pts.append(((t - 0.5) * k, w))
        pts += [(u, -w) for u, w in reversed(pts[1:-1])]
        a = math.radians(ang)
        return 'M' + 'L'.join(f'{cx + u * math.cos(a) - v * math.sin(a):.0f} {cy + vflip * (u * math.sin(a) + v * math.cos(a)):.0f}' for u, v in pts) + 'Z'
    d = leaf(x + flip * 0.42 * k, y - vflip * 0.12 * k, -18 * flip) + leaf(x + flip * 0.12 * k, y + vflip * 0.40 * k, 72 * flip)
    out = f'<path d="{d}" fill="{green}"/>'
    for bx, by in ((0.0, 0.0), (0.13, -0.09), (0.05, 0.13)):
        out += f'<circle cx="{x + flip * bx * k:.0f}" cy="{y + vflip * by * k:.0f}" r="{0.075 * k:.0f}" fill="{red}"/>'
    return out


def inner(svg_text):
    """An SVG's contents and its viewBox."""
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg_text).group(1).split()]
    body = svg_text[svg_text.index('>', svg_text.index('<svg')) + 1:svg_text.rindex('</svg>')]
    return vb, body


def place(vb, box):
    """Fit viewBox vb into box (x, y, w, h), centered: returns (scale, ox, oy)."""
    x, y, w, h = box
    s = min(w / vb[2], h / vb[3])
    ox = x + (w - vb[2] * s) / 2 - vb[0] * s
    oy = y + (h - vb[3] * s) / 2 - vb[1] * s
    return s, ox, oy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--out', default=os.path.join(ROOT, 'out', 'cutaways'))
    ap.add_argument('--png', type=int, default=3200)
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--print', action='store_true', help='also make the 300 dpi print files, stamped, into <out>/print/')
    ap.add_argument('--page', action='store_true', help='also write pages/<page.slug>.md and its images')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    name = os.path.splitext(os.path.basename(a.spec))[0]
    os.makedirs(a.out, exist_ok=True)
    region, year = spec['region'], spec['year']
    build_dir = os.path.join(a.out, 'build')
    if not a.no_build:
        subprocess.run(['node', 'bin/isoscape.js', 'build', region, '--year', str(year), '--no-archive', '--out', build_dir], cwd=ROOT, check=True)
    base = os.path.join(build_dir, f'{region}-{year}')
    iso_svg = open(base + '.svg').read()
    sec_svg = open(base + '-section.svg').read()
    iso_a = json.load(open(base + '.anchors.json'))
    sec_a = json.load(open(base + '-section.anchors.json'))
    history = json.load(open(os.path.join(ROOT, json.load(open(os.path.join(ROOT, 'regions', region + '.json')))['time']['history'])))
    conf_of = {f['id']: f.get('confidence', 'approximate') for f in history['features']}
    # The traveler, as the build drew it, and the route's color, as the section drew it.
    traveler = sec_a.get('traveler')
    m = re.search(r'<g class="traveler"><path fill="([^"]+)"', sec_svg)
    route = m.group(1) if m else INK
    for g in spec['groups']:
        for c in g['callouts']:
            c['_conf'] = confidence(c, conf_of)
    HALO[0] = bool(spec.get('halo'))
    # A theme colors the title, the headings and their rules, and draws a plain border: sheet
    # decoration, never a claim about the drawing.
    theme = theme_colors(spec['theme']) if spec.get('theme') else None
    accent = theme['red'] if theme else INK
    head_ink = theme['green'] if theme else DIM
    rule_ink = theme['green'] if theme else INK

    # The isometric drawing, without its year caption (the sheet has a title of its own).
    vb, iso_body = inner(iso_svg)
    iso_body = re.sub(r'<text\b[^>]*>.*?</text>', '', iso_body, flags=re.S)
    if spec.get('mapData') is False:
        # The build's metadata credits OpenStreetMap; a plate drawn with none of its data says nothing.
        iso_body = re.sub(r'<desc>.*?</desc>', '', iso_body, flags=re.S)
    cap = max(28, (vb[2] - 48) * 0.022) * 2.4
    iso_vb = [vb[0], vb[1] + cap, vb[2], vb[3] - cap]
    svb, sec_body = inner(sec_svg)

    top = 700
    iso_box = (M - 60, top, ART_R - M + 60, spec.get('layout', {}).get('isoHeight', 3900))
    s_iso = min(iso_box[2] / iso_vb[2], iso_box[3] / iso_vb[3])
    iso_h = iso_vb[3] * s_iso
    # The flat section beneath, no taller than SEC_H, from the left edge of the art.
    sec_w = spec.get('layout', {}).get('sectionW', ART_R - M)
    s_sec = min(sec_w / svb[2], (H - spec.get('layout', {}).get('bottom', 330) - (top + iso_h + 330)) / svb[3])
    sec_h = svb[3] * s_sec
    sec_top = top + iso_h + 420
    sec_box = (M, sec_top, svb[2] * s_sec, sec_h)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    if theme:
        # The border: an evergreen rule round the sheet, a finer one inside it, holly at the corners.
        bi = 120
        out.append(f'<rect x="{bi}" y="{bi}" width="{W - 2 * bi}" height="{H - 2 * bi}" fill="none" stroke="{theme["green"]}" stroke-width="14"/>')
        out.append(f'<rect x="{bi + 34}" y="{bi + 34}" width="{W - 2 * bi - 68}" height="{H - 2 * bi - 68}" fill="none" stroke="{theme["green"]}" stroke-width="4"/>')
        for cx, cy, fl, vf in ((bi, bi, 1, 1), (W - bi, bi, -1, 1), (bi, H - bi, 1, -1), (W - bi, H - bi, -1, -1)):
            out.append(f'<circle cx="{cx}" cy="{cy}" r="96" fill="{PAPER}"/>')
            out.append(holly(cx, cy, 170, theme['green'], theme['red'], fl, vf))
    # Title.
    out.append(text(M, 400, spec['title'], 250, 'bold', accent))
    out.append(text(M, 570, spec['subtitle'], 112, 'italic', DIM))
    # The drawings.
    # The plate is centered over the art, or set against its left edge (`layout.isoAlign`).
    iso_x = M if spec.get('layout', {}).get('isoAlign') == 'left' else iso_box[0] + (iso_box[2] - iso_vb[2] * s_iso) / 2
    ox_iso, oy_iso = iso_x - iso_vb[0] * s_iso, iso_box[1] - iso_vb[1] * s_iso
    out.append(f'<svg x="{iso_x:.1f}" y="{iso_box[1]}" width="{iso_vb[2] * s_iso:.1f}" height="{iso_h:.1f}" viewBox="{" ".join(f"{v:.1f}" for v in iso_vb)}" overflow="hidden">{iso_body}</svg>')
    out.append(text(M, sec_top - 70, spec['sectionCaption'], 76, 'italic', DIM))
    out.append(f'<svg x="{sec_box[0]}" y="{sec_box[1]:.1f}" width="{sec_box[2]:.1f}" height="{sec_box[3]:.1f}" viewBox="{" ".join(f"{v:.1f}" for v in svb)}">{sec_body}</svg>')
    ox_sec, oy_sec = sec_box[0] - svb[0] * s_sec, sec_box[1] - svb[1] * s_sec
    iso_rect = (iso_x, iso_box[1], iso_vb[2] * s_iso, iso_h)

    def locate(lonlat):
        r = subprocess.run(['node', 'bin/isoscape.js', 'locate', region, '--year', str(year), '--', f'{lonlat[0]},{lonlat[1]}'], cwd=ROOT, check=True, capture_output=True, text=True)
        q = json.loads(r.stdout)[0]
        return q['x'], q['y']

    def anchor(where, anchors, frame=None):
        if 'part' in where:
            box = anchors['anchors'].get(where['part'])
            if box is None:
                print(f'warning: no part {where["part"]} drawn', file=sys.stderr)
                return None
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            return cx + where.get('dx', 0) * (box[2] - box[0]), cy + where.get('dy', 0) * (box[3] - box[1])
        if 'at' in where:
            return locate(where['at'])
        if 's' in where and frame is not None:
            return (frame['x0'] + where['s']) * frame['scale'], -(where['elevation'] - frame['datum']) * frame['exaggeration'] * frame['scale']
        return None

    # Callout badges on the drawings, and the column beside them. The column's first heading
    # stands on the subtitle's baseline, which leaves the foot of the column clear for the
    # print's title block (tools/print/titleblock.py) at both print sizes.
    y = 570
    x = COL_X
    for g in spec['groups']:
        out.append(text(x, y, g['title'].upper(), 58, 'bold', head_ink, family=SANS, spacing=4))
        if g.get('traveler') and traveler:
            tw = font('bold', 58).getlength(g['title'].upper()) + 4 * len(g['title'])
            out.append(figure(x + tw + 40, y + 4, 82, traveler['shapes'], route))
        out.append(f'<line x1="{x}" y1="{y + 32}" x2="{W - M}" y2="{y + 32}" stroke="{rule_ink}" stroke-width="4"/>')
        y += 170
        for c in g['callouts']:
            conf = c['_conf']
            for where, anchors, frame, (ox, oy, sc) in (('iso', iso_a, None, (ox_iso, oy_iso, s_iso)), ('section', sec_a, sec_a.get('frame'), (ox_sec, oy_sec, s_sec))):
                if where not in c:
                    continue
                # One anchor, or a list of them: a callout may name two parts in one drawing.
                for w in (c[where] if isinstance(c[where], list) else [c[where]]):
                    p = anchor(w, anchors, frame)
                    if p is not None:
                        out.append(badge_at(ox + p[0] * sc, oy + p[1] * sc, w.get('badge'), c['n'], conf, 46))
            out.append(badge(x + 56, y - 26, c['n'], conf, 50))
            out.append(text(x + 140, y, c['title'], 70, 'bold'))
            yy = y + 86
            for line in wrap(c['text'], 'regular', BODY, W - M - x - 140):
                out.append(text(x + 140, yy, line, BODY, 'regular', DIM))
                yy += 72
            y = yy + 58
        y += 36
    # Wayfinding: where the trains and streetcars went, in the plate's margins, each with a
    # leader to the track end or the street it belongs to.
    WF = 50
    for wf in spec.get('wayfinding', []):
        if 'plate' in wf:
            # A place off the plate: pointed to at the plate's edge, as a fraction of its box.
            ax, ay = iso_rect[0] + wf['plate'][0] * iso_rect[2], iso_rect[1] + wf['plate'][1] * iso_rect[3]
        else:
            p = locate(wf['at'])
            ax, ay = ox_iso + p[0] * s_iso, oy_iso + p[1] * s_iso
        # A place beyond the plate's edge is pointed to at the edge, toward it.
        ax = min(max(ax, iso_rect[0] + 16), iso_rect[0] + iso_rect[2] - 16)
        ay = min(max(ay, iso_rect[1] + 16), iso_rect[1] + iso_rect[3] - 16)
        lines = [ln.upper() for ln in wf['lines']]
        wmax = max(font('bold', WF).getlength(ln) + 3 * len(ln) for ln in lines)
        lh = WF * 1.42
        x0, y0 = {
            'top-right': (ART_R - wmax, top - 215),
            # Inside the plate's top-left corner, over its sky, for a place off to the upper left.
            'inside-top-left': (iso_rect[0] + 90, iso_rect[1] + 150),
            'bottom-right': (ART_R - wmax, iso_rect[1] + iso_rect[3] + 70),
            'bottom-left': (M + 20, iso_rect[1] + iso_rect[3] + 70),
            # Inside the plate, at its left edge, just above the place pointed to.
            'inside-left-above': (iso_rect[0] + 90, ay - lh * len(lines) - 60),
            # Inside the plate, at its left edge, just below the place pointed to.
            'inside-left-below': (iso_rect[0] + 90, ay + 160),
            # Below the plate, starting under the place pointed to on its bottom edge.
            'below': (ax - 40, iso_rect[1] + iso_rect[3] + 70),
        }[wf['place']]
        # A label may be nudged off what it would cover (sheet units).
        x0, y0 = x0 + wf.get('offset', [0, 0])[0], y0 + wf.get('offset', [0, 0])[1]
        out.append(f'<rect x="{x0 - 30:.0f}" y="{y0 - WF - 26:.0f}" width="{wmax + 90:.0f}" height="{lh * len(lines) + 34:.0f}" fill="{PAPER}" fill-opacity="0.9"/>')
        out.append(badge(x0 + 6, y0 - WF * 0.36, None, wf['confidence'], 15))
        for i, ln in enumerate(lines):
            out.append(text(x0 + 44, y0 + i * lh, ln, WF, 'bold', INK, family=SANS, spacing=3))
        # The leader: from the label's nearer edge to the place, ending in a dot.
        lx = x0 - 30 if ax < x0 else min(ax, x0 + wmax + 60)
        ly = y0 + lh * len(lines) - lh / 2 if ay > y0 else y0 - WF - 26
        if wf['place'] not in ('top-right', 'inside-top-left', 'inside-left-above'):
            ly = y0 - WF - 26
            lx = max(x0 - 30, min(ax, x0 + wmax + 60))
        if HALO[0]:
            out.append(f'<path d="M{lx:.0f} {ly:.0f}L{ax:.0f} {ay:.0f}" fill="none" stroke="{PAPER}" stroke-width="15" stroke-linecap="round"/>')
            out.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="20" fill="{PAPER}"/>')
        out.append(f'<path d="M{lx:.0f} {ly:.0f}L{ax:.0f} {ay:.0f}" fill="none" stroke="{INK}" stroke-width="5"/>')
        out.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="13" fill="{INK}"/>')
    # Key, sources and notes, at the foot of the callout column, or the key in a block of its own
    # (`layout.key`: x, y, w) with the sources and notes under it (`layout.notes` without y).
    kb = spec.get('layout', {}).get('key')
    kx, ky, kw = (kb['x'], kb['y'], kb['w']) if kb else (x, y + 40, W - M - x)
    out.append(text(kx, ky, 'HOW SURE EACH PART IS', 58, 'bold', head_ink, family=SANS, spacing=4))
    out.append(f'<line x1="{kx}" y1="{ky + 32}" x2="{kx + kw}" y2="{ky + 32}" stroke="{rule_ink}" stroke-width="4"/>')
    ky += 150
    for conf, msg in spec['key']:
        out.append(badge(kx + 56, ky - 22, None, conf, 42))
        for i, line in enumerate(wrap(msg, 'regular', 56, kw - 140)):
            out.append(text(kx + 140, ky, line, 56, 'regular', DIM))
            ky += 76
        ky += 16
    for line in wrap(spec.get('keyNote', 'The same marks, small, stand before each place the trains and streetcars went.'), 'regular', 56, kw - 140):
        out.append(text(kx + 140, ky, line, 56, 'regular', DIM))
        ky += 76
    if spec.get('travelerKey') and traveler:
        ky += 26
        out.append(figure(kx + 56, ky + 14, 90, traveler['shapes'], route))
        for line in wrap(spec['travelerKey'], 'regular', 56, kw - 140):
            out.append(text(kx + 140, ky, line, 56, 'regular', DIM))
            ky += 76
    ky += 40
    nb = spec.get('layout', {}).get('notes')
    nx, ny, nw = (nb['x'], nb.get('y', ky + 30), nb['w']) if nb else (kx, ky, kw)
    for line in wrap(spec['sources'], 'italic', 50, nw) + [''] + wrap(spec['notes'], 'italic', 50, nw):
        if line:
            out.append(text(nx, ny, line, 50, 'italic', DIM))
        ny += 68
    if nb is None and kb is None:
        ky = ny
    elif ny > H - 260:
        print(f'warning: the notes run to {ny:.0f}, past the credit line', file=sys.stderr)
    if y > H - 120 or (kb is None and ky > H - 120):
        print(f'warning: the column runs to {max(y, ky):.0f}, past the credit line', file=sys.stderr)
    LAST[0] = {'column': y, 'key': ky, 'notes': ny}
    # Within a theme's border, the credit line stands higher.
    out.append(text(M, H - (230 if theme else 150), spec['credit'], 46, 'regular', DIM))
    out.append('</svg>')
    sheet = os.path.join(a.out, f'{name}-sheet.svg')
    open(sheet, 'w').write('\n'.join(out))
    section = os.path.join(a.out, f'{name}-section.svg')
    open(section, 'w').write(sec_svg)
    if a.png:
        C.svg_to_png(sheet, os.path.join(a.out, f'{name}-sheet.png'), a.png)
        C.svg_to_png(section, os.path.join(a.out, f'{name}-section.png'), a.png)
    print(f'wrote {sheet}')
    if a.print:
        prints(spec, sheet, os.path.join(a.out, 'print'))
    if a.page:
        page(spec, os.path.join(a.out, 'print'))


def confidence(c, conf_of):
    """A callout's badge: its own `confidence`, else its part's, else approximate."""
    first = lambda w: (w[0] if isinstance(w, list) and w else w) or {}
    part = first(c.get('iso')).get('part') or first(c.get('section')).get('part') or ''
    return c.get('confidence') or conf_of.get(part.replace('history:', '').split(':')[0], 'approximate')


def page(spec, print_dir):
    """pages/<slug>.md: the sheet, its callouts as text, the key, the sources and notes."""
    import plates
    P = spec['page']
    slug = P['slug']
    plate = plates.by_design()[spec['design']]
    key = dict((k, msg.replace(': ', '; ')) for k, msg in spec['key'])      # read in a sentence
    marks = {'drawn': 'solid', 'written': 'ring', 'approximate': 'dashed ring'}
    out = ['---', f"title: {P['title']}", f"order: {P.get('order', 50)}", f"summary: {P['summary']}",
           f'social: {slug}-social.jpg', '---', '', f"# {P['title']}", '',
           f"*{plate['kind']} · Plate {plate['plate'].replace('-', '·')}*" if plate.get('kind') else f"*Plate {plate['plate'].replace('-', '·')}*", '',
           P['intro'], '', f"![{P.get('image_alt', P['title'])}]({slug}-sheet.jpg)", '']
    for g in spec['groups']:
        out += [f"## {g['title']}", '']
        for c in g['callouts']:
            out += [f"### {c['n']}. {c['title']}", '', c['text'], '', f"*How sure: {key[c['_conf']]}.*", '']
    out += ["## How sure each part is", '', P.get('key_intro', ''), '']
    out += [f"- **{marks[k].capitalize()}:** {key[k]}." for k, _ in spec['key']]
    out += ['', P.get('marks_note', 'The same marks, small, stand before each place the trains and streetcars went.'), '']
    if spec.get('travelerKey'):
        out += [P.get('traveler_note', spec['travelerKey']), '']
    if spec.get('wayfinding'):
        out += [f"## {P.get('wayfinding_heading', 'Where the trains and streetcars went')}", '']
        for wf in spec['wayfinding']:
            out += [f"- {wf.get('text') or ' '.join(wf['lines'])} *({key[wf['confidence']][:1].upper() + key[wf['confidence']][1:]}. Sources: {'; '.join(wf.get('sources', [])).rstrip('.')}.)*"]
        out += ['']
    out += ['## Sources', '', re.sub(r'^Sources:\s*', '', spec['sources']), '', spec['notes'], '', '## How it was drawn', '', P['how'], '',
            "More in [How it's made](how-its-made.md#cutaways).", '']
    if P.get('drafted'):
        out += ['---', '', f"*{P['drafted']}*", '']
    open(os.path.join(ROOT, 'pages', f'{slug}.md'), 'w').write('\n'.join(out))
    sheet = os.path.join(print_dir, f"{spec['design']}_32x24.jpg")
    if os.path.exists(sheet):
        im = Image.open(sheet)
        im.resize((1800, 1350), Image.LANCZOS).save(os.path.join(ROOT, 'pages', f'{slug}-sheet.jpg'), quality=84, optimize=True)
        w = im.size[0]
        im.crop((0, 0, w, round(w / 1.905))).resize((1200, 630), Image.LANCZOS).save(os.path.join(ROOT, 'pages', f'{slug}-social.jpg'), quality=86, optimize=True)
    else:
        print(f'warning: no print at {sheet}; run --print first for the page images', file=sys.stderr)
    print(f'pages/{slug}.md')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def prints(spec, sheet, out_dir, version=1):
    """The print files: each size rasterized at 300 dpi and stamped with the title block."""
    import plates, stamp, titleblock
    design = spec['design']
    info = plates.info(design, version)
    os.makedirs(out_dir, exist_ok=True)
    log = {'design': design, 'version': version, 'sheet': os.path.relpath(sheet, ROOT), 'sheet_sha256': sha(sheet), 'info': info,
           'tools': {f: sha(os.path.join(ROOT, f)) for f in ('tools/cutaway/sheet.py', 'tools/print/titleblock.py', 'tools/release/stamp.py', 'catalog/plates.json')},
           'files': {}}
    for w_in, h_in in PRINTS:
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, 'sheet.png')
            C.svg_to_png(sheet, png, w_in * 300, h_in * 300, background=PAPER)
            im = Image.open(png).convert('RGB')
        assert im.size == (w_in * 300, h_in * 300), im.size
        im, at = titleblock.stamp(im, info, stamp.size_u(w_in, 300), where=('foot', 'corner', 'head'))
        p = os.path.join(out_dir, f'{design}_{w_in}x{h_in}.jpg')
        for q in (94, 90, 86, 82, 78):
            im.save(p, quality=q, dpi=(300, 300), optimize=True)
            if os.path.getsize(p) <= MAX_BYTES: break
        log['files'][os.path.basename(p)] = {'size': list(im.size), 'quality': q, 'bytes': os.path.getsize(p), 'sha256': sha(p),
                                             'at': {'x': at[0], 'y': at[1], 'w': at[2], 'h': at[3], 'u': at[4], 'where': at[5]}}
        print(p, im.size, f'{os.path.getsize(p) / 1e6:.1f} MB q{q}', 'block', at)
    json.dump(log, open(os.path.join(out_dir, 'prints.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
