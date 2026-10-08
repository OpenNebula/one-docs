import json
import hashlib
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import provision as lab


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('auth', 'key', 'minione'):
            (self.root / name).write_text('fixture')
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({
            'endpoint': 'http://localhost:2633/RPC2', 'auth_file': 'auth',
            'ssh_key': 'key', 'ssh_user': 'root', 'minione_script': 'minione',
            'template_id': 42, 'opennebula_version': '7.4'}))
        self.run = self.root / 'run'

    def test_nic_selection_does_not_use_first_arbitrary_ip(self):
        one = Mock()
        one.vm.info.return_value = SimpleNamespace(NAME='lab', STATE=3, LCM_STATE=3,
            TEMPLATE={'NIC': [{'NIC_ID': '1', 'IP': '10.1.0.2'},
                              {'NIC_ID': '0', 'IP': '192.0.2.4'}]})
        self.assertEqual(lab.running_address(one, {'vm_id': 4, 'vm_name': 'lab', 'config': {}}), '192.0.2.4')

    def local_user_config(self):
        cfg = lab.load(self.config)
        cfg.update(ssh_local_user='oneadmin', ssh_key='/var/lib/one/.ssh/id_rsa',
                   ssh_known_hosts='/var/lib/one/.ssh/screenshot_lab_known_hosts')
        self.config.write_text(json.dumps(cfg))
        return cfg

    def test_local_user_validates_key_as_that_user(self):
        self.local_user_config()
        with patch.object(lab.shutil, 'which', return_value='/usr/bin/tool'), \
             patch.object(lab.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            cfg = lab.configuration(self.config)
        self.assertEqual(cfg['ssh_key'], '/var/lib/one/.ssh/id_rsa')
        self.assertEqual(run.call_args.args[0], ['sudo', '-n', '-H', '-u', 'oneadmin',
                                               '--', 'test', '-r', cfg['ssh_key']])

    def test_local_user_sudo_failure_is_actionable(self):
        self.local_user_config()
        with patch.object(lab.shutil, 'which', return_value='/usr/bin/tool'), \
             patch.object(lab.subprocess, 'run', return_value=SimpleNamespace(
                 returncode=1, stderr='sudo: a password is required')):
            with self.assertRaisesRegex(lab.ProvisionError, 'sudo authorization'):
                lab.configuration(self.config)

    def test_local_user_requires_absolute_paths(self):
        cfg = self.local_user_config()
        for key in ('ssh_key', 'ssh_known_hosts'):
            with self.subTest(key=key):
                self.config.write_text(json.dumps(dict(cfg, **{key: '~/.ssh/key'})))
                with patch.object(lab.shutil, 'which', return_value='/usr/bin/tool'):
                    with self.assertRaisesRegex(lab.ProvisionError, 'absolute path'):
                        lab.configuration(self.config)

    def test_ssh_local_user_prefix_and_known_hosts(self):
        cfg = self.local_user_config()
        with patch.object(lab.subprocess, 'run') as run:
            lab.ssh({'config': cfg, 'address': '192.0.2.4'}, self.run, 'true\n')
        command = run.call_args.args[0]
        self.assertEqual(command[:7], ['sudo', '-n', '-H', '-u', 'oneadmin', '--', 'ssh'])
        self.assertIn('UserKnownHostsFile=' + cfg['ssh_known_hosts'], command)
        self.assertEqual(command[-2:], ['root@192.0.2.4', 'bash -se'])
        self.assertEqual(run.call_args.kwargs['input'], 'true\n')

    def test_default_ssh_still_uses_run_known_hosts(self):
        cfg = lab.configuration(self.config)
        with patch.object(lab.subprocess, 'run') as run:
            lab.ssh({'config': cfg, 'address': '192.0.2.4'}, self.run, 'true\n')
        command = run.call_args.args[0]
        self.assertEqual(command[0], 'ssh')
        self.assertIn(f'UserKnownHostsFile={self.run / "known_hosts"}', command)
        self.assertFalse(any(arg.startswith('HostKeyAlias=') for arg in command))

    def test_host_keys_are_scoped_to_new_lab_identity(self):
        cfg = self.local_user_config()
        for alias in ('docs-lab-first', 'docs-lab-second'):
            with patch.object(lab.subprocess, 'run') as run:
                lab.ssh({'config': cfg, 'address': '192.0.2.4',
                         'host_key_alias': alias}, self.run, 'true\n')
            command = run.call_args.args[0]
            self.assertIn(f'HostKeyAlias={alias}', command)
            self.assertIn('CheckHostIP=no', command)
            self.assertIn('StrictHostKeyChecking=accept-new', command)

    def test_ssh_failure_is_reported_and_retained(self):
        cfg = lab.load(self.config)
        cfg['boot_timeout'] = 1
        self.config.write_text(json.dumps(cfg))
        one = Mock()
        one.template.instantiate.return_value = 17
        error = 'root@192.0.2.4: Permission denied (publickey).'
        with patch.object(lab, 'connect', return_value=one), \
             patch.object(lab, 'running_address', return_value='192.0.2.4'), \
             patch.object(lab, 'ssh', return_value=SimpleNamespace(returncode=255, stderr=error)), \
             patch.object(lab.time, 'monotonic', side_effect=[0, 0, 2]), \
             patch.object(lab, 'install') as install:
            with self.assertRaisesRegex(lab.ProvisionError, 'Permission denied'):
                lab.provision(self.config, self.run)
        install.assert_not_called()
        state = lab.load(self.run / 'state.json')
        self.assertEqual(state['ssh_error'], error)
        self.assertEqual(state['failed_phase'], 'booting')

    def test_ssh_timeout_and_recovery(self):
        state = {}
        with patch.object(lab, 'ssh', return_value=None):
            self.assertFalse(lab.guest_ready(state, self.run))
        self.assertEqual(state['ssh_error'], 'SSH command timed out')
        with patch.object(lab, 'ssh', return_value=SimpleNamespace(returncode=0)):
            self.assertTrue(lab.guest_ready(state, self.run))
        self.assertNotIn('ssh_error', state)

    def test_failed_install_records_vm_for_cleanup(self):
        one = Mock()
        one.template.instantiate.return_value = 17
        with patch.object(lab, 'connect', return_value=one), \
             patch.object(lab, 'running_address', return_value='192.0.2.4'), \
             patch.object(lab, 'guest_ready', return_value=True), \
             patch.object(lab, 'install', side_effect=lab.ProvisionError('failure')):
            with self.assertRaises(lab.ProvisionError):
                lab.provision(self.config, self.run)
        state = lab.load(self.run / 'state.json')
        self.assertEqual(state['vm_id'], 17)
        self.assertEqual(state['failed_phase'], 'installing')
        self.assertEqual(state['phase'], 'failed')
        self.assertEqual((self.run / 'state.json').stat().st_mode & 0o777, 0o600)

    def test_complete_lifecycle_and_idempotent_destroy(self):
        one = Mock()
        one.template.instantiate.return_value = 17
        with patch.object(lab, 'connect', return_value=one), \
             patch.object(lab, 'running_address', return_value='192.0.2.4'), \
             patch.object(lab, 'guest_ready', return_value=True), \
             patch.object(lab, 'install'), \
             patch.object(lab, 'services_ready', return_value=True), \
             patch.object(lab, 'http_ready', return_value=True):
            lab.provision(self.config, self.run)
            state = lab.load(self.run / 'state.json')
            self.assertEqual(state['phase'], 'ready')
            self.assertEqual(state['host_key_alias'], state['vm_name'])
            one.vm.info.side_effect = [SimpleNamespace(NAME=state['vm_name'], STATE=3),
                                      SimpleNamespace(NAME=state['vm_name'], STATE=6)]
            lab.destroy(self.run)
            lab.destroy(self.run)
        one.vm.action.assert_called_once_with('terminate-hard', 17)

    def test_destroy_refuses_different_vm(self):
        self.run.mkdir()
        lab.save(self.run / 'state.json', {'phase': 'failed', 'vm_id': 17,
                 'vm_name': 'expected', 'config': {}})
        one = Mock()
        one.vm.info.return_value = SimpleNamespace(NAME='different')
        with patch.object(lab, 'connect', return_value=one):
            with self.assertRaises(lab.ProvisionError):
                lab.destroy(self.run)
        one.vm.action.assert_not_called()

    def test_installer_change_refused(self):
        cfg = lab.configuration(self.config)
        (self.root / 'minione').write_text('changed')
        with self.assertRaises(lab.ProvisionError):
            lab.install({'config': cfg}, self.run)

    def test_minione_options_validation(self):
        original = lab.load(self.config)
        for key, value in [('minione_force', 'true'), ('minione_force', 1),
                           ('minione_password', ''), ('minione_password', 123),
                           ('minione_password', 'a\nb'), ('minione_password', 'a\x00b')]:
            with self.subTest(key=key, value=value):
                self.config.write_text(json.dumps(dict(original, **{key: value})))
                with self.assertRaises(lab.ProvisionError):
                    lab.configuration(self.config)

    def test_minione_optional_arguments(self):
        import shlex
        self.run.mkdir()
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                cfg = lab.configuration(self.config)
                password = "debug ' pass; $(false)"
                if enabled:
                    cfg.update(minione_force=True, minione_password=password,
                               repo_base='http://172.20.0.1/build/7.5-nightly/ubuntu2404/repo')
                with patch.object(lab, 'ssh', return_value=SimpleNamespace(returncode=0)) as ssh:
                    lab.install({'config': cfg}, self.run)
                script = ssh.call_args.args[2]
                command = next(line for line in script.splitlines()
                               if line.startswith('bash /root/screenshot-lab/minione '))
                args = shlex.split(command)
                self.assertEqual('--force' in args, enabled)
                self.assertEqual('--password' in args, enabled)
                if enabled:
                    self.assertEqual(args[args.index('--password') + 1], password)
                    self.assertEqual(args[args.index('--repo-base') + 1], cfg['repo_base'])

    def url_config(self):
        cfg = lab.load(self.config)
        cfg['minione_script'] = 'https://example.org/releases/v7.4.0/minione'
        self.config.write_text(json.dumps(cfg))
        return cfg['minione_script']

    def test_url_configuration_is_offline(self):
        url = self.url_config()
        with patch.object(lab, 'urlopen') as download:
            cfg = lab.configuration(self.config)
        download.assert_not_called()
        self.assertEqual(cfg['minione_script'], url)

    def test_download_records_exact_bytes_and_source(self):
        url = self.url_config()
        cfg = lab.configuration(self.config)
        self.run.mkdir()
        script = b'#!/bin/bash\necho fixture\n'
        with patch.object(lab, 'urlopen', return_value=BytesIO(script)):
            lab.prepare_installer(cfg, self.run)
        self.assertEqual(Path(cfg['minione_script']).read_bytes(), script)
        self.assertEqual(cfg['installer_url'], url)
        self.assertEqual(cfg['installer_sha256'], hashlib.sha256(script).hexdigest())
        self.assertEqual(Path(cfg['minione_script']).stat().st_mode & 0o777, 0o600)

    def test_download_failure_does_not_allocate(self):
        self.url_config()
        one = Mock()
        with patch.object(lab, 'connect', return_value=one), \
             patch.object(lab, 'urlopen', side_effect=OSError('download failed')):
            with self.assertRaises(lab.ProvisionError):
                lab.provision(self.config, self.run)
        one.template.instantiate.assert_not_called()
        state = lab.load(self.run / 'state.json')
        self.assertIsNone(state['vm_id'])
        self.assertEqual(state['failed_phase'], 'preparing-installer')

    def test_capture_uses_inner_credentials(self):
        self.run.mkdir()
        lab.save(self.run / 'state.json', {'phase': 'ready', 'vm_id': 17,
                 'vm_name': 'lab', 'config': {}, 'sunstone_url': 'http://192.0.2.4:80'})
        one = Mock()
        one.vm.info.return_value = SimpleNamespace(NAME='lab', STATE=3, LCM_STATE=3)
        with patch.object(lab, 'connect', return_value=one), \
             patch.object(lab, 'ssh', return_value=SimpleNamespace(returncode=0, stdout='oneadmin:inner:password\n')):
            env = lab.capture_environment(self.run)
        self.assertEqual(env['SUNSTONE_PASSWORD'], 'inner:password')


if __name__ == '__main__':
    unittest.main()
