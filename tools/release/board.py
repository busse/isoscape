#!/usr/bin/env python3
"""The production board (catalog/pipeline.json): one entry per design or piece of work, saying
which stage it is at, what version is on sale, and what it waits on. README "Stages and the
board" is the scheme it follows.

    python3 tools/release/board.py check                 the board against plates.json and releases/
    python3 tools/release/board.py show [--md]           a table by stage, "waiting on the owner" first
    python3 tools/release/board.py set <key> f=v ...     edit one entry (--new to add one)
    python3 tools/release/board.py page                  write pages/board.md (public: no private fields)
    python3 tools/release/board.py orders <store-dir>    take order counts from the store's state/orders.json

`set` values are JSON where they parse as JSON (3, true, null, ["a"]) and text otherwise;
`field+=value` appends to a list (`accepted_faults+="a fault @ 10,20,30,40"`), and
`planned_edition.reason=...` sets inside an object. A change of stage is logged in the entry.
Tests: cd tools/release && python3 -m unittest test_board
"""
import argparse, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
BOARD = os.path.join(ISO, 'catalog', 'pipeline.json')
PLATES = os.path.join(ISO, 'catalog', 'plates.json')
REL = os.path.join(ISO, 'releases')
PAGE = os.path.join(ISO, 'pages', 'board.md')

IMAGE = ['research', 'rough draft', 'working draft', 'final draft', 'final production']
STORY = ['research', 'outline', 'fact check', 'outside review', 'published']
STAGES = {'print': IMAGE, 'set box': IMAGE, 'set map': IMAGE, 'set menu': IMAGE, 'cutaway': IMAGE,
          'batch': IMAGE, 'research': ['research', 'done'], 'story': STORY}
ORDER = IMAGE + [s for s in STORY + ['done'] if s not in IMAGE]
# The "waiting on the owner" list, nearest to the store first.
URGENT = ['final draft', 'final production', 'working draft', 'rough draft', 'outside review', 'fact check', 'outline', 'research']
STATUS = ('active', 'on hold', 'blocked', 'backlog')
WAITING = ('owner', 'agent', 'nothing')
REASONS = ('factual correction', 'wall-visible fault', 'improvement')
# The round that needs the owner's say-so (README "Round budget"): the third fix round.
BUDGET = {'rough draft': 4, 'working draft': 4, 'final draft': 3}
SEMVER = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-(d|rc)(\d+))?$')
FIELDS = ('title', 'plate', 'kind', 'stage', 'status', 'asset_version', 'published_version', 'live_version',
          'on_sale', 'orders', 'rounds', 'waiting_on', 'decision', 'accepted_faults', 'planned_edition',
          'last_inspected', 'branch', 'worktree', 'links')
# Never written to the public page.
PRIVATE = ('orders', 'orders_counted', 'notes', 'links', 'branch', 'worktree', 'log', 'budget_note', 'last_inspected')


def load(p=BOARD): return json.load(open(p))


def save(b, p=BOARD):
    b['updated'] = datetime.date.today().isoformat()
    with open(p, 'w') as f:
        json.dump(b, f, indent=1, ensure_ascii=False); f.write('\n')


def parse(v):
    """(major, minor, patch, pre, n) of an asset version, or None."""
    m = SEMVER.match(v or '')
    return m and (int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5]) if m[5] else None)


def file_suffix(asset):
    """The -v part of a print file's name: 3.0.0 -> v3, 3.1.0 -> v3.1, 3.1.1 -> v3.1.1."""
    M, m, p, pre, _ = parse(asset)
    if pre: raise ValueError(f'{asset}: a draft is never a print file in the store')
    return f'v{M}' + (f'.{m}' if m or p else '') + (f'.{p}' if p else '')


def releases():
    p = os.path.join(REL, 'index.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def released_asset(r):
    """The asset version of a design's latest record (records before asset versions: N.0.0)."""
    return r.get('asset_version') or f"{r['current']}.0.0"


def problems(b, plates=None, index=None):
    plates = plates if plates is not None else load(PLATES)
    index = index if index is not None else releases()
    items, bad = b.get('items', {}), []
    by_plate = {p['plate']: p for p in plates['plates']}
    for p in plates['plates']:
        e = items.get(p['design'])
        if e is None: bad.append(f"{p['plate']}: no board entry for {p['design']}")
        elif e.get('plate') != p['plate']: bad.append(f"{p['design']}: plate {e.get('plate')} on the board, {p['plate']} in plates.json")
    for k, e in items.items():
        say = lambda m: bad.append(f'{k}: {m}')
        for f in FIELDS:
            if f not in e: say(f'missing field {f}')
        kind, stage = e.get('kind'), e.get('stage')
        if kind not in STAGES: say(f'unknown kind {kind!r}'); continue
        if stage not in STAGES[kind]: say(f'stage {stage!r} is not a stage of a {kind}')
        if e.get('status') not in STATUS: say(f'status {e.get("status")!r} not one of {STATUS}')
        if e.get('waiting_on') not in WAITING: say(f'waiting_on {e.get("waiting_on")!r} not one of {WAITING}')
        if e.get('waiting_on') == 'owner' and not (e.get('decision') or '').strip(): say('waits on the owner but names no decision')
        pl = e.get('plate')
        if pl and pl not in by_plate: say(f'plate {pl} is not in plates.json')
        elif pl and by_plate[pl]['design'] != k: say(f'plate {pl} belongs to {by_plate[pl]["design"]}')
        if not isinstance(e.get('rounds'), int) or e['rounds'] < 0: say('rounds must be a whole number')
        if not isinstance(e.get('on_sale'), bool): say('on_sale must be true or false')
        lv, pv = e.get('live_version'), e.get('published_version')
        if e.get('on_sale') != (lv is not None): say('on_sale and live_version disagree')
        o = e.get('orders')
        if not (o is None or o == 'unknown' or (isinstance(o, int) and not isinstance(o, bool) and o >= 0)): say(f'orders {o!r}: a count, "unknown" or null')
        if (lv is not None or pv is not None) and o is None: say('a published design needs orders: a count or "unknown"')
        r = index.get(k)
        if r and pv != r['current']: say(f'published_version {pv}, latest release record v{r["current"]}')
        if not r and pv is not None: say(f'published_version {pv} but no release record')
        if lv is not None and lv != pv: say(f'live version {lv} is not the published version {pv}')
        a = e.get('asset_version')
        if a is None:
            if stage in ('working draft', 'final draft', 'final production') and kind in ('print', 'set box', 'set map', 'set menu', 'cutaway'):
                say(f'a {stage} needs an asset version')
        elif not parse(a): say(f'asset version {a!r} is not MAJOR.MINOR.PATCH[-dN|-rcN]')
        else:
            M, m, _, pre, n = parse(a)
            want = {'working draft': 'd', 'final draft': 'rc', 'final production': None}.get(stage, 'none')
            if want == 'none': say(f'a {stage} has no asset version')
            elif pre != want: say(f'{a}: a {stage} is ' + (f'-{want}N' if want else 'a release, not a prerelease'))
            elif pre and n != e.get('rounds'): say(f'{a}: rounds {e.get("rounds")}, the {pre}-number says {n}')
            if stage == 'final production' and r and a != released_asset(r): say(f'{a}: latest release record is {released_asset(r)}')
            if stage == 'final production' and not r: say(f'{a}: final production but no release record')
            if pre:
                base = pv or 0
                if M == base + 1 and m == 0: pass                      # the next edition
                elif M == base and m > 0:                              # a revision of an unsold edition
                    if o != 0: say(f'{a}: a revision within edition {M} needs orders = 0 (it is {o!r}); an ordered edition is frozen')
                else: say(f'{a}: a draft is a prerelease of the next edition ({base + 1}.0.0-…) or of a revision of an unsold one')
        rounds, cap = e.get('rounds') or 0, BUDGET.get(stage)
        if cap and rounds >= cap and not (e.get('budget_note') or '').strip():
            say(f'round {rounds} of a {stage} needs the owner\'s say-so (budget_note)')
        if stage == 'final production' and rounds: say('a released piece has no rounds (start its next edition as a draft)')
        pe = e.get('planned_edition')
        if pe is not None:
            if not isinstance(pe, dict) or pe.get('reason') not in REASONS: say(f'planned edition reason must be one of {REASONS}')
            elif not pe.get('fixes'): say('planned edition lists no fixes')
        for f in e.get('accepted_faults') or []:
            if not isinstance(f, dict) or not (f.get('what') or '').strip(): say('an accepted fault needs a "what"')
            elif 'box' in f and not (isinstance(f['box'], list) and len(f['box']) == 4 and all(isinstance(x, int) for x in f['box'])):
                say(f'accepted fault box {f["box"]!r}: [x0, y0, x1, y1] in print pixels')
    return bad


# ---- show --------------------------------------------------------------------------------------

def group_key(e):
    return ORDER.index(e['stage']) if e['status'] == 'active' else len(ORDER) + STATUS.index(e['status'])


def ver(e):
    a = e.get('asset_version') or ''
    return a + (f" (live {e['live_version']})" if e.get('live_version') and not a.startswith(f"{e['live_version']}.") else '')


def row(k, e):
    return [e.get('plate') or '—', k, e['kind'], ver(e) or '—', 'yes' if e['on_sale'] else 'no',
            str(e['orders']) if e.get('orders') is not None else '—', str(e['rounds']), e['waiting_on'],
            (e.get('decision') or e.get('notes') or '') + (f" [planned: {e['planned_edition']['reason']}]" if e.get('planned_edition') else '')
            + (f" [{len(e['accepted_faults'])} accepted]" if e.get('accepted_faults') else '')]


HEAD = ['plate', 'key', 'kind', 'asset', 'sale', 'orders', 'rd', 'waits', 'decision / notes']


def collapse(rows_in):
    """Runs of on-hold rows of one plate series with nothing to say are one row (the landmarks)."""
    out, runs = [], {}
    for k, e in rows_in:
        series = (e.get('plate') or '')[:3]
        quiet = e['status'] != 'active' and not e.get('planned_edition') and not e.get('accepted_faults')
        if quiet and series: runs.setdefault((series, e['status'], e['kind'], e.get('decision')), []).append((k, e))
        else: out.append(row(k, e))
    for (series, status, kind, dec), rs in runs.items():
        if len(rs) < 4: out += [row(k, e) for k, e in rs]; continue
        plates = sorted(e['plate'] for _, e in rs)
        sale = sum(e['on_sale'] for _, e in rs)
        vs = sorted({e.get('asset_version') or '—' for _, e in rs})
        out.append([f'{plates[0]}…{plates[-1]}', f'({len(rs)} designs)', kind, '/'.join(vs) if len(vs) < 4 else 'various',
                    f'{sale} of {len(rs)}' if sale else 'no', 'unknown' if any(e.get('orders') == 'unknown' for _, e in rs) else '—',
                    '0', rs[0][1]['waiting_on'], dec or ''])
    return out


def table(rows_in, md):
    if md:
        esc = lambda s: s.replace('|', '\\|')
        return '\n'.join(['| ' + ' | '.join(HEAD) + ' |', '|' + '---|' * len(HEAD)] + ['| ' + ' | '.join(esc(c) for c in r) + ' |' for r in rows_in])
    w = [max(len(HEAD[i]), *(len(r[i]) for r in rows_in)) if i < len(HEAD) - 1 else 0 for i in range(len(HEAD))]
    return '\n'.join(('  '.join(c.ljust(w[i]) for i, c in enumerate(r))).rstrip() for r in [HEAD] + rows_in)


def group_name(g):
    return ORDER[g] if g < len(ORDER) else STATUS[g - len(ORDER)]


def show(b, md=False):
    items = b['items']
    out = []
    h = (lambda t, n=2: out.append('#' * n + ' ' + t)) if md else (lambda t, n=2: out.append(t.upper() if n == 2 else t))
    h('Production board', 1)
    out.append(f"{len(items)} entries, updated {b.get('updated')}. The scheme: README \"Stages and the board\".")
    counts = {}
    for e in items.values(): counts[group_name(group_key(e))] = counts.get(group_name(group_key(e)), 0) + 1
    out.append('By stage: ' + ', '.join(f'{n} {s}' for s, n in sorted(counts.items(), key=lambda x: (ORDER + list(STATUS)).index(x[0]))) + '.')
    out.append('')
    h('Waiting on the owner')
    for k, e in sorted(items.items(), key=lambda x: (URGENT.index(x[1]['stage']) if x[1]['stage'] in URGENT else 9, x[1].get('plate') or 'zzz', x[0])):
        if e['waiting_on'] == 'owner':
            out.append(f"- {e.get('plate') or k}{' (' + k + ')' if e.get('plate') else ''}: {e['decision']}")
    groups = {}
    for k, e in items.items(): groups.setdefault(group_key(e), []).append((k, e))
    for g in sorted(groups):
        out.append(''); h(f'{group_name(g)} ({len(groups[g])})')
        rs = sorted(groups[g], key=lambda x: (x[1].get('plate') or 'zzz', x[0]))
        out.append(table(collapse(rs), md))
    return '\n'.join(out) + '\n'


# ---- set ----------------------------------------------------------------------------------------

def value(s):
    try: return json.loads(s)
    except ValueError: return s


def fault(v):
    """An accepted fault from text: "what @ x0,y0,x1,y1" (the box optional)."""
    if isinstance(v, dict): return v
    m = re.match(r'^(.*?)\s*@\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$', v)
    return {'what': m[1], 'box': [int(m[i]) for i in range(2, 6)]} if m else {'what': v}


def set_fields(b, key, pairs, new=False):
    items = b.setdefault('items', {})
    if key not in items:
        if not new: raise SystemExit(f'{key}: no such entry (use --new to add one)')
        items[key] = {'title': key, 'plate': None, 'kind': 'print', 'stage': 'rough draft', 'status': 'active', 'asset_version': None,
                      'published_version': None, 'live_version': None, 'on_sale': False, 'orders': None, 'rounds': 0,
                      'waiting_on': 'agent', 'decision': None, 'accepted_faults': [], 'planned_edition': None,
                      'last_inspected': None, 'branch': None, 'worktree': None, 'links': []}
    e = items[key]
    before = e.get('stage')
    for pair in pairs:
        m = re.match(r'^([a-z_.]+)(\+?=)(.*)$', pair, re.S)
        if not m: raise SystemExit(f'{pair}: field=value or field+=value')
        path, op, v = m[1].split('.'), m[2], value(m[3])
        tgt = e
        for p in path[:-1]:
            if not isinstance(tgt.get(p), dict): tgt[p] = {}
            tgt = tgt[p]
        f = path[-1]
        if f == 'accepted_faults' and op == '+=': v = fault(v)
        if op == '+=': tgt.setdefault(f, []); tgt[f] = (tgt[f] or []) + (v if isinstance(v, list) else [v])
        else: tgt[f] = v
    if e.get('stage') != before:
        e.setdefault('log', []).append(f"{datetime.date.today().isoformat()}: {before} -> {e['stage']}")
    return e


# ---- page ----------------------------------------------------------------------------------------

def public(e):
    return {k: v for k, v in e.items() if k not in PRIVATE}


def page(b):
    items = {k: public(e) for k, e in b['items'].items()}
    L = ['---', 'title: Production board', 'order: 97',
         'summary: Where each map, print and story stands: its stage, what is on sale, and what is planned.',
         'unlisted: true', '---', '', '# Production board', '',
         'Every piece of work on isoscape, from a first look at a subject to a print for sale, moves through the '
         'same stages: rough draft, working draft, final draft and final production. A version number in a print\'s '
         'title block is given only at final production, and names an edition someone could own. Before that, work '
         'is counted in draft rounds (d1, d2) and release candidates (rc1, rc2). The rules are in '
         '[Changes](changes.md#how-versions-work-from-here) and [How it\'s made](how-its-made.md#stages-and-inspection).', '',
         f'This page is generated from the project\'s board (`catalog/pipeline.json`) by `tools/release/board.py page`. '
         f'It was last updated on {b.get("updated")}. The page and the board were set up with Claude.', '']
    counts = {}
    for e in items.values(): counts[group_name(group_key(e))] = counts.get(group_name(group_key(e)), 0) + 1
    L += ['| Stage | Entries |', '|---|---|'] + [f'| {s} | {n} |' for s, n in sorted(counts.items(), key=lambda x: (ORDER + list(STATUS)).index(x[0]))] + ['']
    wait = [(k, e) for k, e in sorted(items.items(), key=lambda x: (URGENT.index(x[1]['stage']) if x[1]['stage'] in URGENT else 9, x[1].get('plate') or 'zzz', x[0])) if e['waiting_on'] == 'owner']
    if wait:
        L += ['## Waiting on a decision', ''] + [f"- **{e['title']}**{' (' + e['plate'].replace('-', '·') + ')' if e.get('plate') else ''}: {e['decision']}" for k, e in wait] + ['']
    groups = {}
    for k, e in items.items(): groups.setdefault(group_key(e), []).append((k, e))
    for g in sorted(groups):
        name = group_name(g)
        L += [f'## {name[0].upper() + name[1:]}', '', '| Plate | Title | Kind | Version | On sale |', '|---|---|---|---|---|']
        rs = sorted(groups[g], key=lambda x: (x[1].get('plate') or 'zzz', x[0]))
        landmarks = [(k, e) for k, e in rs if (e.get('plate') or '')[:2] == 'LM' and e['status'] != 'active']
        for k, e in rs:
            if (k, e) in landmarks: continue
            v = e.get('asset_version') or '—'
            L.append(f"| {(e.get('plate') or '—').replace('-', '·')} | {e['title']} | {e['kind']} | {v} | {'yes, version ' + str(e['live_version']) if e['on_sale'] else 'no'} |")
        if landmarks:
            sets = sorted({e['plate'][:3] for _, e in landmarks})
            L.append(f"| {', '.join(s + '·…' for s in sets)} | {len(landmarks)} landmark prints | print | various | no |")
        L.append('')
    planned = [(k, e) for k, e in sorted(items.items(), key=lambda x: (x[1].get('plate') or 'zzz', x[0])) if e.get('planned_edition')]
    if planned:
        L += ['## Planned editions', '', 'Changes to published work are made in planned editions, each for a stated reason: '
              'a factual correction, a fault visible on the wall, or an improvement.', '']
        for k, e in planned:
            pe = e['planned_edition']
            L.append(f"- **{e['title']}**{' (' + e['plate'].replace('-', '·') + ')' if e.get('plate') else ''}, {pe['reason']}: " + '; '.join(pe['fixes']) + '.')
        L.append('')
    faults = [(k, e) for k, e in sorted(items.items(), key=lambda x: (x[1].get('plate') or 'zzz', x[0])) if e.get('accepted_faults')]
    if faults:
        L += ['## Known faults, accepted', '', 'Small faults seen only up close are listed here, so they are known and not '
              'reported again at each inspection. Any that matter are fixed in a planned edition.', '']
        for k, e in faults:
            L.append(f"- **{e['title']}**{' (' + e['plate'].replace('-', '·') + ')' if e.get('plate') else ''}: " + '; '.join(f['what'] for f in e['accepted_faults']) + '.')
        L.append('')
    return '\n'.join(L)


# ---- orders --------------------------------------------------------------------------------------

def take_orders(b, store):
    """Copy the store's counts (state/orders.json, written by the store's orders.py) onto the board."""
    p = os.path.join(store, 'pipeline', 'state', 'orders.json')
    if not os.path.exists(p): raise SystemExit(f'{p}: none yet; run `python3 orders.py counts` in the store\'s pipeline first')
    o = json.load(open(p))
    day = o['counted'][:10]
    n = 0
    for k, e in b['items'].items():
        if k in o['designs']:
            e['orders'], e['orders_counted'] = o['designs'][k], day; n += 1
    return n, day


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('cmd', choices=['check', 'show', 'set', 'page', 'orders'])
    ap.add_argument('rest', nargs='*'); ap.add_argument('--md', action='store_true'); ap.add_argument('--new', action='store_true')
    a = ap.parse_args(argv)
    b = load()
    if a.cmd == 'check':
        bad = problems(b)
        for x in bad: print(x)
        n = len(b['items'])
        print('ok' if not bad else f'{len(bad)} problems', f'({n} entries)')
        return 0 if not bad else 1
    if a.cmd == 'show':
        sys.stdout.write(show(b, a.md)); return 0
    if a.cmd == 'set':
        if not a.rest: raise SystemExit('set <key> field=value ...')
        set_fields(b, a.rest[0], a.rest[1:], a.new)
        bad = [x for x in problems(b) if x.startswith(a.rest[0] + ':')]
        save(b)
        for x in bad: print('warning:', x)
        print(json.dumps(b['items'][a.rest[0]], indent=1, ensure_ascii=False)); return 0
    if a.cmd == 'page':
        open(PAGE, 'w').write(page(b)); print('wrote', os.path.relpath(PAGE, ISO)); return 0
    if a.cmd == 'orders':
        if not a.rest: raise SystemExit('orders <store-dir>')
        n, day = take_orders(b, a.rest[0]); save(b); print(f'orders for {n} entries, counted {day}'); return 0


if __name__ == '__main__':
    sys.exit(main())
