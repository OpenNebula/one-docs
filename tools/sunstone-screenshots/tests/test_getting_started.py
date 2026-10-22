import csv
import json
import os
from pathlib import Path
import shlex
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from sunstone_screenshots.docs_scan import scan_content
from sunstone_screenshots.manifest import screenshot_variants
from sunstone_screenshots.workflow import load_group


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'tools/sunstone-screenshots'
GROUP = BASE / 'groups/getting-started'


class GettingStartedManifestTests(unittest.TestCase):
    def test_first_four_inventory_rows_map_to_their_own_page_manifests(self):
        with (BASE / 'inventory.csv').open() as stream:
            rows = list(csv.DictReader(stream))[:4]
        config, paths, destroy = load_group(GROUP / 'group.json', ROOT)
        self.assertEqual(config, GROUP / 'provision.json')
        self.assertTrue(destroy)
        self.assertEqual(paths, [(BASE / row['manifest']).resolve() for row in rows])
        for row, path, count in zip(rows, paths, (9, 9, 4, 22)):
            manifest = json.loads(path.read_text())
            self.assertEqual({s['doc'] for s in manifest['screenshots']}, {row['doc']})
            self.assertEqual(len(manifest['screenshots']), count)
            self.assertEqual(row['automation_status'], 'draft')

    def test_all_page_sunstone_images_are_captured_shared_or_explicitly_deferred(self):
        _, paths, _ = load_group(GROUP / 'group.json', ROOT)
        references = scan_content(ROOT, Path('content/getting_started/try_opennebula/opennebula_sandbox_deployment'))
        excluded = {
            'assets/images/ISO/00-onepoc_architecture.svg',
            'assets/images/ISO/0-uefi_boot_screen.png', 'assets/images/ISO/0-mbr_boot_screen.png',
            'assets/images/ISO/01-validation_script.png', 'assets/images/ISO/011-disk_selection.png',
            'assets/images/ISO/02-anaconda_unattended_install.png',
            'assets/images/icons/sunstone/import_into_datastore.png',
            'assets/images/icons/sunstone/instantiate.png', 'assets/images/wordpress_install_page.png',
        }
        for path in paths:
            manifest = json.loads(path.read_text())
            doc = manifest['screenshots'][0]['doc']
            expected = {v.asset_path for r in references if r.doc == doc for v in r.variants
                        if v.asset_path not in excluded and '/minione_aws_' not in v.asset_path}
            mapped = {image for s in manifest['screenshots'] for _, image in screenshot_variants(s)}
            deferred = {s['image'] for s in manifest.get('deferredScreenshots', [])}
            self.assertFalse(mapped & deferred)
            self.assertEqual(mapped | deferred, expected, path.name)

    def test_recipe_capture_order_matches_the_manifest_and_actions_are_supported(self):
        _, paths, _ = load_group(GROUP / 'group.json', ROOT)
        actions = {'goto', 'fill', 'click', 'hover', 'defocus', 'press', 'waitForSelector', 'waitForURL',
                   'waitTime', 'evaluate', 'switchToPage', 'guestCommand'}
        for path in paths:
            manifest = json.loads(path.read_text())
            recipes = {s['recipe'] for s in manifest['screenshots'] if not s.get('sharedFrom')}
            for name in recipes:
                recipe = json.loads((path.parent / name).read_text())
                ids = [c['id'] for c in recipe['captures']]
                self.assertEqual(len(ids), len(set(ids)))
                expected = [s['capture'] for s in manifest['screenshots'] if s['recipe'] == name]
                self.assertEqual([capture_id for capture_id in ids if capture_id in expected], expected)
                for capture in recipe['captures']:
                    if capture['id'] not in expected:
                        self.assertNotIn('screenshot', capture)
                for step in recipe.get('setup', []) + recipe.get('teardown', []) + [s for c in recipe['captures'] for s in c['steps']]:
                    self.assertIn(step['action'], actions)

    def test_iso_never_submits_the_network_form(self):
        recipe = json.loads((GROUP / 'recipes/iso-network.json').read_text())
        steps = recipe['setup'] + recipe['teardown'] + [s for c in recipe['captures'] for s in c['steps']]
        self.assertFalse(any(s['action'] == 'click' and 'Finish' in s.get('selector', '') for s in steps))
        self.assertFalse(any(s['action'] == 'guestCommand' for s in steps))

    def test_wordpress_visits_security_groups_between_network_and_values(self):
        recipe = json.loads((GROUP / 'recipes/wordpress.json').read_text())
        ids = [capture['id'] for capture in recipe['captures']]
        index = ids.index('nic-network')
        self.assertEqual(ids[index:index + 3], ['nic-network', 'nic-security-groups', 'nic-values'])
        security_groups, values = recipe['captures'][index + 1:index + 3]
        next_button = {'action': 'click', 'selector': "[data-cy='modal-attach-nic'] [data-cy='stepper-next-button']"}
        self.assertEqual(security_groups['steps'], [next_button, {
            'action': 'waitForSelector', 'selector': "[data-cy='modal-attach-nic'] [data-cy='security-groups']"},
            {'action': 'defocus'}])
        self.assertNotIn('screenshot', security_groups)
        self.assertEqual(values['steps'], [next_button, {
            'action': 'waitForSelector', 'selector': "[data-cy='modal-attach-nic'] input[name='network-values.IP']"},
            {'action': 'defocus'}])

    def test_vnc_recipe_switches_back_before_logout(self):
        recipe = json.loads((GROUP / 'recipes/alpine-console.json').read_text())
        self.assertTrue(any(s.get('opensPage') for s in recipe['captures'][0]['steps']))
        self.assertEqual(recipe['teardown'][0], {'action': 'switchToPage', 'target': 'first'})

    def test_vnc_recipe_opens_the_drawer_then_the_nested_console_menu(self):
        recipe = json.loads((GROUP / 'recipes/alpine-console.json').read_text())
        steps = recipe['captures'][0]['steps']
        row = next(i for i, step in enumerate(steps)
                   if step['action'] == 'click' and "[data-cy^='vms-']" in step.get('selector', ''))
        self.assertNotIn('vnc', steps[row]['selector'])
        self.assertEqual(steps[row + 1]['action'], 'waitForSelector')
        self.assertIn("[data-cy='vm-info-title']", steps[row + 1]['selector'])
        self.assertEqual(steps[row + 2], {
            'action': 'click', 'selector': "[data-cy='compact-toolbar-overflow']:visible"})
        self.assertEqual(steps[row + 3]['action'], 'hover')
        self.assertIn(":text-is('Console')", steps[row + 3]['selector'])
        self.assertEqual(steps[row + 4], {
            'action': 'click', 'selector': "[data-cy$='-vnc']:visible", 'opensPage': True})
        self.assertEqual([step for step in steps if step.get('opensPage')], [steps[row + 4]])
        self.assertEqual(steps[row + 5]['selector'], 'canvas')

    def test_sidebar_hovers_target_the_visible_drawer_header(self):
        found = 0
        for path in (GROUP / 'recipes').glob('*.json'):
            recipe = json.loads(path.read_text())
            steps = recipe.get('setup', []) + recipe.get('teardown', []) + [s for c in recipe['captures'] for s in c['steps']]
            for step in steps:
                if step.get('action') == 'hover' and 'sidebar' in step.get('selector', ''):
                    found += 1
                    self.assertEqual(step['selector'], "[data-cy='sidebar-paper']:visible .sidebar-header", path.name)
        self.assertGreater(found, 0)

    def test_post_instantiation_captures_use_the_redirect_not_the_menu_toggle(self):
        for name in ('minione.json', 'wordpress.json'):
            with self.subTest(recipe=name):
                recipe = json.loads((GROUP / 'recipes' / name).read_text())
                steps = next(c['steps'] for c in recipe['captures'] if c['id'] == 'running')
                finish = next(i for i, step in enumerate(steps)
                              if step.get('selector') == "button[data-cy='stepper-next-button']:has-text('Finish')")
                self.assertEqual(steps[finish + 1], {'action': 'waitForURL', 'url': '**/vm', 'timeout': 60000})
                self.assertFalse(any('instances' in step.get('selector', '') or 'main-menu-item' in step.get('selector', '')
                                     for step in steps[finish + 1:]))
                self.assertTrue(any(step['action'] == 'waitForSelector' and 'RUNNING' in step.get('selector', '')
                                    for step in steps[finish + 1:]))


class GettingStartedGuestScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.marker = Path(self.temp.name) / 'marker.json'

    def execute(self, filename, output=(), run_effect=None):
        code = (GROUP / 'scripts' / filename).read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        original_path = type(self.marker)
        def path(value):
            return self.marker if str(value).startswith('/root/screenshot-lab/') else original_path(value)
        with patch('pathlib.Path', side_effect=path), patch('subprocess.check_output', side_effect=output) as commands, \
             patch('subprocess.run', side_effect=run_effect) as run, patch('time.sleep'), \
             patch.dict(os.environ, {'SUNSTONE_WORKFLOW_ID': 'current'}):
            self.commands = commands
            self.run = run
            exec(compile(code, filename, 'exec'), {})
        return commands, run

    def record(self, kind, resource_id, name=None, uid='0', state='3'):
        tag = {'vms': 'VM', 'templates': 'VMTEMPLATE', 'images': 'IMAGE'}[kind]
        name = name or ('docs-screenshot-wordpress' if kind == 'vms' else 'Service WordPress - KVM')
        content = f'<ID>{resource_id}</ID><NAME>{name}</NAME><UID>{uid}</UID><STATE>{state}</STATE>'
        if kind == 'vms':
            content += '<TEMPLATE><TEMPLATE_ID>8</TEMPLATE_ID></TEMPLATE>'
        elif kind == 'templates':
            content += '<TEMPLATE><DISK><IMAGE_ID>9</IMAGE_ID></DISK></TEMPLATE>'
        return f'<{tag}>{content}</{tag}>'

    def pool(self, *records):
        return '<POOL>' + ''.join(records) + '</POOL>'

    def marker_data(self, **changes):
        state = {'workflow_id': 'current', 'names': {'vms': 'docs-screenshot-wordpress',
                 'templates': 'Service WordPress - KVM', 'images': 'Service WordPress - KVM'},
                 'previous_ids': {'vms': ['1'], 'templates': ['1'], 'images': ['1']}}
        state.update(changes)
        self.marker.write_text(json.dumps(state))

    def cleanup_results(self, vm=None, template=None, image=None):
        records = [vm or self.record('vms', 7), template or self.record('templates', 8), image or self.record('images', 9)]
        return [value for record in records for value in (self.pool(record), record)]

    def test_prepare_records_previous_ids_and_refuses_existing_resources(self):
        self.execute('prepare-wordpress.sh', [self.pool(self.record('vms', 1, name='other')), self.pool(), self.pool()])
        state = json.loads(self.marker.read_text())
        self.assertEqual(state['previous_ids'], {'vms': ['1'], 'templates': [], 'images': []})
        self.assertEqual(self.marker.stat().st_mode & 0o777, 0o600)
        self.marker.unlink()
        with self.assertRaisesRegex(SystemExit, 'already exist'):
            self.execute('prepare-wordpress.sh', [self.pool(), self.pool(self.record('templates', 1)), self.pool()])
        self.assertFalse(self.marker.exists())

    def test_cleanup_terminates_vm_before_deleting_its_template_and_image(self):
        self.marker_data()
        results = self.cleanup_results() + ['', self.record('vms', 7, state='6'), '', self.pool(self.record('images', 9)), '',
                                          self.pool(self.record('images', 1, name='unrelated'))]
        commands, _ = self.execute('cleanup-wordpress.sh', results)
        destructive = [c.args[0][-1] for c in commands.call_args_list if 'delete ' in c.args[0][-1] or 'terminate ' in c.args[0][-1]]
        self.assertEqual(destructive, ['onevm terminate --hard 7', 'onetemplate delete 8', 'oneimage delete 9'])
        self.assertFalse(self.marker.exists())

    def test_cleanup_refuses_changed_owner_or_dependency_before_any_deletion(self):
        cases = [self.cleanup_results(vm=self.record('vms', 7, uid='1')),
                 self.cleanup_results(vm=self.record('vms', 7).replace('<TEMPLATE_ID>8', '<TEMPLATE_ID>99')),
                 self.cleanup_results(template=self.record('templates', 8).replace('<IMAGE_ID>9', '<IMAGE_ID>1'))]
        for results in cases:
            with self.subTest(results=results):
                self.marker_data()
                with self.assertRaisesRegex(SystemExit, 'refusing cleanup'):
                    self.execute('cleanup-wordpress.sh', results)
                self.assertFalse(any('delete ' in c.args[0][-1] or 'terminate ' in c.args[0][-1]
                                     for c in self.commands.call_args_list))
                self.assertTrue(self.marker.exists())

    def test_cleanup_never_touches_preexisting_or_foreign_resources(self):
        self.marker_data()
        commands, _ = self.execute('cleanup-wordpress.sh', [self.pool(self.record('vms', 1)),
                        self.pool(self.record('templates', 1)), self.pool(self.record('images', 1))])
        self.assertTrue(all(' list -x' in call.args[0][-1] for call in commands.call_args_list))
        self.assertFalse(self.marker.exists())
        self.marker_data(workflow_id='other')
        with self.assertRaises(SystemExit) as result:
            self.execute('cleanup-wordpress.sh')
        self.assertEqual(result.exception.code, 0)
        self.assertTrue(self.marker.exists())

    def test_partial_import_can_remove_only_its_new_image(self):
        self.marker_data()
        image = self.record('images', 9)
        commands, _ = self.execute('cleanup-wordpress.sh', [self.pool(), self.pool(), self.pool(image), image,
                                                          self.pool(image), '', self.pool()])
        self.assertEqual([c.args[0][-1] for c in commands.call_args_list], [
            'onevm list -x', 'onetemplate list -x', 'oneimage list -x', 'oneimage show 9 -x',
            'oneimage list -x', 'oneimage delete 9', 'oneimage list -x'])

    def test_cleanup_waits_for_import_before_deleting_image_without_force(self):
        self.marker_data()
        locked = self.record('images', 9, state='4')
        ready = self.record('images', 9, state='1')
        deleting = self.record('images', 9, state='7')
        results = [self.pool(), self.pool(), self.pool(locked), locked,
                   self.pool(locked), self.pool(ready), '', self.pool(deleting), self.pool()]
        commands, _ = self.execute('cleanup-wordpress.sh', results)
        self.assertEqual([c.args[0][-1] for c in commands.call_args_list], [
            'onevm list -x', 'onetemplate list -x', 'oneimage list -x', 'oneimage show 9 -x',
            'oneimage list -x', 'oneimage list -x', 'oneimage delete 9', 'oneimage list -x', 'oneimage list -x'])
        self.assertFalse(self.marker.exists())

    def test_cleanup_keeps_marker_when_image_stays_locked(self):
        self.marker_data()
        locked = self.record('images', 9, state='4')
        with patch('time.monotonic', side_effect=[0, 121]):
            with self.assertRaisesRegex(SystemExit, r'image 9 cleanup \(STATE=4\).*Marker retained'):
                self.execute('cleanup-wordpress.sh', [self.pool(), self.pool(), self.pool(locked), locked,
                                                      self.pool(locked)])
        self.assertFalse(any('delete ' in c.args[0][-1] for c in self.commands.call_args_list))
        self.assertTrue(self.marker.exists())

    def test_cleanup_refuses_an_image_identity_change_while_waiting(self):
        for changes in ({'uid': '1'}, {'name': 'unrelated'}):
            with self.subTest(changes=changes):
                self.marker_data()
                locked = self.record('images', 9, state='4')
                changed = self.record('images', 9, state='1', **changes)
                with self.assertRaisesRegex(SystemExit, 'image identity changed while waiting'):
                    self.execute('cleanup-wordpress.sh', [self.pool(), self.pool(), self.pool(locked), locked,
                                                          self.pool(locked), self.pool(changed)])
                self.assertFalse(any('delete ' in c.args[0][-1] for c in self.commands.call_args_list))
                self.assertTrue(self.marker.exists())

    def test_cleanup_waits_for_an_already_deleting_image_without_deleting_twice(self):
        self.marker_data()
        deleting = self.record('images', 9, state='7')
        commands, _ = self.execute('cleanup-wordpress.sh', [self.pool(), self.pool(), self.pool(deleting), deleting,
                                                          self.pool(deleting), self.pool()])
        self.assertFalse(any('delete ' in c.args[0][-1] for c in commands.call_args_list))
        self.assertFalse(self.marker.exists())

    def test_theme_setup_preserves_other_settings_and_teardown_restores_them(self):
        user = '<USER><ID>0</ID><TEMPLATE><FIREEDGE><SCHEME>light</SCHEME><LANG>en_US</LANG></FIREEDGE><OTHER>value</OTHER></TEMPLATE></USER>'
        updates = []
        def update(command, **kwargs):
            self.assertEqual(command[:4], ['su', '-', 'oneadmin', '-c'])
            inner = shlex.split(command[-1])
            # A fourth argument would trigger file validation instead of stdin.
            self.assertEqual(inner, ['oneuser', 'update', '0'])
            self.assertTrue(kwargs['check'])
            self.assertTrue(kwargs['text'])
            updates.append(kwargs['input'])

        self.execute('prepare-theme.sh', [user], run_effect=update)
        changed = ET.fromstring(updates[0])
        self.assertEqual(changed.findtext('FIREEDGE/SCHEME'), 'system')
        self.assertEqual(changed.findtext('FIREEDGE/LANG'), 'en_US')
        self.assertEqual(changed.findtext('OTHER'), 'value')
        original = json.loads(self.marker.read_text())['template']
        self.execute('restore-theme.sh', run_effect=update)
        self.assertEqual(updates[1], original)
        self.assertFalse(self.marker.exists())

    def test_theme_marker_is_retained_on_cli_failure(self):
        user = '<USER><ID>0</ID><TEMPLATE><FIREEDGE><SCHEME>light</SCHEME></FIREEDGE></TEMPLATE></USER>'
        for script in ('prepare-theme.sh', 'restore-theme.sh'):
            with self.subTest(script=script):
                if self.marker.exists():
                    self.marker.unlink()
                if script == 'restore-theme.sh':
                    self.marker.write_text(json.dumps({'workflow_id': 'current', 'template': '<TEMPLATE />'}))
                def fail(command, **kwargs):
                    self.assertEqual(shlex.split(command[-1]), ['oneuser', 'update', '0'])
                    self.assertIsInstance(kwargs['input'], str)
                    raise subprocess.CalledProcessError(255, command)
                with self.assertRaises(subprocess.CalledProcessError):
                    self.execute(script, [user], run_effect=fail)
                self.assertTrue(self.marker.exists())

    def test_theme_restore_preserves_another_invocations_marker(self):
        self.marker.write_text(json.dumps({'workflow_id': 'other', 'template': '<TEMPLATE />'}))
        with self.assertRaises(SystemExit) as result:
            self.execute('restore-theme.sh')
        self.assertEqual(result.exception.code, 0)
        self.assertTrue(self.marker.exists())
        self.run.assert_not_called()
