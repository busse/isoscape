#!/usr/bin/env python3
"""Check release records (see record.py): that every pinned file is still there with the bytes
it was recorded with, and, with --rebuild, that every scene still comes out of its recorded
commit and frozen data byte for byte.

    python3 tools/release/check.py <store-dir> [design...] [--rebuild]

--rebuild checks out each recorded commit into a scratch worktree, points its data/ at the
frozen copies, builds each scene as recorded, and compares SHA-256. A scene that matches is
proof the design can be remade exactly; the check writes "reproduces" into the record.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
REL = os.path.join(ISO, 'releases')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def problems(store, r):
    bad = []
    files = json.load(open(os.path.join(store, 'pipeline', 'files.json')))
    for o in [r['outputs']['print']] + r['outputs']['canvas']:
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
        p = os.path.join(ISO, s.get('svg') or '')
        if s.get('sha256') and (not os.path.exists(p) or sha(p) != s['sha256']): bad.append(('scene svg differs from record (rebuild to confirm)', s.get('svg')))
    c = r['isoscape']['commit']
    if subprocess.run(['git', '-C', ISO, 'cat-file', '-e', c + '^{commit}']).returncode != 0: bad.append(('commit not in repo', c))
    return bad


def rebuild(r, keep):
    """(matched, total) scenes rebuilt from the record's commit and frozen data."""
    c = r['isoscape']['commit']
    wt = keep.get(c)
    if wt is None:
        wt = tempfile.mkdtemp(prefix='iso-rel-')
        subprocess.run(['git', '-C', ISO, 'worktree', 'add', '--detach', wt, c], check=True, capture_output=True)
        keep[c] = wt
    os.makedirs(os.path.join(wt, 'data'), exist_ok=True)
    for name, dd in r['data'].items():
        link = os.path.join(wt, 'data', name)
        if os.path.islink(link): os.unlink(link)
        os.symlink(os.path.join(ISO, dd['snapshot']), link)
    ok = n = 0
    for s in r['scenes']:
        if not s.get('region') or not s.get('sha256'): continue
        n += 1
        with tempfile.TemporaryDirectory() as t:
            cmd = ['node', 'bin/isoscape.js', 'build', s['region'], '--no-archive', '--out', t] + (['--year', str(s['year'])] if s.get('year') is not None else []) + s.get('flags', [])
            subprocess.run(cmd, cwd=wt, capture_output=True)
            out = os.path.join(t, (f"{s['region']}-{s['year']}" if s.get('year') is not None else s['region']) + '.svg')
            got = sha(out) if os.path.exists(out) else None
        s['reproduces'] = got == s['sha256']
        ok += s['reproduces']
    return ok, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('store'); ap.add_argument('designs', nargs='*'); ap.add_argument('--rebuild', action='store_true')
    a = ap.parse_args()
    index = json.load(open(os.path.join(REL, 'index.json')))
    keep, fails = {}, 0
    try:
        for k in a.designs or list(index):
            p = os.path.join(REL, k, f"v{index[k]['current']}.json")
            r = json.load(open(p))
            bad = problems(a.store, r)
            line = f"{k} v{r['version']}: " + ('OK' if not bad else f'{len(bad)} problem(s): {bad[:3]}')
            if a.rebuild:
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
