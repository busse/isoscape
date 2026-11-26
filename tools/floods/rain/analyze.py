#!/usr/bin/env python3
"""Gaston 2004 rain: bias-correct the radar to gauges, average it over the Shockoe watershed,
and rank the result against NOAA Atlas 14. Writes rain.json and the derived grids.

    python3 tools/floods/rain/analyze.py WORK OUTDATA

WORK holds what radar.py, watershed.py and the fetches made:
  derived/radar/scans.npz, derived/radar/hourly.npz     (radar.py)
  derived/watershed.geojson                             (watershed.py)
  derived/aorc_raw.npz                                  (AORC v1.1 subset, aorc.py)
  st4/ST4.*.01h.grib, st4/ST4.*.06h.grib, 24h           (Stage IV from the IEM archive)
  ric2004.csv                                           (NCEI Global Hourly, RIC)
  a14_<lat>_<lon>.txt                                   (NOAA Atlas 14 PFDS answers)
Dev tool: numpy, shapely, pygrib.
"""
import csv
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gauges import GAUGES  # noqa: E402

MM = 25.4
EDT = np.timedelta64(-4, "h")
DUR_H = [1, 2, 3, 6, 12]
ARI = [1, 2, 5, 10, 25, 50, 100, 200, 500, 1000]
A14_ROWS = ["5-min", "10-min", "15-min", "30-min", "60-min", "2-hr", "3-hr", "6-hr", "12-hr", "24-hr"]


def rate(dbz, a=250.0, b=1.2):
    d = np.where(np.isfinite(dbz) & (dbz >= 10.0), np.minimum(dbz, 53.0), np.nan)
    r = (10.0 ** (d / 10.0) / a) ** (1.0 / b)
    return np.where(np.isfinite(r), r, 0.0).astype(np.float32)


def decode(u8):
    return np.where(u8 > 0, (u8.astype(np.float32) - 64) / 2, np.nan)


def minute_rates(scans, key, a, b, t0, t1):
    """Rain rate (mm/h) for every minute of [t0, t1), linear in time between scans."""
    times = scans["times"].astype(float)
    dz = decode(scans[key])
    rr = np.stack([rate(x, a, b) for x in dz])
    minutes = np.arange(t0, t1, np.timedelta64(1, "m")).astype("datetime64[s]").astype("int64").astype(float) + 30
    j = np.clip(np.searchsorted(times, minutes) - 1, 0, len(times) - 2)
    w = ((minutes - times[j]) / (times[j + 1] - times[j])).clip(0, 1).astype(np.float32)
    out = np.empty((len(minutes),) + rr.shape[1:], np.float32)
    for m in range(len(minutes)):
        out[m] = rr[j[m]] * (1 - w[m]) + rr[j[m] + 1] * w[m]
    return out


def cell_weights(poly, lats, lons, n=6):
    """Fraction of each grid cell inside the polygon (n x n subsamples per cell)."""
    from shapely import contains_xy
    dla, dlo = lats[1] - lats[0], lons[1] - lons[0]
    W = np.zeros((len(lats), len(lons)))
    minx, miny, maxx, maxy = poly.bounds
    ii = np.where((lats > miny - dla) & (lats < maxy + dla))[0]
    jj = np.where((lons > minx - dlo) & (lons < maxx + dlo))[0]
    off = (np.arange(n) + 0.5) / n - 0.5
    for i in ii:
        for j in jj:
            X, Y = np.meshgrid(lons[j] + off * dlo, lats[i] + off * dla)
            W[i, j] = contains_xy(poly, X.ravel(), Y.ravel()).mean()
    return W


def a14(path):
    s = open(path).read()
    out = {}
    for name in ("quantiles", "upper", "lower"):
        m = re.search(name + r" = (\[\[.*?\]\]);", s)
        out[name] = np.array(eval(m.group(1)), dtype=float)  # the file is a literal list of strings
    return out


def ari_of(depth, row, table):
    """Return period (years) for a depth at one duration row, log-log interpolation.
    Returns (value, flag) with flag '<' below 1 year or '>' above 1,000 years."""
    q = table[row]
    if depth < q[0]:
        return 1.0, "<"
    if depth > q[-1]:
        return 1000.0, ">"
    k = np.searchsorted(q, depth) - 1
    k = max(0, min(k, len(q) - 2))
    f = (np.log(depth) - np.log(q[k])) / (np.log(q[k + 1]) - np.log(q[k]))
    return float(np.exp(np.log(ARI[k]) + f * (np.log(ARI[k + 1]) - np.log(ARI[k])))), ""


def running_max(series_min, hours):
    """Largest sum of a per-minute depth series over any window of `hours`."""
    n = hours * 60
    c = np.concatenate([[0], np.cumsum(series_min)])
    sums = c[n:] - c[:-n]
    k = int(np.argmax(sums))
    return float(sums[k]), k


def main():
    work, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    from shapely.geometry import shape, Point
    t0, t1 = np.datetime64("2004-08-30T12:00"), np.datetime64("2004-08-31T06:00")
    scans = np.load(os.path.join(work, "derived/radar/scans.npz"))
    lats, lons = scans["lats"], scans["lons"]
    ws = json.load(open(os.path.join(work, "derived/watershed.geojson")))["features"][0]
    poly = shape(ws["geometry"])
    W = cell_weights(poly, lats, lons)
    area_km2 = ws["properties"]["area_km2"]

    # radar minute series, both relations, lowest tilt (and 0.9 deg for a check)
    trop = minute_rates(scans, "dbz_lo", 250.0, 1.2, t0, t1) / 60.0  # mm per minute
    std = minute_rates(scans, "dbz_lo", 300.0, 1.4, t0, t1) / 60.0
    trop_hi = minute_rates(scans, "dbz_hi", 250.0, 1.2, t0, t1) / 60.0
    tot = {"tropical": trop.sum(0) / MM, "standard": std.sum(0) / MM, "tropical_0p9": trop_hi.sum(0) / MM}

    def at(grid, la, lo, r=1):
        i = int(np.argmin(abs(lats - la)))
        j = int(np.argmin(abs(lons - lo)))
        return float(grid[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1].mean())

    # gauges: raw radar at each (3 x 3 cells, about 1.6 km square)
    rows = []
    for g in GAUGES:
        if g.get("lat") is None:
            rows.append(dict(g))
            continue
        d = dict(g)
        inside = (lats[0] < g["lat"] < lats[-1]) and (lons[0] < g["lon"] < lons[-1])
        if inside:
            for k, v in tot.items():
                d["radar_" + k] = round(at(v, g["lat"], g["lon"]), 2)
        rows.append(d)

    # 1. mean-field bias: ratio of sums over official gauges whose period matches the window
    use = [r for r in rows if r.get("bias") and "radar_tropical" in r]
    G = np.array([r["inches"] for r in use])
    R = {k: np.array([r["radar_" + k] for r in use]) for k in tot}
    bias = {k: float(G.sum() / R[k].sum()) for k in tot}
    loo = [float((G.sum() - G[i]) / (R["tropical"].sum() - R["tropical"][i])) for i in range(len(use))]

    # 2. local bias: inverse-distance weighting of log(gauge / radar) over every located gauge
    #    with more than 1 inch; weight 1 / (d^2 + L^2), unofficial gauges (approximate places)
    #    at half weight. L = 5 km is the central choice; 3 to 20 km bound it.
    loc = [r for r in rows if "radar_tropical" in r and r["inches"] > 1.0]
    gla = np.array([r["lat"] for r in loc])
    glo = np.array([r["lon"] for r in loc])
    lr = np.log(np.array([r["inches"] / r["radar_tropical"] for r in loc]))
    wk = np.array([1.0 if r["kind"] == "official" else 0.5 for r in loc])
    km = lambda la1, lo1, la2, lo2: np.hypot((la1 - la2) * 110.6, (lo1 - lo2) * 88.2)  # noqa: E731

    def idw(la, lo, L, mask=None):
        m = np.ones(len(loc), bool) if mask is None else mask
        d = km(gla[m][:, None], glo[m][:, None], np.ravel(la)[None, :], np.ravel(lo)[None, :])
        w = wk[m][:, None] / (d**2 + L**2)
        return np.exp((w * lr[m][:, None]).sum(0) / w.sum(0)).reshape(np.shape(la))

    # leave-one-out check of each method at every located gauge (log error, RMS)
    cv = {"raw": [], "mean_field": [], "local_L5": []}
    for i, r in enumerate(loc):
        m = np.arange(len(loc)) != i
        g, rr_ = r["inches"], r["radar_tropical"]
        offm = np.array([x["kind"] == "official" and x.get("bias") for x in loc]) & m
        mf = sum(x["inches"] for x, k in zip(loc, offm) if k) / sum(x["radar_tropical"] for x, k in zip(loc, offm) if k)
        cv["raw"].append(np.log(rr_ / g))
        cv["mean_field"].append(np.log(rr_ * mf / g))
        cv["local_L5"].append(np.log(rr_ * float(idw(r["lat"], r["lon"], 5.0, m)) / g))
    cv_rms = {k: round(float(np.sqrt(np.mean(np.square(v)))), 3) for k, v in cv.items()}

    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    bfield = {L: idw(LA, LO, L) for L in (3.0, 5.0, 10.0, 20.0)}
    corr = tot["tropical"] * bfield[5.0]
    for r in rows:
        if "radar_tropical" in r:
            r["radar_corrected"] = round(at(corr, r["lat"], r["lon"]), 2)
            r["ratio_gauge_to_raw_radar"] = round(r["inches"] / r["radar_tropical"], 2) if r["radar_tropical"] > 0 else None

    # AORC subset (hour ending 13 UTC Aug 30 .. 06 UTC Aug 31)
    a = np.load(os.path.join(work, "derived/aorc_raw.npz"))
    ap = a["apcp"].astype(float)
    ap[ap < 0] = np.nan
    ap = ap * 0.1  # scale_factor 0.1, kg/m2 = mm
    at_ = a["time"].astype("datetime64[s]")
    sel = (at_ > t0) & (at_ <= t1)
    ap, at_ = ap[sel], at_[sel]
    alat, alon = a["lat"], a["lon"]
    Wa = cell_weights(poly, alat, alon, n=8)

    # Stage IV hourly
    import pygrib
    st_files = sorted(glob.glob(os.path.join(work, "st4/ST4.*.01h.grib")))
    st_h, st_t = [], []
    for f in st_files:
        m = pygrib.open(f)[1]
        v = np.ma.filled(m.values, np.nan)
        la4, lo4 = m.latlons()
        st_h.append(v)
        st_t.append(np.datetime64(m.validDate.isoformat()))
    st_h = np.array(st_h)
    box = (la4 > 37.1) & (la4 < 38.0) & (lo4 > -77.9) & (lo4 < -76.9)
    # Stage IV basin weights: share of a fine point sample of the polygon nearest each cell
    pts = []
    minx, miny, maxx, maxy = poly.bounds
    from shapely import contains_xy
    X, Y = np.meshgrid(np.linspace(minx, maxx, 200), np.linspace(miny, maxy, 200))
    inside = contains_xy(poly, X.ravel(), Y.ravel())
    px, py = X.ravel()[inside], Y.ravel()[inside]
    bi = np.where(box.ravel())[0]
    d2 = (la4.ravel()[bi][None, :] - py[:, None]) ** 2 + ((lo4.ravel()[bi][None, :] - px[:, None]) * 0.79) ** 2
    near = bi[np.argmin(d2, axis=1)]
    Ws4 = np.bincount(near, minlength=la4.size).astype(float)
    Ws4 /= Ws4.sum()
    st_basin = np.array([np.nansum(v.ravel() * Ws4) for v in st_h])  # mm per hour
    st6 = {}
    for f in sorted(glob.glob(os.path.join(work, "st4/ST4.*.06h.grib")) + glob.glob(os.path.join(work, "st4/ST4.*.24h.grib"))):
        m = pygrib.open(f)[1]
        v = np.ma.filled(m.values, np.nan)
        st6[os.path.basename(f)] = round(float(np.nansum(v.ravel() * Ws4) / MM), 2)

    # basin averages, minute and hourly (UTC clock hours starting at 12 UTC)
    wsum = W.sum()
    b_raw = (trop * W).sum((1, 2)) / wsum  # mm per minute
    b_trop = (trop * bfield[5.0] * W).sum((1, 2)) / wsum  # corrected, mm per minute
    b_std = (std * W).sum((1, 2)) / wsum
    b_trop_hi = (trop_hi * W).sum((1, 2)) / wsum
    hourly = lambda s: s.reshape(-1, 60).sum(1) / MM  # noqa: E731
    hrs = np.arange(t0, t1, np.timedelta64(1, "h"))
    aorc_basin = np.array([(np.nan_to_num(x) * Wa).sum() / Wa.sum() for x in ap]) / MM
    # the range: every defensible estimate of the basin total
    cand = {
        "radar, no correction": float(b_raw.sum() / MM),
        **{f"radar, local correction L={int(L)} km": float((tot["tropical"] * bfield[L] * W).sum() / wsum) for L in bfield},
        "AORC v1.1": float(aorc_basin.sum()),
        "Stage IV, sum of hourly": float(st_basin.sum() / MM),
        "Stage IV, 24 h analysis to 12 UTC Aug. 31": st6.get("ST4.2004083112.24h.grib"),
    }
    central = float(b_trop.sum() / MM)
    f_lo, f_hi = min(cand.values()) / central, max(cand.values()) / central
    b_c, b_lo, b_hi = 1.0, f_lo, f_hi  # scale factors on the corrected series for the range
    basin = {
        "radar_tropical_raw": hourly(b_raw), "radar_standard_raw": hourly(b_std), "radar_tropical_0p9_raw": hourly(b_trop_hi),
        "radar_corrected": hourly(b_trop), "radar_corrected_low": hourly(b_trop) * b_lo, "radar_corrected_high": hourly(b_trop) * b_hi,
        "radar_mean_field": hourly(b_raw) * bias["tropical"],
        "aorc": aorc_basin, "stage4": st_basin / MM,
    }

    # worst point in the basin and in the frame: largest running n-hour sums of corrected radar
    inb = W > 0.5
    cells = trop[:, inb] * bfield[5.0][inb] / MM  # corrected, inches per minute
    worst = {}
    for hh in DUR_H + [18]:
        n = hh * 60
        c = np.concatenate([np.zeros((1, cells.shape[1])), np.cumsum(cells, 0)])
        s = c[n:] - c[:-n]
        k = np.unravel_index(np.argmax(s), s.shape)
        ii, jj = np.where(inb)
        worst[hh] = {"inches": round(float(s[k]), 2), "start_edt": str((t0 + np.timedelta64(int(k[0]), "m") + EDT)),
                     "lat": float(lats[ii[k[1]]]), "lon": float(lons[jj[k[1]]])}
    basin_dur = {}
    for hh in DUR_H + [18]:
        v, k = running_max(b_trop * b_c / MM, hh)
        lo_, _ = running_max(b_trop * b_lo / MM, hh)
        hi_, _ = running_max(b_trop * b_hi / MM, hh)
        basin_dur[hh] = {"inches": round(v, 2), "low": round(lo_, 2), "high": round(hi_, 2),
                         "start_edt": str(t0 + np.timedelta64(k, "m") + EDT)}
    aorc_dur = {}
    for hh in DUR_H + [18]:
        c = np.concatenate([[0], np.cumsum(aorc_basin)])
        aorc_dur[hh] = round(float((c[hh:] - c[:-hh]).max()), 2)
    st_dur = {}
    for hh in DUR_H + [18]:
        c = np.concatenate([[0], np.cumsum(st_basin / MM)])
        st_dur[hh] = round(float((c[hh:] - c[:-hh]).max()), 2)

    # Atlas 14 at the basin's center
    cen = poly.centroid
    tab = a14(os.path.join(work, "a14_37.5550_-77.4400.txt"))
    rowof = {1: 4, 2: 5, 3: 6, 6: 7, 12: 8}
    rp = {}
    for hh in DUR_H:
        r = rowof[hh]
        e = {}
        for label, depth in (("basin", basin_dur[hh]["inches"]), ("basin_low", basin_dur[hh]["low"]),
                             ("basin_high", basin_dur[hh]["high"]), ("worst_point", worst[hh]["inches"]),
                             ("aorc_basin", aorc_dur[hh]), ("stage4_basin", st_dur[hh])):
            v, flag = ari_of(depth, r, tab["quantiles"])
            # the 90% bounds of the frequency estimate: rarer if the true curve is the lower one
            vl, fl = ari_of(depth, r, tab["upper"])
            vu, fu = ari_of(depth, r, tab["lower"])
            e[label] = {"inches": depth, "ari_years": round(v), "flag": flag,
                        "ari_90pct": [f"{fl}{round(vl)}", f"{fu}{round(vu)}"]}
        rp[f"{hh}h"] = e
    a14_table = {A14_ROWS[i]: dict(zip([str(x) for x in ARI], tab["quantiles"][i].tolist())) for i in range(4, 10)}

    # RIC hourly gauge (Global Hourly AA1, hour ending :54 UTC) and the radar over the same hours
    ric = []
    for row in csv.DictReader(open(os.path.join(work, "ric2004.csv"))):
        d, aa = row["DATE"], row.get("AA1", "")
        if row["REPORT_TYPE"].strip() in ("FM-15", "SY-MT") and aa.startswith("01,") and "2004-08-30T12" <= d <= "2004-08-31T06:59":
            if row["REPORT_TYPE"].strip() == "FM-15" and d[14:16] != "54":
                continue
            if row["REPORT_TYPE"].strip() == "SY-MT" and d != "2004-08-31T00:00:00":
                continue
            ric.append((d, int(aa.split(",")[1]) / 10.0 / MM))
    ric_hourly = [{"hour_ending_utc": d, "hour_ending_edt": str(np.datetime64(d) + EDT), "inches": round(v, 2)} for d, v in ric]
    ric_lat, ric_lon = 37.51154, -77.32338
    i, j = int(np.argmin(abs(lats - ric_lat))), int(np.argmin(abs(lons - ric_lon)))
    ric_radar = trop[:, i - 1:i + 2, j - 1:j + 2].mean((1, 2))
    ric_radar_h = []
    for d, _ in ric:
        e = int((np.datetime64(d) - t0) / np.timedelta64(1, "m"))
        ric_radar_h.append(round(float(ric_radar[max(0, e - 60):e].sum() / MM), 2))

    # grids out (inches, float16 to keep files small)
    hrsum = lambda x: x.reshape(18, 60, *x.shape[1:]).sum(1)  # noqa: E731
    np.savez_compressed(os.path.join(out, "radar-grids.npz"), lats=lats, lons=lons,
                        hour_start_utc=hrs.astype("datetime64[s]").astype("int64"),
                        total_tropical_raw=tot["tropical"].astype(np.float32), total_standard_raw=tot["standard"].astype(np.float32),
                        total_tropical_0p9_raw=tot["tropical_0p9"].astype(np.float32), total_corrected=corr.astype(np.float32),
                        hourly_corrected=(hrsum(trop) / MM * bfield[5.0]).astype(np.float16), bias_field=bfield[5.0].astype(np.float32), basin_weights=W.astype(np.float32))
    np.savez_compressed(os.path.join(out, "aorc-stage4.npz"), aorc_lat=alat, aorc_lon=alon,
                        aorc_hourly_in=(ap / MM).astype(np.float16),
                        aorc_hour_end_utc=at_.astype("int64"),
                        st4_total_in=(np.nansum(st_h, 0)[box] / MM).astype(np.float32), st4_lat=la4[box], st4_lon=lo4[box])

    vol = lambda inches: inches * MM / 1000 * area_km2 * 1e6  # noqa: E731
    tot_c = float(basin["radar_corrected"].sum())
    tot_l = float(basin["radar_corrected_low"].sum())
    tot_h = float(basin["radar_corrected_high"].sum())
    peak = int(np.argmax(basin["radar_corrected"]))
    alt = {}
    altp = os.path.join(work, "derived/watershed-5m.geojson")
    if os.path.exists(altp):
        af = json.load(open(altp))["features"][0]
        Wx = cell_weights(shape(af["geometry"]), lats, lons)
        alt = {"area_km2": af["properties"]["area_km2"], "area_acres": af["properties"]["area_acres"],
               "dem": "isoscape cache data/richmond-streetcars/dem.bin.gz (3DEP, 5 m), east edge -77.3928 (touches the divide)",
               "basin_total_in": round(float((corr * Wx).sum() / Wx.sum()), 2)}
    res = {
        "about": "Every number used in the Gaston rain captions, with its source. 'computed' means "
                 "computed in tools/floods/rain/ (method in each script's docstring). Times EDT = UTC - 4.",
        "window_utc": [str(t0), str(t1)],
        "watershed": {"area_km2": area_km2, "area_acres": ws["properties"]["area_acres"],
                      "source": "computed: tools/floods/rain/watershed.py on 3DEP (see dem_url)",
                      "compare": "City of Richmond, Shockoe Small Area Plan (Aug. 2023), p42: about 8,000-acre watershed (sewershed); https://rva.gov/sites/default/files/2023-08/082023_ShockoePlanFinal_0.pdf, read 2026-11-23",
                      "center": [round(cen.y, 4), round(cen.x, 4)],
                      "dem_url": open(os.path.join(work, "dem/url.txt")).read().strip(),
                      "alternative_5m": alt},
        "radar": {
            "site": "KAKQ Wakefield VA, 36.98405 N 77.007361 W (NCEI HOMR nexrad-stations.txt, read 2026-11-23)",
            "data": "NEXRAD Level II, 268 volumes 11:30 UTC Aug. 30 to 06:30 UTC Aug. 31, https://unidata-nexrad-level2.s3.amazonaws.com/ (manifest-radar.json)",
            "zr": {"tropical": "Z = 250 R^1.2", "standard": "Z = 300 R^1.4"},
            "dbz_floor_cap": [10, 53],
            "raw_max_total_in": {k: round(float(v.max()), 2) for k, v in tot.items()},
            "corrected_max_total_in": round(float(corr.max()), 2),
            "corrected_max_in_basin_in": round(float(corr[W > 0.5].max()), 2),
            "corrected_max_at": [float(lats[np.unravel_index(corr.argmax(), corr.shape)[0]]), float(lons[np.unravel_index(corr.argmax(), corr.shape)[1]])],
        },
        "bias": {"central": "local correction: radar x exp(inverse-distance-weighted mean of log(gauge / raw radar)), weight 1 / (d^2 + L^2) with L = 5 km, unofficial gauges at half weight, every located gauge over 1 inch",
                 "mean_field": {"method": "ratio of the sum of gauge totals to the sum of raw tropical radar at the same points (3 x 3 cells), official gauges whose period covers the window",
                                "gauges_used": [r["name"] for r in use], "tropical": round(bias["tropical"], 3), "standard": round(bias["standard"], 3),
                                "tropical_0p9": round(bias["tropical_0p9"], 3), "leave_one_out": [round(x, 3) for x in loo],
                                "basin_total_in": round(float(basin["radar_mean_field"].sum()), 2)},
                 "local_factor_at_basin_center": {f"L={int(L)} km": round(float(idw(cen.y, cen.x, L)), 3) for L in bfield},
                 "leave_one_out_rms_log_error": cv_rms,
                 "leave_one_out_note": "RMS of ln(estimate / gauge) when each located gauge is predicted from the others; 0.36 is about a factor of 1.4 either way",
                 "basin_total_candidates_in": {k: round(v, 2) for k, v in cand.items()}},
        "gauges": rows,
        "basin_hourly": {"hour_start_edt": [str(h + EDT) for h in hrs], **{k: [round(float(x), 3) for x in v] for k, v in basin.items()}},
        "basin_total_in": {"radar_corrected": round(tot_c, 2), "low": round(tot_l, 2), "high": round(tot_h, 2),
                           "radar_tropical_raw": round(float(basin["radar_tropical_raw"].sum()), 2),
                           "radar_standard_raw": round(float(basin["radar_standard_raw"].sum()), 2),
                           "radar_tropical_0p9_raw": round(float(basin["radar_tropical_0p9_raw"].sum()), 2),
                           "aorc": round(float(aorc_basin.sum()), 2), "stage4_hourly_sum": round(float(st_basin.sum() / MM), 2),
                           "stage4_6h_and_24h_files": st6},
        "basin_peak_hour": {"start_edt": str(hrs[peak] + EDT), "inches": round(float(basin["radar_corrected"][peak]), 2),
                            "low": round(float(basin["radar_corrected_low"][peak]), 2), "high": round(float(basin["radar_corrected_high"][peak]), 2)},
        "basin_volume": {"m3": round(vol(tot_c), -4), "low_m3": round(vol(tot_l), -4), "high_m3": round(vol(tot_h), -4),
                         "million_gallons": round(vol(tot_c) * 264.172 / 1e6), "range_million_gallons": [round(vol(tot_l) * 264.172 / 1e6), round(vol(tot_h) * 264.172 / 1e6)],
                         "method": "computed: basin-average depth x watershed area"},
        "basin_max_n_hour": basin_dur, "aorc_basin_max_n_hour": aorc_dur, "stage4_basin_max_n_hour": st_dur,
        "worst_point_max_n_hour": worst,
        "return_periods": rp,
        "atlas14": {"source": "NOAA Atlas 14 Vol. 2 v3, PFDS partial-duration depths at 37.5550, -77.4400, https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat=37.5550&lon=-77.4400&type=pf&data=depth&units=english&series=pds, read 2026-11-23",
                    "inches": a14_table},
        "ric_hourly": [{**x, "radar_raw_tropical": r} for x, r in zip(ric_hourly, ric_radar_h)],
    }
    json.dump(res, open(os.path.join(out, "rain.json"), "w"), indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("bias", "basin_total_in", "basin_peak_hour", "basin_volume", "basin_max_n_hour", "worst_point_max_n_hour")}, indent=1, default=float))
    print(json.dumps(rp, indent=0))


if __name__ == "__main__":
    main()
