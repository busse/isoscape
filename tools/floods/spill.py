"""
Dev tool (floods spike, step 15): the spill-path test for Shockoe Bottom on the cached 2 m
lidar (3DEP, as isoscape reads it; see export-dem.ts). Fills the bowl from its low point
upward (a rising pool: cells taken in order of the highest ground on the lowest path to them)
and reports where and at what water elevation the pool first reaches open water, under
several assumptions about the ground. Not part of isoscape; numpy, scipy and matplotlib only.

  python3 tools/floods/spill.py <dem-prefix> <osm.json> <out-dir>
"""
import heapq, json, math, os, sys
import numpy as np
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(__file__))
from common import Grid, KX, KY, load_dem, osm_ways

FT = 3.28084
CANAL_NAMES = ('James River and Kanawha Canal', 'Haxall Canal', 'Haxall Canal / James River')

def raster_poly(g, shape, pts):
    """Cells whose centers fall inside a lon/lat ring."""
    rr = [g.rc(lon, lat) for lon, lat in pts]
    r0 = max(0, int(min(r for r, _ in rr)) - 1); r1 = min(shape[0], int(max(r for r, _ in rr)) + 2)
    c0 = max(0, int(min(c for _, c in rr)) - 1); c1 = min(shape[1], int(max(c for _, c in rr)) + 2)
    m = np.zeros(shape, bool)
    if r1 <= r0 or c1 <= c0: return m
    R, C = np.mgrid[r0:r1, c0:c1]
    inside = Path([(c, r) for r, c in rr]).contains_points(np.c_[C.ravel(), R.ravel()]).reshape(R.shape)
    m[r0:r1, c0:c1] = inside
    return m

def raster_line(g, shape, pts, half):
    """Cells within `half` meters of a lon/lat polyline."""
    m = np.zeros(shape, bool)
    for (lo0, la0), (lo1, la1) in zip(pts, pts[1:]):
        a = np.array(g.rc(lo0, la0)); b = np.array(g.rc(lo1, la1))
        pad = half / 2 + 2
        r0 = max(0, int(min(a[0], b[0]) - pad)); r1 = min(shape[0], int(max(a[0], b[0]) + pad) + 1)
        c0 = max(0, int(min(a[1], b[1]) - pad)); c1 = min(shape[1], int(max(a[1], b[1]) + pad) + 1)
        if r1 <= r0 or c1 <= c0: continue
        R, C = np.mgrid[r0:r1, c0:c1]
        d = b - a; l2 = (d ** 2).sum()
        t = np.clip(((R - a[0]) * d[0] + (C - a[1]) * d[1]) / l2 if l2 > 0 else 0, 0, 1)
        dist = np.hypot((R - a[0] - t * d[0]) * g.dy, (C - a[1] - t * d[1]) * g.dx)
        m[r0:r1, c0:c1] |= dist <= half
    return m

def membrane(z, mask, iters=4000):
    """Ground inside `mask` rebuilt from its rim: a Laplace fill (each cell the mean of its four
    neighbors), the rim held at the measured ground."""
    out = z.copy()
    rows, cols = np.where(mask)
    if len(rows) == 0: return out
    r0, r1 = max(0, rows.min() - 2), min(z.shape[0], rows.max() + 3)
    c0, c1 = max(0, cols.min() - 2), min(z.shape[1], cols.max() + 3)
    sub = out[r0:r1, c0:c1].astype(np.float64); m = mask[r0:r1, c0:c1]
    sub[m] = np.mean(sub[~m])
    for _ in range(iters):
        avg = (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1)) / 4
        sub[m] = avg[m]
    out[r0:r1, c0:c1] = sub
    return out

def rising_pool(z, seed, targets):
    """Fill from `seed` upward. Returns, for each cell reached, its key (the highest ground on the
    lowest path from the seed), in the order reached; and, for each target name, the first cell
    of it reached, the spill level, and the saddle (the cell that set that level)."""
    H, W = z.shape
    key = np.full(z.shape, np.inf)
    done = np.zeros(z.shape, bool)
    parent = np.full(z.shape, -1, np.int64)
    heap = [(float(z[seed]), seed[0] * W + seed[1])]
    key[seed] = z[seed]
    hits = {}
    order = []
    while heap and len(hits) < len(targets):
        k, idx = heapq.heappop(heap)
        r, c = divmod(idx, W)
        if done[r, c]: continue
        done[r, c] = True
        order.append(idx)
        for name, t in targets.items():
            if name not in hits and t[r, c]:
                # Walk back to the seed: the saddle is the highest cell on the path.
                path = []; p = idx
                while p >= 0: path.append(p); p = parent.flat[p]
                hz = [z.flat[q] for q in path]
                s = path[int(np.argmax(hz))]
                hits[name] = {'cell': idx, 'level': float(k), 'saddle': s, 'path': path[::-1]}
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and not done[rr, cc]:
                nk = max(k, float(z[rr, cc]))
                if nk < key[rr, cc]:
                    key[rr, cc] = nk; parent[rr, cc] = idx
                    heapq.heappush(heap, (nk, rr * W + cc))
    return key, done, hits

def stage_table(z, key, done, levels, cell_area, probes):
    rows = []
    for L in levels:
        pool = done & (key <= L)
        depth = np.where(pool, L - z, 0)
        row = {'level_m': round(L, 2), 'level_ft': round(L * FT, 1), 'area_ha': round(pool.sum() * cell_area / 1e4, 2),
               'volume_m3': int(depth.sum() * cell_area), 'max_depth_m': round(float(depth.max()), 2)}
        for name, (r, c) in probes.items():
            row['depth_' + name] = round(float(L - z[r, c]), 2) if pool[r, c] else 0.0
        rows.append(row)
    return rows

def main():
    prefix, osm_path, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    h, z0 = load_dem(prefix)
    g = Grid(h)
    z0 = z0.astype(np.float64)
    cell_area = g.dx * g.dy
    ways = list(osm_ways(osm_path))
    # Mapped canal and dock water. The lidar reads their surfaces at about 4.6 to 5.3 m (held
    # above the tide), so they are not the James: they are ground the pool can fill.
    canal = np.zeros(z0.shape, bool)
    dock = np.zeros(z0.shape, bool)
    for wid, t, pts in ways:
        if t.get('natural') == 'water' and t.get('name') in CANAL_NAMES and len(pts) > 3:
            # The relation's members are the Dock, below 17th Street to Rocketts, riverward of the wall.
            if str(wid).startswith('r'): dock |= raster_poly(g, z0.shape, pts)
            else: canal |= raster_poly(g, z0.shape, pts)
    # The James: the largest body of ground the lidar puts below 1.2 m (its hydro-flattened tidal
    # surface reads about 0 to 0.5 m here).
    from scipy import ndimage
    lab, n = ndimage.label(z0 < 1.2)
    sizes = ndimage.sum(np.ones_like(z0), lab, range(1, n + 1))
    river = lab == (1 + int(np.argmax(sizes)))
    walls = [(wid, pts) for wid, t, pts in ways if t.get('wall') == 'flood_wall']
    # The wall's footprint to take out (4 m either side of OSM's line), and the wall itself to
    # stand in (1.5 m either side: watertight on a 2 m grid), each way on its own so the gaps
    # between OSM's ways (the openings, open at street grade) stay open.
    wall_mask = np.zeros(z0.shape, bool)
    wall_line = np.zeros(z0.shape, bool)
    for _, pts in walls:
        wall_mask |= raster_line(g, z0.shape, pts, 4.0)
        wall_line |= raster_line(g, z0.shape, pts, 1.5)
    # The APPROXIMATE tie-ins of regions/richmond-floods.json, and the OSM gaps closed: only
    # for the hypothetical case with every gate shut.
    region = json.load(open(os.path.join(os.path.dirname(__file__), '..', '..', 'regions', 'richmond-floods.json')))
    closed = wall_line.copy()
    for w in region['floodwalls']:
        if 'line' in w: closed |= raster_line(g, z0.shape, w['line'], 1.5)
    gaps = []
    ends = [(pts[0], pts[-1]) for _, pts in walls]
    for i, (a0, a1) in enumerate(ends):
        for j, (b0, b1) in enumerate(ends):
            if j <= i: continue
            for p in (a0, a1):
                for q in (b0, b1):
                    d = math.hypot((p[0] - q[0]) * KX, (p[1] - q[1]) * KY)
                    if 0 < d < 60: gaps.append((p, q, d))
    for p, q, d in gaps: closed |= raster_line(g, z0.shape, [p, q], 1.5)
    WALL_TOP = float(region['floodwalls'][0]['top'])  # a placeholder, not a researched value
    # Railroad on the ground (not bridges) in the window: the embankments along the riverfront.
    rail_mask = np.zeros(z0.shape, bool)
    for wid, t, pts in ways:
        if t.get('railway') in ('rail', 'disused', 'abandoned') and t.get('bridge') is None and t.get('tunnel') is None:
            rail_mask |= raster_line(g, z0.shape, pts, 9.0)
    # Limit the rail removal to the riverfront strip between the Bottom and the water.
    strip = raster_poly(g, z0.shape, [(-77.4372, 37.5352), (-77.4240, 37.5300), (-77.4232, 37.5285), (-77.4360, 37.5320), (-77.4372, 37.5352)])
    rail_mask &= strip

    # Intersections from OSM's street geometry; the market at OSM's outline's middle (100 N. 17th St.).
    probes_ll = {'17th_and_Main': (-77.428532, 37.533434), '17th_Street_Market': (-77.42826, 37.53399), '15th_and_Main': (-77.430374, 37.534548)}
    probes = {k: tuple(int(round(v)) for v in g.rc(*ll)) for k, ll in probes_ll.items()}
    # The low point: the lowest ground in the Bottom's blocks, off the canal.
    # Streets and blocks north of Cary Street between 14th and 21st, away from the canal.
    box = raster_poly(g, z0.shape, [(-77.4330, 37.5328), (-77.4265, 37.5318), (-77.4265, 37.5365), (-77.4330, 37.5365), (-77.4330, 37.5328)])
    from scipy import ndimage as ndi
    near_canal = ndi.binary_dilation(canal, iterations=8)
    cand = np.where(box & ~near_canal, z0, np.inf)
    seed = np.unravel_index(np.argmin(cand), z0.shape)

    cases = {
        'a_lidar_as_is': z0,
        'b_wall_standing_openings_open': np.where(wall_line, np.maximum(z0, WALL_TOP), z0),
        'c_wall_removed': membrane(z0, wall_mask),
        'd_wall_and_rail_embankments_removed': membrane(z0, wall_mask | rail_mask),
        'e_hypothetical_every_gate_shut': np.where(closed, np.maximum(z0, WALL_TOP), z0),
    }
    report = {'wall_top_placeholder_m': WALL_TOP, 'osm_wall_gaps_m': [round(d, 1) for _, _, d in gaps],
              'osm_wall_gaps_lonlat': [[list(p), list(q)] for p, q, _ in gaps], 'dem': h, 'cell_m': [g.dx, g.dy], 'seed': {'rc': list(map(int, seed)), 'lonlat': g.ll(*seed), 'z_m': float(z0[seed]), 'z_ft': float(z0[seed] * FT)},
              'probes': {k: {'lonlat': probes_ll[k], 'z_m': float(z0[v]), 'z_ft': float(z0[v] * FT)} for k, v in probes.items()},
              'cases': {}}
    np.save(os.path.join(out, 'masks.npy'), np.stack([canal, wall_mask, rail_mask, river, dock, wall_line, closed]))
    for name, z in cases.items():
        np.save(os.path.join(out, f'z-{name}.npy'), z.astype(np.float32))
        key, done, hits = rising_pool(z, seed, {'canal': canal, 'dock': dock, 'river': river})
        res = {}
        for tname, hit in hits.items():
            sr, sc = divmod(hit['saddle'], z.shape[1])
            cr, cc = divmod(hit['cell'], z.shape[1])
            res[tname] = {'spill_level_m': round(hit['level'], 2), 'spill_level_ft': round(hit['level'] * FT, 1),
                          'saddle_lonlat': [round(v, 6) for v in g.ll(sr, sc)], 'saddle_z_m': round(float(z[sr, sc]), 2),
                          'reached_at_lonlat': [round(v, 6) for v in g.ll(cr, cc)],
                          'path_lonlat': [[round(v, 6) for v in g.ll(*divmod(p, z.shape[1]))] for p in hit['path'][::4]]}
        top = res['river']['spill_level_m']
        levels = list(np.arange(math.ceil(z0[seed] * 2) / 2, top, 0.5)) + [top]
        res['stage'] = stage_table(z, key, done, levels, cell_area, probes)
        report['cases'][name] = res
        np.save(os.path.join(out, f'key-{name}.npy'), np.where(done, key, np.nan).astype(np.float32))
        print(name, {k: (v['spill_level_m'], v['saddle_lonlat']) for k, v in res.items() if 'spill_level_m' in v})
    json.dump(report, open(os.path.join(out, 'spill.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
