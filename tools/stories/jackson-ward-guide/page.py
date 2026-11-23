#!/usr/bin/env python3
"""Write the Jackson Ward guide's page, pages/jackson-ward-guide.md, from its source here
(story.md). A draft: the page is unlisted and goes in no menu.

    python3 tools/stories/jackson-ward-guide/page.py [--date "November 23, 2026"]

Fills story.md's tokens from the guide's own data and the story's:
  {{where_N}}, {{sees_N}}   where to stand and what to look at, from route.json (route.py)
  {{pair_N}}                the stop's 1952-and-today figure (pairs.json, pairs.py), or why it has none
  {{km}} {{miles}} {{minutes}} {{pace}} {{back_m}} {{back_ft}}   the walk, from route.json
  {{paved}} {{corridor}}    the count, from tools/sanborn/jw/counts.json, as the story's page.py does
  {{sources}}               the story's own source entries (pages/jackson-ward.md, "Sources")
                            for every source the guide cites, word for word
Nothing else types a number. The images are written by map.py and pairs.py.
"""
import argparse
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

# Caption notes a pair carries, by stop key, each from the story (its captions and "How we know").
NOTES = {
    'second-trench': 'Inside today\'s trench the 1952 ground is an estimate, about ±2 m in its middle.',
    'sixth-mount-zion': 'Inside today\'s trench the 1952 ground is an estimate.',
    'chamberlayne-bridge': 'Inside today\'s trench the 1952 ground is an estimate; at its ends the error may be 3 to 4 m or more.',
    'gilpin-edge': 'In 1952 Gilpin Court is drawn in the sheet\'s own colors, green and blue, though the sheet labels its buildings brick-faced.',
    'bates-street': 'Hatched blocks are where no building was traced from the 1952 sheets; only buildings standing today are drawn there, and the picture should not be read as showing those blocks empty.',
    'first-bridge': 'Inside today\'s trench the 1952 ground is an estimate. Hatched blocks are where no building was traced.',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    route = json.load(open(os.path.join(HERE, 'route.json')))
    pairs = json.load(open(os.path.join(HERE, 'pairs.json')))
    counts = json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counts.json')))
    text = open(os.path.join(HERE, 'story.md')).read()
    t = route['total_m']
    tokens = {'date': a.date, 'km': f'{t / 1000:.1f}', 'miles': f'{t / 1609.344:.1f}',
              'minutes': round(t / route['walk_m_per_min'] / 5) * 5, 'pace': route['walk_m_per_min'],
              'back_m': int(round(route['last_to_first_m'], -1)), 'back_ft': int(round(route['last_to_first_m'] / 0.3048, -2)),
              'paved': counts['paved']['buildings'], 'corridor': counts['corridor']['buildings']}
    for st in route['stops']:
        n = st['n']
        tokens[f'where_{n}'] = st['where']
        tokens[f'sees_{n}'] = st['sees']
        p = pairs[str(n)]
        if p['file']:
            note = NOTES.get(st['key'], '')
            tokens[f'pair_{n}'] = (
                '::: figure\n'
                f'![Stop {n}, {st["title"]}, drawn from the south: the same blocks in 1952 (top) and today (bottom), with the stop\'s number where you stand]({p["file"]})\n\n'
                f'Stop {n} in 1952 (top) and today (bottom), seen from the south. The number is where you stand. {note}'.rstrip() + '\n:::')
        else:
            tokens[f'pair_{n}'] = f'*No 1952-and-today picture for this stop.* {p["why"]}'
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
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md: ' + re.search(r'\{\{[^}]+\}\}', text).group(0)
    # the guide's own copy rules
    assert '—' not in text, 'an em dash'
    assert not re.search(r'\bby hand\b|hand-drawn', text, re.I)
    open(os.path.join(ROOT, 'pages/jackson-ward-guide.md'), 'w').write(text)
    print('wrote pages/jackson-ward-guide.md;', len(cited), 'sources cited')


if __name__ == '__main__':
    main()
