#!/usr/bin/env python3
"""Write the Jackson Ward story page, pages/jackson-ward.md, from its source here (story.md).

    python3 tools/stories/jackson-ward/page.py [--rough DIR]

The count's numbers come from one file, tools/sanborn/jw/counts.json, and are filled in where
story.md says {{paved}}, {{corridor}} and {{all}}; nothing else in the text types them. With
--rough, the region views (rough drafts, drawn with isoscape) are copied into pages/ as WebP,
1600 px wide, so the explorer page stays light. Run charts.py and timeline.ts for the charts.
"""
import argparse
import datetime
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

# Region views and the page names they take (from the rough-draft folder, see rough.md).
VIEWS = {
    '01-state-1952.png': 'jackson-ward-state-1952.webp',
    '01-state-1959.png': 'jackson-ward-state-1959.webp',
    '01-state-2026.png': 'jackson-ward-state-2026.webp',
    '02-count-1952.png': 'jackson-ward-count-1952.webp',
    '03-streets-1952.png': 'jackson-ward-streets-1952.webp',
    '03-streets-2026.png': 'jackson-ward-streets-2026.webp',
    '04-second-street-1952.png': 'jackson-ward-second-street-1952.webp',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rough', default=None)
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    c = json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counts.json')))
    text = open(os.path.join(HERE, 'story.md')).read()
    for k, v in {'paved': c['paved']['buildings'], 'corridor': c['corridor']['buildings'], 'all': f"{c['all traced']['buildings']:,}", 'date': a.date}.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    open(os.path.join(ROOT, 'pages/jackson-ward.md'), 'w').write(text)
    print('wrote pages/jackson-ward.md')
    if a.rough:
        for src, dst in VIEWS.items():
            im = Image.open(os.path.join(a.rough, src)).convert('RGB')
            if im.width > 1600:
                im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
            im.save(os.path.join(ROOT, 'pages', dst), quality=82, method=6)
            print('wrote pages/' + dst, im.size)
        # The link preview: the 1952 view, cropped to 1.91:1 around the corridor, 1200 x 630.
        im = Image.open(os.path.join(a.rough, '01-state-1952.png')).convert('RGB')
        w = round(im.height * 0.86 * 1.905)
        h = round(im.height * 0.86)
        x0 = (im.width - w) // 2
        y0 = round(im.height * 0.07)
        im.crop((x0, y0, x0 + w, y0 + h)).resize((1200, 630), Image.LANCZOS).save(os.path.join(ROOT, 'pages', 'jackson-ward-social.jpg'), quality=84)
        print('wrote pages/jackson-ward-social.jpg')


if __name__ == '__main__':
    main()
