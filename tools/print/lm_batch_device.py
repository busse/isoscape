"""On the Mac shell: compose print + canvas files for every built landmark that has none yet.
python3 lm_batch_device.py <seconds> [slug...]  (named slugs are recomposed even if done)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lm_compose as M
T0 = time.time(); B = float(sys.argv[1]) if len(sys.argv) > 1 else 1e9
LM = os.path.expanduser('~/mnt/ISO-TEST/chrisbusse-store/landmarks')
OUT = os.path.expanduser('~/mnt/ISO-TEST/chrisbusse-store/print-files/landmarks')
SVG = os.path.expanduser('~/mnt/ISO-TEST/isoscape/out/landmarks')
L = {x[0]: x for x in json.load(open(os.path.join(LM, 'list.json')))}
# Tall mountain scenes: keep the whole scene, and take the panel from this share of the height.
OPTS = {'matterhorn': {'zoom': False}}
# Scenes taller than wide get a portrait (24x36) print and portrait canvases.
PORTRAIT = {'matterhorn'}
ONLY = set(sys.argv[2:])
built = set()
for f in ('status.json', 'status-0.json', 'status-1.json', 'status-r.json'):
    p = os.path.join(LM, f)
    if os.path.exists(p): built |= {k for k, v in json.load(open(p)).items() if v.get('built')}
for slug in L:
    if ONLY and slug not in ONLY: continue
    last = f'lm-{slug}_canvas-24x36.jpg' if slug in PORTRAIT else f'lm-{slug}_canvas-36x24.jpg'
    if slug not in built or (not ONLY and os.path.exists(os.path.join(OUT, last))): continue
    if time.time() - T0 > B: print('OUT OF TIME'); break
    t = time.time()
    credit = M.elevation_credit(os.path.join(os.path.dirname(SVG), '..', 'regions', f'lm-{slug}.json'))
    fn, size, dpi, q, b = M.make(slug, L[slug][1], L[slug][2], os.path.join(SVG, f'lm-{slug}.svg'), OUT, credit=credit, landscape=slug not in PORTRAIT, **OPTS.get(slug, {}))
    M.make_canvas(fn, OUT, f'lm-{slug}', portrait=slug in PORTRAIT)
    print('composed', slug, size, dpi, round(b / 1e6, 1), 'MB', round(time.time() - t), 's', flush=True)
