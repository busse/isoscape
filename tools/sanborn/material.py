"""Sanborn colors (later editions add olive-brown for fire-proof), read relative to each sheet's own paper (scans differ in tone): pink is
brick, yellow frame, blue stone (and water), gray iron, green 'special' (fire-resistive)."""
import numpy as np

CLASSES = ['none', 'brick', 'frame', 'stone', 'iron', 'special', 'fireproof']


def classify(im, fireproof=False):
    im = im.astype(np.int16)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    V = im.max(2)
    # printed lines: dark relative to the paper (scans differ in exposure)
    ink = V < 0.6 * np.percentile(V, 90)
    # paper: the commonest light color
    light = ~ink & (V >= np.percentile(V, 40))
    q = (im[light] // 6).reshape(-1, 3).astype(np.int64)
    vals, counts = np.unique(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2], return_counts=True)
    m = vals[counts.argmax()]
    P = np.array([m // 10000, (m // 100) % 100, m % 100]) * 6 + 3
    rg, bg, br = (R - G) - (P[0] - P[1]), (B - G) - (P[2] - P[1]), (B - R) - (P[2] - P[0])
    lum = (R + G + B) / 3 - P.mean()
    sat = im.max(2) - im.min(2)
    out = np.zeros(R.shape, np.uint8)
    out[(rg > 9) & (bg > 6) & ~ink] = 1                       # pink: brick
    out[(bg < -10) & (rg > -6) & (lum > -8) & ~ink] = 2       # yellow: frame
    out[(br > 22) & ~ink] = 3                                 # blue: stone or water
    out[(sat < 14) & (lum < -22) & ~ink & (out == 0)] = 4     # gray: iron
    greenish = (G - (R + B) / 2 - (P[1] - (P[0] + P[2]) / 2) > 8) & ~ink
    # On aged paper the yellow wash reads green; true green specials lean blue.
    out[greenish & (br <= 10)] = 2
    out[greenish & (br > 10)] = 5
    if fireproof:
        # Later editions add an olive-brown for fire-proof construction (steel and concrete).
        olive = (bg > -38) & (bg < -10) & (rg > 5) & (lum < -35) & ~ink
        out[olive] = 6
        out[(bg <= -38) & ~ink] = 2
    return out, ink, P
