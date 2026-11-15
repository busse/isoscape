#!/usr/bin/env python3
"""Recover the composer settings each landmark print was made with, so its recipe is complete.

Some landmark prints were composed with settings given by hand (zoom, anchor, trim), and with
framing code since changed, that were never written down. This finds the crop each print's map
panel actually shows, by matching the panel against its frozen scene, and records it as an
explicit window (SVG units) in tools/print/lm_params.json, which lm_batch_device.py reads. The
window is checked by recomposing at 24 dpi and comparing with the print sold, both blurred and
small: a mean difference under 3.5 (of 255) is a match (what is left is the rasterizer's
antialiasing); a landmark that does not match is reported, not guessed. All 55 were also
compared side by side by eye on November 15, 2026.

    python3 tools/release/landmark_params.py <store-dir> [<seconds>] [slug...]
"""
import datetime, importlib, json, os, subprocess, sys, tempfile, time
from PIL import Image, ImageChops, ImageFilter, ImageStat

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ISO, 'tools', 'print'))
import lm_compose as M  # noqa: E402

MODS = {}
def composer_at(when):
    """lm_compose (and compose) as they were at the commit current at `when` (a file's mtime):
    the code that made the print, which later commits may have changed."""
    iso = datetime.datetime.fromtimestamp(when, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    c = subprocess.run(['git', '-C', ISO, 'rev-list', '-1', f'--before={iso}', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if subprocess.run(['git', '-C', ISO, 'cat-file', '-e', f'{c}:tools/print/lm_compose.py'], capture_output=True).returncode != 0:
        # Made before the composer was first committed (it was committed with the batch): take that first commit.
        c = subprocess.run(['git', '-C', ISO, 'log', '--reverse', '--format=%H', '--', 'tools/print/lm_compose.py'], capture_output=True, text=True).stdout.split()[0]
    if c not in MODS:
        d = tempfile.mkdtemp(prefix='lmc-')
        for f in ('lm_compose.py', 'compose.py'):
            src = subprocess.run(['git', '-C', ISO, 'show', f'{c}:tools/print/{f}'], capture_output=True, text=True).stdout
            open(os.path.join(d, f), 'w').write(src)
        os.symlink(os.path.join(ISO, 'tools', 'print', 'fonts'), os.path.join(d, 'fonts'))
        for m in ('lm_compose', 'compose'): sys.modules.pop(m, None)
        sys.path.insert(0, d)
        mod = importlib.import_module('lm_compose')
        sys.path.remove(d)
        for m in ('lm_compose', 'compose'): sys.modules.pop(m, None)
        MODS[c] = mod
    return c, MODS[c]

OUT = os.path.join(ISO, 'tools', 'print', 'lm_params.json')


def diff(A, B):
    """Mean difference (of 255) between two prints, blurred and small, so it measures the framing
    and drawing and not the rasterizer's antialiasing."""
    f = lambda im: im.convert('RGB').resize((600, 400)).filter(ImageFilter.GaussianBlur(3)).resize((150, 100))
    d = ImageStat.Stat(ImageChops.difference(f(A), f(B)))
    return sum(d.mean) / 3


def quick(M, slug, title, place, svg, landscape, **opts):
    """The print that module M's make() lays out, at 24 dpi, for comparing settings quickly."""
    if not getattr(M, '_quick', False):
        orig_compose, orig_box, memo = M.C.compose, M.content_box, {}
        M.C.compose = lambda design, size, svgs, regions, dpi: orig_compose(design, size, svgs, regions, 24)
        def box(*a, **k):
            key = repr((a, sorted(k.items())))
            if key not in memo: memo[key] = orig_box(*a, **k)
            return memo[key]
        M.content_box = box
        M._quick = True
    with tempfile.TemporaryDirectory() as d:
        M.make(slug, title, place, svg, d, **({'landscape': landscape} if landscape is not None else {}), **opts)
        f = [x for x in os.listdir(d) if x.endswith('.jpg')][0]
        return Image.open(os.path.join(d, f)).convert('RGB')


def recover_window(svg, sold):
    """The crop window (x, y, w, h in SVG units) a print's map panel shows, found by matching the
    panel against the whole scene over a range of scales (the layout's panel: margin 4.5% and band
    10% of the short side, as lm_compose lays it out)."""
    import re, numpy as np, cv2
    vb = list(map(float, re.search(r'viewBox="([^"]+)"', open(svg, encoding='utf-8').read(3000)).group(1).split()))
    SW = 1400
    with tempfile.TemporaryDirectory() as d:
        src = re.sub(r'<g class="caption".*?</g>', '', open(svg, encoding='utf-8').read(), flags=re.S)
        open(os.path.join(d, 'a.svg'), 'w', encoding='utf-8').write(src)
        M.C.svg_to_png(os.path.join(d, 'a.svg'), os.path.join(d, 'a.png'), SW, None, M.C.PAPER)
        scene = cv2.cvtColor(np.asarray(Image.open(os.path.join(d, 'a.png')).convert('RGB')), cv2.COLOR_RGB2GRAY)
    k = vb[2] / scene.shape[1]
    S = Image.open(sold).convert('RGB'); W, H = S.size; short = min(W, H)
    m = round(short * 0.045); band = round(short * 0.1)
    panel = S.crop((m + 3, m + 3, W - m - 3, H - m - band - 3))
    best = None
    for frac in np.linspace(0.25, 1.0, 61):   # the panel's width as a share of the scene's
        tw = int(scene.shape[1] * frac); th = int(tw * panel.size[1] / panel.size[0])
        if th >= scene.shape[0] or tw >= scene.shape[1] or tw < 40: continue
        t = cv2.cvtColor(np.asarray(panel.resize((tw, th), Image.LANCZOS)), cv2.COLOR_RGB2GRAY)
        res = cv2.matchTemplate(scene, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if best is None or mx > best[0]: best = (mx, loc, tw, th)
    mx, (x, y), tw, th = best
    pad = 3 / panel.size[0] * tw   # the 3 px trimmed from the panel's edges, back in scene pixels
    return [vb[0] + (x - pad) * k, vb[1] + (y - pad) * k, (tw + 2 * pad) * k, (th + 2 * pad) * k], round(float(mx), 3)


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
        # Record the crop itself, not the settings that once produced it: a window in SVG units
        # stays true however the automatic framing code changes.
        S = Image.open(sold)
        win, score = recover_window(svg, sold)
        opts = {'window': [round(v, 2) for v in win]}
        img = quick(M, slug, L[slug][1], L[slug][2], svg, landscape, credit=credit, **opts)
        d = diff(img, S)
        best = (d, opts); commit = 'any (explicit window; template score %s)' % score
        got[slug] = {'composer_commit': commit, 'opts': best[1], 'landscape': landscape, 'mean_diff': round(best[0], 3), 'match': best[0] < 3.5}
        json.dump(got, open(OUT, 'w'), indent=1)
        print(slug, got[slug], flush=True)


if __name__ == '__main__':
    main()
