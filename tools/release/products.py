#!/usr/bin/env python3
"""The pieces of each set that are on sale, for the explorer: isoscape.config.json `shop.products`,
the explorer view each piece is cut from -> its product page and the words of its link. The
content pages then show each place's (or stop's) print beside its "See it on the map", and the
map's prints beside "Open the map" (`printLinks` in src/social.ts).

    python3 tools/release/products.py <store-dir>            write shop.products
    python3 tools/release/products.py <store-dir> --check    exit 1 if it is out of date

Read from the store (<store-dir>/pipeline): catalog.json (each design's `explore`, the view it is
cut from) and state/merged.json (its product handle and status). Read here: catalog/pipeline.json
(the board), whose `on_sale` says what sells, and sets/*.json (a set's page and its noun, "place"
or "stop"). Only a set's boxes, map and framed map (kinds "set box", "set map", "set menu") that
the board has on sale and the store has active go in. Run it after anything goes on or off sale.
Tests: cd tools/release && python3 -m unittest test_products
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
CONFIG = os.path.join(ISO, 'isoscape.config.json')
BOARD = os.path.join(ISO, 'catalog', 'pipeline.json')
KINDS = ('set map', 'set menu', 'set box')   # in this order where two share a view


def label(kind, noun):
    if kind == 'set box': return f'Buy a print of this {noun} ↗'
    if kind == 'set map': return 'Buy a print of the map alone ↗'
    return f'Buy a print of the map with every {noun} ↗'


def sets_of(paths):
    """Each set's design-key prefix -> (its page slug, its noun)."""
    out = {}
    for p in paths:
        s = json.load(open(p))
        page = s.get('page') or {}
        out[s['slug'] + '-'] = (page.get('slug'), page.get('noun', 'place'))
    return out


def products(designs, merged, board, sets, shop_url):
    """The view -> [{url, label, design}] map: every set piece the board has on sale and the store
    has active, by the view its catalog entry names. Raises on two pieces of one kind at a view."""
    rows = []
    for k, d in designs.items():
        e = board.get(k) or {}
        if e.get('kind') not in KINDS or e.get('on_sale') is not True: continue
        m = merged.get(k) or {}
        view = d.get('explore')
        if not view or not m.get('handle') or m.get('status') != 'ACTIVE': continue
        prefix = next((p for p in sorted(sets, key=len, reverse=True) if k.startswith(p)), None)
        if prefix is None: continue
        rows.append((view, KINDS.index(e['kind']), k, {'url': shop_url.rstrip('/') + '/products/' + m['handle'],
                                                       'label': label(e['kind'], sets[prefix][1]), 'design': k}))
    out = {}
    for view, kind, k, p in sorted(rows, key=lambda r: (r[1] == 2, r[2].split('-0')[0], r[1], r[2])):
        if any(KINDS.index(board[q['design']]['kind']) == kind for q in out.get(view, [])):
            raise SystemExit(f'{k}: another {KINDS[kind]} on sale is cut from the same view {view}')
        out.setdefault(view, []).append(p)
    return out


def unlinked(prods, sets, pages_dir):
    """Pieces whose view no page of their set links to: they would show nowhere."""
    bad = []
    for view, ps in prods.items():
        for p in ps:
            prefix = next(q for q in sorted(sets, key=len, reverse=True) if p['design'].startswith(q))
            slug = sets[prefix][0]
            try: md = open(os.path.join(pages_dir, f'{slug}.md')).read()
            except (OSError, TypeError): md = ''
            if not re.search(r'\]\([^)]*#' + re.escape(view) + r'\)', md): bad.append(f"{p['design']}: pages/{slug}.md has no link to {view}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('store')
    ap.add_argument('--check', action='store_true', help='exit 1 if shop.products is out of date')
    a = ap.parse_args()
    P = os.path.join(a.store, 'pipeline')
    designs = json.load(open(os.path.join(P, 'catalog.json')))['designs']
    merged = json.load(open(os.path.join(P, 'state', 'merged.json')))
    board = json.load(open(BOARD))['items']
    sets = sets_of(sorted(glob.glob(os.path.join(ISO, 'sets', '*.json'))))
    text = open(CONFIG).read()
    cfg = json.loads(text)
    prods = products(designs, merged, board, sets, cfg['shop']['url'])
    for line in unlinked(prods, sets, os.path.join(ISO, 'pages')): print('warning:', line, file=sys.stderr)
    n = sum(len(v) for v in prods.values())
    if a.check:
        if cfg['shop'].get('products') != prods:
            have = {p['design'] for v in cfg['shop'].get('products', {}).values() for p in v}
            want = {p['design'] for v in prods.values() for p in v}
            print(f'shop.products is out of date: {len(want - have)} to add, {len(have - want)} to drop'
                  + (f" ({', '.join(sorted(have - want))})" if have - want else '') + '; run without --check')
            sys.exit(1)
        print(f'shop.products: {n} pieces, up to date')
        return
    cfg['shop']['products'] = prods
    open(CONFIG, 'w').write(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n')
    print(f'isoscape.config.json: shop.products, {n} pieces at {len(prods)} views')


if __name__ == '__main__':
    main()
