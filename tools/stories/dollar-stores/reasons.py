"""Summarize the reasons measured by features.py, as stated in hypotheses.md.

Usage: python3 reasons.py <edge_points.csv> <stores.csv> <out.csv>
"""
import math
import sys

import pandas as pd

CHAINS = ["Dollar General", "Family Dollar", "Dollar Tree"]


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def verdict(lo, hi, ref):
    if ref < lo:
        return "supported"
    if ref > hi:
        return "contradicted"
    return "cannot tell"


def main():
    pts_path, stores_path, out = sys.argv[1:4]
    p = pd.read_csv(pts_path)
    p["chain"] = p["kind"].isin(CHAINS)
    p["other_side"] = p["angle_to_supermarket"] > 90
    groups = {"Three chains": p[p.chain], "Dollar General": p[p.kind == "Dollar General"],
              "Random road points": p[p.kind == "random"], "Supermarkets and groceries": p[p.group == "grocery"],
              "Convenience stores": p[p.group == "convenience"]}
    tests = [("1 Road into town", "on_approach_road"), ("2 Crossroads", "near_junction"),
             ("3 Outside town limits", "outside_limits"), ("4 Built on open land after 2001", "greenfield"),
             ("6 Other side of town from the supermarket", "other_side")]
    rows = []
    for label, col in tests:
        ref_g = groups["Random road points"][col].dropna()
        ref = ref_g.mean()
        for g, df in groups.items():
            v = df[col].dropna().astype(bool)
            k, n = int(v.sum()), len(v)
            lo, hi = wilson(k, n)
            rows.append({"reason": label, "group": g, "k": k, "n": n, "share": round(k / n, 3) if n else None,
                         "ci_low": round(lo, 3), "ci_high": round(hi, 3),
                         "verdict_vs_random": verdict(lo, hi, ref) if g in ("Three chains", "Dollar General") else ""})
    # 5: share of people within 5 km by road living outside the built-up area (a mean, with a simple interval)
    for g, df in groups.items():
        v = df["share_outside_builtup"].dropna()
        se = v.std(ddof=1) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
        rows.append({"reason": "5 Reaching people outside town (mean share)", "group": g, "k": None, "n": len(v),
                     "share": round(v.mean(), 3), "ci_low": round(v.mean() - 1.96 * se, 3),
                     "ci_high": round(v.mean() + 1.96 * se, 3), "verdict_vs_random": ""})
    ref = groups["Random road points"]["share_outside_builtup"].dropna().mean()
    for r in rows:
        if r["reason"].startswith("5") and r["group"] in ("Three chains", "Dollar General"):
            r["verdict_vs_random"] = verdict(r["ci_low"], r["ci_high"], ref)
    # 7: newer than in-town Dollar General
    st = pd.read_csv(stores_path)
    st = st[(~st["metro"]) & (st["kind"] == "Dollar General")]
    for g, df in [("Dollar General, edge", st[(st.A_lead > 1) & (st.A_lead <= 2)]),
                  ("Dollar General, in town", st[st.A_lead <= 1]),
                  ("Dollar General, between places", st[st["class"] == "between places"])]:
        k, n = int((df.auth_year > 2005).sum()), len(df)
        lo, hi = wilson(k, n)
        rows.append({"reason": "7 Authorized after 2005", "group": g, "k": k, "n": n, "share": round(k / n, 3),
                     "ci_low": round(lo, 3), "ci_high": round(hi, 3), "verdict_vs_random": ""})
    out_df = pd.DataFrame(rows)
    out_df.to_csv(out, index=False)
    pd.set_option("display.width", 200)
    print(out_df.to_string())


if __name__ == "__main__":
    main()
