"""Chart of the stated reasons for edge stores (research stage).

Usage: python3 reasons_chart.py <reasons.csv> <out.png>
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e2e1dc"
YELLOW = "#eda100"
ORDER = ["2 Crossroads", "1 Road into town", "3 Outside town limits", "4 Built on open land after 2001",
         "5 Reaching people outside town (mean share)", "6 Other side of town from the supermarket"]
LABEL = {"2 Crossroads": "Within 250 m of a junction of\ntwo US or state routes",
         "1 Road into town": "On a US or state route that\ncrosses the town's edge",
         "3 Outside town limits": "Outside the town's legal limits",
         "4 Built on open land after 2001": "Site under 10% paved in 2001,\n20%+ in 2021",
         "5 Reaching people outside town (mean share)": "Of people within 5 km by road,\nshare living outside town",
         "6 Other side of town from the supermarket": "Opposite side of town from\nthe nearest supermarket"}
VERDICT = {"supported": "more often than random", "contradicted": "less often than random",
           "cannot tell": "can't tell from random"}


def main():
    src, out = sys.argv[1:3]
    r = pd.read_csv(src)
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5.6), dpi=200, gridspec_kw={"width_ratios": [2.3, 1]})
    fig.patch.set_facecolor(SURFACE)
    for a in (ax, ax2):
        a.set_facecolor(SURFACE)
        a.grid(axis="x", color=GRID, lw=0.6)
        a.set_axisbelow(True)
        for sp in ("top", "right"):
            sp_ = a.spines[sp]
            sp_.set_visible(False)
        a.set_xlim(-0.02, 1.0)
        a.set_xticks([0, 0.25, 0.5, 0.75, 1])
        a.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ys = list(range(len(ORDER)))[::-1]
    for y, reason in zip(ys, ORDER):
        q = r[r.reason == reason].set_index("group")
        dg = q.loc["Dollar General"]
        rnd = q.loc["Random road points"]
        gro = q.loc["Supermarkets and groceries"]
        ax.plot([dg.ci_low, dg.ci_high], [y, y], color=INK2, lw=1.5)
        ax.plot([rnd.share], [y], marker="|", color=INK, ms=15, mew=2.4, zorder=4)
        ax.scatter([gro.share], [y - 0.22], marker="D", s=26, fc=SURFACE, ec=INK, lw=1.0, zorder=3)
        ax.scatter([dg.share], [y], marker="s", s=85, fc=YELLOW, ec=INK, lw=1.5, zorder=5)
        word = VERDICT[dg.verdict_vs_random]
        if dg.verdict_vs_random == "supported" and dg.ci_low - rnd.share < 0.02:
            word += ", just"
        ax.text(1.0, y + 0.18, word, ha="right", fontsize=7.8, color=INK2)
    ax.set_yticks(ys)
    ax.set_yticklabels([LABEL[o] for o in ORDER], fontsize=8.5)
    ax.set_ylim(-0.7, len(ORDER) - 0.4)
    ax.set_title("The 34 Dollar General stores at a town's edge, against random sites in the same band",
                 loc="left", fontsize=10, pad=8)
    q = r[r.reason == "7 Authorized after 2005"].set_index("group")
    rows = ["Dollar General, in town", "Dollar General, edge", "Dollar General, between places"]
    names = ["In town", "At the edge", "Between places"]
    for y, g in zip([2, 1, 0], rows):
        v = q.loc[g]
        ax2.plot([v.ci_low, v.ci_high], [y, y], color=INK2, lw=1.5)
        ax2.scatter([v.share], [y], marker="s", s=85, fc=YELLOW, ec=INK, lw=1.5, zorder=5)
        ax2.text(0.99, y + 0.2, f"{int(v.k)} of {int(v.n)}", ha="right", fontsize=7.8, color=INK2)
    ax2.set_yticks([2, 1, 0])
    ax2.set_yticklabels(names, fontsize=8.5)
    ax2.set_ylim(-0.6, 2.6)
    ax2.set_title("Share authorized for SNAP after 2005", loc="left", fontsize=10, pad=8)
    fig.suptitle("Why the edge? Dollar General's edge stores sit at crossroads four times as often as random sites, and are newer",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold")
    fig.text(0.01, 0.012,
             "Yellow: share of edge Dollar General stores, line its 95% interval. Black tick: 1,920 random points on main roads "
             "in the same edge band (score A 1 to 2) of the same towns, 40 per edge store. Diamond: edge-band supermarkets "
             "and groceries.\nReasons and tests written before the analysis ran (hypotheses.md). Free-standing Virginia towns and "
             "cities; stores USDA SNAP 2025; roads OSM (ODbL); land NLCD 2001 and 2021; people Census 2020. "
             "Research draft made with Claude.", fontsize=6.8, color=INK2)
    fig.subplots_adjust(left=0.2, right=0.985, top=0.86, bottom=0.14, wspace=0.42)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
