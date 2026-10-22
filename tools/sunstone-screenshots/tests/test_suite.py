import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots import cli, workflow


class SuiteTests(unittest.TestCase):
    def test_example_suite_validates_in_requested_order(self):
        root = Path(__file__).resolve().parents[3]
        groups = workflow.load_suite(root / 'tools/sunstone-screenshots/groups/example-suite.json', root)
        self.assertEqual([g.parent.name for g in groups], ['single-node', 'service-and-hosts'])

    def test_check_is_offline_and_does_not_create_run_directory(self):
        root = Path(__file__).resolve().parents[3]
        with TemporaryDirectory() as tmp, patch.object(cli.lab, 'provision') as provision, \
             patch.object(cli.lab, 'configuration') as configuration:
            run_dir = Path(tmp) / 'suite'
            self.assertEqual(cli.main(['--repo-root', str(root), 'run-suite',
                str(root / 'tools/sunstone-screenshots/groups/example-suite.json'),
                '--run-dir', str(run_dir), '--check']), 0)
            self.assertFalse(run_dir.exists())
        provision.assert_not_called()
        configuration.assert_not_called()

    def test_suite_rejects_retained_groups_before_execution(self):
        root = Path(__file__).resolve().parents[3]
        with patch.object(workflow, 'load_group', return_value=(Path('config'), [], False)):
            with self.assertRaisesRegex(workflow.ManifestError, 'require destroyOnSuccess'):
                workflow.load_suite(root / 'tools/sunstone-screenshots/groups/example-suite.json', root)

    def test_suite_rejects_duplicate_group_paths(self):
        with TemporaryDirectory() as tmp:
            suite = Path(tmp) / 'suite.json'
            suite.write_text(json.dumps({'version': 1, 'groups': ['first/group.json', 'first/../first/group.json']}))
            with patch.object(workflow, 'load_group', return_value=(Path('config'), [], True)):
                with self.assertRaisesRegex(workflow.ManifestError, 'Duplicate group'):
                    workflow.load_suite(suite, Path(tmp))

    def test_each_vm_is_destroyed_before_the_next_is_provisioned(self):
        for failure in (None, 'capture', 'destroy', 'unconfirmed-destroy'):
            with self.subTest(failure=failure), TemporaryDirectory() as tmp:
                root = Path(tmp)
                args = argparse.Namespace(suite='suite.json', run_dir=str(root / 'suite'),
                                          check=False, debug=False, reuse=False, keep_open_on_failure=True)
                groups = [root / 'first/group.json', root / 'second/group.json']
                events = []
                allocated = []

                def provision(config, run_dir):
                    run_dir = Path(run_dir)
                    run_dir.mkdir(parents=True)
                    vm_id = 1001 + len(allocated)
                    allocated.append(vm_id)
                    cli.lab.save(run_dir / 'state.json', {'phase': 'ready', 'vm_id': vm_id})
                    events.append(('provision', vm_id))

                def capture(args, repo_root):
                    self.assertTrue(args.keep_open_on_failure)
                    vm_id = cli.lab.load(Path(args.run_dir) / 'state.json')['vm_id']
                    events.append(('capture', vm_id))
                    if failure == 'capture':
                        raise RuntimeError('capture failed')
                    return 0

                def destroy(run_dir):
                    path = Path(run_dir) / 'state.json'
                    state = cli.lab.load(path)
                    events.append(('destroy', state['vm_id']))
                    if failure == 'destroy':
                        raise RuntimeError('destroy failed')
                    state['phase'] = 'terminating' if failure == 'unconfirmed-destroy' else 'destroyed'
                    cli.lab.save(path, state)

                with patch.object(workflow, 'load_suite', return_value=groups), \
                     patch.object(workflow, 'load_group', return_value=(Path('config'), [Path('page')], True)), \
                     patch.object(cli.lab, 'configuration'), \
                     patch.object(cli.lab, 'provision', side_effect=provision), \
                     patch.object(cli.lab, 'destroy', side_effect=destroy), \
                     patch.object(cli, '_capture', side_effect=capture), \
                     patch.object(cli, 'load_manifest', return_value={}), \
                     patch.object(cli, 'write_qa_report'):
                    if failure:
                        with self.assertRaises((RuntimeError, cli.lab.ProvisionError)):
                            cli._run_suite(args, root)
                    else:
                        self.assertEqual(cli._run_suite(args, root), 0)
                summary = cli.lab.load(root / 'suite/suite.json')
                if failure:
                    self.assertEqual(allocated, [1001])
                    self.assertEqual([g['status'] for g in summary['groups']], ['failed', 'pending'])
                else:
                    self.assertEqual(events, [('provision', 1001), ('capture', 1001), ('destroy', 1001),
                                              ('provision', 1002), ('capture', 1002), ('destroy', 1002)])
                    self.assertEqual([g['vm_id'] for g in summary['groups']], [1001, 1002])
                    self.assertEqual([g['lab_status'] for g in summary['groups']], ['destroyed', 'destroyed'])
                    self.assertNotEqual(summary['groups'][0]['run_dir'], summary['groups'][1]['run_dir'])

    def test_all_provision_settings_validated_before_first_vm(self):
        with TemporaryDirectory() as tmp:
            args = argparse.Namespace(suite='suite', run_dir=str(Path(tmp) / 'run'), check=False)
            with patch.object(workflow, 'load_suite', return_value=[Path('a'), Path('b')]), \
                 patch.object(workflow, 'load_group', return_value=(Path('config'), [], True)), \
                 patch.object(cli.lab, 'configuration', side_effect=[{}, cli.lab.ProvisionError('bad key')]), \
                 patch.object(cli.lab, 'provision') as provision:
                with self.assertRaisesRegex(cli.lab.ProvisionError, 'bad key'):
                    cli._run_suite(args, Path(tmp))
            provision.assert_not_called()
            self.assertFalse(Path(args.run_dir).exists())
