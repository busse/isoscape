#!/usr/bin/env python3
"""Recover the composer settings each landmark print was made with, so its recipe is complete.

Some landmark prints were composed with settings given by hand (zoom, anchor, trim) that were
never written down. This recomposes each landmark from its frozen scene with the settings in
lm_batch_device.OPTS, compares it with the print that was sold, and where they differ searches
the settings until one matches. Results go to tools/print/lm_params.json, which
lm_batch_device.py reads; a landmark with no match is reported, not guessed.

    python3 tools/release/landmark_params.py <store-dir> [<seconds>] [slug...]
"""
import itertools, json, os, sys, tempfile, time
from PIL import Image, ImageChops, ImageStat

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ISO, 'tools', 'print'))
import lm_compose as M  # noqa: E402

OUT = os.path.join(ISO, 'tools', 'print', 'lm_params.json')


def diff(a, b):
    A = Image.open(a).convert('RGB'); B = Image.open(b).convert('RGB')
    if A.size != B.size: return 999.0
    d = ImageStat.Stat(ImageChops.difference(A.resize((900, 600)), B.resize((900, 600))))
    return sum(d.mean) / 3


def main():
    store = sys.argv[1]; budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9; only = set(sys.argv[3:])
    t0 = time.time()
    L = {x[0]: x for x in json.load(open(os.path.join(store, 'landmarks', 'list.json')))}
    got = json.load(open(OUT)) if os.path.exists(OUT) else {}
    index = json.load(open(os.path.join(ISO, 'releases', 'index.json')))
    base = {'matterhorn': {'zoom': False, 'trim': False}}
    tries = [{}] + [{'zoom': z, **({'anchor': a} if a is not None else {})} for z in (False, True)
                    for a in (None, 'top', 'left', 0.0, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0)]
    for key in index:
        if not key.startswith('lm-'): continue
        slug = key[3:]
        if (only and slug not in only) or (not only and slug in got): continue
        if time.time() - t0 > budget: print('OUT OF TIME'); break
        r = json.load(open(os.path.join(ISO, 'releases', key, f"v{index[key]['current']}.json")))
        sold = os.path.join(store, r['outputs']['print']['file'])
        svg = os.path.join(ISO, r['scenes'][0]['frozen'])
        landscape = 'x'.join(sorted(os.path.basename(sold).rsplit('_', 1)[1][:-4].split('x'), key=int, reverse=True)) == os.path.basename(sold).rsplit('_', 1)[1][:-4]
        credit = M.elevation_credit(os.path.join(ISO, 'regions', f'{key}.json'))
        best = None
        for t in tries:
            opts = {**base.get(slug, {}), **t}
            with tempfile.TemporaryDirectory() as d:
                try: M.make(slug, L[slug][1], L[slug][2], svg, d, credit=credit, landscape=landscape, **opts)
                except Exception as e: continue
                f = [x for x in os.listdir(d) if x.endswith('.jpg') and '_canvas' not in x][0]
                s = diff(os.path.join(d, f), sold)
            if best is None or s < best[0]: best = (s, opts)
            if s < 1.0: break
        got[slug] = {'opts': best[1], 'landscape': landscape, 'mean_diff': round(best[0], 3), 'match': best[0] < 1.0}
        json.dump(got, open(OUT, 'w'), indent=1)
        print(slug, got[slug], flush=True)


if __name__ == '__main__':
    main()
