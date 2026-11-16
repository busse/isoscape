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


if __name__ == '__main__':
    unittest.main()
