#!/usr/bin/env python3
"""The guide's folded sheet: one US Letter sheet, printed on both sides at home or at a library
and folded in thirds (a letter fold) to a 3.67 x 8.5 in pocket guide.

    python3 tools/stories/jackson-ward-guide/fold.py [--out DIR] [--look DIR] [--date 2026-11-23]

The sheet lies landscape (11 x 8.5 in), in three panels of 3.67 in.

  Inside (PDF page 1, seen whole when the sheet is opened out): the plan map across the sheet,
  8.9 in wide, every street named at 8.5 pt or more, with the grid (map.py's `sheet` rendering,
  its names kept as text), and in a strip at the right the key, the ten places to stand with
  their grid squares, and the credits.
  Outside (PDF page 2): the whole ward in 1952 and today with the streets named (pairs.py's
  `ward-sheet`) across the left and middle panels, and the cover on the right panel: the title,
  the author line, how to use it, the live address and how to print and fold.

Print both sides, flipping on the short edge. With the map facing you, fold the right third in,
then the left third over it: the cover is then on the front, the middle of the drawings on the
back, and opening the sheet out shows the whole map. The street index is on the page, not the
sheet: at 7.5 pt its 84 rows need more room than the sheet has beside the map.

Type: body 8.5 pt and up, credits 7 pt and up (checked here on the PDF's own text; the map's
turned names in its SVG). Fonts are Inter (SIL Open Font License, tools/pdf/fonts), embedded; the
text is real text and each picture carries alt text. The map tells today's streets, the 1952
streets, Gilpin Court and the highway apart by line style, outline and label as well as color, so
it survives a black-and-white printer (--look writes a grayscale render to check, and a fold
mock-up).

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


def image_uri(path, width=None, quality=88):
    im = Image.open(path).convert('RGB')
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=quality, subsampling=0)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode(), im.size


def map_svg():
    """map.py's sheet rendering, its fonts set to the embedded Inter, sized to its box by CSS."""
    s = open(os.path.join(ROOT, 'out/stories/jackson-ward-guide/jackson-ward-guide-map-sheet.svg')).read()
    s = s[s.index('<svg'):]
    s = re.sub(r'<metadata>.*?</metadata>', '', s, flags=re.S)
    s = s.replace("font-family: 'Inter'", "font-family: 'Inter PDF'")
    s = re.sub(r'<svg ([^>]*?)width="[^"]+" height="[^"]+"', r'<svg \1class="map" role="img" aria-labelledby="map-title"', s, count=1)
    s = s.replace('>', '><title id="map-title">Plan of Jackson Ward, north up, with a grid of squares A to F and 1 to 6: every '
                       'street named, today\'s upright and the 1952 streets the I-95 trench cut dashed and in italic, the bridges '
                       'over the trench, where streets end at it, the highway\'s exits, landmarks, Gilpin Court as a bordered area, '
                       'and ten numbered places to stand with a wedge showing which way to look</title>', 1)
    return s


SWATCH = {
    'street': '<span class="sw" style="border-top: 2.2pt solid {street}"></span>',
    'bridge': '<span class="sw" style="border-top: 1pt solid {ink}; border-bottom: 1pt solid {ink}; height: 2.6pt; background: {street}"></span>',
    'end': '<span class="sw" style="border-top: 2.2pt solid {street}; border-right: 1.8pt solid {ink}; height: 5pt; margin-top: -2pt"></span>',
    'lost': '<span class="sw" style="border-top: 1.6pt dashed {lost}"></span>',
    'highway': '<span class="sw box" style="background: {highway}; border: 0.5pt solid {hedge}"></span>',
    'gilpin': '<span class="sw box" style="background: {plan}; border: 1.2pt solid {ink}"></span>',
    'stop': '<span class="sw disc" style="background: {ink}; color: {sky}">1</span>',
    'landmark': '<span class="sw box small" style="background: {fresh}; border: 0.5pt solid {ink}"></span>',
    'grid': '<span class="sw tab" style="border: 0.5pt solid {ink}">C4</span>',
}


def document(date):
    P = palette()
    import map as M
    V = load('vantage.json')
    O = load('orient.json')
    sys.path.insert(0, HERE)
    import pairs as PR
    colors = dict(street=_hex(M.C['street']), ink=P['ink'], lost=P['mark']['line'], highway=_hex(M.C['highway']),
                  hedge=_hex(M.C['highway_edge']), plan=P['plan'], sky=P['sky'], fresh=P['fresh'])
    key = ''.join(f'<li>{SWATCH[k].format(**colors)}<span>{E(t)}</span></li>' for k, t in M.KEY)
    places = ''.join(f'<li><b>{v["n"]}</b> {v["square"]} {E(PR.PLACE.get(v["key"], v["title"]))}</li>' for v in V['points'])
    ward, (ww, wh) = image_uri(os.path.join(ROOT, 'out/stories/jackson-ward-guide/jackson-ward-guide-ward-sheet.png'), 2400, 86)
    css = f'''
{story_pdf.font_faces()}
@page {{ size: 11in 8.5in; margin: 0 }}
* {{ box-sizing: border-box }}
html, body {{ margin: 0; padding: 0 }}
body {{ font-family: 'Inter PDF', sans-serif; color: {P['ink']}; font-size: {BODY_PT}pt; line-height: 1.2; }}
.side {{ position: relative; width: 11in; height: 8.5in; overflow: hidden; break-after: page; background: {P['sky']} }}
.side:last-child {{ break-after: auto }}
.fold {{ position: absolute; width: 0; height: 0.16in; border-left: 0.5pt solid {P['ink']} }}
.mapbox {{ position: absolute; left: 0.22in; top: 0.42in; width: 8.93in }}
.mapbox svg {{ width: 8.93in; height: auto; display: block }}
.maptitle {{ position: absolute; left: 0.25in; top: 0.16in; font-weight: 700; font-size: 10pt }}
.strip {{ position: absolute; left: 9.3in; top: 0.3in; width: 1.5in; height: 7.95in; display: flex; flex-direction: column }}
.strip h2 {{ font-size: 9pt; margin: 0 0 0.05in; font-weight: 700 }}
.strip ul {{ list-style: none; margin: 0 0 0.12in; padding: 0 }}
.strip li {{ margin: 0 0 0.045in; display: flex; gap: 0.05in; align-items: flex-start }}
.places li {{ display: block; text-indent: -0.14in; padding-left: 0.14in }}
.sw {{ flex: 0 0 0.3in; display: inline-block; height: 0; margin-top: 0.06in }}
.sw.box {{ height: 0.1in; margin-top: 0.01in }}
.sw.small {{ flex-basis: 0.12in; margin-right: 0.18in }}
.sw.disc {{ flex: 0 0 0.15in; height: 0.15in; border-radius: 50%; text-align: center; font-size: 8.5pt; line-height: 0.15in;
           font-weight: 700; margin: 0 0.15in 0 0 }}
.sw.tab {{ flex: 0 0 auto; height: auto; font-size: 8.5pt; font-weight: 700; padding: 0 2pt; margin: 0 0.08in 0 0 }}
.credits {{ margin-top: auto; font-size: {CREDIT_PT + 0.3}pt; line-height: 1.22 }}
.credits p {{ margin: 0 0 0.04in }}
.ward {{ position: absolute; left: 0.25in; top: 0.3in; width: 6.95in }}
.ward img {{ width: 100%; height: auto; display: block }}
.ward p {{ margin: 0.05in 0 0; font-size: {BODY_PT}pt }}
.cover {{ position: absolute; left: {2 * PANEL + 0.3:.3f}in; top: 0.35in; width: {PANEL - 0.6:.3f}in; height: 7.8in;
          display: flex; flex-direction: column }}
.cover h1 {{ font-size: 25pt; line-height: 1.05; margin: 0.2in 0 0.08in; font-weight: 700 }}
.cover .sub {{ font-size: 13pt; line-height: 1.2; font-weight: 600; margin: 0 0 0.14in }}
.cover .by {{ font-size: 10pt; margin: 0 0 0.2in }}
.cover p {{ margin: 0 0 0.09in }}
.cover .url {{ font-weight: 600; word-break: break-all }}
.cover .rule {{ border-top: 0.75pt solid {P['ink']}; margin: 0.1in 0 0.12in }}
.cover .credits {{ margin-top: auto }}
'''
    folds = ''.join(f'<div class="fold" style="left:{x:.4f}in; top:0"></div><div class="fold" style="left:{x:.4f}in; bottom:0"></div>'
                    for x in (PANEL, 2 * PANEL))
    n = len(V['points'])
    return f'''<!DOCTYPE html>
<html lang="en-US"><head><meta charset="utf-8"><title>Seeing the change: finding your place in Jackson Ward, 1952 and today (folded sheet)</title>
<style>{css}</style></head><body>
<main>
<div class="side inside">{folds}
<div class="maptitle">Jackson Ward, north up, every street named. Grid squares match the street index on the guide's page.</div>
<div class="mapbox">{map_svg()}</div>
<div class="strip">
<h2>Key</h2>
<ul class="key">{key}</ul>
<h2>Places to stand</h2>
<ul class="places">{places}</ul>
<div class="credits">
<p>© OpenStreetMap contributors (ODbL), {E(V['osm_date'])}. 1952 streets: Sanborn map, 1952, Library of Congress, and
USGS map, 1933–34. Gilpin Court: City of Richmond parcels, approximate.</p>
</div>
</div>
</div>
<div class="side outside">{folds}
<figure class="ward"><img src="{ward}" width="{ww}" height="{wh}" alt="Jackson Ward in Richmond seen from the south, 1952 above and today below, with the streets named in both: in 1952 the blocks built up where the I-95 trench runs today, with the streets it cut named in italic; today the highway in its trench, crossed by a few bridges">
<p>Jackson Ward in 1952 and today, seen from the south. Today's street names are upright; in 1952 the streets the trench cut
are in italic, and a street of today is named only where it ran on the same line then. Hatched: no 1952 building traced.</p>
</figure>
<div class="cover">
<h1>Seeing the change</h1>
<p class="sub">Finding your place in Jackson Ward, Richmond, Virginia, 1952 and today</p>
<p class="by">Chris Busse, a Richmond artist</p>
<p>Open the sheet out for the map: every street is named, today's and 1952's, with a grid to find a place by.</p>
<p>Beside the cover, the whole ward in 1952 and today, with the streets named on the drawings.</p>
<p>{n} places to stand are on public sidewalks, numbered west to east only to find them. Go to any of them, in any order.</p>
<p>The guide, with the street index, a 1952-and-today picture at each place and the history with its sources:</p>
<p class="url">{E(LIVE.replace('https://', ''))}</p>
<div class="rule"></div>
<p><b>To print and fold:</b> print both sides of one US Letter sheet, flipping on the short edge. With the map facing you,
fold the right third in, then the left third over it.</p>
<div class="credits">
<p>Chris Busse made this guide with Claude. Its history comes from the published Jackson Ward story on the same site and that
story's sources. The pictures are drawn by Chris Busse with isoscape from the story's views of 1952 and today; the street
names are placed on them in code.</p>
<p>Corrections are welcome: {E(CONTACT.replace('https://', ''))}. This sheet: {E(date.strftime('%B %-d, %Y'))}.</p>
</div>
</div>
</div>
</main>
</body></html>'''


def _hex(c):
    if isinstance(c, str):
        return c
    return '#' + ''.join(f'{round(v * 255):02x}' for v in c[:3])


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
        meta['dc:title'] = 'Seeing the change: finding your place in Jackson Ward, 1952 and today (folded sheet)'
        meta['dc:creator'] = [story_pdf.AUTHOR]
        meta['dc:description'] = ('A one-sheet pocket guide to Jackson Ward in Richmond, Virginia, to print on both sides of US Letter '
                                  'and fold in thirds: a map with every street named, ten places to stand, and the ward in 1952 and '
                                  'today with the streets named.')
        meta['dc:language'] = ['en-US']
        meta['pdf:Keywords'] = 'isoscape, Richmond, Virginia, Jackson Ward, street names, maps, history'
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
    inside, outside = (Image.open(os.path.join(out, f)).convert('RGB') for f in sides)
    W, H = outside.size
    pw = W // 3
    panel = lambda im, k: im.crop((k * pw, 0, (k + 1) * pw, H))  # noqa: E731
    # folded with the map inside: front = outside's right panel; back = outside's middle; opening
    # the cover shows the inside's left panel beside the flap (the outside's left panel)
    gap = 40
    mock = Image.new('RGB', (pw * 4 + gap * 5, H + 90), (255, 255, 255))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(mock)
    f = ImageFont.truetype(os.path.join(ROOT, 'tools/pdf/fonts/Inter-SemiBold.ttf'), 22)
    items = [('Front (cover)', panel(outside, 2)), ('Back', panel(outside, 1)),
             ('Open the cover: left', panel(inside, 0)), ('Open the cover: the flap', panel(outside, 0))]
    for i, (label, im) in enumerate(items):
        x = gap + i * (pw + gap)
        d.text((x, 20), label, font=f, fill=(0, 0, 0))
        mock.paste(im, (x, 70))
        d.rectangle((x - 1, 69, x + pw, 70 + H), outline=(0, 0, 0))
    mock.save(os.path.join(out, 'fold-mockup.png'))
    # the whole sheet, opened, with the folds marked
    sheet = Image.new('RGB', (W, H * 2 + 60), (255, 255, 255))
    sheet.paste(inside, (0, 0))
    sheet.paste(outside, (0, H + 60))
    d = ImageDraw.Draw(sheet)
    for k in (1, 2):
        for y0 in (0, H + 60):
            d.line((k * W / 3, y0, k * W / 3, y0 + H), fill=(200, 0, 0), width=1)
    d.text((10, H + 15), 'Above: inside (the map, seen when the sheet is opened out). Below: outside (1952 and today, and the cover). Red: the folds.', font=f, fill=(0, 0, 0))
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
