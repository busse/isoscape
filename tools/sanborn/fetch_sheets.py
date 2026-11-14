import json, sys, os, time, urllib.request
n, pct = sys.argv[1], sys.argv[2]
want = sys.argv[3:]
d = json.load(open(f'item_{n}.json'))
os.makedirs(f'img{pct}', exist_ok=True)
for f in d['resources'][0]['files']:
    jp2 = [x['url'] for x in f if x.get('mimetype') == 'image/jp2'][0]
    name = jp2.split('/')[-1][:-4]
    if want and not any(name.endswith(w) for w in want): continue
    iiif = [x['url'] for x in f if x.get('mimetype') == 'image/jpeg'][0].split('/full/')[0]
    out = f'img{pct}/{name}.jpg'
    if os.path.exists(out) and os.path.getsize(out) > 1000: continue
    for attempt in range(4):
        try:
            req = urllib.request.Request(f'{iiif}/full/pct:{pct}/0/default.jpg', headers={'User-Agent': 'isoscape/0.1'})
            data = urllib.request.urlopen(req, timeout=90).read()
            open(out, 'wb').write(data); print(out, len(data)); break
        except Exception as e:
            print('retry', name, e); time.sleep(3 * (attempt + 1))
    time.sleep(0.5)
