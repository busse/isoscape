#!/usr/bin/env python3
"""The guide's link-preview picture, pages/jackson-ward-guide-social.jpg (1200 x 630): the walk's
overview map on the left and, on the right, what the page is and where, in the picture itself,
so a shared link says it without its text. Colors from src/palette.ts (common.palette), type in
Inter (tools/pdf/fonts, SIL Open Font License).

    python3 tools/stories/jackson-ward-guide/social.py

Reads out/stories/jackson-ward-guide/jackson-ward-guide-map-phone.png (map.py) and route.json.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load, palette  # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1200, 630
FONTS = os.path.join(ROOT, 'tools/pdf/fonts')


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, f'Inter-{name}.ttf'), size)


def wrap(d, text, f, width):
    lines, line = [], ''
    for w in text.split():
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=f) <= width:
            line = t
        else:
            lines.append(line)
            line = w
    return lines + [line]


def main():
    P = palette()
    route = load('route.json')
    im = Image.new('RGB', (W, H), P['sky'])
    m = Image.open(os.path.join(ROOT, 'out/stories/jackson-ward-guide/jackson-ward-guide-map-phone.png')).convert('RGB')
    # the map's own frame: below its title rows (map.py: head = 3.6 x 13.5 px), above its key; at 3x
    from map import RENDERS
    (x0, x1, y0, y1), w_css = RENDERS['phone'][0], RENDERS['phone'][1]
    top = round(13.5 * 3.6 * 3)
    map_h = round((y1 - y0) / ((x1 - x0) / (w_css - 2)) * 3)
    crop = m.crop((0, top, m.width, top + map_h))
    mw = round(crop.width * H / crop.height)
    im.paste(crop.resize((mw, H), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(im)
    d.line((mw, 0, mw, H), fill=P['ink'], width=2)
    x, y, width = mw + 36, 64, W - mw - 66
    for text, f, gap in (('Seeing the change', font('Bold', 44), 18),
                         ('A walking guide to Jackson Ward, Richmond, Virginia', font('SemiBold', 30), 30),
                         (f'Eight stops on {route["total_m"] / 1609.344:.1f} miles of sidewalk. '
                          'Seven of the places are shown as they were in 1952 and as they are today.', font('Regular', 24), 26),
                         ('By Chris Busse, a Richmond artist', font('Regular', 22), 0)):
        for line in wrap(d, text, f, width):
            d.text((x, y), line, font=f, fill=P['ink'])
            y += round(f.size * 1.25)
        y += gap
    out = os.path.join(ROOT, 'pages', 'jackson-ward-guide-social.jpg')
    im.save(out, quality=86, optimize=True)
    print('wrote', out, im.size)


if __name__ == '__main__':
    main()
