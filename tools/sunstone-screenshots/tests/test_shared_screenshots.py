import argparse
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots import cli, workflow
from sunstone_screenshots.manifest import validate_manifest
from sunstone_screenshots.qa_report import write_qa_report


class SharedScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('first.md', 'second.md', 'image.png', 'dark.png'):
            (self.root / name).touch()
        self.write('recipe.json', {'captures': [{'id': 'capture'}]})
        self.write('provision.json', {})
        self.first = {'version': 1, 'group': 'group.json', 'screenshots': [{
            'id': 'first', 'doc': 'first.md', 'image': 'image.png', 'darkImage': 'dark.png',
            'recipe': 'recipe.json', 'capture': 'capture'}]}
        self.second = copy.deepcopy(self.first)
        self.second['screenshots'][0].update(id='second', doc='second.md', sharedFrom={'manifest': 'first.json', 'id': 'first'})
        self.write('first.json', self.first)
        self.write('second.json', self.second)
        self.group = {'version': 1, 'provision': 'provision.json', 'manifests': ['first.json', 'second.json']}
        self.write('group.json', self.group)

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data))

    def args(self, **changes):
        values = dict(manifest=str(self.root / 'second.json'), output_root=str(self.root / 'output'),
                      ids=None, tags=None, run_dir='unused')
        values.update(changes)
        return argparse.Namespace(**values)

    def test_explicit_shared_images_validate_in_group(self):
        _, manifests, _ = workflow.load_group(self.root / 'group.json', self.root)
        self.assertEqual([p.name for p in manifests], ['first.json', 'second.json'])

    def test_accidental_duplicate_outputs_still_rejected(self):
        del self.second['screenshots'][0]['sharedFrom']
        self.write('second.json', self.second)
        with self.assertRaisesRegex(workflow.ManifestError, 'Duplicate output asset'):
            workflow.load_group(self.root / 'group.json', self.root)

    def test_source_must_run_before_consumer(self):
        self.group['manifests'].reverse()
        self.write('group.json', self.group)
        with self.assertRaisesRegex(workflow.ManifestError, 'earlier in the same group'):
            workflow.load_group(self.root / 'group.json', self.root)

    def test_shared_reference_rejects_inconsistent_or_missing_sources(self):
        for key, value in (
            ('image', 'dark.png'), ('darkImage', None), ('capture', 'other'),
            ('sharedFrom', {'manifest': 'first.json', 'id': 'unknown'}),
            ('sharedFrom', {'manifest': 'first.json'}),
            ('sharedFrom', {'manifest': 'missing.json', 'id': 'first'}),
        ):
            with self.subTest(key=key, value=value):
                manifest = copy.deepcopy(self.second)
                manifest['screenshots'][0][key] = value
                self.assertTrue(validate_manifest(manifest, self.root, self.root / 'second.json'))

    def test_shared_capture_settings_must_match(self):
        changed = dict(self.second, defaults={'viewport': {'width': 800, 'height': 600}})
        self.assertTrue(any('defaults differ' in e for e in validate_manifest(changed, self.root, self.root / 'second.json')))
        self.write('other-recipe.json', {'captures': [{'id': 'capture'}]})
        changed = copy.deepcopy(self.second)
        changed['screenshots'][0]['recipe'] = 'other-recipe.json'
        self.assertTrue(any('recipe differs' in e for e in validate_manifest(changed, self.root, self.root / 'second.json')))

    def test_shared_source_cannot_be_disabled_or_another_reference(self):
        for change in ({'status': 'disabled'}, {'sharedFrom': {'manifest': 'second.json', 'id': 'second'}}):
            first = copy.deepcopy(self.first)
            first['screenshots'][0].update(change)
            self.write('first.json', first)
            self.assertTrue(any('directly captured' in e for e in validate_manifest(self.second, self.root, self.root / 'second.json')))

    def test_shared_only_page_needs_no_browser_guest_hooks_or_credentials(self):
        output = self.root / 'output'
        output.mkdir()
        for name in ('image.png', 'dark.png'):
            (output / name).touch()
        with patch.object(cli, '_run_capture') as capture, patch.object(cli.lab, 'capture_environment') as environment, \
             patch.object(workflow, 'capture_with_hooks') as hooks:
            self.assertEqual(cli._capture(self.args(), self.root), 0)
        capture.assert_not_called()
        environment.assert_not_called()
        hooks.assert_not_called()

    def test_missing_shared_replacement_fails_instead_of_recapturing(self):
        with patch.object(cli, '_run_capture') as capture:
            with self.assertRaisesRegex(cli.CaptureError, 'Run its producer manifest first'):
                cli._capture(self.args(), self.root)
        capture.assert_not_called()

    def test_shared_capture_checks_only_selected_images(self):
        with patch.object(cli, '_run_capture', side_effect=cli.CaptureError('No screenshots matched')) as capture:
            with self.assertRaisesRegex(cli.CaptureError, 'No screenshots matched'):
                cli._capture(self.args(ids=['not-selected'], run_dir=None), self.root)
        capture.assert_called_once()

    def test_deferred_images_are_validated_and_visible_in_qa(self):
        self.first['deferredScreenshots'] = [{'image': 'dark.png', 'reason': 'Needs a GPU <not available>'}]
        self.assertEqual(validate_manifest(self.first, self.root, self.root / 'first.json'), [])
        report = self.root / 'qa.html'
        write_qa_report(self.first, self.root, self.root / 'output', report)
        html = report.read_text()
        self.assertIn('1 deferred', html)
        self.assertIn('Deferred Screenshots', html)
        self.assertIn('Needs a GPU &lt;not available&gt;', html)
        for value in (None, ['bad'], [{'image': 'missing.png', 'reason': 'Missing'}], [{'image': 'image.png', 'reason': ''}]):
            with self.subTest(value=value):
                self.first['deferredScreenshots'] = value
                self.assertTrue(validate_manifest(self.first, self.root, self.root / 'first.json'))
