#!/usr/bin/env python3
"""A cutaway sheet: the isometric cutaway large, the flat section of the same cut beneath it,
numbered callouts in a column beside them, a key to how sure each part is, sources and credits.

    python3 tools/cutaway/sheet.py cutaways/broad-street-1943.json [--out <dir>] [--png 3200]

It builds the region (isoscape build <region> --year <year> --no-archive), which writes the
cutaway, its flat section and where each part is drawn in both (*.anchors.json), then lays the
sheet out at 32 x 24 in, 300 dpi (9,600 x 7,200 units), the set-sheet size, as one SVG with both
drawings inline. A callout names a drawn part (or a place) in either drawing; its badge is that
part's confidence, from the history file, unless the callout says otherwise: a solid disc for a
part drawn from a plan, section or survey map, a ring for one placed from written accounts, a
dashed ring for one that is approximate.
"""
import argparse, json, os, re, subprocess, sys
from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'print'))
import compose as C  # noqa: E402

W, H = 9600, 7200            # 32 x 24 in at 300 dpi
M = 330                      # margin
INK, PAPER, DIM = C.INK, C.PAPER, C.DIM
SERIF = "'Libre Baskerville', Baskerville, Georgia, serif"
SANS = 'Helvetica, Arial, sans-serif'
COL_X = 7480                 # the callout column
ART_R = COL_X - 240          # the drawings' right edge


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

    # The isometric drawing, without its year caption (the sheet has a title of its own).
    vb, iso_body = inner(iso_svg)
    cap = max(28, (vb[2] - 48) * 0.022) * 2.4
    iso_vb = [vb[0], vb[1] + cap, vb[2], vb[3] - cap]
    svb, sec_body = inner(sec_svg)

    top = 760
    iso_box = (M, top, ART_R - M, 4200)
    s_iso, ox_iso, oy_iso = place(iso_vb, iso_box)
    iso_h = iso_vb[3] * s_iso
    # The section, centered in the room between the cutaway and the key.
    s_sec = (ART_R - M) / svb[2]
    sec_h = svb[3] * s_sec
    room_top, room_bottom = top + iso_h + 160, 6330
    sec_top = room_top + max(140, (room_bottom - room_top - sec_h) / 2)
    sec_box = (M, sec_top, ART_R - M, sec_h)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    # Title.
    out.append(text(M, 420, spec['title'], 250, 'bold'))
    out.append(text(M, 600, spec['subtitle'], 112, 'italic', DIM))
    # The drawings.
    out.append(f'<svg x="{iso_box[0]}" y="{iso_box[1]}" width="{iso_box[2]}" height="{iso_box[3]}" viewBox="{" ".join(f"{v:.1f}" for v in iso_vb)}" preserveAspectRatio="xMidYMin meet" overflow="hidden">{iso_body}</svg>')
    s_iso, ox_iso, oy_iso = s_iso, iso_box[0] + (iso_box[2] - iso_vb[2] * s_iso) / 2 - iso_vb[0] * s_iso, iso_box[1] - iso_vb[1] * s_iso
    out.append(text(M, sec_top - 70, spec['sectionCaption'], 76, 'italic', DIM))
    out.append(f'<svg x="{sec_box[0]}" y="{sec_box[1]}" width="{sec_box[2]}" height="{sec_box[3]}" viewBox="{" ".join(f"{v:.1f}" for v in svb)}" preserveAspectRatio="xMidYMin meet">{sec_body}</svg>')
    ox_sec, oy_sec = sec_box[0] + (sec_box[2] - svb[2] * s_sec) / 2 - svb[0] * s_sec, sec_box[1] - svb[1] * s_sec

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

    # Callout badges on the drawings, and the column beside them.
    y = 840
    x = COL_X
    for g in spec['groups']:
        out.append(text(x, y, g['title'].upper(), 58, 'bold', DIM, family=SANS, spacing=4))
        out.append(f'<line x1="{x}" y1="{y + 32}" x2="{W - M}" y2="{y + 32}" stroke="{INK}" stroke-width="4"/>')
        y += 170
        for c in g['callouts']:
            part = (c.get('iso') or {}).get('part') or (c.get('section') or {}).get('part') or ''
            conf = c.get('confidence') or conf_of.get(part.replace('history:', '').split(':')[0], 'approximate')
            c['_conf'] = conf
            if 'iso' in c:
                p = anchor(c['iso'], iso_a)
                if p is not None:
                    out.append(badge(ox_iso + p[0] * s_iso, oy_iso + p[1] * s_iso, c['n'], conf, 46))
            if 'section' in c:
                p = anchor(c['section'], sec_a, sec_a.get('frame'))
                if p is not None:
                    out.append(badge(ox_sec + p[0] * s_sec, oy_sec + p[1] * s_sec, c['n'], conf, 40))
            out.append(badge(x + 56, y - 26, c['n'], conf, 50))
            out.append(text(x + 140, y, c['title'], 74, 'bold'))
            yy = y + 92
            for line in wrap(c['text'], 'regular', 56, W - M - x - 140):
                out.append(text(x + 140, yy, line, 56, 'regular', DIM))
                yy += 76
            y = yy + 74
        y += 60
    # Key, sources, notes, credit.
    ky = 6720 - 120
    out.append(text(M, ky - 120, 'How sure each part is', 80, 'bold'))
    kx = M
    for conf, msg in spec['key']:
        out.append(badge(kx + 46, ky - 26, None, conf, 46))
        out.append(text(kx + 120, ky, msg, 60, 'regular', DIM))
        kx += 120 + font('regular', 60).getlength(msg) + 220
    out.append(text(M, ky + 150, spec['sources'], 50, 'italic', DIM))
    out.append(text(M, ky + 230, spec['notes'], 50, 'italic', DIM))
    out.append(text(W - M, H - 150, spec['credit'], 46, 'regular', DIM, 'end'))
    out.append('</svg>')
    sheet = os.path.join(a.out, f'{name}-sheet.svg')
    open(sheet, 'w').write('\n'.join(out))
    section = os.path.join(a.out, f'{name}-section.svg')
    open(section, 'w').write(sec_svg)
    if a.png:
        C.svg_to_png(sheet, os.path.join(a.out, f'{name}-sheet.png'), a.png)
        C.svg_to_png(section, os.path.join(a.out, f'{name}-section.png'), a.png)
    print(f'wrote {sheet}')


if __name__ == '__main__':
    main()
