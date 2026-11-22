"""Step 14: which towns get Dollar Generals (hypotheses in casestudy/2026-11-22-14-snap-towns/hypotheses.md).

Usage: python3 snap_towns.py <conf_all-dir> <acs-dir> <out-dir>

<acs-dir> holds b22010-place-7states.dat, b22010-bg-7states.dat and cb_2024_<fips>_bg_500k.zip.
Writes towns.csv (one row per place), towns_tests.csv and towns_thirds.csv. Made with Claude.
"""
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from confirm import SEED, SMALL  # noqa: E402
from snap_test import circle_share, load_bg  # noqa: E402

KINDS = {"Dollar General": "dg", "grocery": "grocery", "convenience": "conv"}


def place_acs(acs):
    t = pd.read_csv(f"{acs}/b22010-place-7states.dat", sep="|", header=None, dtype=str).iloc[:, :5]
    t.columns = ["GEO_ID", "hh", "hh_m", "snap", "snap_m"]
    t["geoid"] = t.GEO_ID.str[9:].astype(int)
    for c in ("hh", "snap"):
        t[c] = pd.to_numeric(t[c], errors="coerce")
    return t[["geoid", "hh", "snap"]]


def fit(d, y, hh, share, B=2000):
    """Poisson rate ratio for +10 points of SNAP share, with log households and state; bootstrap over places."""
    def one(x):
        X = pd.get_dummies(x["state"], drop_first=True, dtype=float)
        X["share10"] = x[share] * 10
        X["loghh"] = np.log(x[hh])
        X = sm.add_constant(X)
        r = sm.GLM(x[y], X, family=sm.families.Poisson()).fit()
        return float(np.exp(r.params["share10"]))
    est = one(d)
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(B):
        x = d.iloc[rng.integers(0, len(d), len(d))]
        if x["state"].nunique() < d["state"].nunique():
            continue
        try:
            bs.append(one(x))
        except Exception:  # a resample with a degenerate fit is skipped
            pass
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, len(bs)


def main():
    conf, acs, out = sys.argv[1:4]
    cols = ["is_store", "id", "kind", "x", "y", "A_lead", "geoid", "state", "set", "pop", "joined", "LSAD",
            "FUNCSTAT", "center_x", "center_y"]
    p = pd.read_csv(f"{conf}/points.csv.gz", usecols=cols, low_memory=False)
    p["small"] = (p.LSAD.astype(str) != "57") & (p.FUNCSTAT == "A") & ~p.joined.astype(bool) & (p["pop"] < SMALL)
    places = p.groupby("geoid").agg(state=("state", "first"), set=("set", "first"), small=("small", "first"),
                                    pop=("pop", "first"), center_x=("center_x", "first"),
                                    center_y=("center_y", "first")).reset_index()
    st = p[p.is_store].sort_values(["A_lead", "pop", "geoid"], ascending=[True, False, True],
                                   kind="mergesort").drop_duplicates("id")
    st = st[st.A_lead <= 2]
    for k, col in KINDS.items():
        places[col] = places.geoid.map(st[st.kind == k].groupby("geoid").size()).fillna(0).astype(int)
    places = places[places.small & places["set"].isin(["B", "discovery", "A"])]
    places = places.merge(place_acs(acs), on="geoid", how="left")
    places["share"] = places.snap / places.hh
    bg = load_bg(acs)
    c = places.rename(columns={"center_x": "x", "center_y": "y"})[["x", "y"]]
    ok = c.notna().all(axis=1)
    s5, h5 = np.full(len(c), np.nan), np.full(len(c), np.nan)
    s5[ok.values], h5[ok.values] = circle_share(c[ok], bg, 5000)
    places["share5"], places["hh5"] = s5, h5
    places.to_csv(f"{out}/towns.csv", index=False)

    rows = []
    prim = places[(places["set"] == "B") & (places.hh > 0) & places.share.notna()]
    sens = places[(places["set"] == "B") & (places.hh5 > 0) & places.share5.notna()]
    va = places[(places.state == "VA") & (places.hh > 0) & places.share.notna()]
    print("places: six states", len(prim), "with a Dollar General", int((prim.dg > 0).sum()), "| Virginia", len(va))
    for test, d, y, hh, sh in (("T1", prim, "dg", "hh", "share"), ("T2", sens, "dg", "hh5", "share5"),
                               ("T3 grocery", prim, "grocery", "hh", "share"), ("T3 convenience", prim, "conv", "hh", "share"),
                               ("Virginia (exploratory)", va.assign(state="VA"), "dg", "hh", "share")):
        est, lo, hi, n_ok = fit(d, y, hh, sh)
        v = "holds" if lo > 1 else "against" if hi < 1 else "cannot tell"
        if test.startswith("Virginia"):
            v = "exploratory"
        rows.append({"test": test, "places": len(d), "stores": int(d[y].sum()), "rate_ratio_per_10pts": round(est, 3),
                     "low": round(lo, 3), "high": round(hi, 3), "resamples": n_ok, "verdict": v})
    t = pd.DataFrame(rows)
    t.to_csv(f"{out}/towns_tests.csv", index=False)
    print(t.to_string())

    prim = prim.copy()
    prim["third"] = pd.qcut(prim.share, 3, labels=["lowest third", "middle third", "highest third"])
    th = prim.groupby("third", observed=True).agg(places=("geoid", "size"), snap_share_lo=("share", "min"),
                                                  snap_share_hi=("share", "max"), households=("hh", "sum"),
                                                  dg=("dg", "sum"), grocery=("grocery", "sum"),
                                                  with_dg=("dg", lambda v: (v > 0).mean()))
    for k in ("dg", "grocery"):
        th[f"{k}_per_1000_hh"] = th[k] / th.households * 1000
    th = th.round(3)
    th.to_csv(f"{out}/towns_thirds.csv")
    print(th.to_string())


if __name__ == "__main__":
    main()
