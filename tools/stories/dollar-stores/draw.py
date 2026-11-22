"""Seeded draw of the editorial grid's towns.

Usage: python3 draw.py <sub-est2024_51.csv> <regions.json> <out.csv>

Pool: every incorporated town and independent city in Virginia under 50,000 people
(Census Vintage 2024 estimates, July 1, 2024). A town in two counties is placed by the county
holding most of its people. Cells: region x size band. One draw per cell with SEED; cells are
sorted by name first so the draw repeats exactly. An empty cell is filled, after all other
cells are drawn, by one more draw from the same size band statewide, among places not drawn.
"""
import json
import sys

import numpy as np
import pandas as pd

SEED = 20261121
BANDS = [(0, 1000, "under 1,000"), (1000, 2500, "1,000-2,499"), (2500, 10000, "2,500-9,999"),
         (10000, 50000, "10,000-49,999")]


def main():
    est, regions_path, out = sys.argv[1:4]
    d = pd.read_csv(est, encoding="latin-1", dtype=str)
    d["pop"] = d["POPESTIMATE2024"].astype(int)
    counties = d[d.SUMLEV == "050"].set_index("COUNTY")["NAME"]
    reg = json.load(open(regions_path))["regions"]
    region_of = {loc: r for r, pdcs in reg.items() for locs in pdcs.values() for loc in locs}
    places = d[d.SUMLEV == "162"][["PLACE", "NAME", "pop"]]
    parts = d[d.SUMLEV == "157"].sort_values("pop", ascending=False).drop_duplicates("PLACE")
    places = places.merge(parts[["PLACE", "COUNTY"]], on="PLACE", how="left")
    places["county"] = places["COUNTY"].map(counties)
    # an independent city is its own county-equivalent
    is_city = places["NAME"].str.endswith(" city")
    places.loc[is_city, "county"] = places.loc[is_city, "NAME"]
    places["region"] = places["county"].map(region_of)
    missing = places[places["region"].isna()]
    assert missing.empty, missing
    places = places[places["pop"] < 50000].copy()
    places["band"] = pd.cut(places["pop"], [b[0] for b in BANDS] + [50000], right=False,
                            labels=[b[2] for b in BANDS])
    rng = np.random.default_rng(SEED)
    picks = []
    counts = places.pivot_table(index="region", columns="band", values="NAME", aggfunc="count", observed=False)
    print(counts.fillna(0).astype(int).to_string())
    for r in reg:
        for _, _, label in BANDS:
            cell = places[(places.region == r) & (places.band == label)].sort_values("NAME")
            if cell.empty:
                picks.append({"region": r, "band": label, "NAME": None, "pop": None, "county": None, "cell_size": 0})
                continue
            row = cell.iloc[rng.integers(len(cell))]
            picks.append({"region": r, "band": label, "NAME": row.NAME, "pop": row["pop"],
                          "county": row.county, "cell_size": len(cell)})
    for pk in picks:
        if pk["NAME"] is None:
            taken = {x["NAME"] for x in picks}
            cell = places[(places.band == pk["band"]) & ~places.NAME.isin(taken)].sort_values("NAME")
            row = cell.iloc[rng.integers(len(cell))]
            pk.update({"NAME": row.NAME, "pop": row["pop"], "county": row.county,
                       "cell_size": len(cell), "note": f"empty cell; drawn statewide from {row.region}"})
    p = pd.DataFrame(picks)
    p.to_csv(out, index=False)
    places.to_csv(out.replace(".csv", "-pool.csv"), index=False)
    print(p.to_string())


if __name__ == "__main__":
    main()
