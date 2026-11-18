"""Tests for the plate register and the title block. Run from tools/release/: python3 -m unittest"""
import hashlib, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'print')]
from PIL import Image, ImageDraw  # noqa: E402
import plates, stamp, titleblock  # noqa: E402

# A fixed block with no kind, as every title block was drawn before kinds existed (Pillow 12.3).
FIXED = {'collection': 'Places through time', 'set': 'Richmond', 'piece': '1925', 'plate': 'RVA-01', 'version': '1',
         'drawn': '2026', 'location': '37.534° N 77.427° W', 'facing': '351°'}
FIXED_SHA = '167edba5b5162249e77a1b8930171619f2c27daae24b42f03a9245c0eb807d88'


def pt(units, long_in):
    """A size in block units, in points, on a sheet `long_in` inches long at 300 dpi."""
    return units * stamp.size_u(long_in, 300) / 300 * 72


class Register(unittest.TestCase):
    def test_register_is_sound(self):
        self.assertTrue(plates.check())

    def test_kind_only_where_the_plate_names_one(self):
        self.assertNotIn('kind', plates.info('richmond-1925'))
        self.assertNotIn('kind', plates.info('broad-street-1943-menu'))
        cut = plates.info('broad-street-1943-cutaway')
        self.assertEqual(cut['kind'], 'Building cutaway')
        self.assertEqual(cut['plate'], 'BSS-15')
        self.assertEqual(cut['facing'], '342°')     # the cutaway region's own camera, not the set map's

    def test_set_codes_of_three_or_four_letters(self):
        for ok in ('RVA-01', 'BSS-M', 'BPPH-01', 'BPPH-100'):
            self.assertTrue(plates.PLATE.match(ok), ok)
        for bad in ('RV-01', 'BPPHX-01', 'bpph-01', 'BPPH-1', 'BPPH01'):
            self.assertFalse(plates.PLATE.match(bad), bad)
        cut = plates.info('pump-house-cutaway')
        self.assertEqual((cut['plate'], cut['set'], cut['kind']), ('BPPH-01', 'Byrd Park Pump House, 1885', 'Building cutaway'))
        self.assertTrue(plates.cutaway_of('pump-house-cutaway')[0].endswith('pump-house-1885-pumped.json'))   # d3, by its key
        self.assertIn('BPPH-01', [r['plate'].replace('·', '-') for r in plates.rows()])


class Block(unittest.TestCase):
    def test_a_block_without_a_kind_is_unchanged(self):
        im = titleblock.block(dict(FIXED), 1.0)
        if not Image.__version__.startswith('12.3'):
            self.skipTest('the fixed hash was made with Pillow 12.3')
        self.assertEqual(hashlib.sha256(im.tobytes()).hexdigest(), FIXED_SHA)

    def test_the_kind_is_drawn_full_size_and_legible(self):
        a = titleblock.block(dict(FIXED), 1.0)
        b = titleblock.block(dict(FIXED, kind='Building cutaway'), 1.0)
        self.assertEqual(a.size, b.size)              # the block keeps its size
        self.assertNotEqual(a.tobytes(), b.tobytes())
        d = ImageDraw.Draw(Image.new('RGB', (4, 4)))
        width = d.textlength('Building cutaway', font=titleblock._font('regular', titleblock.KIND_SIZE))
        self.assertLess(width, titleblock.NAME_W - 36)   # fits without shrinking
        self.assertGreaterEqual(pt(titleblock.KIND_SIZE, 24), 7.0)


if __name__ == '__main__':
    unittest.main()
