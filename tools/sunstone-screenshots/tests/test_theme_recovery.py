import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


GROUP = Path(__file__).resolve().parents[1] / 'groups/getting-started'


class ThemeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        spec = importlib.util.spec_from_file_location('recover_theme', GROUP / 'scripts/recover-theme.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.result = {'group': str(GROUP / 'group.json'), 'lab_status': 'retained',
                       'pages': [{'manifest': str(GROUP / 'deploy_opennebula_onprem_with_minione.json'), 'status': 'failed'}]}
        self.state = {'phase': 'ready', 'config': {}, 'address': '172.20.0.16'}
        self.write('workflow.json', self.result)
        self.write('state.json', self.state)
        (self.run / 'guest-commands.log').write_text('argument 1 must be one of file\noneuser update 0 /dev/stdin\n')
        self.workflow_id = 'a' * 32
        self.original = '<TEMPLATE><FIREEDGE><SCHEME>light</SCHEME><LANG>en_US</LANG></FIREEDGE></TEMPLATE>'
        self.marker = {'workflow_id': self.workflow_id, 'template': self.original}
        self.alpine = {'workflow_id': self.workflow_id, 'name': 'docs-screenshot-alpine',
                       'template_id': '0', 'previous_ids': ['1']}
        self.wordpress = {'workflow_id': self.workflow_id,
                          'names': {'vms': 'docs-screenshot-wordpress', 'templates': 'Service WordPress - KVM',
                                    'images': 'Service WordPress - KVM'},
                          'previous_ids': {'vms': ['1'], 'templates': ['1'], 'images': ['1']}}
        self.archive = self.run / f'workflow.failed-theme-{self.workflow_id}.json'

    def write(self, path, data):
        (self.run / path).write_text(json.dumps(data))

    def response(self, stdout='', returncode=0):
        return SimpleNamespace(stdout=stdout, returncode=returncode)

    def user(self, template=None):
        return self.response('<USER><ID>0</ID>' + (template or self.original) + '</USER>')

    def recover(self, responses=None, address='172.20.0.16', include_alpine=False, include_wordpress=False,
                workflow_record=None):
        if responses is None:
            responses = [self.response(json.dumps(self.marker))]
            if include_alpine or include_wordpress:
                responses.append(self.response(json.dumps(self.alpine)))
            if include_wordpress:
                responses.append(self.response(json.dumps(self.wordpress)))
            responses.append(self.user())
            if include_wordpress:
                responses.append(self.response())
            if include_alpine or include_wordpress:
                responses.append(self.response())
            responses.extend([self.response(), self.user()])
        with patch.object(self.module.lab, 'connect') as connect, \
             patch.object(self.module.lab, 'running_address', return_value=address), \
             patch.object(self.module.lab, 'ssh', side_effect=responses) as ssh:
            self.ssh = ssh
            self.connect = connect
            self.module.recover(self.run, include_alpine=include_alpine, include_wordpress=include_wordpress,
                                workflow_record=workflow_record)
        return ssh

    def validation_run(self):
        names = ('deploy_opennebula_onprem_with_minione.json', 'deploy_opennebula_on_aws.json',
                 'deploy_opennebula_onprem_with_poc_iso.json', 'validate_the_environment.json')
        self.result['pages'] = [{'manifest': str(GROUP / name), 'status': 'failed' if i == 3 else 'complete'}
                                for i, name in enumerate(names)]
        self.write('workflow.json', self.result)
        self.archive = self.run / f'workflow.failed-wordpress-{self.workflow_id}.json'

    def test_recovery_restores_and_verifies_before_archiving_without_reinstall(self):
        calls = self.recover()
        self.assertFalse((self.run / 'workflow.json').exists())
        self.assertEqual(json.loads(self.archive.read_text()), self.result)
        self.assertEqual(json.loads((self.run / 'state.json').read_text()), self.state)
        self.assertEqual(calls.call_count, 4)
        self.assertIn('alpine-workflow.json', calls.call_args_list[0].args[2])
        cleanup = calls.call_args_list[2]
        self.assertIn('export SUNSTONE_WORKFLOW_ID=' + self.workflow_id, cleanup.args[2])
        self.assertIn("'oneuser update 0'", cleanup.args[2])
        self.assertNotIn('/dev/stdin', cleanup.args[2])
        self.assertIn('test ! -e /root/screenshot-lab/theme-workflow.json', calls.call_args_list[3].args[2])

    def test_recovery_accepts_only_the_known_theme_change(self):
        current = self.original.replace('<SCHEME>light</SCHEME>', '<SCHEME>system</SCHEME>')
        self.recover([self.response(json.dumps(self.marker)), self.user(current), self.response(), self.user()])
        self.assertTrue(self.archive.exists())

    def test_recovery_refuses_later_or_different_failed_pages(self):
        for pages in ([self.result['pages'][0]] * 2,
                      [dict(self.result['pages'][0], manifest=str(GROUP / 'validate_the_environment.json'))],
                      [dict(self.result['pages'][0], status='complete')]):
            with self.subTest(pages=pages):
                self.write('workflow.json', dict(self.result, pages=pages))
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'first page'):
                    self.recover([])
                self.connect.assert_not_called()

    def test_recovery_refuses_existing_captures(self):
        output = self.run / 'screenshots/assets/images'
        output.mkdir(parents=True)
        (output / 'login.png').touch()
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'Screenshots already exist'):
            self.recover([])
        self.connect.assert_not_called()

    def test_recovery_refuses_unknown_failure_or_unready_lab(self):
        (self.run / 'guest-commands.log').write_text('Some unrelated failure')
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'does not identify'):
            self.recover([])
        self.connect.assert_not_called()
        (self.run / 'guest-commands.log').write_text('argument 1 must be one of file\noneuser update 0 /dev/stdin\n')
        self.write('state.json', dict(self.state, phase='failed'))
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'ready lab'):
            self.recover([])
        self.connect.assert_not_called()

    def test_recovery_refuses_stopped_or_moved_vm_before_ssh(self):
        for address in (None, '172.20.0.99'):
            with self.subTest(address=address):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'saved address'):
                    self.recover([], address=address)
                self.ssh.assert_not_called()

    def test_recovery_refuses_resource_markers_or_unreadable_guest(self):
        for result in (None, self.response(returncode=1)):
            with self.subTest(result=result):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'theme-only guest state'):
                    self.recover([result])
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_recovery_refuses_other_user_changes(self):
        current = self.original.replace('en_US', 'es_ES')
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'changed outside the theme hook'):
            self.recover([self.response(json.dumps(self.marker)), self.user(current)])
        self.assertEqual(self.ssh.call_count, 2)
        self.assertTrue((self.run / 'workflow.json').exists())
        self.assertFalse(self.archive.exists())

    def test_recovery_keeps_failed_record_when_restore_or_verification_fails(self):
        for restore, verify in ((self.response(returncode=1), None), (self.response(), self.response(returncode=1)),
                                (self.response(), self.user('<TEMPLATE><OTHER>changed</OTHER></TEMPLATE>'))):
            with self.subTest(restore=restore, verify=verify):
                with self.assertRaises(self.module.lab.ProvisionError):
                    self.recover([self.response(json.dumps(self.marker)), self.user(), restore, verify])
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_recovery_refuses_invalid_marker_or_existing_archive(self):
        for workflow_id in ('invalid', 1):
            marker = dict(self.marker, workflow_id=workflow_id)
            with self.subTest(workflow_id=workflow_id):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'Unexpected theme workflow ID'):
                    self.recover([self.response(json.dumps(marker))])
        self.archive.write_text('existing archive')
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'archive already exists'):
            self.recover([self.response(json.dumps(self.marker))])
        self.assertEqual(self.archive.read_text(), 'existing archive')
        self.assertTrue((self.run / 'workflow.json').exists())

    def test_interrupted_capture_cleanup_preserves_images_and_uses_matching_invocation(self):
        (self.run / 'guest-commands.log').write_text('sudo: a password is required\nPrevious theme marker exists\n')
        output = self.run / 'screenshots/login.png'
        output.parent.mkdir()
        output.write_bytes(b'existing replacement')
        calls = self.recover(include_alpine=True)
        self.assertEqual(output.read_bytes(), b'existing replacement')
        self.assertEqual(json.loads(self.archive.read_text()), self.result)
        self.assertEqual(json.loads((self.run / 'state.json').read_text()), self.state)
        self.assertEqual(calls.call_count, 6)
        alpine_cleanup, theme_restore = calls.call_args_list[3:5]
        self.assertIn('export SUNSTONE_WORKFLOW_ID=' + self.workflow_id, alpine_cleanup.args[2])
        self.assertIn('onevm show ', alpine_cleanup.args[2])
        self.assertIn('onevm terminate --hard ', alpine_cleanup.args[2])
        self.assertIn("'oneuser update 0'", theme_restore.args[2])
        self.assertIn('test ! -e ' + self.module.ALPINE_MARKER, calls.call_args_list[-1].args[2])
        self.assertIn(self.module.WORDPRESS_GUARD, calls.call_args_list[0].args[2])

    def test_interrupted_capture_can_retry_when_alpine_was_already_cleaned(self):
        calls = self.recover([self.response(json.dumps(self.marker)), self.response('null'),
                              self.user(), self.response(), self.user()], include_alpine=True)
        self.assertEqual(calls.call_count, 5)
        self.assertFalse(any('onevm terminate' in call.args[2] for call in calls.call_args_list))
        self.assertTrue(self.archive.exists())

    def test_interrupted_capture_refuses_foreign_or_invalid_alpine_markers(self):
        for marker in (dict(self.alpine, workflow_id='b' * 32), dict(self.alpine, name='other'),
                       dict(self.alpine, template_id='invalid'), dict(self.alpine, previous_ids='1'),
                       dict(self.alpine, previous_ids=[None]), [], 'not a marker'):
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'same workflow'):
                    self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(marker))],
                                 include_alpine=True)
                self.assertEqual(self.ssh.call_count, 2)
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_interrupted_capture_verifies_user_settings_before_terminating_alpine(self):
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'changed outside the theme hook'):
            self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                          self.user(self.original.replace('en_US', 'es_ES'))], include_alpine=True)
        self.assertEqual(self.ssh.call_count, 3)
        self.assertTrue((self.run / 'workflow.json').exists())

    def test_interrupted_capture_retains_failed_record_on_alpine_cleanup_failure(self):
        for result in (None, self.response(returncode=1)):
            with self.subTest(result=result):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'Alpine recovery failed'):
                    self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                                  self.user(), result], include_alpine=True)
                self.assertEqual(self.ssh.call_count, 4)
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_interrupted_capture_refuses_other_page_or_moved_lab(self):
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'saved address'):
            self.recover([], address='172.20.0.99', include_alpine=True)
        self.ssh.assert_not_called()
        self.write('workflow.json', dict(self.result, pages=[dict(self.result['pages'][0],
                   manifest=str(GROUP / 'validate_the_environment.json'))]))
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'first page'):
            self.recover([], include_alpine=True)
        self.connect.assert_not_called()

    def test_wordpress_recovery_runs_matching_cleanups_in_dependency_order(self):
        self.validation_run()
        image = self.run / 'screenshots/existing.png'
        image.parent.mkdir()
        image.write_bytes(b'keep')
        calls = self.recover(include_wordpress=True)
        self.assertEqual(calls.call_count, 8)
        wordpress, alpine, theme = calls.call_args_list[4:7]
        for call in (wordpress, alpine, theme):
            self.assertIn('export SUNSTONE_WORKFLOW_ID=' + self.workflow_id, call.args[2])
        self.assertIn('WordPress VM template does not match', wordpress.args[2])
        self.assertEqual(wordpress.kwargs['timeout'], 360)
        self.assertIn('Workflow VM identity changed', alpine.args[2])
        self.assertEqual(alpine.kwargs['timeout'], 240)
        self.assertIn("'oneuser update 0'", theme.args[2])
        self.assertEqual(theme.kwargs['timeout'], 30)
        self.assertIn(self.module.RESOURCE_GUARDS, calls.call_args_list[-1].args[2])
        self.assertEqual(image.read_bytes(), b'keep')
        self.assertEqual(json.loads(self.archive.read_text()), self.result)
        self.assertEqual(json.loads((self.run / 'state.json').read_text()), self.state)

    def test_wordpress_recovery_refuses_unrelated_page_histories(self):
        self.validation_run()
        histories = [self.result['pages'][:-1],
                     [dict(page, status='failed') for page in self.result['pages']],
                     list(reversed(self.result['pages']))]
        for pages in histories:
            with self.subTest(pages=pages):
                self.write('workflow.json', dict(self.result, pages=pages))
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'validation page'):
                    self.recover([], include_wordpress=True)
                self.connect.assert_not_called()

    def test_wordpress_recovery_validates_all_markers_before_any_cleanup(self):
        self.validation_run()
        for marker in (dict(self.wordpress, workflow_id='b' * 32),
                       dict(self.wordpress, names={'vms': 'foreign'}),
                       dict(self.wordpress, previous_ids={}),
                       dict(self.wordpress, previous_ids={'vms': ['invalid'], 'templates': [], 'images': []}), []):
            with self.subTest(marker=marker):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'WordPress marker.*same workflow'):
                    self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                                  self.response(json.dumps(marker))], include_wordpress=True)
                self.assertEqual(self.ssh.call_count, 3)
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_wordpress_recovery_refuses_other_user_changes_before_deletion(self):
        self.validation_run()
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'changed outside the theme hook'):
            self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                          self.response(json.dumps(self.wordpress)), self.user(self.original.replace('en_US', 'es_ES'))],
                         include_wordpress=True)
        self.assertEqual(self.ssh.call_count, 4)

    def test_wordpress_recovery_keeps_failed_record_if_cleanup_fails(self):
        self.validation_run()
        for result in (None, self.response(returncode=1)):
            with self.subTest(result=result):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'WordPress recovery failed'):
                    self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                                  self.response(json.dumps(self.wordpress)), self.user(), result], include_wordpress=True)
                self.assertEqual(self.ssh.call_count, 5)
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_wordpress_recovery_can_retry_after_wordpress_was_already_cleaned(self):
        self.validation_run()
        calls = self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                              self.response('null'), self.user(), self.response(), self.response(), self.user()],
                             include_wordpress=True)
        self.assertEqual(calls.call_count, 7)
        self.assertTrue(self.archive.exists())

    def test_wordpress_only_recovery_preserves_settings_after_theme_teardown(self):
        self.validation_run()
        current = '<TEMPLATE><FIREEDGE><SCHEME>dark</SCHEME><LANG>es_ES</LANG></FIREEDGE></TEMPLATE>'
        calls = self.recover([self.response('null'), self.response('null'),
                              self.response(json.dumps(self.wordpress)), self.user(current),
                              self.response(), self.user(current)], include_wordpress=True)
        self.assertEqual(calls.call_count, 6)
        self.assertIn('export SUNSTONE_WORKFLOW_ID=' + self.workflow_id, calls.call_args_list[4].args[2])
        self.assertIn('oneimage delete ', calls.call_args_list[4].args[2])
        self.assertFalse(any('oneuser update' in c.args[2] for c in calls.call_args_list))
        self.assertEqual(json.loads(self.archive.read_text()), self.result)

    def test_wordpress_only_recovery_rejects_foreign_alpine_marker_before_cleanup(self):
        self.validation_run()
        alpine = dict(self.alpine, workflow_id='b' * 32)
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'Alpine marker.*same workflow'):
            self.recover([self.response('null'), self.response(json.dumps(alpine)),
                          self.response(json.dumps(self.wordpress))], include_wordpress=True)
        self.assertEqual(self.ssh.call_count, 3)
        self.assertTrue((self.run / 'workflow.json').exists())
        self.assertFalse(self.archive.exists())

    def test_wordpress_only_recovery_requires_a_valid_remaining_ownership_marker(self):
        self.validation_run()
        for marker in (None, [], dict(self.wordpress, workflow_id='invalid'),
                       dict(self.wordpress, workflow_id=42), dict(self.wordpress, previous_ids={})):
            with self.subTest(marker=marker):
                with self.assertRaises(self.module.lab.ProvisionError):
                    self.recover([self.response('null'), self.response('null'),
                                  self.response(json.dumps(marker))], include_wordpress=True)
                self.assertEqual(self.ssh.call_count, 3)
                self.assertTrue((self.run / 'workflow.json').exists())
                self.assertFalse(self.archive.exists())

    def test_wordpress_only_recovery_verifies_settings_are_unchanged(self):
        self.validation_run()
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'User settings differ after recovery'):
            self.recover([self.response('null'), self.response('null'),
                          self.response(json.dumps(self.wordpress)), self.user(), self.response(),
                          self.user(self.original.replace('en_US', 'es_ES'))], include_wordpress=True)
        self.assertTrue((self.run / 'workflow.json').exists())
        self.assertFalse(self.archive.exists())

    def test_wordpress_only_recovery_can_use_an_archive_after_a_standalone_capture(self):
        self.validation_run()
        source = self.run / ('workflow.failed-wordpress-' + 'b' * 32 + '.json')
        original = json.dumps(self.result)
        source.write_text(original)
        (self.run / 'workflow.json').unlink()
        calls = self.recover([self.response('null'), self.response('null'),
                              self.response(json.dumps(self.wordpress)), self.user(), self.response(), self.user()],
                             include_wordpress=True, workflow_record=source)
        self.assertEqual(calls.call_count, 6)
        self.assertEqual(source.read_text(), original)
        self.assertEqual(json.loads(self.archive.read_text()), self.result)

    def test_later_standalone_capture_can_recover_from_preserved_archived_record(self):
        self.validation_run()
        source = self.run / ('workflow.failed-wordpress-' + 'b' * 32 + '.json')
        original = json.dumps(self.result)
        source.write_text(original)
        (self.run / 'workflow.json').unlink()
        calls = self.recover(include_wordpress=True, workflow_record=source)
        self.assertEqual(calls.call_count, 8)
        self.assertEqual(source.read_text(), original)
        self.assertEqual(json.loads(self.archive.read_text()), self.result)
        self.assertFalse((self.run / 'workflow.json').exists())

    def test_archived_record_is_preserved_when_later_cleanup_fails(self):
        self.validation_run()
        source = self.run / ('workflow.failed-wordpress-' + 'b' * 32 + '.json')
        original = json.dumps(self.result)
        source.write_text(original)
        (self.run / 'workflow.json').unlink()
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'WordPress recovery failed'):
            self.recover([self.response(json.dumps(self.marker)), self.response(json.dumps(self.alpine)),
                          self.response(json.dumps(self.wordpress)), self.user(), self.response(returncode=1)],
                         include_wordpress=True, workflow_record=source)
        self.assertEqual(source.read_text(), original)
        self.assertFalse(self.archive.exists())
        self.assertFalse((self.run / 'workflow.json').exists())
        with self.module.lab.run_lock(self.run):
            pass

    def test_archived_record_cannot_override_an_active_group_record(self):
        self.validation_run()
        source = self.run / ('workflow.failed-wordpress-' + 'b' * 32 + '.json')
        source.write_text(json.dumps(self.result))
        with self.assertRaisesRegex(self.module.lab.ProvisionError, 'workflow.json still exists'):
            self.recover([], include_wordpress=True, workflow_record=source)
        self.connect.assert_not_called()

    def test_archived_record_must_be_a_wordpress_archive_in_this_lab(self):
        self.validation_run()
        (self.run / 'workflow.json').unlink()
        for source in (self.run / 'state.json', self.run.parent / ('workflow.failed-wordpress-' + 'b' * 32 + '.json')):
            with self.subTest(source=source):
                with self.assertRaisesRegex(self.module.lab.ProvisionError, 'archived WordPress workflow in this run'):
                    self.recover([], include_wordpress=True, workflow_record=source)
                self.connect.assert_not_called()

    def test_recovery_refuses_to_touch_a_lab_with_an_active_capture(self):
        self.validation_run()
        with self.module.lab.run_lock(self.run):
            with self.assertRaisesRegex(self.module.lab.ProvisionError, 'Another capture or recovery'):
                self.recover([], include_wordpress=True)
        self.connect.assert_not_called()
