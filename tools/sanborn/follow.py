"""Carry a sheet's georeference to the same sheet in a later edition (a correction or reprint of
the same plate): match features between the two scans (ORB, RANSAC similarity) and compose."""
import json, sys
import numpy as np
import cv2
from geo import to_m, w2i, fit_sim, px_per_m

def match(a_path, b_path, n=6000):
    A = cv2.imread(a_path, cv2.IMREAD_GRAYSCALE); B = cv2.imread(b_path, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(n)
    ka, da = orb.detectAndCompute(A, None); kb, db = orb.detectAndCompute(B, None)
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=5000)
    return M, int(inl.sum()) if inl is not None else 0, len(m)

if __name__ == '__main__':
    geo_in, fmt_a, fmt_b, out = sys.argv[1:5]
    sheets = sys.argv[5:]
    g = json.load(open(geo_in)); res = {}
    for sh in sheets:
        if sh not in g: continue
        p = g[sh]['params']
        M, inl, nm = match(fmt_a.format(sh=int(sh)), fmt_b.format(sh=int(sh)))
        if M is None or inl < 40:
            print(sh, 'no match', inl, nm); continue
        # world points spread over the old sheet, carried through the image-to-image map
        uu, vv = np.meshgrid(np.linspace(100, 1500, 6), np.linspace(100, 1800, 6))
        uv = np.stack([uu.ravel(), vv.ravel()], 1)
        from geo import i2w
        xy = i2w(p, uv)
        uv2 = uv @ M[:, :2].T + M[:, 2]
        q = fit_sim(xy, uv2)
        res[sh] = {'params': [float(v) for v in q], 'from': geo_in, 'inliers': inl}
        print(sh, 'inliers', inl, '/', nm, 'scale', round(float(np.hypot(*M[:, 0])), 3), 'm/px', round(1 / px_per_m(q), 4))
    json.dump(res, open(out, 'w'), indent=1)
