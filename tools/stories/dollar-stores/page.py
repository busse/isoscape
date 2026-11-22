#!/usr/bin/env python3
"""Write the dollar stores story page, pages/dollar-stores.md, from its source here (story.md).

    python3 tools/stories/dollar-stores/page.py

Every number comes from counts.json (written by counts.py from the committed results) and is
filled in where story.md says {{name}}; nothing else in the text types one. The pictures are
written by figures.py from the poster's PDF. Made with Claude.
"""
import argparse
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    c = json.load(open(os.path.join(HERE, 'counts.json')))
    c['date'] = a.date
    text = open(os.path.join(HERE, 'story.md')).read()
    for k, v in c.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    open(os.path.join(ROOT, 'pages/dollar-stores.md'), 'w').write(text)
    print('wrote pages/dollar-stores.md')


if __name__ == '__main__':
    main()
