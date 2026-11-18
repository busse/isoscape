"""Register the 1925 printing of a Jackson Ward sheet (Sanborn, Richmond vol. 3, 1925) onto the
same sheet as republished in 1952, and warp it into the 1952 half-size scan's pixel frame, so the
1952 fits (geo1952.json) place it on the ground unchanged.

The 1952 volume reprints the 1925 plates with later buildings redrawn: streets, block lines, lot
lines, numbers and most buildings sit where they did. Features are matched between the two scans
(SIFT, ratio test), a homography is fitted by RANSAC, and then a smooth correction (a quadratic in
u and v, fitted to the RANSAC inliers) takes up the paper's uneven shrinkage. What is reported per
sheet: the matches kept, and the median and 90th-percentile distance, in meters on the ground, between
each kept match's 1952 position and where its 1925 position lands after the warp.

    python3 reg25.py "<1925 half scan with {sh}>" "<1952 half scan with {sh}>" geo1952.json <out dir> reg25.json [sheet ...]
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np, cv2
from geo import px_per_m


def poly_terms(u, v):
    return np.stack([np.ones_like(u), u, v, u * u, u * v, v * v], 1)


def register(a_path, b_path):
    A = cv2.imread(a_path, cv2.IMREAD_GRAYSCALE)
    B = cv2.imread(b_path, cv2.IMREAD_GRAYSCALE)
    k = B.shape[1] / A.shape[1]  # bring 1925 to roughly the 1952 scale first
    As = cv2.resize(A, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    sift = cv2.SIFT_create(20000)
    ka, da = sift.detectAndCompute(As, None)
    kb, db = sift.detectAndCompute(B, None)
    mm = cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2)
    good = [m for m, n in mm if m.distance < 0.75 * n.distance]
    pa = np.float32([ka[m.queryIdx].pt for m in good]) / k  # 1925 half-scan pixels
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    H, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 4.0, maxIters=20000)
    inl = inl.ravel().astype(bool)
    pa, pb = pa[inl], pb[inl]
    q = cv2.perspectiveTransform(pa[None], H)[0]
    # smooth correction on top of the homography (in 1952 pixels), fitted with one trimming pass
    T = poly_terms(q[:, 0] / 1000, q[:, 1] / 1000)
    keep = np.ones(len(q), bool)
    for _ in range(2):
        cu = np.linalg.lstsq(T[keep], (pb - q)[keep, 0], rcond=None)[0]
        cv_ = np.linalg.lstsq(T[keep], (pb - q)[keep, 1], rcond=None)[0]
        r = np.hypot(T @ cu - (pb - q)[:, 0], T @ cv_ - (pb - q)[:, 1])
        keep = r < max(2.0, np.percentile(r, 90))
    return A, B, H, cu, cv_, pa, pb, keep, k


def warp(A, B, H, cu, cv_):
    """1925 image into the 1952 frame: for each 1952 pixel, undo the correction (one fixed-point
    step is enough: it is a few pixels and smooth), then the inverse homography."""
    h, w = B.shape[:2]
    uu, vv = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    q = np.stack([uu.ravel(), vv.ravel()], 1)
    T = poly_terms(q[:, 0] / 1000, q[:, 1] / 1000)
    q0 = q - np.stack([T @ cu, T @ cv_], 1)
    T = poly_terms(q0[:, 0] / 1000, q0[:, 1] / 1000)
    q0 = q - np.stack([T @ cu, T @ cv_], 1)
    src = cv2.perspectiveTransform(q0[None].astype(np.float64), np.linalg.inv(H))[0]
    mx = src[:, 0].reshape(h, w).astype(np.float32); my = src[:, 1].reshape(h, w).astype(np.float32)
    return mx, my


if __name__ == '__main__':
    fa, fb, geo, outdir, outjson = sys.argv[1:6]
    sheets = sys.argv[6:]
    g = json.load(open(geo))
    res = json.load(open(outjson)) if os.path.exists(outjson) else {}
    os.makedirs(outdir, exist_ok=True)
    for sh in sheets:
        A, B, H, cu, cv_, pa, pb, keep, k = register(fa.format(sh=sh), fb.format(sh=sh))
        q = cv2.perspectiveTransform(pa[None], H)[0]
        T = poly_terms(q[:, 0] / 1000, q[:, 1] / 1000)
        q = q + np.stack([T @ cu, T @ cv_], 1)
        r = np.hypot(*(q - pb).T)
        mpp = 1 / px_per_m(g[sh]['params']) if sh in g else float('nan')
        Ac = cv2.imread(fa.format(sh=sh))
        mx, my = warp(Ac, B, H, cu, cv_)
        W = cv2.remap(Ac, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
        cv2.imwrite(os.path.join(outdir, f'{int(sh):04d}.png'), W)
        res[sh] = {'matches': int(len(pb)), 'kept': int(keep.sum()),
                   'median_m': round(float(np.median(r[keep]) * mpp), 2),
                   'p90_m': round(float(np.percentile(r[keep], 90) * mpp), 2),
                   'median_m_all': round(float(np.median(r) * mpp), 2),
                   'H': H.tolist(), 'cu': cu.tolist(), 'cv': cv_.tolist()}
        print(sh, {k_: v for k_, v in res[sh].items() if k_ not in ('H', 'cu', 'cv')}, flush=True)
    json.dump(res, open(outjson, 'w'), indent=1)
