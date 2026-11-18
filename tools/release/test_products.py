"""Tests for shop.products (products.py). Run from tools/release/: python3 -m unittest test_products"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import products as P  # noqa: E402

SETS = {'bss-': ('broad-street', 'place'), 'stc-': ('streetcars', 'stop')}
DESIGNS = {'bss-01-ay': {'explore': 'lines:1943@1,2,6'}, 'bss-03-old': {'explore': 'lines:1943@3,3,6'},
           'bss-03-new': {'explore': 'lines:1943@4,4,6'}, 'bss-map': {'explore': 'lines:1943'},
           'bss-menu': {'explore': 'lines:1943'}, 'stc-01-park': {'explore': 'cars:1925@5,5,6'},
           'bss-cutaway': {}, 'richmond-1925': {'explore': 'town:1925'}}
MERGED = {k: {'handle': k + '-h', 'status': 'ACTIVE'} for k in DESIGNS}
BOARD = {'bss-01-ay': {'kind': 'set box', 'on_sale': True}, 'bss-03-old': {'kind': 'set box', 'on_sale': False},
         'bss-03-new': {'kind': 'set box', 'on_sale': True}, 'bss-map': {'kind': 'set map', 'on_sale': True},
         'bss-menu': {'kind': 'set menu', 'on_sale': True}, 'stc-01-park': {'kind': 'set box', 'on_sale': True},
         'bss-cutaway': {'kind': 'cutaway', 'on_sale': True}, 'richmond-1925': {'kind': 'print', 'on_sale': True}}


def run(merged=MERGED, board=BOARD):
    return P.products(DESIGNS, merged, board, SETS, 'https://shop.example/')


class Products(unittest.TestCase):
    def test_set_pieces_on_sale_by_their_view(self):
        out = run()
        self.assertEqual(set(out), {'lines:1943@1,2,6', 'lines:1943@4,4,6', 'lines:1943', 'cars:1925@5,5,6'})
        self.assertEqual(out['lines:1943@1,2,6'], [{'url': 'https://shop.example/products/bss-01-ay-h', 'label': 'Buy a print of this place ↗', 'design': 'bss-01-ay'}])
        self.assertEqual(out['cars:1925@5,5,6'][0]['label'], 'Buy a print of this stop ↗')

    def test_the_map_alone_comes_before_the_framed_map(self):
        self.assertEqual([p['design'] for p in run()['lines:1943']], ['bss-map', 'bss-menu'])
        self.assertEqual(run()['lines:1943'][1]['label'], 'Buy a print of the map with every place ↗')

    def test_off_sale_or_inactive_in_the_store_is_left_out(self):
        merged = dict(MERGED, **{'bss-01-ay': {'handle': 'x', 'status': 'DRAFT'}})
        self.assertNotIn('lines:1943@1,2,6', run(merged=merged))
        self.assertNotIn('lines:1943@3,3,6', run())

    def test_two_of_a_kind_at_one_view_is_refused(self):
        designs = dict(DESIGNS, **{'bss-03-new': {'explore': 'lines:1943@1,2,6'}})
        with self.assertRaises(SystemExit):
            P.products(designs, MERGED, BOARD, SETS, 'https://shop.example/')

    def test_a_piece_its_page_never_links_to_is_named(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, 'broad-street.md'), 'w').write('[See it on the map](https://x/#lines:1943@1,2,6) [Open the map](https://x/#lines:1943)')
            open(os.path.join(d, 'streetcars.md'), 'w').write('')
            bad = P.unlinked(run(), SETS, d)
        self.assertEqual(sorted(b.split(':')[0] for b in bad), ['bss-03-new', 'stc-01-park'])


if __name__ == '__main__':
    unittest.main()
