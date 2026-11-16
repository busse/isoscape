"""Tests for release records: every print file and product a design has, and redraws.
Run from tools/release/: python3 -m unittest test_record"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'print')]
import check, record, stamp  # noqa: E402


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').close()


class Outputs(unittest.TestCase):
    def test_every_size_of_a_prints_map_is_an_output(self):
        # The Broad Street cutaway: one print file per size, text sized for each.
        d = {'print': 'cut_32x24.jpg', 'print_dir': 'print-files/bss', 'prints': {'18x24': 'cut_24x18.jpg', '24x32': 'cut_32x24.jpg'}}
        with tempfile.TemporaryDirectory() as store:
            pfile, others, canvas = record.outputs_of(store, d, 'cut')
            self.assertEqual(os.path.basename(pfile), 'cut_32x24.jpg')
            self.assertEqual([os.path.basename(p) for p in others], ['cut_24x18.jpg'])
            self.assertEqual(canvas, [])

    def test_canvas_files_are_found_beside_or_under_canvas(self):
        d = {'print': 'g-v3_36x24.jpg', 'canvas': 'g-v3_canvas-{w}x{h}.jpg'}
        with tempfile.TemporaryDirectory() as store:
            for n in ('g-v3_canvas-18x12.jpg', 'g-v3_canvas-30x20.jpg', 'g-v2_canvas-18x12.jpg'): touch(os.path.join(store, 'print-files', 'canvas', n))
            _, others, canvas = record.outputs_of(store, d, 'g')
            self.assertEqual(others, [])
            self.assertEqual([os.path.basename(c) for c in canvas], ['g-v3_canvas-18x12.jpg', 'g-v3_canvas-30x20.jpg'])

    def test_check_reads_every_output(self):
        r = {'outputs': {'print': {'file': 'a'}, 'prints': [{'file': 'b'}], 'canvas': [{'file': 'c'}]}}
        self.assertEqual([o['file'] for o in check.outputs(r)], ['a', 'b', 'c'])
        self.assertEqual([o['file'] for o in check.outputs({'outputs': {'print': {'file': 'a'}, 'canvas': []}})], ['a'])


class Products(unittest.TestCase):
    def test_the_merged_product_comes_first_then_per_format_ones(self):
        shop = {'g-print': {'design': 'g', 'id': 'gid://1', 'format': 'Print', 'status': 'DRAFT'},
                'h-print': {'design': 'h', 'id': 'gid://2', 'format': 'Print', 'status': 'ACTIVE'}}
        merged = {'g': {'id': 'gid://9', 'handle': 'g', 'status': 'DRAFT', 'variants': {'A': '1', 'B': '2'}}}
        got = record.products_of('g', shop, merged)
        self.assertEqual([p['handle'] for p in got], ['g', 'g-print'])
        self.assertEqual(got[0]['format'], 'all (merged)')
        self.assertEqual(got[0]['variants'], 2)

    def test_a_design_sold_only_as_a_merged_product_still_lists_it(self):
        got = record.products_of('c', {}, {'c': {'id': 'gid://5', 'handle': 'c', 'status': 'ACTIVE', 'variants': {}}})
        self.assertEqual([(p['handle'], p['status']) for p in got], [('c', 'ACTIVE')])
        self.assertEqual(record.products_of('c', {}, None), [])


class Redraw(unittest.TestCase):
    def test_names(self):
        self.assertEqual(stamp.unversioned('gwynns-island-v2_36x24.jpg'), 'gwynns-island_36x24.jpg')
        self.assertEqual(stamp.unversioned('gwynns-island-v2_canvas-18x12.jpg'), 'gwynns-island_canvas-18x12.jpg')
        self.assertEqual(stamp.versioned('gwynns-island_canvas-18x12.jpg', 3), 'gwynns-island-v3_canvas-18x12.jpg')

    def test_a_redraw_stamps_the_new_files_into_the_current_files_folders(self):
        d = {'print': 'g-v2_36x24.jpg', 'canvas': 'g-v2_canvas-{w}x{h}.jpg'}
        with tempfile.TemporaryDirectory() as store:
            touch(os.path.join(store, 'print-files', 'g-v2_36x24.jpg'))
            touch(os.path.join(store, 'print-files', 'canvas', 'g-v2_canvas-18x12.jpg'))
            base = os.path.join(store, 'print-files', 'drawn', 'g-v3')
            touch(os.path.join(base, 'g_36x24.jpg'))
            touch(os.path.join(base, 'canvas', 'g_canvas-18x12.jpg'))
            got = stamp.redraw_files(store, d, 'g', base)
            self.assertEqual(got, [(os.path.join(base, 'g_36x24.jpg'), os.path.join(store, 'print-files')),
                                   (os.path.join(base, 'canvas', 'g_canvas-18x12.jpg'), os.path.join(store, 'print-files', 'canvas'))])

    def test_a_redraw_missing_a_file_stops(self):
        d = {'print': 'g-v2_36x24.jpg'}
        with tempfile.TemporaryDirectory() as store:
            touch(os.path.join(store, 'print-files', 'g-v2_36x24.jpg'))
            with self.assertRaises(SystemExit):
                stamp.redraw_files(store, d, 'g', os.path.join(store, 'nowhere'))

    def test_check_restamps_a_redraw(self):
        self.assertIn('redraw', check.STAMPED)
        self.assertIn('stamp', check.STAMPED)


if __name__ == '__main__':
    unittest.main()
