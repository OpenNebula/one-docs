import json
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from sunstone_screenshots import cli, workflow


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'tools/sunstone-screenshots/groups/oneks-quickstart/oneks_quickstart.json'


class ForceWorkflowTests(unittest.TestCase):
    def archive_command(self):
        calls = []
        token = workflow.guest_runner.set(calls.append)
        try:
            workflow.archive_workflow_markers(json.loads(MANIFEST.read_text()))
        finally:
            workflow.guest_runner.reset(token)
        return calls[0]['command'].split('\n', 1)[1].rsplit('SUNSTONE_ARCHIVE', 1)[0]

    def test_archives_selected_markers_and_preserves_unrelated_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('oneks-workflow.json', 'theme-workflow.json', 'wordpress-workflow.json', 'oneks-workflow.py'):
                (root / name).write_text(name)
            command = self.archive_command().replace("Path('/root/screenshot-lab')", repr(root))
            with patch.dict(os.environ, SUNSTONE_WORKFLOW_ID='new-attempt'), redirect_stdout(StringIO()):
                exec(command, {'PosixPath': Path})
            for name in ('oneks-workflow.json', 'theme-workflow.json'):
                self.assertFalse((root / name).exists())
                self.assertEqual((root / 'abandoned-new-attempt' / name).read_text(), name)
            self.assertTrue((root / 'wordpress-workflow.json').exists())
            self.assertTrue((root / 'oneks-workflow.py').exists())
            self.assertEqual((root / 'abandoned-new-attempt').stat().st_mode & 0o777, 0o700)

    def test_symlink_is_refused_before_any_marker_is_moved(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'oneks-workflow.json').write_text('original')
            (root / 'theme-workflow.json').symlink_to(root / 'missing')
            command = self.archive_command().replace("Path('/root/screenshot-lab')", repr(root))
            with self.assertRaisesRegex(SystemExit, 'non-regular'):
                exec(command, {'PosixPath': Path})
            self.assertEqual((root / 'oneks-workflow.json').read_text(), 'original')

    def test_unknown_hooks_are_not_silently_bypassed(self):
        with self.assertRaisesRegex(workflow.lab.ProvisionError, 'no supported'):
            workflow.archive_workflow_markers({'hooks': {'setup': [{'script': 'custom.sh'}]}})

    def test_flag_requires_run_dir_and_hooks(self):
        for extra in ([], ['--run-dir', '/unused', '--skip-hooks']):
            with self.subTest(extra=extra), patch.object(cli.lab, 'capture_environment') as environment, \
                    redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(cli.main(['capture', str(MANIFEST), '--force-workflow'] + extra), 1)
                environment.assert_not_called()

    def test_cli_archives_before_hooks_without_provisioning(self):
        with TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
            events = []
            with patch.object(cli.lab, 'capture_environment', return_value={}), \
                    patch.object(workflow.lab, 'ssh', return_value=Mock(returncode=0)) as ssh, \
                    patch.object(workflow, 'archive_workflow_markers', side_effect=lambda m: events.append('archive')), \
                    patch.object(workflow, 'capture_with_hooks', side_effect=lambda *a: events.append('hooks')), \
                    patch.object(cli.lab, 'provision') as provision, redirect_stdout(StringIO()):
                result = cli.main(['capture', str(MANIFEST), '--run-dir', str(run),
                                   '--output-root', str(run / 'screenshots'), '--force-workflow'])
            self.assertEqual(result, 0)
            self.assertEqual(events, ['archive', 'hooks'])
            provision.assert_not_called()
            record = json.loads((run / 'screenshots/capture-results.json').read_text())
            self.assertTrue(next(iter(record['manifests'].values()))['force_workflow'])


if __name__ == '__main__':
    unittest.main()
