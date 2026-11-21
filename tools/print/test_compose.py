"""Tests for the credit line in compose.py. Run from tools/print/: python3 -m unittest"""
import io, json, os, sys, tempfile, unittest, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C  # noqa: E402


def svg(d, name, credits=None):
    attr = '' if credits is None else ' data-credits="%s"' % json.dumps(credits).replace('&', '&amp;').replace('"', '&quot;')
    p = os.path.join(d, name + '.svg')
    open(p, 'w', encoding='utf-8').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" class="isoscape"%s role="img"></svg>' % attr)
    return p


class Credit(unittest.TestCase):
    def test_derived_from_the_builds_union_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            builds = {'a': svg(d, 'a', ['Map data © OpenStreetMap contributors (ODbL)', 'Elevation: USGS 3DEP']),
                      'b': svg(d, 'b', ['Map data © OpenStreetMap contributors (ODbL)', 'Elevation: USGS 3DEP', 'Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress'])}
            self.assertEqual(C.design_credit({'panels': [{'build': 'a'}]}, builds),
                             'isoscape by Chris Busse  ·  Map data © OpenStreetMap contributors (ODbL)  ·  Elevation: USGS 3DEP')
            both = C.design_credit({'panels': [{'build': 'a'}, {'build': 'b'}], 'credit': 'hand-kept line'}, builds)
            self.assertTrue(both.endswith('Elevation: USGS 3DEP  ·  Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress'))
            self.assertNotIn('hand-kept', both)

    def test_a_build_without_credits_keeps_the_line_it_was_sold_with(self):
        with tempfile.TemporaryDirectory() as d:
            builds = {'old': svg(d, 'old')}
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(C.design_credit({'panels': [{'build': 'old'}], 'credit': 'X'}, builds), 'X')
                self.assertEqual(C.design_credit({'panels': [{'build': 'old'}]}, builds), C.LEGACY_CREDIT)


class SmallestSize(unittest.TestCase):
    def test_a_24x36_is_also_an_8x12_and_a_panorama_only_itself(self):
        spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.json')))
        self.assertAlmostEqual(C.smallest_scale(spec, (36, 24)), 1 / 3)
        self.assertEqual(C.smallest_scale(spec, (24, 10)), 1.0)
        self.assertEqual(C.smallest_scale({}, (36, 24)), 1.0)

    def test_the_reserved_corner_is_the_stamped_block(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'release'))
        import stamp, titleblock
        u = stamp.size_u(36, 300)
        self.assertAlmostEqual(C.block_reserve(36, 300), titleblock.WIDTH * u + titleblock.H * u * 0.5)
        spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.json')))
        self.assertEqual(C.stamped_faces(spec, (36, 24)), [36, 18, 30, 36])
        u18 = stamp.size_u(18, 300)                    # an 18x12 face, in the 36x24 sheet's pixels
        self.assertAlmostEqual(C.block_reserve(36, 300, faces=[36, 18]), (titleblock.WIDTH + titleblock.H * 0.5) * u18 * 2)


class WideCredit(unittest.TestCase):
    """A subtitle so long that the column beside it is too short (Gwynn's Island): the credit goes
    on wide lines above the title block's corner, at the minimum size, and the art is untouched."""
    SOURCES = ['Map data © OpenStreetMap contributors (ODbL)', 'Elevation: USGS 3DEP',
               'Land cover: USGS National Land Cover Database 2021 (MRLC, public domain)',
               'Building footprints: Microsoft Global ML Building Footprints (ODbL)']

    def sheet(self, subtitle, sources):
        import numpy as np
        spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.json')))
        with tempfile.TemporaryDirectory() as d:
            builds = {'b': svg(d, 'b', sources)}
            design = {'title': "Gwynn's Island", 'subtitle': subtitle, 'region': 'r', 'panels': [{'build': 'b'}]}
            saved = C.CREDIT, C.CREDIT_DERIVED
            C.CREDIT, C.CREDIT_DERIVED = C.design_credit(design, builds), True
            try:
                img = C.compose(design, (36, 24), builds, {'r': {'box': [0, 0, 1, 1]}}, 300, 1 / 6,
                                C.smallest_scale(spec, (36, 24)), C.stamped_faces(spec, (36, 24)))
            finally:
                C.CREDIT, C.CREDIT_DERIVED = saved
        return np.asarray(img.convert('L')) < 200, spec

    def test_long_subtitle_puts_the_credit_on_wide_lines_clear_of_the_block(self):
        import numpy as np
        ink, spec = self.sheet('Mathews County, Virginia · between the Piankatank and Milford Haven', self.SOURCES)
        H, W = ink.shape
        m, band = round(H * 0.05), round(H * 0.11)
        right = ink[H - m - band:, round(W * 0.6):]                 # right of the subtitle's end
        rows = np.nonzero(right.any(axis=1))[0] + H - m - band
        top = C.block_top(H, m, 36, 300, 1 / 6, C.stamped_faces(spec, (36, 24)))
        text = rows[rows > H - m - band + band * 0.08 + 2]          # below the rule
        self.assertTrue(len(text))
        self.assertLess(text.max(), top)                            # clear of every face's title block
        self.assertFalse(ink[round(top):H - m, W - m - 1].any())    # the corner itself is empty paper

    def test_a_credit_too_long_for_even_wide_lines_is_refused(self):
        with self.assertRaises(ValueError):
            self.sheet('Mathews County, Virginia · between the Piankatank and Milford Haven', self.SOURCES * 3)


class CreditBelow(unittest.TestCase):
    """A design with "credit": "below" (Then & Now) sets its credit under the subtitle at the left
    margin, in a taller band, with the title sized for its "titleBand", clear of the block."""
    def test_credit_under_the_subtitle_clear_of_the_block(self):
        import numpy as np
        spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.json')))
        sources = ['Map data © OpenStreetMap contributors (ODbL)', 'Elevation: USGS 3DEP', 'Buildings dated from assessor records',
                   'Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress']
        with tempfile.TemporaryDirectory() as d:
            builds = {'b': svg(d, 'b', sources)}
            design = {'title': 'Richmond, Then & Now', 'subtitle': '1886 and 2026, the same blocks from the same spot', 'region': 'r',
                      'orientation': 'portrait', 'credit': 'below', 'band': 0.19, 'titleBand': 0.11,
                      'note': 'The ground is today’s, from lidar. Traced buildings’ heights are assumed from their material.', 'panels': [{'build': 'b'}]}
            saved = C.CREDIT, C.CREDIT_DERIVED
            C.CREDIT, C.CREDIT_DERIVED = C.design_credit(design, builds), True
            try:
                img = C.compose(design, (24, 36), builds, {'r': {'box': [0, 0, 1, 1]}}, 300, 1 / 2,
                                C.smallest_scale(spec, (24, 36)), C.stamped_faces(spec, (24, 36)))
            finally:
                C.CREDIT, C.CREDIT_DERIVED = saved
        ink = np.asarray(img.convert('L')) < 200
        H, W = ink.shape
        m = round(W * 0.05)
        reserve = C.block_reserve(36, 300, 1 / 2, C.stamped_faces(spec, (24, 36)))
        self.assertFalse(ink[H - m - round(H * 0.03):H - m, round(W - m - reserve):W - m].any())   # the block's corner is paper
        self.assertTrue(ink[H - m - round(W * 0.19 * 0.4):H - m, m:m + round(W * 0.3)].any())       # the credit, low at the left


class Balanced(unittest.TestCase):
    def test_no_word_is_left_alone(self):
        from PIL import Image, ImageDraw, ImageFont
        d = ImageDraw.Draw(Image.new('RGB', (4, 4)))
        f = ImageFont.truetype(C.FONT['italic'], 40)
        text = 'The ground is today’s, from lidar: cuts and fills made since show in it.'
        w = d.textlength(text, font=f) - d.textlength(' it.', font=f) + 2   # greedy leaves "it." alone
        self.assertEqual(C.wrap_words(d, text, f, w)[-1], 'it.')
        got = C.balanced(d, text, f, w)
        self.assertEqual(len(got), 2)
        self.assertGreater(min(len(x) for x in got), 20)
        self.assertEqual(' '.join(got), text)


if __name__ == '__main__':
    unittest.main()
