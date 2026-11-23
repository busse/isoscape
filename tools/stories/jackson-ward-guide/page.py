#!/usr/bin/env python3
"""Write the Jackson Ward guide's page, pages/jackson-ward-guide.md, from its source here
(story.md). The page is unlisted and goes in no menu.

    python3 tools/stories/jackson-ward-guide/page.py [--date "November 23, 2026"]

Fills story.md's tokens from the guide's own data and the story's:
  {{stand_N}}               where to stand, its grid square, which way to look: vantage.json
  {{pair_N}}                the place's 1952-and-today figure (pairs.json), or why it has none
  {{in1952_N}}              which 1952 streets its picture names (pairs.json), as a plain note
  {{vantage_list}}          the ten places, one line each, with their squares
  {{tiles}}                 the six map tiles as figures, with their squares
  {{index}} {{index_counts}}  the street index (orient.json), as a table, and its counts
  {{label_rules}} {{navy_hill}}  how the drawings are labeled, and the known gap, said once
  {{osm_date}}              the OpenStreetMap date
  {{paved}} {{corridor}}    the count, from tools/sanborn/jw/counts.json, as the story's page.py does
  {{sources}}               the story's own source entries for every source the guide cites
Nothing else types a number. The images are written by map.py, pairs.py and social.py.
"""
import argparse
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

GROUND = ("Where the trench is now, the 1952 ground is an estimate, about ±2 m in its middle and "
          "3 to 4 m or more at its ends.")
NOTES = {
    'gilpin-edge': 'In 1952 Gilpin Court is drawn in the sheet\'s own colors, green and blue, though the sheet labels its buildings brick-faced.',
    'bates-street': 'Hatched blocks are where no building was traced from the 1952 sheets; only buildings standing today are drawn there, so the picture does not show those blocks as they were.',
    'fifth-bridge': 'Hatched blocks are where no building was traced from the 1952 sheets; only buildings standing today are drawn there.',
}
LABEL_RULES = ('Today\'s names are upright. In 1952 the streets the trench cut are named in italic, dark red, as on the maps; '
               'a street of today is named in 1952 only where it ran on the same line then, at the same place as in today\'s half.')
NAVY_HILL = ('In Navy Hill, north of Leigh Street and east of about 3rd Street, the 1952 streets were not read off the sheets, '
             'so the 1952 drawings there show today\'s street lines, some of them through houses the sheets print; those lines '
             'are not named in 1952. A tracing pass for them is planned.')


def plain_list(xs):
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def index_table(O):
    rows = ['| Street | Squares | What the maps show |', '|---|---|---|']
    for r in O['index']:
        what = '; '.join(r['kinds'])
        what = what[0].upper() + what[1:]
        rows.append(f"| {r['name']} | {r['grid']} | {what}. |")
    return '\n'.join(rows)


def index_counts(O):
    n = len(O['index'])
    bridge = sum(any(k.startswith('today, crosses') for k in r['kinds']) for r in O['index'])
    ends = sum(any('ends at the trench' in k for k in r['kinds']) for r in O['index'])
    cut = sum(any(k.startswith('1952, cut') for k in r['kinds']) for r in O['index'])
    under = sum(any(k.startswith('1952, the stretch') for k in r['kinds']) for r in O['index'])
    only52 = sum(all(k.startswith('1952') for k in r['kinds']) for r in O['index'])
    return (f'It lists {n} names. Today {bridge} streets cross the trench on a bridge and {ends} end at it; {cut} names '
            f'have a 1952 stretch read off the sheets that the trench cut, and {under} have a stretch under today\'s highway '
            f'joined across as the USGS map shows it. {only52} names are of 1952 only.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    pairs = json.load(open(os.path.join(HERE, 'pairs.json')))
    counts = json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counts.json')))
    text = open(os.path.join(HERE, 'story.md')).read()
    O = json.load(open(os.path.join(HERE, 'orient.json')))
    V = json.load(open(os.path.join(HERE, 'vantage.json')))
    tokens = {'date': a.date, 'osm_date': V['osm_date'], 'paved': counts['paved']['buildings'],
              'corridor': counts['corridor']['buildings'], 'label_rules': LABEL_RULES, 'navy_hill': NAVY_HILL,
              'index': index_table(O), 'index_counts': index_counts(O)}
    lines = []
    for v in V['points']:
        n = v['n']
        anchor = re.sub(r'[^a-z0-9 -]', '', f"{n}. {v['title']}".lower()).replace(' ', '-')
        lines.append(f"- **{n}**, square {v['square']}: [{v['title']}](#{anchor}).")
        tokens[f'stand_{n}'] = f"**Stand** {v['where']} (square {v['square']}). **Look** {v['sees']}."
        p = pairs[str(n)]
        if p['file']:
            note = NOTES.get(v['key'], '')
            tokens[f'pair_{n}'] = (
                '::: figure\n'
                f'![Place {n}, {v["title"]}, in Jackson Ward, drawn from the south: the same blocks in 1952 (top) and today (bottom), with the streets named in both and the number {n} where you stand]({p["file"]})\n\n'
                f'{v["title"]}, place {n}: 1952 above, today below, seen from the south, with the streets named. The numbered disc is where you stand. {GROUND} {note}'.rstrip() + '\n:::')
            from labels import short
            full = {short(x['name']): x['name'] for x in O['lost']}
            italic = [full.get(t, t) for t in p.get('italic_1952', [])]
            tokens[f'in1952_{n}'] = (f"In the 1952 picture, {plain_list(italic)} {'is' if len(italic) == 1 else 'are'} named where "
                                     f"{'it' if len(italic) == 1 else 'they'} ran before the trench."
                                     if italic else '')
        else:
            tokens[f'pair_{n}'] = f'*No 1952-and-today picture for this place.* {p["why"]}'
            tokens[f'in1952_{n}'] = ''
    tokens['vantage_list'] = '\n'.join(lines)
    import sys
    sys.path.insert(0, HERE)
    from map import tile_squares
    tiles = []
    for i in range(6):
        tiles.append('::: figure\n'
                     f'![Map {i + 1} of 6, north up: grid squares {tile_squares(i)} of Jackson Ward with every street named, today\'s upright and the 1952 streets the trench cut in italic, with bridges, street ends, exits, landmarks and the places to stand in these squares]'
                     f'(jackson-ward-guide-map-tile-{i + 1}.webp)\n\n'
                     f'Map {i + 1}: squares {tile_squares(i)}. The small plan at its top right shows where it lies.\n:::')
    tokens['tiles'] = '\n\n'.join(tiles)
    # the sources the guide cites, as the story lists them
    story = open(os.path.join(ROOT, 'pages/jackson-ward.md')).read()
    entries = {}
    for line in story[story.index('\n## Sources'):].split('\n'):
        m = re.match(r'- \*\*(.+?)\*\*:', line)
        if m:
            entries[m.group(1)] = line
    cited = []
    for k in re.findall(r'\[([^\[\]]+?)\]\(#sources\)', text):
        k = k.replace('\n', ' ')
        if k not in cited:
            cited.append(k)
    missing = [k for k in cited if k not in entries]
    assert not missing, f'cited but not in the story\'s sources: {missing}'
    tokens['sources'] = '\n'.join(entries[k] for k in sorted(cited, key=lambda k: list(entries).index(k)))
    for k, v in tokens.items():
        text = text.replace('{{' + k + '}}', str(v))
    text = re.sub(r'\n{3,}', '\n\n', text)
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md: ' + re.search(r'\{\{[^}]+\}\}', text).group(0)
    # the guide's own copy rules
    assert '—' not in text, 'an em dash'
    assert not re.search(r'\bdraft\b', re.sub(r'a draft\s+agreement', '', text.split('## Sources')[0]), re.I), 'draft wording on the page'
    assert not re.search(r'\bby hand\b|hand-drawn', text, re.I)
    open(os.path.join(ROOT, 'pages/jackson-ward-guide.md'), 'w').write(text)
    print('wrote pages/jackson-ward-guide.md;', len(cited), 'sources cited')


if __name__ == '__main__':
    main()
