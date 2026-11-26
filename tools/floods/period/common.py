"""Shared helpers for the period-city evidence tools: reading a crop and its georeferencing,
lon/lat to crop pixels (with the fitted registration), today's streets from the OSM cache."""
import json, os
import numpy as np
from PIL import Image
from pyproj import Transformer

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'data', 'floods-period')
OSM = os.path.join(ROOT, 'data', 'richmond-i195-rocketts', 'osm.json')
STREET_KINDS = ('primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk')
WIDTH = {'trunk': 16, 'primary': 14, 'secondary': 12, 'tertiary': 10, 'residential': 8, 'unclassified': 8}


class Crop:
    def __init__(self, area, key):
        self.area, self.key = area, key
        self.meta_path = os.path.join(DATA, f'{area}-{key}.json')
        self.meta = json.load(open(self.meta_path))
        self.img = Image.open(os.path.join(DATA, f'{area}-{key}.jpg'))
        self.gray = np.asarray(self.img.convert('L'), dtype=np.float32)
        self.rgb = np.asarray(self.img.convert('RGB'), dtype=np.float32)
        self.t = self.meta['transform']
        self.to_crs = Transformer.from_crs('EPSG:4326', self.meta['crs'], always_xy=True)
        self.px = abs(self.t[1])  # crs meters per pixel
        # Ground meters per CRS meter: Web Mercator is stretched by 1/cos(lat).
        self.ground = np.cos(np.radians(37.53)) if self.meta['crs'] == 'EPSG:3857' else 1.0

    @property
    def reg(self):
        r = self.meta.get('registration')
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0) if r is None else tuple(r['affine'])

    def crs_xy(self, lon, lat):
        return self.to_crs.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))

    def pixel(self, lon, lat, reg=None, extra=(0.0, 0.0)):
        """lon/lat (WGS84) to crop pixel (col, row). The registration is a shift in CRS meters
        that grows linearly across the crop: dx = a0 + a1 u + a2 v, dy = b0 + b1 u + b2 v, with
        u, v the offsets in km from the crop's center."""
        x, y = self.crs_xy(lon, lat)
        a = self.reg if reg is None else reg
        cx, cy = self.center()
        u, v = (x - cx) / 1000, (y - cy) / 1000
        x = x + a[0] + a[1] * u + a[2] * v + extra[0]
        y = y + a[3] + a[4] * u + a[5] * v + extra[1]
        return (x - self.t[0]) / self.t[1], (y - self.t[3]) / self.t[5]

    def center(self):
        h, w = self.gray.shape
        return self.t[0] + self.t[1] * w / 2, self.t[3] + self.t[5] * h / 2


def streets(bbox):
    """Today's street center lines in a lon/lat box: (kind, lons, lats) per way."""
    w, s, e, n = bbox
    out = []
    for el in json.load(open(OSM))['elements']:
        t = el.get('tags', {})
        if el['type'] != 'way' or t.get('highway') not in STREET_KINDS or not el.get('geometry') or t.get('bridge') not in (None, 'no') or t.get('tunnel') not in (None, 'no'):
            continue
        lo = np.array([g['lon'] for g in el['geometry']]); la = np.array([g['lat'] for g in el['geometry']])
        if lo.max() < w or lo.min() > e or la.max() < s or la.min() > n:
            continue
        out.append((t['highway'], lo, la))
    return out
