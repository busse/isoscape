"""Tests for the production board (board.py) and asset versions in stamp.py, record.py and check.py.
Run from tools/release/: python3 -m unittest test_board"""
import copy, datetime, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'print')]
import board, check, record, stamp  # noqa: E402

PLATES = {'plates': [{'plate': 'BSS-07', 'design': 'bss-07'}, {'plate': 'BSS-M', 'design': 'bss-map'}]}
INDEX = {'bss-07': {'current': 3}, 'bss-map': {'current': 2}}


def entry(**kw):
    e = {'title': 'T', 'plate': None, 'kind': 'set box', 'stage': 'final production', 'status': 'active', 'asset_version': '3.0.0',
         'published_version': 3, 'live_version': 3, 'on_sale': True, 'orders': 'unknown', 'rounds': 0, 'waiting_on': 'nothing',
         'decision': None, 'accepted_faults': [], 'planned_edition': None, 'last_inspected': None, 'branch': None,
         'worktree': None, 'links': []}
    e.update(kw)
    return e


def good():
    return {'items': {'bss-07': entry(plate='BSS-07'),
                      'bss-map': entry(plate='BSS-M', kind='set map', stage='final draft', asset_version='3.0.0-rc1', published_version=2,
                                       live_version=None, on_sale=False, rounds=1, waiting_on='owner', decision='approve release')}}


def bad(b):
    return board.problems(b, PLATES, INDEX)


class Check(unittest.TestCase):
    def test_a_good_board_passes(self):
        self.assertEqual(bad(good()), [])

    def test_every_plate_needs_an_entry(self):
        b = good(); del b['items']['bss-map']
        self.assertTrue(any('BSS-M: no board entry' in x for x in bad(b)))

    def test_live_version_must_be_the_latest_record(self):
        b = good(); b['items']['bss-07'].update(published_version=2, live_version=2, asset_version='2.0.0')
        self.assertTrue(any('latest release record v3' in x for x in bad(b)))

    def test_on_sale_and_live_version_agree(self):
        b = good(); b['items']['bss-07']['on_sale'] = False
        self.assertTrue(any('disagree' in x for x in bad(b)))

    def test_a_draft_is_a_prerelease_of_the_next_edition(self):
        b = good(); b['items']['bss-map']['asset_version'] = '2.0.0-rc1'
        self.assertTrue(any('prerelease of the next edition' in x for x in bad(b)))
        b['items']['bss-map']['asset_version'] = '3.0.0-d1'
        self.assertTrue(any('a final draft is -rcN' in x for x in bad(b)))

    def test_a_revision_needs_no_orders(self):
        b = good(); b['items']['bss-07'].update(stage='final draft', asset_version='3.1.0-rc1', rounds=1)
        self.assertTrue(any('needs orders = 0' in x for x in bad(b)))
        b['items']['bss-07']['orders'] = 0
        self.assertEqual(bad(b), [])

    def test_the_third_fix_round_needs_the_owners_say_so(self):
        b = good(); b['items']['bss-map'].update(asset_version='3.0.0-rc3', rounds=3)
        self.assertTrue(any("say-so" in x for x in bad(b)))
        b['items']['bss-map']['budget_note'] = 'owner, November 20: one more round'
        self.assertEqual(bad(b), [])

    def test_waiting_on_the_owner_names_a_decision(self):
        b = good(); b['items']['bss-map']['decision'] = ''
        self.assertTrue(any('names no decision' in x for x in bad(b)))

    def test_planned_edition_has_a_stated_reason(self):
        b = good(); b['items']['bss-07']['planned_edition'] = {'reason': 'because', 'fixes': ['x']}
        self.assertTrue(any('reason' in x for x in bad(b)))

    def test_site_stages(self):
        b = good(); b['items']['x'] = entry(kind='site', stage='owner test', asset_version=None, published_version=None, live_version=None,
                                            plate=None, on_sale=False, waiting_on='owner', decision='try it on a phone')
        self.assertEqual(bad(b), [])
        b['items']['x']['stage'] = 'final draft'
        self.assertTrue(any('not a stage of a site' in x for x in bad(b)))

    def test_story_stages_are_editorial(self):
        b = good(); b['items']['s'] = entry(kind='story', stage='outline', asset_version=None, published_version=None, live_version=None,
                                            on_sale=False, orders=None)
        self.assertEqual(bad(b), [])
        b['items']['s']['stage'] = 'final draft'
        self.assertTrue(any('not a stage of a story' in x for x in bad(b)))


class Editorial(unittest.TestCase):
    """An editorial piece: released (final production, an editorial record) but not for sale, with no plate."""
    def board(self, **kw):
        b = good()
        b['items']['poster'] = entry(kind='print', plate=None, asset_version='1.0.0', published_version=1, live_version=None,
                                     on_sale=False, orders=0, **kw)
        return b

    def index(self):
        return dict(INDEX, poster={'current': 1, 'kind': 'editorial', 'for_sale': False})

    def test_released_unsold_and_unplated_is_legal(self):
        self.assertEqual(board.problems(self.board(), PLATES, self.index()), [])

    def test_without_its_record_it_is_not_released(self):
        self.assertTrue(any('poster: 1.0.0: final production but no release record' in x for x in board.problems(self.board(), PLATES, INDEX)))

    def test_an_editorial_record_never_backs_a_sale(self):
        b = self.board(); b['items']['poster'].update(on_sale=True, live_version=1)
        self.assertTrue(any('release record is editorial' in x for x in board.problems(b, PLATES, self.index())))


class Versions(unittest.TestCase):
    def test_file_suffix_prints_only_what_is_needed(self):
        self.assertEqual([board.file_suffix(a) for a in ('3.0.0', '3.1.0', '3.0.1', '3.1.2')], ['v3', 'v3.1', 'v3.0.1', 'v3.1.2'])
        with self.assertRaises(ValueError): board.file_suffix('3.0.0-rc1')

    def test_stamp_names_and_unnames_revision_files(self):
        self.assertEqual(stamp.versioned('b-07-v3_24x18.jpg', 'v3.1'), 'b-07-v3.1_24x18.jpg')
        self.assertEqual(stamp.versioned('b-07-v3.1_canvas-24x18.jpg', 4), 'b-07-v4_canvas-24x18.jpg')
        self.assertEqual(stamp.unversioned('b-07-v3.1_24x18.jpg'), 'b-07_24x18.jpg')
        self.assertEqual(stamp.unversioned('richmond-2026-v4_36x24.jpg'), 'richmond-2026_36x24.jpg')

    def test_record_names_and_revisions(self):
        self.assertEqual(record.record_name('3.0.0'), 'v3.json')
        self.assertEqual(record.record_name('3.1.0'), 'v3.1.json')
        self.assertEqual(record.asset_of({'version': 3}), '3.0.0')
        self.assertTrue(record.is_revision('3.1.0', '3.0.0'))
        self.assertFalse(record.is_revision('4.0.0', '3.0.0'))
        self.assertFalse(record.is_revision('3.0.1', '3.0.0'))


class RevisionGate(unittest.TestCase):
    def items(self, **kw):
        return {'bss-07': dict(entry(plate='BSS-07'), **kw)}

    def test_unknown_orders_refuse(self):
        why = record.revision_gate('bss-07', '3.1.0', self.items(), '')
        self.assertIn('orders = \'unknown\'', why)
        self.assertIn('edition 4', why)

    def test_old_counts_refuse(self):
        why = record.revision_gate('bss-07', '3.1.0', self.items(orders=0, orders_counted='2026-11-01'), '', datetime.date(2026, 11, 18))
        self.assertIn('count them again', why)

    def test_on_sale_needs_a_changes_line(self):
        it = self.items(orders=0, orders_counted='2026-11-18')
        self.assertIn('pages/changes.md', record.revision_gate('bss-07', '3.1.0', it, '', datetime.date(2026, 11, 18)))
        ok = '- Main Street Station (BSS·07), corrected in place as revision 3.1: the station drawn to its measured height.'
        self.assertIsNone(record.revision_gate('bss-07', '3.1.0', it, ok, datetime.date(2026, 11, 18)))


class Edit(unittest.TestCase):
    def test_set_appends_faults_with_boxes_and_logs_stage_changes(self):
        b = good()
        e = board.set_fields(b, 'bss-07', ['accepted_faults+=a street meets a 1940 building @ 6020,1215,6270,1420',
                                           'planned_edition.reason=improvement', 'planned_edition.fixes+=bigger labels',
                                           'stage=working draft', 'asset_version=4.0.0-d1', 'rounds=1'])
        self.assertEqual(e['accepted_faults'], [{'what': 'a street meets a 1940 building', 'box': [6020, 1215, 6270, 1420]}])
        self.assertEqual(e['planned_edition'], {'reason': 'improvement', 'fixes': ['bigger labels']})
        self.assertTrue(e['log'][-1].endswith('final production -> working draft'))
        self.assertEqual(e['rounds'], 1)
        self.assertEqual(bad(b), [])

    def test_set_refuses_an_unknown_key_without_new(self):
        with self.assertRaises(SystemExit): board.set_fields(good(), 'nope', ['stage=research'])


class Page(unittest.TestCase):
    def test_the_page_is_unlisted_and_has_no_private_fields(self):
        b = good(); b['updated'] = '2026-11-18'
        b['items']['bss-07'].update(notes='SECRET-NOTE', branch='SECRET-BRANCH', links=['/SECRET/path'], orders=7)
        text = board.page(b)
        self.assertIn('unlisted: true', text)
        self.assertIn('title: Production board', text)
        for s in ('SECRET', '| 7 |'): self.assertNotIn(s, text)
        self.assertIn('approve release', text)

    def test_show_lists_the_owners_decisions_first(self):
        out = board.show(dict(good(), updated='2026-11-18'))
        self.assertLess(out.index('approve release'), out.index('FINAL DRAFT'))


class Orders(unittest.TestCase):
    def test_counts_come_from_the_stores_orders_json(self):
        b = good()
        with tempfile.TemporaryDirectory() as store:
            os.makedirs(os.path.join(store, 'pipeline', 'state'))
            json.dump({'counted': '2026-11-19T10:00:00+00:00', 'designs': {'bss-07': 0, 'bss-map': 2}},
                      open(os.path.join(store, 'pipeline', 'state', 'orders.json'), 'w'))
            self.assertEqual(board.take_orders(b, store), (2, '2026-11-19'))
        self.assertEqual((b['items']['bss-07']['orders'], b['items']['bss-map']['orders']), (0, 2))


class CheckReadsRevisions(unittest.TestCase):
    def test_superseded_files_must_stay(self):
        with tempfile.TemporaryDirectory() as store:
            json.dump({}, open(os.path.join(store, 'files.json'), 'w'))
            os.makedirs(os.path.join(store, 'pipeline')); json.dump({}, open(os.path.join(store, 'pipeline', 'files.json'), 'w'))
            r = {'outputs': {'print': {'file': 'missing.jpg', 'missing': True}, 'canvas': []}, 'data': {}, 'scenes': [],
                 'kind': 'revision', 'recipe': {}, 'isoscape': {'commit': '0' * 40},
                 'supersedes': {'record': 'v3.json', 'outputs': [{'file': 'old-v3_24x18.jpg', 'sha256': 'x'}]}}
            kinds = [p[0] for p in check.problems(store, r)]
            self.assertIn('superseded output missing', kinds)


class TheBoardItself(unittest.TestCase):
    def test_the_committed_board_checks(self):
        self.assertEqual(board.problems(board.load()), [])


if __name__ == '__main__':
    unittest.main()
