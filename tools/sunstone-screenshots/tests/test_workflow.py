import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import workflow, cli
from sunstone_screenshots.capture import _run_step
from sunstone_screenshots.inventory import import_inventory


class WorkflowTests(unittest.TestCase):
    def test_teardown_after_partial_setup_failure(self):
        execute = Mock(side_effect=[RuntimeError('setup'), None, None])
        token = workflow.guest_runner.set(execute)
        self.addCleanup(workflow.guest_runner.reset, token)
        capture = Mock()
        manifest = {'hooks': {'setup': [{'command': 'setup'}],
                              'teardown': [{'command': 'clean1'}, {'command': 'clean2'}]}}
        with self.assertRaisesRegex(RuntimeError, 'setup'):
            workflow.capture_with_hooks(manifest, capture)
        capture.assert_not_called()
        self.assertEqual(execute.call_count, 3)

    def test_all_teardowns_attempted_on_capture_failure(self):
        execute = Mock(side_effect=[RuntimeError('cleanup'), None])
        token = workflow.guest_runner.set(execute)
        self.addCleanup(workflow.guest_runner.reset, token)
        with self.assertRaisesRegex(workflow.lab.ProvisionError, 'Teardown failed'):
            workflow.capture_with_hooks({'hooks': {'teardown': [{'command': 'a'}, {'command': 'b'}]}},
                                        Mock(side_effect=RuntimeError('capture')))
        self.assertEqual(execute.call_count, 2)

    def test_guest_action_keeps_page(self):
        execute = Mock()
        token = workflow.guest_runner.set(execute)
        self.addCleanup(workflow.guest_runner.reset, token)
        page = object()
        command = {'action': 'guestCommand', 'command': 'true'}
        self.assertIs(_run_step(page, command, {}), page)
        execute.assert_called_once_with(command)

    def test_guest_action_requires_lab(self):
        with self.assertRaises(workflow.lab.ProvisionError):
            workflow.run_guest({'command': 'true'})

    def test_import_preserves_unresolved_and_external_rows(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.csv'
            source.write_text('Title,Page,Priority,Assigned,Status,Comments,Any Sunstone Errors?\n'
                              'Section,,,,,,\nUnknown,,1,A,Merged,note,bug\n'
                              'External,https://github.com/example,2,B,Merged,,\n')
            rows = import_inventory(source, root / 'inventory.csv', root)
            self.assertEqual([r['automation_status'] for r in rows], ['needs-path', 'external'])
            self.assertEqual(rows[0]['manual_status'], 'Merged')
            self.assertEqual(rows[0]['comments'], 'note')
            with self.assertRaises(FileExistsError):
                import_inventory(source, root / 'inventory.csv', root)

    def test_group_check_is_offline(self):
        with patch.object(cli.workflow, 'load_group', return_value=(Path('config'), [Path('manifest')])), \
             patch.object(cli.lab, 'provision') as provision:
            self.assertEqual(cli.main(['run-group', 'group', '--run-dir', 'unused', '--check']), 0)
        provision.assert_not_called()

    def test_group_stops_after_failure_and_retains_lab(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = type('Args', (), dict(group='group', run_dir=str(root), reuse=False))()
            args.check = False
            with patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('a'), Path('b')])), \
                 patch.object(cli.lab, 'provision') as provision, \
                 patch.object(cli, '_capture', side_effect=RuntimeError('failed')) as capture:
                with self.assertRaisesRegex(RuntimeError, 'failed'):
                    cli._run_group(args, root)
            provision.assert_called_once()
            capture.assert_called_once()
            self.assertEqual(json.loads((root / 'workflow.json').read_text())['pages'][0]['status'], 'failed')

    def test_example_group_validates(self):
        root = Path(__file__).resolve().parents[3]
        config, manifests = workflow.load_group(root / 'tools/sunstone-screenshots/groups/single-node/group.json', root)
        self.assertTrue(config.is_file())
        self.assertEqual(len(manifests), 1)

    def test_group_success_provisions_once_and_reports_each_page(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = type('Args', (), dict(group='group', run_dir=str(root), reuse=False, check=False))()
            with patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('a'), Path('b')])), \
                 patch.object(cli.lab, 'provision') as provision, \
                 patch.object(cli, '_capture', return_value=0) as capture, \
                 patch.object(cli, 'load_manifest', return_value={}), \
                 patch.object(cli, 'write_qa_report') as report:
                self.assertEqual(cli._run_group(args, root), 0)
            provision.assert_called_once()
            self.assertEqual(capture.call_count, 2)
            self.assertEqual(report.call_count, 2)
            self.assertEqual([p['status'] for p in json.loads((root / 'workflow.json').read_text())['pages']],
                             ['complete', 'complete'])

    def test_guest_session_uses_ssh_and_restores_context(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
            with patch.object(workflow.lab, 'ssh', return_value=Mock(returncode=0)) as ssh:
                with workflow.guest_session(root):
                    workflow.run_guest({'command': 'echo test', 'timeout': 13})
            self.assertEqual(ssh.call_args.kwargs['timeout'], 13)
            self.assertIn('echo test', ssh.call_args.args[2])
            self.assertIsNone(workflow.guest_runner.get())
            self.assertEqual((root / 'guest-commands.log').stat().st_mode & 0o777, 0o600)

    def test_group_rejects_duplicate_manifests_before_provision(self):
        root = Path(__file__).resolve().parents[3]
        group = root / 'tools/sunstone-screenshots/groups/single-node/group.json'
        original = json.loads(group.read_text())
        original['manifests'] *= 2
        with patch.object(workflow.json, 'loads', side_effect=[original, json.loads((group.parent / 'automated.json').read_text()),
                          json.loads((group.parent / 'recipes/login.json').read_text())]):
            with self.assertRaisesRegex(workflow.ManifestError, 'Duplicate manifest'):
                workflow.load_group(group, root)
