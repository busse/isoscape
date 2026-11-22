"""Test 3 (description): traffic past edge Dollar General stores when they were authorized.

Usage: python3 traffic_then.py <traffic_points.csv> <hpms-dir> <out.csv>

<hpms-dir>/<year>/ holds the unzipped shapefile for that year (one .shp per folder); reading
straight from the zip failed on the 2014-2016 files' DBF.

For each edge Dollar General authorized for SNAP 2011-2017 with a year file available
(virginia<year>.zip from FHWA's HPMS shapefiles, saved as va<year>.zip), the AADT of the
nearest section within 60 m in that year, beside the 2024 count.
"""
import os
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

MATCH_M = 60


def main():
    pts_path, zdir, out = sys.argv[1:4]
    p = pd.read_csv(pts_path)
    d = p[(p.kind == "Dollar General") & (p.auth_year >= 2011) & (p.auth_year <= 2017)]
    rows = []
    for _, r in d.iterrows():
        y = int(r.auth_year)
        # FHWA's 2016 Virginia file is cut off: its DBF declares 4.38 GB and holds 2.15 GB,
        # so no GDAL or pyshp reader opens it. Those stores use the 2015 file, the year before.
        if y == 2016:
            y = 2015
            rec_note = "2015 file (2016 file truncated at source)"
        else:
            rec_note = ""
        folder = f"{zdir}/{y}"
        z = next((f"{folder}/{f}" for f in os.listdir(folder) if f.lower().endswith(".shp")), folder) \
            if os.path.isdir(folder) else folder
        rec = {"town": r.town, "authorized": int(r.auth_year), "count_year": y, "aadt_2024": r.aadt, "A": r.A_lead}
        if not os.path.exists(z):
            rec["note"] = f"no {y} file"
            rows.append(rec)
            continue
        pt = gpd.GeoSeries(gpd.points_from_xy([r.x], [r.y]), crs=32617)
        bb = tuple(pt.buffer(400).to_crs(4326).total_bounds)
        g = gpd.read_file(z, bbox=bb).to_crs(32617)
        col = next(c for c in g.columns if c.upper().startswith("AADT"))
        g = g[pd.to_numeric(g[col], errors="coerce") > 0]
        if g.empty:
            rec["note"] = "no counted section nearby"
            rows.append(rec)
            continue
        dist = g.distance(pt.iloc[0])
        k = dist.idxmin()
        if dist[k] > MATCH_M:
            rec["note"] = f"nearest counted section {dist[k]:.0f} m"
        else:
            rec["aadt_then"] = float(g.loc[k, col])
            rec["note"] = rec_note or f"{col} in {y} file"
        rows.append(rec)
    res = pd.DataFrame(rows)
    if "aadt_then" in res:
        res["change"] = (res["aadt_2024"] / res["aadt_then"] - 1).round(2)
    res.to_csv(out, index=False)
    print(res.to_string())


if __name__ == "__main__":
    main()
