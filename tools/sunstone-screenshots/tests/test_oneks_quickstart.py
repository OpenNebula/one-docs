import copy
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from sunstone_screenshots import capture, cli
from sunstone_screenshots.docs_scan import scan_document
from sunstone_screenshots.manifest import screenshot_variants
from sunstone_screenshots import workflow
from sunstone_screenshots.workflow import load_group


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'tools/sunstone-screenshots'
GROUP = BASE / 'groups/oneks-quickstart'
DOC = 'content/getting_started/install_opennebula/evaluation/oneks_quickstart.md'


class OneKSManifestTests(unittest.TestCase):
    def test_lab_configs_pin_the_oneks_tproxy_fixed_installer(self):
        expected = ('https://raw.githubusercontent.com/OpenNebula/minione/'
                    '6cc1d37a122b3edca3e3f105c15f40f47ca33c6a/minione')
        configs = [BASE / 'provision.example.json',
                   BASE / 'groups/getting-started/provision.json',
                   BASE / 'groups/service-and-hosts/provision.json',
                   GROUP / 'provision.json']
        for config in configs:
            with self.subTest(config=config):
                self.assertEqual(json.loads(config.read_text())['minione_script'], expected)

    def test_group_and_inventory_point_to_the_same_document_and_provision(self):
        config, paths, destroy = load_group(GROUP / 'group.json', ROOT)
        self.assertEqual(config, GROUP / 'provision.json')
        self.assertEqual(json.loads(config.read_text())['vm_resources'],
                         {'cpu': 4, 'vcpu': 4, 'memory_mb': 16384})
        self.assertEqual(paths, [GROUP / 'oneks_quickstart.json'])
        self.assertTrue(destroy)
        with (BASE / 'inventory.csv').open() as stream:
            rows = [r for r in csv.DictReader(stream) if r['doc'] == DOC]
        self.assertEqual(len(rows), 1)
        self.assertEqual(BASE / rows[0]['manifest'], paths[0])
        self.assertEqual(BASE / rows[0]['group'], GROUP / 'group.json')
        self.assertEqual(rows[0]['automation_status'], 'draft')

    def test_all_sunstone_pairs_are_mapped_once_in_document_order(self):
        manifest = json.loads((GROUP / 'oneks_quickstart.json').read_text())
        references = scan_document(ROOT, Path(DOC))
        expected = [v.asset_path for r in references for v in r.variants
                    if not v.asset_path.endswith('/k8s_example_application.png')]
        actual = [asset for shot in manifest['screenshots'] for _, asset in screenshot_variants(shot)]
        self.assertEqual(actual, expected)
        self.assertEqual(len(manifest['screenshots']), 19)
        self.assertEqual(len(actual), 38)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual({s['doc'] for s in manifest['screenshots']}, {DOC})
        self.assertTrue(all(s['status'] == 'draft' for s in manifest['screenshots']))
        recipe = json.loads((GROUP / 'recipes/oneks-quickstart.json').read_text())
        self.assertEqual([c['id'] for c in recipe['captures']], [s['capture'] for s in manifest['screenshots']])
        actions = {'goto', 'fill', 'click', 'press', 'hover', 'defocus', 'waitForSelector', 'waitTime', 'guestCommand'}
        steps = recipe['setup'] + recipe['teardown'] + [s for c in recipe['captures'] for s in c['steps']]
        self.assertTrue(all(s['action'] in actions for s in steps))

    def test_lifecycle_commands_are_checkpoints_and_waits_not_unguarded_deletions(self):
        recipe = json.loads((GROUP / 'recipes/oneks-quickstart.json').read_text())
        commands = [s for c in recipe['captures'] for s in c['steps'] if s['action'] == 'guestCommand']
        self.assertEqual([s['command'].split()[-1] for s in commands],
                         ['private', 'dns', 'cluster', 'wait-cluster', 'wait-worker'])
        self.assertTrue(all(s['command'].startswith('python3 /root/screenshot-lab/oneks-workflow.py ') for s in commands))
        self.assertEqual(commands[-2]['timeout'], 1860)
        self.assertEqual(commands[-1]['timeout'], 1260)
        self.assertEqual(recipe['teardown'][-1]['selector'], "input[type='password']")
        kubeconfig = recipe['captures'][-1]
        self.assertEqual(kubeconfig['screenshot']['maskSelectors'],
                         ["[data-cy='tab-content-kubeconfig'] .code-container"])
        self.assertEqual(kubeconfig['steps'][1]['selector'], kubeconfig['screenshot']['maskSelectors'][0])

    def test_check_does_not_allocate_a_vm_or_create_a_run_directory(self):
        with TemporaryDirectory() as tmp, patch.object(cli.lab, 'provision') as provision:
            run = Path(tmp) / 'not-created'
            self.assertEqual(cli.main(['--repo-root', str(ROOT), 'run-group', str(GROUP / 'group.json'),
                                       '--run-dir', str(run), '--check']), 0)
            self.assertFalse(run.exists())
            provision.assert_not_called()

    def test_capture_retry_keeps_the_failed_group_record_and_does_not_reprovision(self):
        with TemporaryDirectory() as tmp:
            run = Path(tmp)
            manifest = GROUP / 'oneks_quickstart.json'
            failed = {'group': str(GROUP / 'group.json'), 'pages': [
                {'manifest': str(manifest), 'status': 'failed'}], 'lab_status': 'retained'}
            (run / 'state.json').write_text(json.dumps({'phase': 'ready', 'config': {}}))
            record = run / 'workflow.json'
            record.write_text(json.dumps(failed))
            before = record.read_bytes()
            with patch.object(cli.lab, 'capture_environment', return_value={'SUNSTONE_URL': 'http://fixture.test'}), \
                 patch.object(workflow.lab, 'ssh', return_value=SimpleNamespace(returncode=0)) as ssh, \
                 patch.object(cli.lab, 'provision') as provision, patch.object(cli, 'capture_screenshots') as browser:
                self.assertEqual(cli.main(['--repo-root', str(ROOT), 'capture', str(manifest),
                                           '--run-dir', str(run), '--output-root', str(run / 'screenshots'),
                                           '--debug', '--keep-open-on-failure']), 0)
            self.assertEqual(record.read_bytes(), before)
            provision.assert_not_called()
            browser.assert_called_once()
            self.assertEqual(ssh.call_count, 4)
            self.assertIn("['systemctl', 'restart', 'opennebula-ks']", ssh.call_args_list[0].args[2])
            result = json.loads((run / 'screenshots/capture-results.json').read_text())
            identity = manifest.relative_to(ROOT).as_posix()
            self.assertEqual(result['manifests'][identity]['status'], 'complete')


class OneKSGuestTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.environment = patch.dict('os.environ', {'SUNSTONE_WORKFLOW_ID': 'current'})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.marker = Path(self.temp.name) / 'oneks.json'
        code = (GROUP / 'scripts/prepare-oneks.sh').read_text().split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
        self.ns = {'__name__': 'oneks_fixture'}
        exec(compile(code, 'oneks-workflow.py', 'exec'), self.ns)
        self.ns['MARKER'] = self.marker
        self.state = dict(version=1, workflow_id='current', public_id='0', original_dns='8.8.8.8',
                          previous_networks=['0'], previous_clusters=['7'], private_id=None, cluster_id=None)
        self.public = self.network('0', 'vnet', dns='1.1.1.1')
        self.private = self.network('1', 'private-k8s')
        self.cluster = dict(ID='8', NAME='docs-screenshot-oneks', UID='0', TEMPLATE={'CLUSTER_BODY': {
            'state': 'RUNNING', 'deployment': {'cluster': {'id': 0}, 'networks': {
                'public': {'id': 0}, 'private': {'id': 1}}}, 'node_groups': []}})
        self.extra_clusters = []
        self.vms = []
        self.events = []
        self.ns['one'] = self.one
        self.ns['save'](self.state)

    def network(self, identity, name, dns=None):
        template = '<DNS>' + dns + '</DNS>' if dns is not None else ''
        return ET.fromstring(f'<VNET><ID>{identity}</ID><NAME>{name}</NAME><UID>0</UID>'
                             f'<USED_LEASES>0</USED_LEASES><CLUSTERS><ID>0</ID></CLUSTERS>'
                             f'<TEMPLATE>{template}<CUSTOM>preserved</CUSTOM></TEMPLATE></VNET>')

    def one(self, *args, input=None):
        self.events.append((args, input))
        if args == ('onevnet', 'list', '-x'):
            pool = ET.Element('VNET_POOL')
            pool.extend([r for r in (self.public, self.private) if r is not None])
            return ET.tostring(pool, encoding='unicode')
        if args[:2] == ('onevnet', 'show'):
            record = next(r for r in (self.public, self.private) if r is not None and r.findtext('ID') == args[2])
            return ET.tostring(record, encoding='unicode')
        if args == ('oneks', 'list', 'clusters', '--json'):
            return json.dumps(([self.cluster] if self.cluster is not None else []) + self.extra_clusters)
        if args[:3] == ('oneks', 'show', 'cluster'):
            return json.dumps(self.cluster)
        if args[:3] == ('oneks', 'delete', 'cluster'):
            self.cluster = None
            return ''
        if args == ('onevm', 'list', '-x'):
            return '<VM_POOL>' + ''.join(self.vms) + '</VM_POOL>'
        if args[:2] == ('onevnet', 'delete'):
            self.assertEqual(args[2], '1')
            self.private = None
            return ''
        if args[:2] == ('onevnet', 'update'):
            self.assertEqual(args[2], '0')
            self.public.remove(self.public.find('TEMPLATE'))
            self.public.append(ET.fromstring(input))
            return ''
        raise AssertionError('Unexpected CLI invocation: ' + repr(args))

    def destructive(self):
        return [args for args, _ in self.events if 'delete' in args or 'update' in args]

    def test_cleanup_deletes_only_its_cluster_then_network_and_restores_dns(self):
        self.ns['cleanup']()
        self.assertEqual(self.destructive(), [('oneks', 'delete', 'cluster', '8'),
                         ('onevnet', 'delete', '1'), ('onevnet', 'update', '0')])
        self.assertEqual(self.public.findtext('TEMPLATE/DNS'), '8.8.8.8')
        self.assertEqual(self.public.findtext('TEMPLATE/CUSTOM'), 'preserved')
        self.assertFalse(self.marker.exists())

    def test_cleanup_removes_dns_when_the_original_attribute_was_absent(self):
        self.state['original_dns'] = None
        self.ns['save'](self.state)
        self.ns['cleanup']()
        self.assertIsNone(self.public.find('TEMPLATE/DNS'))

    def test_cleanup_without_browser_resources_restores_dns_without_deleting_others(self):
        self.cluster = self.private = None
        self.public.find('TEMPLATE/DNS').text = '8.8.8.8'
        self.ns['cleanup']()
        self.assertEqual(self.destructive(), [('onevnet', 'update', '0')])

    def test_foreign_marker_is_preserved_before_any_cli_access(self):
        self.state['workflow_id'] = 'other'
        self.ns['save'](self.state)
        with self.assertRaisesRegex(SystemExit, 'another invocation'):
            self.ns['cleanup']()
        self.assertEqual(self.events, [])
        self.assertTrue(self.marker.exists())

    def test_owner_and_deployment_changes_are_rejected_before_any_deletion(self):
        original = copy.deepcopy(self.cluster)
        for change in ('owner', 'private', 'public', 'placement'):
            with self.subTest(change=change):
                self.cluster = copy.deepcopy(original)
                self.events.clear()
                data = self.cluster['TEMPLATE']['CLUSTER_BODY']['deployment']
                if change == 'owner':
                    self.cluster['UID'] = '1'
                elif change == 'placement':
                    data['cluster']['id'] = 99
                else:
                    data['networks'][change]['id'] = 99
                with self.assertRaisesRegex(SystemExit, 'refusing cleanup'):
                    self.ns['cleanup']()
                self.assertEqual(self.destructive(), [])
                self.assertTrue(self.marker.exists())

    def test_private_network_identity_and_public_dns_changes_are_preserved(self):
        for kind in ('private', 'dns'):
            with self.subTest(kind=kind):
                self.private.find('UID').text = '1' if kind == 'private' else '0'
                self.public.find('TEMPLATE/DNS').text = '9.9.9.9' if kind == 'dns' else '1.1.1.1'
                with self.assertRaisesRegex(SystemExit, 'refusing'):
                    self.ns['cleanup']()
                self.assertEqual(self.destructive(), [])

    def test_ambiguous_or_preexisting_cluster_cannot_be_claimed(self):
        self.extra_clusters = [dict(self.cluster, ID='9')]
        with self.assertRaisesRegex(SystemExit, 'ambiguous'):
            self.ns['cleanup']()
        self.extra_clusters = []
        self.state['cluster_id'] = '8'
        self.state['previous_clusters'].append('8')
        self.ns['save'](self.state)
        with self.assertRaisesRegex(SystemExit, 'identity changed'):
            self.ns['cleanup']()
        self.assertEqual(self.destructive(), [])

    def test_leases_and_attached_vms_prevent_network_deletion(self):
        self.cluster = None
        self.private.find('USED_LEASES').text = '1'
        with self.assertRaisesRegex(SystemExit, 'leases or attached VMs'):
            self.ns['cleanup']()
        self.private.find('USED_LEASES').text = '0'
        self.vms = ['<VM><STATE>3</STATE><TEMPLATE><NIC><NETWORK_ID>1</NETWORK_ID></NIC></TEMPLATE></VM>']
        with self.assertRaisesRegex(SystemExit, 'leases or attached VMs'):
            self.ns['cleanup']()
        self.assertEqual(self.destructive(), [])
        self.assertTrue(self.marker.exists())

    def test_failed_deprovisioning_retains_marker_and_does_not_force_delete(self):
        self.cluster['TEMPLATE']['CLUSTER_BODY']['state'] = 'DEPROVISIONING'
        original = self.ns['cluster_document']
        calls = 0
        def changed(*args):
            nonlocal calls
            calls += 1
            result = original(*args)
            if calls > 1:
                result['TEMPLATE']['CLUSTER_BODY']['state'] = 'DEPROVISIONING_FAILURE'
            return result
        self.ns['cluster_document'] = changed
        with self.assertRaisesRegex(SystemExit, 'No forced deletion'):
            self.ns['cleanup']()
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.destructive(), [])

    def test_checkpoints_record_only_new_workflow_resources(self):
        for stage in ('private', 'dns', 'cluster'):
            self.ns['checkpoint'](stage)
        saved = json.loads(self.marker.read_text())
        self.assertEqual((saved['private_id'], saved['cluster_id']), ('1', '8'))
        self.assertEqual(self.marker.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.destructive(), [])

    def test_waits_require_real_running_states_and_fail_fast_on_provisioning_errors(self):
        self.ns['wait_for']('cluster', 1)
        self.cluster['TEMPLATE']['CLUSTER_BODY']['node_groups'] = [
            {'name': 'worker1', 'state': 'RUNNING', 'vms': ['3']}]
        self.ns['wait_for']('worker', 1)
        self.cluster['TEMPLATE']['CLUSTER_BODY']['state'] = 'BOOTSTRAPPING_FAILURE'
        with self.assertRaisesRegex(SystemExit, 'BOOTSTRAPPING_FAILURE'):
            self.ns['wait_for']('cluster', 1)
        self.cluster['TEMPLATE']['CLUSTER_BODY']['state'] = 'PENDING'
        with patch.object(self.ns['time'], 'monotonic', side_effect=[0, 10]):
            with self.assertRaisesRegex(SystemExit, 'Timed out'):
                self.ns['wait_for']('cluster', 1)

    def test_prepare_records_baseline_and_refuses_resource_name_collisions(self):
        self.marker.unlink()
        self.private = self.cluster = None
        actual_path = Path
        def paths(value):
            return Mock(read_text=lambda: 'MemTotal: 16777216 kB') if value == '/proc/meminfo' else actual_path(value)
        with patch.dict(self.ns, Path=paths), patch.object(self.ns['os'], 'cpu_count', return_value=4), \
             patch.object(self.ns['os'], 'access', return_value=True), \
             patch.object(self.ns['shutil'], 'disk_usage', return_value=SimpleNamespace(free=80 * 1024**3)), \
             patch.object(self.ns['subprocess'], 'run'):
            self.ns['prepare']()
            saved = json.loads(self.marker.read_text())
            self.assertEqual(saved['previous_networks'], ['0'])
            self.assertIsNone(saved['private_id'])
            self.marker.unlink()
            self.private = self.network('1', 'private-k8s')
            with self.assertRaisesRegex(SystemExit, 'refusing to reuse'):
                self.ns['prepare']()
            self.assertFalse(self.marker.exists())

    def test_insufficient_capacity_fails_before_service_or_resource_changes(self):
        self.marker.unlink()
        for memory, cpus in ((8 * 1024**2, 4), (16 * 1024**2, 2)):
            with self.subTest(memory=memory, cpus=cpus), \
                 patch.dict(self.ns, Path=Mock(return_value=Mock(read_text=lambda: f'MemTotal: {memory} kB'))), \
                 patch.object(self.ns['os'], 'cpu_count', return_value=cpus), \
                 patch.object(self.ns['subprocess'], 'run') as service:
                with self.assertRaisesRegex(SystemExit, '12 GiB RAM and 4 vCPUs') as error:
                    self.ns['prepare']()
                self.assertIn(f'guest reports {memory // 1024} MiB RAM and {cpus} vCPUs', str(error.exception))
                service.assert_not_called()
                self.assertEqual(self.events, [])
                self.assertFalse(self.marker.exists())

    def test_unknown_wait_stage_is_rejected_without_guest_access(self):
        with self.assertRaisesRegex(SystemExit, 'Unknown OneKS wait stage'):
            self.ns['wait_for']('typo', 100)
        self.assertEqual(self.events, [])

    def test_ready_api_is_not_restarted(self):
        with patch.object(self.ns['subprocess'], 'run') as service:
            self.assertEqual(self.ns['ensure_oneks_ready'](), [self.cluster])
            service.assert_not_called()

    def test_connection_refusal_is_recovered_with_restart_not_start(self):
        pool = Mock(side_effect=[SystemExit('Connection refused - localhost:10780'), []])
        with patch.dict(self.ns, clusters=pool), patch.object(self.ns['time'], 'sleep'), \
             patch.object(self.ns['subprocess'], 'run', return_value=SimpleNamespace(returncode=0)) as service:
            self.assertEqual(self.ns['ensure_oneks_ready'](), [])
        self.assertEqual(pool.call_count, 2)
        self.assertEqual(service.call_args.args[0], ['systemctl', 'restart', 'opennebula-ks'])
        self.assertTrue(service.call_args.kwargs['capture_output'])
        self.assertLessEqual(service.call_args.kwargs['timeout'], 30)

    def test_restarts_are_bounded_and_keep_the_last_systemd_diagnostic(self):
        elapsed = [0]
        def sleep(seconds):
            elapsed[0] += seconds
        pool = Mock(side_effect=SystemExit('Connection refused - localhost:10780'))
        with patch.dict(self.ns, clusters=pool), \
             patch.object(self.ns['time'], 'monotonic', side_effect=lambda: elapsed[0]), \
             patch.object(self.ns['time'], 'sleep', side_effect=sleep), \
             patch.object(self.ns['subprocess'], 'run', return_value=SimpleNamespace(
                 returncode=1, stderr='appliance is not ready', stdout='')) as service:
            with self.assertRaisesRegex(SystemExit, '300 seconds after 3 restart attempts') as error:
                self.ns['ensure_oneks_ready']()
        self.assertIn('appliance is not ready', str(error.exception))
        self.assertIn('journalctl -u opennebula-ks', str(error.exception))
        self.assertEqual(service.call_count, 3)
        self.assertEqual(elapsed[0], 300)
        self.assertEqual(self.destructive(), [])

    def test_authentication_and_malformed_json_errors_are_not_restarted(self):
        for error in (SystemExit('OneKS authentication failed'), json.JSONDecodeError('bad JSON', '', 0)):
            with self.subTest(error=type(error).__name__), patch.dict(self.ns, clusters=Mock(side_effect=error)), \
                 patch.object(self.ns['subprocess'], 'run') as service:
                with self.assertRaises(type(error)):
                    self.ns['ensure_oneks_ready']()
                service.assert_not_called()

    def test_slow_restart_does_not_abort_when_api_subsequently_becomes_ready(self):
        pool = Mock(side_effect=[SystemExit('ECONNREFUSED'), []])
        with patch.dict(self.ns, clusters=pool), patch.object(self.ns['time'], 'sleep'), \
             patch.object(self.ns['subprocess'], 'run', side_effect=self.ns['subprocess'].TimeoutExpired(
                 ['systemctl', 'restart', 'opennebula-ks'], 30)):
            self.assertEqual(self.ns['ensure_oneks_ready'](), [])


class ScreenshotMaskTests(unittest.TestCase):
    def test_masks_are_forwarded_for_all_screenshot_modes(self):
        for options in ({}, {'selector': 'body'}, {'selector': 'body', 'buffer': 4}, {'clip': {}}):
            with self.subTest(options=options):
                page, mask, target = Mock(), Mock(), Mock()
                mask.count.return_value = 1
                mask.first.is_visible.return_value = True
                target.first.bounding_box.return_value = dict(x=10, y=10, width=100, height=100)
                page.locator.side_effect = lambda selector: mask if selector == '#secret' else target
                options = dict(options, maskSelectors=['#secret'], maskColor='#123456')
                with patch.object(capture, '_clip_from_options', return_value=dict(x=0, y=0, width=100, height=100)
                                  if 'clip' in options else None):
                    capture._take_screenshot(page, options, Path('/tmp/masked.png'), {})
                screenshot = page.screenshot if not options.get('selector') or options.get('buffer') else target.first.screenshot
                self.assertEqual(screenshot.call_args.kwargs['mask'], [mask])
                self.assertEqual(screenshot.call_args.kwargs['mask_color'], '#123456')

    def test_missing_hidden_or_invalid_masks_refuse_unredacted_capture(self):
        for selectors, count, visible in (([], 1, True), ('#secret', 1, True), ([None], 1, True),
                                           (['#secret'], 0, True), (['#secret'], 1, False)):
            with self.subTest(selectors=selectors, count=count, visible=visible):
                page = Mock()
                page.locator.return_value.count.return_value = count
                page.locator.return_value.first.is_visible.return_value = visible
                with patch.object(capture, '_clip_from_options', return_value=None), self.assertRaises(capture.CaptureError):
                    capture._take_screenshot(page, {'maskSelectors': selectors}, Path('/tmp/no-secrets.png'), {})
                page.screenshot.assert_not_called()
