"""Floods series d3: render the boxes of tools/floods/d3/boxes.json from the built plates.

    python3 tools/floods/d3/render_boxes.py <area> <plates-dir> <counts.json> <out-dir> [strip-box-id ...]

Each box is cut from the plate's own SVG (its viewBox narrowed, so it matches the map), with the
map's small type (gauge figures, place names) set at 0.62 of its plate size (larger labels, the wall's, at 0.35) so it sits in the box.
Writes box-<n>-<id>-pair.jpg (the plate beside its pair: Shockoe's dry twin, Manchester's
no-wall), and for each strip box a strip across the area's `across` floods.
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_B = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
INK = (44, 43, 51)
ACCENT = (155, 58, 44)
TEXT_SCALE = 0.62
TILE_NOTES = {
    'gaston-b': ['rain; reported depths: solid to about 28 ft,', 'hatched to 35 ft (they imply 24 to 35)'],
    '1996': ['the city of 1996, behind the wall', '(its openings drawn shut)'],
    '2020': ['the city of 2020, behind the wall', '(its openings drawn shut)'],
}
LABELS = {'1972': 'Agnes, June 1972', '1972-dry': 'its dry twin: the same city, no flood', 'agnes-today': "the 1972 height, today's wall", 'agnes-today-nowall': 'the same height, no wall',
          '1936': 'March 1936', '1969': 'Camille, 1969', '1985': 'November 1985', 'gaston-b': "Gaston's rain, 2004", '1996': 'Fran, 1996, with the wall', '2020': 'November 2020, with the wall'}


def svg_of(d, region, year, flood):
    return os.path.join(d, f'{region}-{year}-flood-{flood}.svg')


def locate(region, year, pts):
    out = subprocess.run(['node', 'bin/isoscape.js', 'locate', region, '--year', str(year), '--', *[f'{a},{b}' for a, b in pts]], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [(p['x'], p['y']) for p in json.loads(out)]


_cache = {}


def crop(svg, cx, cy, w, h, px):
    if svg not in _cache:
        s = open(svg, encoding='utf8').read()
        s = re.sub(r'<g class="caption".*?</g>', '', s, flags=re.S)
        s = re.sub(r'font-size="([0-9.]+)"', lambda m: f'font-size="{float(m.group(1)) * (TEXT_SCALE if float(m.group(1)) < 30 else 0.35):.1f}"', s)
        _cache.clear(); _cache[svg] = s
    s = re.sub(r'viewBox="[^"]+"', f'viewBox="{cx - w / 2:.1f} {cy - h / 2:.1f} {w} {h}"', _cache[svg], count=1)
    with tempfile.TemporaryDirectory() as t:
        a, b = os.path.join(t, 'c.svg'), os.path.join(t, 'c.png')
        open(a, 'w', encoding='utf8').write(s)
        subprocess.run(['rsvg-convert', '-w', str(px), '-o', b, a], check=True)
        return Image.open(b).convert('RGB')


def depth_text(c, place="the box's center"):
    return f"{int(c['depthFt'] + 0.5)} ft deep at {place}" if c['depthFt'] >= 0.5 else f'dry at {place}'


def save(img, path):
    q = 88
    img.save(path, quality=q, optimize=True)
    while os.path.getsize(path) > 1_900_000 and q > 50:
        q -= 8; img.save(path, quality=q, optimize=True)


def main(area, plates, counts_path, out, *strips):
    spec = json.load(open(os.path.join(ROOT, 'tools/floods/d3/boxes.json')))
    A = spec[area]
    W, H = A['size']
    counts = json.load(open(counts_path))
    os.makedirs(out, exist_ok=True)
    (f1, y1), (f2, y2) = A['pair']
    pts = locate(A['region'], y1, [b['at'] for b in A['boxes']])
    T, S = ImageFont.truetype(SERIF_B, 30), ImageFont.truetype(SERIF, 22)
    PX = 900
    ph = round(PX * H / W)
    if H > W: PX = 700; ph = round(PX * H / W)
    for b, (x, y) in zip(A['boxes'], pts):
        a = crop(svg_of(plates, A['region'], y1, f1), x, y, W, H, PX)
        o = crop(svg_of(plates, A['region'], y2, f2), x, y, W, H, PX)
        c1, c2 = counts[f'{f1}:{y1}'][b['id']], counts[f'{f2}:{y2}'][b['id']]
        img = Image.new('RGB', (2 * PX + 12, ph + 110), (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((8, 6), f"{b['n']}  {b['title']}", fill=INK, font=T)
        sub = depth_text(c1) + (f"; {c1['inWater']} buildings in water ({c1['inWaterUnconfirmed']} unconfirmed)" if c1['inWater'] else '')
        if area == 'manchester':
            sub = ('behind the wall: ' + depth_text(c1) if c1['depthFt'] < 0.5 else depth_text(c1)) + f"; without the wall {c2['depthFt']:.0f} ft, {c2['inWater']} buildings in water"
        d.text((8, 44), sub, fill=ACCENT, font=S)
        img.paste(a, (0, 104)); img.paste(o, (PX + 12, 104))
        d.text((8, 76), LABELS.get(f1, f1), fill=INK, font=S); d.text((PX + 20, 76), LABELS.get(f2, f2), fill=INK, font=S)
        save(img, os.path.join(out, f"{area}-box-{b['n']}-{b['id']}-pair.jpg"))
        print('box', b['n'], b['id'], sub)
    for sid in strips:
        b = next(x for x in A['boxes'] if x['id'] == sid)
        k = A['boxes'].index(b)
        x, y = pts[k]
        tiles = []
        for fl, yr in A['across']:
            t = crop(svg_of(plates, A['region'], yr, fl), x, y, W, H, 620)
            c = counts[f'{fl}:{yr}'][b['id']]
            tile = Image.new('RGB', (620, t.height + 118), (255, 255, 255))
            dd = ImageDraw.Draw(tile)
            dd.text((4, 2), LABELS.get(fl, fl), fill=INK, font=ImageFont.truetype(SERIF_B, 22))
            # Gaston was rain, its water drawn from reports: its tile says so, so its paler look reads as meant.
            sub = TILE_NOTES.get(fl, [f'the city of {yr}'])
            for j, ln in enumerate(sub):
                dd.text((4, 32 + j * 22), ln, fill=INK, font=ImageFont.truetype(SERIF, 17))
            dd.text((4, 32 + 2 * 22 + 6), depth_text(c, b.get('depthName', "the box's center")) + f"; {c['inWater']} in the water", fill=ACCENT, font=ImageFont.truetype(SERIF, 18))
            tile.paste(t, (0, 118))
            tiles.append(tile)
        strip = Image.new('RGB', (len(tiles) * 628, tiles[0].height + 56), (255, 255, 255))
        ImageDraw.Draw(strip).text((6, 8), f"{b['n']}  {b['title']}, flood by flood (each on the city of its year)  ·  FINAL DRAFT rc3", fill=INK, font=T)
        for i, t in enumerate(tiles):
            strip.paste(t, (i * 628, 56))
        save(strip, os.path.join(out, f"{area}-box-{b['n']}-{b['id']}-across-floods.jpg"))
        print('strip', sid)


if __name__ == '__main__':
    main(*sys.argv[1:])
