#!/usr/bin/env python3
"""The redlining story's numbers, computed from the cached data, into one file.

    python3 tools/stories/redlining/measure.py

Writes tools/stories/redlining/numbers.json: the one place the story's computed numbers live
(page.py and charts.py read them; nothing else types them). Inputs, all cached (see sources.md):

  data/holc/richmond-1937.geojson         Mapping Inequality's Richmond polygons (CC BY-NC)
  data/richmond-streetcars/osm.json        OpenStreetMap, fetched November 16, 2026 (ODbL)
  data/richmond-streetcars/yearbuilt.json  City of Richmond, Year_of_Construction parcels
  history/sanborn/jackson-ward-1952.geojson, jackson-ward-lost.geojson   the 1952 trace
  regions/richmond-1937.json               the hero's frame

Method. Areas and lengths are measured on a local plane (equirectangular about 37.55° N; the
error over 15 km is well under 0.1%). Each grade's land is the union of its polygons, so an
overlap between two areas of one grade is counted once; where areas of different grades
overlap, the overlap is counted in both (the overlap is reported). Highway length is the
length of OSM ways tagged highway=motorway (each carriageway of a divided road counted
separately, as the brief did), with and without motorway_link ramps, cut by each grade's land.
"""
import json
import math
import os

from shapely.geometry import LineString, Point, Polygon, MultiPolygon, shape
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LAT0 = 37.55
KX = 111320 * math.cos(math.radians(LAT0))
KY = 111132
GRADES = ['A', 'B', 'C', 'D']


def xy(lon, lat):
    return ((lon + 77.46) * KX, (lat - LAT0) * KY)


def proj(geom):
    if geom['type'] == 'Polygon':
        polys = [geom['coordinates']]
    elif geom['type'] == 'MultiPolygon':
        polys = geom['coordinates']
    else:
        return None
    out = [Polygon([xy(*p) for p in poly[0]], [[xy(*p) for p in r] for r in poly[1:]]).buffer(0) for poly in polys]
    return unary_union(out)


def main():
    root = lambda p: os.path.join(ROOT, p)  # noqa: E731
    holc = json.load(open(root('data/holc/richmond-1937.geojson')))
    areas = {}
    for f in holc['features']:
        p = f['properties']
        areas[p['label'].strip()] = {'grade': p.get('grade'), 'geom': proj(f['geometry'])}
    by = {g: unary_union([a['geom'] for a in areas.values() if a['grade'] == g]) for g in GRADES}
    graded = unary_union(list(by.values()))
    n = {g: sum(1 for a in areas.values() if a['grade'] == g) for g in GRADES}
    total = sum(by[g].area for g in GRADES)
    overlap = total - graded.area
    land = {g: {'areas': n[g], 'km2': round(by[g].area / 1e6, 2), 'share': round(by[g].area / total, 3)} for g in GRADES}
    ungraded = [k for k, a in areas.items() if a['grade'] not in GRADES]

    # The hero's frame (bearing 0: a lon/lat box about the center) and how much of each grade it holds.
    reg = json.load(open(root('regions/richmond-1937.json')))
    cx, cy = xy(*reg['center'])
    # The region's own scale: meters across at its center latitude.
    kx_c = 111320 * math.cos(math.radians(reg['center'][1]))
    hw = reg['width'] / 2 * KX / kx_c
    hd = reg['depth'] / 2
    frame = Polygon([(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)])
    in_frame = {g: round(by[g].intersection(frame).area / by[g].area, 3) for g in GRADES}
    cut = sorted(k for k, a in areas.items() if a['grade'] in GRADES and a['geom'].difference(frame).area > 0.02 * a['geom'].area)

    # Highways from the OSM cache.
    osm = json.load(open(root('data/richmond-streetcars/osm.json')))
    roads = {'motorway': [], 'motorway_link': []}
    refs = {}
    for e in osm['elements']:
        t = e.get('tags', {})
        hw_ = t.get('highway')
        if e['type'] != 'way' or hw_ not in roads or 'geometry' not in e:
            continue
        line = LineString([xy(p['lon'], p['lat']) for p in e['geometry']])
        roads[hw_].append(line)
        refs.setdefault(hw_, []).append((t.get('ref', ''), t.get('name', ''), line))
    def lengths(lines):
        pg = prep(graded)
        inside = [ln for ln in lines if pg.intersects(ln)]
        allg = sum(ln.intersection(graded).length for ln in inside)
        per = {g: sum(ln.intersection(by[g]).length for ln in inside) for g in GRADES}
        return {'km_in_graded': round(allg / 1000, 2), 'km_total_in_cache': round(sum(ln.length for ln in lines) / 1000, 1),
                'by_grade_km': {g: round(v / 1000, 2) for g, v in per.items()},
                'by_grade_share': {g: round(v / allg, 3) for g, v in per.items()}}
    motor = lengths(roads['motorway'])
    with_links = lengths(roads['motorway'] + roads['motorway_link'])
    # By road, motorway only, inside D land.
    road_d = {}
    for ref, name, line in refs['motorway']:
        k = (ref or name) or 'unnamed'
        v = line.intersection(by['D']).length
        if v > 0:
            road_d[k] = road_d.get(k, 0) + v
    road_d = {k: round(v / 1000, 2) for k, v in sorted(road_d.items(), key=lambda kv: -kv[1])}
    # Which D areas a highway crosses, and how far.
    d_crossed = {}
    for k, a in areas.items():
        if a['grade'] != 'D':
            continue
        v = sum(ln.intersection(a['geom']).length for ln in roads['motorway'])
        if v > 0:
            d_crossed[k] = round(v / 1000, 2)

    # Buildings drawn for 1937: today's parcels the city dates to 1937 or before, by grade.
    yb = json.load(open(root('data/richmond-streetcars/yearbuilt.json')))
    prepared = {g: prep(by[g]) for g in GRADES}
    yb_counts = {g: {'parcels': 0, 'by1937': 0, 'since2000': 0} for g in GRADES}
    for f in yb['features']:
        y = f['properties'].get('Year_Built')
        try:
            c = shape(f['geometry']).representative_point()
        except Exception:
            continue
        pt = Point(xy(c.x, c.y))
        for g in GRADES:
            if prepared[g].contains(pt):
                yb_counts[g]['parcels'] += 1
                if isinstance(y, (int, float)) and 1700 < y <= 1937:
                    yb_counts[g]['by1937'] += 1
                if isinstance(y, (int, float)) and y >= 2000:
                    yb_counts[g]['since2000'] += 1
                break
    for g in GRADES:
        c = yb_counts[g]
        c['share_by1937'] = round(c['by1937'] / c['parcels'], 3) if c['parcels'] else None
        c['share_2000_on'] = round(c['since2000'] / c['parcels'], 3) if c['parcels'] else None

    # The public-housing courts the brief names: which area each OSM outline's center falls in,
    # and how far it lies from the nearest D land.
    courts = {}
    names = ['Gilpin Court', 'Mosby Court', 'Creighton Court', 'Fairfield Court', 'Whitcomb Court', 'Hillside Court']
    for e in osm['elements']:
        nm = e.get('tags', {}).get('name', '')
        if e['type'] != 'way' or nm not in names or 'geometry' not in e or nm in courts:
            continue
        pts = [xy(q['lon'], q['lat']) for q in e['geometry']]
        if len(pts) < 4 or pts[0] != pts[-1]:
            continue
        c = Polygon(pts).centroid
        inside = [k for k, a in areas.items() if a['geom'].contains(c)]
        courts[nm] = {'osm': f"w{e['id']}", 'in': inside or ['ungraded'], 'm_to_D': round(by['D'].distance(c))}

    # A check on survival where the 1952 Sanborn sheets were traced (Jackson Ward).
    jw52 = json.load(open(root('history/sanborn/jackson-ward-1952.geojson')))
    jwlost = json.load(open(root('history/sanborn/jackson-ward-lost.geojson')))
    traced = len(jw52['features'])
    lost = sum(1 for f in jwlost['features'] if f['properties'].get('from') == 1952)
    jw = {'outlines_1952': traced, 'gone_today': lost, 'standing_today': traced - lost, 'share_standing': round((traced - lost) / traced, 3)}

    out = {
        'about': 'Computed by tools/stories/redlining/measure.py from the cached data; see its docstring for the method.',
        'graded_land': land, 'graded_km2_union': round(graded.area / 1e6, 2), 'overlap_km2': round(overlap / 1e6, 3),
        'ungraded_features': ungraded,
        'extent_km': [round((graded.bounds[2] - graded.bounds[0]) / 1000, 1), round((graded.bounds[3] - graded.bounds[1]) / 1000, 1)],
        'frame': {'share_of_grade_inside': in_frame, 'areas_cut_by_frame': cut},
        'motorway': motor, 'motorway_and_links': with_links, 'motorway_in_d_by_road_km': road_d, 'motorway_in_d_by_area_km': d_crossed,
        'yearbuilt_by_grade': yb_counts, 'courts': courts,
        'courts_note': 'Empty when the OSM cache holds no outline named for the court (true of the November 16, 2026 cache): the brief\'s placements are not yet rechecked here.',
        'jackson_ward_1952_survival': jw,
    }
    path = os.path.join(HERE, 'numbers.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1)
        fh.write('\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
