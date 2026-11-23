"""Shared pieces for the Jackson Ward pocket guide's tools: the plan's frame (north up, meters
east and north of a point in the ward), the OpenStreetMap cache, and the palette.

The plan is a true plan: a local equirectangular projection about 37.5505 N, which over the
two kilometers the guide covers is within a few centimeters of a conformal one.
"""
import json
import math
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

LON0, LAT0 = -77.4375, 37.5505
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574

OSM = os.path.join(ROOT, 'data/richmond-streetcars/osm.json')


def to_m(lon, lat):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def to_ll(x, y):
    return x / KX + LON0, y / KY + LAT0


_OSM = None


def osm():
    global _OSM
    if _OSM is None:
        _OSM = json.load(open(OSM))['elements']
    return _OSM


def palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def load(name):
    return json.load(open(os.path.join(HERE, name)))
