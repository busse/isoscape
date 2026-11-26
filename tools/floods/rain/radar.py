#!/usr/bin/env python3
"""NEXRAD Level II (KAKQ) to gridded rain rate and hourly accumulation, for Gaston 2004.

    python3 tools/floods/rain/radar.py RAWDIR OUTDIR

Dev tool (needs numpy and Py-ART: pip install arm-pyart). isoscape's build does not use it.

Method, in order:
  1. Read each volume with Py-ART. Take reflectivity from the lowest tilt (0.5 degrees,
     the surveillance cut) and, as a check, from the next distinct tilt up (about 0.9 to 1.5
     degrees, whichever the volume coverage pattern gives).
  2. Sample it at the centers of a lat/lon grid (0.005 deg lat by 0.00625 deg lon, about
     0.55 km, over 37.20-37.90 N, 77.80-77.00 W) by nearest ray and nearest gate. The radar's
     own reflectivity gates are 1 km long and about 1 degree wide (1.2 to 1.6 km across at
     70 to 95 km), so the honest resolution is about 1.5 km; the fine grid only avoids adding
     a second resampling error.
  3. dBZ below 10 is set to no rain; dBZ above 53 is capped at 53 (the usual NWS hail cap).
  4. Rain rate from two Z-R relations: tropical Z = 250 R^1.2 and standard (convective)
     Z = 300 R^1.4, with Z in mm^6/m^3 and R in mm/h.
  5. Rate is interpolated linearly in time, minute by minute, between successive scans (scan
     time = the middle of the 0.5-degree sweep), and summed into clock hours (UTC). Gaps over
     20 minutes are reported and filled the same way.

Outputs in OUTDIR: scans.npz (dBZ per scan, uint8 coded as 2*dBZ+64, plus scan times and
grid), hourly.npz (hourly mm for both relations and both tilts), radar-log.json.
"""
import glob
import json
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")
os.environ.setdefault("PYART_QUIET", "1")
import pyart  # noqa: E402

# KAKQ position from NCEI HOMR nexrad-stations.txt (read 2026-11-23): 36.98405 N, 77.007361 W,
# ground 255 ft. The Level II headers of 2004 carry no position (Py-ART reads 0, 0).
RADAR_LAT, RADAR_LON = 36.98405, -77.007361
LAT0, LAT1, DLAT = 37.20, 37.90, 0.005
LON0, LON1, DLON = -77.80, -77.00, 0.00625
DBZ_MIN, DBZ_CAP = 10.0, 53.0
T0 = np.datetime64("2004-08-30T12:00")
T1 = np.datetime64("2004-08-31T06:00")
ZR = {"tropical": (250.0, 1.2), "standard": (300.0, 1.4)}


def grid():
    lats = np.round(np.arange(LAT0, LAT1 + 1e-9, DLAT), 6)
    lons = np.round(np.arange(LON0, LON1 + 1e-9, DLON), 6)
    return lats, lons


def polar(lats, lons):
    """Azimuth (deg) and ground range (m) from the radar to each grid center (WGS84)."""
    import pyproj
    g = pyproj.Geod(ellps="WGS84")
    LO, LA = np.meshgrid(lons, lats)
    az, _, dist = g.inv(np.full(LA.shape, RADAR_LON), np.full(LA.shape, RADAR_LAT), LO, LA)
    return np.mod(az, 360.0), dist


def slant_range(ground, elev_deg, ke_a=4.0 / 3.0 * 6371000.0):
    """Slant range for a ground distance at a tilt, 4/3 earth model (flat enough here)."""
    e = np.radians(elev_deg)
    # ground s = ke_a * asin(r cos e / (ke_a + h)); for these ranges r ~ s / cos e within 0.3%
    return ground / np.cos(e)


def beam_height(slant, elev_deg, ke_a=4.0 / 3.0 * 6371000.0):
    e = np.radians(elev_deg)
    return np.sqrt(slant**2 + ke_a**2 + 2 * slant * ke_a * np.sin(e)) - ke_a


def sample(radar, sweep, az, ground):
    s = radar.get_slice(sweep)
    dz = radar.fields["reflectivity"]["data"][s]
    ray_az = radar.azimuth["data"][s]
    elev = float(np.median(radar.elevation["data"][s]))
    rng = radar.range["data"]
    order = np.argsort(ray_az)
    a = ray_az[order]
    # nearest ray (the area lies at azimuths 300 to 350 degrees, clear of the 0/360 seam)
    i = np.searchsorted(a, az)
    i0 = np.clip(i - 1, 0, len(a) - 1)
    i1 = np.clip(i, 0, len(a) - 1)
    d0 = np.abs((az - a[i0] + 180) % 360 - 180)
    d1 = np.abs((az - a[i1] + 180) % 360 - 180)
    ray = np.where(d0 <= d1, order[i0], order[i1])
    sr = slant_range(ground, elev)
    gate = np.clip(np.round((sr - rng[0]) / (rng[1] - rng[0])).astype(int), 0, len(rng) - 1)
    vals = np.ma.filled(dz[ray, gate].astype(float), np.nan)
    t = radar.time["data"][s]
    tmid = float(np.median(t))
    return vals, elev, tmid


def tilts(radar):
    """Index of the 0.5-degree sweep with reflectivity, and of the next distinct tilt up."""
    out = []
    last = None
    for i in range(radar.nsweeps):
        s = radar.get_slice(i)
        if radar.fields["reflectivity"]["data"][s].count() == 0:
            continue
        el = float(np.median(radar.elevation["data"][s]))
        if last is None or el - last > 0.3:
            out.append(i)
            last = el
        if len(out) == 2:
            break
    return out


def rate(dbz, a, b):
    d = np.where(np.isfinite(dbz) & (dbz >= DBZ_MIN), np.minimum(dbz, DBZ_CAP), np.nan)
    z = 10.0 ** (d / 10.0)
    r = (z / a) ** (1.0 / b)
    return np.where(np.isfinite(r), r, 0.0)


def main():
    raw, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    lats, lons = grid()
    az, ground = polar(lats, lons)
    files = sorted(glob.glob(os.path.join(raw, "**", "KAKQ*.gz"), recursive=True))
    times, dbz_lo, dbz_hi, elevs, log = [], [], [], [], []
    for f in files:
        try:
            r = pyart.io.read_nexrad_archive(f)
        except Exception as e:
            log.append({"file": os.path.basename(f), "error": str(e)[:200]})
            continue
        tl = tilts(r)
        base = np.datetime64(r.time["units"].split("since ")[1].rstrip("Z"))
        v0, e0, t0 = sample(r, tl[0], az, ground)
        v1, e1, _ = sample(r, tl[1], az, ground) if len(tl) > 1 else (np.full_like(v0, np.nan), np.nan, 0)
        t = base + np.timedelta64(int(round(t0)), "s")
        times.append(t)
        dbz_lo.append(v0)
        dbz_hi.append(v1)
        elevs.append((e0, e1))
        log.append({"file": os.path.basename(f), "time": str(t), "tilts": [round(e0, 2), round(float(e1), 2)],
                    "vcp": int(r.metadata.get("vcp_pattern") or 0) if r.metadata.get("vcp_pattern") else None})
        print(os.path.basename(f), t, round(e0, 2), round(float(e1), 2), flush=True)
    times = np.array(times, dtype="datetime64[s]")
    order = np.argsort(times)
    times = times[order]
    lo = np.array(dbz_lo)[order]
    hi = np.array(dbz_hi)[order]

    def code(x):
        return np.where(np.isfinite(x), np.clip(np.round(x * 2 + 64), 1, 255), 0).astype(np.uint8)

    np.savez_compressed(os.path.join(out, "scans.npz"), dbz_lo=code(lo), dbz_hi=code(hi),
                        times=times.astype("int64"), lats=lats, lons=lons,
                        elevs=np.array(elevs)[order], radar=np.array([RADAR_LAT, RADAR_LON]))

    # minute-by-minute linear interpolation of rate, summed by UTC clock hour
    minutes = np.arange(T0, T1, np.timedelta64(1, "m")).astype("datetime64[s]")
    tsec = times.astype("int64").astype(float)
    msec = minutes.astype("int64").astype(float) + 30.0
    j = np.clip(np.searchsorted(tsec, msec) - 1, 0, len(tsec) - 2)
    w = np.clip((msec - tsec[j]) / (tsec[j + 1] - tsec[j]), 0, 1)
    gaps = [(str(times[k]), str(times[k + 1])) for k in range(len(times) - 1)
            if (tsec[k + 1] - tsec[k]) > 1200 and T0 <= times[k] < T1]
    nh = int((T1 - T0) / np.timedelta64(1, "h"))
    hourly = {}
    for tag, dz in (("lo", lo), ("hi", hi)):
        for name, (a, b) in ZR.items():
            rr = np.stack([rate(x, a, b) for x in dz])  # mm/h per scan
            acc = np.zeros((nh,) + rr.shape[1:])
            for m in range(len(minutes)):
                rm = rr[j[m]] * (1 - w[m]) + rr[j[m] + 1] * w[m]
                acc[m // 60] += rm / 60.0
            hourly[f"{name}_{tag}"] = acc.astype(np.float32)
    hours = np.arange(T0, T1, np.timedelta64(1, "h")).astype("datetime64[s]").astype("int64")
    np.savez_compressed(os.path.join(out, "hourly.npz"), hour_start_utc=hours, lats=lats, lons=lons, **hourly)

    # geometry over the grid, for the report
    sr = slant_range(ground, 0.5)
    h = beam_height(sr, 0.5) + 98.0  # antenna about 98 m above sea level (78 m ground + 20 m tower; approximate)
    json.dump({"scans": log, "gaps_over_20_min": gaps, "n_scans": int(len(times)),
               "range_km_min_max": [float(ground.min() / 1000), float(ground.max() / 1000)],
               "beam_center_m_msl_min_max_0p5deg": [float(h.min()), float(h.max())]},
              open(os.path.join(out, "radar-log.json"), "w"), indent=1)
    print("scans", len(times), "gaps", gaps)


if __name__ == "__main__":
    main()
