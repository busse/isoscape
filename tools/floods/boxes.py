"""
Dev tool (floods series, d2): the close-up boxes of a flood view, as a set would frame them:
each box cut from the big view's SVG (so it matches the map exactly) for the flood and its dry
twin, with the depth at its center from the cached 2 m lidar, and a menu-style sheet mockup.

  python3 tools/floods/boxes.py <area: shockoe|manchester> <svg-dir> <out-dir>
"""
import json, math, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont

FT = 3.28084
# Agnes 1972: 35.5 ft at the Locks, 36.8 ft at the Mayo Bridge, ramped between, held outside.
LOCKS, MAYO = (-77.42171, 10.82), (-77.43458, 11.217)
def level(lon):
    t = max(0.0, min(1.0, (lon - LOCKS[0]) / (MAYO[0] - LOCKS[0])))
    return LOCKS[1] + (MAYO[1] - LOCKS[1]) * t

BOXES = {
    'shockoe': {'region': 'richmond-floods-shockoe', 'flood': ('1972', 1972), 'boxes': [
        (1, '17th Street Market', [-77.42826, 37.53399], 'The lowest blocks of Shockoe Bottom; the market where most of Gaston\'s water met, too.'),
        (2, 'Main Street Station', [-77.42916, 37.53460], 'The station and its train shed standing in the water.'),
        (3, '17th and Dock, the canal\'s end', [-77.42965, 37.53228], 'Where the Bottom spills to the river today (step 15); the wall\'s V and its Dock Street opening.'),
        (4, 'Shockoe Slip, 14th and Cary', [-77.43244, 37.53453], 'The edge of the water at the foot of downtown.'),
        (5, 'Mayo Island', [-77.4326, 37.5292], 'The island under the river, its buildings standing in it.'),
        (6, 'Tobacco Row and the Dock', [-77.4228, 37.5290], 'The warehouses along Dock Street, the Dock between them and the river.'),
        (7, 'Great Shiplock Park', [-77.42161, 37.52586], 'The canal\'s lock to the tidal river, at Rocketts.'),
    ]},
    'manchester': {'region': 'richmond-floods-manchester', 'flood': ('agnes-today', 2026), 'boxes': [
        (1, 'Hull Street at the Mayo Bridge', [-77.4352, 37.5257], 'The bridge foot, inside the wall: dry with it, deep without.'),
        (2, 'The flats: 5th and Stockton', [-77.436818, 37.522792], 'Warehouses and shops on the old floodplain the wall now guards.'),
        (3, 'Commerce Road and Maury', [-77.437703, 37.519511], 'Industrial Manchester at the foot of the bluff.'),
        (4, 'The tank farm', [-77.4335, 37.5215], 'Storage tanks on the flats, behind the wall.'),
        (5, 'On the wall', [-77.4390, 37.5272], 'The south wall: the 1972 height on the river side, dry ground behind.'),
        (6, 'The treatment plant grounds', [-77.4235, 37.5175], 'Tanks and basins east of the I-95 ridge: open to the river in this fill.'),
    ]},
}

def locate(region, year, lonlat):
    out = subprocess.run(['node', 'bin/isoscape.js', 'locate', region, '--year', str(year), '--', *[f'{a},{b}' for a, b in lonlat]], capture_output=True, text=True, check=True).stdout
    return [(p['x'], p['y']) for p in json.loads(out)]

def crop(svg, out, cx, cy, w, h, px):
    s = open(svg).read()
    s = re.sub(r'viewBox="[^"]+"', f'viewBox="{cx - w / 2} {cy - h / 2} {w} {h}"', s, count=1)
    tmp = out + '.svg'
    open(tmp, 'w').write(s)
    subprocess.run(['rsvg-convert', '-w', str(px), '-o', out, tmp], check=True)
    os.remove(tmp)

def depth_at(lon, lat):
    # The cached 2 m elevation, sampled the way isoscape reads it.
    js = f"import('./src/dem.ts').then(async (m) => {{ const d = await m.loadDem('data/richmond-i195-rocketts/dem.bin.gz'); m.cleanDem(d); console.log(m.sampler(d)({lon}, {lat})) }})"
    g = float(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
    return level(lon) - g, g

def main():
    area, svgdir, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    spec = BOXES[area]
    key, year = spec['flood']
    region = spec['region']
    wet_svg = f'{svgdir}/{region}-{year}-flood-{key}.svg'
    dry_svg = f'{svgdir}/{region}-{year}-flood-{key}-nowall.svg' if area == 'manchester' else f'{svgdir}/{region}-{year}-flood-1972-dry.svg'
    pts = locate(region, year, [b[2] for b in spec['boxes']])
    W, H = 420, 280
    info = []
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 30); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 20)
    except Exception: font = small = ImageFont.load_default()
    for (n, title, at, why), (x, y) in zip(spec['boxes'], pts):
        a, b = f'{out}/box-{n}-flood.png', f'{out}/box-{n}-other.png'
        crop(wet_svg, a, x, y, W, H, 900)
        crop(dry_svg, b, x, y, W, H, 900)
        d, g = depth_at(*at)
        info.append({'n': n, 'title': title, 'at': at, 'svg_xy': [x, y], 'why': why, 'ground_m': round(g, 2), 'depth_ft': round(d * FT, 1)})
        pair = Image.new('RGB', (1810, 660), 'white')
        pair.paste(Image.open(a).convert('RGB'), (0, 60)); pair.paste(Image.open(b).convert('RGB'), (910, 60))
        dr = ImageDraw.Draw(pair)
        dep = (f'{d * FT:.0f} ft of water at the center (2 m lidar)' if d > 0 else 'dry at the center') + (' without the wall' if area == 'manchester' and d > 0 else '')
        dr.text((10, 10), f'{n}  {title}: {dep}', fill=(30, 30, 30), font=font)
        dr.text((910, 30), 'no wall' if area == 'manchester' else 'dry', fill=(60, 60, 60), font=small)
        pair.save(f'{out}/box-{n}-pair.png')
    json.dump(info, open(f'{out}/boxes.json', 'w'), indent=1)
    # The big map with numbered box frames, and a 4:3 sheet mockup, menu style.
    big = Image.open(wet_svg.replace('.svg', '.png')).convert('RGB')
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', open(wet_svg).read(1000)).group(1).split()]
    k = big.size[0] / vb[2]
    dr = ImageDraw.Draw(big)
    try: num = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 44)
    except Exception: num = ImageFont.load_default()
    for it in info:
        x, y = it['svg_xy']
        X, Y = (x - vb[0]) * k, (y - vb[1]) * k
        w, h = W * k, H * k
        dr.rectangle([X - w / 2, Y - h / 2, X + w / 2, Y + h / 2], outline=(155, 58, 44), width=5)
        dr.ellipse([X - w / 2 - 30, Y - h / 2 - 30, X - w / 2 + 30, Y - h / 2 + 30], fill=(155, 58, 44))
        dr.text((X - w / 2 - 13, Y - h / 2 - 26), str(it['n']), fill='white', font=num)
    big.save(f'{out}/map-with-boxes.png')
    SW, SH = 4000, 3000
    sheet = Image.new('RGB', (SW, SH), (244, 241, 234))
    m = big.resize((2600, round(big.size[1] * 2600 / big.size[0])))
    sheet.paste(m, (700, 300))
    sd = ImageDraw.Draw(sheet)
    try: t1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 80); t2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 34)
    except Exception: t1 = t2 = ImageFont.load_default()
    sd.text((700, 120), 'Shockoe Bottom: Hurricane Agnes, June 1972' if area == 'shockoe' else 'Manchester: the 1972 flood\'s height against today\'s wall', fill=(44, 43, 51), font=t1)
    slots = [(40, 300), (40, 1100), (40, 1900), (3340, 300), (3340, 1100), (3340, 1900), (1690, 2300)]
    for it, (sx, sy) in zip(info, slots):
        im = Image.open(f'{out}/box-{it["n"]}-flood.png').convert('RGB').resize((620, 413))
        sheet.paste(im, (sx, sy + 60))
        sd.text((sx, sy), f'{it["n"]}  {it["title"]}', fill=(44, 43, 51), font=t2)
        lab = (f'{it["depth_ft"]:.0f} ft deep' if it['depth_ft'] > 0 else 'dry') if area != 'manchester' else \
              (f'behind the wall; {it["depth_ft"]:.0f} ft deep without it' if it['depth_ft'] > 0 else 'dry either way')
        sd.text((sx, sy + 480), lab, fill=(155, 58, 44), font=t2)
    sd.text((700, 2900), 'MOCKUP: layout only. ROUGH DRAFT; levels checked, buildings as recorded.', fill=(90, 90, 90), font=t2)
    sheet.save(f'{out}/sheet-mockup.png')
    print(json.dumps(info, indent=1))

if __name__ == '__main__':
    main()
