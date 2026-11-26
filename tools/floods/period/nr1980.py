"""The 1980 survey in the National Register nomination of the Shockoe Valley and Tobacco Row
Historic District (VLR 1981, NRHP 1983, NRIS 83003308) as a check on the photographs: every
address it lists with a building and a date, matched to today's OSM buildings by their address
(addr:housenumber and addr:street).

    python3 tools/floods/period/nr1980.py <out.json>

Downloads the nomination (public, no login; 30.8 MB) to a temporary folder, checks its SHA-256,
reads its text layer and deletes it. An entry is "<number>[-<number>]: <description> ... <date>";
its core date is the earliest year in it (a remodeling or a new front is later). A building the
survey lists with a core date before 1969 stood through 1969 and 1972 (unless the entry says it
was moved or rebuilt). A lot the survey lists as vacant says nothing about 1972.

Output: {osm id: {address, built, entry}} for today's buildings whose address the survey lists.
"""
import hashlib, json, os, re, shutil, sys, tempfile, urllib.request

URL = 'https://npgallery.nps.gov/GetAsset/2f9dd6b2-9d0e-4544-89d4-7071fc6d0063'
SHA = '873719264540c43993e0fa4620121d06da61720a9640e308723ec02c373269eb'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STREET = re.compile(r'^\s*((?:EAST|NORTH|SOUTH)\s+[0-9A-Za-z]+|MAIN|DOCK|CRANE|PEAR|AMBLER)\s+STREET(?:\s*\(continued\))?\s*$')
ENTRY = re.compile(r'^\s*(\d{2,4})(?:\s*-\s*(\d{1,4}))?\s*(?:,?\s*(?:extension|addition)[^:;]*|\([^)]*\)?)?\s*[:;]')


def norm_street(s):
    s = s.upper().replace('  ', ' ')
    w = s.split()
    d = {'EAST': 'East', 'NORTH': 'North', 'SOUTH': 'South'}
    if len(w) == 2:
        name = w[1].lower() if w[1][0].isdigit() else w[1].title()
        return f'{d[w[0]]} {name} Street'
    return f'{w[0].title()} Street'


def parse(text):
    out = {}
    street = None
    cur = None
    for line in text.splitlines():
        m = STREET.match(line)
        if m:
            street = norm_street(m.group(1))
            cur = None
            continue
        if street is None:
            continue
        e = ENTRY.match(line)
        if e:
            a = int(e.group(1))
            b = e.group(2)
            hi = a if b is None else int(str(a)[:len(str(a)) - len(b)] + b) if len(b) < len(str(a)) else int(b)
            cur = {'street': street, 'numbers': list(range(a, hi + 1)) if 0 <= hi - a <= 12 else [a], 'text': line.strip()}
            # A building's own entry wins over a range that spans its number.
            for n in cur['numbers']:
                if len(cur['numbers']) == 1 or (street, n) not in out:
                    out[(street, n)] = cur
            continue
        if cur is not None and len(cur['text']) < 600:
            cur['text'] += ' ' + line.strip()
    for v in out.values():
        body = re.split(r'[:;]', v['text'], maxsplit=1)[-1]  # not the address itself
        ys = [int(y) for y in re.findall(r'\b(1[789]\d\d)s?\b', body)]
        v['built'] = min(ys) if ys else None
    return out


def main(out_path):
    tmp = tempfile.mkdtemp(prefix='nr1980-')
    try:
        data = urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': 'isoscape-floods/1'}), timeout=300).read()
        if hashlib.sha256(data).hexdigest() != SHA:
            raise SystemExit('checksum differs from the recorded one')
        pdf = os.path.join(tmp, 'nr.pdf')
        open(pdf, 'wb').write(data)
        import fitz
        text = '\n'.join(p.get_text() for p in fitz.open(pdf))
    finally:
        shutil.rmtree(tmp)
    entries = parse(text)
    osm = json.load(open(os.path.join(ROOT, 'data', 'richmond-i195-rocketts', 'osm.json')))['elements']
    res = {}
    for el in osm:
        t = el.get('tags', {})
        if el['type'] not in ('way', 'relation') or 'building' not in t or 'addr:housenumber' not in t or 'addr:street' not in t:
            continue
        m = re.match(r'(\d+)', t['addr:housenumber'])
        if not m:
            continue
        st = t['addr:street'].replace('1st', '1st')
        key = (st, int(m.group(1)))
        e = entries.get(key)
        if e is None or e['built'] is None:
            continue
        idp = ('w' if el['type'] == 'way' else 'r') + str(el['id'])
        res[idp] = {'address': f"{t['addr:housenumber']} {t['addr:street']}", 'built': e['built'], 'entry': e['text'][:300]}
    json.dump(res, open(out_path, 'w'), indent=0)
    print(len(entries), 'survey entries with an address;', len(res), 'OSM buildings matched by address')


if __name__ == '__main__':
    main(*sys.argv[1:])
