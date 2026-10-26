import copy
import importlib.util
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots.review import ReviewError, ReviewSession, compare_images, digest
from sunstone_screenshots import cli
from review_fixture import create_review_fixture


REVIEW_DEPS = bool(importlib.util.find_spec('PIL') and importlib.util.find_spec('skimage'))


@unittest.skipUnless(REVIEW_DEPS, 'Install requirements-review.txt to run image review tests.')
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = create_review_fixture(self.root)

    def session(self, **kwargs):
        return ReviewSession(self.root, self.run, self.root / 'inventory.csv', **kwargs)

    def item(self, session, name):
        return next(c for c in session.data['comparisons'].values() if c['asset'] == f'assets/images/{name}.png')

    def nominate(self, session, item, value=True):
        return session.nominate(item['id'], value, item['baseline']['sha256'], item['candidate']['sha256'])

    def test_identical_pixels_are_exactly_zero_even_with_different_png_encoding(self):
        from PIL import Image
        baseline = self.root / 'assets/images/same.png'
        new = self.run / 'screenshots/assets/images/same.png'
        with Image.open(baseline) as image:
            image.save(new, compress_level=0)
        self.assertNotEqual(digest(baseline), digest(new))
        compared = compare_images(baseline, new)
        self.assertEqual(compared['ssim'], 1)
        self.assertEqual(compared['change_percent'], 0)
        self.assertFalse(compared['changed'])

    def test_small_and_large_changes_have_increasing_structural_difference(self):
        from PIL import Image
        baseline = self.root / 'assets/images/same.png'
        candidate = self.run / 'screenshots/assets/images/same.png'
        with Image.open(baseline) as image:
            image.putpixel((45, 25), (200, 100, 70))
            image.save(candidate)
        small = compare_images(baseline, candidate)
        Image.new('RGB', (96, 64), '#101010').save(candidate)
        large = compare_images(baseline, candidate)
        self.assertGreater(small['change_percent'], 0)
        self.assertLess(small['change_percent'], large['change_percent'])
        self.assertGreater(large['change_percent'], 10)

    def test_dimension_changes_are_separate_and_images_are_never_resized(self):
        result = self.item(self.session(), 'resized')
        self.assertTrue(result['dimensions_changed'])
        self.assertIsNone(result['ssim'])
        self.assertIsNone(result['change_percent'])
        self.assertEqual(result['candidate']['width'], 80)
        self.assertTrue(result['can_substitute'])

    def test_missing_images_and_workflow_status_are_independent(self):
        session = self.session()
        docs = {doc['id']: doc for doc in session.data['documents']}
        self.assertEqual(docs['first']['status'], 'complete')
        self.assertEqual(docs['second']['status'], 'failed')
        self.assertEqual(docs['third']['status'], 'not_run')
        self.assertEqual(docs['second']['missing_candidate'], 1)
        self.assertEqual(docs['second']['missing_baseline'], 1)
        self.assertEqual(docs['third']['missing_candidate'], 0)
        self.assertIn('RUNNING', docs['second']['failure'])
        self.assertFalse(self.item(session, 'missing-new')['can_substitute'])
        self.assertFalse(self.item(session, 'missing-old')['can_substitute'])

    def test_markdown_reference_order_is_preserved(self):
        path = self.root / 'content/first.md'
        path.write_text('# Sunstone\n![Resized](/images/resized.png)\n![Same](/images/same.png)\n![Changed](/images/changed.png)\n')
        session = self.session()
        self.assertEqual([session.data['comparisons'][i['id']]['asset'] for i in session.data['documents'][0]['images']],
                         ['assets/images/resized.png', 'assets/images/same.png', 'assets/images/changed.png'])

    def test_suite_review_uses_each_group_artifact_directory(self):
        suite = self.root / 'suite'
        child = suite / '01-first'
        shutil.copytree(self.run, child)
        (suite / 'suite.json').write_text(json.dumps({'groups': [
            {'group': 'group.json', 'run_dir': '01-first', 'status': 'failed'}]}))
        session = ReviewSession(self.root, suite, self.root / 'inventory.csv')
        item = self.item(session, 'same')
        self.assertTrue(item['candidate']['exists'])
        self.assertTrue(item['replacement'].startswith('01-first/screenshots/'))
        self.nominate(session, item)
        self.assertTrue((suite / 'review/substitutions.json').is_file())

    def test_shared_nomination_has_one_target_and_all_document_consumers(self):
        second = json.loads((self.root / 'second.json').read_text())
        source = json.loads((self.root / 'first.json').read_text())['screenshots'][0]
        second['screenshots'].append(dict(source, id='second.shared', doc='content/second.md',
                                          sharedFrom={'manifest': 'first.json', 'id': source['id']}))
        (self.root / 'second.json').write_text(json.dumps(second))
        with (self.root / 'content/second.md').open('a') as stream:
            stream.write('\n![Sunstone shared](/images/same.png)\n')
        session = self.session()
        item = self.item(session, 'same')
        self.assertEqual(set(item['documents']), {'first', 'second'})
        self.nominate(session, item)
        saved = json.loads(session.selection_file.read_text())
        self.assertEqual(len(saved['selections']), 1)
        self.assertEqual(set(saved['selections'][0]['documents']), {'first', 'second'})

    def test_substitution_is_persistent_hash_bound_and_never_applies_files(self):
        session = self.session()
        item = self.item(session, 'changed')
        before = (self.root / item['asset']).read_bytes()
        self.nominate(session, item)
        saved = json.loads(session.selection_file.read_text())
        self.assertEqual(saved['selections'][0]['asset'], item['asset'])
        self.assertEqual(saved['selections'][0]['baseline_sha256'], item['baseline']['sha256'])
        self.assertEqual(saved['selections'][0]['candidate_sha256'], item['candidate']['sha256'])
        self.assertEqual(session.selection_file.stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.root / item['asset']).read_bytes(), before)
        reloaded = self.session()
        self.assertIn(item['id'], reloaded.view()['selected'])
        self.nominate(reloaded, item, False)
        self.assertEqual(reloaded.view()['selected'], [])

    def test_changed_files_reject_stale_nomination_and_make_saved_selection_stale(self):
        from PIL import Image
        session = self.session()
        item = self.item(session, 'same')
        self.nominate(session, item)
        Image.new('RGB', (96, 64), 'black').save(self.run / 'screenshots/assets/images/same.png')
        with self.assertRaisesRegex(ReviewError, 'contents changed'):
            self.nominate(session, item)
        refreshed = session.refresh()
        self.assertEqual(refreshed['selected'], [])
        self.assertIn(item['id'], refreshed['stale'])

    def test_missing_corrupt_and_outside_root_images_cannot_be_nominated(self):
        session = self.session()
        with self.assertRaisesRegex(ReviewError, 'Both images'):
            self.nominate(session, self.item(session, 'missing-new'))
        (self.run / 'screenshots/assets/images/changed.png').write_bytes(b'not an image')
        session.refresh()
        self.assertTrue(self.item(session, 'changed')['candidate']['error'])
        with self.assertRaisesRegex(ReviewError, 'Both images'):
            self.nominate(session, self.item(session, 'changed'))
        source = self.run / 'screenshots/assets/images/same.png'
        source.unlink()
        source.symlink_to(self.root / 'assets/images/same.png')
        with self.assertRaisesRegex(ReviewError, 'outside'):
            session.image_path(self.item(session, 'same')['id'], 'candidate')

    def test_legacy_run_requires_no_credential_or_vm_access(self):
        (self.run / 'workflow.json').unlink()
        with patch.object(cli.lab, 'connect', side_effect=AssertionError('No infrastructure access')):
            session = self.session(manifest='first.json')
        self.assertEqual(session.data['documents'][0]['status'], 'unknown')

    def test_partial_capture_only_marks_selected_outputs_as_expected(self):
        (self.run / 'screenshots/capture-results.json').write_text(json.dumps(dict(version=1, manifests={
            'first.json': dict(status='complete', expected_images=['assets/images/same.png'])})))
        session = self.session()
        self.assertTrue(self.item(session, 'same')['expected'])
        self.assertFalse(self.item(session, 'changed')['expected'])
        self.assertFalse(self.item(session, 'resized')['expected'])

    def test_standalone_output_directory_is_a_reviewable_run(self):
        (self.run / 'screenshots/capture-results.json').write_text(json.dumps(dict(version=1, manifests={
            'first.json': dict(status='complete', expected_images=['assets/images/same.png'])})))
        session = ReviewSession(self.root, self.run / 'screenshots', self.root / 'inventory.csv')
        self.assertTrue(self.item(session, 'same')['candidate']['exists'])
        self.assertEqual(session.data['documents'][0]['status'], 'complete')

    def test_multiple_candidates_for_the_same_target_are_not_silently_overwritten(self):
        session = self.session()
        first = self.item(session, 'same')
        second = dict(copy.deepcopy(first), id='other-candidate')
        session.data['comparisons'][second['id']] = second
        session.paths[second['id']] = session.paths[first['id']]
        self.nominate(session, first)
        with self.assertRaisesRegex(ReviewError, 'Another candidate'):
            self.nominate(session, second)

    def test_clear_selections_and_unknown_ids_are_safe(self):
        session = self.session()
        self.nominate(session, self.item(session, 'same'))
        self.assertEqual(session.clear()['selected'], [])
        with self.assertRaisesRegex(ReviewError, 'Unknown'):
            session.nominate('not-a-comparison', True)
        with self.assertRaisesRegex(ReviewError, 'boolean'):
            session.nominate(self.item(session, 'same')['id'], 'yes')

    def test_bad_saved_selection_file_is_not_overwritten(self):
        session = self.session()
        session.directory.mkdir()
        session.selection_file.write_text('{"version": 999}')
        with self.assertRaisesRegex(ReviewError, 'refusing'):
            session.clear()
        self.assertEqual(session.selection_file.read_text(), '{"version": 999}')

    def test_missing_markdown_still_exposes_manifest_images_for_debugging(self):
        (self.root / 'content/first.md').unlink()
        session = self.session()
        self.assertFalse(session.data['documents'][0]['exists'])
        self.assertEqual(len(session.data['documents'][0]['images']), 3)

    def test_standalone_capture_result_records_success_and_failure(self):
        from argparse import Namespace
        args = Namespace(manifest=str(self.root / 'first.json'), output_root=str(self.run / 'screenshots'),
                         ids=['first.same'], tags=None, run_dir=None, headed=False, browser='chromium',
                         debug=False, slow_mo=0, pause_before_step=False, pause_after_step=False, keep_open_on_failure=False)
        manifest_path = self.root / 'first.json'
        manifest = json.loads(manifest_path.read_text())
        for error in (None, RuntimeError('recipe failed')):
            with self.subTest(error=error), patch.object(cli, 'capture_screenshots', side_effect=error):
                if error:
                    with self.assertRaisesRegex(RuntimeError, 'recipe failed'):
                        cli._capture(args, self.root)
                else:
                    cli._capture(args, self.root)
            saved = json.loads((self.run / 'screenshots/capture-results.json').read_text())
            self.assertEqual(saved['manifests']['first.json']['status'], 'failed' if error else 'complete')
            self.assertEqual(saved['manifests']['first.json']['expected_images'], ['assets/images/same.png'])

    def test_guest_hook_failure_is_recorded_before_any_browser_capture(self):
        from argparse import Namespace
        args = Namespace(manifest=str(self.root / 'first.json'), output_root=str(self.run / 'screenshots'),
                         ids=None, tags=None, run_dir=None)
        with patch.object(cli.workflow, 'capture_with_hooks', side_effect=RuntimeError('Guest setup hook failed')), \
             patch.object(cli, 'capture_screenshots') as browser:
            with self.assertRaisesRegex(RuntimeError, 'Guest setup'):
                cli._capture(args, self.root)
        browser.assert_not_called()
        record = json.loads((self.run / 'screenshots/capture-results.json').read_text())['manifests']['first.json']
        self.assertEqual(record['status'], 'failed')
        self.assertIn('Guest setup hook failed', record['error'])


if __name__ == '__main__':
    unittest.main()
