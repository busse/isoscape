"""Chart of the traffic tests (research stage).

Usage: python3 traffic_chart.py <traffic_tests.csv> <out.png>
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e2e1dc"
YELLOW = "#eda100"
ROWS = [("Dollar General, all edge", "Dollar General, all 34", "s", YELLOW, INK),
        ("Dollar General, towns (follow-up to an exploratory split)", "Dollar General, in towns (18)", "s", YELLOW, INK),
        ("Dollar General, cities (same)", "Dollar General, in cities (16)", "s", YELLOW, INK),
        ("Supermarkets and groceries, edge", "Supermarkets and groceries", "D", SURFACE, INK),
        ("Convenience stores, edge", "Convenience stores", "o", MUTED, MUTED)]


def main():
    src, out = sys.argv[1:3]
    t = pd.read_csv(src).set_index("group")
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=200, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    ys = list(range(len(ROWS)))[::-1]
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    for y, (g, lab, m, fc, ec) in zip(ys, ROWS):
        r = t.loc[g]
        a.plot([r.ci_low, r.ci_high], [y, y], color=INK2, lw=1.5)
        a.plot([r.random_median], [y], marker="|", color=INK, ms=15, mew=2.4, zorder=4)
        a.scatter([r.median_aadt], [y], marker=m, s=85, fc=fc, ec=ec, lw=1.5, zorder=5)
        lo, hi = [float(v) for v in r.top2_ci.split("-")]
        b.plot([lo, hi], [y, y], color=INK2, lw=1.5)
        b.plot([r.random_on_top2], [y], marker="|", color=INK, ms=15, mew=2.4, zorder=4)
        b.scatter([r.on_top2_crossing], [y], marker=m, s=85, fc=fc, ec=ec, lw=1.5, zorder=5)
        b.text(0.99, y, f"{int(r.top2_k)} of {int(r.n)}", ha="right", va="center", fontsize=7.8, color=INK2)
    a.set_xlim(0, 16000)
    a.set_xticks([0, 4000, 8000, 12000, 16000])
    a.set_xticklabels(["0", "4,000", "8,000", "12,000", "16,000"])
    a.set_yticks(ys)
    a.set_yticklabels([f"{r[1]}\n{int(t.loc[r[0]].with_count)} with a traffic count" for r in ROWS], fontsize=8.5)
    a.set_title("Median vehicles a day on the road past the site (2024)", loc="left", fontsize=10, pad=8)
    b.set_xlim(-0.02, 1.0)
    b.set_xticks([0, 0.25, 0.5, 0.75, 1])
    b.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    b.set_title("On one of the two busiest roads into town", loc="left", fontsize=10, pad=8)
    fig.suptitle("Edge Dollar General stores sit on roads twice as busy as other edge sites; in towns, mostly on a top-two road in",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    fig.text(0.01, 0.012, "Black tick: random main-road points in the same edge band (score A 1 to 2) of the same places. Lines: 95% "
             "intervals (bootstrap of the median, left; Wilson, right). Roads into town: HPMS sections crossing the built-up edge,\n"
             "ranked by AADT where they cross. Traffic: FHWA HPMS 2024, public domain. Tests written before the counts were "
             "fetched; the town and city split follows up an exploratory finding. Research draft made with Claude.",
             fontsize=6.8, color=INK2)
    fig.subplots_adjust(left=0.2, right=0.985, top=0.84, bottom=0.17, wspace=0.08)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
