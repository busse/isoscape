# Read FIS flood-profile lines from vector geometry (pdftocairo SVG).
# Each profile is drawn as dashed segments of stroke width ~1.134 pt. At a station x we collect
# every segment that spans x (or lies within WIN pt of it, extended linearly) and cluster the y values.
import sys, json
sys.path.insert(0, '/home/claude/floods-research/check/scripts')
from svgpaths import parse
PANELS = {  # PDF page: (panel, x at first major V line, y at top major H line); 1,000 ft and 20 ft per 72 pt
 106: ('17P', 131000, 100), 107: ('18P', 144000, 100), 108: ('19P', 157000, 120),
 109: ('20P', 170000, 180), 110: ('21P', 183000, 200), 111: ('22P', 196000, 220), 112: ('23P', 209000, 220)}
X0P, Y0P, PT = 129.6, 72.0, 72.0
def cal(page):
    _, x0, ytop = PANELS[page]
    fx = lambda X: x0 + (X - X0P) / PT * 1000.0
    fy = lambda Y: ytop - (Y - Y0P) / PT * 20.0
    ix = lambda x: X0P + (x - x0) / 1000.0 * PT
    return fx, fy, ix
def segs(page, width=1.134):
    P = parse(f'/home/claude/floods-research/check/work/svg/p{page}.svg')
    out = []
    for w, c, sp in P:
        if abs(w - width) > 0.01 or len(sp) < 2: continue
        for a, b in zip(sp, sp[1:]):
            if a[0] == b[0]: continue  # vertical pieces: bridge marks, frame
            if a[0] > b[0]: a, b = b, a
            if a[0] < 129 or b[0] > 1066.5: continue
            if a[1] > 718 and b[1] > 718: continue
            out.append((a, b))
    return out
def sample2(page, x, win=3.0, tol=0.45):
    """Only segments that come within win pt of x; values clamped to the segment (no extrapolation)."""
    fx, fy, ix = cal(page)
    X = ix(x); ys = []
    for (a, b) in segs(page):
        if a[0] > 850 and a[1] > 575: continue  # legend box
        if b[0] < X - win or a[0] > X + win: continue
        Xc = min(max(X, a[0]), b[0])
        t = (Xc - a[0]) / (b[0] - a[0]); Y = a[1] + t * (b[1] - a[1])
        ys.append((Y, abs(Xc - X)))
    ys.sort(); cl = []
    for Y, d in ys:
        if cl and abs(Y - cl[-1][-1][0]) < tol: cl[-1].append((Y, d))
        else: cl.append([(Y, d)])
    return [round(fy(min(c, key=lambda t: t[1])[0]), 2) for c in cl][::1]
def sample(page, x, win=6.0, tol=0.25):
    fx, fy, ix = cal(page)
    X = ix(x); S = segs(page)
    ys = []
    for (a, b) in S:
        if a[0] - win <= X <= b[0] + win:
            # skip legend box
            if a[0] > 1000 and a[1] > 570: continue
            t = (X - a[0]) / (b[0] - a[0])
            Y = a[1] + t * (b[1] - a[1])
            d = 0 if a[0] <= X <= b[0] else min(abs(X - a[0]), abs(X - b[0]))
            ys.append((Y, d))
    ys.sort()
    cl = []
    for Y, d in ys:
        if cl and abs(Y - cl[-1][-1][0]) < tol: cl[-1].append((Y, d))
        else: cl.append([(Y, d)])
    res = []
    for c in cl:
        best = min(c, key=lambda t: t[1])
        res.append((round(fy(best[0]), 2), round(best[1], 1), len(c)))
    return res
if __name__ == '__main__':
    page = int(sys.argv[1])
    for x in map(float, sys.argv[2:]):
        print(int(x), sample(page, x))
