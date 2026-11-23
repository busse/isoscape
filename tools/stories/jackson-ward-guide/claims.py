#!/usr/bin/env python3
"""The guide's claim list, for a fact check: every sentence the guide shows a reader, wherever it
is (the page's front matter and text, its alt texts, the text inside its pictures, the folded
sheet), with what kind of sentence it is and where it comes from.

    python3 tools/stories/jackson-ward-guide/claims.py OUT.csv

Kinds:
  story fact     a sentence about the ward's history, matched to the story sentence it comes from
                 (among the story's sentences that cite the same sources, or in the section it
                 links), with that sentence's sources
  picture note   what a picture or map shows and how it was made
  map fact       where to stand, what is in view, grid squares, bridges, street ends, exits,
                 landmarks, names on the maps and drawings: from OpenStreetMap as cached on its
                 date (vantage.json, orient.json) or the story's trace (history/jackson-ward.json)
  index          one row of the street index per kind, with its source
  about          who made the guide and from what
  navigation     headings, map pointers, the PDF and contact lines
The match is by word overlap and says its score; a person checks the rows (the `check` column is
left for them). Reads pages/jackson-ward-guide.md, pages/jackson-ward.md, vantage.json,
orient.json, pairs.json (the names on each drawing), map.py's key and credits, social.py's text
and fold.py's sheet.
"""
import csv
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from common import load  # noqa: E402

STOP = set('a an the of in and or to on at by for from with as is was were it its that this be are has had have which who '
           'their there then than into over under about after before not no'.split())


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1}


def plain(md):
    md = re.sub(r'\[\[([^\]]*?)\]\]', '', md)                    # citations [[...]]
    md = re.sub(r'!\[([^\]]*)\]\([^)]*\)', '', md)
    md = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', md)
    md = re.sub(r'[*_`>]', '', md)
    return re.sub(r'\s+', ' ', md).strip()


ABBR = re.compile(r'\b(St|Sr|Jr|Dr|vol|No|Ave|Pkwy|Rd|Pl|U\.S|[A-Z]|p|pp|Va|Mr|Mrs|ca|i\.e|e\.g)\.$')


def sentences(text):
    out, cur = [], ''
    for part in re.split(r'(?<=[.!?])\s+', text):
        cur = (cur + ' ' + part).strip()
        if ABBR.search(cur) or re.search(r'\d\.$', cur) and len(cur) < 4:
            continue
        out.append(cur)
        cur = ''
    if cur:
        out.append(cur)
    return [s for s in out if s]


def story_index():
    """The story's sentences with the source keys each cites and the section each is in."""
    src = open(os.path.join(ROOT, 'pages/jackson-ward.md')).read()
    body = src[src.index('\n# '):src.index('\n## Sources')] + src[src.index('\n## Corrections and changes'):]
    out, section = [], ''
    for para in re.split(r'\n\s*\n', body):
        if para.startswith('#'):
            section = re.sub(r'[^a-z0-9 -]', '', para.lstrip('# ').lower()).replace(' ', '-')
            continue
        keys = re.findall(r'\[([^\[\]]+?)\]\(#sources\)', para.replace('\n', ' '))
        for s in sentences(plain(para.replace('\n', ' '))):
            out.append(dict(text=s, section=section, keys=keys, w=words(s)))
    return out


def match(sentence, cites, sections, index):
    cand = [s for s in index if (cites and set(cites) & set(s['keys'])) or (sections and s['section'] in sections)] or index
    w = words(sentence)
    best = max(cand, key=lambda s: len(w & s['w']) / max(1, len(w)))
    return best, round(len(w & best['w']) / max(1, len(w)), 2)


# Rows whose kind the word-matching cannot tell, with a note for the checker: (start of the
# sentence, kind, note).
OVERRIDE = [
    ('The whole frame, north up', 'picture note', ''),
    ("Today's map shows that 2nd Street", 'map fact', 'OpenStreetMap (orient.json): North 2nd Street ends at the trench on each side; the story lists the seven streets without saying which end.'),
    ("Today's map shows that it ends on each side", 'map fact', 'OpenStreetMap (orient.json): Saint James Street ends at the trench, north and south sides.'),
    ('This guide takes no position', 'about', "The guide's own stance, as the story's \"This page takes no position\"."),
    ('As the story has it', 'navigation', ''),
    ('The trench is up to about 8 m deep between Brook Road', 'story fact', 'Story, "The ground before the trench": "... 8 m deep between Brook Road and Chamberlayne Parkway."'),
    ('People live in Gilpin Court today, and this guide describes it as homes', 'story fact', 'As the story ("it is drawn here as homes"), in the guide\'s words.'),
    ('Where the trench is now, the 1952 ground is an estimate', 'picture note', 'The story\'s own words on the ground ("The ground before the trench" and its captions).'),
    ('In the 1952 picture,', 'map fact', 'The 1952 stretches named on that drawing (pairs.json italic_1952), from the story\'s trace.'),
    ('Find a street you know', 'navigation', ''),
    ("Today's names are upright", 'picture note', 'labels.py rules.'),
    ('A tracing pass for them is planned', 'picture note', 'Board entry jackson-ward-navy-hill-streets (Not started).'),
    ('Jackson Ward in 1952 and today, with the streets named', 'picture note', ''),
    ('Its grid square', 'navigation', ''),
    ('The drawings show the same blocks', 'picture note', ''),
    ('The ten places to stand are on public sidewalks', 'map fact', 'vantage.json: each on an OSM sidewalk, checked against Gilpin Court and the crossing rules.'),
    ('Each place is on a public sidewalk', 'map fact', 'vantage.json (vantage.py): sidewalk ways, reachability in the graph of mapped sidewalks and crossings, Gilpin outline test.'),
    ('In Navy Hill, north of Leigh Street', 'picture note', 'The story (fix.md, board follow-up): the 1952 streets there were not read off the sheets; the planned pass is the board entry jackson-ward-navy-hill-streets.'),
    ('It lists ', 'index', 'Counts from orient.json.'),
    ('Chamberlayne Parkway is one of seven streets', 'story fact', ''),
    ('St. James Street is one of the seven streets', 'story fact', ''),
    ("Chamberlayne Avenue's run from Leigh Street", 'story fact', 'Story, "Corrections and changes", November 23, 2026.'),
    ('The story\'s 1925 and 1952 pictures were corrected', 'story fact', 'Story, "Corrections and changes", November 23, 2026.'),
    ('5th Street keeps its name', 'story fact', 'Story, "Corrections and changes", November 23, 2026.'),
]


def page_rows(index):
    page = open(os.path.join(ROOT, 'pages/jackson-ward-guide.md')).read()
    fm, body = page.split('\n---\n', 1)
    rows = []
    for k in ('title', 'deck', 'summary'):
        v = re.search(rf'^{k}: (.*)$', fm, re.M).group(1)
        rows.append(('front matter: ' + k, 'about' if k != 'title' else 'navigation', v, '', ''))
    section = ''
    body = body[:body.index('\n## Sources')]
    for para in re.split(r'\n\s*\n', body):
        p = para.strip()
        if not p or p.startswith(':::') and len(p) < 20:
            continue
        if p.startswith('|'):
            continue        # the street index: its rows are listed by index_rows, with their sources
        if p.startswith('#'):
            section = p.lstrip('# ')
            rows.append((f'heading', 'navigation', section, '', ''))
            continue
        for alt in re.findall(r'!\[([^\]]+)\]', p):
            rows.append((f'alt text ({section})', 'picture note', alt, '', ''))
        p = re.sub(r'^::: ?\w*.*$', '', p, flags=re.M)
        cites = re.findall(r'\[([^\[\]]+?)\]\(#sources\)', p.replace('\n', ' '))
        secs = re.findall(r'jackson-ward\.md#([a-z0-9-]+)', p)
        for s in sentences(plain(p.replace('\n', ' '))):
            rows.append((f'page ({section})', None, s, cites, secs))
    out = []
    V = load('vantage.json')
    way = {x for st in V['points'] for x in (st['where'], st['sees'])}
    for where, kind, s, cites, secs in rows:
        story, sources, score, note = '', '', '', ''
        for start, k, n in OVERRIDE:
            if s.startswith(start):
                kind, note = k, n
        if kind is None and where.startswith('page (About'):
            kind = 'about'
        if kind is None:
            if s.startswith(('Stand', 'Look')) or any(d in s for d in way) or re.match(r'^\| ', s) or re.match(r'^- \*\*\d', s):
                kind = 'map fact'
            elif where.startswith('page (Who keeps') or cites or secs and not re.search(r'picture|drawn|map|traced|pair|isoscape', s, re.I):
                kind = 'story fact'
            elif re.search(r'picture|drawn|map|traced|pair|disc|1952 above|dashed|outline|isoscape|lidar', s, re.I):
                kind = 'picture note'
            elif where.startswith('page (About'):
                kind = 'about'
            else:
                kind = 'navigation'
        if kind == 'story fact' or (kind == 'about' and (cites or secs)):
            best, score = match(s, cites, secs, index)
            story, sources = best['text'], '; '.join(dict.fromkeys(best['keys'])) or f'(story section {best["section"]})'
        elif kind == 'map fact':
            sources = f'OpenStreetMap as cached {V["osm_date"]} (vantage.json, orient.json)'
        out.append(dict(where=where, kind=kind, sentence=s, story=story, sources=sources, score=score, check=note))
    return out


def index_rows():
    O = load('orient.json')
    rows = []
    lost = {x['name']: x for x in O['lost']}
    for r in O['index']:
        for k in r['kinds']:
            src = ('history/jackson-ward.json (' + ', '.join(x['id'] for x in O['lost'] if x['name'] == r['name']) + ')'
                   if k.startswith('1952') else 'OpenStreetMap (orient.json)')
            rows.append(dict(where='street index', kind='index', sentence=f"{r['name']} | {r['grid']} | {k}", story='', sources=src, score=''))
    return rows


def image_rows():
    rows = []
    sys.path.insert(0, HERE)
    import pairs as P   # noqa: E402
    import map as M     # noqa: E402
    for key, place in P.PLACE.items():
        for word in ('1952', 'Today'):
            rows.append(dict(where='inside picture: pair label', kind='picture note', sentence=f'{word} {place}', story='', sources='OpenStreetMap names', score=''))
    rows.append(dict(where='inside picture: 1952 hatch label', kind='picture note', sentence=P.UNTRACED.replace('\n', ' '), story='(the story\'s own hatch label)', sources='views.untraced', score=''))
    rows.append(dict(where='inside picture: ward', kind='picture note', sentence='Jackson Ward, seen from the south, with the streets named', story='', sources='pairs.py', score=''))
    for kind, t in M.KEY:
        rows.append(dict(where='inside picture: map key', kind='picture note', sentence=t, story='', sources='map.py', score=''))
    for s in sentences(M.CREDIT) + sentences(M.TILE_NOTE):
        rows.append(dict(where='inside picture: map credits', kind='about', sentence=s, story='', sources='map.py', score=''))
    O = load('orient.json')
    for e in O['exits']:
        rows.append(dict(where='inside picture: maps', kind='map fact', sentence=e['label'], story='', sources=f"OpenStreetMap w{e['way']} junction:ref, destination", score=''))
    for b in O['bridges']:
        rows.append(dict(where='inside picture: maps', kind='map fact', sentence=b['name'] + ' bridge', story='', sources='OpenStreetMap ' + ', '.join(f'w{w}' for w in b['ways']), score=''))
    for m in O['landmarks']:
        rows.append(dict(where='inside picture: maps', kind='map fact', sentence=m['label'], story='', sources=f"OpenStreetMap w{m['id']} ({m['osm_name']})", score=''))
    pairs = load('pairs.json')
    for k, p in pairs.items():
        if p.get('named'):
            for yr, names in p['named'].items():
                rows.append(dict(where=f'inside picture: names on drawing {k}, {"1952" if yr == "1952" else "today"}', kind='map fact',
                                 sentence='; '.join(names), story='', sources='OpenStreetMap names; 1952 stretches from the story\'s trace (italic: ' + ', '.join(p.get('italic_1952', [])) + ')', score=''))
    soc = open(os.path.join(HERE, 'social.py')).read()
    for t in re.findall(r"\(\('([^']+)'|\('([^']+)', font", soc):
        for x in t:
            if x:
                rows.append(dict(where='inside picture: link preview', kind='about', sentence=x, story='', sources='social.py', score=''))
    return rows


def sheet_rows():
    import fold   # noqa: E402
    import datetime
    doc = fold.document(datetime.date.today())
    doc = re.sub(r'<svg.*?</svg>', '', doc, flags=re.S)
    doc = re.sub(r'<style>.*?</style>', '', doc, flags=re.S)
    rows = []
    for alt in re.findall(r'alt="([^"]+)"', doc):
        rows.append(dict(where='folded sheet: alt text', kind='picture note', sentence=html.unescape(alt), story='', sources='', score=''))
    for block in re.findall(r'<(?:p|h1|h2)[^>]*>(.*?)</(?:p|h1|h2)>', doc, re.S):
        t = html.unescape(re.sub(r'<[^>]+>', ' ', block))
        t = re.sub(r'\s+', ' ', t).strip()
        for s in sentences(t):
            kind = 'map fact' if re.match(r'^\d+ [A-F]\d', s) or 'sidewalk' in s else 'about'
            rows.append(dict(where='folded sheet', kind=kind, sentence=s, story='', sources='fold.py (vantage.json, map.py, the page\'s words)', score=''))
    return rows


def main():
    out = sys.argv[1]
    index = story_index()
    rows = page_rows(index) + index_rows() + image_rows() + sheet_rows()
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'where', 'kind', 'guide sentence', 'story sentence it comes from', 'sources', 'match score (word overlap)', 'check'])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r['where'], r['kind'], r['sentence'], r['story'], r['sources'], r['score'], r.get('check', '')])
    from collections import Counter
    print(out, len(rows), 'rows;', dict(Counter(r['kind'] for r in rows)))


if __name__ == '__main__':
    main()
