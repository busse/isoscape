"""
Dev tool (floods spike, step 15): cross-sections of the cached 2 m lidar across Shockoe
Bottom's riverfront (Dock Street, the CSX viaduct, the railroad, the floodwall, the Dock),
with every OSM way the section crosses marked. One PNG per section and one sheet of all.

  python3 tools/floods/sections.py <dem-prefix> <osm.json> <spill.json> <out-dir>
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from common import Grid, KX, KY, load_dem, osm_ways

FT = 3.28084
# Each: name, center lon/lat, bearing of the section line (degrees from north, toward the river), half-length m.
SECTIONS = [
    ('A  15th Street', (-77.43235, 37.53255), 215, 110),
    ('B  canal crossing at 17th and Dock (the spill saddle)', (-77.43050, 37.53160), 200, 110),
    ('C  18th Street', (-77.42860, 37.53150), 215, 110),
    ('D  20th Street', (-77.42680, 37.53060), 215, 110),
    ('E  along Dock Street, 14th to 21st', (-77.42900, 37.53220), 118, 330),
]

def seg_cross(p, q, a, b):
    rx, ry = q[0] - p[0], q[1] - p[1]; sx, sy = b[0] - a[0], b[1] - a[1]
    den = rx * sy - ry * sx
    if abs(den) < 1e-12: return None
    t = ((a[0] - p[0]) * sy - (a[1] - p[1]) * sx) / den
    u = ((a[0] - p[0]) * ry - (a[1] - p[1]) * rx) / den
    return t if 0 <= t <= 1 and 0 <= u <= 1 else None

def main():
    prefix, osm_path, spill_path, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    h, z = load_dem(prefix); g = Grid(h)
    zmax = ndimage.maximum_filter(z, size=3)  # the highest pixel within 2 m: a thin wall's best chance
    spill = json.load(open(spill_path))
    ways = [w for w in osm_ways(osm_path) if w[2]]
    sp = spill['cases']['a_lidar_as_is']['river']['spill_level_m']
    fig_all, axes = plt.subplots(len(SECTIONS), 1, figsize=(12, 3.2 * len(SECTIONS)))
    for (name, (lon, lat), brg, half), axa in zip(SECTIONS, axes):
        b = math.radians(brg)
        ux, uy = math.sin(b), math.cos(b)  # meters east, north per meter along
        s = np.arange(-half, half + 0.01, 1.0)
        lons = lon + s * ux / KX; lats = lat + s * uy / KY
        rc = np.array([g.rc(lo, la) for lo, la in zip(lons, lats)]).T
        prof = ndimage.map_coordinates(z, rc, order=1)
        profx = ndimage.map_coordinates(zmax, rc, order=1)
        p0 = (lons[0], lats[0]); p1 = (lons[-1], lats[-1])
        marks = []
        for wid, t, pts in ways:
            kind = ('floodwall' if t.get('wall') == 'flood_wall' else
                    ('rail bridge' if t.get('bridge') else 'railroad') if t.get('railway') in ('rail', 'disused', 'abandoned') else
                    ((t.get('name') or t['highway']) + (' (bridge)' if t.get('bridge') else '')) if t.get('highway') in ('primary', 'secondary', 'tertiary', 'residential', 'trunk', 'motorway', 'unclassified', 'motorway_link', 'trunk_link') else
                    (t.get('name') or 'water') if (t.get('natural') == 'water' or t.get('waterway')) else None)
            if kind is None: continue
            for a, c in zip(pts, pts[1:]):
                tt = seg_cross(p0, p1, a, c)
                if tt is not None: marks.append((s[0] + tt * (s[-1] - s[0]), kind))
        for ax in ([axa] if True else []):
            ax.fill_between(s, -2, prof, color='#d9cbb0')
            ax.plot(s, prof, 'k-', lw=1, label='lidar (2 m cells, as cached)')
            ax.plot(s, profx, 'k:', lw=0.8, label='highest cell within 2 m')
            ax.axhline(sp, color='tab:blue', lw=1, ls='--', label=f'spill level, lidar as is: {sp:.2f} m ({sp*FT:.1f} ft)')
            for lvl, lab in ((27 / FT, '27 ft'), (35 / FT, '35 ft')):
                ax.axhline(lvl, color='tab:red', lw=0.6, ls=':')
                ax.text(s[0], lvl + 0.1, f'reported Gaston surfaces: {lab}' if lab == '27 ft' else lab, fontsize=6, color='tab:red')
            for x, k in sorted(set((round(x, 1), k) for x, k in marks)):
                ax.axvline(x, color='tab:red' if k == 'floodwall' else '0.5', lw=1.2 if k == 'floodwall' else 0.5)
                ax.text(x, ax.get_ylim()[1] if False else 11.6, k, rotation=90, fontsize=6, va='top', ha='right', color='tab:red' if k == 'floodwall' else '0.3')
            ax.set_ylim(0, 12); ax.set_xlim(s[0], s[-1])
            ax.set_title(f'{name}   (from {"inland" if brg != 118 else "west"} on the left; {lat:.5f}, {lon:.5f}, bearing {brg} deg)', fontsize=8, loc='left')
            ax.set_ylabel('m NAVD88', fontsize=7); ax.tick_params(labelsize=6)
            ax.legend(fontsize=6, loc='lower left')
        f1, a1 = plt.subplots(figsize=(12, 4))
        a1.fill_between(s, -2, prof, color='#d9cbb0'); a1.plot(s, prof, 'k-', lw=1); a1.plot(s, profx, 'k:', lw=0.8)
        a1.axhline(sp, color='tab:blue', lw=1, ls='--')
        for x, k in sorted(set((round(x, 1), k) for x, k in marks)):
            a1.axvline(x, color='tab:red' if k == 'floodwall' else '0.5', lw=1.2 if k == 'floodwall' else 0.5)
            a1.text(x, 11.6, k, rotation=90, fontsize=7, va='top', ha='right', color='tab:red' if k == 'floodwall' else '0.3')
        a1.set_ylim(0, 12); a1.set_xlim(s[0], s[-1]); a1.set_ylabel('m NAVD88'); a1.set_xlabel('meters along the section')
        a1.set_title(name + f'   (blue dashed: spill level {sp:.2f} m)', fontsize=9, loc='left')
        f1.savefig(os.path.join(out, 'section-' + name.split()[0] + '.png'), dpi=100, bbox_inches='tight'); plt.close(f1)
    axes[-1].set_xlabel('meters along the section', fontsize=7)
    fig_all.suptitle('Shockoe Bottom riverfront: cross-sections of the cached 3DEP lidar (2 m)', fontsize=10)
    fig_all.tight_layout()
    fig_all.savefig(os.path.join(out, 'sections.png'), dpi=100)

if __name__ == '__main__':
    main()
