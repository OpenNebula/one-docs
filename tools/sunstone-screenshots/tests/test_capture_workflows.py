import json
import importlib.util
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import capture, cli, workflow


GROUP = Path(__file__).resolve().parents[1] / 'groups/single-node'


class CaptureWorkflowTests(unittest.TestCase):
    def test_console_only_debug_can_skip_manifest_hooks_but_retains_credentials_and_filters(self):
        root = Path(__file__).resolve().parents[3]
        manifest = root / 'tools/sunstone-screenshots/groups/getting-started/deploy_opennebula_onprem_with_minione.json'
        for skip_hooks in (False, True):
            for failed in (False, True):
                with self.subTest(skip_hooks=skip_hooks, failed=failed), TemporaryDirectory() as tmp:
                    run = Path(tmp)
                    (run / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
                    args = ['--repo-root', str(root), 'capture', str(manifest), '--run-dir', str(run),
                            '--id', 'minione.console', '--debug', '--keep-open-on-failure']
                    if skip_hooks:
                        args.append('--skip-hooks')
                    output = StringIO()
                    with patch.object(cli.lab, 'capture_environment', return_value={'SUNSTONE_URL': 'http://debug.test'}) as environment, \
                         patch.object(workflow.lab, 'ssh', return_value=Mock(returncode=0)) as ssh, \
                         patch.object(cli, 'capture_screenshots', side_effect=capture.CaptureError('test failure') if failed else None) as browser, \
                         patch.dict(os.environ, {'SUNSTONE_URL': 'http://original.test'}), \
                         redirect_stdout(output), redirect_stderr(StringIO()):
                        self.assertEqual(cli.main(args), 1 if failed else 0)
                        self.assertEqual(os.environ['SUNSTONE_URL'], 'http://original.test')
                    environment.assert_called_once_with(str(run))
                    browser.assert_called_once()
                    self.assertEqual(browser.call_args.kwargs['selected_ids'], {'minione.console'})
                    self.assertTrue(browser.call_args.kwargs['debug'])
                    self.assertTrue(browser.call_args.kwargs['keep_open_on_failure'])
                    self.assertEqual(ssh.call_count, 0 if skip_hooks else 4)
                    self.assertEqual('Skipping manifest guest setup/teardown hooks' in output.getvalue(), skip_hooks)
                    self.assertIsNone(workflow.guest_runner.get())

    def test_action_failure_is_reported_with_recipe_step_context(self):
        error = RuntimeError('Locator.hover: Timeout 30000ms exceeded')
        step = {'action': 'hover', 'selector': "[data-cy='sidebar']"}
        label = 'minione.json capture network-menu step 1'
        with patch.object(capture, '_run_step', side_effect=error):
            with self.assertRaisesRegex(capture.CaptureError, label + ': Locator.hover') as result:
                capture._run_debug_step(Mock(), step, {}, label, False, False, False)
        self.assertIs(result.exception.__cause__, error)

    def test_browser_logout_runs_after_screenshot_and_before_guest_cleanup(self):
        for failure in (False, True):
            with self.subTest(failure=failure), TemporaryDirectory() as tmp:
                root = Path(tmp)
                events = []
                browser = Mock()
                context = browser.new_context.return_value
                context.close.side_effect = lambda: events.append('context-close')
                playwright = Mock()
                playwright.chromium.launch.return_value = browser
                manager = Mock()
                manager.__enter__ = Mock(return_value=playwright)
                manager.__exit__ = Mock(return_value=False)
                api = SimpleNamespace(sync_playwright=lambda: manager)
                recipe = {'captures': [{'id': 'running', 'steps': []}],
                          'teardown': [{'action': 'logout'}]}
                manifest = {'screenshots': [{'id': 'test', 'recipe': 'recipe.json',
                             'capture': 'running', 'image': 'image.png'}],
                            'hooks': {'teardown': [{'command': 'cleanup'}]}}
                output = StringIO()

                def inspect():
                    self.assertIn('Recipe failed: screenshot failed', output.getvalue())
                    self.assertEqual(events, ['screenshot'])
                    events.append('inspect')

                def screenshot(*args):
                    events.append('screenshot')
                    if failure:
                        raise capture.CaptureError('screenshot failed')

                token = workflow.guest_runner.set(lambda command: events.append('guest-cleanup'))
                try:
                    with patch.dict(sys.modules, {'playwright.sync_api': api}), \
                         patch.object(capture, '_load_recipe', return_value=recipe), \
                         patch.object(capture, '_take_screenshot', side_effect=screenshot), \
                         patch.object(capture, '_run_debug_step', side_effect=lambda page, *a, **k: events.append('logout') or page), \
                         patch('builtins.input', side_effect=inspect), redirect_stdout(output):
                        def run():
                            workflow.capture_with_hooks(manifest, lambda: capture.capture_screenshots(
                                manifest, root / 'manifest.json', root, root / 'output', keep_open_on_failure=failure))
                        if failure:
                            with self.assertRaisesRegex(capture.CaptureError, 'screenshot failed'):
                                run()
                        else:
                            run()
                finally:
                    workflow.guest_runner.reset(token)
                self.assertEqual(events, ['screenshot'] + (['inspect'] if failure else [])
                                 + ['logout', 'context-close', 'guest-cleanup'])

    def test_wait_refreshes_until_vm_is_visibly_running(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = [Timeout(), None]
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 5, 5]):
            capture._wait_for_selector(page, {'selector': '.running', 'timeout': 10000,
                                             'refreshSelector': '.refresh'}, {})
        page.locator.assert_called_once_with('.refresh')
        self.assertEqual(page.wait_for_selector.call_count, 2)

    def test_wait_refresh_honors_deadline(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = Timeout()
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 10]):
            with self.assertRaisesRegex(capture.CaptureError, 'Timed out'):
                capture._wait_for_selector(page, {'selector': '.running', 'timeout': 10000,
                                                 'refreshSelector': '.refresh'}, {})
        page.locator.assert_not_called()

    def test_disabled_refresh_does_not_abort_wait_for_running_vm(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = [Timeout(), None]
        page.locator.return_value.first.click.side_effect = Timeout('Refresh is disabled')
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 5, 10]):
            capture._wait_for_selector(page, {'selector': '.running', 'timeout': 15000,
                                             'refreshSelector': '.refresh'}, {})
        self.assertEqual(page.wait_for_selector.call_count, 2)
        page.locator.return_value.first.click.assert_called_once_with(timeout=5000)

    def test_disabled_refresh_still_obeys_overall_deadline(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = Timeout()
        page.locator.return_value.first.click.side_effect = Timeout('Refresh is disabled')
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 5, 10]):
            with self.assertRaisesRegex(capture.CaptureError, 'Timed out waiting for selector: .running'):
                capture._wait_for_selector(page, {'selector': '.running', 'timeout': 10000,
                                                 'refreshSelector': '.refresh'}, {})
        self.assertEqual(page.wait_for_selector.call_count, 1)

    def test_refresh_click_timeout_is_bounded_by_remaining_time(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = [Timeout(), None]
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 8, 9]):
            capture._wait_for_selector(page, {'selector': '.running', 'timeout': 10000,
                                             'refreshSelector': '.refresh'}, {})
        page.locator.return_value.first.click.assert_called_once_with(timeout=2000)

    def test_refresh_does_not_swallow_unrelated_browser_errors(self):
        class Timeout(Exception):
            pass
        page = Mock()
        page.wait_for_selector.side_effect = Timeout()
        page.locator.return_value.first.click.side_effect = RuntimeError('Page closed')
        with patch.dict(sys.modules, {'playwright.sync_api': SimpleNamespace(TimeoutError=Timeout)}), \
             patch.object(capture.time, 'monotonic', side_effect=[0, 0, 5]):
            with self.assertRaisesRegex(RuntimeError, 'Page closed'):
                capture._wait_for_selector(page, {'selector': '.running', 'timeout': 10000,
                                                 'refreshSelector': '.refresh'}, {})


class AlpineCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.marker = Path(self.temp.name) / 'marker.json'
        self.marker.write_text(json.dumps({'name': 'docs-screenshot-alpine', 'template_id': '0',
                                          'workflow_id': 'current', 'previous_ids': ['3']}))

    def execute(self, script, results):
        code = (GROUP / 'scripts' / script).read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        original_path = Path
        def path(value):
            if str(value) == '/root/screenshot-lab/alpine-workflow.json':
                return self.marker
            return original_path(value)
        with patch('pathlib.Path', side_effect=path), \
             patch('subprocess.check_output', side_effect=results) as command, \
             patch.dict(os.environ, {'SUNSTONE_WORKFLOW_ID': 'current'}):
            exec(compile(code, script, 'exec'), {})
        return command

    def vm(self, vm_id='4', template='0', state='3', name='docs-screenshot-alpine'):
        return f'<VM><ID>{vm_id}</ID><NAME>{name}</NAME><STATE>{state}</STATE><TEMPLATE><TEMPLATE_ID>{template}</TEMPLATE_ID></TEMPLATE></VM>'

    def pool(self, *vms):
        # OpenNebula's abbreviated pool XML does not include TEMPLATE_ID.
        import xml.etree.ElementTree as ET
        root = ET.Element('VM_POOL')
        for xml in vms:
            vm = ET.fromstring(xml)
            template = vm.find('TEMPLATE')
            template.remove(template.find('TEMPLATE_ID'))
            root.append(vm)
        return ET.tostring(root, encoding='unicode')

    def test_cleanup_terminates_only_new_matching_vm_and_waits_done(self):
        pool = self.pool(self.vm('3'), self.vm(), self.vm('5', name='unrelated'))
        commands = self.execute('cleanup-alpine.sh', [pool, self.vm(), '', self.vm(state='6')])
        self.assertEqual([c.args[0][-1] for c in commands.call_args_list], [
            'onevm list -x', 'onevm show 4 -x', 'onevm terminate --hard 4', 'onevm show 4 -x'])
        self.assertFalse(self.marker.exists())

    def test_cleanup_refuses_changed_template(self):
        with self.assertRaisesRegex(SystemExit, 'template does not match .*expected 0, found 99'):
            self.execute('cleanup-alpine.sh', [self.pool(self.vm()), self.vm(template='99')])
        self.assertTrue(self.marker.exists())

    def test_cleanup_refuses_full_record_without_template(self):
        with self.assertRaisesRegex(SystemExit, 'found None'):
            self.execute('cleanup-alpine.sh', [self.pool(self.vm()),
                         '<VM><ID>4</ID><NAME>docs-screenshot-alpine</NAME></VM>'])
        self.assertTrue(self.marker.exists())

    def test_cleanup_refuses_vm_identity_change(self):
        with self.assertRaisesRegex(SystemExit, 'identity changed'):
            self.execute('cleanup-alpine.sh', [self.pool(self.vm()), self.vm(name='unrelated')])
        self.assertTrue(self.marker.exists())

    def test_cleanup_leaves_another_invocations_marker(self):
        data = json.loads(self.marker.read_text())
        data['workflow_id'] = 'other'
        self.marker.write_text(json.dumps(data))
        with self.assertRaises(SystemExit) as exited:
            self.execute('cleanup-alpine.sh', [])
        self.assertEqual(exited.exception.code, 0)
        self.assertTrue(self.marker.exists())

    def test_script_hook_resolves_relative_to_manifest(self):
        execute = Mock()
        token = workflow.guest_runner.set(execute)
        try:
            manifest = {'hooks': {'setup': [{'script': 'scripts/prepare-alpine.sh'}]}}
            workflow.capture_with_hooks(manifest, lambda: None, GROUP / 'automated.json')
        finally:
            workflow.guest_runner.reset(token)
        self.assertIn('onetemplate list -x', execute.call_args.args[0]['command'])
        self.assertNotIn('script', execute.call_args.args[0])

    def test_script_hook_requires_existing_file(self):
        with self.assertRaisesRegex(workflow.ManifestError, 'does not exist'):
            workflow.validate_commands([{'script': 'missing.sh'}], GROUP)


class AlpineRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location('recover_alpine', GROUP / 'scripts/recover-alpine.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.result = {'group': str(GROUP / 'group.json'),
                       'pages': [{'manifest': str(GROUP / 'automated.json'), 'status': 'failed'}]}
        (self.run / 'workflow.json').write_text(json.dumps(self.result))
        (self.run / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
        self.workflow_id = 'a' * 32
        self.marker = SimpleNamespace(returncode=0, stdout=json.dumps(
            {'name': 'docs-screenshot-alpine', 'workflow_id': self.workflow_id}))

    def recover(self, results):
        with patch.object(self.module.lab, 'connect'), \
             patch.object(self.module.lab, 'owned_vm', return_value=SimpleNamespace(STATE=3, LCM_STATE=3)), \
             patch.object(self.module.lab, 'ssh', side_effect=results) as ssh:
            self.module.recover(self.run)
        return ssh

    def test_recovery_archives_failure_only_after_verified_cleanup(self):
        ssh = self.recover([self.marker, SimpleNamespace(returncode=0), SimpleNamespace(returncode=0)])
        self.assertIn('export SUNSTONE_WORKFLOW_ID=' + self.workflow_id, ssh.call_args_list[1].args[2])
        self.assertFalse((self.run / 'workflow.json').exists())
        self.assertEqual(json.loads((self.run / f'workflow.failed-{self.workflow_id}.json').read_text()), self.result)

    def test_failed_cleanup_preserves_failed_run(self):
        with self.assertRaisesRegex(workflow.lab.ProvisionError, 'recovery failed'):
            self.recover([self.marker, SimpleNamespace(returncode=1)])
        self.assertTrue((self.run / 'workflow.json').exists())

    def test_marker_remaining_preserves_failed_run(self):
        with self.assertRaisesRegex(workflow.lab.ProvisionError, 'marker remains'):
            self.recover([self.marker, SimpleNamespace(returncode=0), SimpleNamespace(returncode=1)])
        self.assertTrue((self.run / 'workflow.json').exists())

    def test_recovery_refuses_other_failed_page(self):
        self.result['pages'][0]['manifest'] = str(GROUP / 'marketplace-apps.json')
        (self.run / 'workflow.json').write_text(json.dumps(self.result))
        with self.assertRaisesRegex(workflow.lab.ProvisionError, 'first, Alpine workflow'):
            self.recover([])
