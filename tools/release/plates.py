#!/usr/bin/env python3
"""The plate register (catalog/plates.json): check it, list it, and give a design's title block.

    python3 tools/release/plates.py check [<store-dir>]   every plate unique and well formed; every
                                                          design in the store's catalog has one
    python3 tools/release/plates.py list [--csv]         the catalog as a text reference list
    python3 tools/release/plates.py info <design> [--version N] [--store <dir>]
                                                          the fields its title block prints

Plates are permanent: a redraw changes a design's version, never its plate, and a plate is never
reused. New designs get the next free number in their set (`next <SET>` prints it).
"""
import argparse, csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
REG = os.path.join(ISO, 'catalog', 'plates.json')
PLATE = re.compile(r'^[A-Z]{3}-(\d{2,3}|M)$')


def load():
    return json.load(open(REG))


def by_design(reg=None):
    reg = reg or load()
    return {p['design']: p for p in reg['plates']}


def dms(v, pos, neg):
    """Decimal degrees to three places (about 100 m): 37.534° N. (The print face has no prime.)"""
    return f'{abs(v):.3f}° {pos if v >= 0 else neg}'


def cutaway_of(design):
    """The cutaway sheet spec (cutaways/*.json) whose `design` this is, or None."""
    for sp in sorted(glob.glob(os.path.join(ISO, 'cutaways', '*.json'))):
        C = json.load(open(sp))
        if C.get('design') == design:
            return sp, C
    return None


def where(design):
    """(lon, lat, bearing) the design was drawn at: a cutaway's region, a set box's own point and
    scene, else the region of its first scene."""
    cut = cutaway_of(design)
    if cut:
        cfg = json.load(open(os.path.join(ISO, 'regions', f'{cut[1]["region"]}.json')))
        lon, lat = cfg['center']
        return lon, lat, cfg.get('bearing', 0)
    recs = sorted(glob.glob(os.path.join(ISO, 'releases', design, 'v*.json')), key=lambda p: int(re.findall(r'v(\d+)', p)[-1]))
    rec = json.load(open(recs[-1])) if recs else {}
    region = None
    for sp in glob.glob(os.path.join(ISO, 'sets', '*.json')):
        S = json.load(open(sp))
        if not design.startswith(S['slug'] + '-'): continue
        rest = design[len(S['slug']) + 1:]
        boxes = S['boxes'] if isinstance(S['boxes'], list) else json.load(open(os.path.join(ISO, S['boxes'])))
        boxes = boxes.get('stops', boxes) if isinstance(boxes, dict) else boxes
        m = re.match(r'(\d+)-', rest)
        b = next((b for b in boxes if m and b.get('n') == int(m.group(1))), None)
        region = (b or {}).get('region') or S['map']['region']
        cfg = json.load(open(os.path.join(ISO, 'regions', f'{region}.json')))
        lon, lat = (b or {}).get('at') or cfg['center']
        return lon, lat, cfg.get('bearing', 0)
    if not region:
        region = next((s['region'] for s in rec.get('scenes', []) if s.get('region')), None) or design
    cfg = json.load(open(os.path.join(ISO, 'regions', f'{region}.json')))
    lon, lat = cfg['center']
    return lon, lat, cfg.get('bearing', 0)


def info(design, version=None, drawn=None, reg=None):
    reg = reg or load()
    p = by_design(reg)[design]
    code = p['plate'].split('-')[0]
    s = next(s for s in reg['sets'] if s['code'] == code)
    col = next(c for c in reg['collections'] if c['id'] == s['collection'])
    lon, lat, bearing = where(design)
    out = {'collection': col['name'], 'set': s['name'], 'piece': p['piece'], 'plate': p['plate'],
           'version': str(version or p.get('version', 1)), 'drawn': str(drawn or 2026),
           'location': f'{dms(lat, "N", "S")} {dms(lon, "E", "W")}', 'facing': f'{round(bearing) % 360}°'}
    if p.get('kind'):           # only when the plate names one: older blocks stay as they were
        out['kind'] = p['kind']
    return out


def check(store=None):
    reg = load(); bad = []
    plates = [p['plate'] for p in reg['plates']]
    designs = [p['design'] for p in reg['plates']]
    codes = {s['code'] for s in reg['sets']}
    cols = {c['id'] for c in reg['collections']}
    bad += [f'duplicate plate {x}' for x in sorted({x for x in plates if plates.count(x) > 1})]
    bad += [f'duplicate design {x}' for x in sorted({x for x in designs if designs.count(x) > 1})]
    bad += [f'malformed plate {x}' for x in plates if not PLATE.match(x)]
    bad += [f'unknown set in {x}' for x in plates if x.split('-')[0] not in codes]
    bad += [f'set {s["code"]} in unknown collection' for s in reg['sets'] if s['collection'] not in cols]
    bad += [f'empty or malformed kind in {p["plate"]}' for p in reg['plates'] if 'kind' in p and (not isinstance(p['kind'], str) or not p['kind'].strip() or len(p['kind']) > 24)]
    if store:
        cat = json.load(open(os.path.join(store, 'pipeline', 'catalog.json')))['designs']
        bad += [f'no plate for {k}' for k in cat if k not in designs]
    for b in bad: print(b)
    print('ok' if not bad else f'{len(bad)} problems', f'({len(plates)} plates)')
    return not bad


def sort_key(p):
    c, n = p['plate'].split('-')
    return (c, -1 if n == 'M' else int(n))


def rows(reg=None):
    reg = reg or load()
    sets = {s['code']: s for s in reg['sets']}
    cols = {c['id']: c['name'] for c in reg['collections']}
    order = {c['id']: i for i, c in enumerate(reg['collections'])}
    setorder = {s['code']: i for i, s in enumerate(reg['sets'])}
    ps = sorted(reg['plates'], key=lambda p: (order[sets[p['plate'][:3]]['collection']], setorder[p['plate'][:3]], sort_key(p)[1] if sort_key(p)[1] >= 0 else 999))
    for p in ps:
        s = sets[p['plate'][:3]]
        yield {'plate': p['plate'].replace('-', '·'), 'title': p['title'], 'piece': p['piece'], 'set': s['name'],
               'collection': cols[s['collection']], 'place': p.get('place') or '', 'design': p['design']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'list', 'info', 'next'])
    ap.add_argument('arg', nargs='?'); ap.add_argument('--store'); ap.add_argument('--version', type=int)
    ap.add_argument('--csv', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'check':
        sys.exit(0 if check(a.arg or a.store) else 1)
    if a.cmd == 'info':
        print(json.dumps(info(a.arg, a.version), ensure_ascii=False, indent=1))
    if a.cmd == 'next':
        nums = [int(p['plate'][4:]) for p in load()['plates'] if p['plate'].startswith(a.arg + '-') and p['plate'][4:].isdigit()]
        print(f'{a.arg}-{(max(nums) if nums else 0) + 1:02d}')
    if a.cmd == 'list':
        rs = list(rows())
        if a.csv:
            w = csv.DictWriter(sys.stdout, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
        else:
            cur = None
            for r in rs:
                head = f'{r["collection"]} › {r["set"]}'
                if head != cur:
                    print(f'\n{head}\n'); cur = head
                print(f'  {r["plate"]:<8} {r["title"]}' + (f'  ({r["piece"]})' if r['piece'] not in r['title'] else ''))


if __name__ == '__main__':
    main()
