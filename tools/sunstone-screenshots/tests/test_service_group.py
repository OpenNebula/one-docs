import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots.capture import _run_step


GROUP = Path(__file__).resolve().parents[1] / 'groups/service-and-hosts'


class OneSlurmFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.marker = Path(self.temp.name) / 'oneslurm.json'

    def marker_data(self, **changes):
        data = {'name': 'docs-screenshot-oneslurm', 'workflow_id': 'current', 'previous_ids': ['1']}
        data.update(changes)
        self.marker.write_text(json.dumps(data))

    def pool(self, templates):
        return json.dumps({'DOCUMENT_POOL': {'DOCUMENT': templates}})

    def template(self, template_id=2, name='docs-screenshot-oneslurm'):
        return {'ID': template_id, 'NAME': name, 'TEMPLATE': {'BODY': {'roles': []}}}

    def execute(self, filename, results):
        code = (GROUP / 'scripts' / filename).read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        original_path = Path
        def path(value):
            return self.marker if str(value) == '/root/screenshot-lab/oneslurm-workflow.json' else original_path(value)
        with patch('pathlib.Path', side_effect=path), \
             patch('subprocess.check_output', side_effect=results) as commands, \
             patch('time.sleep'), \
             patch.dict(os.environ, {'SUNSTONE_WORKFLOW_ID': 'current'}):
            exec(compile(code, filename, 'exec'), {})
        return commands

    def test_prepare_records_existing_ids_and_handles_empty_pool(self):
        self.execute('prepare-oneslurm.sh', [self.pool(None)])
        self.assertEqual(json.loads(self.marker.read_text()), {
            'name': 'docs-screenshot-oneslurm', 'workflow_id': 'current', 'previous_ids': []})

    def test_prepare_refuses_existing_named_service(self):
        with self.assertRaisesRegex(SystemExit, 'already exists'):
            self.execute('prepare-oneslurm.sh', [self.pool(self.template())])
        self.assertFalse(self.marker.exists())

    def test_cleanup_deletes_only_new_service_and_waits_for_removal(self):
        self.marker_data()
        existing = self.template(1)
        imported = self.template()
        unrelated = self.template(3, 'unrelated')
        commands = self.execute('cleanup-oneslurm.sh', [
            self.pool([existing, imported, unrelated]), json.dumps({'DOCUMENT': imported}), '',
            self.pool([existing, unrelated])])
        self.assertEqual([c.args[0][-1] for c in commands.call_args_list], [
            'oneflow-template list -j', 'oneflow-template show 2 -j',
            'oneflow-template delete 2', 'oneflow-template list -j'])
        self.assertFalse(self.marker.exists())

    def test_cleanup_refuses_identity_mismatch(self):
        self.marker_data()
        with self.assertRaisesRegex(SystemExit, 'identity changed'):
            self.execute('cleanup-oneslurm.sh', [self.pool([self.template()]),
                         json.dumps({'DOCUMENT': self.template(name='unrelated')})])
        self.assertTrue(self.marker.exists())

    def test_cleanup_refuses_ambiguous_imports(self):
        self.marker_data()
        with self.assertRaisesRegex(SystemExit, 'ambiguous cleanup'):
            self.execute('cleanup-oneslurm.sh', [self.pool([self.template(), self.template(3)])])
        self.assertTrue(self.marker.exists())

    def test_cleanup_preserves_foreign_invocation(self):
        self.marker_data(workflow_id='other')
        with self.assertRaises(SystemExit) as result:
            self.execute('cleanup-oneslurm.sh', [])
        self.assertEqual(result.exception.code, 0)
        self.assertTrue(self.marker.exists())

    def test_wait_for_import_modal_to_close(self):
        from unittest.mock import Mock
        page = Mock()
        self.assertIs(_run_step(page, {'action': 'waitForSelector', 'selector': '.import',
                                      'state': 'hidden', 'timeout': 900000}, {}), page)
        page.wait_for_selector.assert_called_once_with('.import', timeout=900000, state='hidden')
