"""LinkedIn carousel (1080 x 1350 px slides, one PDF): the research and data-viz methods behind
"Why does it always seem like there's a Dollar General on the edge of town?"

Usage: python3 carousel.py <ds-dir> <out-stem>

Numbers come from counts.json and the committed SNAP results; pictures from the released poster's
page figures (pages/dollar-stores-*-large.webp) and one working map from case-study step 2.
Writes <out-stem>.pdf and <out-stem>-NN.png per slide. Made with Claude.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from PIL import Image  # noqa: E402

import poster as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CS = f"{ROOT}/drafts/dollar-stores-virginia/casestudy"
PAPER, INK, INK2, MUTED, GRAY = "#fbfaf7", "#111111", "#4a4946", "#8a8984", "#b9b7b0"
W, H = 10.8, 13.5  # inches at 100 dpi = 1080 x 1350 px
URL = "busse.github.io/isoscape/p/dollar-stores.html"
N = 9


def img(name):
    return Image.open(f"{ROOT}/pages/{name}").convert("RGB")


def slide(n, kicker, head):
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(PAPER)
    fig.text(0.07, 0.955, f"{n}/{N}   {kicker.upper()}", fontsize=13, color=MUTED, va="top")
    h = P.wrap(head, W * 0.86, 34, "bold")
    fig.text(0.07, 0.915, h, fontsize=34, fontweight="bold", color=INK, va="top", linespacing=1.15)
    fig.text(0.07, 0.03, "Chris Busse · made with Claude · " + URL, fontsize=12, color=MUTED, va="bottom")
    fig.top = 0.915 - (h.count("\n") + 1) * 34 * 1.15 / 72 / H - 0.03  # where the paragraph starts
    return fig


def body(fig, y, s, size=19, width=0.86, color=INK2):
    fig.text(0.07, y, P.wrap(s, W * width, size), fontsize=size, color=color, va="top", linespacing=1.45)


def picture(fig, im, box, frame=False):
    x0, y0, w, h = box
    ax = fig.add_axes([x0, y0, w, h])
    ax.imshow(im)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(frame)
        s.set_color(GRAY)
    return ax


def main():
    ds, out = sys.argv[1:3]
    P.setup_fonts(ds)
    c = json.load(open(f"{HERE}/counts.json"))
    th = pd.read_csv(f"{CS}/2026-11-22-14-snap-towns/towns_thirds.csv")
    poster = img("dollar-stores-poster-large.webp")
    charts = img("dollar-stores-charts-large.webp")
    tiles = img("dollar-stores-tiles-large.webp")
    figs = []

    f = slide(1, "A question from the road", "Why does it always seem like there's a Dollar General on the edge of town?")
    body(f, f.top, "It's something you notice driving Virginia's state highways. We set out to check whether "
                  "it's true, and why, using only public data.")
    picture(f, poster.crop((0, 0, 3600, 3700)), (0.17, 0.08, 0.66, 0.6), frame=True)
    figs.append(f)

    f = slide(2, "The answer first", "Most aren't at the edge. The edge ones are hard to miss.")
    body(f, f.top, f"Near small towns in six states around Virginia, {c['edge']} of {c['total']} Dollar Generals "
                  f"stand just outside the built-up part of town, about one in {c['one_in']}. Those edge stores are "
                  f"about {c['junction_x']} times as likely as a random roadside spot to be near a crossing of two "
                  f"US or state highways, on the roads people drive into town.")
    picture(f, charts.crop((0, 70, 1180, 1053)), (0.07, 0.13, 0.62, 0.46))
    body(f, 0.115, "The poster's first chart: the stores counted by where they sit.", size=13, color=MUTED)
    figs.append(f)

    f = slide(3, "Method: turn a feeling into a measure", "First, decide where a town stops.")
    body(f, f.top, "\"The edge of town\" has no official line. We built one from the 2020 Census and federal "
                  "land-cover data. Start where most of the town's people live and move outward. The town ends "
                  "where there are fewer than 200 homes per square mile and little paved or built-on land.")
    m = Image.open(f"{CS}/2026-11-21-02-edge-test/map-marion.png").convert("RGB").crop((132, 142, 1468, 1478))
    picture(f, m, (0.12, 0.11, 0.76, 0.48), frame=True)
    body(f, 0.1, "An early working map of Marion: two candidate edges (blue) against the town limits (black).",
         size=13, color=MUTED)
    figs.append(f)

    f = slide(4, "Method: compare against chance", "First, know what random looks like.")
    body(f, f.top, "Every store was compared with random spots on the same main roads, at the edge of the same "
                  "town. A town with one highway will put a lot of things on that highway. The question is "
                  "whether the stores do it more than chance would.")
    picture(f, charts.crop((1240, 70, 2470, 1053)), (0.07, 0.13, 0.86, 0.46))
    body(f, 0.115, "Yellow: edge Dollar Generals, with the margin of error. Black tick: random spots. Circle: "
                   "convenience stores.", size=13, color=MUTED)
    figs.append(f)

    f = slide(5, "Method: write the test down first", "We saw it in Virginia, then tested it somewhere else.")
    body(f, f.top, "Before opening any data from North Carolina, Tennessee, Kentucky, West Virginia, Maryland or "
                  "South Carolina, we wrote down the tests and what would count as a result. A separate review "
                  "recomputed the main results with its own code.")
    rows = [("Held", f"Near a highway crossing: {c['junction']} of edge stores, against {c['junction_exp']} of random "
                     f"spots. It held in every check."),
            ("Mostly held", f"On one of the two busiest roads in: {c['busiest']} against {c['busiest_exp']}. It "
                            f"failed some checks."),
            ("Changed", f"Inside the town limits: {c['inside']} against {c['inside_exp']}, but most "
                        f"({c['outside']}) are outside. In Virginia most were just inside.")]
    y = 0.56
    for tag, s in rows:
        f.text(0.07, y, tag.upper(), fontsize=14, fontweight="bold", color=INK, va="top")
        body(f, y - 0.03, s, size=19)
        y -= 0.15
    figs.append(f)

    f = slide(6, "Method: add a second data source", "Then bring in the traffic counts.")
    body(f, f.top, f"Federal traffic counts (FHWA, 2024) show how many vehicles pass each spot. On average the road "
                  f"in front of an edge Dollar General carries about {c['traffic_x']} times the traffic of the "
                  f"random spots. Convenience stores sit on the same busy stretches.")
    picture(f, tiles.crop((0, 0, 1730, 1184)), (0.07, 0.13, 0.86, 0.5))
    body(f, 0.115, "Six of the Virginia maps. Darker, thicker roads carry more traffic.", size=13, color=MUTED)
    figs.append(f)

    f = slide(7, "Method: test the obvious explanation", "SNAP looked like a cause. It wasn't.")
    body(f, f.top, f"Around edge stores, {c['s1_store']} of households get SNAP. Around random spots at the same "
                  f"edges it is {c['s1_null']}. Across towns, places with more SNAP households have more food "
                  f"stores of every kind, groceries included.")
    ax = f.add_axes([0.12, 0.19, 0.8, 0.34])
    xs = range(len(th))
    ax.bar([x - 0.19 for x in xs], th.dg_per_1000_hh, width=0.36, color=P.YELLOW, edgecolor=INK, lw=1.2,
           label="Dollar General")
    ax.bar([x + 0.19 for x in xs], th.grocery_per_1000_hh, width=0.36, color=GRAY, label="Grocery")
    for x, a, b in zip(xs, th.dg_per_1000_hh, th.grocery_per_1000_hh):
        ax.text(x - 0.19, a + 0.03, f"{a:.2f}", ha="center", fontsize=13, color=INK)
        ax.text(x + 0.19, b + 0.03, f"{b:.2f}", ha="center", fontsize=13, color=INK)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["Fewest SNAP\nhouseholds", "Middle", "Most SNAP\nhouseholds"], fontsize=14)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_facecolor(PAPER)
    ax.legend(frameon=False, fontsize=14, loc="upper left")
    ax.set_title(f"Stores per 1,000 households, {c['t_places']} small towns in six states", fontsize=14,
                 color=INK2, loc="left")
    body(f, 0.115, "We also couldn't measure SNAP spending at any one store, because federal law has kept that "
                 "data confidential since 2018.", size=14, color=MUTED)
    figs.append(f)

    f = slide(8, "Method: show every case", "Show every case, even the misfits.")
    body(f, f.top, f"The poster maps all {c['va_grid']} Dollar Generals at the edge of a small Virginia town, drawn "
                  f"the same way at the same scale. Some sit at a busy crossing. Some don't. Leaving out the "
                  f"ones that don't fit would have made the case look stronger than it is.")
    picture(f, poster.crop((90, 960, 3510, 3770)).resize((1710, 1405)), (0.07, 0.17, 0.86, 0.5))
    body(f, 0.155, "Each chart has one axis and says what it measures. Every number on the poster is computed "
                 "from the results and traces to a public source.", size=15)
    figs.append(f)

    f = slide(9, "How this was made", "A question, public data and a record of every step.")
    body(f, f.top, "I asked the question and directed the work. The research, the statistics, the maps and the "
                  "page were made in code with Claude. Every draft, dead end and fix was kept as we went, which "
                  "is how this post could be written.")
    body(f, 0.52, "Sources: USDA SNAP Retailer Locator, FHWA traffic counts, the U.S. Census Bureau, USGS land "
                  "cover and OpenStreetMap. Independent, and not affiliated with any company named.", size=16,
         color=MUTED)
    body(f, 0.36, "The full story, the poster and how we know:", size=19, color=INK)
    body(f, 0.31, URL, size=19, color=INK)
    figs.append(f)

    with PdfPages(out + ".pdf") as pdf:
        for i, f in enumerate(figs, 1):
            f.savefig(f"{out}-{i:02d}.png", facecolor=PAPER)
            pdf.savefig(f, facecolor=PAPER)
    print("slides", len(figs))


if __name__ == "__main__":
    main()
