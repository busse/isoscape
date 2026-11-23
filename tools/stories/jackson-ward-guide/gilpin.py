#!/usr/bin/env python3
"""The outline of Gilpin Court for the guide's plan, written to gilpin-outline.json.

    python3 tools/stories/jackson-ward-guide/gilpin.py [--fetch]

Neither OpenStreetMap nor the story's files carry a boundary for Gilpin Court. This one is drawn
from the City of Richmond's parcel layer (City_of_Richmond_Parcels, ArcGIS REST, public): the
parcels north of the I-95 trench whose owner is the Richmond Redevelopment and Housing Authority
and whose land use is Multi-Family, joined across the streets between them (closing by 14 m),
so the outline runs along the property line of the streets around it. RRHA's vacant lots
nearby (single-family and commercial lots) are left out. --fetch queries the layer once and
keeps only those parcels, with owner and land use, in rrha-parcels.geojson (fetched November
23, 2026); without it the kept file is used, so the map never touches the network.

The map labels the area only "Gilpin Court (RRHA public housing)" and draws nothing inside it
but streets and their names. It is not an official project boundary.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, to_ll, to_m  # noqa: E402

import numpy as np  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import shape  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

URL = 'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/City_of_Richmond_Parcels/FeatureServer/0/query'
BBOX = '-77.4445,37.5505,-77.4290,37.5580'
OWNER = 'Richmond Redevelopment And Housing Authority'
CLOSE_M = 14
KEPT = os.path.join(HERE, 'rrha-parcels.geojson')


def fetch():
    args = ['curl', '-s', '--max-time', '60', '-G', URL]
    for k, v in (('where', f"OwnerName = '{OWNER}' AND LandUse = 'Multi-Family'"), ('geometry', BBOX), ('geometryType', 'esriGeometryEnvelope'),
                 ('inSR', '4326'), ('spatialRel', 'esriSpatialRelIntersects'), ('outFields', 'OwnerName,LandUse,PropertyClass'),
                 ('outSR', '4326'), ('f', 'geojson')):
        args += ['--data-urlencode', f'{k}={v}']
    d = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)
    d = {'type': 'FeatureCollection', 'source': URL, 'fetched': '2026-11-23', 'where': f"OwnerName = '{OWNER}' AND LandUse = 'Multi-Family'",
         'features': [dict(type='Feature', properties=f['properties'], geometry=f['geometry']) for f in d['features']]}
    json.dump(d, open(KEPT, 'w'))
    print('kept', len(d['features']), 'parcels')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    if ap.parse_args().fetch:
        fetch()
    fs = json.load(open(KEPT))['features']
    polys = [shapely.transform(shape(f['geometry']), lambda a: np.column_stack(to_m(a[:, 0], a[:, 1]))).buffer(0) for f in fs]
    area = unary_union(polys).buffer(CLOSE_M, join_style=2).buffer(-CLOSE_M, join_style=2)
    parts = sorted(getattr(area, 'geoms', [area]), key=lambda p: -p.area)
    main_part = parts[0].simplify(1.0)
    ring = [list(to_ll(x, y)) for x, y in main_part.exterior.coords]
    out = {'about': __doc__.split('\n\n', 2)[1].strip(), 'source': URL, 'fetched': '2026-11-23', 'parcels': len(fs),
           'parcel_acres': round(sum(p.area for p in polys) / 4046.86, 1), 'outline_acres': round(main_part.area / 4046.86, 1),
           'left_out_parts': len(parts) - 1, 'outline_lonlat': [[round(a, 7), round(b, 7)] for a, b in ring]}
    json.dump(out, open(os.path.join(HERE, 'gilpin-outline.json'), 'w'), indent=1)
    print({k: v for k, v in out.items() if k not in ('outline_lonlat', 'about')})


if __name__ == '__main__':
    main()
