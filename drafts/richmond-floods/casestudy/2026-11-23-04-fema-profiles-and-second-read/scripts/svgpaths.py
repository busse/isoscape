# Parse pdftocairo SVG output into stroked polylines in page coordinates (points, y down).
import re, sys, collections
NUM = r'-?[\d.]+(?:e-?\d+)?'
def parse(fn):
    s = open(fn).read()
    out = []
    for m in re.finditer(r'<path ([^>]*?)/>', s):
        a = m.group(1)
        if 'stroke=' not in a or 'fill="none"' not in a: continue
        sw = float(re.search(r'stroke-width="([^"]+)"', a).group(1))
        col = re.search(r'stroke="([^"]+)"', a).group(1)
        d = re.search(r' d="([^"]+)"', a).group(1)
        t = re.search(r'transform="matrix\(([^)]+)\)"', a)
        M = [float(x) for x in t.group(1).split(',')] if t else [1,0,0,1,0,0]
        toks = re.findall(r'[MLCZ]|' + NUM, d)
        subs = []; cur = []; cmd = None; buf = []
        i = 0
        while i < len(toks):
            tk = toks[i]
            if tk in 'MLCZ':
                cmd = tk
                if tk == 'M':
                    if cur: subs.append(cur)
                    cur = []
                if tk == 'Z' and cur: cur.append(cur[0])
                i += 1; continue
            n = 6 if cmd == 'C' else 2
            vals = [float(x) for x in toks[i:i+n]]; i += n
            x, y = vals[-2], vals[-1]
            X = M[0]*x + M[2]*y + M[4]; Y = M[1]*x + M[3]*y + M[5]
            cur.append((X, Y))
        if cur: subs.append(cur)
        swp = sw * abs(M[0]) if t else sw
        for sp in subs:
            out.append((round(swp, 3), col, sp))
    return out
if __name__ == '__main__':
    P = parse(sys.argv[1])
    c = collections.Counter((p[0], p[1]) for p in P)
    for k, v in sorted(c.items()): print(k, v)
