#!/usr/bin/env python3
"""Check release records (see record.py): that every pinned file is still there with the bytes
it was recorded with, and, with --rebuild, that every scene still comes out of its recorded
commit and frozen data byte for byte.

    python3 tools/release/check.py <store-dir> [design...] [--rebuild]

--rebuild checks out each recorded commit into a scratch worktree, points its data/ at the
frozen copies, builds each scene as recorded, and compares SHA-256. A scene that matches is
proof the design can be remade exactly; the check writes "reproduces" into the record. A
stamped version (kind "stamp", stamp.py) is also stamped again from its base files with the
recorded commit's tools, and every file must come out byte for byte ("restamped").
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
REL = os.path.join(ISO, 'releases')
# Scenes already rebuilt (commit, region, year, flags, frozen data) -> SHA-256, so a scene shared
# by many designs (every print of a set) is rebuilt once.
MEMO_P = os.path.join(ISO, 'data', '_releases', 'rebuilt.json')
MEMO = json.load(open(MEMO_P)) if os.path.exists(MEMO_P) else {}


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
        f = os.path.join(ISO, s.get('frozen') or '')
        if s.get('sha256') and (not s.get('frozen') or not os.path.exists(f) or sha(f) != s['sha256']): bad.append(('frozen scene missing or changed', s.get('frozen')))
    for f, v in ((r.get('recipe') or {}).get('files') or {}).items() if r.get('kind') == 'stamp' else []:
        q = os.path.join(store, v['base'])
        if not os.path.exists(q): bad.append(('stamp base missing', v['base']))
        elif sha(q) != v['base_sha256']: bad.append(('stamp base changed', v['base']))
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
        memo_key = json.dumps([c, s['region'], s.get('year'), s.get('flags', []), sorted((k, v['snapshot']) for k, v in r['data'].items())])
        if memo_key in MEMO:
            s['reproduces'] = MEMO[memo_key] == s['sha256']; ok += s['reproduces']; continue
        wt = worktree(c, r, keep)
        with tempfile.TemporaryDirectory() as t:
            cmd = ['node', 'bin/isoscape.js', 'build', s['region'], '--no-archive', '--out', t] + (['--year', str(s['year'])] if s.get('year') is not None else []) + s.get('flags', [])
            subprocess.run(cmd, cwd=wt, capture_output=True)
            out = os.path.join(t, (f"{s['region']}-{s['year']}" if s.get('year') is not None else s['region']) + '.svg')
            got = sha(out) if os.path.exists(out) else None
        MEMO[memo_key] = got
        json.dump(MEMO, open(MEMO_P, 'w'))
        s['reproduces'] = got == s['sha256']
        ok += s['reproduces']
    return ok, n


def restamp(store, r, keep):
    """(matched, total) files of a stamped version made again from their base files with the
    recorded commit's stamp.py and title block, compared by SHA-256."""
    files = r['recipe']['files']; outs = {os.path.basename(o['file']): o for o in [r['outputs']['print']] + r['outputs']['canvas']}
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


def main():
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
            p = os.path.join(REL, k, f"v{index[k]['current']}.json")
            r = json.load(open(p))
            bad = problems(a.store, r)
            line = f"{k} v{r['version']}: " + ('OK' if not bad else f'{len(bad)} problem(s): {bad[:3]}')
            if a.rebuild and r.get('kind') == 'stamp' and (a.again or 'restamped' not in r):
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
