from contextlib import nullcontext, redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import cli, provision as lab


class SudoSessionTests(unittest.TestCase):
    def test_disabled_session_does_not_invoke_sudo(self):
        with patch.object(lab.subprocess, 'run') as run:
            with lab.sudo_session():
                pass
        run.assert_not_called()

    def test_session_validates_without_prompting_and_stops_worker_on_exit(self):
        with patch.object(lab.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            with lab.sudo_session(True):
                self.assertTrue(any(t.name == 'sunstone-sudo-keepalive' for t in threading.enumerate()))
            run.assert_called_once_with(['sudo', '-n', '-v'], capture_output=True, text=True, timeout=10)
        self.assertFalse(any(t.name == 'sunstone-sudo-keepalive' for t in threading.enumerate()))

    def test_missing_authorization_fails_before_running_the_command(self):
        command = Mock()
        with patch.object(lab.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stderr='password required')):
            with self.assertRaisesRegex(lab.ProvisionError, 'Run sudo -v'):
                with lab.sudo_session(True):
                    command()
        command.assert_not_called()

    def test_session_refreshes_during_long_work(self):
        refreshed = threading.Event()
        calls = []
        def refresh(*args, **kwargs):
            calls.append(args)
            if len(calls) >= 2:
                refreshed.set()
            return SimpleNamespace(returncode=0)
        with patch.object(lab, '_SUDO_REFRESH_INTERVAL', 0.01), \
             patch.object(lab.subprocess, 'run', side_effect=refresh):
            with lab.sudo_session(True):
                self.assertTrue(refreshed.wait(3))
        self.assertGreaterEqual(len(calls), 2)
        self.assertFalse(any(t.name == 'sunstone-sudo-keepalive' for t in threading.enumerate()))

    def test_refresh_failure_warns_without_prompting_in_background(self):
        refreshed = threading.Event()
        calls = []
        def refresh(*args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                return SimpleNamespace(returncode=0)
            refreshed.set()
            return SimpleNamespace(returncode=1, stderr='policy denied')
        output = StringIO()
        with patch.object(lab, '_SUDO_REFRESH_INTERVAL', 0.01), \
             patch.object(lab.subprocess, 'run', side_effect=refresh), redirect_stderr(output):
            with lab.sudo_session(True):
                self.assertTrue(refreshed.wait(3))
        self.assertEqual(len(calls), 2)
        self.assertIn('Subsequent guest commands and cleanup may fail', output.getvalue())

    def test_exceptions_and_interrupts_stop_the_refresh_worker(self):
        for error in (RuntimeError('failed'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), \
                 patch.object(lab.subprocess, 'run', return_value=SimpleNamespace(returncode=0)):
                with self.assertRaises(type(error)):
                    with lab.sudo_session(True):
                        raise error
                self.assertFalse(any(t.name == 'sunstone-sudo-keepalive' for t in threading.enumerate()))

    def test_sudo_errors_and_timeout_are_actionable(self):
        for error in (FileNotFoundError('sudo'), subprocess.TimeoutExpired(['sudo'], 10)):
            with self.subTest(error=type(error).__name__), patch.object(lab.subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(lab.ProvisionError, 'Could not refresh sudo authorization'):
                    with lab.sudo_session(True):
                        self.fail('Command must not run')

    def test_capture_group_and_suite_flags_scope_the_session_to_dispatch(self):
        for command, handler in (('capture', '_capture'), ('run-group', '_run_group'), ('run-suite', '_run_suite')):
            with self.subTest(command=command), \
                 patch.object(lab, 'sudo_session', return_value=nullcontext()) as session, \
                 patch.object(cli, handler, return_value=0):
                self.assertEqual(cli.main([command, 'example.json', '--run-dir', 'unused', '--keep-sudo-alive']), 0)
                session.assert_called_once_with(True)
        with patch.object(lab, 'sudo_session', return_value=nullcontext()) as session, patch.object(lab, 'provision'):
            self.assertEqual(cli.main(['provision', 'config.json', '--run-dir', 'unused', '--keep-sudo-alive']), 0)
            session.assert_called_once_with(True)

    def test_group_check_never_starts_sudo_refresh(self):
        with patch.object(cli.workflow, 'load_group', return_value=(Path('config'), [Path('page')], False)), \
             patch.object(lab, 'sudo_session', wraps=lab.sudo_session) as session, \
             patch.object(lab.subprocess, 'run') as sudo:
            self.assertEqual(cli.main(['run-group', 'example.json', '--run-dir', 'unused',
                                      '--keep-sudo-alive', '--check']), 0)
        session.assert_called_once_with(False)
        sudo.assert_not_called()
