"""
Dev tool (floods spike, step 15): the plan map, stage-area-volume chart and outlet chart
for the spill-path test, from spill.py's and outlet.py's output.

  python3 tools/floods/charts.py <dem-prefix> <osm.json> <spill-out-dir> <png-dir>
"""
import json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
sys.path.insert(0, os.path.dirname(__file__))
from common import Grid, KX, KY, load_dem, osm_ways

FT = 3.28084
CASES = [('a_lidar_as_is', 'a: lidar as is', 'tab:blue'),
         ('b_wall_standing_openings_open', 'b: wall standing, openings open', 'tab:red'),
         ('c_wall_removed', 'c: wall removed', 'tab:green'),
         ('d_wall_and_rail_embankments_removed', 'd: wall and rail embankments removed', 'tab:purple')]
REPORTED = (24 / FT, 35 / FT)

def plan(h, z, g, osm, rep, out):
    W, E, S, N = -77.4370, -77.4235, 37.5285, 37.5395
    r0, c0 = g.rc(W, N); r1, c1 = g.rc(E, S)
    r0, r1, c0, c1 = int(r0), int(r1) + 1, int(c0), int(c1) + 1
    sub = z[r0:r1, c0:c1].astype(float)
    ext = [g.ll(r0, c0)[0], g.ll(r0, c1)[0], g.ll(r1, c0)[1], g.ll(r0, c0)[1]]
    ls = LightSource(315, 40)
    rgb = ls.shade(np.clip(sub, 0, 16), plt.cm.gist_earth, vert_exag=3, blend_mode='soft', vmin=-2, vmax=18, dx=g.dx, dy=g.dy)
    fig, ax = plt.subplots(figsize=(12, 10.5))
    ax.imshow(rgb, extent=ext)
    X = np.linspace(ext[0], ext[1], sub.shape[1]); Y = np.linspace(ext[3], ext[2], sub.shape[0])
    cs = ax.contour(X, Y, sub, levels=[5, 6, 7, 8, 9, 10], colors='k', linewidths=0.35, alpha=0.6)
    ax.clabel(cs, fontsize=6, fmt='%d m')
    key = np.load(os.path.join(os.path.dirname(out), 'key-a_lidar_as_is.npy'))[r0:r1, c0:c1]
    sp = rep['cases']['a_lidar_as_is']['river']['spill_level_m']
    pool = np.where(key <= sp, 1.0, np.nan)
    ax.imshow(pool, extent=ext, cmap='Blues', vmin=0, vmax=1.2, alpha=0.75)
    for wid, t, pts in osm:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < W or min(xs) > E or max(ys) < S or min(ys) > N: continue
        if t.get('wall') == 'flood_wall': ax.plot(xs, ys, '-', color='#c0392b', lw=2.6, solid_capstyle='butt')
        elif t.get('highway') in ('primary', 'secondary', 'tertiary', 'residential', 'unclassified') and not t.get('bridge'):
            ax.plot(xs, ys, '-', color='white', lw=0.6, alpha=0.8)
    for p, q in rep['osm_wall_gaps_lonlat']:
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        if W < m[0] < E and S < m[1] < N: ax.plot(*m, 'o', mfc='none', mec='#c0392b', ms=9, mew=1.5)
    for name, label, col in CASES:
        c = rep['cases'][name]['river']
        path = np.array(c['path_lonlat'])
        ax.plot(path[:, 0], path[:, 1], '-', color=col, lw=1.6, alpha=0.9)
        ax.plot(*c['saddle_lonlat'], '*', color=col, ms=16, mec='k', mew=0.6, label=f"{label}: spills at {c['spill_level_m']:.2f} m ({c['spill_level_ft']:.1f} ft)")
    ax.plot(*rep['seed']['lonlat'], 'v', color='k', ms=10, label=f"low point {rep['seed']['z_m']:.2f} m ({rep['seed']['z_ft']:.1f} ft)")
    for k, v in rep['probes'].items():
        ax.plot(*v['lonlat'], 's', color='w', mec='k', ms=7)
        ax.text(v['lonlat'][0] + 0.0001, v['lonlat'][1] + 0.0001, f"{k.replace('_', ' ')}\n{v['z_m']:.2f} m ({v['z_ft']:.1f} ft)", fontsize=7)
    ax.text(-77.4290, 37.5295, 'the Dock\n(held water, lidar 4.6 m)', fontsize=7, color='w', ha='center')
    ax.text(-77.4355, 37.5300, 'the James', fontsize=9, color='w')
    ax.annotate('the routes reach the James here,\nin the tidal water by the Dock\'s head', xy=(-77.43094, 37.53093), xytext=(-77.4345, 37.5292), fontsize=7, color='w', arrowprops=dict(arrowstyle='->', color='w'))
    ax.set_xlim(W, E); ax.set_ylim(S, N); ax.set_aspect(1 / math.cos(math.radians(37.533)))
    ax.set_title("Shockoe Bottom on the cached 3DEP lidar (2 m): the lowest overland route from the low point to the James\n"
                 "blue: the pool at case a's spill level; red line: OSM floodwall; red circles: gaps between OSM's wall ways (road and rail openings).\n"
                 "Each route is one lowest path from the low point; across the flat held water of the Dock it wanders", fontsize=9, loc='left')
    ax.legend(fontsize=7, loc='upper left', framealpha=0.9)
    ax.tick_params(labelsize=6)
    fig.savefig(out, dpi=110, bbox_inches='tight')

def stage(rep, out):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    for name, label, col in CASES[:2]:
        rows = rep['cases'][name]['stage']
        L = [r['level_m'] for r in rows]
        a1.plot(L, [r['area_ha'] for r in rows], 'o-', color=col, label=f'{label}: area')
        a2.plot(L, [r['volume_m3'] / 1000 for r in rows], 'o-', color=col, label=f'{label}: volume')
        for ax in (a1, a2): ax.axvline(L[-1], color=col, ls='--', lw=0.8)
    for ax in (a1, a2):
        ax.axvspan(*REPORTED, color='tab:red', alpha=0.08)
        ax.text(REPORTED[0] + 0.05, ax.get_ylim()[1] * 0.9, 'Gaston surfaces implied by\nreported depths, 24 to 35 ft\n(all above both spill levels)', fontsize=7, color='tab:red')
        ax.set_xlabel('pool level, m NAVD88'); ax.grid(alpha=0.3); ax.set_xlim(4, 11)
        sec = ax.secondary_xaxis('top', functions=(lambda m: m * FT, lambda f: f / FT)); sec.set_xlabel('ft NAVD88', fontsize=8)
    a1.set_ylabel('pool area, hectares'); a2.set_ylabel('pool volume, thousand m³')
    a1.legend(fontsize=7, loc='center left'); a2.legend(fontsize=7, loc='center left')
    fig.suptitle('Stage, area and volume of the pool rising from the low point, up to where it first spills (dashed). '
                 '17th and Main (ground 6.58 m) stays dry in a and gets 4 cm in b; the 17th Street Market (5.84 m) gets 0.78 m in b.', fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=100)

def outlet(o, out):
    rows = o['rows']
    L = [r['level_m'] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(L, [r['Q_wall_removed_m3s'] for r in rows], '-', color='tab:green', label='riverfront line open along its 1.2 km (wall removed)')
    ax.plot(L, [r['Q_openings_only_m3s'] for r in rows], '-', color='tab:red', label='only the four gaps in OSM\'s wall open (wall standing, gates open)')
    ax.axhspan(170, 310, color='0.5', alpha=0.15)
    ax.text(5.6, 330, 'research\'s rough runoff estimate, 6,000 to 11,000 cfs (rational method, whole watershed)', fontsize=7)
    ax.axvspan(*REPORTED, color='tab:red', alpha=0.08)
    ax.text(REPORTED[0] + 0.05, 1400, 'Gaston surfaces implied\nby reported depths', fontsize=7, color='tab:red')
    ax.set_yscale('log'); ax.set_ylim(1, 5000); ax.set_xlim(5.5, 11)
    ax.set_xlabel('pool level, m NAVD88'); ax.set_ylabel('overflow, m³/s (log)')
    sec = ax.secondary_xaxis('top', functions=(lambda m: m * FT, lambda f: f / FT)); sec.set_xlabel('ft NAVD88', fontsize=8)
    ax.grid(alpha=0.3, which='both'); ax.legend(fontsize=7, loc='lower right')
    ax.set_title('Order of magnitude only: overflow over the riverfront line by a broad-crested weir formula (Q = 1.7 b H^1.5).\n'
                 'Ignores the sewers, submergence by the Dock, the approach and every opening\'s real width and sill.', fontsize=8, loc='left')
    fig.tight_layout(); fig.savefig(out, dpi=100)

def main():
    prefix, osm_path, sp_dir, png = sys.argv[1:5]
    os.makedirs(png, exist_ok=True)
    h, z = load_dem(prefix); g = Grid(h)
    rep = json.load(open(os.path.join(sp_dir, 'spill.json')))
    osm = [w for w in osm_ways(osm_path) if w[2]]
    plan(h, z, g, osm, rep, os.path.join(sp_dir, 'plan.png'))
    stage(rep, os.path.join(sp_dir, 'stage.png'))
    outlet(json.load(open(os.path.join(sp_dir, 'outlet.json'))), os.path.join(sp_dir, 'outlet.png'))
    for f in ('plan.png', 'stage.png', 'outlet.png'): os.replace(os.path.join(sp_dir, f), os.path.join(png, f))

if __name__ == '__main__':
    main()
