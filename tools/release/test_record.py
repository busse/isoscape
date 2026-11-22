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

    def test_a_redraw_with_canvas_files_is_recorded(self):
        # record.from_redraw over a stamp log with a print and two canvas files (the composed
        # print is pinned to its builds by from_spec, stubbed here).
        log = {f'g-v3{s}': {'design': 'g', 'version': 3, 'base': f'print-files/drawn/g-v3/{b}', 'base_sha256': 'x', 'redraw': True,
                            'info': {'version': '3'}, 'at': {}, 'tools': {'tools/release/stamp.py': 'y'}}
               for s, b in (('_36x24.jpg', 'g_36x24.jpg'), ('_canvas-30x20.jpg', 'canvas/g_canvas-30x20.jpg'), ('_canvas-18x12.jpg', 'canvas/g_canvas-18x12.jpg'))}
        with tempfile.TemporaryDirectory() as store:
            for v in log.values(): touch(os.path.join(store, v['base']))
            spec, record.from_spec = record.from_spec, lambda key, d, made: ('compose', {'run': ['c'], 'pinned': 'p'}, [{'build': 'b'}], {'tools/print/spec.json': 'z'})
            try:
                kind, recipe, scenes, inputs = record.from_redraw(store, 'g', {'version': 3}, log)
            finally:
                record.from_spec = spec
        self.assertEqual(kind, 'redraw')
        self.assertEqual(scenes, [{'build': 'b'}])
        self.assertIn('canvas.py', recipe['run'][1])
        self.assertTrue(recipe['run'][1].endswith('18x12 30x20'))
        self.assertIn('--base print-files/drawn/g-v3', recipe['run'][2])
        self.assertEqual(len(recipe['files']), 3)

    def test_check_restamps_a_redraw(self):
        self.assertIn('redraw', check.STAMPED)
        self.assertIn('stamp', check.STAMPED)


class Editorial(unittest.TestCase):
    """record.py --editorial and check.py --editorial: a released piece in no store."""
    def spec(self, root):
        os.makedirs(os.path.join(root, 'tools'))
        open(os.path.join(root, 'tools', 'make.py'), 'w').write(
            'import sys, os\nos.makedirs(os.path.dirname(sys.argv[2]) or ".", exist_ok=True)\n'
            'open(sys.argv[2], "w").write(open(os.path.join(sys.argv[1], "in.txt")).read().upper())\n')
        os.makedirs(os.path.join(root, 'art')); open(os.path.join(root, 'art', 'a.txt'), 'w').write('HELLO')
        return {'design': 'ed', 'title': 'Ed', 'version': 1, 'asset_version': '1.0.0',
                'recipe': {'tool': 'tools/make.py', 'run': ['python3 tools/make.py <ds> art/a.txt'],
                           'steps': [{'name': 'art', 'run': [sys.executable, 'tools/make.py', '{ds}', '{out}/a.txt'],
                                      'needs': {'ds': {'what': 'data', 'where': 'elsewhere', 'files': ['in.txt']}},
                                      'makes': {'out/a.txt': 'art/a.txt'}}]},
                'inputs': ['tools/make.py'], 'outputs': {'print': 'art/a.txt'}, 'shown': {'explorer': 'x#/ed'}}

    def make(self, root):
        import json
        sp = os.path.join(root, 'spec.json'); json.dump(self.spec(root), open(sp, 'w'))
        old = record.ISO
        record.ISO = root
        try: r = record.editorial(sp, True)
        finally: record.ISO = old
        return r

    def test_the_record_has_no_store_and_pins_every_file(self):
        with tempfile.TemporaryDirectory() as root:
            r = self.make(root)
        self.assertEqual((r['kind'], r['for_sale'], r['version'], r['asset_version']), ('editorial', False, 1, '1.0.0'))
        self.assertNotIn('store', r)
        self.assertEqual(set(r['inputs']), {'tools/make.py', 'spec.json'})
        self.assertEqual(r['outputs']['print']['file'], 'art/a.txt')
        self.assertEqual(r['outputs']['canvas'], [])
        self.assertEqual(r['scenes'], [])

    def test_a_draft_is_never_recorded(self):
        with tempfile.TemporaryDirectory() as root:
            import json
            s = self.spec(root); s['asset_version'] = '1.0.0-rc2'
            sp = os.path.join(root, 'spec.json'); json.dump(s, open(sp, 'w'))
            with self.assertRaises(SystemExit): record.editorial(sp)

    def test_check_finds_a_changed_file_and_rebuilds_from_the_recipe(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as ds:
            r = self.make(root)
            r['isoscape']['commit'] = '0' * 40
            self.assertEqual([p[0] for p in check.editorial_problems(r, root)], ['commit not in repo'])
            # no data here: the step is not run, and says exactly what it lacks
            got = check.editorial_rebuild(r, {}, root)
            self.assertEqual(got['art']['result'], 'not run')
            self.assertIn('--data ds=<folder>', got['art']['missing'][0])
            self.assertEqual(check.editorial_rebuild(r, {'ds': ds}, root)['art']['missing'], ['ds: in.txt'])
            open(os.path.join(ds, 'in.txt'), 'w').write('hello')
            got = check.editorial_rebuild(r, {'ds': ds}, root)['art']
            self.assertEqual(got['result'], 'reproduced')
            self.assertEqual(got['files']['art/a.txt'], {'same': True, 'how': 'identical bytes'})
            self.assertIn('ds/in.txt', got['data_sha256'])
            open(os.path.join(ds, 'in.txt'), 'w').write('other')
            self.assertEqual(check.editorial_rebuild(r, {'ds': ds}, root)['art']['result'], 'differs')
            open(os.path.join(root, 'art', 'a.txt'), 'w').write('changed')
            self.assertIn(('output changed', 'art/a.txt'), check.editorial_problems(r, root))

    def test_a_pdf_that_differs_only_in_its_creation_date_is_the_same(self):
        with tempfile.TemporaryDirectory() as t:
            a, b = os.path.join(t, 'a.pdf'), os.path.join(t, 'b.pdf')
            open(a, 'wb').write(b"%PDF-1.4\n<< /Producer (x) /CreationDate (D:20261122114346-04'00') >>\n")
            open(b, 'wb').write(b"%PDF-1.4\n<< /Producer (x) /CreationDate (D:20261122130610-04'00') >>\n")
            self.assertEqual(check.compare(a, b), (True, 'identical but for the PDF creation date'))


if __name__ == '__main__':
    unittest.main()
