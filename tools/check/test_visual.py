"""Tests for the comparison in visual.py. Run from tools/check/: python3 -m unittest"""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import visual  # noqa: E402


def scene(h=300, w=400, seed=1):
    """A map-like test image: flat paper, a few filled blocks with dark one-pixel outlines."""
    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), (236, 231, 220), np.uint8)
    for _ in range(12):
        y, x = rng.integers(10, h - 60), rng.integers(10, w - 80)
        bh, bw = rng.integers(20, 50), rng.integers(30, 70)
        img[y:y + bh, x:x + bw] = rng.integers(150, 230, 3)
        img[y, x:x + bw] = img[y + bh - 1, x:x + bw] = img[y:y + bh, x] = img[y:y + bh, x + bw - 1] = (60, 60, 60)
    return img


class Compare(unittest.TestCase):
    def test_identical_passes(self):
        a = scene()
        r = visual.compare(a, a.copy())
        self.assertTrue(r['ok'])
        self.assertEqual(r['raw'], 0)
        self.assertEqual(r['changed'], 0)
        self.assertEqual(r['mean'], 0)

    def test_shifted_block_fails(self):
        a = scene()
        b = a.copy()
        block = a[100:150, 100:160].copy()
        b[100:150, 100:160] = (236, 231, 220)
        b[100:150, 112:172] = block  # the same block, 12 px to the right
        r = visual.compare(a, b)
        self.assertFalse(r['ok'])
        self.assertGreater(r['changed'], visual.MAX_CHANGED)
        self.assertTrue(r['mask'][100:150, 100:172].any())
        self.assertFalse(r['mask'][:80].any())

    def test_new_dot_fails(self):
        # One stray 3 x 3 dark dot, the size of a corner dot at print scale.
        a = scene()
        b = a.copy()
        b[20:23, 300:303] = (40, 40, 40)
        self.assertFalse(visual.compare(a, b)['ok'])

    def test_antialiasing_noise_passes(self):
        # Every pixel off by up to 2 levels, and isolated edge pixels off by up to 60: what a
        # sub-pixel shift of an outline or a different rasterizer build does to antialiasing.
        a = scene()
        rng = np.random.default_rng(7)
        b = a.astype(np.int16) + rng.integers(-2, 3, a.shape)
        edges = np.argwhere((a == 60).all(axis=2))
        pick = edges[rng.choice(len(edges), len(edges) // 40, replace=False)]
        for y, x in pick: b[y, x] += rng.integers(-60, 61)
        b = np.clip(b, 0, 255).astype(np.uint8)
        r = visual.compare(a, b)
        self.assertGreater(r['raw'], 50)  # nearly every pixel differs at all
        self.assertTrue(r['ok'], r)

    def test_shade_change_fails(self):
        # A fill nudged by 10 levels everywhere it appears (a palette change).
        a = scene()
        b = a.copy()
        fill = (a != (236, 231, 220)).any(axis=2) & (a != 60).any(axis=2)
        b[fill] = np.clip(a[fill].astype(int) - 10, 0, 255)
        self.assertFalse(visual.compare(a, b)['ok'])

    def test_size_change_fails(self):
        a = scene()
        r = visual.compare(a, a[:-10])
        self.assertFalse(r['ok'])
        self.assertIn('size changed', r['note'])


class Quantize(unittest.TestCase):
    def test_requantizing_with_the_stored_palette_is_exact(self):
        # The baseline is stored as a palette PNG; check maps the new crop to that palette, so
        # an unchanged crop must come out exactly as stored.
        a = scene()
        a[:, :, 0] = np.clip(a[:, :, 0].astype(int) + np.arange(a.shape[1]) // 8, 0, 255)  # a gradient: > 256 colors
        q = visual.quantize(a)
        again = visual.quantize(a, q)
        self.assertTrue((np.asarray(q.convert('RGB')) == np.asarray(again.convert('RGB'))).all())


class CropsOutside(unittest.TestCase):
    view = {'name': 'v', 'args': ['v'], 'width': 400, 'crops': [
        {'name': 'top', 'x': 0, 'y': 0, 'w': 200, 'h': 100},
        {'name': 'foot', 'x': 0, 'y': 250, 'w': 200, 'h': 100}]}

    def test_outside_crops(self):
        # A 400 px render of a 4:3 viewBox is 300 px tall: the foot crop (250 + 100) is past it.
        bad, w, h = visual.outside_crops(self.view, [0, 0, 800, 600])
        self.assertEqual(bad, ['foot'])
        self.assertEqual((w, h), (400, 300))
        self.assertEqual(visual.outside_crops(self.view, [0, 0, 800, 800])[0], [])

    def test_check_reports_a_crop_outside_the_render_instead_of_crashing(self):
        import json, tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            base, out = os.path.join(tmp, 'base'), os.path.join(tmp, 'out')
            os.makedirs(os.path.join(base, 'v'))
            img = scene(100, 200)
            for c in self.view['crops']:
                visual.save_png(visual.quantize(img), os.path.join(base, 'v', c['name'] + '.png'))
            json.dump({'width': 400, 'args': ['v'], 'warnings': [], 'svg_sha256': 'old', 'data': {},
                       'crops': self.view['crops']}, open(os.path.join(base, 'v', 'baseline.json'), 'w'))
            svg = os.path.join(tmp, 'v.svg')
            open(svg, 'w').write('<svg/>')

            def fake_render(svg_, width, box, dest):
                visual.save_png(img, dest)
            with mock.patch.multiple(visual, BASE=base, OUT=out, data_files=lambda v: [],
                                     build=lambda v: (svg, [0, 0, 800, 600], [], 0.0),
                                     render_crop=fake_render, sha_file=lambda p: 'new'):
                code = visual.check([self.view], 1)
            self.assertEqual(code, 1)
            report = open(os.path.join(out, 'index.html')).read()
            self.assertIn('outside the render', report)
            self.assertTrue(os.path.exists(os.path.join(out, 'crops', 'v', 'top-new.png')))
            self.assertFalse(os.path.exists(os.path.join(out, 'crops', 'v', 'foot-new.png')))


if __name__ == '__main__':
    unittest.main()
