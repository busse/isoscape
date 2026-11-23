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
  wayfinding     where to stand, what to look at, directions, distances: from route.json
                 (route.py, OpenStreetMap as cached on its osm_date)
  about          who made the guide and from what
  navigation     headings, map pointers, the PDF and contact lines
The match is by word overlap and says its score; a person checks the rows (the `check` column is
left for them). Reads pages/jackson-ward-guide.md, pages/jackson-ward.md, route.json, pairs.py's
labels, map.py's key and credits, social.py's text and fold.py's sheet.
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
    body = src[src.index('\n# '):src.index('\n## Sources')]
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
    ('The whole walk, north up', 'picture note', ''),
    ("Today's map shows that 2nd Street", 'wayfinding', 'From OpenStreetMap (route.py): North 2nd Street ends at East Duval Street; the story lists the seven streets without saying which end.'),
    ('This guide takes no position', 'about', "The guide's own stance, as the story's \"This page takes no position\"."),
    ('As the story has it', 'navigation', ''),
    ('Where the trench is now, the 1952 ground is an estimate', 'picture note', 'The story\'s own words on the ground ("The ground before the trench" and its captions).'),
    ('The walk has eight stops', 'wayfinding', ''),
    ('It starts at Second and Leigh', 'wayfinding', ''),
    ('Every stop is on a public sidewalk', 'wayfinding', ''),
    ('The walk starts here', 'wayfinding', ''),
    ('The route keeps to mapped sidewalks', 'wayfinding', ''),
    ('The route and directions follow the sidewalks', 'wayfinding', 'The sentence flagged for the owner (keep or cut).'),
    ('Each stop starts with directions', 'navigation', ''),
    ('The trench is up to about 8 m deep between Brook Road', 'story fact', 'Story, "The ground before the trench": "... 8 m deep between Brook Road and Chamberlayne Parkway."'),
    ('People live in Gilpin Court today, and this guide describes it as homes', 'story fact', 'As the story ("it is drawn here as homes"), in the guide\'s words.'),
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
    route = load('route.json')
    way = {x for st in route['stops'] for x in (st['where'], st['sees'])} | {d for l in route['legs'] for d in l['directions']}
    for where, kind, s, cites, secs in rows:
        story, sources, score, note = '', '', '', ''
        for start, k, n in OVERRIDE:
            if s.startswith(start):
                kind, note = k, n
        if kind is None and where.startswith('page (About'):
            kind = 'about'
        if kind is None:
            if s.startswith(('Getting there', 'Stand', 'Look')) or any(d in s for d in way) or 'Walk ' in s or s.startswith('Cross '):
                kind = 'wayfinding'
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
        elif kind == 'wayfinding':
            sources = f'route.json (route.py; OpenStreetMap as cached {route["osm_date"]})'
        out.append(dict(where=where, kind=kind, sentence=s, story=story, sources=sources, score=score, check=note))
    return out


def image_rows():
    rows = []
    sys.path.insert(0, HERE)
    import pairs as P   # noqa: E402
    for key, place in P.PLACE.items():
        for word in ('1952', 'Today'):
            rows.append(dict(where='inside picture: pair label', kind='picture note', sentence=f'{word} {place}', story='', sources='OpenStreetMap names', score=''))
    rows.append(dict(where='inside picture: 1952 hatch label', kind='picture note', sentence=P.UNTRACED.replace('\n', ' '), story='(the story\'s own hatch label)', sources='views.untraced', score=''))
    src = open(os.path.join(HERE, 'map.py')).read()
    for m in re.finditer(r"\('(street|bridge|lost|highway|gilpin|route|stop|landmark)', f?'([^']+)'\)", src):
        rows.append(dict(where='inside picture: map key', kind='picture note', sentence=m.group(2), story='', sources='map.py', score=''))
    for m in re.finditer(r"credit = \(([^)]*?)\)\n", src, re.S):
        txt = ''.join(re.findall(r"f?'([^']*)'", m.group(1)))
        for s in sentences(txt):
            rows.append(dict(where='inside picture: map credits', kind='about', sentence=s, story='', sources='map.py', score=''))
    for t in ('The walk, north up. Numbers are the stops, in walking order.', 'North is up. The west and east maps overlap.',
              'The dashed frames are the west and east maps, which name more streets.', 'E. Bates St. (JXN Haus)',
              'Gilpin Court (RRHA public housing)', '200 m is about 2.5 minutes on foot'):
        rows.append(dict(where='inside picture: map text', kind='picture note' if 'JXN' not in t else 'story fact', sentence=t,
                         story='It opened on Bates Street in April 2026 with the JXN Haus, the project\'s headquarters (as the guide quotes it)' if 'JXN' in t else '',
                         sources='The Richmonder, April 2026; Richmond Magazine, May 2026' if 'JXN' in t else 'map.py', score=''))
    soc = open(os.path.join(HERE, 'social.py')).read()
    for t in re.findall(r"\(\('([^']+)'|\('([^']+)', font", soc):
        for x in t:
            if x:
                rows.append(dict(where='inside picture: link preview', kind='about', sentence=x, story='', sources='social.py', score=''))
    rows.append(dict(where='inside picture: link preview', kind='about', sentence='Eight stops on 2.6 miles of sidewalk. Seven of the places are shown as they were in 1952 and as they are today.', story='', sources='route.json; pairs.json', score=''))
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
            kind = 'wayfinding' if re.search(r'^(From stop|Walk|Cross|Stand|The walk starts|Look)', s) or 'sidewalk' in s else 'about'
            rows.append(dict(where='folded sheet', kind=kind, sentence=s, story='', sources='fold.py (route.json, the page\'s words)', score=''))
    return rows


def main():
    out = sys.argv[1]
    index = story_index()
    rows = page_rows(index) + image_rows() + sheet_rows()
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'where', 'kind', 'guide sentence', 'story sentence it comes from', 'sources', 'match score (word overlap)', 'check'])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r['where'], r['kind'], r['sentence'], r['story'], r['sources'], r['score'], r.get('check', '')])
    from collections import Counter
    print(out, len(rows), 'rows;', dict(Counter(r['kind'] for r in rows)))


if __name__ == '__main__':
    main()
