import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'sunstone_screenshots/guest/pause-apt-updates.sh'


class GuestUpdateGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.apt = self.root / 'apt.conf.d'
        self.apt.mkdir()
        self.log = self.root / 'commands.log'
        self.states = self.root / 'states.json'
        self.script = SCRIPT.read_text().replace('/etc/apt/apt.conf.d', str(self.apt))
        self.env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ['PATH'],
                        GUARD_LOG=str(self.log), GUARD_STATES=str(self.states))
        systemctl = self.root / 'systemctl'
        systemctl.write_text('''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
args = sys.argv[1:]
with Path(os.environ['GUARD_LOG']).open('a') as stream:
    stream.write(' '.join(args) + '\\n')
if args[0] == os.environ.get('GUARD_FAIL'):
    sys.exit(1)
if args[0] == 'show':
    path = Path(os.environ['GUARD_STATES'])
    states = json.loads(path.read_text())
    if '--property=LoadState' in args:
        print('not-found' if args[1] in states.get('missing', []) else 'loaded')
    else:
        sequence = states.get(args[1], ['inactive'])
        print(sequence[0])
        if len(sequence) > 1:
            states[args[1]] = sequence[1:]
            path.write_text(json.dumps(states))
elif args[0] == 'stop':
    if any(not unit.endswith('.timer') for unit in args[1:]):
        sys.exit('Refusing to terminate a running package service in this test')
elif args[0] == 'mask':
    if '--now' in args:
        sys.exit('Masking must not terminate running package services')
else:
    sys.exit('Unexpected systemctl command')
''')
        systemctl.chmod(0o700)
        sleep = self.root / 'sleep'
        sleep.write_text('#!/bin/sh\nprintf "sleep %s\\n" "$1" >> "$GUARD_LOG"\n')
        sleep.chmod(0o700)

    def execute(self, states=None, **env):
        self.states.write_text(json.dumps(states or {}))
        return subprocess.run(['bash', '-se'], input=self.script, text=True,
                              capture_output=True, env=dict(self.env, **env), timeout=5)

    def commands(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_stops_only_timers_and_waits_for_active_package_jobs(self):
        result = self.execute({'apt-daily.service': ['active', 'deactivating', 'inactive'],
                               'apt-daily-upgrade.service': ['activating', 'active', 'inactive']})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.apt / '99sunstone-screenshot-lab').read_text(), 'APT::Periodic::Enable "0";\n')
        commands = self.commands()
        self.assertEqual([command for command in commands if command.startswith('stop ')],
                         ['stop apt-daily.timer', 'stop apt-daily-upgrade.timer'])
        mask = 'mask apt-daily.timer apt-daily-upgrade.timer apt-daily.service apt-daily-upgrade.service'
        self.assertLess(commands.index(mask), commands.index('show apt-daily.service --property=ActiveState --value'))
        self.assertEqual(commands.count('sleep 2'), 4)
        self.assertIn('Scheduled APT jobs are idle', result.stdout)

    def test_missing_timers_are_not_stopped(self):
        result = self.execute({'missing': ['apt-daily.timer', 'apt-daily-upgrade.timer']})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(command.startswith('stop ') for command in self.commands()))
        self.assertTrue(any(command.startswith('mask ') for command in self.commands()))

    def test_non_apt_guest_is_left_unchanged(self):
        self.apt.rmdir()
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('does not use APT', result.stdout)
        self.assertFalse(self.apt.exists())
        self.assertEqual(self.commands(), [])

    def test_failure_to_mask_aborts_instead_of_assuming_safe_capture_environment(self):
        result = self.execute(GUARD_FAIL='mask')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Scheduled APT jobs are idle', result.stdout)

    def test_unknown_package_job_state_aborts(self):
        result = self.execute({'apt-daily.service': ['unexpected']})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unexpected state for apt-daily.service', result.stderr)

    def test_bootstrap_does_not_continue_until_both_jobs_are_idle(self):
        self.script += '\necho miniONE-started\n'
        result = self.execute({'apt-daily-upgrade.service': ['active', 'inactive']})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(result.stdout.index('Waiting for apt-daily-upgrade.service'),
                        result.stdout.index('miniONE-started'))
        result = self.execute({'apt-daily-upgrade.service': ['unexpected']})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('miniONE-started', result.stdout)
