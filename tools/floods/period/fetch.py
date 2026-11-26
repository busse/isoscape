"""Evidence images for the floods series' period city: small georeferenced crops of public
orthophotos over the two flood areas, written to data/floods-period/ (outside git; rerun this
to make them again). Raw downloads go to a temporary folder and are deleted after use.

    python3 tools/floods/period/fetch.py [image ...]     # default: every image

Each crop is <area>-<image>.jpg with <area>-<image>.json beside it: the CRS (WKT or EPSG),
the GDAL-style transform from pixel to CRS meters, the date, the source and its URL, and a
SHA-256 (of the raw file where there is one; of the crop where the image comes from a map
service, which can change). Registration against today's streets is a separate step
(register.py), written into the same JSON.

All sources are public and need no login. Read on November 24, 2026.
"""
import hashlib, io, json, math, os, shutil, sys, tempfile, time, urllib.request
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, 'data', 'floods-period')

# The two areas: each region's frame (tools/floods/period/inventory.ts) with about 60 m to spare.
AREAS = {
    'shockoe': (-77.4433, 37.5221, -77.4147, 37.5423),
    'manchester': (-77.4451, 37.5113, -77.4149, 37.5311),
}

USGS74 = {
    'tif': ('https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/VA/VA_Richmond_186506_1974_24000_geo.tif',
            'f6a6926b579095e7b8853afb43ab0e5072eb1c50a7ea0511fef6cd8ffb3a694d'),
    'pdf': ('https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/VA/24000/VA_Richmond_186506_1974_24000_geo.pdf',
            '9a1ebfac3a7e6ae4d98a7b71abf6ccf85f6c51fa096fc0add9512ad457853163'),
}

IMAGES = {
    '1974': dict(date=1974, title='USGS 1:24,000 orthophoto map, Richmond quadrangle, 1974 photography (imprint 1977), item 186506',
                 kind='usgs74', license='USGS, public domain ("Acknowledgment of the U.S. Geological Survey is expected")',
                 url=USGS74['pdf'][0], resolution='GeoPDF rendered at 600 dpi: about 1.0 m per pixel (a printed halftone; about 2 m in practice)'),
    '1999': dict(date=1999, title='City of Richmond orthophotos 1999 (credit on the service: DIT (VGIN))', kind='tiles',
                 url='https://tiles.arcgis.com/tiles/k3vhq11XkBNeeOfM/arcgis/rest/services/Orthophotos1999_/MapServer', z=18,
                 license='public City of Richmond map service, no login; no license stated', resolution='zoom 18 tiles: about 0.47 m per pixel on the ground'),
    '2002': dict(date=2002, title='VGIN Virginia Base Mapping Program (VBMP) orthophotos, spring 2002', kind='export',
                 url='https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VBMP_Imagery/VBMP2002_WGS/MapServer',
                 license='Virginia Geographic Information Network public map service, no login', resolution='1 ft to 2 ft collected; exported at about 0.63 m per pixel'),
    '2017': dict(date=2017, title='VGIN VBMP orthophotos, 2017', kind='export',
                 url='https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VBMP_Imagery/VBMP2017_WGS/MapServer',
                 license='Virginia Geographic Information Network public map service, no login', resolution='exported at about 0.63 m per pixel'),
    '2021': dict(date=2021, title='VGIN VBMP orthophotos, spring 2021', kind='export',
                 url='https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VBMP_Imagery/VBMP2021_WGS/MapServer',
                 license='Virginia Geographic Information Network public map service, no login', resolution='exported at about 0.63 m per pixel'),
}

MERC_PX = 0.8  # Web Mercator meters per pixel of an exported crop (about 0.63 m on the ground here)


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'isoscape-floods/1'}), timeout=120) as r:
                return r.read()
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(2 + 3 * k)


def merc(lon, lat):
    R = 6378137.0
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def save(area, key, img, meta):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{area}-{key}.jpg')
    img.save(path, quality=66, optimize=True)  # under 5 MB a crop (the 1999 ones were scored at 74)
    meta = dict(meta, file=os.path.relpath(path, ROOT), size=list(img.size), bytes=os.path.getsize(path),
                crop_sha256=hashlib.sha256(open(path, 'rb').read()).hexdigest(), read='2026-11-24')
    old = os.path.join(OUT, f'{area}-{key}.json')
    if os.path.exists(old):  # keep a registration already fitted
        prev = json.load(open(old))
        if 'registration' in prev:
            meta['registration'] = prev['registration']
    json.dump(meta, open(old, 'w'), indent=1)
    print(path, img.size, meta['bytes'] // 1024, 'KB')


def usgs74(spec):
    import rasterio
    from rasterio.warp import transform as warp
    import fitz
    tmp = tempfile.mkdtemp(prefix='usgs74-')
    try:
        paths = {}
        for k, (url, sha) in USGS74.items():
            data = get(url)
            got = hashlib.sha256(data).hexdigest()
            if got != sha:
                raise SystemExit(f'{url}: checksum {got} is not the recorded {sha}')
            paths[k] = os.path.join(tmp, os.path.basename(url))
            open(paths[k], 'wb').write(data)
        r = rasterio.open(paths['tif'])
        doc = fitz.open(paths['pdf'])
        page = doc[0]
        # The GeoTIFF is the same sheet scanned at 300 dpi (6625 by 8075 px; the PDF page is
        # 1590.3 by 1938.0 pt): a PDF point is 300/72 TIFF pixels. Render at 600 dpi.
        k = 300 / 72
        for area, (w, s, e, n) in AREAS.items():
            xs, ys = warp('EPSG:4326', r.crs, [w, e, w, e], [s, s, n, n])
            c0, r0 = ~r.transform * (min(xs), max(ys))
            c1, r1 = ~r.transform * (max(xs), min(ys))
            clip = fitz.Rect(c0 / k, r0 / k, c1 / k, r1 / k)
            pix = page.get_pixmap(dpi=600, clip=clip, colorspace=fitz.csGRAY)
            img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
            # Pixel (0, 0) of the render is the clip's corner; 600 dpi is 2 TIFF pixels a pixel.
            t = r.transform
            x0, y0 = t * (clip.x0 * k, clip.y0 * k)
            tr = [x0, t.a * clip.width * k / img.width, 0.0, y0, 0.0, t.e * clip.height * k / img.height]
            save(area, '1974', img, dict(spec, crs=r.crs.to_wkt(), transform=tr, raw_sha256={k2: v[1] for k2, v in USGS74.items()},
                                         note='Rendered from the GeoPDF at 600 dpi; placed with the GeoTIFF\'s georeferencing (NAD27, Lambert conformal conic).'))
    finally:
        shutil.rmtree(tmp)


def tiles(spec, key):
    z = spec['z']
    n = 2 ** z
    R = 6378137.0
    size = 2 * math.pi * R / n
    for area, (w, s, e, nn) in AREAS.items():
        x0 = int((w + 180) / 360 * n); x1 = int((e + 180) / 360 * n)
        ty = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
        y0 = ty(nn); y1 = ty(s)
        img = Image.new('RGB', ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                data = get(f"{spec['url']}/tile/{z}/{y}/{x}")
                img.paste(Image.open(io.BytesIO(data)).convert('RGB'), ((x - x0) * 256, (y - y0) * 256))
        px = size / 256
        ox, oy = -math.pi * R + x0 * size, math.pi * R - y0 * size
        # Downsample to MERC_PX to keep the crop small.
        f = px / MERC_PX
        img = img.resize((round(img.width * f), round(img.height * f)), Image.LANCZOS)
        save(area, key, img, dict({k: v for k, v in spec.items() if k != 'z'}, crs='EPSG:3857', transform=[ox, MERC_PX, 0.0, oy, 0.0, -MERC_PX]))


def export(spec, key):
    for area, (w, s, e, n) in AREAS.items():
        ax, ay = merc(w, s); bx, by = merc(e, n)
        W = math.ceil((bx - ax) / MERC_PX); H = math.ceil((by - ay) / MERC_PX)
        img = Image.new('RGB', (W, H))
        step = 2000
        for i in range(0, W, step):
            for j in range(0, H, step):
                cw = min(step, W - i); ch = min(step, H - j)
                x0 = ax + i * MERC_PX; y1 = by - j * MERC_PX
                bbox = f'{x0},{y1 - ch * MERC_PX},{x0 + cw * MERC_PX},{y1}'
                data = get(f"{spec['url']}/export?bbox={bbox}&bboxSR=3857&imageSR=3857&size={cw},{ch}&format=png32&transparent=false&f=image")
                img.paste(Image.open(io.BytesIO(data)).convert('RGB'), (i, j))
        save(area, key, img, dict(spec, crs='EPSG:3857', transform=[ax, MERC_PX, 0.0, by, 0.0, -MERC_PX]))


if __name__ == '__main__':
    for key in (sys.argv[1:] or list(IMAGES)):
        spec = IMAGES[key]
        {'usgs74': lambda: usgs74(spec), 'tiles': lambda: tiles(spec, key), 'export': lambda: export(spec, key)}[spec['kind']]()
