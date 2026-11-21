"""Pool the scored towns: classes, the edge test, and per-town tables.

Usage: python3 pool.py <raw-dir> <work-dir> <out-dir> <town-slug> [...]

Classes, on score A against the lead edge (homes or non-road paved land):
  in town        A <= 1
  fringe         1 < A <= 2
  another place  A > 2 and inside the limits of another Census place (town, city or CDP)
  between places A > 2 and inside no Census place
A store seen from two towns' windows is counted once, with the town that gives it the lowest A.
Towns joined to a larger urban area (meta in_larger_urban_area) are reported apart and left out
of the edge test.

Edge test: among stores scoring A <= 3, the share in the fringe (1 < A <= 2), against the same
share for random points on main roads (null.csv), with each town's random points weighted to
the number of stores of that kind the town contributes.
"""
import json
import math
import os
import sys

import geopandas as gpd
import pandas as pd

KINDS = ["Dollar General", "Family Dollar", "Dollar Tree", "grocery", "pharmacy", "convenience"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main():
    raw, work, out, slugs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    places = gpd.read_file(f"zip://{raw}/tl_2024_51_place.zip").to_crs(32617)[["GEOID", "NAMELSAD", "geometry"]]
    rows, nulls, metas = [], [], {}
    for t in slugs:
        m = json.load(open(f"{work}/{t}/meta.json"))
        own = gpd.read_file(f"{work}/{t}/place.gpkg")["GEOID"].iloc[0]
        s = pd.read_csv(f"{work}/{t}/scores.csv").assign(town=t)
        g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.x, s.y), crs=32617)
        j = gpd.sjoin(g, places[places.GEOID != own], how="left", predicate="within")
        j = j[~j.index.duplicated()]
        s["other_place"] = j["NAMELSAD"].values
        rows.append(s)
        nulls.append(pd.read_csv(f"{work}/{t}/null.csv").assign(town=t))
        metas[t] = m
    s = pd.concat(rows, ignore_index=True)
    s["metro"] = s["town"].map(lambda t: metas[t]["in_larger_urban_area"])
    s = s.sort_values("A_lead").drop_duplicates("id")  # each store once, at its lowest A

    def cls(r):
        if r.A_lead <= 1:
            return "in town"
        if r.A_lead <= 2:
            return "fringe"
        return "another place" if isinstance(r.other_place, str) else "between places"
    s["class"] = s.apply(cls, axis=1)
    s.to_csv(f"{out}/stores.csv", index=False)
    free = s[~s["metro"]]
    order = ["in town", "fringe", "another place", "between places"]
    tab = pd.crosstab(free["kind"], free["class"]).reindex(index=KINDS, columns=order, fill_value=0)
    tab.to_csv(f"{out}/classes_free_standing.csv")
    tab_m = pd.crosstab(s[s["metro"]]["kind"], s[s["metro"]]["class"]).reindex(index=KINDS, columns=order, fill_value=0)
    tab_m.to_csv(f"{out}/classes_joined_towns.csv")

    nl = pd.concat(nulls, ignore_index=True)
    nl = nl[nl["town"].map(lambda t: not metas[t]["in_larger_urban_area"])]
    test = []
    for k in KINDS:
        sk = free[(free["kind"] == k) & (free["A_lead"] <= 3)]
        n, f = len(sk), int(((sk["A_lead"] > 1) & (sk["A_lead"] <= 2)).sum())
        w = sk["town"].value_counts()
        num = den = 0.0
        for t, c in w.items():
            q = nl[(nl["town"] == t) & (nl["A_lead"] <= 3)]
            if len(q):
                num += c * ((q["A_lead"] > 1) & (q["A_lead"] <= 2)).mean()
                den += c
        lo, hi = wilson(f, n)
        test.append({"kind": k, "stores_A_le_3": n, "in_fringe": f, "share": round(f / n, 3) if n else None,
                     "ci95_low": round(lo, 3), "ci95_high": round(hi, 3),
                     "random_road_share": round(num / den, 3) if den else None})
    test = pd.DataFrame(test)
    test.to_csv(f"{out}/edge_test.csv", index=False)
    per = []
    for t in slugs:
        st = s[s["town"] == t]
        per.append({"town": t, "people_2020": metas[t]["pop_in_limits"], "joined": metas[t]["in_larger_urban_area"],
                    "edge_rule": metas[t]["lead_rule"], "builtup_km2": metas[t]["builtup_km2"]["lead"],
                    **{f"DG_{c}": int(((st.kind == "Dollar General") & (st["class"] == c)).sum()) for c in order},
                    "FD_DT": int(st.kind.isin(["Family Dollar", "Dollar Tree"]).sum()),
                    "grocery": int((st.kind == "grocery").sum())})
    pd.DataFrame(per).to_csv(f"{out}/towns.csv", index=False)
    pd.set_option("display.width", 220)
    print(tab.to_string())
    print(tab_m.to_string())
    print(test.to_string())
    print(pd.DataFrame(per).to_string())


if __name__ == "__main__":
    main()
