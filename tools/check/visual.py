#!/usr/bin/env python3
"""Visual check: compare new renders of watched views with the last approved ones.

    python3 tools/check/visual.py approve [view...]   build, render and store the crops as the baseline
    python3 tools/check/visual.py check [view...]     build, render and compare with the baseline
    python3 tools/check/visual.py list                the watched views and their crops

    --render   with check: render and compare even when the SVG is identical

The views are in tools/check/views.json: each names the exact build arguments, the width in
pixels to render the whole scene at (about 300 dpi on the largest print of that piece, capped
at 12,000) and two to four crop boxes in render pixels. Only the crops are rendered
(rsvg-convert, one call per crop) and kept.

`approve` writes tools/check/baseline/<view>/<crop>.png and baseline.json (commit, the SVG's
SHA-256, the build's warnings, the cached data it read, the width and the boxes). `check`
writes out/check/index.html with baseline, new and difference side by side for every crop,
worst first, and exits 1 if any crop is out of tolerance. A view whose SVG is byte for byte
the baseline's is reported "identical" without rendering. A view whose cached data is not here
is "skipped: no cached data", not a failure.

Re-approve only after a person has looked at the report and accepted every change in it.
"""
import argparse, concurrent.futures as cf, hashlib, html, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SPEC = os.path.join(HERE, 'views.json')
BASE = os.path.join(HERE, 'baseline')
OUT = os.path.join(ROOT, 'out', 'check')

# A pixel counts as changed when, after a 3x3 blur of both images, some channel differs by more
# than LEVEL (0-255). The blur spreads a lone antialiased pixel over nine, so edge noise stays
# under it while a moved line, a new shape or a shifted shade does not. A crop is within
# tolerance when at most MAX_CHANGED percent of its pixels changed and the mean blurred
# difference is at most MAX_MEAN levels.
LEVEL = 8
MAX_CHANGED = 0.02  # percent
MAX_MEAN = 0.5


# ---- comparison (pure: arrays in, numbers out) ------------------------------------------------

def blur3(a):
    """3x3 box blur of an H x W x C float array, edges repeated."""
    import numpy as np
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    h, w = a.shape[:2]
    s = np.zeros_like(a)
    for dy in range(3):
        for dx in range(3):
            s += p[dy:dy + h, dx:dx + w]
    return s / 9.0


def compare(base, new, level=LEVEL, max_changed=MAX_CHANGED, max_mean=MAX_MEAN):
    """Compare two H x W x 3 uint8 images. Returns raw (percent of pixels differing at all),
    changed (percent differing by more than `level` after a 3x3 blur), mean (mean absolute
    blurred difference, 0-255), ok (within tolerance) and mask (H x W bool, the changed pixels)."""
    import numpy as np
    a = np.asarray(base, dtype=np.float32)
    b = np.asarray(new, dtype=np.float32)
    if a.shape != b.shape:
        h, w = a.shape[:2]
        return {'raw': 100.0, 'changed': 100.0, 'mean': 255.0, 'ok': False, 'mask': np.ones((h, w), bool),
                'note': f'size changed from {a.shape[1]}x{a.shape[0]} to {b.shape[1]}x{b.shape[0]}'}
    raw = np.abs(a - b).max(axis=2) > 0
    d = np.abs(blur3(a) - blur3(b))
    return judge(d.max(axis=2) > level, float(d.mean()), 100.0 * raw.sum() / raw.size, max_changed, max_mean)


def judge(mask, mean, raw, max_changed=MAX_CHANGED, max_mean=MAX_MEAN):
    changed = 100.0 * float(mask.sum()) / mask.size
    return {'raw': raw, 'changed': changed, 'mean': mean, 'ok': bool(changed <= max_changed and mean <= max_mean), 'mask': mask}


def diff_image(new, mask, base, compared=None):
    """The new crop faded to pale gray, with changed pixels in red and every other pixel that
    differs (base against `compared`, default `new`) in amber, so a change reads at a glance."""
    import numpy as np
    a = np.asarray(base, dtype=np.int16)
    b = np.asarray(new if compared is None else compared, dtype=np.int16)
    gray = np.asarray(new, dtype=np.float32).mean(axis=2) if np.asarray(new).shape[:2] == mask.shape else np.full(mask.shape, 200.0)
    out = np.empty(mask.shape + (3,), np.uint8)
    pale = (175 + gray * 75 / 255).astype(np.uint8)
    out[..., 0] = out[..., 1] = out[..., 2] = pale
    if a.shape == b.shape:
        any_ = np.abs(a - b).max(axis=2) > 0
        out[any_ & ~mask] = (240, 170, 40)
    out[mask] = (210, 20, 20)
    return out


# ---- the spec, builds and renders ------------------------------------------------------------

def load_spec():
    return json.load(open(SPEC))['views']


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()


def git(*a):
    try:
        return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def data_files(view):
    """The cached files the build reads: data/<region's data or name>/, top level only.
    None if the folder or its osm.json is missing."""
    region = view['args'][0]
    cfg = json.load(open(os.path.join(ROOT, 'regions', region + '.json')))
    d = os.path.join(ROOT, 'data', cfg.get('data', region))
    if not os.path.isfile(os.path.join(d, 'osm.json')): return None
    return sorted(os.path.join(d, f) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))


def build(view):
    """Build the view into out/check/build/<view>/; return (svg path, viewBox, warnings, seconds)."""
    out = os.path.join(OUT, 'build', view['name'])
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    t0 = time.time()
    r = subprocess.run(['node', 'bin/isoscape.js', 'build', *view['args'], '--no-archive', '--out', out],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"build {' '.join(view['args'])} failed:\n{r.stderr.strip()}")
    svgs = [f for f in os.listdir(out) if f.endswith('.svg')]
    if len(svgs) != 1: raise RuntimeError(f'expected one SVG in {out}, found {svgs}')
    svg = os.path.join(out, svgs[0])
    # Anything the CLI says besides its summary and "wrote" lines is a warning (missing data,
    # drawn flat, ...). It is recorded with the baseline, since it changes what is drawn.
    warnings = [ln for ln in r.stderr.splitlines()
                if ln.strip() and not ln.startswith('wrote ') and ' MB svg, ' not in ln]
    return svg, view_box(svg), warnings, time.time() - t0


def view_box(svg):
    import re
    head = open(svg, encoding='utf-8').read(4000)
    m = re.search(r'viewBox="([^"]+)"', head)
    return [float(v) for v in m.group(1).split()]


def render_crop(svg, width, box, dest):
    x, y, w, h = box
    subprocess.run(['rsvg-convert', '-w', str(width), '--page-width', str(w), '--page-height', str(h),
                    f'--left={-x}', f'--top={-y}', '-b', 'white', '-o', dest, svg], check=True)


def check_boxes(view, vb):
    """Every crop must fall inside the render."""
    W = view['width']
    H = W * vb[3] / vb[2]
    bad = [c['name'] for c in view['crops'] if c['x'] < 0 or c['y'] < 0 or c['x'] + c['w'] > W or c['y'] + c['h'] > H]
    if bad: raise RuntimeError(f"{view['name']}: crops {bad} fall outside the {W} x {H:.0f} px render")


def render_all(view, svg, dest_dir, jobs):
    os.makedirs(dest_dir, exist_ok=True)
    with cf.ThreadPoolExecutor(jobs) as ex:
        futs = [ex.submit(render_crop, svg, view['width'], (c['x'], c['y'], c['w'], c['h']),
                          os.path.join(dest_dir, c['name'] + '.png')) for c in view['crops']]
        for f in futs: f.result()


def load_rgb(p):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(p).convert('RGB'))


def quantize(rgb, palette=None):
    """Map an RGB crop to 256 colors without dithering: to `palette` (a P-mode image) if given,
    else to a median-cut palette of its own. The second step always maps to the nearest palette
    color, so quantizing the same pixels with the stored palette gives the stored image exactly."""
    from PIL import Image
    im = Image.fromarray(rgb) if not isinstance(rgb, Image.Image) else rgb.convert('RGB')
    if palette is None:
        palette = im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return im.quantize(palette=palette, dither=Image.Dither.NONE)


def residual(rgb, q):
    """Per pixel, the largest channel of |blur(rgb) - blur(quantized)|: how far a pixel's color
    is from the palette, after the same blur the comparison uses."""
    import numpy as np
    a = np.asarray(rgb, dtype=np.float32)
    b = np.asarray(q.convert('RGB'), dtype=np.float32)
    return np.abs(blur3(a) - blur3(b)).max(axis=2)


def save_png(arr, dest):
    from PIL import Image
    im = Image.fromarray(arr) if not isinstance(arr, Image.Image) else arr
    im.save(dest, optimize=True)


# ---- approve ---------------------------------------------------------------------------------

def approve(views, jobs):
    import numpy as np
    from PIL import Image
    commit = git('rev-parse', 'HEAD')
    dirty = bool(git('status', '--porcelain', '--untracked-files=no', '--', 'src', 'bin', 'regions', 'history'))
    total = 0
    for v in views:
        files = data_files(v)
        if files is None:
            print(f"{v['name']}: skipped: no cached data"); continue
        t0 = time.time()
        svg, vb, warnings, secs = build(v)
        check_boxes(v, vb)
        tmp = os.path.join(OUT, 'approve', v['name'])
        shutil.rmtree(tmp, ignore_errors=True)
        render_all(v, svg, tmp, jobs)
        dest = os.path.join(BASE, v['name'])
        shutil.rmtree(dest, ignore_errors=True)
        os.makedirs(dest)
        resid = {}
        for c in v['crops']:
            # Stored as a 256-color palette PNG to keep the baseline small. check quantizes the new
            # crop with this palette before comparing, so an unchanged render compares equal; the
            # largest residual here bounds how far an unchanged pixel can sit from the palette.
            rgb = load_rgb(os.path.join(tmp, c['name'] + '.png'))
            q = quantize(rgb)
            p = os.path.join(dest, c['name'] + '.png')
            save_png(q, p)
            again = quantize(rgb, Image.open(p))
            if not (load_rgb(p) == np.asarray(again.convert('RGB'))).all():
                raise RuntimeError(f"{v['name']}/{c['name']}: stored crop does not requantize to itself")
            r = residual(rgb, again)
            resid[c['name']] = {'max': round(float(r.max()), 3), 'mean': round(float(r.mean()), 4)}
        rec = {
            'view': v['name'], 'args': v['args'], 'commit': commit, 'dirty': dirty,
            'approved': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'svg_sha256': sha_file(svg), 'svg_bytes': os.path.getsize(svg), 'viewBox': vb,
            'width': v['width'], 'crops': [{k: c[k] for k in ('name', 'x', 'y', 'w', 'h')} for c in v['crops']],
            'warnings': warnings, 'residual': resid,
            'data': {os.path.relpath(f, ROOT): sha_file(f) for f in files},
        }
        json.dump(rec, open(os.path.join(dest, 'baseline.json'), 'w'), indent=1)
        size = sum(os.path.getsize(os.path.join(dest, f)) for f in os.listdir(dest))
        total += size
        print(f"{v['name']}: approved {len(v['crops'])} crops, {size / 1e6:.2f} MB, {time.time() - t0:.0f} s"
              + (f"  (warnings: {'; '.join(warnings)})" if warnings else ''))
    all_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(BASE) for f in fs)
    print(f'baseline: {all_size / 1e6:.2f} MB in {os.path.relpath(BASE, ROOT)}')


# ---- check -----------------------------------------------------------------------------------

def check(views, jobs, force=False):
    import numpy as np
    from PIL import Image
    t_all = time.time()
    shutil.rmtree(os.path.join(OUT, 'crops'), ignore_errors=True)
    results, rows, failed = [], [], False
    for v in views:
        name = v['name']
        bdir = os.path.join(BASE, name)
        bj = os.path.join(bdir, 'baseline.json')
        files = data_files(v)
        if files is None:
            results.append((name, 'skipped: no cached data', None)); print(f'{name}: skipped: no cached data'); continue
        if not os.path.exists(bj):
            failed = True
            results.append((name, 'no baseline: run approve', None)); print(f'{name}: FAIL no baseline (run approve)'); continue
        base = json.load(open(bj))
        notes = []
        spec_crops = [{k: c[k] for k in ('name', 'x', 'y', 'w', 'h')} for c in v['crops']]
        if base['width'] != v['width'] or base['crops'] != spec_crops or base['args'] != v['args']:
            failed = True
            msg = 'views.json changed since approval (args, width or crops): re-approve this view'
            results.append((name, 'FAIL ' + msg, None)); print(f'{name}: FAIL {msg}'); continue
        data_now = {os.path.relpath(f, ROOT): sha_file(f) for f in files}
        if data_now != base['data']:
            changed = sorted(set(data_now.items()) ^ set(base['data'].items()))
            notes.append('cached data differs from the baseline\'s: ' + ', '.join(sorted({k for k, _ in changed})))
        t0 = time.time()
        svg, vb, warnings, _ = build(v)
        if warnings != base['warnings']:
            notes.append('build warnings differ: was ' + (('; '.join(base['warnings'])) or 'none') + ', now ' + (('; '.join(warnings)) or 'none'))
        digest = sha_file(svg)
        if digest == base['svg_sha256'] and not force:
            line = f'{name}: identical ({time.time() - t0:.0f} s)'
            print(line + (f"  [{' | '.join(notes)}]" if notes else ''))
            results.append((name, 'identical', notes)); continue
        check_boxes(v, vb)
        cdir = os.path.join(OUT, 'crops', name)
        render_all(v, svg, cdir, jobs)
        worst, nbad = None, 0
        for c in v['crops']:
            bp = os.path.join(bdir, c['name'] + '.png')
            np_ = os.path.join(cdir, c['name'] + '.png')
            if not os.path.exists(bp):
                failed = True; nbad += 1
                rows.append({'view': name, 'crop': c['name'], 'why': c.get('why', ''), 'missing': True, 'ok': False,
                             'raw': 100, 'changed': 100, 'mean': 255}); continue
            a, full = load_rgb(bp), load_rgb(np_)
            q = quantize(full, Image.open(bp))
            b = np.asarray(q.convert('RGB'))
            r = compare(a, b)
            # Colors the baseline's palette cannot hold (a new shade) show as a residual larger
            # than any the baseline had; count those pixels as changed too.
            rb = base.get('residual', {}).get(c['name'], {'max': 0, 'mean': 0})
            rn = residual(full, q)
            off = rn > max(rb['max'], LEVEL)
            if off.any() or rn.mean() > rb['mean']:
                r = judge(r['mask'] | off, r['mean'] + max(0.0, float(rn.mean()) - rb['mean']), r['raw'])
            stem = os.path.join(cdir, c['name'])
            shutil.copyfile(bp, stem + '-base.png')
            os.replace(np_, stem + '-new.png')
            save_png(diff_image(full, r['mask'], a, b), stem + '-diff.png')
            rows.append({'view': name, 'crop': c['name'], 'why': c.get('why', ''), 'ok': r['ok'], 'raw': r['raw'],
                         'changed': r['changed'], 'mean': r['mean'], 'note': r.get('note', ''),
                         'img': os.path.relpath(stem, OUT)})
            if not r['ok']: nbad += 1; failed = True
            if worst is None or r['mean'] > worst[1]['mean']: worst = (c['name'], r)
        status = f'{nbad} of {len(v["crops"])} crops changed' if nbad else 'within tolerance'
        detail = f"worst {worst[0]}: {worst[1]['changed']:.3f}% changed, mean {worst[1]['mean']:.2f}" if worst else ''
        print(f"{name}: {'FAIL ' if nbad else ''}{status}; {detail} ({time.time() - t0:.0f} s)"
              + (f"  [{' | '.join(notes)}]" if notes else ''))
        results.append((name, ('FAIL ' if nbad else '') + status, notes))
    write_report(results, rows, time.time() - t_all)
    print(f'report: {os.path.relpath(os.path.join(OUT, "index.html"), ROOT)} ({time.time() - t_all:.0f} s)')
    return 1 if failed else 0


def write_report(results, rows, secs):
    e = html.escape
    rows.sort(key=lambda r: (r['ok'], -r['changed'], -r['mean']))
    commit = git('rev-parse', '--short', 'HEAD') or '?'
    if git('status', '--porcelain', '--untracked-files=no'): commit += ' with uncommitted changes'
    parts = [f'''<!doctype html><meta charset="utf-8"><title>isoscape visual check</title>
<style>
body{{font:14px/1.45 system-ui,sans-serif;margin:24px;color:#222;background:#fafafa}}
h1{{font-size:20px;margin:0 0 4px}} .sub{{color:#666;margin-bottom:16px}}
table.sum{{border-collapse:collapse;margin-bottom:24px}} .sum td{{padding:3px 12px 3px 0;vertical-align:top}}
.fail{{color:#b00;font-weight:600}} .ok{{color:#070}} .note{{color:#875;font-size:12px}}
.crop{{background:#fff;border:1px solid #ddd;border-radius:6px;padding:12px;margin:0 0 20px}}
.crop.bad{{border-color:#d55}} .crop h2{{font-size:15px;margin:0 0 2px}} .why{{color:#555;margin-bottom:8px}}
.imgs{{display:flex;gap:8px}} .imgs figure{{flex:1;margin:0;min-width:0}} .imgs img{{width:100%;display:block;border:1px solid #ccc}}
figcaption{{font-size:12px;color:#666}} .legend span{{display:inline-block;width:10px;height:10px;margin:0 4px 0 10px}}
</style>
<h1>isoscape visual check</h1>
<div class="sub">commit {e(commit)} · {time.strftime('%Y-%m-%d %H:%M')} · {secs:.0f} s ·
a pixel counts as changed when it differs by more than {LEVEL} levels after a 3×3 blur; a crop passes at ≤ {MAX_CHANGED}% changed and mean ≤ {MAX_MEAN}.
Approve again only after a person has looked at every change here and accepted it.</div>
<table class="sum">''']
    for name, status, notes in results:
        cls = 'fail' if status.startswith(('FAIL', 'no baseline')) else 'ok'
        parts.append(f'<tr><td>{e(name)}</td><td class="{cls}">{e(status)}</td><td class="note">{e(" | ".join(notes or []))}</td></tr>')
    parts.append('</table>')
    if rows:
        parts.append('<div class="legend">Difference: <span style="background:#d21414"></span>changed '
                     '<span style="background:#f0aa28"></span>differs, but by less than the threshold (antialiasing, faint shade changes)</div><br>')
    for r in rows:
        bad = not r['ok']
        head = f"{e(r['view'])} / {e(r['crop'])} — <span class=\"{'fail' if bad else 'ok'}\">" + \
               (f"{r['changed']:.3f}% changed, mean {r['mean']:.2f}, {r['raw']:.2f}% of pixels differ at all" if not r.get('missing') else 'no baseline crop') + '</span>'
        parts.append(f'<div class="crop{" bad" if bad else ""}"><h2>{head}</h2><div class="why">{e(r["why"])}'
                     + (f' <b>{e(r["note"])}</b>' if r.get('note') else '') + '</div>')
        if not r.get('missing'):
            parts.append('<div class="imgs">' + ''.join(
                f'<figure><a href="{e(r["img"])}-{k}.png"><img src="{e(r["img"])}-{k}.png" loading="lazy"></a><figcaption>{t}</figcaption></figure>'
                for k, t in (('base', 'baseline'), ('new', 'new'), ('diff', 'difference'))) + '</div>')
        parts.append('</div>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w').write('\n'.join(parts))


# ---- main ------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('command', choices=('approve', 'check', 'list'))
    ap.add_argument('views', nargs='*', help='view names (default: all)')
    ap.add_argument('--render', action='store_true',
                    help='check: render and compare even when the SVG is identical (after updating rsvg-convert or Pillow)')
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 2, help='crops rendered at once')
    a = ap.parse_args()
    views = load_spec()
    if a.views:
        unknown = set(a.views) - {v['name'] for v in views}
        if unknown: ap.error(f'unknown views: {", ".join(sorted(unknown))}')
        views = [v for v in views if v['name'] in a.views]
    if a.command == 'list':
        for v in views:
            print(f"{v['name']}: build {' '.join(v['args'])} at {v['width']} px")
            for c in v['crops']: print(f"  {c['name']} {c['w']}x{c['h']}+{c['x']}+{c['y']}  {c.get('why', '')}")
        return 0
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        sys.exit('visual.py needs Pillow and numpy: pip install pillow numpy')
    if shutil.which('rsvg-convert') is None: sys.exit('visual.py needs rsvg-convert (brew install librsvg)')
    if a.command == 'approve':
        approve(views, a.jobs); return 0
    return check(views, a.jobs, a.render)


if __name__ == '__main__':
    sys.exit(main())
