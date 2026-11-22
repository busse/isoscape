#!/usr/bin/env python3
"""The redlining story's numbers, computed from the cached data, into one file.

    python3 tools/stories/redlining/measure.py

Writes tools/stories/redlining/numbers.json: the one place the story's computed numbers live
(page.py and charts.py read them; nothing else types them). Inputs, all cached (see sources.md):

  the 1937 outlines named in outlines.py  (Mapping Inequality's, CC BY-NC, or a redraw from the scan)
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
from outlines import PATH as GRADES_PATH, load as load_outlines  # the one switch: outlines.py


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


def terrain_by_grade(holc):
    """Elevation (meters above sea level) and slope (degrees) of each grade's land, read from the
    cached lidar grid (USGS 3DEP, 5 m) at every grid node whose center falls inside the grade's
    outlines, unnumbered pieces included. The grid is today's bare earth, so the Turnpike's and
    the expressway's cuts are in it. Slope is from the grid's gradient over 5 m."""
    import gzip
    import numpy as np
    from matplotlib.path import Path
    raw = gzip.open(os.path.join(ROOT, 'data/richmond-streetcars/dem.bin.gz')).read()
    nl = raw.index(b'\n')
    h = json.loads(raw[:nl])
    q = np.frombuffer(raw[nl + 1:], dtype='<i2').reshape(h['height'], h['width'])
    z = np.where(q == -32768, np.nan, h['offset'] + q * h['scale']).astype(float)
    z[z < -5] = np.nan  # the void patches cleanDem marks
    W, S, E, N, Hh, Ww = h['west'], h['south'], h['east'], h['north'], h['height'], h['width']
    dx = (E - W) / Ww * 111320 * math.cos(math.radians((N + S) / 2))
    dy = (N - S) / Hh * 111132
    gy, gx = np.gradient(z, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy))).ravel()
    lon, lat = np.meshgrid(W + (np.arange(Ww) + 0.5) * (E - W) / Ww, N - (np.arange(Hh) + 0.5) * (N - S) / Hh)
    pts = np.column_stack([lon.ravel(), lat.ravel()])
    zz = z.ravel()
    picks = {g: [] for g in GRADES}
    for f in holc['features']:
        g = f['properties'].get('grade')
        if g not in picks:
            continue
        geom = shape(f['geometry'])
        for poly in (geom.geoms if geom.geom_type == 'MultiPolygon' else [geom]):
            x0, y0, x1, y1 = poly.bounds
            idx = np.where((pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1))[0]
            inside = Path(np.array(poly.exterior.coords)).contains_points(pts[idx])
            for hole in poly.interiors:
                inside &= ~Path(np.array(hole.coords)).contains_points(pts[idx])
            picks[g].append(idx[inside])
    out = {}
    for g in GRADES:
        i = np.concatenate(picks[g])
        e, s = zz[i], slope[i]
        ok = ~np.isnan(e) & ~np.isnan(s)
        out[g] = {'nodes': int(ok.sum()), 'elev_mean_m': round(float(np.mean(e[ok])), 1), 'elev_median_m': round(float(np.median(e[ok])), 1),
                  'elev_p10_m': round(float(np.percentile(e[ok], 10)), 1), 'elev_p90_m': round(float(np.percentile(e[ok], 90)), 1),
                  'slope_mean_deg': round(float(np.mean(s[ok])), 1), 'slope_median_deg': round(float(np.median(s[ok])), 1),
                  'share_steeper_10deg': float(np.mean(s[ok] > 10))}
    return out


CAPITOL_WAY = 45088494  # OSM's outline of the Virginia State Capitol; its centroid is the center
RING_M = 1000           # ring width for the location-only expectation
NEAR_M = 4000           # "near the center": within this distance of the Capitol
SAMPLE_M = 50           # grid step for the distance medians
SHIFTS_M = (12, 24)     # the fit's RMS error and its largest error at the map's edges


def base_rate(osm, by, graded, frame, motorway):
    """What the highway share in D should be compared with (the scholar's read, M2 and S10).

    - Density: km of motorway carriageway per km² of each grade's land, and of the ungraded land
      inside the drawn frame (the frame less all graded land: downtown, industry, rail yards,
      parks, the river and land outside the 1937 survey), over all land and within NEAR_M of
      the State Capitol.
    - Distance: the median distance from the Capitol of each grade's land, read at every node of
      a SAMPLE_M grid inside it.
    - Location alone: rings RING_M wide about the Capitol. In each ring the motorway inside
      graded land is shared among the grades in proportion to their land in that ring; summed
      over the rings, D's part is what location alone would give D.
    - Fit error: every outline shifted by each of SHIFTS_M in eight directions, D's share again.
    """
    import numpy as np
    from shapely import affinity
    cap = None
    for e in osm['elements']:
        if e['type'] == 'way' and e['id'] == CAPITOL_WAY:
            cap = Polygon([xy(q['lon'], q['lat']) for q in e['geometry']]).centroid
    assert cap is not None, 'the Capitol outline is not in the OSM cache'
    near = cap.buffer(NEAR_M, quad_segs=64)
    ungraded = frame.difference(graded)
    lands = {**{g: by[g] for g in GRADES}, 'ungraded': ungraded}
    pg = {k: prep(v) for k, v in lands.items()}

    def km_in(geom):
        return sum(ln.intersection(geom).length for ln in motorway) / 1000

    density, density_near = {}, {}
    for k, v in lands.items():
        density[k] = {'km': km_in(v), 'km2': v.area / 1e6}
        density[k]['km_per_km2'] = density[k]['km'] / density[k]['km2']
        w = v.intersection(near)
        density_near[k] = {'km': km_in(w), 'km2': w.area / 1e6}
        density_near[k]['km_per_km2'] = density_near[k]['km'] / density_near[k]['km2'] if w.area else None

    # Median distance from the Capitol, on a grid.
    x0, y0, x1, y1 = frame.bounds
    gx, gy = np.meshgrid(np.arange(x0, x1, SAMPLE_M), np.arange(y0, y1, SAMPLE_M))
    from shapely import points, contains
    pts = points(gx.ravel(), gy.ravel())
    dist = np.hypot(gx.ravel() - cap.x, gy.ravel() - cap.y)
    median_km = {}
    for k in GRADES:
        inside = contains(by[k], pts)
        median_km[k] = float(np.median(dist[inside])) / 1000

    # Location alone: rings about the Capitol.
    reach = max(Point(cap.x, cap.y).distance(Point(x, y)) for x, y in [(graded.bounds[0], graded.bounds[1]), (graded.bounds[2], graded.bounds[3]), (graded.bounds[0], graded.bounds[3]), (graded.bounds[2], graded.bounds[1])])
    rings = []
    expected = {g: 0.0 for g in GRADES}
    observed = {g: 0.0 for g in GRADES}
    r = 0
    while r < reach:
        ring = cap.buffer(r + RING_M, quad_segs=64).difference(cap.buffer(r, quad_segs=64)) if r else cap.buffer(RING_M, quad_segs=64)
        land = {g: by[g].intersection(ring) for g in GRADES}
        tot = sum(v.area for v in land.values())
        road = {g: km_in(land[g]) for g in GRADES}
        allr = sum(road.values())
        if tot > 0:
            for g in GRADES:
                expected[g] += allr * land[g].area / tot
                observed[g] += road[g]
        rings.append({'from_km': r / 1000, 'to_km': (r + RING_M) / 1000, 'graded_km2': tot / 1e6,
                      'D_land_share': land['D'].area / tot if tot else None, 'motorway_km_in_graded': allr,
                      'D_motorway_km': road['D']})
        r += RING_M
    total = sum(observed.values())
    loc = {'expected_share': {g: expected[g] / total for g in GRADES}, 'observed_share': {g: observed[g] / total for g in GRADES},
           'expected_km': expected, 'observed_km': observed, 'rings': rings}

    # Fit error: shift every outline and measure D's share again.
    shifts = {}
    for s in SHIFTS_M:
        vals = []
        for a in range(8):
            dx, dy = s * math.cos(a * math.pi / 4), s * math.sin(a * math.pi / 4)
            sb = {g: affinity.translate(by[g], dx, dy) for g in GRADES}
            sg = unary_union(list(sb.values()))
            allg = km_in(sg)
            vals.append(km_in(sb['D']) / allg)
        shifts[str(s)] = {'min': min(vals), 'max': max(vals)}
    edge = by['D'].boundary.buffer(25)
    return {
        'about': 'Base rates for the highway share in D (measure.py, base_rate): density, distance, location alone, fit error.',
        'capitol': {'osm_way': CAPITOL_WAY, 'lonlat': [cap.x / KX - 77.46, cap.y / KY + LAT0]},
        'ring_m': RING_M, 'near_m': NEAR_M, 'sample_m': SAMPLE_M,
        'density': density, 'density_near': density_near, 'median_distance_km': median_km,
        'location_alone': loc, 'shift_D_share': shifts,
        'D_km_within_25m_of_D_edge': km_in(by['D'].intersection(edge)),
    }


def name_checks(osm, areas):
    """Two overlaps the page's area names rest on (d5, the dignity read), sampled on a 20 m grid:
    the share of D8 inside the Oregon Hill Historic District as the Valentine bounds it (West Cary
    Street to the river, South Belvidere Street to Linden Street and Hollywood Cemetery), with
    the west line at Linden Street or at the cemetery's east edge; and the share of D1 west of
    North Belvidere Street and north of West Broad Street, in Carver as the City of Richmond's
    civic-group map bounds it."""
    import numpy as np

    def pts(names):
        return np.array([xy(q['lon'], q['lat']) for e in osm['elements'] if e['type'] == 'way' and e.get('tags', {}).get('name') in names
                         and e.get('tags', {}).get('highway') and e.get('geometry') for q in e['geometry']])
    cary, belv, lind = pts({'West Cary Street'}), pts({'South Belvidere Street', 'North Belvidere Street'}), pts({'South Linden Street'})
    broad = pts({'West Broad Street'})
    cem = [e for e in osm['elements'] if e['type'] == 'way' and e.get('tags', {}).get('name') == 'Hollywood Cemetery' and e.get('geometry')]
    cem_east = max(xy(q['lon'], q['lat'])[0] for e in cem for q in e['geometry'])

    def sample(g):
        x0, y0, x1, y1 = g.bounds
        from shapely import points, contains
        gx, gy = np.meshgrid(np.arange(x0, x1, 20), np.arange(y0, y1, 20))
        p = points(gx.ravel(), gy.ravel())
        k = contains(g, p)
        return gx.ravel()[k], gy.ravel()[k]

    def near(arr, v, axis):
        return arr[np.abs(arr[:, axis][None, :] - v[:, None]).argmin(axis=1)]

    x, y = sample(areas['D8']['geom'])
    south = y < near(cary, x, 0)[:, 1]
    east_of_b = x < near(belv, y, 1)[:, 0]
    low = south & east_of_b & (x > near(lind, y, 1)[:, 0])
    high = south & east_of_b & (x > cem_east)
    x1_, y1_ = sample(areas['D1']['geom'])
    b = near(belv, y1_, 1)
    carver = (x1_ < b[:, 0]) & (np.abs(b[:, 1] - y1_) < 330) & (y1_ > near(broad, x1_, 0)[:, 1])
    return {'D8_share_in_oregon_hill_district': {'west_line_at_linden_street': float(low.mean()), 'west_line_at_cemetery_east_edge': float(high.mean())},
            'D1_share_west_of_belvidere_north_of_broad': float(carver.mean())}


def main():
    root = lambda p: os.path.join(ROOT, p)  # noqa: E731
    holc = load_outlines(ROOT)
    areas = {}
    for i, f in enumerate(holc['features']):
        p = f['properties']
        # Pieces the map prints no number on (unnumbered.json) count in the totals by grade
        # and in no area's own figures.
        key = f'unnumbered-{i}' if p.get('unnumbered') else p['label'].strip()
        areas[key] = {'grade': p.get('grade'), 'geom': proj(f['geometry']), 'numbered': not p.get('unnumbered')}
    by = {g: unary_union([a['geom'] for a in areas.values() if a['grade'] == g]) for g in GRADES}
    graded = unary_union(list(by.values()))
    n = {g: sum(1 for a in areas.values() if a['grade'] == g and a['numbered']) for g in GRADES}
    total = sum(by[g].area for g in GRADES)
    overlap = total - graded.area
    land = {g: {'areas': n[g], 'km2': round(by[g].area / 1e6, 2), 'share': by[g].area / total} for g in GRADES}
    ungraded = [k for k, a in areas.items() if a['grade'] not in GRADES]
    unnumbered = {g: round(sum(a['geom'].area for a in areas.values() if a['grade'] == g and not a['numbered']) / 1e4, 1) for g in GRADES}

    # The hero's frame (bearing 0: a lon/lat box about the center) and how much of each grade it holds.
    reg = json.load(open(root('regions/richmond-1937.json')))
    cx, cy = xy(*reg['center'])
    # The region's own scale: meters across at its center latitude.
    kx_c = 111320 * math.cos(math.radians(reg['center'][1]))
    hw = reg['width'] / 2 * KX / kx_c
    hd = reg['depth'] / 2
    frame = Polygon([(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)])
    in_frame = {g: by[g].intersection(frame).area / by[g].area for g in GRADES}
    cut = sorted(k for k, a in areas.items() if a['grade'] in GRADES and a['numbered'] and a['geom'].difference(frame).area > 0.02 * a['geom'].area)
    # How much of each area cut by the frame lies outside it (share of the area's land).
    cut_outside = {k: areas[k]['geom'].difference(frame).area / areas[k]['geom'].area for k in cut}

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
                # Inside the drawn frame (regions/richmond-1937.json), graded or not.
                'km_in_frame': round(sum(ln.intersection(frame).length for ln in lines) / 1000, 1),
                'by_grade_km': {g: round(v / 1000, 2) for g, v in per.items()},
                'by_grade_share': {g: v / allg for g, v in per.items()}}
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
        if a['grade'] != 'D' or not a['numbered']:
            continue
        v = sum(ln.intersection(a['geom']).length for ln in roads['motorway'])
        if v > 0:
            d_crossed[k] = round(v / 1000, 2)

    # D1's carriageway by road: OSM's "Richmond-Petersburg Turnpike" (I-95, and I-95 with I-64)
    # and the rest (I-64 alone).
    d1 = areas['D1']['geom']
    d1_split = {'turnpike': 0.0, 'other': 0.0}
    for ref, name, line in refs['motorway']:
        d1_split['turnpike' if 'Turnpike' in name else 'other'] += line.intersection(d1).length
    d1_split = {k: round(v / 1000, 2) for k, v in d1_split.items()}
    # Two things the per-area text names: how much of OSM's Providence Park outline lies in D4,
    # and how many of D6's building outlines carry a historic or heritage tag.
    checks = {}
    for e in osm['elements']:
        t = e.get('tags', {})
        if e['type'] == 'way' and t.get('name') == 'Providence Park' and e.get('geometry') and len(e['geometry']) > 3:
            pp = Polygon([xy(q['lon'], q['lat']) for q in e['geometry']]).buffer(0)
            checks['providence_park_share_in_D4'] = pp.intersection(areas['D4']['geom']).area / pp.area
    pg6 = prep(areas['D6']['geom'])
    n6 = h6 = 0
    for e in osm['elements']:
        t = e.get('tags', {})
        if e['type'] != 'way' or 'building' not in t or not e.get('geometry'):
            continue
        pts = [xy(q['lon'], q['lat']) for q in e['geometry'] if q]
        if len(pts) < 3 or not pg6.contains(Point(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))):
            continue
        n6 += 1
        if any(k.startswith('historic') or k.startswith('heritage') for k in t):
            h6 += 1
    checks['providence_park_osm_is'] = 'leisure=park (a park, not the neighborhood): not used on the page from d5'
    checks.update(name_checks(osm, areas))
    checks['D6_buildings_osm'] = n6
    checks['D6_buildings_historic_or_heritage'] = h6

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
        c['share_by1937'] = c['by1937'] / c['parcels'] if c['parcels'] else None
        c['share_2000_on'] = c['since2000'] / c['parcels'] if c['parcels'] else None

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
        inside = [k for k, a in areas.items() if a['numbered'] and a['geom'].contains(c)]
        courts[nm] = {'osm': f"w{e['id']}", 'in': inside or ['ungraded'], 'm_to_D': round(by['D'].distance(c))}

    # Each D area, and A5 (the worked example's other half): its size, today's dated parcels
    # (how many the city dates to 1937 or before, to 1938-1977, and to 2000 or later), today's
    # OSM building outlines whose center falls inside, and limited-access highway inside it.
    per_area = {}
    focus = [k for k, a in areas.items() if a['grade'] == 'D' and a['numbered']] + ['A5']
    for k in focus:
        g = areas[k]['geom']
        pg = prep(g)
        c = {'km2': round(g.area / 1e6, 2), 'parcels': 0, 'by1937': 0, 'y1938_1977': 0, 'since2000': 0, 'buildings_osm': 0}
        for f in yb['features']:
            y = f['properties'].get('Year_Built')
            try:
                pt = shape(f['geometry']).representative_point()
            except Exception:
                continue
            if not pg.contains(Point(xy(pt.x, pt.y))):
                continue
            c['parcels'] += 1
            if isinstance(y, (int, float)) and 1700 < y <= 1937:
                c['by1937'] += 1
            elif isinstance(y, (int, float)) and 1938 <= y <= 1977:
                c['y1938_1977'] += 1
            if isinstance(y, (int, float)) and y >= 2000:
                c['since2000'] += 1
        for e in osm['elements']:
            if e['type'] != 'way' or 'building' not in e.get('tags', {}) or not e.get('geometry'):
                continue
            pts = [xy(q['lon'], q['lat']) for q in e['geometry'] if q]
            if len(pts) < 3:
                continue
            cx_ = sum(p[0] for p in pts) / len(pts); cy_ = sum(p[1] for p in pts) / len(pts)
            if pg.contains(Point(cx_, cy_)):
                c['buildings_osm'] += 1
        c['motorway_km'] = round(sum(ln.intersection(g).length for ln in roads['motorway']) / 1000, 2)
        for key in ('by1937', 'y1938_1977', 'since2000'):
            c['share_' + key] = c[key] / c['parcels'] if c['parcels'] else None
        per_area[k] = c

    # A check on survival where the 1952 Sanborn sheets were traced (Jackson Ward).
    jw52 = json.load(open(root('history/sanborn/jackson-ward-1952.geojson')))
    jwlost = json.load(open(root('history/sanborn/jackson-ward-lost.geojson')))
    traced = len(jw52['features'])
    lost = sum(1 for f in jwlost['features'] if f['properties'].get('from') == 1952)
    jw = {'outlines_1952': traced, 'gone_today': lost, 'standing_today': traced - lost, 'share_standing': (traced - lost) / traced}

    out = {
        'about': 'Computed by tools/stories/redlining/measure.py from the cached data; see its docstring for the method.',
        'graded_land': land, 'graded_km2_union': round(graded.area / 1e6, 2), 'overlap_km2': round(overlap / 1e6, 3),
        'ungraded_features': ungraded,
        'unnumbered_ha_by_grade': unnumbered,
        'extent_km': [round((graded.bounds[2] - graded.bounds[0]) / 1000, 1), round((graded.bounds[3] - graded.bounds[1]) / 1000, 1)],
        'frame': {'share_of_grade_inside': in_frame, 'areas_cut_by_frame': cut, 'share_of_area_outside': cut_outside},
        'motorway': motor, 'motorway_and_links': with_links, 'motorway_in_d_by_road_km': road_d, 'motorway_in_d_by_area_km': d_crossed,
        'motorway_in_d1_km': d1_split, 'osm_checks': checks,
        'motorway_base_rate': base_rate(osm, by, graded, frame, roads["motorway"]),
        'yearbuilt_by_grade': yb_counts, 'courts': courts,
        'courts_note': 'Empty when the OSM cache holds no outline named for the court (true of the November 16, 2026 cache): the brief\'s placements are not yet rechecked here.',
        'jackson_ward_1952_survival': jw,
        'areas': per_area,
        'terrain_by_grade': terrain_by_grade(holc),
        'outlines': GRADES_PATH,
    }
    path = os.path.join(HERE, 'numbers.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=1)
        fh.write('\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
