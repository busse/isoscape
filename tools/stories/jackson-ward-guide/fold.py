#!/usr/bin/env python3
"""The guide's folded sheet: one US Letter sheet, printed on both sides at home or at a library
and folded in thirds (a letter fold) to a 3.67 x 8.5 in pocket guide.

    python3 tools/stories/jackson-ward-guide/fold.py [--out DIR] [--look DIR] [--date 2026-11-23]

The sheet lies landscape (11 x 8.5 in), in three panels of 3.67 in.

  Outside (PDF page 1), as you look at it: the map across the left and middle panels (map.py's
  `sheet` rendering, its names kept as text) and the cover on the right panel: the title, the
  author line, the walk in brief, the live address, how to print and fold, and the credits.
  Inside (PDF page 2): the eight stops in walking order across the three panels, each with the
  directions to it, where to stand and what to look at (the page's own words, from route.json),
  and its 1952-and-today pair (pairs.py), set at the top of the stop so it stays beside its title.

Print both sides, flipping on the short edge. Fold the inside's right panel in first, then its
left panel over it: the cover is then on the front, the middle of the map on the back, and the
first stops are the first thing inside. The fold lines fall in the gutters between the text
columns, and short marks at the top and bottom edges show where they are.

Type: body 8.5 pt and up, credits 7 pt and up (checked here on the PDF's own text). Fonts are
Inter (SIL Open Font License, tools/pdf/fonts), embedded; the text is real text and each picture
carries alt text. The map tells the walk, the 1952 streets, Gilpin Court and the highway apart by
line style, outline and label as well as color, so it survives a black-and-white printer
(--look writes a grayscale render to check, and a fold mock-up).

Chrome prints the HTML (headless, sandbox on, file:// only) as tools/pdf/story_pdf.py does, and
pikepdf writes the document facts. Needs what story_pdf.py needs.
"""
import argparse
import base64
import datetime
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'pdf'))
from common import load, palette  # noqa: E402
import story_pdf  # noqa: E402  (chrome(), font_faces(), AUTHOR, SITE_URL)

import pikepdf  # noqa: E402
import pdfplumber  # noqa: E402
from PIL import Image  # noqa: E402

SLUG = 'jackson-ward-guide'
PANEL = 11 / 3          # in
BODY_PT, CREDIT_PT = 8.5, 7.0
LIVE = f'{story_pdf.SITE_URL}p/{SLUG}.html'
CONTACT = f'{story_pdf.SITE_URL}#/about/contact'
E = html.escape


def pair_jpeg(name, width=640):
    im = Image.open(os.path.join(ROOT, 'pages', name)).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=86, subsampling=0)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode(), im.size


def map_svg():
    """map.py's sheet rendering, its fonts set to the embedded Inter, sized to its box by CSS."""
    s = open(os.path.join(ROOT, 'out/stories/jackson-ward-guide/jackson-ward-guide-map-sheet.svg')).read()
    s = s[s.index('<svg'):]
    s = re.sub(r'<metadata>.*?</metadata>', '', s, flags=re.S)
    s = s.replace("font-family: 'Inter'", "font-family: 'Inter PDF'")
    s = re.sub(r'<svg ([^>]*?)width="[^"]+" height="[^"]+"', r'<svg \1class="map" role="img" aria-labelledby="map-title"', s, count=1)
    s = s.replace('>', '><title id="map-title">The walk in Jackson Ward, north up: eight numbered stops along the route on mapped '
                       'sidewalks, today\'s streets named upright, the 1952 streets the I-95 trench cut dashed and named in italic, the '
                       'highway in its trench, and Gilpin Court as a bordered area, with a key and credits</title>', 1)
    return s


def document(date):
    P = palette()
    route = load('route.json')
    pairs = load('pairs.json')
    legs = {l['to']: l for l in route['legs']}
    t = route['total_m']
    minutes = round(t / route['walk_m_per_min'] / 5) * 5
    stops = []
    for st in route['stops']:
        n = st['n']
        if n in legs:
            l = legs[n]
            get = (f"<b>From stop {l['frm']}</b>, about {int(round(l['m'], -1)):,} m ({l['minutes']} min). "
                   + E(' '.join(l['directions'])))
        else:
            get = '<b>The walk starts here.</b>'
        p = pairs[str(n)]
        if p['file']:
            src, (w, h) = pair_jpeg(p['file'])
            fig = (f'<figure class="pair"><img src="{src}" width="{w}" height="{h}" alt="Stop {n}, {E(st["title"])}, drawn from the south: '
                   f'the same blocks in 1952 (top) and today (bottom), with the stop\'s number where you stand">'
                   '</figure>')
        else:
            fig = ''
        note = '' if p['file'] else '<p class="note">No 1952 picture for this stop: the full guide says why.</p>'
        stops.append(f'''<section class="stop" aria-label="Stop {n}">
<h2><span class="n">{n}</span> {E(st["title"])}</h2>
{fig}<p class="get">{get}</p>
<p><b>Stand</b> {E(st["where"])}. <b>Look</b> {E(st["sees"])}.</p>{note}
</section>''')
    css = f'''
{story_pdf.font_faces()}
@page {{ size: 11in 8.5in; margin: 0 }}
* {{ box-sizing: border-box }}
html, body {{ margin: 0; padding: 0 }}
body {{ font-family: 'Inter PDF', sans-serif; color: {P['ink']}; font-size: {BODY_PT}pt; line-height: 1.17; }}
.side {{ position: relative; width: 11in; height: 8.5in; overflow: hidden; break-after: page; background: {P['sky']} }}
.side:last-child {{ break-after: auto }}
.fold {{ position: absolute; width: 0; height: 0.16in; border-left: 0.5pt solid {P['ink']} }}
.mapbox {{ position: absolute; left: 0.27in; top: 0.3in; width: 6.8in; height: 7.9in }}
.mapbox svg {{ width: 6.8in; height: 7.9in; display: block }}
.cover {{ position: absolute; left: {2 * PANEL + 0.3:.3f}in; top: 0.35in; width: {PANEL - 0.6:.3f}in; height: 7.8in;
          display: flex; flex-direction: column }}
.cover h1 {{ font-size: 25pt; line-height: 1.05; margin: 0.25in 0 0.08in; font-weight: 700 }}
.cover .sub {{ font-size: 13pt; line-height: 1.2; font-weight: 600; margin: 0 0 0.16in }}
.cover .by {{ font-size: 10pt; margin: 0 0 0.22in }}
.cover p {{ margin: 0 0 0.09in }}
.cover .url {{ font-weight: 600; word-break: break-all }}
.cover .credits {{ margin-top: auto; font-size: {CREDIT_PT + 0.3}pt; line-height: 1.25; color: {P['ink']} }}
.cover .credits p {{ margin: 0 0 0.05in }}
.cover .rule {{ border-top: 0.75pt solid {P['ink']}; margin: 0.1in 0 0.12in }}
.cols {{ position: absolute; left: 0.3in; top: 0.32in; width: {11 - 0.6:.3f}in; height: 7.9in;
         column-count: 3; column-gap: 0.6in; column-fill: auto }}
.stop {{ margin: 0 0 0.08in }}
.stop h2 {{ font-size: 10.5pt; line-height: 1.15; margin: 0 0 0.04in; font-weight: 700; break-after: avoid }}
.stop .n {{ display: inline-block; width: 1.45em; height: 1.45em; line-height: 1.45em; border-radius: 50%; text-align: center;
           background: {P['ink']}; color: {P['sky']}; font-size: 9pt; margin-right: 0.05in; vertical-align: 0.05em }}
.stop p {{ margin: 0 0 0.04in }}
.stop .get {{ break-before: avoid }}
.pair {{ float: right; clear: right; width: 1.2in; margin: 0.02in 0 0.04in 0.08in; break-inside: avoid }}
.pair img {{ width: 100%; height: auto; display: block; border: 0.4pt solid {P['ink']} }}
.pair figcaption {{ font-size: {BODY_PT}pt; line-height: 1.1; margin-top: 0.02in }}
.note {{ font-style: italic }}
.head {{ font-size: 9pt; font-weight: 700; margin: 0 0 0.08in }}
'''
    folds = ''.join(f'<div class="fold" style="left:{x:.4f}in; top:0"></div><div class="fold" style="left:{x:.4f}in; bottom:0"></div>'
                    for x in (PANEL, 2 * PANEL))
    cover = f'''<div class="cover">
<h1>Seeing the change</h1>
<p class="sub">A walking guide to Jackson Ward, Richmond, Virginia</p>
<p class="by">Chris Busse, a Richmond artist</p>
<p>Eight stops on {t / 1000:.1f} km ({t / 1609.344:.1f} miles) of sidewalk, about {minutes} minutes on foot at about
{route['walk_m_per_min']} m a minute. The walk starts at Second and Leigh Streets and ends across East Leigh Street from the
Coliseum, {int(round(route['last_to_first_m'], -1))} m from where it began.</p>
<p>The stops are inside, with directions and each place in 1952 and today where there is a picture. The full guide has the
history of each stop and its sources:</p>
<p class="url">{E(LIVE.replace('https://', ''))}</p>
<div class="rule"></div>
<p><b>To print and fold:</b> print both sides of one US Letter sheet, flipping on the short edge. With the stops facing you,
fold the right third in, then the left third over it.</p>
<div class="credits">
<p>Chris Busse made this guide with Claude. Its history comes from the published Jackson Ward story on the same site and that
story's sources. The route, the directions and the distances were laid out in code from OpenStreetMap as it stood on
{E(route['osm_date'])}; the directions say what OpenStreetMap shows at each crossing.</p>
<p>Map © OpenStreetMap contributors (ODbL). 1952 streets: Sanborn Fire Insurance Map, Richmond, 1952, vol. 3, Library of
Congress, with seven stretches joined across the trench as the U.S. Geological Survey's map of 1933–34 shows them. Gilpin
Court: City of Richmond parcel records, approximate. The pictures are drawn by Chris Busse with isoscape from the story's
views of 1952 and today.</p>
<p>Corrections are welcome: {E(CONTACT.replace('https://', ''))}. This sheet: {E(date.strftime('%B %-d, %Y'))}.</p>
</div>
</div>'''
    return f'''<!DOCTYPE html>
<html lang="en-US"><head><meta charset="utf-8"><title>Seeing the change: a walking guide to Jackson Ward (folded sheet)</title>
<style>{css}</style></head><body>
<main>
<div class="side outside">{folds}
<div class="mapbox">{map_svg()}</div>
{cover}
</div>
<div class="side inside">{folds}
<div class="cols">
<p class="head">The stops, in walking order. The map is on the other side.</p>
{''.join(stops)}
</div>
</div>
</main>
</body></html>'''


def print_pdf(doc, out):
    work = tempfile.mkdtemp(prefix='fold-')
    page = os.path.join(work, 'page.html')
    open(page, 'w').write(doc)
    story_pdf.run_chrome(work, out)
    subprocess.run(['rm', '-rf', work], check=False)


def finish(pdf_path, date):
    pdf = pikepdf.open(pdf_path, allow_overwriting_input=True)
    iso = date.isoformat()
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta['dc:title'] = 'Seeing the change: a walking guide to Jackson Ward, Richmond, Virginia (folded sheet)'
        meta['dc:creator'] = [story_pdf.AUTHOR]
        meta['dc:description'] = ('A one-sheet walking guide to Jackson Ward in Richmond, Virginia, to print on both sides of US Letter '
                                  'and fold in thirds: the map, eight stops with directions, and seven places in 1952 and today.')
        meta['dc:language'] = ['en-US']
        meta['pdf:Keywords'] = 'isoscape, Richmond, Virginia, Jackson Ward, walking guide, maps, history'
        meta['pdf:Producer'] = 'Skia/PDF (Chrome), pikepdf'
        meta['xmp:CreatorTool'] = "isoscape's guide sheet tool (tools/stories/jackson-ward-guide/fold.py)"
        meta['xmp:CreateDate'] = iso
        meta['xmp:ModifyDate'] = iso
    pdf.Root.Lang = pikepdf.String('en-US')
    pdf.Root.ViewerPreferences = pikepdf.Dictionary(DisplayDocTitle=True)
    pdf.save(pdf_path, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)


def check(pdf_path):
    """Two landscape Letter pages, tagged, Inter only, no body text under 8.5 pt and no credit
    under 7 pt, nothing off the sheet. Returns a list of problems."""
    problems = []
    p = pikepdf.open(pdf_path)
    if len(p.pages) != 2:
        problems.append(f'{len(p.pages)} pages, not 2')
    for i, pg in enumerate(p.pages):
        box = [float(v) for v in pg.MediaBox]
        if (round(box[2] - box[0]), round(box[3] - box[1])) != (792, 612):
            problems.append(f'page {i + 1} is {box}, not 792 x 612 pt')
    if '/StructTreeRoot' not in p.Root:
        problems.append('not tagged')
    fonts = set()
    for pg in p.pages:
        for _, f in (pg.Resources.get('/Font') or {}).items():
            fonts.add(str(f.get('/BaseFont')))
            if f.get('/Subtype') == '/Type3':
                problems.append('a Type 3 font')
    if any('Inter' not in f for f in fonts):
        problems.append(f'fonts outside Inter: {sorted(fonts)}')
    # The map's names are checked in its SVG, where their sizes are plain (1 SVG unit is 1 pt at
    # the size the sheet prints it); pdfplumber reports a turned name's size as its box's height.
    svg = open(os.path.join(ROOT, 'out/stories/jackson-ward-guide/jackson-ward-guide-map-sheet.svg')).read()
    for m in re.finditer(r'<text[^>]*style="([^"]*)"[^>]*>(.*?)</text>', svg, re.S):
        fs = float(re.search(r'font-size: ([\d.]+)px', m.group(1)).group(1))
        credit = 'fill: #2c2b33' not in m.group(1) and fs < BODY_PT
        if fs < (CREDIT_PT if credit else BODY_PT) - 0.05:
            problems.append(f'map text at {fs:.2f} pt: {re.sub("<[^>]+>", "", m.group(2))[:40]!r}')
    with pdfplumber.open(pdf_path) as pl:
        sizes = {}
        for i, pg in enumerate(pl.pages):
            for ch in pg.chars:
                a_, b_, c_, d_ = ch['matrix'][:4]
                if abs(b_) > 1e-3 or abs(c_) > 1e-3:
                    continue      # a turned map name: checked in the SVG above
                s = round(ch['size'], 1)
                sizes[s] = sizes.get(s, 0) + 1
                if ch['x0'] < 0 or ch['x1'] > pg.width or ch['top'] < 0 or ch['bottom'] > pg.height:
                    problems.append(f'text off page {i + 1}: {ch["text"]!r}')
                    break
        small = {s: n for s, n in sizes.items() if s < CREDIT_PT - 0.05}
        if small:
            problems.append(f'text under {CREDIT_PT} pt: {small}')
    return problems, sorted(fonts), sizes


def look(pdf_path, out):
    """Both sides at 100% (96 dpi) in color and in grayscale, at 200 dpi for detail, and a mock-up
    of the folded sheet: front, back and the first opening."""
    os.makedirs(out, exist_ok=True)
    for dpi, tag in ((96, '100pct'), (200, '200dpi')):
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', pdf_path, os.path.join(out, f'side-{tag}')], check=True)
        subprocess.run(['pdftoppm', '-r', str(dpi), '-gray', '-png', pdf_path, os.path.join(out, f'side-{tag}-gray')], check=True)
    sides = sorted(f for f in os.listdir(out) if f.startswith('side-100pct-') and 'gray' not in f)
    outside, inside = (Image.open(os.path.join(out, f)).convert('RGB') for f in sides)
    W, H = outside.size
    pw = W // 3
    panel = lambda im, k: im.crop((k * pw, 0, (k + 1) * pw, H))  # noqa: E731
    # folded: front = outside's right panel; back = outside's middle; opening the cover shows the
    # inside's left panel beside the flap's outside (the outside's left panel)
    gap = 40
    mock = Image.new('RGB', (pw * 4 + gap * 5, H + 90), (255, 255, 255))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(mock)
    f = ImageFont.truetype(os.path.join(ROOT, 'tools/pdf/fonts/Inter-SemiBold.ttf'), 22)
    items = [('Front (cover)', panel(outside, 2)), ('Back', panel(outside, 1)),
             ('Open the cover: left', panel(inside, 0)), ('Open the cover: right (the flap)', panel(outside, 0))]
    for i, (label, im) in enumerate(items):
        x = gap + i * (pw + gap)
        d.text((x, 20), label, font=f, fill=(0, 0, 0))
        mock.paste(im, (x, 70))
        d.rectangle((x - 1, 69, x + pw, 70 + H), outline=(0, 0, 0))
    mock.save(os.path.join(out, 'fold-mockup.png'))
    # the whole sheet, opened, with the folds marked
    sheet = Image.new('RGB', (W, H * 2 + 60), (255, 255, 255))
    sheet.paste(outside, (0, 0))
    sheet.paste(inside, (0, H + 60))
    d = ImageDraw.Draw(sheet)
    for k in (1, 2):
        for y0 in (0, H + 60):
            d.line((k * W / 3, y0, k * W / 3, y0 + H), fill=(200, 0, 0), width=1)
    d.text((10, H + 15), 'Above: outside (map and cover). Below: inside (the stops). Red: the folds.', font=f, fill=(0, 0, 0))
    sheet.save(os.path.join(out, 'sheet-opened.png'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'out/stories/jackson-ward-guide'))
    ap.add_argument('--look', default=None)
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    a = ap.parse_args()
    date = datetime.date.fromisoformat(a.date)
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, f'{SLUG}-folded.pdf')
    print_pdf(document(date), out)
    finish(out, date)
    problems, fonts, sizes = check(out)
    print(f'{out}: {os.path.getsize(out) / 1e6:.1f} MB, fonts {", ".join(fonts)}; type sizes (pt: chars) '
          + ', '.join(f'{s}: {n}' for s, n in sorted(sizes.items())))
    if a.look:
        look(out, a.look)
        print('look:', a.look)
    if problems:
        sys.exit('fold: ' + '; '.join(problems))


if __name__ == '__main__':
    main()
