"""Fixed-scale fit (rotation and shift only) from control points: the scans of one edition share a
scale, so two named corners are enough, and a third shows a misread one."""
import json, sys, math, itertools
import numpy as np
from geo import to_m, w2i

def fit_rigid(xy, uv, s):
    a = np.stack([xy[:, 0], -xy[:, 1]], 1) * s
    ma, mb = a.mean(0), uv.mean(0)
    A, B = a - ma, uv - mb
    C = B.T @ A
    U, S, Vt = np.linalg.svd(C)
    D = np.diag([1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    th = math.atan2(R[1, 0], R[0, 0])
    t = mb - R @ ma
    return (float(t[0]), float(t[1]), th, s)

def best_fit(rows, s, tol=6.0):
    uv = np.array([r[:2] for r in rows], float)
    x, y = to_m([r[2] for r in rows], [r[3] for r in rows]); xy = np.stack([x, y], 1)
    best = None
    n = len(rows)
    for k in range(n, 1, -1):
        for sub in itertools.combinations(range(n), k):
            sub = list(sub)
            p = fit_rigid(xy[sub], uv[sub], s)
            res = np.hypot(*(w2i(p, xy) - uv).T) / s
            score = (sum(res[sub] <= tol), -res[sub].max())
            if best is None or score > best[0]:
                best = (score, p, res, sub)
        if best and best[0][0] == k and best[2][best[3]].max() <= tol:
            break
    return best

if __name__ == '__main__':
    cps = json.load(open(sys.argv[1])); s = 1 / float(sys.argv[2]); out = sys.argv[3]
    res = {}
    for sh, rows in cps.items():
        (_, worst), p, r, sub = best_fit(rows, s)
        res[sh] = dict(params=p, used=[rows[i][4] for i in sub], resid_m=[round(float(v), 1) for v in r], ok=bool(-worst <= 6 and len(sub) >= 2))
        print(sh, res[sh]['resid_m'], 'used', len(sub), 'ok' if res[sh]['ok'] else 'CHECK')
    json.dump(res, open(out, 'w'), indent=1)
