#!/usr/bin/env python3
"""Check release records (see record.py): that every pinned file is still there with the bytes
it was recorded with, and, with --rebuild, that every scene still comes out of its recorded
commit and frozen data byte for byte.

    python3 tools/release/check.py <store-dir> [design...] [--rebuild]

--rebuild checks out each recorded commit into a scratch worktree, points its data/ at the
frozen copies, builds each scene as recorded, and compares SHA-256. A scene that matches is
proof the design can be remade exactly; the check writes "reproduces" into the record. A
stamped version (kind "stamp", stamp.py, or "redraw", stamp.py --base) is also stamped again from its base files with the
recorded commit's tools, and every file must come out byte for byte ("restamped"). A revision
(kind "revision": corrected art replacing an unsold edition's files, asset version 3.1.0, record
v3.1.json) is checked as a redraw, and the files it superseded must still be there unchanged.

An editorial record (kind "editorial": released, not for sale, in no store) is skipped by a store
check and checked on its own, with no store:

    python3 tools/release/check.py --editorial [design...] [--rebuild] [--data NAME=FOLDER]

Every pinned input, output and the inspection report must match its SHA-256. --rebuild runs each
step of the record's recipe in a scratch folder holding only the pinned inputs and compares what
it makes with the recorded outputs: identical bytes; for a PDF, identical but for its creation
date, else the same pixels rasterized (pdftoppm); for an image, the same pixels. A step whose
outside data (--data), Python modules or programs are not here is not run: the check names
exactly what is missing and fails as INCOMPLETE. The result is written into "reproduced".
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
REL = os.path.join(ISO, 'releases')
# Scenes already rebuilt (commit, region, year, flags, frozen data) -> SHA-256, so a scene shared
# by many designs (every print of a set) is rebuilt once.
MEMO_P = os.path.join(ISO, 'data', '_releases', 'rebuilt.json')
MEMO = json.load(open(MEMO_P)) if os.path.exists(MEMO_P) else {}


# Kinds whose files are stamped from base files (stamp.py): a new block on the previous version's
# files ("stamp"), or new art composed and then stamped ("redraw", stamp.py --base).
STAMPED = ('stamp', 'redraw', 'revision')   # a revision (record.py) is a redraw within an unsold edition


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def outputs(r):
    """Every output file of a record: its print, any other size's print (a "prints" map), its canvas."""
    o = r['outputs']
    return [o['print']] + o.get('prints', []) + o['canvas']


def problems(store, r):
    bad = []
    files = json.load(open(os.path.join(store, 'pipeline', 'files.json')))
    for o in outputs(r):
        p = os.path.join(store, o['file'])
        if o.get('missing') or not os.path.exists(p): bad.append(('output missing', o['file'])); continue
        if sha(p) != o['sha256']: bad.append(('output changed', o['file']))
        if o.get('printful_file_id') and files.get(os.path.basename(p)) != o['printful_file_id']: bad.append(('printful file id changed', o['file']))
    for name, dd in r['data'].items():
        snap = os.path.join(ISO, dd['snapshot'])
        for f, h in dd['files'].items():
            q = os.path.join(snap, f)
            if not os.path.exists(q): bad.append(('frozen data missing', dd['snapshot'], f))
            elif sha(q) != h: bad.append(('frozen data changed', dd['snapshot'], f))
    for s in r['scenes']:
        f = os.path.join(ISO, s.get('frozen') or '')
        if s.get('sha256') and (not s.get('frozen') or not os.path.exists(f) or sha(f) != s['sha256']): bad.append(('frozen scene missing or changed', s.get('frozen')))
    for f, v in ((r.get('recipe') or {}).get('files') or {}).items() if r.get('kind') in STAMPED else []:
        q = os.path.join(store, v['base'])
        if not os.path.exists(q): bad.append(('stamp base missing', v['base']))
        elif sha(q) != v['base_sha256']: bad.append(('stamp base changed', v['base']))
    for o in (r.get('supersedes') or {}).get('outputs', []):   # a revision keeps the files it replaced
        q = os.path.join(store, o['file'])
        if not os.path.exists(q): bad.append(('superseded output missing', o['file']))
        elif o.get('sha256') and sha(q) != o['sha256']: bad.append(('superseded output changed', o['file']))
    c = r['isoscape']['commit']
    if subprocess.run(['git', '-C', ISO, 'cat-file', '-e', c + '^{commit}']).returncode != 0: bad.append(('commit not in repo', c))
    return bad


def worktree(c, r, keep):
    wt = keep.get(c)
    if wt is None:
        wt = tempfile.mkdtemp(prefix='iso-rel-')
        subprocess.run(['git', '-C', ISO, 'worktree', 'add', '--detach', wt, c], check=True, capture_output=True)
        keep[c] = wt
    os.makedirs(os.path.join(wt, 'data'), exist_ok=True)
    for name, dd in r['data'].items():
        link = os.path.join(wt, 'data', name)
        if os.path.islink(link): os.unlink(link)
        elif os.path.isdir(link): shutil.rmtree(link)   # data tracked in git at that commit: the frozen copy has it too
        os.symlink(os.path.join(ISO, dd['snapshot']), link)
    return wt


def rebuild(r, keep):
    """(matched, total) scenes rebuilt from their commit (the scene's own, else the record's)
    and the frozen data. A scene that does not match is still safe: its frozen SVG is the art."""
    ok = n = 0
    for s in r['scenes']:
        if not s.get('region') or not s.get('sha256'): continue
        n += 1
        c = s.get('commit') or r['isoscape']['commit']
        # A build can write more than one scene (a cutaway's flat section: output "-section").
        memo_key = json.dumps([c, s['region'], s.get('year'), s.get('flags', []), sorted((k, v['snapshot']) for k, v in r['data'].items())] + ([s['output']] if s.get('output') else []))
        if memo_key in MEMO:
            s['reproduces'] = MEMO[memo_key] == s['sha256']; ok += s['reproduces']; continue
        wt = worktree(c, r, keep)
        with tempfile.TemporaryDirectory() as t:
            cmd = ['node', 'bin/isoscape.js', 'build', s['region'], '--no-archive', '--out', t] + (['--year', str(s['year'])] if s.get('year') is not None else []) + s.get('flags', [])
            subprocess.run(cmd, cwd=wt, capture_output=True)
            out = os.path.join(t, (f"{s['region']}-{s['year']}" if s.get('year') is not None else s['region']) + s.get('output', '') + '.svg')
            got = sha(out) if os.path.exists(out) else None
        MEMO[memo_key] = got
        json.dump(MEMO, open(MEMO_P, 'w'))
        s['reproduces'] = got == s['sha256']
        ok += s['reproduces']
    return ok, n


def restamp(store, r, keep):
    """(matched, total) files of a stamped version made again from their base files with the
    recorded commit's stamp.py and title block, compared by SHA-256."""
    store = os.path.abspath(store)
    files = r['recipe']['files']; outs = {os.path.basename(o['file']): o for o in outputs(r)}
    wt = worktree(r['isoscape']['commit'], {'data': {}}, keep)
    ok = 0
    with tempfile.TemporaryDirectory() as t:
        for f, v in files.items():
            dst = os.path.join(t, f)
            code = ('import sys, json; sys.path[:0] = ["tools/print", "tools/release"]; import stamp; '
                    f'stamp.stamp_file({os.path.join(store, v["base"])!r}, {dst!r}, json.loads({json.dumps(json.dumps(r["recipe"]["block"]))}))')
            subprocess.run([sys.executable, '-c', code], cwd=wt, capture_output=True)
            ok += os.path.exists(dst) and sha(dst) == (outs.get(f) or {}).get('sha256')
    return ok, len(files)


# ---- editorial records (record.py --editorial): released, in no store --------------------------

EDITORIAL = 'editorial'


def editorial_files(r):
    """Every file an editorial record pins: (path in the repo, sha256, what it is)."""
    o = r['outputs']
    out = [(f, h, 'input') for f, h in r['inputs'].items()]
    out += [(x['file'], x['sha256'], 'output') for x in [o['print']] + o.get('prints', []) + o.get('derived', [])]
    if r.get('inspection'): out.append((r['inspection']['report'], r['inspection']['sha256'], 'inspection report'))
    return out


def editorial_problems(r, root=ISO):
    bad = []
    for f, h, what in editorial_files(r):
        q = os.path.join(root, f)
        if not os.path.isfile(q): bad.append((f'{what} missing', f))
        elif sha(q) != h: bad.append((f'{what} changed', f))
    c = r['isoscape']['commit']
    if subprocess.run(['git', '-C', root, 'cat-file', '-e', c + '^{commit}'], capture_output=True).returncode != 0: bad.append(('commit not in repo', c))
    return bad


_CREATED = re.compile(rb'/CreationDate \(D:[^)]*\)|/ModDate \(D:[^)]*\)|/ID \[<[0-9A-Fa-f]*> ?<[0-9A-Fa-f]*>\]')


def same_pixels(a, b):
    """None if the two images decode to the same pixels, else a short difference."""
    from PIL import Image, ImageChops
    Image.MAX_IMAGE_PIXELS = None
    A, B = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    if A.size != B.size: return f'sizes differ: {A.size} and {B.size}'
    box = ImageChops.difference(A, B).getbbox()
    if box is None: return None
    hist = ImageChops.difference(A, B).convert('L').histogram()
    return f'{sum(hist[1:])} pixels differ (largest difference {max(i for i, n in enumerate(hist) if n)} of 255) within {list(box)}'


def compare(got, want, dpi=100):
    """(same, how) for a remade file against the recorded one: identical bytes; or, for a PDF,
    identical but for its creation date and ID (matplotlib stamps the time), else the same pixels
    when both are rasterized; for an image, the same pixels."""
    a, b = open(got, 'rb').read(), open(want, 'rb').read()
    if a == b: return True, 'identical bytes'
    if want.lower().endswith('.pdf'):
        if _CREATED.sub(b'', a) == _CREATED.sub(b'', b): return True, 'identical but for the PDF creation date'
        if not shutil.which('pdftoppm'): return False, 'PDF bytes differ and pdftoppm is not here to rasterize them'
        with tempfile.TemporaryDirectory() as t:
            for n, f in (('got', got), ('want', want)): subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-singlefile', f, os.path.join(t, n)], check=True)
            d = same_pixels(os.path.join(t, 'got.png'), os.path.join(t, 'want.png'))
        return (True, f'same pixels rasterized at {dpi} dpi (PDF bytes differ)') if d is None else (False, f'rasterized at {dpi} dpi: {d}')
    try: d = same_pixels(got, want)
    except Exception as e: return False, f'bytes differ ({e.__class__.__name__} decoding them)'
    return (True, 'same pixels (bytes differ)') if d is None else (False, d)


def missing_for(step, data):
    """What a step needs that is not here: a data folder, a file in it, a Python module, a program."""
    miss = []
    for name, need in (step.get('needs') or {}).items():
        root = data.get(name)
        if not root: miss.append(f'--data {name}=<folder>: {need.get("what", name)} ({need.get("where", "not in git")})'); continue
        if not os.path.isdir(root): miss.append(f'{name}: {root} is not a folder'); continue
        miss += [f'{name}: {f}' for f in need.get('files', []) if not os.path.isfile(os.path.join(root, f))]
        miss += [f'{name}: {f}/ (folder)' for f in need.get('dirs', []) if not os.path.isdir(os.path.join(root, f))]
    for m in step.get('modules', []):
        if subprocess.run([sys.executable, '-c', f'import {m}'], capture_output=True).returncode: miss.append(f'Python module {m}')
    miss += [f'program {p}' for p in step.get('programs', []) if not shutil.which(p)]
    return miss


def editorial_rebuild(r, data, root=ISO):
    """Remake each step of an editorial recipe in a scratch folder holding only the record's
    inputs (so nothing unrecorded is read from the repo), and compare what it makes with the
    recorded outputs. A step whose data or tools are not here is not run, and says what it lacks.
    -> {step: {result, ...}}"""
    res = {}
    for step in r['recipe'].get('steps', []):
        miss = missing_for(step, data)
        if miss: res[step['name']] = {'result': 'not run', 'missing': miss}; continue
        with tempfile.TemporaryDirectory(prefix='iso-ed-') as t:
            for f in r['inputs']:
                os.makedirs(os.path.dirname(os.path.join(t, f)), exist_ok=True); shutil.copy2(os.path.join(root, f), os.path.join(t, f))
            for x in [r['outputs']['print']] + r['outputs'].get('prints', []):   # a later step may read the recorded art
                os.makedirs(os.path.dirname(os.path.join(t, x['file'])), exist_ok=True); shutil.copy2(os.path.join(root, x['file']), os.path.join(t, x['file']))
            os.makedirs(os.path.join(t, 'out'), exist_ok=True)
            for d in step.get('mkdirs', []): os.makedirs(os.path.join(t, d), exist_ok=True)
            subs = dict(data, out=os.path.join(t, 'out'))
            cmd = [a.format(**subs) for a in step['run']]
            p = subprocess.run(cmd, cwd=t, capture_output=True, text=True)
            got = {'result': 'ran' if p.returncode == 0 else f'failed (exit {p.returncode})', 'files': {}}
            if p.returncode: got['stderr'] = p.stderr.strip().splitlines()[-5:]
            for made, want in step['makes'].items():
                q = os.path.join(t, made)
                if not os.path.isfile(q): got['files'][want] = {'same': False, 'how': 'not made'}; continue
                same, how = compare(q, os.path.join(root, want))
                got['files'][want] = {'same': same, 'how': how}
            ok = p.returncode == 0 and got['files'] and all(v['same'] for v in got['files'].values())
            got['result'] = 'reproduced' if ok else ('differs' if p.returncode == 0 else got['result'])
            if ok and step.get('needs'):   # the outside files that made it, now known to be the right ones
                got['data_sha256'] = {f'{n}/{f}': sha(os.path.join(data[n], f)) for n, need in step['needs'].items() for f in need.get('files', [])}
            res[step['name']] = got
    return res


def main_editorial(argv):
    ap = argparse.ArgumentParser(prog='check.py --editorial', description='check editorial records (released, not for sale): no store is read')
    ap.add_argument('--editorial', action='store_true', required=True)
    ap.add_argument('designs', nargs='*')
    ap.add_argument('--rebuild', action='store_true', help='remake each step of the recipe in a scratch folder and compare')
    ap.add_argument('--data', action='append', default=[], metavar='NAME=FOLDER', help='an outside data folder a step needs (the record names them)')
    a = ap.parse_args(argv)
    data = dict(x.split('=', 1) for x in a.data)
    index = json.load(open(os.path.join(REL, 'index.json')))
    keys = a.designs or [k for k, v in index.items() if v.get('kind') == EDITORIAL]
    fails = 0
    for k in keys:
        p = os.path.join(REL, k, index[k].get('record') or f"v{index[k]['current']}.json")
        r = json.load(open(p))
        if r.get('kind') != EDITORIAL: print(f'{k}: a store record; check it with check.py <store> {k}'); fails += 1; continue
        bad = editorial_problems(r)
        n = len(editorial_files(r))
        print(f"{k} v{r['version']} ({r['asset_version']}, editorial): " + (f'OK, {n} files match their hashes' if not bad else f'{len(bad)} problem(s): {bad[:5]}'), flush=True)
        if a.rebuild:
            if bad: print('  not rebuilt: the pinned files above must match first'); fails += 1; continue
            res = editorial_rebuild(r, data)
            r['reproduced'] = {'checked': time.strftime('%Y-%m-%d'), 'at_commit': subprocess.run(['git', '-C', ISO, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
                               'steps': res}
            json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
            for name, s in res.items():
                print(f'  {name}: {s["result"].upper() if s["result"] != "reproduced" else "reproduced"}')
                for m in s.get('missing', []): print(f'    missing: {m}')
                for f, v in s.get('files', {}).items(): print(f'    {"same" if v["same"] else "DIFFERS"}: {f}: {v["how"]}')
                for line in s.get('stderr', []): print(f'    {line}')
            if any(s['result'] != 'reproduced' for s in res.values()):
                print(f'  INCOMPLETE: {sum(s["result"] == "reproduced" for s in res.values())} of {len(res)} steps reproduced; the rest are listed above'); bad.append('rebuild')
        fails += bool(bad)
    sys.exit(1 if fails else 0)


def main():
    if '--editorial' in sys.argv[1:]: return main_editorial(sys.argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument('store'); ap.add_argument('designs', nargs='*'); ap.add_argument('--rebuild', action='store_true')
    ap.add_argument('--budget', type=float, default=1e9, help='seconds; stop between designs after this (rebuilds resume where they left off)')
    ap.add_argument('--again', action='store_true', help='rebuild designs already rebuilt')
    a = ap.parse_args()
    index = json.load(open(os.path.join(REL, 'index.json')))
    keep, fails, t0 = {}, 0, time.time()
    try:
        for k in a.designs or list(index):
            if time.time() - t0 > a.budget: print('OUT OF TIME: run again to continue'); break
            if index[k].get('kind') == EDITORIAL:   # in no store: check.py --editorial checks it
                if a.designs: print(f'{k}: editorial, not in the store; check it with check.py --editorial {k}')
                continue
            p = os.path.join(REL, k, index[k].get('record') or f"v{index[k]['current']}.json")
            r = json.load(open(p))
            bad = problems(a.store, r)
            av = r.get('asset_version')
            line = f"{k} v{r['version']}" + (f" ({av})" if av and av != f"{r['version']}.0.0" else '') + ': ' + ('OK' if not bad else f'{len(bad)} problem(s): {bad[:3]}')
            if a.rebuild and r.get('kind') in STAMPED and (a.again or 'restamped' not in r):
                ok, n = restamp(a.store, r, keep)
                r['restamped'] = {'files': n, 'matched': ok}
                json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
                line += f'; restamped {ok}/{n} files identical'
                if ok < n: bad.append('restamp')
            if a.rebuild and (a.again or 'reproduced' not in r):
                ok, n = rebuild(r, keep)
                r['reproduced'] = {'scenes': n, 'matched': ok}
                json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
                line += f'; rebuilt {ok}/{n} scenes identical'
                if ok < n: bad.append('rebuild')
            fails += bool(bad)
            print(line, flush=True)
    finally:
        for wt in keep.values():
            subprocess.run(['git', '-C', ISO, 'worktree', 'remove', '--force', wt], capture_output=True)
            shutil.rmtree(wt, ignore_errors=True)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
