#!/usr/bin/env python3
"""The Gaston rain pictures: plan map, hourly small multiples, hyetograph, radar-vs-gauge check,
watershed figure, and the storm-total bands as GeoJSON.

    python3 tools/floods/rain/figures.py OUTDIR [--round N]

Reads tools/floods/rain/data/ (made by analyze.py and watershed.py). Dev tool: numpy, scipy,
matplotlib, shapely. Writes PNGs (under 2 MB each) and data/bands.geojson.
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style import R, plt, cmap_for, TOTAL_LEVELS, HOURLY_LEVELS, footer, mix, P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
COS = np.cos(np.radians(37.55))
EDT = np.timedelta64(-4, "h")

rain = json.load(open(os.path.join(DATA, "rain.json")))
grids = np.load(os.path.join(DATA, "radar-grids.npz"))
LATS, LONS = grids["lats"], grids["lons"]
counties = json.load(open(os.path.join(DATA, "counties.geojson")))
water = json.load(open(os.path.join(DATA, "water.geojson")))
shed = json.load(open(os.path.join(DATA, "watershed.geojson")))["features"][0]
track = json.load(open(os.path.join(DATA, "gaston-track.json")))

SRC_RADAR = ("Rain: NEXRAD Level II, KAKQ Wakefield (NOAA, via the Unidata bucket on AWS), tropical Z = 250 R^1.2, "
             "corrected to gauges (NCEI GHCN-Daily and Global Hourly; NWS Wakefield and NHC reports).")
SRC_MAP = "Boundaries and water: US Census TIGER 2023. Watershed: computed from USGS 3DEP. Track: NHC HURDAT2."


def rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    if geom["type"] == "GeometryCollection":
        out = []
        for g in geom["geometries"]:
            out += rings(g)
        return out
    return []


def draw_water(ax, lw=0.5, z=4, min_km2=0.4):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    for f in water["features"]:
        for poly in rings(f["geometry"]):
            r0 = np.array(poly[0])
            a_km2 = abs(0.5 * np.sum(r0[:-1, 0] * r0[1:, 1] - r0[1:, 0] * r0[:-1, 1])) * 111.32 * COS * 110.57
            if "rivers" not in f["properties"]["name"] and a_km2 < min_km2:
                continue
            verts, codes = [], []
            for ring in poly:
                verts += ring
                codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=R["water"], edgecolor=R["waterLine"], lw=lw, zorder=z))


def draw_counties(ax, lw=0.5, city_lw=1.4, z=5, label_city=True):
    for f in counties["features"]:
        city = f["properties"]["geoid"] == "51760"
        for poly in rings(f["geometry"]):
            x, y = zip(*poly[0])
            if city:
                ax.plot(x, y, color=R["ink"], lw=city_lw, ls=(0, (4, 2)), zorder=z + 1)
            else:
                ax.plot(x, y, color=R["faint"], lw=lw, zorder=z)


def draw_shed(ax, lw=2.0, z=7, color=None):
    x, y = zip(*shed["geometry"]["coordinates"][0])
    ax.plot(x, y, color=R["paper"], lw=lw + 2.2, zorder=z, solid_joinstyle="round")
    ax.plot(x, y, color=color or R["shed"], lw=lw, zorder=z + 0.1, solid_joinstyle="round")


def frame(ax, w, e, s, n):
    ax.set_xlim(w, e)
    ax.set_ylim(s, n)
    ax.set_aspect(1 / COS)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)


def smooth(g, sigma=1.1):
    return ndimage.gaussian_filter(g.astype(float), sigma)


def scalebar(ax, x, y, km=10, label=None):
    dlon = km / (111.32 * COS)
    ax.plot([x, x + dlon], [y, y], color=R["ink"], lw=1.6, solid_capstyle="butt", zorder=9)
    for xx in (x, x + dlon):
        ax.plot([xx, xx], [y - 0.004, y + 0.004], color=R["ink"], lw=1.0, zorder=9)
    ax.text(x + dlon / 2, y + 0.007, label or f"{km} km ({km * 0.621:.0f} mi)", ha="center", va="bottom", fontsize=8.5, zorder=9)


def halo(t, w=3):
    import matplotlib.patheffects as pe
    t.set_path_effects([pe.withStroke(linewidth=w, foreground=R["paper"])])
    return t


def gauge_marks(ax, fontsize=8.6, only_in=None, show_values=True):
    placed = []
    for g in rain["gauges"]:
        if g.get("lat") is None:
            continue
        if only_in and not (only_in[0] < g["lon"] < only_in[1] and only_in[2] < g["lat"] < only_in[3]):
            continue
        off = g["kind"] == "official"
        ax.scatter([g["lon"]], [g["lat"]], s=34 if off else 30, marker="o" if off else "D",
                   facecolor=R["ink"] if off else R["paper"], edgecolor=R["ink"], lw=1.1, zorder=10)
        label = f"{g['short']} {g['inches']:.2f}" if show_values else g["short"]
        dx, dy, ha = 0.010, 0.0, "left"
        # nudges where labels collide
        nudge = {"Science Museum": (-0.010, -0.004, "right"), "St. Christopher's": (-0.010, 0.010, "right"),
                 "WWBT": (-0.010, -0.010, "right"), "Sandston": (0.010, -0.008, "left"), "Airport": (0.010, -0.010, "left"),
                 "Math & Sci. Ctr.": (0.008, 0.012, "left"), "Mechanicsville": (0.010, 0.006, "left"), "Winterpock": (0.010, 0.008, "left"), "Midlothian": (-0.010, 0.0, "right"), "Clover Hill": (-0.010, 0.0, "right")}
        if g["short"] in nudge:
            dx, dy, ha = nudge[g["short"]]
        t = ax.text(g["lon"] + dx, g["lat"] + dy, label, fontsize=fontsize, ha=ha, va="center", zorder=11,
                    fontweight=600 if off else 400)
        halo(t)
        placed.append(g["short"])
    return placed


def plan_map(out, rnd):
    tot = smooth(grids["total_corrected"])
    W_, E_, S_, N_ = -77.74, -77.10, 37.30, 37.82
    fig = plt.figure(figsize=(8.6, 8.9), dpi=190)
    ax = fig.add_axes([0.02, 0.085, 0.96, 0.775])
    cmap, norm, cols = cmap_for(TOTAL_LEVELS)
    X, Y = np.meshgrid(LONS, LATS)
    ax.contourf(X, Y, tot, levels=TOTAL_LEVELS, cmap=cmap, norm=norm, zorder=1)
    cs = ax.contour(X, Y, tot, levels=TOTAL_LEVELS[1:-1], colors=[R["paper"]], linewidths=0.6, zorder=2)
    lab = ax.clabel(cs, fmt=lambda v: f"{v:g} in", fontsize=8, inline=True, inline_spacing=4)
    for t in lab:
        t.set_color(R["ink"])
        halo(t, 2.4)
    draw_water(ax)
    draw_counties(ax)
    draw_shed(ax)
    gauge_marks(ax, only_in=(W_, E_, S_, N_))
    # labels
    c = shed["properties"]
    ax.annotate("Shockoe Creek\nwatershed", xy=(-77.455, 37.578), xytext=(-77.50, 37.66), fontsize=9.5, fontweight=600, color=R["shed"],
                ha="center", va="bottom", zorder=12, arrowprops=dict(arrowstyle="-", color=R["shed"], lw=1.0),
                bbox=dict(boxstyle="round,pad=0.2", fc=R["paper"], ec="none", alpha=0.85))
    halo(ax.text(-77.565, 37.515, "RICHMOND", fontsize=9, color=R["ink"], ha="center", zorder=12, fontweight=600))
    halo(ax.text(-77.70, 37.567, "James River", fontsize=8.6, color=R["waterLine"], style="italic", rotation=-12, zorder=12))
    for name, x, y in (("HANOVER", -77.60, 37.76), ("HENRICO", -77.24, 37.47), ("CHESTERFIELD", -77.62, 37.36), ("GOOCHLAND", -77.72, 37.66)):
        halo(ax.text(x, y, name, fontsize=8, color=R["muted"], ha="left", zorder=6))
    # the storm's center: outside this frame, to the southeast
    cp = track["closest_point"]
    ax.annotate("", xy=(E_ - 0.005, S_ + 0.012), xytext=(E_ - 0.075, S_ + 0.075),
                arrowprops=dict(arrowstyle="-|>", color=R["ink"], lw=1.0), zorder=12)
    halo(ax.text(E_ - 0.08, S_ + 0.082, f"Gaston's center passed\nabout {track["closest_to_shockoe_km"]:.0f} km ({track["closest_to_shockoe_km"] * 0.621:.0f} mi) southeast,\n"
                 "about 6:30 p.m. EDT", fontsize=8.2, ha="right", va="bottom", zorder=12))
    scalebar(ax, -77.30, 37.315)
    frame(ax, W_, E_, S_, N_)
    # title and key
    bt = rain["basin_total_in"]
    fig.text(0.03, 0.965, "Tropical Storm Gaston: rain over Richmond, Aug. 30, 2004", fontsize=14, fontweight=600, va="top")
    fig.text(0.03, 0.935, f"Storm total, 8 a.m. Aug. 30 to 2 a.m. Aug. 31 EDT, inches. Over the Shockoe Creek watershed: about "
             f"{bt['radar_corrected']:.0f} in (range {bt['low']:.1f} to {bt['high']:.1f}).", fontsize=9.6, va="top", color=R["ink"])
    kx, ky = 0.03, 0.905
    for i, (lo, hi) in enumerate(zip(TOTAL_LEVELS[:-1], TOTAL_LEVELS[1:])):
        fig.patches.append(plt.Rectangle((kx + i * 0.06, ky - 0.012), 0.058, 0.012, transform=fig.transFigure, facecolor=cols[i], edgecolor="none"))
        fig.text(kx + i * 0.06 + 0.029, ky - 0.016, f"{lo}-{hi}" if hi < 99 else f"{lo}+", fontsize=8, ha="center", va="top")
    fig.text(kx + 7 * 0.06 + 0.008, ky - 0.006, "inches", fontsize=8.5, va="center", color=R["muted"])
    fig.text(0.56, ky - 0.006, "●  official gauge    ◇  unofficial report, place\n     approximate (number: storm total, inches)", fontsize=8.1, va="center")
    footer(fig, SRC_RADAR + " " + SRC_MAP + " The radar sees about 1.5 km detail; bands are smoothed to that. "
           "Top band: the correction north of Ashland rests on one gauge.", y=0.012)
    p = os.path.join(out, f"plan-map-r{rnd}.png")
    fig.savefig(p, dpi=190)
    plt.close(fig)
    return p


def small_multiples(out, rnd):
    H = grids["hourly_corrected"].astype(float)
    hrs = (grids["hour_start_utc"].astype("datetime64[s]") + EDT)
    W_, E_, S_, N_ = -77.62, -77.24, 37.42, 37.70
    cmap, norm, cols = cmap_for(HOURLY_LEVELS, lo=0.1)
    fig, axs = plt.subplots(2, 4, figsize=(10.5, 6.6), dpi=170)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.79, bottom=0.09, wspace=0.03, hspace=0.16)
    X, Y = np.meshgrid(LONS, LATS)
    bh = rain["basin_hourly"]
    for k, ax in enumerate(axs.flat):
        idx = [i for i, h in enumerate(hrs) if h.astype(object).hour == 14 + k][0]
        g = smooth(H[idx], 0.9)
        ax.contourf(X, Y, g, levels=HOURLY_LEVELS, cmap=cmap, norm=norm, zorder=1)
        draw_water(ax, lw=0.3)
        draw_counties(ax, lw=0.3, city_lw=0.9)
        draw_shed(ax, lw=1.3)
        frame(ax, W_, E_, S_, N_)
        h0 = 14 + k
        lab = lambda h: f"{(h - 1) % 12 + 1} {'p.m.' if h >= 12 else 'a.m.'}"  # noqa: E731
        ax.set_title(f"{lab(h0)} to {lab(h0 + 1)}", fontsize=10.5, pad=3)
        v = bh["radar_corrected"][idx]
        halo(ax.text(0.03, 0.04, f"watershed {v:.1f} in", transform=ax.transAxes, fontsize=9, fontweight=600, color=R["shed"], zorder=12))
    fig.text(0.01, 0.975, "Gaston, Aug. 30, 2004: six hours of heavy rain over the Shockoe Creek watershed", fontsize=13.5, fontweight=600, va="top")
    fig.text(0.01, 0.935, "Rain in each hour, EDT, inches. Red outline: the Shockoe Creek watershed; dashed: the city line.",
             fontsize=9.5, va="top")
    kx, ky = 0.01, 0.895
    for i, (lo, hi) in enumerate(zip(HOURLY_LEVELS[:-1], HOURLY_LEVELS[1:])):
        fig.patches.append(plt.Rectangle((kx + i * 0.07, ky - 0.014), 0.067, 0.014, transform=fig.transFigure, facecolor=cols[i], edgecolor="none"))
        fig.text(kx + i * 0.07 + 0.033, ky - 0.018, f"{lo:g}-{hi:g}" if hi < 99 else f"{lo:g}+", fontsize=8, ha="center", va="top")
    fig.text(kx + 7 * 0.07 + 0.005, ky - 0.007, "inches in the hour (under 0.1 left blank)", fontsize=8.5, va="center", color=R["muted"])
    footer(fig, SRC_RADAR + " " + SRC_MAP, y=0.012)
    p = os.path.join(out, f"hourly-r{rnd}.png")
    fig.savefig(p, dpi=170)
    plt.close(fig)
    return p


EVENTS = [
    # (EDT hour as float, short label, source key, confirmed?)
    (15 + 58 / 60, "3:58 first flash-flood warning", "S20", True),
    (16.5, "4:30 flooding under way (Storm Events start; lawsuit says by 4:30)", "S5, S18", True),
    (18.5, "about 6:30 a car afloat in the Bottom", "S23", True),
    (21.25, "9:15 James at Westham peaks, 14,800 cfs: far below flood", "S10, S12", True),
    (22.0, "10:00 Storm Events end time", "S5", True),
]


def hyetograph(out, rnd):
    bh = rain["basin_hourly"]
    t = np.array([np.datetime64(x).astype(object).hour + np.datetime64(x).astype(object).minute / 60 + (24 if np.datetime64(x) >= np.datetime64("2004-08-31") else 0)
                  for x in bh["hour_start_edt"]])
    c, lo, hi = map(np.array, (bh["radar_corrected"], bh["radar_corrected_low"], bh["radar_corrected_high"]))
    keep = (t >= 11) & (t < 24)
    fig = plt.figure(figsize=(8.4, 7.4), dpi=180)
    ax = fig.add_axes([0.09, 0.42, 0.88, 0.41])
    ax.bar(t[keep] + 0.5, c[keep], width=0.86, color=R["rain"], zorder=3, label="watershed average (radar corrected to gauges)")
    ax.errorbar(t[keep] + 0.5, c[keep], yerr=[c[keep] - lo[keep], hi[keep] - c[keep]], fmt="none", ecolor=R["muted"], elinewidth=1.1, capsize=3, zorder=4)
    # airport gauge, hour ending :54 (plotted at its own hour)
    ric = rain["ric_hourly"]
    def hrs_since_midnight(x):
        d = np.datetime64(x).astype(object)
        return d.hour + d.minute / 60 + (24 if d.day == 31 else 0)
    rt = np.array([hrs_since_midnight(x["hour_ending_edt"]) for x in ric]) - 0.5
    rv = np.array([x["inches"] for x in ric])
    m = (rt > 11) & (rt < 24)
    ax.plot(rt[m], rv[m], color=R["pick"], lw=1.8, marker="o", ms=5.5, mec=R["paper"], mew=1.2, zorder=6)
    ax.set_xlim(11, 24)
    ax.set_ylim(0, 3.4)
    ax.set_xticks(range(11, 25))
    ax.set_xticklabels(["11 a.m.", "noon"] + [f"{h - 12}" for h in range(13, 24)] + ["midnight"], fontsize=8.8)
    ax.set_ylabel("inches in the hour")
    ax.yaxis.grid(True, color=R["faint"], lw=0.5)
    ax.set_axisbelow(True)
    # direct labels
    pk = int(np.argmax(c))
    halo(ax.text(20.2, 1.15, f"Shockoe watershed average\npeak {c[pk]:.1f} in, 5 to 6 p.m.\n(bar: best estimate;\nwhisker: range of estimates)",
                 fontsize=8.8, color=R["rain"], fontweight=600, va="bottom", ha="left"))
    k2 = int(np.argmax(rv))
    halo(ax.text(rt[k2] - 0.2, rv[k2] - 0.05, f"Richmond airport gauge\n{rv[k2]:.2f} in, 2:54 to 3:54 p.m.", fontsize=8.8, color=R["pick"], fontweight=600, ha="right", va="center"))
    # Atlas 14 one-hour lines for reference
    a1 = rain["atlas14"]["inches"]["60-min"]
    for ari, ls in (("10", ":"), ("100", "--")):
        ax.axhline(a1[ari], color=R["muted"], lw=0.8, ls=ls, zorder=2)
        ax.text(23.95, a1[ari] + 0.03, f"{ari}-year one-hour rain at a point, {a1[ari]:.2f} in (NOAA Atlas 14)", fontsize=7.8, color=R["muted"], va="bottom", ha="right")
    # cumulative panel
    ax2 = fig.add_axes([0.09, 0.135, 0.88, 0.2], sharex=ax)
    cum = np.concatenate([[0], np.cumsum(c)])
    cl = np.concatenate([[0], np.cumsum(lo)])
    ch = np.concatenate([[0], np.cumsum(hi)])
    tt = np.concatenate([t, [t[-1] + 1]])
    ax2.fill_between(tt, cl, ch, color=R["range"], lw=0, zorder=2)
    ax2.plot(tt, cum, color=R["rain"], lw=2, zorder=3)
    rc = np.concatenate([[0], np.cumsum(rv)])
    ax2.step(np.concatenate([[rt[0] - 0.5], rt + 0.5]), rc, where="post", color=R["pick"], lw=1.4, zorder=3)
    ax2.set_ylim(0, 12.5)
    ax2.set_ylabel("inches so far")
    ax2.yaxis.grid(True, color=R["faint"], lw=0.5)
    ax2.set_axisbelow(True)
    halo(ax2.text(22.1, cum[-1] + 0.25, f"watershed {cum[-1]:.1f} in", fontsize=8.8, color=R["rain"], fontweight=600, va="bottom"))
    halo(ax2.text(23.9, rc[-1] - 0.5, f"airport {rc[-1]:.2f} in (hourly reports;\nday total 6.68)", fontsize=8.8, color=R["pick"], fontweight=600, va="top", ha="right"))
    plt.setp(ax2.get_xticklabels(), fontsize=8.8)
    ax2.set_xlabel("Monday, Aug. 30, 2004, EDT (p.m. hours)")
    # events
    for k, (x, txt, src, _) in enumerate(EVENTS):
        ax.axvline(x, color=R["ink"], lw=0.7, zorder=5)
        ax2.axvline(x, color=R["ink"], lw=0.7, zorder=5)
        ax.text(x, 3.42 + 0.0, f"{k + 1}", fontsize=8.5, ha="center", va="bottom", fontweight=600, clip_on=False)
    fig.text(0.03, 0.975, "Gaston over the Shockoe Creek watershed: inches per hour", fontsize=13.5, fontweight=600, va="top")
    fig.text(0.03, 0.945, "Watershed average from radar corrected to gauges (bars), against the Richmond airport gauge, about 7 mi east (red).",
             fontsize=9.2, va="top")
    ev = "   ".join(f"{k + 1}  {txt} [{src}]" for k, (x, txt, src, _) in enumerate(EVENTS))
    fig.text(0.03, 0.915, ev, fontsize=7.9, va="top", wrap=True)
    footer(fig, SRC_RADAR + " Airport: NCEI Global Hourly 72401013740. Events: news and NCEI Storm Events (keys in the research sources.md); "
           "Storm Events times are labeled EST in the file, so they may be an hour late.", y=0.008)
    p = os.path.join(out, f"hyetograph-r{rnd}.png")
    fig.savefig(p, dpi=180)
    plt.close(fig)
    return p


def bias_check(out, rnd):
    gs = [g for g in rain["gauges"] if g.get("radar_tropical") is not None]
    fig, axs = plt.subplots(1, 3, figsize=(11, 4.6), dpi=160, sharex=True, sharey=True)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.76, bottom=0.2, wspace=0.12)
    for ax, key, title in zip(axs, ("radar_standard", "radar_tropical", "radar_corrected"),
                              ("Standard Z-R (300R^1.4), raw", "Tropical Z-R (250R^1.2), raw", "Tropical, corrected (in-sample)")):
        ax.plot([0, 14], [0, 14], color=R["muted"], lw=0.8, zorder=1)
        for f, ls in ((1.4, ":"),):
            ax.plot([0, 14], [0, 14 * f], color=R["faint"], lw=0.8, ls=ls)
            ax.plot([0, 14], [0, 14 / f], color=R["faint"], lw=0.8, ls=ls)
        for g in gs:
            off = g["kind"] == "official"
            v = g.get(key)
            ax.scatter([v], [g["inches"]], s=34, marker="o" if off else "D", facecolor=R["ink"] if off else R["paper"], edgecolor=R["ink"], lw=1.1, zorder=3)
            if g["short"] in ("Ashland", "Science Museum", "Math & Sci. Ctr.", "Airport", "Mechanicsville"):
                halo(ax.text(v + 0.25, g["inches"], g["short"], fontsize=7.8, va="center"))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 14)
        ax.set_aspect(1)
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel("radar at the gauge, inches")
    axs[0].set_ylabel("gauge, inches")
    axs[1].text(13.6, 13.6 / 1.4 - 0.4, "factor 1.4", fontsize=7.5, color=R["muted"], ha="right", va="top")
    b = rain["bias"]
    fig.text(0.06, 0.965, "Radar against gauges: before and after correction", fontsize=13, fontweight=600, va="top")
    fig.text(0.06, 0.915, "Storm totals, inches. Solid line: radar equals gauge; dotted: off by a factor of 1.4.   ● official gauge   ◇ unofficial report, place approximate.", fontsize=9, va="top")
    fig.text(0.06, 0.875, f"Fair test, each gauge predicted without itself; typical miss: raw tropical x{np.exp(b['leave_one_out_rms_log_error']['raw']):.2f}, "
             f"one factor for the map (x{b['mean_field']['tropical']:.2f}) x{np.exp(b['leave_one_out_rms_log_error']['mean_field']):.2f}, "
             f"local correction (used) x{np.exp(b['leave_one_out_rms_log_error']['local_L5']):.2f}.", fontsize=9, va="top")
    footer(fig, SRC_RADAR, y=0.012)
    p = os.path.join(out, f"radar-vs-gauges-r{rnd}.png")
    fig.savefig(p, dpi=160)
    plt.close(fig)
    return p


def bands_geojson(levels=None, name="bands.geojson"):
    """Storm-total bands as GeoJSON polygons (non-overlapping), from the smoothed corrected grid.

    The grid is smoothed (sigma 1.1 cells, about the radar's own detail), then resampled four
    times finer with a cubic spline so the band edges come out as curves, not 0.55 km steps.
    Rings are sorted into outers and holes by how many other rings hold them (even: outer).
    """
    from shapely.geometry import Polygon, mapping
    from shapely.ops import unary_union
    levels = levels or TOTAL_LEVELS
    tot = ndimage.zoom(smooth(grids["total_corrected"]), 4, order=3)
    la = np.linspace(LATS[0], LATS[-1], tot.shape[0])
    lo = np.linspace(LONS[0], LONS[-1], tot.shape[1])
    X, Y = np.meshgrid(lo, la)
    fig, ax = plt.subplots()
    cs = ax.contourf(X, Y, tot, levels=levels)
    plt.close(fig)
    _, _, cols = cmap_for(levels)
    feats = []
    for k, path in enumerate(cs.get_paths()):
        rings_ = [Polygon(r) for r in path.to_polygons() if len(r) >= 4]
        rings_ = [r.buffer(0) for r in rings_ if r.area > 0]
        depth = [sum(1 for j, o in enumerate(rings_) if j != i and o.area > r.area and o.contains(r.representative_point())) for i, r in enumerate(rings_)]
        polys = []
        for i, (r, d) in enumerate(zip(rings_, depth)):
            if d % 2:
                continue
            inner = [h for h, dh in zip(rings_, depth) if dh == d + 1 and r.contains(h.representative_point())]
            polys.append(r.difference(unary_union(inner)) if inner else r)
        if not polys:
            continue
        geom = unary_union(polys)
        geom = geom.simplify(0.0001, preserve_topology=True)
        if geom.is_empty:
            continue
        lo_, hi_ = levels[k], levels[k + 1]
        feats.append({"type": "Feature", "properties": {"min_in": lo_, "max_in": None if hi_ >= 99 else hi_, "band": k,
                                                         "label": f"{lo_:g}-{hi_:g} in" if hi_ < 99 else f"{lo_:g}+ in",
                                                         "color": "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in cols[k])},
                      "geometry": mapping(geom)})
    gj = {"type": "FeatureCollection", "name": "gaston-2004-storm-total-bands",
          "properties": {"source": "computed: tools/floods/rain/figures.py from data/radar-grids.npz total_corrected, smoothed sigma 1.1 cells, cubic x4",
                         "units": "inches", "window": "2004-08-30 12 UTC to 2004-08-31 06 UTC"},
          "features": feats}
    json.dump(gj, open(os.path.join(DATA, name), "w"))
    return len(feats)


def main():
    out = sys.argv[1]
    rnd = sys.argv[sys.argv.index("--round") + 1] if "--round" in sys.argv else "1"
    os.makedirs(out, exist_ok=True)
    which = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else ["plan", "hourly", "hyeto", "bias", "bands"]
    if "plan" in which:
        print(plan_map(out, rnd))
    if "hourly" in which:
        print(small_multiples(out, rnd))
    if "hyeto" in which:
        print(hyetograph(out, rnd))
    if "bias" in which:
        print(bias_check(out, rnd))
    if "bands" in which:
        print("bands", bands_geojson())
        print("bands, 1 inch", bands_geojson([0, 7, 8, 9, 10, 11, 12, 99], "bands-1in.geojson"))


if __name__ == "__main__":
    main()
