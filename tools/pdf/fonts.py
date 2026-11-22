#!/usr/bin/env python3
"""Make the story PDFs' fonts: Inter, cut to Latin text and turned into TrueType outlines.

The site sets its text in the reader's system font (San Francisco, Segoe UI and the like), and
those fonts may not be embedded in a document we hand out. So the PDFs use Inter, by The Inter
Project Authors, under the SIL Open Font License 1.1 (OFL.txt here; Inter has no Reserved Font
Name, so a cut-down copy may keep its name). Chrome embeds CFF fonts such as Inter's .otf files as
Type 3 fonts, which some readers draw roughly and screen readers handle less well, so this turns
the outlines into TrueType (quadratic, within 1 unit of the original) and keeps only the
characters the stories use, with room to spare:

    python3 tools/pdf/fonts.py [/path/to/inter/otf/folder]

It reads Inter-{Regular,Italic,SemiBold,SemiBoldItalic,Bold,BoldItalic}.otf (Debian's and
Ubuntu's fonts-inter puts them in /usr/share/fonts/opentype/inter; they are also at
https://rsms.me/inter/) and writes tools/pdf/fonts/Inter-*.ttf. The files are committed, so a
machine without Inter can still make the PDFs; rerun this only to widen the character set.
"""
import os
import sys

from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fonts')
STYLES = ['Regular', 'Italic', 'SemiBold', 'SemiBoldItalic', 'Bold', 'BoldItalic']
# Basic Latin, Latin-1, Latin Extended-A, general punctuation, super- and subscripts, currency,
# letterlike symbols, number forms, arrows, math operators, geometric shapes.
RANGES = [(0x20, 0x7E), (0xA0, 0x17F), (0x2000, 0x206F), (0x2070, 0x209F), (0x20A0, 0x20BF),
          (0x2100, 0x214F), (0x2150, 0x218F), (0x2190, 0x21FF), (0x2200, 0x22FF), (0x25A0, 0x25FF)]


def to_truetype(font: TTFont) -> None:
    """Replace a CFF font's outlines with quadratic TrueType ones (fontTools' otf2ttf recipe)."""
    order = font.getGlyphOrder()
    glyphs = font.getGlyphSet()
    glyf = newTable('glyf')
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(glyphs)
        glyphs[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font['loca'] = newTable('loca')
    font['glyf'] = glyf
    del font['CFF ']
    if 'VORG' in font:
        del font['VORG']
    font['maxp'] = newTable('maxp')
    maxp = font['maxp']
    maxp.tableVersion = 0x00010000
    for k in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs',
              'maxStackElements', 'maxSizeOfInstructions', 'maxComponentElements'):
        setattr(maxp, k, 0)
    maxp.maxZones = 1
    font['head'].glyphDataFormat = 0
    post = font['post']
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = order
    font.sfntVersion = '\x00\x01\x00\x00'
    font.recalcBBoxes = True


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/opentype/inter'
    os.makedirs(OUT, exist_ok=True)
    unicodes = [u for a, b in RANGES for u in range(a, b + 1)]
    for style in STYLES:
        font = TTFont(os.path.join(src, f'Inter-{style}.otf'))
        opts = subset.Options()
        opts.layout_features = ['kern', 'liga', 'calt', 'tnum', 'case', 'frac', 'sups', 'ccmp', 'locl', 'mark', 'mkmk']
        opts.name_IDs = ['*']
        opts.notdef_outline = True
        opts.hinting = False
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=unicodes)
        sub.subset(font)
        to_truetype(font)
        path = os.path.join(OUT, f'Inter-{style}.ttf')
        font.save(path)
        print(f'{path}: {os.path.getsize(path) // 1024} KB')


if __name__ == '__main__':
    main()
