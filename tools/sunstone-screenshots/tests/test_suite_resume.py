import argparse
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots import cli, workflow


class SuiteResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.groups = [self.root / 'first/group.json', self.root / 'second/group.json']
        self.args = argparse.Namespace(suite=str(self.root / 'suite.json'), run_dir=str(self.run),
                                       check=False, debug=False, reuse=False, resume=True)
        self.saved = {'version': 1, 'suite': self.args.suite, 'groups': [
            {'group': str(group), 'run_dir': str(self.run / f'{i:02d}-{group.parent.name}'),
             'status': 'failed' if i == 1 else 'pending'}
            for i, group in enumerate(self.groups, 1)]}
        self.first = Path(self.saved['groups'][0]['run_dir'])
        self.first.mkdir(parents=True)
        self.config = {'minione_script': 'https://example.org/minione'}
        cli.lab.save(self.first / 'state.json', {'phase': 'failed', 'failed_phase': 'checking-services',
            'vm_id': 239, 'address': '192.0.2.4', 'vm_name': 'lab', 'config': self.config})
        cli.lab.save(self.run / 'suite.json', self.saved)

    def test_resume_rechecks_first_vm_and_provisions_only_second(self):
        events = []
        def resume(path):
            state = cli.lab.load(path / 'state.json')
            events.append(('resume', state['vm_id']))
            state['phase'] = 'ready'
            cli.lab.save(path / 'state.json', state)
        def provision(config, path):
            events.append(('provision', 240))
            path.mkdir(parents=True)
            cli.lab.save(path / 'state.json', {'phase': 'ready', 'vm_id': 240})
        def capture(args, root):
            events.append(('capture', cli.lab.load(Path(args.run_dir) / 'state.json')['vm_id']))
            return 0
        def destroy(path):
            state = cli.lab.load(path / 'state.json')
            events.append(('destroy', state['vm_id']))
            state['phase'] = 'destroyed'
            cli.lab.save(path / 'state.json', state)
        with patch.object(workflow, 'load_suite', return_value=self.groups), \
             patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('page')], True)), \
             patch.object(cli.lab, 'configuration', return_value=self.config), \
             patch.object(cli.lab, 'resume_readiness', side_effect=resume), \
             patch.object(cli.lab, 'provision', side_effect=provision), \
             patch.object(cli.lab, 'destroy', side_effect=destroy), \
             patch.object(cli, '_capture', side_effect=capture), \
             patch.object(cli, 'load_manifest', return_value={}), \
             patch.object(cli, 'write_qa_report'):
            self.assertEqual(cli._run_suite(self.args, self.root), 0)
        self.assertEqual(events, [('resume', 239), ('capture', 239), ('destroy', 239),
                                  ('provision', 240), ('capture', 240), ('destroy', 240)])

    def test_resume_refuses_partial_install_and_started_workflow(self):
        cli.lab.save(self.first / 'workflow.json', {'pages': []})
        with self.assertRaisesRegex(cli.lab.ProvisionError, 'already started'):
            cli._validate_suite_resume(self.saved, self.saved)
        (self.first / 'workflow.json').unlink()
        state = cli.lab.load(self.first / 'state.json')
        state['failed_phase'] = 'installing'
        cli.lab.save(self.first / 'state.json', state)
        with self.assertRaisesRegex(cli.lab.ProvisionError, 'completed installations'):
            cli._validate_suite_resume(self.saved, self.saved)

    def test_resume_rejects_tampered_run_directory(self):
        tampered = copy.deepcopy(self.saved)
        tampered['groups'][0]['run_dir'] = str(self.root / 'other-lab')
        with self.assertRaisesRegex(cli.lab.ProvisionError, 'paths/order'):
            cli._validate_suite_resume(tampered, self.saved)

    def test_completed_group_must_be_destroyed(self):
        saved = copy.deepcopy(self.saved)
        saved['groups'][0].update(status='complete', vm_id=239)
        with self.assertRaisesRegex(cli.lab.ProvisionError, 'recorded VM destroyed'):
            cli._validate_suite_resume(saved, self.saved)
        state = cli.lab.load(self.first / 'state.json')
        state['phase'] = 'destroyed'
        cli.lab.save(self.first / 'state.json', state)
        self.assertEqual(cli._validate_suite_resume(saved, self.saved), saved)

    def test_resume_check_is_offline_and_preserves_saved_state(self):
        self.args.check = True
        before = (self.run / 'suite.json').read_bytes()
        with patch.object(workflow, 'load_suite', return_value=self.groups), \
             patch.object(cli.lab, 'configuration') as config, \
             patch.object(cli.lab, 'resume_readiness') as resume:
            self.assertEqual(cli._run_suite(self.args, self.root), 0)
        config.assert_not_called()
        resume.assert_not_called()
        self.assertEqual((self.run / 'suite.json').read_bytes(), before)
