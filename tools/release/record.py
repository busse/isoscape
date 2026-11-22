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
  * every output by SHA-256: the print file (every size's, when the catalog has a "prints" map)
    and its canvas files, with their Printful file IDs,
  * where it is sold and shown: Shopify product handles and IDs (the merged product, one per
    design, from state/merged.json, and any per-format products from state/shopify.json),
    mockup images, explorer view.

Run where the data and the store live (the Mac):
    python3 tools/release/record.py <store-dir> [design...] [--version N] [--note "..."]
With no designs, records every design in the store's catalog that has no record of its current
version yet. A redrawn design (catalog "version" N) gets a new v<N>.json; older ones are kept.
check.py verifies records, and with --rebuild remakes each scene from its record.

An editorial piece (released at final production, not for sale: no plate, no store) is recorded
from a spec instead of the store's catalog (README "Editorial pieces (not for sale)"):
    python3 tools/release/record.py --editorial releases/editorial/<design>.json --release
It writes releases/<design>/v<N>.json with kind "editorial", for_sale false and no store section.

Asset versions (README "Stages and the board"): a record stores the design's asset version, the
store catalog's "asset_version" (default N.0.0, N its "version"). A record whose asset version
raises MINOR within the same edition (3.0.0 -> 3.1.0: corrected art replacing an unsold edition's
files in place) is kind "revision", written as v3.1.json beside v3.json. It keeps the superseded
record's output hashes ("supersedes"), and is refused unless the board (catalog/pipeline.json)
says the design has 0 orders, counted within the last two days, and, when the design is on sale,
pages/changes.md has a line naming its plate and the revision (BSS·07 ... 3.1).
"""
import argparse, datetime, glob, hashlib, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board as BOARD  # noqa: E402
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


def from_cutaway(key, d):
    """A cutaway sheet (tools/cutaway/sheet.py --print): its spec in cutaways/ names the design.
    Its scenes are the region's cutaway, every flat section the sheet draws (its own and a
    `crossSection`, or each region in `sections`; each written by its region's build), and the
    sheet SVG composed from them (frozen, not rebuilt: sheet.py makes it again from them). An
    `inset`'s cached map extract and context.py are inputs. (Records before November 18, 2026
    pinned only the region's own section: MSS-01's v1 lacks its shed section.)"""
    for sp in sorted(glob.glob(os.path.join(ISO, 'cutaways', '*.json'))):
        C = json.load(open(sp))
        if C.get('design') != key: continue
        name = os.path.splitext(os.path.basename(sp))[0]
        region, year = C['region'], C['year']
        bdir = os.path.join(ISO, 'out', 'cutaways', 'build')
        build = os.path.join(bdir, f'{region}-{year}')
        # Every flat section the sheet draws, as sheet.py lays them out: a spec's `sections` list,
        # else the region's own section and any `crossSection` (each region's build writes it).
        secs = [x['region'] for x in C['sections']] if C.get('sections') else [region] + ([C['crossSection']['region']] if C.get('crossSection') else [])
        scenes = [scene(region, year, build + '.svg')]
        scenes += [dict(scene(r, year, os.path.join(bdir, f'{r}-{year}-section.svg')), output='-section') for r in secs]
        scenes += [scene(None, None, os.path.join(ISO, 'out', 'cutaways', f'{name}-sheet.svg'))]
        log_p = os.path.join(ISO, 'out', 'cutaways', 'print', 'prints.json')
        log = json.load(open(log_p)) if os.path.exists(log_p) else {}
        recipe = {'tool': 'tools/cutaway/sheet.py',
                  'run': [f'python3 tools/cutaway/sheet.py cutaways/{name}.json --print   # where data/ is cached; out/cutaways/print/',
                          f'python3 tools/release/remake.py {key} && python3 tools/cutaway/sheet.py cutaways/{name}.json --no-build --print   # from the frozen scenes'],
                  'block': log.get('info'), 'files': log.get('files'), 'tools_at_printing': log.get('tools'),
                  'copied': 'out/cutaways/print/<file> is copied unchanged to the store\'s print_dir'}
        inputs = {rel(sp): sha(sp)}
        for f in ('tools/cutaway/sheet.py', 'tools/print/titleblock.py', 'tools/release/stamp.py', 'catalog/plates.json'):
            inputs[f] = sha(os.path.join(ISO, f))
        if C.get('inset'):    # the context map: its cached extract and the tool that draws it
            for f in (C['inset']['context'], 'tools/cutaway/context.py'):
                inputs[f] = sha(os.path.join(ISO, f))
        return 'cutaway', recipe, scenes, inputs
    return None


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
        scenes.append(scene(m['region'], (m.get('time') or {}).get('year'), os.path.join(ISO, 'out', 'builds', b, 'image.svg'), flags=m.get('flags', []), build_id=b,
                            made_at=(m.get('git') or {}).get('commit')))
    recipe = {'tool': 'tools/print/compose.py', 'run': [f'python3 tools/print/compose.py tools/print/spec.json out/builds <out> --only {key}'],
              'pinned': 'panels use the builds named in scenes[].build, not the newest'}
    return 'compose', recipe, scenes, {'tools/print/spec.json': sha(os.path.join(ISO, 'tools', 'print', 'spec.json'))}


def from_stamp(store, key, d):
    """A version made by stamping the title block on the previous version's files (stamp.py):
    the art, its scenes and its data are the previous version's; the recipe is the stamp."""
    log_p = os.path.join(store, 'pipeline', 'state', 'stamps.json')
    log = json.load(open(log_p)) if os.path.exists(log_p) else {}
    asset = asset_of(d)
    mine = {f: v for f, v in log.items() if v['design'] == key and v['version'] == d.get('version', 1)
            and v.get('asset_version', f"{v['version']}.0.0") == asset}
    if not mine: return None
    if any(v.get('redraw') for v in mine.values()): return from_redraw(store, key, d, mine)
    base_v = d['version'] - 1
    base_p = os.path.join(REL, key, d.get('_previous') or f'v{base_v}.json')   # a re-stamp (PATCH): this edition's record
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


def from_redraw(store, key, d, mine):
    """A redraw (stamp.py --base): new art composed from new builds (compose.py, canvas.py), then
    stamped as the next version. Its scenes and data are the new builds', not the previous
    version's; check.py rebuilds the scenes and stamps the base files again."""
    first = sorted(mine.values(), key=lambda v: v['base'])
    base_print = next((v for v in first if '_canvas-' not in v['base']), first[0])
    got = from_spec(key, d, os.path.getmtime(os.path.join(store, base_print['base'])))
    set_got = None if got else from_set(key, d)
    if got is None and set_got is None: raise SystemExit(f'{key}: a redraw is recorded only for a design in tools/print/spec.json or a set')
    _, made, scenes, inputs = got or set_got
    tools = base_print['tools']
    now = {f: sha(os.path.join(ISO, f)) for f in tools}
    base_dir = os.path.dirname(base_print['base'])
    canvas = sorted((v for v in mine.values() if '_canvas-' in v['base']), key=lambda v: v['base'])
    sizes = ' '.join(re.search(r'_canvas-(\d+x\d+)\.jpg$', v['base']).group(1) for v in canvas)
    if got:
        run = [f'python3 tools/print/compose.py tools/print/spec.json out/builds <store>/{base_dir} --only {key}']
        if canvas: run.append(f'python3 tools/print/canvas.py <store>/{base_print["base"]} <store>/{base_dir}/canvas {sizes}')
    else:
        # A set's print (set.py menu|map|boxes, then canvas), copied unchanged into base_dir and
        # base_dir/canvas; the scenes are the set's, from out/sets/<set>/scenes.
        run = [f'{c}   # into out/sets/<set>/print (or --dir)' if ' prepare' not in c else c for c in made['run']]
        run.append(f'cp <set print>/{os.path.basename(base_print["base"])} <store>/{base_dir}/' + (f' && cp <set print>/canvas/<the {sizes} files> <store>/{base_dir}/canvas/' if canvas else ''))
    run.append(f'python3 tools/release/stamp.py <store> {key} --version {d["version"]} --base {base_dir}')
    recipe = {'tool': 'tools/release/stamp.py', 'run': run, 'redraw': True, 'base_kind': 'compose' if got else 'set',
              'previous_record': rel(os.path.join(REL, key, d.get('_previous') or f"v{d['version'] - 1}.json")) if d.get('_previous') or d['version'] > 1 else None,   # a new design's first version has none
              'pinned': made.get('pinned') or 'scenes are the set\'s scene SVGs below, by SHA-256',
              'block': base_print['info'],
              'files': {f: {'base': v['base'], 'base_sha256': v['base_sha256'], 'at': v['at']} for f, v in sorted(mine.items())},
              'tools_at_stamping': tools, 'tools_match_commit': tools == now}
    inputs = dict(inputs); inputs.update(tools)
    if set_got: inputs['tools/sets/set.py'] = sha(os.path.join(ISO, 'tools', 'sets', 'set.py'))
    if canvas and got: inputs['tools/print/canvas.py'] = sha(os.path.join(ISO, 'tools', 'print', 'canvas.py'))
    return 'redraw', recipe, scenes, inputs


def outputs_of(store, d, key):
    """(print file, other print files, canvas files): the catalog's "print", every other file of
    its "prints" map (one per size, when the text is sized for each), and its canvas files."""
    pdir = os.path.join(store, d.get('print_dir') or ('print-files/landmarks' if key.startswith('lm-') else 'print-files'))
    pfile = os.path.join(pdir, d['print'])
    others = sorted({os.path.join(pdir, f) for f in (d.get('prints') or {}).values()} - {pfile})
    cpat = (d.get('canvas') or '').replace('{w}', '*').replace('{h}', '*')
    canvas = (sorted(glob.glob(os.path.join(pdir, 'canvas', cpat))) + sorted(glob.glob(os.path.join(pdir, cpat)))) if cpat else []
    return pfile, others, canvas


def products_of(key, shop, merged):
    """The design's Shopify products: its merged product (one per design, every format and size)
    first, then any per-format products."""
    out = []
    m = (merged or {}).get(key)
    if m: out.append({'handle': m['handle'], 'id': m['id'], 'format': 'all (merged)', 'status': m.get('status'), 'variants': len(m.get('variants') or {})})
    out += [{'handle': h, 'id': v['id'], 'format': v['format'], 'status': v.get('status')} for h, v in shop.items() if v['design'] == key]
    return out


# ---- one record ---------------------------------------------------------------------------------

def record(store, key, d, files, shop, mocks, note=None, merged=None):
    pfile, others, canvas = outputs_of(store, d, key)
    made = os.path.getmtime(pfile) if os.path.exists(pfile) else 0
    st = from_stamp(store, key, d)
    redraw = bool(st) and st[0] == 'redraw'   # new art: its scenes and data are its own
    got = None if st else (from_cutaway(key, d) or from_set(key, d) or from_landmark(key, d) or from_spec(key, d, made))
    kind, recipe, scenes, inputs = st[:4] if st else got if got else ('unknown', {}, [], {})
    data = dict(st[4]) if st and not redraw else {}
    for s in ([] if st and not redraw else scenes):
        r = s.get('region')
        if not r or not os.path.exists(os.path.join(ISO, 'regions', f'{r}.json')): continue
        inputs.update(history_inputs(r))
        dd = data_dir(r)
        if os.path.basename(dd) in data or not os.path.isdir(dd): continue
        snap, fl = freeze(dd)
        data[os.path.basename(dd)] = {'snapshot': snap, 'files': fl}
    out = lambda p: {'file': rel(p) if p.startswith(ISO) else os.path.relpath(p, store), 'sha256': sha(p), 'bytes': os.path.getsize(p),
                     'printful_file_id': files.get(os.path.basename(p))} if os.path.exists(p) else {'file': os.path.basename(p), 'missing': True}
    prods = products_of(key, shop, merged)
    mk = {f: [m['url'] for m in (mocks.get(f'{key}|{f}') or {}).get('mockups', [])] for f in d.get('formats', [])}
    return {
        'design': key, 'title': d['title'], 'version': d.get('version', 1), 'asset_version': asset_of(d),
        'version_note': d.get('version_note'), 'recorded': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'provenance': 'recorded at release' if note == 'release' else 'reconstructed: recorded after release; check.py --rebuild confirms the scenes reproduce',
        'isoscape': commit(), 'kind': kind, 'recipe': recipe, 'scenes': scenes,
        'inputs': inputs, 'data': data,
        'outputs': dict({'print': out(pfile)}, **({'prints': [out(p) for p in others]} if others else {}), canvas=[out(c) for c in canvas]),
        'store': {'catalog': {k: v for k, v in d.items() if k not in ('blurb', 'blurb_html') and not k.startswith('_')}, 'products': prods, 'mockups': mk},
        'explorer': {'view': d.get('explore')},
    }


# ---- asset versions and revisions ----------------------------------------------------------------

def asset_of(d):
    """A catalog entry's asset version: its "asset_version", else <version>.0.0."""
    return d.get('asset_version') or f"{d.get('version', 1)}.0.0"


def record_name(asset):
    """v3.json for 3.0.0; v3.1.json for 3.1.0; v3.1.1.json for 3.1.1."""
    return BOARD.file_suffix(asset) + '.json'


def is_revision(asset, prev):
    """True when `asset` raises MINOR within the edition of the previous record (asset `prev`)."""
    if not prev: return False
    a, b = BOARD.parse(asset), BOARD.parse(prev)
    return a[0] == b[0] and a[1] > b[1]


def revision_gate(key, asset, items=None, changes=None, today=None):
    """Why a revision may not be recorded (None if it may): the edition must be unsold, as the
    board says from the store's counts, and an on-sale revision must be on the Changes page."""
    items = items if items is not None else BOARD.load()['items']
    e = items.get(key)
    if e is None: return f'{key} is not on the board (catalog/pipeline.json)'
    M, m = BOARD.parse(asset)[:2]
    if e.get('orders') != 0:
        return (f'{key}: the board says orders = {e.get("orders")!r}. A revision ({asset}) replaces an edition in place and is '
                f'only for an edition nobody has ordered. Run `python3 orders.py counts` in the store (on the Mac), then '
                f'`python3 tools/release/board.py orders <store-dir>`; if it has any order, make edition {M + 1} instead.')
    day = e.get('orders_counted')
    today = today or datetime.date.today()
    if not day or (today - datetime.date.fromisoformat(day)).days > 2:
        return f'{key}: orders were counted {day or "never"}; count them again (orders.py counts, board.py orders) before replacing files'
    if e.get('on_sale'):
        plate = (e.get('plate') or '').replace('-', '·')
        text = changes if changes is not None else open(os.path.join(ISO, 'pages', 'changes.md')).read()
        if not any(plate in line and f'{M}.{m}' in line for line in text.splitlines()):
            return f'{key} is on sale: add a dated line to pages/changes.md naming {plate} and revision {M}.{m} (what was corrected), then record'
    return None


# ---- editorial pieces: released, not for sale ---------------------------------------------------

def editorial(spec_p, release=False):
    """The record of an editorial piece (a poster for a story page, say): released at final
    production but in no store, so it has no plate, no title block, no products and no Printful
    files. Its spec (releases/editorial/<design>.json) names what the store would otherwise say:
    the recipe, the inputs, the outputs, the data kept outside git, and where the piece is shown.
    Every input and output is pinned by SHA-256, as in a store record."""
    S = json.load(open(spec_p))
    asset = S['asset_version']
    p = BOARD.parse(asset)
    if not p or p[3]: raise SystemExit(f"{S['design']}: asset version {asset!r}: a release is MAJOR.MINOR.PATCH, never a draft")
    if p[0] != S['version']: raise SystemExit(f"{S['design']}: asset version {asset} is not of edition {S['version']}")
    def pin(f):
        q = os.path.join(ISO, f)
        if not os.path.isfile(q): raise SystemExit(f"{S['design']}: {f} is not there; an editorial record pins only files in the repo")
        return {'file': f, 'sha256': sha(q), 'bytes': os.path.getsize(q)}
    inputs = {f: pin(f)['sha256'] for f in S['inputs']}
    inputs[rel(spec_p)] = sha(spec_p)
    outs = S['outputs']
    rep = S.get('inspection')
    return {
        'design': S['design'], 'title': S['title'], 'version': S['version'], 'asset_version': asset,
        'version_note': S.get('version_note'), 'recorded': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'provenance': 'recorded at release' if release else 'reconstructed: recorded after release',
        'isoscape': commit(), 'kind': 'editorial', 'for_sale': False,
        'recipe': S['recipe'], 'scenes': [], 'inputs': inputs, 'data': {},
        'external': S.get('external'),
        # 'print' is the art itself; 'prints' the same art in other files; 'derived' what was made from it.
        'outputs': {'print': pin(outs['print']), 'prints': [pin(f) for f in outs.get('prints', [])], 'canvas': [],
                    'derived': [pin(f) for f in outs.get('derived', [])]},
        'shown': S.get('shown'), 'explorer': {'view': None, 'page': (S.get('shown') or {}).get('explorer')},
        'inspection': rep and {'report': rep, 'sha256': sha(os.path.join(ISO, rep))},
        'notes': S.get('notes', []),
    }


def main_editorial(argv):
    ap = argparse.ArgumentParser(prog='record.py --editorial', description='record an editorial piece (released, not for sale) from its spec')
    ap.add_argument('--editorial', required=True, metavar='SPEC', help='releases/editorial/<design>.json')
    ap.add_argument('--release', action='store_true', help='this record is made at release time (not reconstructed)')
    ap.add_argument('--force', action='store_true', help='rewrite an existing record of the same version')
    a = ap.parse_args(argv)
    r = editorial(a.editorial, a.release)
    k = r['design']
    p = os.path.join(REL, k, record_name(r['asset_version']))
    index_p = os.path.join(REL, 'index.json')
    index = json.load(open(index_p)) if os.path.exists(index_p) else {}
    if index.get(k) and index[k].get('kind') != 'editorial':
        raise SystemExit(f'{k} has store records: once a piece is on sale it is recorded from the store (record.py <store>)')
    if os.path.exists(p) and not a.force: raise SystemExit(f'{rel(p)} exists (--force to rewrite it)')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
    index[k] = {'title': r['title'], 'current': r['version'], 'kind': 'editorial', 'for_sale': False, 'records': sorted(os.listdir(os.path.dirname(p)))}
    if r['asset_version'] != f"{r['version']}.0.0": index[k].update(asset_version=r['asset_version'], record=os.path.basename(p))
    json.dump(dict(sorted(index.items())), open(index_p, 'w'), indent=1, ensure_ascii=False)
    print('recorded', k, f"v{r['version']}", 'editorial', len(r['inputs']), 'inputs', 1 + len(r['outputs']['prints']) + len(r['outputs']['derived']), 'outputs')


def main():
    if any(x == '--editorial' or x.startswith('--editorial=') for x in sys.argv[1:]): return main_editorial(sys.argv[1:])
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
    mp = os.path.join(P, 'state', 'merged.json')
    merged = json.load(open(mp)) if os.path.exists(mp) else {}
    keys = a.designs or list(cat)
    index_p = os.path.join(REL, 'index.json')
    index = json.load(open(index_p)) if os.path.exists(index_p) else {}
    for k in keys:
        d = cat[k]; v = d.get('version', 1)
        asset = asset_of(d)
        if not BOARD.parse(asset) or BOARD.parse(asset)[3]: raise SystemExit(f'{k}: asset version {asset!r}: a release is MAJOR.MINOR.PATCH, never a draft')
        if BOARD.parse(asset)[0] != v: raise SystemExit(f'{k}: asset version {asset} is not of edition {v}')
        p = os.path.join(REL, k, record_name(asset))
        if os.path.exists(p) and not a.force: continue
        prev = index.get(k)
        prev_asset = prev and (prev.get('asset_version') or f"{prev['current']}.0.0")
        revision = prev_asset != asset and is_revision(asset, prev_asset)
        if revision:
            why = revision_gate(k, asset)
            if why: raise SystemExit('refusing a revision: ' + why)
        if prev and prev_asset != asset and BOARD.parse(prev_asset)[0] == v:   # a revision, or a re-stamp (PATCH), of this edition
            d = dict(d, _previous=prev.get('record') or f"v{prev['current']}.json")
        r = record(a.store, k, d, files, shop, mocks, 'release' if a.release else None, merged)
        if revision:
            old = json.load(open(os.path.join(REL, k, d['_previous'])))
            r['recipe']['made_as'] = r['kind']; r['kind'] = 'revision'
            r['supersedes'] = {'record': d['_previous'], 'asset_version': old.get('asset_version') or f"{old['version']}.0.0",
                               'outputs': [{'file': o['file'], 'sha256': o.get('sha256')} for o in [old['outputs']['print']] + old['outputs'].get('prints', []) + old['outputs']['canvas']]}
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(r, open(p, 'w'), indent=1, ensure_ascii=False)
        index[k] = {'title': d['title'], 'current': v, 'kind': r['kind'], 'records': sorted(os.listdir(os.path.dirname(p)))}
        if asset != f'{v}.0.0': index[k].update(asset_version=asset, record=os.path.basename(p))
        print('recorded', k, f'v{v}', r['kind'], len(r['scenes']), 'scenes', len(r['data']), 'data dirs', flush=True)
    json.dump(dict(sorted(index.items())), open(index_p, 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
