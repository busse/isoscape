"""Floods series d3: one 4:3 sheet per area, menu style: the big map (or, for Manchester, the
pair with and without today's wall) large, numbered box frames on it, the boxes in a row under
it with title, depth and a one-line note, a title, three caption lines, a key, a bearing note
with a north arrow, a scale bar, credits and the draft's stage.

    python3 tools/floods/d3/sheet.py <area> <plates-dir> <counts.json> <out.png> [--dpi 100]

A composed sheet, not set.py's menu: the menu frames up to fourteen boxes in a ring of a 5 x 4
grid and keys a set by names only, where a flood sheet needs a map of 2:1, a row of boxes and a
key with swatches. It borrows the set tooling's pieces (tools/sets/set.py: Scene for the plate
without its caption, map_box for the cut, marker for the numbers). Every color in the key is
read from palette.ts (node), none is set here.
"""
import json, math, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sets'))
import set as SET  # noqa: E402
from PIL import Image, ImageDraw, ImageFont

ROOT = SET.ROOT
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SERIF_I = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf'
STYLES = ['blue-grey', 'wall-cased-red', 'xray-heavy', 'unconfirmed-slate-both']
CREDIT = {
    'shockoe': ('Water levels: USGS (high-water marks, PP 924, HA-410), NOAA and the National Weather Service. Ground: USGS 3DEP lidar. '
                'Buildings: © OpenStreetMap contributors (ODbL); City of Richmond assessor; Sanborn maps, Library of Congress; '
                'air photos: USGS 1974 orthophoto, City of Richmond 1999 and VGIN 2002, 2017 and 2021 orthophotos.'),
    'manchester': ('Water levels: USGS (high-water marks, PP 924, HA-410), NOAA and the National Weather Service. Ground: USGS 3DEP lidar. '
                   'Buildings: © OpenStreetMap contributors (ODbL); City of Richmond assessor.'),
}
BYLINE = 'Drawn with isoscape by Chris Busse; made in code with Claude.'


def pal():
    js = ("import('./src/palette.ts').then(m => { const p = m.withFloodStyles(m.palette('paper'), " + json.dumps(STYLES) + ");"
          " console.log(JSON.stringify({ flood: p.flood, wallLit: p.wallLit, wallShade: p.wallShade, roof: p.roofs.commercial[1], ink: p.ink, land: p.land, sky: p.sky, water: p.water, mix: m.mix(p.wallLit, p.flood.unconfirmed.tone, p.flood.unconfirmed.share), mixShade: m.mix(p.wallShade, p.flood.unconfirmed.tone, p.flood.unconfirmed.share), mixRoof: m.mix(p.roofs.commercial[1], p.flood.unconfirmed.roofTone, p.flood.unconfirmed.roofShare), deckUnder: m.mix(p.flood.tones[p.flood.tones.length - 1], p.flood.streets, 0.55) })) })")
    return json.loads(subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout)


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def F(path, px):
    return ImageFont.truetype(path, max(6, round(px)))


def cube(d, x, y, s, wall, shade, roof, ink, dash=None):
    """A small building: a roof and two walls, s px across."""
    h = s * 0.55
    top = [(x, y + s * 0.25), (x + s * 0.5, y), (x + s, y + s * 0.25), (x + s * 0.5, y + s * 0.5)]
    left = [(x, y + s * 0.25), (x + s * 0.5, y + s * 0.5), (x + s * 0.5, y + s * 0.5 + h), (x, y + s * 0.25 + h)]
    right = [(x + s * 0.5, y + s * 0.5), (x + s, y + s * 0.25), (x + s, y + s * 0.25 + h), (x + s * 0.5, y + s * 0.5 + h)]
    for poly, c in ((left, wall), (right, shade), (top, roof)):
        d.polygon(poly, fill=c, outline=ink)
    if dash:
        pts = top + [top[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = 6
            for k in range(0, n, 2):
                d.line([(ax + (bx - ax) * k / n, ay + (by - ay) * k / n), (ax + (bx - ax) * (k + 1) / n, ay + (by - ay) * (k + 1) / n)], fill=dash, width=max(1, round(s / 18)))


def key(d, x, y, w, h, P, dpi, area, gauges=None, band=None):
    """The key, a band of swatches with their names, left to right."""
    I = lambda v: v * dpi
    ink = hexrgb(P['ink'])
    f, fs = F(SERIF, I(0.16)), F(SERIF_I, I(0.14))
    sw = I(0.34)
    cx = x
    # Water by depth: the nine tones with feet under them.
    d.text((cx, y), 'Water, by depth', font=f, fill=ink)
    tones, bands = P['flood']['tones'], P['flood']['bands']
    for i, t in enumerate(tones):
        d.rectangle((cx + i * sw, y + I(0.3), cx + (i + 1) * sw, y + I(0.3) + sw), fill=hexrgb(t))
        if i % 2 == 0 or i == len(tones) - 1:
            d.text((cx + i * sw, y + I(0.3) + sw + I(0.04)), f"{round(bands[i] / 0.3048)}", font=fs, fill=ink)
    d.text((cx + len(tones) * sw + I(0.08), y + I(0.3) + sw + I(0.04)), 'ft', font=fs, fill=ink)
    cx += len(tones) * sw + I(0.6)
    items = []
    items.append(('The river\'s own channel', lambda X, Y: d.rectangle((X, Y, X + sw * 1.6, Y + sw), fill=hexrgb(P['flood']['channel']))))

    def hatch(X, Y):
        d.rectangle((X, Y, X + sw * 1.6, Y + sw), fill=hexrgb(P['flood']['band']))
        for k in range(-4, 8):
            x0 = X + k * sw * 0.25
            d.line([(max(X, x0), Y + sw - max(0, X - x0)), (min(X + sw * 1.6, x0 + sw), Y + max(0, (x0 + sw) - (X + sw * 1.6)))], fill=hexrgb(P['flood']['bandHatch']), width=max(1, round(I(0.012))))
    if (area == 'shockoe') if band is None else band:
        items.append(('Range of an estimate', hatch))
    items.append(('Building', lambda X, Y: cube(d, X, Y - sw * 0.2, sw * 1.3, hexrgb(P['wallLit']), hexrgb(P['wallShade']), hexrgb(P['roof']), ink)))
    if area == 'shockoe':
        items.append(('Not ascertained for the year', lambda X, Y: cube(d, X, Y - sw * 0.2, sw * 1.3, hexrgb(P['mix']), hexrgb(P['mixShade']), hexrgb(P['mixRoof']), ink, dash=hexrgb(P['flood']['unconfirmed']['outline']['color']))))

    def wall(X, Y):
        d.line([(X, Y + sw * 0.5), (X + sw * 1.6, Y + sw * 0.5)], fill=hexrgb(P['flood']['wallCasing']), width=round(I(0.11)))
        d.line([(X, Y + sw * 0.5), (X + sw * 1.6, Y + sw * 0.5)], fill=hexrgb(P['flood']['wallLine']), width=round(I(0.06)))
    items.append(('Floodwall (1994)', wall))

    def gauge(X, Y):
        d.line([(X + sw * 0.3, Y - sw * 0.2), (X + sw * 0.3, Y + sw * 1.1)], fill=ink, width=max(2, round(I(0.02))))
        for k in range(4):
            d.line([(X + sw * 0.3, Y + k * sw * 0.3), (X + sw * 0.5, Y + k * sw * 0.3)], fill=ink, width=1)
        d.text((X + sw * 0.6, Y - sw * 0.15), '15 ft', font=F(SERIF_B, I(0.16)), fill=ink)
    if (area == 'shockoe') if gauges is None else gauges:
        items.append(('Depth gauge', gauge))
    for name, draw in items:
        draw(cx, y + I(0.3))
        d.text((cx, y), name, font=f, fill=ink)
        cx += max(d.textlength(name, font=f), sw * 1.6) + I(0.45)
    return cx


def key_cell(d, x, y, w, P, dpi, area):
    """The key stacked in one cell: the depth ramp, then one swatch a line."""
    I = lambda v: v * dpi
    ink = hexrgb(P['ink'])
    f, fs = F(SERIF, I(0.15)), F(SERIF_I, I(0.13))
    sw = I(0.3)
    tones, bands = P['flood']['tones'], P['flood']['bands']
    d.text((x, y), 'Water, by depth (ft)', font=f, fill=ink)
    for i, t in enumerate(tones):
        d.rectangle((x + i * sw, y + I(0.26), x + (i + 1) * sw, y + I(0.26) + sw), fill=hexrgb(t))
        if i % 2 == 0 or i == len(tones) - 1:
            d.text((x + i * sw, y + I(0.26) + sw + I(0.02)), f"{round(bands[i] / 0.3048)}", font=fs, fill=ink)
    yy = y + I(0.95)
    rows = [
        ("The river's own channel", lambda X, Y: d.rectangle((X, Y, X + sw * 1.4, Y + sw * 0.8), fill=hexrgb(P['flood']['channel']))),
        ('Hatched: the range of an estimate', lambda X, Y: hatch_sw(d, X, Y, sw * 1.4, sw * 0.8, P, I)),
        ('A building of the year', lambda X, Y: cube(d, X + sw * 0.1, Y - sw * 0.25, sw * 1.2, hexrgb(P['wallLit']), hexrgb(P['wallShade']), hexrgb(P['roof']), ink)),
        ('Grey, dashed roof edge: on an earlier map or photo, not ascertained for the year', lambda X, Y: cube(d, X + sw * 0.1, Y - sw * 0.25, sw * 1.2, hexrgb(P['mix']), hexrgb(P['mixShade']), hexrgb(P['mixRoof']), ink, dash=hexrgb(P['flood']['unconfirmed']['outline']['color']))),
        ('The floodwall (1994), where it stands', lambda X, Y: (d.line([(X, Y + sw * 0.4), (X + sw * 1.4, Y + sw * 0.4)], fill=hexrgb(P['flood']['wallCasing']), width=round(I(0.1))), d.line([(X, Y + sw * 0.4), (X + sw * 1.4, Y + sw * 0.4)], fill=hexrgb(P['flood']['wallLine']), width=round(I(0.055))))),
        ('A depth gauge, the figure in feet', lambda X, Y: (d.line([(X + sw * 0.6, Y - sw * 0.2), (X + sw * 0.6, Y + sw)], fill=ink, width=max(2, round(I(0.02)))), [d.line([(X + sw * 0.6, Y + k * sw * 0.3), (X + sw * 0.85, Y + k * sw * 0.3)], fill=ink, width=1) for k in range(4)])),
    ]
    for name, draw in rows:
        draw(x, yy)
        for j, ln in enumerate(SET.wrap(d, name, f, w - sw * 2.2)):
            d.text((x + sw * 2.0, yy - I(0.02) + j * I(0.2)), ln, font=f, fill=ink)
        yy += I(0.38) + (I(0.2) if d.textlength(name, font=f) > w - sw * 2.2 else 0)


def hatch_sw(d, X, Y, w, h, P, I):
    d.rectangle((X, Y, X + w, Y + h), fill=hexrgb(P['flood']['band']))
    k = 0
    while k * h * 0.35 < w + h:
        x0 = X + k * h * 0.35
        a = (max(X, x0 - h), Y + h - max(0, X - (x0 - h)))
        d.line([(max(X, x0 - h), min(Y + h, Y + h - (max(X, x0 - h) - (x0 - h)))), (min(X + w, x0), Y + max(0, x0 - (X + w)))], fill=hexrgb(P['flood']['bandHatch']), width=max(1, round(I(0.012))))
        k += 1


def north(d, x, y, r, bearing, squash, ink, f):
    """An arrow to north on the drawing (the view looks along `bearing`), and its note."""
    b = math.radians(bearing)
    vx, vy = -math.sin(b), -math.cos(b) * squash
    n = math.hypot(vx, vy); vx, vy = vx / n, vy / n
    tip = (x + vx * r, y + vy * r); tail = (x - vx * r, y - vy * r)
    d.line([tail, tip], fill=ink, width=max(2, round(r / 10)))
    px, py = -vy, vx
    d.polygon([tip, (tip[0] - vx * r * 0.4 + px * r * 0.22, tip[1] - vy * r * 0.4 + py * r * 0.22), (tip[0] - vx * r * 0.4 - px * r * 0.22, tip[1] - vy * r * 0.4 - py * r * 0.22)], fill=ink)
    d.text((tip[0] + vx * r * 0.25 - r * 0.15, tip[1] + vy * r * 0.25 - r * 0.3), 'N', font=f, fill=ink)


def scalebar(d, x, y, px_per_m, ink, f, meters=200):
    L = px_per_m * meters
    for k in range(4):
        d.rectangle((x + k * L / 4, y, x + (k + 1) * L / 4, y + L / 40), fill=ink if k % 2 == 0 else None, outline=ink)
    d.text((x, y + L / 40 + 4), '0', font=f, fill=ink)
    d.text((x + L - d.textlength(f'{meters} m', font=f), y + L / 40 + 4), f'{meters} m (across the picture)', font=f, fill=ink)


def main(area, plates, counts_path, out, dpi='100'):
    dpi = float(dpi.replace('--dpi=', '')) if not dpi.startswith('--') else 100.0
    I = lambda v: v * dpi
    spec = json.load(open(os.path.join(ROOT, 'tools/floods/d3/boxes.json')))
    A = spec[area]
    counts = json.load(open(counts_path))
    region = json.load(open(os.path.join(ROOT, 'regions', A['region'] + '.json')))
    P = pal()
    ink, paper = hexrgb(P['ink']), hexrgb(P['sky'])
    accent = SET.ACCENT
    W, H = round(I(32)), round(I(24))
    img = Image.new('RGB', (W, H), paper)
    d = ImageDraw.Draw(img)
    m = I(0.6)
    (f1, y1), (f2, y2) = A['pair']
    svg1 = os.path.join(plates, f"{A['region']}-{y1}-flood-{f1}.svg")
    svg2 = os.path.join(plates, f"{A['region']}-{y2}-flood-{f2}.svg")
    fl = region['floods'][f1]
    info = json.load(open(svg1[:-4] + '.info.json'))
    fill = lambda t: __import__('re').sub(r'\{(\w+)\}', lambda mm: f"{info[mm.group(1)]:,}" if mm.group(1) in info else mm.group(0), t)
    # Title band.
    title = {'shockoe': 'Shockoe Bottom in flood: Hurricane Agnes, June 1972',
             'manchester': "Manchester: the 1972 flood's height, with today's wall and without it"}[area]
    d.text((m, m - I(0.05)), title, font=F(SERIF_B, I(0.46)), fill=ink)
    lines = [fl['caption']] + [fill(n) for n in fl['notes']]
    if area == 'manchester':
        info2 = json.load(open(svg2[:-4] + '.info.json'))
        lines[1] = f"With the wall: {info['floodAcres']} acres under water off the channel, {info['floodBuildingsInWater']} buildings in it. Without it: {info2['floodAcres']} acres, {info2['floodBuildingsInWater']} buildings."
    y = m + I(0.62)
    for i, ln in enumerate(lines[:3]):
        d.text((m, y), ln, font=F(SERIF_I if i == 0 else SERIF, I(0.17)), fill=ink); y += I(0.26)
    stage = 'WORKING DRAFT d3'
    sf = F(SERIF_B, I(0.24))
    d.text((W - m - d.textlength(stage, font=sf), m), stage, font=sf, fill=accent)
    top = m + I(1.55)
    d.line((m, top - I(0.12), W - m, top - I(0.12)), fill=ink, width=max(1, round(I(0.012))))
    # The map(s): Shockoe's across the sheet at the plate's own shape; Manchester's two side by
    # side, cut at the sides as little as keeps every box frame on them.
    mw = W - 2 * m
    BW, BH = A['size']
    pts = SET.subprocess.run(['node', 'bin/isoscape.js', 'locate', A['region'], '--year', str(y1), '--', *[f"{b['at'][0]},{b['at'][1]}" for b in A['boxes']]],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    pts = [(p['x'], p['y']) for p in json.loads(pts)]
    corners = [(px + sx * BW / 2, py + sy * BH / 2) for px, py in pts for sx in (-1, 1) for sy in (-1, 1)]
    sc1 = SET.Scene(svg1, A['region'])
    cov = sc1.covered()
    if area == 'shockoe':
        h = mw * cov[3] / cov[2]
        maps = [(sc1, m, top, mw, h)]
    else:
        gap = I(0.3)
        w = (mw - gap) / 2
        need = max(c[0] for c in corners) - min(c[0] for c in corners)
        h = w * cov[3] / max(need * 1.03, cov[3] * w / I(6.6))
        maps = [(sc1, m, top, w, h), (SET.Scene(svg2, A['region']), m + w + gap, top, w, h)]
    px_per_unit = None
    for k, (sc, x, yy, w, h) in enumerate(maps):
        box = SET.map_box(sc, w / h, corners, pad=0.0)
        img.paste(sc.render(box, round(w), round(h)), (round(x), round(yy)))
        kk = w / box[2]
        px_per_unit = kk
        for b, (px, py) in zip(A['boxes'], pts):
            X0, Y0 = x + (px - BW / 2 - box[0]) * kk, yy + (py - BH / 2 - box[1]) * kk
            X1, Y1 = X0 + BW * kk, Y0 + BH * kk
            X0, Y0, X1, Y1 = max(X0, x), max(Y0, yy), min(X1, x + w), min(Y1, yy + h)
            d.rectangle((X0, Y0, X1, Y1), outline=accent, width=max(2, round(I(0.03))))
            SET.marker(d, min(max(X0, x + I(0.18)), x + w - I(0.18)), min(max(Y0, yy + I(0.18)), yy + h - I(0.18)), b['n'], I(0.16))
        d.rectangle((x, yy, x + w, yy + h), outline=ink, width=max(1, round(I(0.01))))
        if area == 'manchester':
            lab = ["With today's wall", 'Without it'][k]
            lf = F(SERIF_B, I(0.22))
            d.rectangle((x + I(0.1), yy + I(0.1), x + I(0.3) + d.textlength(lab, font=lf), yy + I(0.45)), fill=paper)
            d.text((x + I(0.2), yy + I(0.12)), lab, font=lf, fill=ink)
    my = top + maps[0][4]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render_boxes as RB
    tf, sf2, nf = F(SERIF_B, I(0.17)), F(SERIF_I, I(0.145)), F(SERIF, I(0.135))
    g = I(0.25)
    text_h = I(0.95)
    foot_top = H - m - I(0.5)
    # Cells: Shockoe two rows of four (the key in the last cell), Manchester one row of five
    # with each box's pair stacked, and the key in a band under it.
    if area == 'shockoe':
        cols, rows = 4, 2
    else:
        cols, rows = len(A['boxes']), 1
    cw = (mw - (cols - 1) * g) / cols
    key_band = I(1.0) if area == 'manchester' else 0
    cell_h = (foot_top - I(0.25) - key_band - (my + I(0.3)) - (rows - 1) * g) / rows
    stack = 2 if area == 'manchester' else 1
    ih = (cell_h - text_h - (stack - 1) * I(0.06)) / stack
    for i, (b, (px, py)) in enumerate(zip(A['boxes'], pts)):
        c, r = i % cols, i // cols
        x = m + c * (cw + g)
        yy = my + I(0.3) + r * (cell_h + g)
        pics = [RB.crop(svg1, px, py, BW, BH, round(cw))] + ([RB.crop(svg2, px, py, BW, BH, round(cw))] if stack == 2 else [])
        for k, pimg in enumerate(pics):
            img.paste(pimg.resize((round(cw), round(ih))), (round(x), round(yy)))
            d.rectangle((x, yy, x + cw, yy + ih), outline=ink, width=1)
            if stack == 2:
                lab = ['with the wall', 'without it'][k]
                d.rectangle((x + I(0.04), yy + I(0.04), x + I(0.12) + d.textlength(lab, font=sf2), yy + I(0.26)), fill=paper)
                d.text((x + I(0.08), yy + I(0.05)), lab, font=sf2, fill=ink)
            yy += ih + I(0.06)
        rr = SET.marker(d, x + I(0.15), yy + I(0.15), b['n'], I(0.15))
        d.text((x + 2 * rr + I(0.08), yy + I(0.02)), b['title'], font=tf, fill=ink)
        c1, c2 = counts[f'{f1}:{y1}'][b['id']], counts[f'{f2}:{y2}'][b['id']]
        if area == 'shockoe':
            dep = (f"{c1['depthFt']:.0f} ft deep at the center" if c1['depthFt'] >= 0.5 else 'dry at the center') + (f"; {c1['inWater']} buildings in water" + (f" ({c1['inWaterUnconfirmed']} grey)" if c1['inWaterUnconfirmed'] else '') if c1['inWater'] else '')
        else:
            dep = ('dry behind the wall' if c1['depthFt'] < 0.5 else f"{c1['depthFt']:.0f} ft deep with the wall") + f"; {c2['depthFt']:.0f} ft without it"
        d.text((x, yy + I(0.36)), dep, font=sf2, fill=accent)
        for j2, ln in enumerate(SET.wrap(d, b['note'], nf, cw)[:2]):
            d.text((x, yy + I(0.58) + j2 * I(0.19)), ln, font=nf, fill=ink)
    if area == 'shockoe':
        kx, ky = m + 3 * (cw + g), my + I(0.3) + cell_h + g
        d.text((kx, ky), 'Key', font=F(SERIF_B, I(0.2)), fill=ink)
        key_cell(d, kx, ky + I(0.4), cw, P, dpi, area)
        bx, by2 = kx, ky + cell_h - I(0.55)
    else:
        ky = foot_top - I(0.25) - key_band + I(0.1)
        end = key(d, m, ky, mw, I(1.0), P, dpi, area)
        bx, by2 = end + I(0.4), ky
    nf2 = F(SERIF, I(0.15))
    pts16 = ['north', 'north-northeast', 'northeast', 'east-northeast', 'east', 'east-southeast', 'southeast', 'south-southeast', 'south', 'south-southwest', 'southwest', 'west-southwest', 'west', 'west-northwest', 'northwest', 'north-northwest']
    north(d, bx + I(0.4), by2 + I(0.45), I(0.35), region['bearing'], region.get('squash', 0.5), ink, F(SERIF_B, I(0.18)))
    d.text((bx + I(1.0), by2), f"The view looks {pts16[round(region['bearing'] / 22.5) % 16]} ({region['bearing']:.0f}°)", font=nf2, fill=ink)
    scalebar(d, bx + I(1.0), by2 + I(0.4), px_per_unit * region['scale'], ink, F(SERIF, I(0.13)))
    # Foot: credits and byline.
    fy = foot_top
    ff = F(SERIF, I(0.13))
    for j, ln in enumerate(SET.wrap(d, CREDIT[area] + ' ' + BYLINE, ff, mw)):
        d.text((m, fy + j * I(0.19)), ln, font=ff, fill=SET.DIM if isinstance(SET.DIM, tuple) else ink)
    img.save(out)
    print(out, img.size, 'map height', round(maps[0][4] / dpi, 2), 'in; box picture height', round(ih / dpi, 2), 'in')


if __name__ == '__main__':
    main(*sys.argv[1:])
