#!/usr/bin/env python3
"""Put a design's frozen scenes back where its recipe reads them, so the print can be remade
exactly as sold (see record.py). Then run the record's recipe; check.py compares the result.

    python3 tools/release/remake.py <design> [--version N] [--compose <store-dir>]

Scenes go back to the paths in the record (out/sets/<set>/scenes/, out/landmarks/,
out/builds/<id>/image.svg). --compose also runs the recipe's last steps for the kinds that are
one command (landmark, compose) into out/remake/<design>/ and reports whether the print file
matches the one sold, byte for byte.

To change a design rather than remake it, edit its inputs, build, look, and release it as the
next version: catalog "version", -vN print files, a dated entry in pages/changes.md, and a new
record (record.py --release).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('design'); ap.add_argument('--version', type=int); ap.add_argument('--compose')
    a = ap.parse_args()
    index = json.load(open(os.path.join(ISO, 'releases', 'index.json')))
    v = a.version or index[a.design]['current']
    r = json.load(open(os.path.join(ISO, 'releases', a.design, f'v{v}.json')))
    for s in r['scenes']:
        if not s.get('frozen'): print('no frozen scene for', s); continue
        dst = os.path.join(ISO, s['svg'])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) or sha(dst) != s['sha256']:
            shutil.copy2(os.path.join(ISO, s['frozen']), dst); print('restored', s['svg'])
    print('recipe:', *r['recipe'].get('run', []), sep='\n  ')
    if a.compose and r['kind'] in ('landmark', 'compose'):
        out = os.path.join(ISO, 'out', 'remake', a.design)
        os.makedirs(out, exist_ok=True)
        if r['kind'] == 'landmark':
            sys.path.insert(0, os.path.join(ISO, 'tools', 'print')); import lm_compose as M  # noqa: E402
            L = {x[0]: x for x in json.load(open(os.path.join(a.compose, 'landmarks', 'list.json')))}
            slug = a.design[3:]
            portrait = r['store']['catalog'].get('orientation') == 'vertical'
            credit = M.elevation_credit(os.path.join(ISO, 'regions', f'{a.design}.json'))
            opts = r['recipe'].get('composer_settings') or ({'zoom': False, 'trim': False} if slug == 'matterhorn' else {})
            M.make(slug, L[slug][1], L[slug][2], os.path.join(ISO, r['scenes'][0]['svg']), out, credit=credit, landscape=not portrait, **opts)
        else:
            # compose.py reads the newest build of each panel: point it at a builds dir holding only the pinned ones.
            pinned = os.path.join(out, 'builds')
            for s in r['scenes']:
                d = os.path.join(pinned, s['build']); os.makedirs(d, exist_ok=True)
                shutil.copy2(os.path.join(ISO, s['frozen']), os.path.join(d, 'image.svg'))
            subprocess.run(['python3', os.path.join(ISO, 'tools', 'print', 'compose.py'), os.path.join(ISO, 'tools', 'print', 'spec.json'), pinned, out, '--only', a.design], check=True)
        want = r['outputs']['print']
        got = os.path.join(out, os.path.basename(want['file']))
        if os.path.exists(got):
            print('print', 'IDENTICAL to the one sold' if sha(got) == want['sha256'] else 'differs from the one sold (compare by eye)', got)
        else:
            print('no print at', got, '; files:', os.listdir(out))


if __name__ == '__main__':
    main()
