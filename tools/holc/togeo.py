"""Write the traced areas as GeoJSON in WGS84.

    python3 -I togeo.py <areas_px.json> <georef.json> <out.geojson> <scan sha256> <labels.json>

Each area becomes one feature (Polygon or MultiPolygon) with grade, area_number, label and
how each piece was named, and label_coords
([lat, lon] of the first seed point inside the area, or for D10, whose circle stands outside
it, a point inside its largest part; as the story's scripts expect); coordinates rounded to 7 decimals (about 1 cm).
"""
import json
import os
import sys

from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import georef  # noqa: E402


def ll(t, ring):
    xy = georef.apply(t, ring)
    lon, lat = georef.to_ll(xy[:, 0], xy[:, 1])
    return list(zip(lon.round(7), lat.round(7)))


def main(src, gj, out, sha, labels):
    A = json.load(open(src))
    seeds = json.load(open(labels))['seeds']
    G = json.load(open(gj))
    t = G['transform']
    fits = G['fits'][G['use']]
    feats = []
    for a in A['areas']:
        polys = [Polygon(ll(t, p[0]), [ll(t, h) for h in p[1:]]).buffer(0) for p in a['polygons_px']]
        g = unary_union(polys)
        n = a['area_number']
        s0 = next((s for s in seeds if s['label'] == a['label'] and not s.get('leader_only')), None)
        if s0:
            xy = georef.apply(t, [s0['at']])[0]
            lon, lat = georef.to_ll([xy[0]], [xy[1]])
        else:  # label printed outside the area (D10): a point inside its largest part
            big = max(getattr(g, 'geoms', [g]), key=lambda q: q.area).representative_point()
            lon, lat = [big.x], [big.y]
        feats.append({'type': 'Feature',
                      'properties': {'grade': a['grade'], 'area_number': n, 'label': a['label'],
                                     'printed': a['label'].replace('.5', ' 1/2'),
                                     'label_coords': [round(float(lat[0]), 6), round(float(lon[0]), 6)],
                                     'pieces_named_by': sorted(set(v.split(' ')[0] for v in a['how'].values()))},
                      'geometry': mapping(g)})
    meta = {
        'title': "Richmond, Virginia, HOLC residential security map (April 3, 1937), graded areas, redrawn",
        'source_map': "Home Owners' Loan Corporation, Residential Security Map, Richmond, Va., Apr. 3, 1937. National Archives, RG 195, City Survey Files (public domain), scan via FRASER, Federal Reserve Bank of St. Louis: https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/rg195_holc_Richmond_VA.pdf",
        'source_sha256': sha,
        'georeferencing': f"affine fit to {len(G['points'])} street corners read off the scan by machine against OpenStreetMap; RMS {fits['rms']:.1f} m, largest {fits['max']:.1f} m, leave-one-out RMS {fits['loo_rms']:.1f} m",
        'method': "Traced in code by color segmentation of the scan (tools/holc in the isoscape repo); labels as printed on the map. Done with Claude for Chris Busse, November 2026.",
        'street_data': "Control points from OpenStreetMap, (c) OpenStreetMap contributors, ODbL 1.0",
        'not_derived_from': "Mapping Inequality's polygons or control points were not used as input.",
        'license_note': "The map is a U.S. federal record in the public domain. Control-point coordinates come from OpenStreetMap (ODbL); credit '(c) OpenStreetMap contributors'.",
    }
    json.dump({'type': 'FeatureCollection', 'metadata': meta, 'features': feats}, open(out, 'w'))
    print(len(feats), 'features')


if __name__ == '__main__':
    main(*sys.argv[1:])
