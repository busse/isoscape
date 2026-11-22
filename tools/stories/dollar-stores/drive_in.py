"""The driver's view (exploratory, written after the frozen tests, labeled as such).

Usage: python3 drive_in.py <points.csv.gz> [...] --out <dir>

For each place and each road that crosses its built-up edge (confirm.py's crossing roads), the
"gateway" stores are the SNAP stores matched to that road (nearest HPMS section within 60 m)
with score A from 0.75 to 2: the stretch a driver covers from twice the edge distance out to
just inside the edge. Driving in, the first store passed is the one with the highest A.

Reports, by unit and set: how often the first store on a road in is a Dollar General (or any of
the three chains), against the chains' share of all gateway stores on those roads; and how
often a road in has a Dollar General anywhere on that stretch.
"""
import sys

import numpy as np
import pandas as pd

CHAINS = ["Dollar General", "Family Dollar", "Dollar Tree"]


def main():
    args = sys.argv[1:]
    out = args[args.index("--out") + 1]
    files = [a for a in args if a.endswith(".csv.gz")]
    p = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
    s = p[p["is_store"] == True].copy()  # noqa: E712
    s = s.sort_values("A_lead").drop_duplicates("id")
    s["incorporated"] = (s["LSAD"].astype(str) != "57") & (s["FUNCSTAT"] == "A")
    s["unit"] = np.where(s["joined"], "joined", np.where(~s["incorporated"], "CDP",
                         np.where(s["pop"] < 25000, "small", "large")))
    g = s[(s["A_lead"] > 0.75) & (s["A_lead"] <= 2) & s["rank"].notna()].copy()
    g["chain"] = g["kind"].isin(CHAINS)
    rows = []
    for (st, unit), d in g.groupby(["set", "unit"]):
        first = d.sort_values("A_lead", ascending=False).groupby(["geoid", "road"]).head(1)
        roads = d.groupby(["geoid", "road"])
        rows.append({"set": st, "unit": unit, "roads_in_with_a_store": len(first),
                     "first_is_DG": round((first["kind"] == "Dollar General").mean(), 3),
                     "first_is_chain": round(first["chain"].mean(), 3),
                     "DG_share_of_gateway_stores": round((d["kind"] == "Dollar General").mean(), 3),
                     "chain_share_of_gateway_stores": round(d["chain"].mean(), 3),
                     "roads_with_any_DG": round(roads.apply(lambda x: (x["kind"] == "Dollar General").any()).mean(), 3),
                     "first_is_convenience": round((first["kind"] == "convenience").mean(), 3),
                     "first_is_grocery": round((first["kind"] == "grocery").mean(), 3)})
    r = pd.DataFrame(rows)
    r.to_csv(f"{out}/drive_in.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.to_string())


if __name__ == "__main__":
    main()
