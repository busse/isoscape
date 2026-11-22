"""Pooled chart for the free-standing towns of the editorial draw (research stage).

Usage: python3 pool_chart.py <pool-dir> <out.png>

Left: share of stores beyond the town (score A above 2), with 95% intervals.
Right: among stores within A 3, share in the fringe (A 1 to 2), against random main-road points.
"""
import math
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e2e1dc"
YELLOW = "#eda100"
KINDS = ["Dollar General", "Family Dollar", "Dollar Tree", "grocery", "pharmacy", "convenience"]
LABEL = {"grocery": "Supermarket or grocery", "pharmacy": "Pharmacy chain", "convenience": "Convenience store"}
STYLE = {"Dollar General": ("s", YELLOW, INK), "Family Dollar": ("o", YELLOW, INK), "Dollar Tree": ("^", YELLOW, INK),
         "grocery": ("D", SURFACE, INK), "pharmacy": ("P", INK2, INK2), "convenience": ("o", MUTED, MUTED)}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main():
    pool, out = sys.argv[1:3]
    cls = pd.read_csv(f"{pool}/classes_free_standing.csv", index_col=0)
    test = pd.read_csv(f"{pool}/edge_test.csv").set_index("kind")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=200, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    ys = list(range(len(KINDS)))[::-1]
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.set_xlim(-0.02, 1.0)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    a = axes[0]
    for y, k in zip(ys, KINDS):
        row = cls.loc[k]
        n = int(row.sum())
        b = int(row["another place"] + row["between places"])
        lo, hi = wilson(b, n)
        m, fc, ec = STYLE[k]
        a.plot([lo, hi], [y, y], color=INK2, lw=1.4)
        a.scatter([b / n], [y], marker=m, s=80, fc=fc, ec=ec, lw=1.4, zorder=3)
        a.text(0.99, y, f"{b} of {n}", va="center", ha="right", fontsize=8, color=INK2)
    a.set_yticks(ys)
    a.set_yticklabels([LABEL.get(k, k) for k in KINDS])
    a.set_title("Beyond the town: score A above 2", loc="left", fontsize=10.5, pad=16)
    b_ = axes[1]
    for y, k in zip(ys, KINDS):
        r = test.loc[k]
        m, fc, ec = STYLE[k]
        b_.plot([r.ci95_low, r.ci95_high], [y, y], color=INK2, lw=1.4)
        b_.plot([r.random_road_share], [y], marker="|", color=INK, ms=14, mew=2.2)
        b_.scatter([r.share], [y], marker=m, s=80, fc=fc, ec=ec, lw=1.4, zorder=3)
        b_.text(0.99, y, f"{int(r.in_fringe)} of {int(r.stores_A_le_3)}", va="center", ha="right", fontsize=8, color=INK2)
    b_.set_title("At the edge: of stores within A 3, share at A 1 to 2", loc="left", fontsize=10.5, pad=16)
    b_.text(0, 1.005, "Black tick: random points on main roads in the same towns", transform=b_.transAxes,
            fontsize=7.5, color=INK2, va="bottom")
    fig.suptitle("16 free-standing towns: Dollar General is often out of town, and no more often at its edge than road frontage",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, 0.01, "Score A: distance from the town's population-weighted center over the distance to its built-up edge "
             "on that bearing. Lines: 95% intervals (Wilson). Stores: USDA SNAP, authorized as of 2025, within 8 km of each "
             "town's limits.\nLeft out: Troutville, Vinton, Dumfries and Fredericksburg, which are joined to larger urban areas. "
             "Research draft made with Claude.", fontsize=7, color=INK2)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.86, bottom=0.17, wspace=0.12)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
