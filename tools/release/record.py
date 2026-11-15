#!/usr/bin/env python3
"""Release records: for every design for sale, everything needed to revisit it and remake it,
or to change it with confidence, kept in releases/<design>/v<N>.json and committed.

A record pins:
  * the isoscape commit the art was drawn with (or, for designs older than records, the commit
    their scenes were checked to reproduce at; see check.py),
  * the recipe: which tool made the print file and with what arguments,
  * every input by SHA-256: region files, history files, traced Sanborn files, the set or print
    spec, and the cached data each scene read (OSM, elevation, year built, footprints, cover),
    with a frozen copy of that data in data/_releases/<dir>@<hash>/ (fetch overwrites data/;
    the copy never changes),
  * every scene SVG the print was cut from, by SHA-256 (builds are deterministic: same code and
    same data give the same bytes),
  * every output by SHA-256: the print file and its canvas files, with their Printful file IDs,
  * where it is sold and shown: Shopify product handles and IDs, mockup images, explorer view.

Run where the data and the store live (the Mac):
    python3 tools/release/record.py <store-dir> [design...] [--version N] [--note "..."]
With no designs, records every design in the store's catalog that has no record of its current
version yet. A redrawn design (catalog "version" N) gets a new v<N>.json; older ones are kept.
check.py verifies records, and with --rebuild remakes each scene from its record.
"""
import argparse, datetime, glob, hashlib, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
REL = os.path.join(ISO, 'releases')
SNAP = os.path.join(ISO, 'data', '_releases')


def sha(path, cache={}):
    if path in cache: return cache[path]
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    cache[path] = h.hexdigest()
    return cache[path]


def rel(p): return os.path.relpath(p, ISO)


def git(*a): return subprocess.run(['git', '-C', ISO, *a], capture_output=True, text=True).stdout.strip()


def commit():
    dirty = [l for l in git('status', '--porcelain', '--untracked-files=no').splitlines() if not l.endswith('.pyc')]
    return {'commit': git('rev-parse', 'HEAD'), 'subject': git('log', '-1', '--format=%s'), 'dirty': bool(dirty)}


def region_cfg(r): return json.load(open(os.path.join(ISO, 'regions', f'{r}.json')))


def data_dir(r): return os.path.join(ISO, 'data', region_cfg(r).get('data', r))


def freeze(d):
    """A frozen copy of a data directory, named for the hash of its contents: (path, files)."""
    files = {}
    for p in sorted(glob.glob(os.path.join(d, '**', '*'), recursive=True)):
        if os.path.isfile(p) and '/osm-tiles/' not in p: files[os.path.relpath(p, d)] = sha(p)
    key = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]
    dst = os.path.join(SNAP, f'{os.path.basename(d)}@{key}')
    if not os.path.isdir(dst):
        os.makedirs(dst)
        for f in files:
            os.makedirs(os.path.dirname(os.path.join(dst, f)), exist_ok=True)
            shutil.copy2(os.path.join(d, f), os.path.join(dst, f))
    return rel(dst), files


def history_inputs(r):
    """The region file, and its history with the traced files the history names."""
    out = {rel(os.path.join(ISO, 'regions', f'{r}.json')): None}
    t = region_cfg(r).get('time')
    if t:
        hp = os.path.join(ISO, t['history']); out[t['history']] = None
        h = json.load(open(hp))
        lost = (h.get('sanborn') or {}).get('lost')
        for p in ([lost] if isinstance(lost, str) else lost or []): out[p] = None
    return {p: sha(os.path.join(ISO, p)) for p in out}


def scene(region, year, svg, flags=(), build_id=None, made_at=None):
    """A scene the print was cut from. Its SVG is frozen by hash (out/ is a work area), so the
    print can always be recomposed exactly; `commit` is the code it was drawn with, when known."""
    s = {'region': region, 'year': year, 'flags': list(flags), 'svg': rel(svg) if os.path.exists(svg) else svg,
         'sha256': sha(svg) if os.path.exists(svg) else None}
    if s['sha256']:
        dst = os.path.join(SNAP, 'scenes', s['sha256'] + '.svg')
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(svg, dst)
        s['frozen'] = rel(dst)
    if build_id: s['build'] = build_id
    if made_at: s['commit'] = made_at
    return s


# ---- the three ways a print file is made ----------------------------------------------------

def sets_by_slug():
    out = {}
    for p in glob.glob(os.path.join(ISO, 'sets', '*.json')):
        s = json.load(open(p)); out[s['slug']] = (os.path.splitext(os.path.basename(p))[0], s)
    return out


def from_set(key, d):
    for slug, (name, S) in sets_by_slug().items():
        if not key.startswith(slug + '-'): continue
        sys.path.insert(0, os.path.join(ISO, 'tools', 'sets')); import set as SETPY  # noqa: E402
        st = SETPY.Set(name)
        what = key[len(slug) + 1:]
        scenes = []
        fine = S.get('fine') or []
        for (region, year) in sorted({st.scene_of()} | {st.scene_of(b) for b in st.boxes}, key=str):
            scenes.append(scene(region, year, st.svg(region, year)))
            if fine: scenes.append(scene(region, year, st.svg(region, year, True), fine))
        step = 'menu' if what == 'menu' else 'map' if what == 'map' else 'boxes ' + what.split('-', 1)[1]
        recipe = {'tool': 'tools/sets/set.py', 'run': [f'python3 tools/sets/set.py {name} prepare   # where data/ is cached',
                  f'python3 tools/sets/set.py {name} {step}', f'python3 tools/sets/set.py {name} canvas'],
                  'renames': 'print files with a -vN suffix are the same output renamed for the store (see pages/changes.md)'}
        inputs = {f'sets/{name}.json': sha(os.path.join(ISO, 'sets', f'{name}.json'))}
        if isinstance(S.get('boxes'), str): inputs[S['boxes']] = sha(os.path.join(ISO, S['boxes']))
        pts = os.path.join(st.dir, 'points.json')
        if os.path.exists(pts): inputs[rel(pts)] = sha(pts)
        return 'set', recipe, scenes, inputs
    return None


def from_landmark(key, d):
    if not key.startswith('lm-'): return None
    slug = key[3:]
    svg = os.path.join(ISO, 'out', 'landmarks', f'{key}.svg')
    lp = json.load(open(os.path.join(ISO, 'tools', 'print', 'lm_params.json'))).get(slug, {}) if os.path.exists(os.path.join(ISO, 'tools', 'print', 'lm_params.json')) else {}
    recipe = {'tool': 'tools/print/lm_batch_device.py', 'run': [f'python3 tools/release/remake.py {key}   # restores the frozen scene',
              f'python3 tools/print/lm_batch_device.py 600 {slug}   # composes with tools/print/lm_params.json'],
              'composer_settings': lp.get('opts'), 'settings_checked': {k: lp.get(k) for k in ('mean_diff', 'match', 'checked_by_eye')}}
    return 'landmark', recipe, [scene(key, None, svg)], {f'tools/print/{f}': sha(os.path.join(ISO, 'tools', 'print', f)) for f in ('lm_compose.py', 'compose.py', 'lm_params.json')}


def from_spec(key, d, made):
    spec = json.load(open(os.path.join(ISO, 'tools', 'print', 'spec.json')))
    sd = spec['designs'].get(key)
    if sd is None: return None
    # compose.py takes each panel's newest archived build; pin the one that was newest when the
    # print file was made.
    builds = sorted(os.listdir(os.path.join(ISO, 'out', 'builds')))
    scenes = []
    for p in sd.get('panels', []) or [{'build': sd.get('build')}]:
        name = p.get('build')
        if not name: continue
        cands = [b for b in builds if re.match(r'\d{8}-\d{6}-' + re.escape(name) + '$', b)]
        when = datetime.datetime.utcfromtimestamp(made).strftime('%Y%m%d-%H%M%S')
        pick = [b for b in cands if b[:15] <= when] or cands
        if not pick: scenes.append({'build': None, 'name': name}); continue
        b = pick[-1]; m = json.load(open(os.path.join(ISO, 'out', 'builds', b, 'meta.json')))
        scenes.append(scene(m['region'], (m.get('time') or {}).get('year'), os.path.join(ISO, 'out', 'builds', b, 'image.svg'), build_id=b,
                            made_at=(m.get('git') or {}).get('commit')))
    recipe = {'tool': 'tools/print/compose.py', 'run': [f'python3 tools/print/compose.py tools/print/spec.json out/builds <out> --only {key}'],
              'pinned': 'panels use the builds named in scenes[].build, not the newest'}
    return 'compose', recipe, scenes, {'tools/print/spec.json': sha(os.path.join(ISO, 'tools', 'print', 'spec.json'))}


def from_stamp(store, key, d):
    """A version made by stamping the title block on the previous version's files (stamp.py):
    the art, its scenes and its data are the previous version's; the recipe is the stamp."""
    log_p = os.path.join(store, 'pipeline', 'state', 'stamps.json')
    log = json.load(open(log_p)) if os.path.exists(log_p) else {}
    mine = {f: v for f, v in log.items() if v['design'] == key and v['version'] == d.get('version', 1)}
    if not mine: return None
    base_v = d['version'] - 1
    base_p = os.path.join(REL, key, f'v{base_v}.json')
    base = json.load(open(base_p))
    scenes = [dict(s, commit=s.get('commit') or base['isoscape']['commit']) for s in base['scenes']]
    tools = next(iter(mine.values()))['tools']
    now = {f: sha(os.path.join(ISO, f)) for f in tools}
    recipe = {'tool': 'tools/release/stamp.py',
              'run': [f'python3 tools/release/stamp.py <store> {key} --version {d["version"]}   # from the v{base_v} files below'],
              'base_version': base_v, 'base_record': rel(base_p), 'base_kind': base['kind'],
              'block': next(iter(mine.values()))['info'],
              'files': {f: {'base': v['base'], 'base_sha256': v['base_sha256'], 'at': v['at']} for f, v in sorted(mine.items())},
              'tools_at_stamping': tools, 'tools_match_commit': tools == now}
    inputs = dict(tools); inputs[rel(base_p)] = sha(base_p)
    return 'stamp', recipe, scenes, inputs, base.get('data', {})


# ---- one record ---------------------------------------------------------------------------------

def record(store, key, d, files, shop, mocks, note=None):
    pdir = os.path.join(store, d.get('print_dir') or ('print-files/landmarks' if key.startswith('lm-') else 'print-files'))
    pfile = os.path.join(pdir, d['print'])
    cpat = (d.get('canvas') or '').replace('{w}', '*').replace('{h}', '*')
    canvas = (sorted(glob.glob(os.path.join(pdir, 'canvas', cpat))) + sorted(glob.glob(os.path.join(pdir, cpat)))) if cpat else []
    made = os.path.getmtime(pfile) if os.path.exists(pfile) else 0
    st = from_stamp(store, key, d)
    got = None if st else (from_set(key, d) or from_landmark(key, d) or from_spec(key, d, made))
    kind, recipe, scenes, inputs = st[:4] if st else got if got else ('unknown', {}, [], {})
    data = dict(st[4]) if st else {}
    for s in ([] if st else scenes):
        r = s.get('region')
        if not r or not os.path.exists(os.path.join(ISO, 'regions', f'{r}.json')): continue
        inputs.update(history_inputs(r))
        dd = data_dir(r)
        if os.path.basename(dd) in data or not os.path.isdir(dd): continue
        snap, fl = freeze(dd)
        data[os.path.basename(dd)] = {'snapshot': snap, 'files': fl}
    out = lambda p: {'file': rel(p) if p.startswith(ISO) else os.path.relpath(p, store), 'sha256': sha(p), 'bytes': os.path.getsize(p),
                     'printful_file_id': files.get(os.path.basename(p))} if os.path.exists(p) else {'file': os.path.basename(p), 'missing': True}
    prods = [{'handle': h, 'id': v['id'], 'format': v['format'], 'status': v.get('status')} for h, v in shop.items() if v['design'] == key]
    mk = {f: [m['url'] for m in (mocks.get(f'{key}|{f}') or {}).get('mockups', [])] for f in d.get('formats', [])}
    return {
        'design': key, 'title': d['title'], 'version': d.get('version', 1),
        'version_note': d.get('version_note'), 'recorded': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'provenance': 'recorded at release' if note == 'release' else 'reconstructed: recorded after release; check.py --rebuild confirms the scenes reproduce',
        'isoscape': commit(), 'kind': kind, 'recipe': recipe, 'scenes': scenes,
        'inputs': inputs, 'data': data,
        'outputs': {'print': out(pfile), 'canvas': [out(c) for c in canvas]},
        'store': {'catalog': {k: v for k, v in d.items() if k not in ('blurb', 'blurb_html')}, 'products': prods, 'mockups': mk},
        'explorer': {'view': d.get('explore')},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('store'); ap.add_argument('designs', nargs='*')
    ap.add_argument('--release', action='store_true', help='this record is made at release time (not reconstructed)')
    ap.add_argument('--force', action='store_true', help='rewrite an existing record of the same version')
    a = ap.parse_args()
    P = os.path.join(a.store, 'pipeline')
    cat = json.load(open(os.path.join(P, 'catalog.json')))['designs']
    files = json.load(open(os.path.join(P, 'files.json')))
    shop = json.load(open(os.path.join(P, 'state', 'shopify.json')))
    mocks = json.load(open(os.path.join(P, 'state', 'mockups.json')))
    keys = a.designs or list(cat)
    index_p = os.path.join(REL, 'index.json')
    index = json.load(open(index_p)) if os.path.exists(index_p) else {}
    for k in keys:
        d = cat[k]; v = d.get('version', 1)
        p = os.path.join(REL, k, f'v{v}.json')
        if os.path.exists(p) and not a.force: continue
        r = record(a.store, k, d, files, shop, mocks, 'release' if a.release else None)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
        index[k] = {'title': d['title'], 'current': v, 'kind': r['kind'], 'records': sorted(os.listdir(os.path.dirname(p)))}
        print('recorded', k, f'v{v}', r['kind'], len(r['scenes']), 'scenes', len(r['data']), 'data dirs', flush=True)
    json.dump(dict(sorted(index.items())), open(index_p, 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
