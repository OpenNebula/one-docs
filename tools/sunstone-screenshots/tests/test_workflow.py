import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import workflow, cli
from sunstone_screenshots.capture import _run_step
from sunstone_screenshots.inventory import import_inventory


class WorkflowTests(unittest.TestCase):
    def test_group_and_suite_parsers_forward_the_keep_open_option(self):
        for command, handler in (('run-group', '_run_group'), ('run-suite', '_run_suite')):
            for keep_open in (False, True):
                with self.subTest(command=command, keep_open=keep_open):
                    args = [command, 'example.json', '--run-dir', 'unused', '--debug']
                    if keep_open:
                        args.append('--keep-open-on-failure')
                    with patch.object(cli, handler, return_value=0) as execute:
                        self.assertEqual(cli.main(args), 0)
                    parsed = execute.call_args.args[0]
                    self.assertEqual(parsed.keep_open_on_failure, keep_open)
                    self.assertTrue(parsed.debug)

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

    def test_teardown_failure_preserves_the_original_error(self):
        for stage in ('setup', 'capture'):
            with self.subTest(stage=stage):
                original = RuntimeError(stage + ' failed')
                execute = Mock(side_effect=[original, RuntimeError('cleanup failed'), None]
                               if stage == 'setup' else [RuntimeError('cleanup failed'), None])
                token = workflow.guest_runner.set(execute)
                capture = Mock(side_effect=original if stage == 'capture' else None)
                manifest = {'hooks': {'setup': [{'command': 'setup'}] if stage == 'setup' else [],
                                     'teardown': [{'command': 'first cleanup'}, {'command': 'second cleanup'}]}}
                try:
                    with self.assertRaisesRegex(workflow.lab.ProvisionError, stage + ' failed.*Teardown failed: cleanup failed') as result:
                        workflow.capture_with_hooks(manifest, capture)
                finally:
                    workflow.guest_runner.reset(token)
                self.assertIs(result.exception.__cause__, original)
                self.assertEqual(execute.call_count, 3 if stage == 'setup' else 2)
                if stage == 'setup':
                    capture.assert_not_called()

    def test_guest_action_keeps_page(self):
        execute = Mock()
        token = workflow.guest_runner.set(execute)
        self.addCleanup(workflow.guest_runner.reset, token)
        page = object()
        command = {'action': 'guestCommand', 'command': 'true'}
        self.assertIs(_run_step(page, command, {}), page)
        execute.assert_called_once_with(command)

    def test_guest_hook_failure_names_stage_index_and_script(self):
        for stage in ('setup', 'teardown'):
            with self.subTest(stage=stage):
                token = workflow.guest_runner.set(Mock(side_effect=workflow.lab.ProvisionError('Guest command failed')))
                manifest = {'hooks': {stage: [{'script': 'cleanup-wordpress.sh'}]}}
                try:
                    with patch.object(Path, 'read_text', return_value='true'):
                        with self.assertRaisesRegex(workflow.lab.ProvisionError,
                                f'Guest {stage} hook 1 \\(cleanup-wordpress.sh\\): Guest command failed'):
                            workflow.capture_with_hooks(manifest, Mock(), Path('manifest.json'))
                finally:
                    workflow.guest_runner.reset(token)

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
        with patch.object(cli.workflow, 'load_group', return_value=(Path('config'), [Path('manifest')], False)), \
             patch.object(cli.lab, 'provision') as provision:
            self.assertEqual(cli.main(['run-group', 'group', '--run-dir', 'unused', '--check']), 0)
        provision.assert_not_called()

    def test_group_stops_after_failure_and_retains_lab(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = type('Args', (), dict(group='group', run_dir=str(root), reuse=False))()
            args.check = False
            with patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('a'), Path('b')], False)), \
                 patch.object(cli.lab, 'provision') as provision, \
                 patch.object(cli, '_capture', side_effect=RuntimeError('failed')) as capture:
                with self.assertRaisesRegex(RuntimeError, 'failed'):
                    cli._run_group(args, root)
            provision.assert_called_once()
            capture.assert_called_once()
            self.assertEqual(json.loads((root / 'workflow.json').read_text())['pages'][0]['status'], 'failed')

    def test_example_group_validates(self):
        root = Path(__file__).resolve().parents[3]
        config, manifests, destroy_on_success = workflow.load_group(root / 'tools/sunstone-screenshots/groups/single-node/group.json', root)
        self.assertTrue(config.is_file())
        self.assertEqual(len(manifests), 2)
        self.assertTrue(destroy_on_success)

    def test_group_success_provisions_once_and_reports_each_page(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = type('Args', (), dict(group='group', run_dir=str(root), reuse=False, check=False))()
            with patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('a'), Path('b')], False)), \
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

    def test_second_group_has_independent_provision_and_destruction_policy(self):
        root = Path(__file__).resolve().parents[3]
        base = root / 'tools/sunstone-screenshots/groups'
        first_config, _, first_destroy = workflow.load_group(base / 'single-node/group.json', root)
        second_config, pages, destroy = workflow.load_group(base / 'service-and-hosts/group.json', root)
        self.assertNotEqual(first_config, second_config)
        self.assertTrue(first_destroy)
        self.assertTrue(destroy)
        self.assertEqual([p.name for p in pages], ['oneslurm.json', 'host-pci.json'])

    def test_destroy_policy_is_strict_boolean(self):
        root = Path(__file__).resolve().parents[3]
        for value in ('true', 1, None):
            with self.subTest(value=value), patch.object(workflow.json, 'loads', return_value={
                    'version': 1, 'destroyOnSuccess': value}):
                with self.assertRaisesRegex(workflow.ManifestError, 'must be a boolean'):
                    workflow.load_group(root / 'tools/sunstone-screenshots/groups/service-and-hosts/group.json', root)

    def test_automatic_destruction_happens_only_after_all_reports(self):
        for failure in (None, 'capture', 'report', 'destroy'):
            with self.subTest(failure=failure), TemporaryDirectory() as tmp:
                root = Path(tmp)
                args = type('Args', (), dict(group='group', run_dir=str(root), reuse=False, check=False))()
                events = []
                def capture(*args):
                    events.append('capture')
                    if failure == 'capture':
                        raise RuntimeError('capture failed')
                    return 0
                def report(*args):
                    events.append('report')
                    if failure == 'report':
                        raise RuntimeError('report failed')
                def destroy(*args):
                    events.append('destroy')
                    if failure == 'destroy':
                        raise RuntimeError('destroy failed')
                with patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('a'), Path('b')], True)), \
                     patch.object(cli.lab, 'provision', side_effect=lambda *a: events.append('provision')), \
                     patch.object(cli, '_capture', side_effect=capture), \
                     patch.object(cli, 'load_manifest', return_value={}), \
                     patch.object(cli, 'write_qa_report', side_effect=report), \
                     patch.object(cli.lab, 'destroy', side_effect=destroy):
                    if failure:
                        with self.assertRaisesRegex(RuntimeError, failure + ' failed'):
                            cli._run_group(args, root)
                    else:
                        self.assertEqual(cli._run_group(args, root), 0)
                summary = json.loads((root / 'workflow.json').read_text())
                if failure in ('capture', 'report'):
                    self.assertNotIn('destroy', events)
                    self.assertEqual(summary['lab_status'], 'retained')
                else:
                    self.assertEqual(events, ['provision', 'capture', 'report', 'capture', 'report', 'destroy'])
                    self.assertEqual(summary['lab_status'], 'destroy-failed' if failure else 'destroyed')

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

    def test_guest_session_refuses_concurrent_capture_before_guest_commands(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
            with workflow.guest_session(root), patch.object(workflow.lab, 'ssh') as ssh:
                with self.assertRaisesRegex(workflow.lab.ProvisionError, 'Finish any paused run'):
                    with workflow.guest_session(root):
                        self.fail('A second capture must not start')
                ssh.assert_not_called()
            with workflow.guest_session(root):
                pass
            self.assertIsNone(workflow.guest_runner.get())

    def test_lab_lock_is_released_after_an_exception(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'failure'):
                with workflow.lab.run_lock(tmp):
                    raise RuntimeError('failure')
            with workflow.lab.run_lock(tmp):
                pass

    def test_group_rejects_duplicate_manifests_before_provision(self):
        root = Path(__file__).resolve().parents[3]
        group = root / 'tools/sunstone-screenshots/groups/single-node/group.json'
        original = json.loads(group.read_text())
        original['manifests'] = [original['manifests'][0]] * 2
        with patch.object(workflow.json, 'loads', side_effect=[original, json.loads((group.parent / 'automated.json').read_text()),
                          json.loads((group.parent / 'recipes/login.json').read_text())]):
            with self.assertRaisesRegex(workflow.ManifestError, 'Duplicate manifest'):
                workflow.load_group(group, root)
