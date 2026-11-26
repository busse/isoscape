"""Floods series, final draft (rc1, rc2): one sheet per flood plate, at print size (the house menu
size, 32 x 24 in, unless --size says otherwise), composed as d3's sheets were
(tools/floods/d3/sheet.py: the big map with numbered box frames, the boxes under it, the key,
bearing, scale, credits), with every word read from drafts/richmond-floods/notes.json
(tools/floods/rc1/notes.py) and the stage mark and version on the sheet.

    python3 tools/floods/rc1/sheet.py <sheet-id> <plates-dir> <counts.json> <out> [--dpi 300] [--size 32x24] [--no-boxes]

<sheet-id> is one of notes.json's `sheets`. Shockoe sheets show one plate and its seven boxes;
Manchester sheets show two plates side by side (the headline: with and without today's wall;
or Fran's and 2020's heights) and each box of both. --no-boxes draws the map, captions and key
only (the 1771 estimate). The key shows only what the plate draws (the hatched range where the
flood has one, the wall where it stands, gauges where there are any, pins for Gaston).
Prints the least type size used, in points at the sheet's size.

rc2: a sheet takes its box list from boxes.json (`lists`, by sheet id; else the area's own);
Shockoe maps are all one height (10.6 in) and never show the plate's front face; box pictures
keep the aspect of their frame; boxes 1 to 3 name the place their depth is read at; the key's
rows follow what the plate draws (unknown ground, decks under water, pins, the 1788 town); a
sheet's notes can differ by sheet (`sheetNotes`); badges and frames are checked for overlap.
"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'd3'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'sets'))
import set as SET  # noqa: E402
import sheet as D3  # noqa: E402
import render_boxes as RB  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
Image.MAX_IMAGE_PIXELS = None

ROOT = SET.ROOT
SERIF, SERIF_B, SERIF_I = D3.SERIF, D3.SERIF_B, D3.SERIF_I
LEAST = [1e9]  # the least font size used, px


def F(path, px):
    LEAST[0] = min(LEAST[0], max(6, round(px)))
    return D3.F(path, px)


RIVER = 'The river, canal and basins at their own level'
UNKNOWN = 'Cross-hatched: not known; the earthen levee is not mapped (the edges assume where it runs)'
DECK = 'A bridge deck under the water (deck heights are estimates)'
PINS = 'Lettered pins: places named in reports'


def swatch(d, name, X, Y, P, dpi):
    """The swatch for one key row, its top left at (X, Y); returns its width."""
    I = lambda v: v * dpi
    hx = D3.hexrgb
    ink = hx(P['ink'])
    sw = I(0.3)
    if name == RIVER:
        d.rectangle((X, Y, X + sw * 1.4, Y + sw * 0.8), fill=hx(P['flood']['channel']))
    elif name.startswith('Hatched'):
        D3.hatch_sw(d, X, Y, sw * 1.4, sw * 0.8, P, I)
    elif name == UNKNOWN:
        x1, y1 = X + sw * 1.4, Y + sw * 0.8
        d.rectangle((X, Y, x1, y1), fill=hx(P['flood'].get('unknown', P['land'])))
        step = sw * 0.28
        k = -10
        while k * step < sw * 3:
            for sgn in (1, -1):
                xa = X + k * step
                pts = [(xa, Y), (xa + sgn * (y1 - Y), y1)]
                (ax, ay), (bx, by) = pts
                # clip the diagonal to the rectangle
                tlo, thi = 0.0, 1.0
                for p0, p1, lo, hi in ((ax, bx, X, x1), (ay, by, Y, y1)):
                    dp = p1 - p0
                    if abs(dp) < 1e-9:
                        if p0 < lo or p0 > hi: tlo, thi = 1, 0
                        continue
                    t0, t1 = (lo - p0) / dp, (hi - p0) / dp
                    tlo, thi = max(tlo, min(t0, t1)), min(thi, max(t0, t1))
                if tlo < thi:
                    d.line([(ax + (bx - ax) * tlo, ay + (by - ay) * tlo), (ax + (bx - ax) * thi, ay + (by - ay) * thi)], fill=hx(P['flood'].get('unknownHatch', P['ink'])), width=max(1, round(I(0.01))))
            k += 1
        d.rectangle((X, Y, x1, y1), outline=hx(P['flood'].get('unknownHatch', P['ink'])), width=1)
    elif name.startswith('A building'):
        D3.cube(d, X + sw * 0.1, Y - sw * 0.25, sw * 1.2, hx(P['wallLit']), hx(P['wallShade']), hx(P['roof']), ink)
    elif name.startswith('Grey, dashed'):
        D3.cube(d, X + sw * 0.1, Y - sw * 0.25, sw * 1.2, hx(P['mix']), hx(P['mixShade']), hx(P['mixRoof']), ink, dash=hx(P['flood']['unconfirmed']['outline']['color']))
    elif name.startswith('The floodwall'):
        d.line([(X, Y + sw * 0.4), (X + sw * 1.4, Y + sw * 0.4)], fill=hx(P['flood']['wallCasing']), width=round(I(0.1)))
        d.line([(X, Y + sw * 0.4), (X + sw * 1.4, Y + sw * 0.4)], fill=hx(P['flood']['wallLine']), width=round(I(0.055)))
    elif name == DECK:
        d.rectangle((X, Y, X + sw * 1.4, Y + sw * 0.8), fill=hx(P['flood']['tones'][4]))
        d.polygon([(X + sw * 0.1, Y + sw * 0.55), (X + sw * 1.3, Y + sw * 0.15), (X + sw * 1.3, Y + sw * 0.35), (X + sw * 0.1, Y + sw * 0.75)], fill=hx(P['deckUnder']))
    elif name.startswith('A depth gauge'):
        d.line([(X + sw * 0.6, Y - sw * 0.2), (X + sw * 0.6, Y + sw)], fill=ink, width=max(2, round(I(0.02))))
        for k in range(4):
            d.line([(X + sw * 0.6, Y + k * sw * 0.3), (X + sw * 0.85, Y + k * sw * 0.3)], fill=ink, width=max(1, round(I(0.008))))
    elif name == PINS:
        SET.marker(d, X + sw * 0.7, Y + sw * 0.4, 'A', sw * 0.45)
    return sw * 1.4


def ramp(d, x, y, P, dpi, f, fs, label='Water, by depth (ft)'):
    I = lambda v: v * dpi
    sw = I(0.3)
    tones, bands = P['flood']['tones'], P['flood']['bands']
    d.text((x, y), label, font=f, fill=D3.hexrgb(P['ink']))
    for i, t in enumerate(tones):
        d.rectangle((x + i * sw, y + I(0.26), x + (i + 1) * sw, y + I(0.26) + sw), fill=D3.hexrgb(t))
        if i % 2 == 0 or i == len(tones) - 1:
            d.text((x + i * sw, y + I(0.26) + sw + I(0.02)), f"{round(bands[i] / 0.3048)}", font=fs, fill=D3.hexrgb(P['ink']))
    return len(tones) * sw


def key_rows(d, x, y, w, P, dpi, rows):
    """The key stacked in one column: the depth ramp, then one swatch a line."""
    I = lambda v: v * dpi
    ink = D3.hexrgb(P['ink'])
    f, fs = F(SERIF, I(0.15)), F(SERIF_I, I(0.13))
    sw = I(0.3)
    ramp(d, x, y, P, dpi, f, fs)
    yy = y + I(0.95)
    for name in rows:
        swatch(d, name, x, yy, P, dpi)
        lines = wrapk(d, name, f, w - sw * 2.2)
        for j, ln in enumerate(lines):
            d.text((x + sw * 2.0, yy - I(0.02) + j * I(0.2)), ln, font=f, fill=ink)
        yy += I(0.38) + I(0.2) * (len(lines) - 1)
    return yy


def key_band(d, x, y, P, dpi, rows, maxw):
    """The key in one band, left to right: the ramp, then each swatch with its name over it."""
    I = lambda v: v * dpi
    ink = D3.hexrgb(P['ink'])
    f, fs = F(SERIF, I(0.15)), F(SERIF_I, I(0.13))
    cx = x + ramp(d, x, y, P, dpi, f, fs) + I(0.5)
    for name in rows:
        lines = wrapk(d, name, f, I(2.6))
        wtext = max(d.textlength(l, font=f) for l in lines)
        swatch(d, name, cx, y + I(0.3) + I(0.2) * (len(lines) - 1), P, dpi)
        for j, ln in enumerate(lines):
            d.text((cx, y + j * I(0.2)), ln, font=f, fill=ink)
        cx += max(wtext, I(0.42)) + I(0.4)
    return cx


def rows_for(fl, f1, info, area, second_fl=None, second_info=None):
    """The key's rows: what the plate (and its pair) draws."""
    flags = [fl] + ([second_fl] if second_fl else [])
    infos = [info] + ([second_info] if second_info else [])
    rows = [RIVER]
    if any((x.get('uncertainty') or 0) > 0 for x in flags):
        rows.append('Hatched: the range of an estimate')
    if any('floodUnknownAcres' in i for i in infos):
        rows.append(UNKNOWN)
    rows.append('A building standing in 1788 (by its year built)' if f1 == '1771' else 'A building of the year')
    if area == 'shockoe' and f1 != '1771':
        rows.append('Grey, dashed roof edge: on an earlier map or photo, not ascertained for the year')
    if any(x.get('walls') for x in flags) and f1 != '1771':
        rows.append('The floodwall (1994), where it stands')
    if any((i.get('floodDeckSpansAwash') or 0) > 0 for i in infos):
        rows.append(DECK)
    if any(i.get('_gauges') for i in infos):  # a gauge is drawn only where its place is under water
        rows.append('A depth gauge, the figure in feet')
    if fl.get('markers'):
        rows.append(PINS)
    return rows


def labels_mask(src, box, w, h):
    """The map's labels and their halos alone, as a mask at the map's size (None if it has none)."""
    g = re.search(r'<g class="labels".*?</g>', src, re.S)
    if not g:
        return None
    head = re.match(r'<\?xml[^>]*>\s*<svg[^>]*>|<svg[^>]*>', src, re.S).group(0)
    svg = head + g.group(0) + '</svg>'
    svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{box[0]:.2f} {box[1]:.2f} {box[2]:.2f} {box[3]:.2f}"', svg, count=1)
    svg = svg.replace('<svg ', f'<svg width="{w}" height="{h}" preserveAspectRatio="none" ', 1)
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        p, o = os.path.join(t, 'l.svg'), os.path.join(t, 'l.png')
        open(p, 'w', encoding='utf-8').write(svg)
        SET.subprocess.run(['rsvg-convert', '-w', str(w), '-h', str(h), p, '-o', o], check=True)
        a = Image.open(o).convert('RGBA').getchannel('A')
    return a.point(lambda v: 255 if v > 8 else 0).filter(ImageFilter.MaxFilter(3))


UNITS = r'(ft|in|m|acres|sq mi|square miles|inches|cfs|p\.m\.|a\.m\.)'
LAID = []  # every line of text laid out on the sheet, in order (written to the .maps.json)


def refuse_split(lines):
    """Stop the sheet if a figure ends one line and its unit begins the next ("13.4 / ft")."""
    for a_, b_ in zip(lines, lines[1:]):
        if re.search(r'\d$', a_.rstrip()) and re.match(UNITS + r'\b', b_.lstrip()):
            raise SystemExit(f"refused: a figure split from its unit: {a_[-30:]!r} / {b_[:20]!r}")
    LAID.extend(lines)
    return lines


def keep(t):
    """A figure stays on the line of its unit ('13.4 ft', '6 ft 2 in', '9:15 p.m.'): the space
    between them is held by a '|' while the words are wrapped (str.split breaks at a no-break space)."""
    return re.sub(r'(\d) ' + UNITS + r'(?=\W|$)', '\\1|\\2', t)


def wrapk(d, text, f, w):
    return refuse_split([ln.replace('|', ' ') for ln in SET.wrap(d, keep(text), f, w)])


def rain_panel(d, x, y, w, h, R, P, dpi):
    """The rain over the watershed, by hour (Gaston sheet, rc3): bars with the range of estimates,
    the timed events as thin lines, a caption and a source line, in the sheet's type and palette."""
    I = lambda v: v * dpi
    hx = D3.hexrgb
    ink, paper = hx(P['ink']), hx(P['sky'])
    light = tuple(round(a_ * 0.18 + b_ * 0.82) for a_, b_ in zip(ink, paper))
    bar = hx(P['flood']['tones'][4])
    accent = SET.ACCENT
    tf, nf, sf, af = F(SERIF_B, I(0.17)), F(SERIF, I(0.135)), F(SERIF, I(0.13)), F(SERIF_I, I(0.13))
    d.text((x, y), R['title'], font=tf, fill=ink)
    LAID.append(R['title'])
    yy = y + I(0.3)
    for ln in wrapk(d, R['caption'], nf, w):
        d.text((x, yy), ln, font=nf, fill=ink); yy += I(0.19)
    src = wrapk(d, R['source'], sf, w)
    foot = y + h - len(src) * I(0.18)
    for j, ln in enumerate(src):
        d.text((x, foot + j * I(0.18)), ln, font=sf, fill=ink)
    # the plot: hours 1 p.m. to 11 p.m. across; 0 to 2.5 in up
    lab_w = d.textlength('2.5', font=af) + I(0.1)
    px0, px1 = x + lab_w, x + w - I(0.1)
    ev_rows = 2
    py0 = yy + I(0.15) + ev_rows * I(0.2)
    py1 = foot - I(0.45)
    h0, h1, top = R['hours'][0], R['hours'][-1] + 1, 2.5
    X = lambda t: px0 + (t - h0) / (h1 - h0) * (px1 - px0)
    Y = lambda v: py1 - v / top * (py1 - py0)
    for v in (0, 0.5, 1, 1.5, 2, 2.5):
        d.line([(px0, Y(v)), (px1, Y(v))], fill=light if v else ink, width=max(1, round(I(0.006 if v else 0.01))))
        if v == int(v):
            t = f'{v:g} in' if v == 2 else f'{v:g}'
            d.text((px0 - I(0.08) - d.textlength(t, font=af), Y(v) - I(0.09)), t, font=af, fill=ink)
    # the events, behind the bars: a thin line from the axis to its label, labels on two rows
    ends = [-1e9] * ev_rows
    for t_, label in R['events']:
        tw = d.textlength(label, font=af)
        lx = min(X(t_) - I(0.04), px1 - tw)
        row = next((k for k in range(ev_rows) if lx > ends[k] + I(0.15)), ev_rows - 1)
        ends[row] = lx + tw
        ly = yy + I(0.12) + row * I(0.2)
        d.line([(X(t_), ly + I(0.18)), (X(t_), Y(0))], fill=accent, width=max(1, round(I(0.012))))
        d.text((lx, ly), label, font=af, fill=accent)
        LAID.append(label)
    for hr, v, lo, hi in zip(R['hours'], R['inches'], R['low'], R['high']):
        d.rectangle((X(hr + 0.1), Y(v), X(hr + 0.9), Y(0)), fill=bar)
        if hi - lo > 0.02:
            cx = X(hr + 0.5)
            d.line([(cx, Y(lo)), (cx, Y(hi))], fill=ink, width=max(1, round(I(0.008))))
            for q in (lo, hi):
                d.line([(cx - I(0.04), Y(q)), (cx + I(0.04), Y(q))], fill=ink, width=max(1, round(I(0.008))))
    for hr in range(h0, h1 + 1):
        t = f"{hr - 12} p.m." if hr in (h0, h1) else f"{hr - 12}"
        tw = d.textlength(t, font=af)
        d.line([(X(hr), Y(0)), (X(hr), Y(0) + I(0.05))], fill=ink, width=max(1, round(I(0.008))))
        d.text((min(max(X(hr) - tw / 2, px0), px1 - tw), Y(0) + I(0.07)), t, font=af, fill=ink)


def ft(v):
    """Feet as a whole number, halves up (as the gauges round them)."""
    return int(v + 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet'); ap.add_argument('plates'); ap.add_argument('counts'); ap.add_argument('out')
    ap.add_argument('--dpi', type=float, default=300); ap.add_argument('--size', default='32x24'); ap.add_argument('--no-boxes', action='store_true')
    a = ap.parse_args()
    N = json.load(open(os.path.join(ROOT, 'drafts/richmond-floods/notes.json')))
    sh = next(s for s in N['sheets'] if s['id'] == a.sheet)
    area = sh['area']
    dpi = a.dpi
    I = lambda v: v * dpi
    spec = json.load(open(os.path.join(ROOT, 'tools/floods/d3/boxes.json')))
    A = spec[area]
    # The sheet's own box list where it has one (`lists`), else the area's.
    lst = next((l for l in (A.get('lists') or {}).values() if sh['id'] in l['sheets']), None)
    src_boxes, size = (lst['boxes'], lst['size']) if lst else (A['boxes'], A['size'])
    over = N.get('sheetNotes', {}).get(sh['id'], {})
    boxes = [] if a.no_boxes else [{**b, **N['boxes'][area][b['id']], **({'note': over[b['id']]['note']} if b['id'] in over else {})} for b in src_boxes]
    counts = json.load(open(a.counts))
    counts = counts['rc3']['boxes'][area] if 'rc3' in counts else counts
    region = json.load(open(os.path.join(ROOT, 'regions', A['region'] + '.json')))
    P = D3.pal()
    ink, paper = D3.hexrgb(P['ink']), D3.hexrgb(P['sky'])
    accent = SET.ACCENT
    sw_in, sh_in = map(float, a.size.split('x'))
    W, H = round(I(sw_in)), round(I(sh_in))
    img = Image.new('RGB', (W, H), paper)
    d = ImageDraw.Draw(img)
    m = I(0.6)
    f1, y1 = sh['plate'].split(':'); y1 = int(y1)
    second = sh.get('second')
    f2, y2 = (second.split(':')[0], int(second.split(':')[1])) if second else (None, None)
    svg1 = os.path.join(a.plates, f"{A['region']}-{y1}-flood-{f1}.svg")
    svg2 = os.path.join(a.plates, f"{A['region']}-{y2}-flood-{f2}.svg") if second else None
    fl = region['floods'][f1]
    info1 = json.load(open(svg1[:-4] + '.info.json'))
    info2 = json.load(open(svg2[:-4] + '.info.json')) if second else None
    info1['_gauges'] = 'data-id="floodgauge:' in open(svg1).read()
    if second:
        info2['_gauges'] = 'data-id="floodgauge:' in open(svg2).read()
    cap = N['captions'][f'{area}:{f1}:{y1}']['lines']
    # Title band: the title, the caption lines, the stage and version.
    d.text((m, m - I(0.05)), sh['title'], font=F(SERIF_B, I(0.46)), fill=ink)
    lines = cap[:3]
    if second:
        cap2 = N['captions'][f'{area}:{f2}:{y2}']['lines']
        if f2.endswith('nowall'):
            lines = [cap[0], f"With the wall: {info1['floodAcres']} acres under water off the channel, plus {info1['floodUnknownAcres']} acres not known ({info1['floodUnknownBuildings']} buildings on it); {info1['floodShownInWater']} buildings in the water. "
                             f"Without it: {info2['floodAcres']} acres, {info2['floodShownInWater']} buildings.", cap[2]]
        else:
            lines = [f"Left: {cap[0]}", f"Right: {cap2[0]}", f"Left: {cap[1]}", f"Right: {cap2[1]}", cap[2]]
    y = m + I(0.62)
    fcap = I(0.17)
    for i, ln in enumerate(lines):
        for ln2 in wrapk(d, ln, F(SERIF_I if i == 0 else SERIF, fcap), W - 2 * m - I(4)):
            d.text((m, y), ln2, font=F(SERIF_I if i == 0 else SERIF, fcap), fill=ink); y += I(0.26)
    stage = N['stage']
    sf = F(SERIF_B, I(0.24))
    d.text((W - m - d.textlength(stage, font=sf), m), stage, font=sf, fill=accent)
    vf = F(SERIF, I(0.15))
    vt = f"{N['version']} · not for sale · {sh['id']}"
    d.text((W - m - d.textlength(vt, font=vf), m + I(0.34)), vt, font=vf, fill=ink)
    top = max(m + I(1.55), y + I(0.15))
    d.line((m, top - I(0.12), W - m, top - I(0.12)), fill=ink, width=max(1, round(I(0.012))))
    mw = W - 2 * m
    foot_top = H - m - I(0.5)
    g = I(0.25)
    text_h = I(1.12)
    # The box grid: Shockoe's own seven in 4 x 2 (the key in the last cell); a sheet's own list in
    # rows of three (the key in the cells left over); Manchester's five in one row, each pair stacked.
    if not boxes:
        cols = nrows = 0
    elif area == 'shockoe' and lst is None:
        cols, nrows = 4, 2
    elif area == 'shockoe':
        cols = 3
        nrows = -(-(len(boxes) + 1) // cols)
    else:
        cols, nrows = len(boxes), 1
    stack = 2 if second else 1
    pts = []
    if boxes:
        out = SET.subprocess.run(['node', 'bin/isoscape.js', 'locate', A['region'], '--year', str(y1), '--', *[f"{b['at'][0]},{b['at'][1]}" for b in boxes]], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        pts = [(p['x'], p['y']) for p in json.loads(out)]
    sc1 = SET.Scene(svg1, A['region'])
    scenes = [sc1] + ([SET.Scene(svg2, A['region'])] if second else [])
    for sc in scenes:
        # The plate's front face never shows: the ground alone is measured, whatever pattern
        # definitions (a hatch) stand between the paper's rectangle and the face.
        sc.ground_src = re.sub(r'(<rect [^\n]*/>\n)((?:<defs><pattern[^\n]*</defs>\n)*)(?:<path (?:class="i" )?fill="[^"]+" d="[^"]*"/>\n)+(?=<defs><clipPath id="above">)', r'\1\2', sc.src, count=1)
        sc._content = None
    cov = sc1.covered()
    if not second:
        if boxes:
            h = I(10.6) if area == 'shockoe' else mw * cov[3] / cov[2]
            maps = [(sc1, m, top, mw, h)]
        else:
            mw1 = mw - I(5.0)  # a key column at the right
            h = min(mw1 * cov[3] / cov[2], foot_top - I(0.6) - top)
            maps = [(sc1, m, top, h * cov[2] / cov[3], h)]
    else:
        gap = I(0.3)
        w = (mw - gap) / 2
        h = I(6.2) if boxes else min(w * cov[3] / cov[2], foot_top - I(1.6) - top)
        maps = [(sc1, m, top, w, h), (scenes[1], m + w + gap, top, w, h)]
    my = top + maps[0][4]
    key_band_h = I(1.0) if (area == 'manchester') else 0
    if boxes:
        cw = (mw - (cols - 1) * g) / cols
        cell_h = (foot_top - I(0.25) - key_band_h - (my + I(0.3)) - (nrows - 1) * g) / nrows
        ih = (cell_h - text_h - (stack - 1) * I(0.06)) / stack
        BW = size[0]
        # The frame keeps its picture's aspect. A list whose boxes are taller than the cell's
        # shape draws its pictures narrower than the cell, left-aligned, with the text full width.
        BH = size[1]
        pw = ih * BW / BH
        if pw > cw:
            pw, BH = cw, BW * ih / cw
            if abs(BH - size[1]) > 3:
                print(f"note: {sh['id']} boxes drawn {BW} x {BH:.0f} units; boxes.json says {size}", file=sys.stderr)
    else:
        BW = BH = pw = 0
    corners = [(px + sx * BW / 2, py + sy * BH / 2) for px, py in pts for sx in (-1, 1) for sy in (-1, 1)]
    px_per_unit = None
    sc_path = [svg1, svg2]
    MAPS = []  # where each plate sits on the sheet: sheet px = sheetX + (svg x - viewBox x) * pxPerUnit
    FRAMES = []
    labels2 = {'agnes-today': "With today's wall", 'agnes-today-nowall': 'Without it', '1996': "Fran's height, 1996", '2020': 'The November 2020 height'}
    for k, (sc, x, yy, w, h) in enumerate(maps):
        box = SET.map_box(sc, w / h, corners, pad=0.02)
        kk = w / box[2]
        # Map type under 7.5 pt at this scale (a gauge's place name on a half-width map) is set up to it.
        least_units = 7.5 / 72 * dpi / kk
        sc.src = re.sub(r'font-size="([0-9.]+)"', lambda mm: f'font-size="{max(float(mm.group(1)), least_units) if float(mm.group(1)) < 30 else float(mm.group(1)):.1f}"', sc.src)
        # A wall's label that would sit on the map's bottom edge (on the stub of wall it names, at
        # the frame line) is moved clear of both: its baseline 1.3 type sizes above the edge, and
        # 0.6 of its width to the left, so it ends short of the stub.
        def lift(mm):
            tx, ty, fs, txt = float(mm.group(2)), float(mm.group(4)), float(mm.group(6)), mm.group(8)
            bottom = box[1] + box[3]
            if ty + 0.4 * fs > bottom - 1.0 * fs:
                lw = 0.56 * fs * len(txt)
                ty, tx = bottom - 1.3 * fs, tx - 0.6 * lw
            return f'{mm.group(1)}{tx:.1f}{mm.group(3)}{ty:.1f}{mm.group(5)}{fs:g}{mm.group(7)}{txt}'
        sc.src = re.sub(r'(<text x=")([-0-9.]+)(" y=")([-0-9.]+)(" font-size=")([0-9.]+)("[^>]*>)(Floodwall[^<]*)', lift, sc.src)
        mimg = sc.render(box, round(w), round(h))
        img.paste(mimg, (round(x), round(yy)))
        # Where a box frame would cross a map label (the wall's, a gauge's, a pin's), the label, with
        # its halo and nothing else, is laid back over it.
        MAPS.append({'svg': os.path.basename(sc_path[k]), 'sheetX': round(x, 1), 'sheetY': round(yy, 1), 'viewBox': [round(v, 2) for v in box], 'pxPerUnit': round(kk, 5)})
        px_per_unit = kk
        for b, (px, py) in zip(boxes, pts):
            X0, Y0 = x + (px - BW / 2 - box[0]) * kk, yy + (py - BH / 2 - box[1]) * kk
            X1, Y1 = X0 + BW * kk, Y0 + BH * kk
            if X0 < x - 1 or Y0 < yy - 1 or X1 > x + w + 1 or Y1 > yy + h + 1:
                print(f"WARNING: {sh['id']} box {b['n']} cut by the map's edge", file=sys.stderr)
            X0, Y0, X1, Y1 = max(X0, x), max(Y0, yy), min(X1, x + w), min(Y1, yy + h)
            d.rectangle((X0, Y0, X1, Y1), outline=accent, width=max(2, round(I(0.03))))
            FRAMES.append((k, b['n'], X0, Y0, X1, Y1))
        lm = labels_mask(sc.src, box, round(w), round(h))
        if lm is not None:
            img.paste(mimg, (round(x), round(yy)), lm)
        # Badges last, over the labels laid back.
        for b, (_, n, X0, Y0, X1, Y1) in zip(boxes, [f for f in FRAMES if f[0] == k]):
            SET.marker(d, min(max(X0, x + I(0.18)), x + w - I(0.18)), min(max(Y0, yy + I(0.18)), yy + h - I(0.18)), b['n'], I(0.16))
        d.rectangle((x, yy, x + w, yy + h), outline=ink, width=max(1, round(I(0.01))))
        if second:
            lab = labels2[[f1, f2][k]]
            lf = F(SERIF_B, I(0.22))
            d.rectangle((x + I(0.1), yy + I(0.1), x + I(0.3) + d.textlength(lab, font=lf), yy + I(0.45)), fill=paper)
            d.text((x + I(0.2), yy + I(0.12)), lab, font=lf, fill=ink)
    # No badge inside another frame, no two frames overlapping.
    r_b = I(0.16) * 1.15
    for k, n, X0, Y0, X1, Y1 in FRAMES:
        for k2, n2, A0, B0, A1, B1 in FRAMES:
            if k2 != k or n2 == n:
                continue
            if X0 - r_b < A1 and X0 + r_b > A0 and Y0 - r_b < B1 and Y0 + r_b > B0:
                print(f"WARNING: {sh['id']} badge {n} touches frame {n2}", file=sys.stderr)
            if n < n2 and X0 < A1 and X1 > A0 and Y0 < B1 and Y1 > B0:
                print(f"WARNING: {sh['id']} frames {n} and {n2} overlap", file=sys.stderr)
    rows = rows_for(fl, f1, info1, area, region['floods'][f2] if second else None, info2)
    tf, sf2, nf = F(SERIF_B, I(0.17)), F(SERIF_I, I(0.145)), F(SERIF, I(0.135))
    if boxes:
        for i, (b, (px, py)) in enumerate(zip(boxes, pts)):
            c, r = i % cols, i // cols
            x = m + c * (cw + g)
            yy = my + I(0.3) + r * (cell_h + g)
            pics = [RB.crop(svg1, px, py, BW, BH, round(pw))] + ([RB.crop(svg2, px, py, BW, BH, round(pw))] if stack == 2 else [])
            for kk2, pimg in enumerate(pics):
                img.paste(pimg.resize((round(pw), round(ih))), (round(x), round(yy)))
                d.rectangle((x, yy, x + pw, yy + ih), outline=ink, width=max(1, round(I(0.006))))
                if stack == 2:
                    lab = {'agnes-today': 'with the wall', 'agnes-today-nowall': 'without it', '1996': "Fran's height", '2020': '2020 height'}[[f1, f2][kk2]]
                    d.rectangle((x + I(0.04), yy + I(0.04), x + I(0.12) + d.textlength(lab, font=sf2), yy + I(0.26)), fill=paper)
                    d.text((x + I(0.08), yy + I(0.05)), lab, font=sf2, fill=ink)
                yy += ih + I(0.06)
            rr = SET.marker(d, x + I(0.15), yy + I(0.15), b['n'], I(0.15))
            d.text((x + 2 * rr + I(0.08), yy + I(0.02)), b['title'], font=tf, fill=ink)
            c1 = counts[f'{f1}:{y1}'][b['id']]
            place = f"at {b['depthName']}" if b.get('depthName') else "at the box's center"
            if area == 'shockoe':
                dep = f"{ft(c1['depthFt'])} ft deep {place}" if c1['depthFt'] >= 0.5 else f"dry {place}"
                if f1.startswith('gaston'):
                    dep = 'at 28 ft, ' + dep
                dep += (f"; {c1['inWater']} building{'s' if c1['inWater'] != 1 else ''} in the water" + (f" ({c1['inWaterUnconfirmed']} grey)" if c1['inWaterUnconfirmed'] else '') if c1['inWater'] else '')
            else:
                c2 = counts[f'{f2}:{y2}'][b['id']]
                unk = b['id'] == 'plant'
                if f2.endswith('nowall'):
                    dep = ('not known with the wall' if unk else 'dry behind the wall' if c1['depthFt'] < 0.5 else f"{ft(c1['depthFt'])} ft deep with the wall") + f"; {ft(c2['depthFt'])} ft without it ({place})"
                else:
                    dep = 'not known at either height' if unk else f"Fran's height: {'dry' if c1['depthFt'] < 0.5 else str(ft(c1['depthFt'])) + ' ft'}; 2020's: {'dry' if c2['depthFt'] < 0.5 else str(ft(c2['depthFt'])) + ' ft'} ({place})"
            d.text((x, yy + I(0.36)), dep, font=sf2, fill=accent)
            nl = wrapk(d, b['note'], nf, cw)
            if len(nl) > 3:
                print(f"WARNING: {sh['id']} box {b['n']} note runs to {len(nl)} lines", file=sys.stderr)
            for j2, ln in enumerate(nl[:3]):
                d.text((x, yy + I(0.58) + j2 * I(0.19)), ln, font=nf, fill=ink)
        if area == 'shockoe':
            i = len(boxes)
            c, r = i % cols, i // cols
            kx, ky = m + c * (cw + g), my + I(0.3) + r * (cell_h + g)
            kw = W - m - kx
            d.text((kx, ky), 'Key', font=F(SERIF_B, I(0.2)), fill=ink)
            key_rows(d, kx, ky + I(0.4), min(kw, cw), P, dpi, rows)
            bx, by2 = kx, ky + cell_h - I(0.55)
            if N.get('rain') and sh['id'] == 'shockoe-2004' and len(boxes) + 1 < cols * nrows:
                i = len(boxes) + 1
                c, r = i % cols, i // cols
                rain_panel(d, m + c * (cw + g), my + I(0.3) + r * (cell_h + g), cw, cell_h, N['rain'], P, dpi)
        else:
            ky = foot_top - I(0.25) - key_band_h + I(0.1)
            end = key_band(d, m, ky, P, dpi, rows, mw)
            bx, by2 = end + I(0.2), ky
    elif second:
        # A panel of two plates: the key in a band under them.
        ky = my + I(0.35)
        end = key_band(d, m, ky, P, dpi, rows, mw)
        bx, by2 = end + I(0.2), ky
    else:
        # No boxes: the key in a column right of the map.
        kx = m + maps[0][3] + I(0.5)
        d.text((kx, top), 'Key', font=F(SERIF_B, I(0.2)), fill=ink)
        kend = key_rows(d, kx, top + I(0.4), W - m - kx, P, dpi, rows)
        bx, by2 = kx, kend + I(0.3)
    nf2 = F(SERIF, I(0.15))
    pts16 = ['north', 'north-northeast', 'northeast', 'east-northeast', 'east', 'east-southeast', 'southeast', 'south-southeast', 'south', 'south-southwest', 'southwest', 'west-southwest', 'west', 'west-northwest', 'northwest', 'north-northwest']
    D3.north(d, bx + I(0.4), by2 + I(0.45), I(0.35), region['bearing'], region.get('squash', 0.5), ink, F(SERIF_B, I(0.18)))
    d.text((bx + I(1.0), by2), f"The view looks {pts16[round(region['bearing'] / 22.5) % 16]} ({region['bearing']:.0f}°)", font=nf2, fill=ink)
    D3.scalebar(d, bx + I(1.0), by2 + I(0.4), px_per_unit * region['scale'], ink, F(SERIF, I(0.13)))
    ff = F(SERIF, I(0.13))
    for j, ln in enumerate(wrapk(d, N['credits'].get(sh['id'], N['credits'][area])['text'], ff, mw)):
        d.text((m, foot_top + j * I(0.19)), ln, font=ff, fill=ink)
    if a.out.lower().endswith(('.jpg', '.jpeg')):
        img.save(a.out, quality=92, optimize=True, dpi=(dpi, dpi))
    else:
        img.save(a.out, dpi=(dpi, dpi))
    json.dump({'sheet': sh['id'], 'dpi': dpi, 'lines': LAID, 'maps': MAPS, 'frames': [{'map': k, 'n': n, 'box': [round(v) for v in (X0, Y0, X1, Y1)]} for k, n, X0, Y0, X1, Y1 in FRAMES]},
              open(os.path.splitext(a.out)[0] + '.maps.json', 'w'), indent=1)
    print(json.dumps({'out': a.out, 'px': img.size, 'inches': [sw_in, sh_in], 'dpi': dpi, 'leastPt': round(LEAST[0] / dpi * 72, 1),
                      'mapIn': round(maps[0][4] / dpi, 2), 'bytes': os.path.getsize(a.out)}))


if __name__ == '__main__':
    main()
