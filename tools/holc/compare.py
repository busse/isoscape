"""Compare the redrawn outlines with another set of the same areas (Mapping Inequality's).

    python3 -I compare.py <redrawn.geojson> <other.geojson> <per-area.csv> <summary.json>

Both are measured on the local plane of the story's measure.py (equirectangular about 37.55 N).
Per area (matched by label): hectares in each, intersection over union, the largest boundary
offset (the Hausdorff distance between the two outlines, in meters), and whether grade and
label agree. Overall: each grade's land (union of its areas) in each set. The other set is read
only; nothing from it is written except the numbers.
"""
import csv
import json
import math
import sys

from shapely.geometry import shape
from shapely.ops import transform, unary_union

LAT0 = 37.55
KX = 111320 * math.cos(math.radians(LAT0))
KY = 111132
G = 'ABCD'


def proj(geom):
    g = shape(geom)
    return transform(lambda x, y, z=None: ((x + 77.46) * KX, (y - LAT0) * KY), g).buffer(0)


def load(p):
    out = {}
    for f in json.load(open(p))['features']:
        lab = (f['properties'].get('label') or '').strip()
        out[lab] = {'grade': f['properties'].get('grade'), 'g': proj(f['geometry'])}
    return out


def key(s):
    try:
        return (s[0], float(s[1:]))
    except ValueError:
        return ('Z', 0)


def main(a, b, csvp, js):
    R, M = load(a), load(b)
    rows = []
    for lab in sorted(set(R) | set(M), key=key):
        r, m = R.get(lab), M.get(lab)
        row = {'label': lab}
        if r:
            row['grade_redrawn'] = r['grade']
            row['ha_redrawn'] = round(r['g'].area / 1e4, 1)
        if m:
            row['grade_lab'] = m['grade']
            row['ha_lab'] = round(m['g'].area / 1e4, 1)
        if r and m:
            i = r['g'].intersection(m['g']).area
            u = r['g'].union(m['g']).area
            row['iou'] = round(i / u, 3)
            row['max_offset_m'] = round(r['g'].boundary.hausdorff_distance(m['g'].boundary))
            row['area_diff_pct'] = round(100 * (r['g'].area - m['g'].area) / m['g'].area, 1)
            row['grade_agrees'] = r['grade'] == m['grade']
            row['label_agrees'] = True
        else:
            row['label_agrees'] = False
        rows.append(row)
    cols = ['label', 'grade_redrawn', 'grade_lab', 'grade_agrees', 'label_agrees', 'ha_redrawn', 'ha_lab',
            'area_diff_pct', 'iou', 'max_offset_m']
    with open(csvp, 'w', newline='') as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})
    tot = {}
    for name, S in (('redrawn', R), ('lab', M)):
        by = {g: unary_union([x['g'] for x in S.values() if x['grade'] == g]) for g in G}
        t = sum(v.area for v in by.values())
        tot[name] = {g: {'areas': sum(1 for x in S.values() if x['grade'] == g), 'km2': round(by[g].area / 1e6, 2),
                         'share': round(by[g].area / t, 3)} for g in G}
        tot[name]['total_km2'] = round(t / 1e6, 2)
    byg_r = {g: unary_union([x['g'] for x in R.values() if x['grade'] == g]) for g in G}
    byg_m = {g: unary_union([x['g'] for x in M.values() if x['grade'] == g]) for g in G}
    agree = {g: round(byg_r[g].intersection(byg_m[g]).area / byg_r[g].union(byg_m[g]).area, 3) for g in G}
    both = [r for r in rows if 'iou' in r]
    summary = {'totals': tot, 'iou_by_grade_land': agree,
               'iou_area_weighted': round(sum(r['iou'] * r['ha_lab'] for r in both) / sum(r['ha_lab'] for r in both), 3),
               'iou_median': sorted(r['iou'] for r in both)[len(both) // 2],
               'max_offset_median_m': sorted(r['max_offset_m'] for r in both)[len(both) // 2],
               'only_in_redrawn': [r['label'] for r in rows if r.get('ha_redrawn') and not r.get('ha_lab')],
               'only_in_lab': [r['label'] for r in rows if r.get('ha_lab') and not r.get('ha_redrawn')],
               'worst_iou': [(r['label'], r['iou'], r['max_offset_m']) for r in sorted(both, key=lambda r: r['iou'])[:8]]}
    json.dump({'summary': summary, 'rows': rows}, open(js, 'w'), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
