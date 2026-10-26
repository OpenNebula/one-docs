import copy
import csv
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sunstone_screenshots.catalogue import build_catalogue
from sunstone_screenshots import cli
from sunstone_screenshots.docs_scan import scan_content, scan_document


EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/catalogue'


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        shutil.copytree(EXAMPLE, self.root)

    def build(self, filename='inventory.csv', **kwargs):
        with patch.object(cli.lab, 'connect', side_effect=AssertionError('Catalogue must be offline')), \
             patch.object(cli.lab, 'configuration', side_effect=AssertionError('Do not inspect runner credentials')):
            return build_catalogue(self.root / filename, self.root, **kwargs)

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data))

    def inventory(self, rows):
        with (self.root / 'inventory.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['id', 'title', 'source_page', 'doc', 'group', 'manifest', 'automation_status', 'section'])
            writer.writeheader()
            writer.writerows(rows)

    def codes(self, result):
        return {item['code'] for item in result['diagnostics']}

    def test_valid_example_traces_documents_to_shared_capture_assets_and_provision(self):
        result = self.build()
        self.assertTrue(result['valid'], result['diagnostics'])
        self.assertEqual(result['summary']['documents'], 3)
        self.assertEqual(result['summary']['manifests'], 2)
        self.assertEqual(result['summary']['recipes'], 1)
        self.assertEqual(result['summary']['assets'], 2)
        self.assertEqual(result['summary']['screenshots'], 2)
        first, second, pending = result['documents']
        self.assertEqual(first['id'], 'demo.first')
        self.assertEqual(first['manifests'], ['manifests/first.json'])
        self.assertEqual(first['group'], 'group.json')
        self.assertEqual(second['manifests'], ['manifests/second.json'])
        self.assertEqual([i['coverage'] for i in first['images']], ['mapped', 'mapped'])
        self.assertEqual(pending['images'][0]['coverage'], 'unmapped')
        self.assertIn('document.unmapped', self.codes(result))
        self.assertIn('image.unmapped', self.codes(result))
        source, consumer = result['screenshots']
        self.assertEqual(consumer['shared_from'], source['id'])
        self.assertEqual(source['recipe'], 'recipes/login.json')
        self.assertEqual(source['capture'], 'login')
        self.assertEqual(result['groups'][0]['provision'], 'provision.json')
        for asset in result['assets']:
            self.assertEqual(len(asset['sha256']), 64)
            self.assertEqual(asset['screenshots'], [source['id'], consumer['id']])
            self.assertIn(first['id'], asset['documents'])
            self.assertIn(second['id'], asset['documents'])

    def test_broken_example_reports_multiple_errors_and_still_exports_relationships(self):
        result = self.build('broken.csv')
        self.assertFalse(result['valid'])
        self.assertTrue({'manifest.invalid', 'capture.missing', 'recipe.invalid', 'document.missing',
                         'screenshot.not-referenced'}.issubset(self.codes(result)))
        self.assertEqual(len(result['documents']), 2)
        self.assertEqual(len(result['screenshots']), 2)

    def test_export_is_reproducible_portable_and_does_not_embed_commands_or_secrets(self):
        before = self.build()
        self.assertEqual(before, self.build())
        copied = self.root.parent / 'copy'
        shutil.copytree(self.root, copied)
        self.assertEqual(before, build_catalogue(copied / 'inventory.csv', copied))
        self.write('provision.json', {'password': 'never-export-this'})
        payload = json.dumps(self.build())
        self.assertNotIn('never-export-this', payload)
        self.assertNotIn('${SUNSTONE_URL}', payload)
        self.assertNotIn(str(self.root), payload)
        self.assertNotIn('setup', json.loads(payload)['recipes'][0])

    def test_broken_catalogue_is_also_portable(self):
        before = self.build('broken.csv')
        copied = self.root.parent / 'copy'
        shutil.copytree(self.root, copied)
        self.assertEqual(before, build_catalogue(copied / 'broken.csv', copied))
        self.assertNotIn(str(self.root), json.dumps(before))

    def test_missing_shared_source_diagnostics_do_not_include_checkout_paths(self):
        second = json.loads((self.root / 'manifests/second.json').read_text())
        second['screenshots'][0]['sharedFrom']['manifest'] = 'not-there.json'
        self.write('manifests/second.json', second)
        result = self.build()
        self.assertFalse(result['valid'])
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_missing_recipe_and_asset_and_malformed_json_do_not_crash(self):
        (self.root / 'recipes/login.json').write_text('{invalid')
        (self.root / 'assets/images/sunstone-dark.svg').unlink()
        result = self.build()
        self.assertFalse(result['valid'])
        self.assertIn('recipe.invalid', self.codes(result))
        self.assertIn('asset.missing', self.codes(result))
        (self.root / 'manifests/first.json').write_text('[]')
        self.assertFalse(self.build()['valid'])

    def test_duplicate_capture_and_document_id_are_errors(self):
        recipe = json.loads((self.root / 'recipes/login.json').read_text())
        recipe['captures'].append(copy.deepcopy(recipe['captures'][0]))
        self.write('recipes/login.json', recipe)
        with (self.root / 'inventory.csv').open('a') as stream:
            stream.write('demo.first,Duplicate,,content/first.md,,,pending,Examples\n')
        result = self.build()
        self.assertIn('recipe.duplicate-capture', self.codes(result))
        self.assertIn('document.duplicate', self.codes(result))

    def test_deleted_doc_still_has_traceable_manifest_and_screenshot_nodes(self):
        (self.root / 'content/first.md').unlink()
        result = self.build()
        self.assertIn('document.missing', self.codes(result))
        self.assertEqual(result['documents'][0]['manifests'], ['manifests/first.json'])
        self.assertEqual(result['screenshots'][0]['document'], 'demo.first')

    def test_stale_mapping_after_markdown_change_is_an_error(self):
        (self.root / 'content/first.md').write_text('# No images left\n')
        result = self.build()
        errors = [d for d in result['diagnostics'] if d['code'] == 'screenshot.not-referenced']
        self.assertEqual(len(errors), 2)

    def test_explicit_deferred_images_are_not_reported_as_unmapped(self):
        manifest = json.loads((self.root / 'manifests/first.json').read_text())
        manifest['screenshots'] = []
        manifest['deferredScreenshots'] = [{'image': f'assets/images/sunstone-{theme}.svg', 'reason': 'GPU required'}
                                           for theme in ('light', 'dark')]
        self.write('manifests/first.json', manifest)
        self.inventory([dict(id='demo.first', title='First', doc='content/first.md', manifest='manifests/first.json')])
        result = self.build()
        self.assertTrue(result['valid'], result['diagnostics'])
        self.assertEqual([i['coverage'] for i in result['documents'][0]['images']], ['deferred', 'deferred'])
        self.assertEqual(result['documents'][0]['images'][0]['deferred_reason'], 'GPU required')

    def test_disabled_capture_is_not_counted_as_automated_coverage(self):
        first = json.loads((self.root / 'manifests/first.json').read_text())
        first['screenshots'][0]['status'] = 'disabled'
        self.write('manifests/first.json', first)
        result = self.build()
        self.assertEqual(result['documents'][0]['images'][0]['coverage'], 'disabled')
        self.assertFalse(result['valid'])  # Shared consumers cannot use disabled producers.

    def test_shared_source_mismatch_and_accidental_duplicate_producers_are_errors(self):
        second = json.loads((self.root / 'manifests/second.json').read_text())
        second['screenshots'][0]['capture'] = 'navigation-only'
        self.write('manifests/second.json', second)
        self.assertFalse(self.build()['valid'])
        del second['screenshots'][0]['sharedFrom']
        self.write('manifests/second.json', second)
        self.assertIn('asset.multiple-producers', self.codes(self.build()))

    def test_shared_producer_must_precede_consumer_in_the_same_group(self):
        self.write('group.json', {'version': 1, 'provision': 'provision.json',
                                 'manifests': ['manifests/second.json', 'manifests/first.json']})
        self.assertIn('shared-source.order', self.codes(self.build()))
        self.write('other-group.json', {'version': 1, 'provision': 'provision.json', 'manifests': ['manifests/first.json']})
        first = json.loads((self.root / 'manifests/first.json').read_text())
        first['group'] = '../other-group.json'
        self.write('manifests/first.json', first)
        self.assertIn('shared-source.group-mismatch', self.codes(self.build()))

    def test_shared_cycle_is_reported_without_recursing_forever(self):
        first = json.loads((self.root / 'manifests/first.json').read_text())
        first['screenshots'][0]['sharedFrom'] = {'manifest': 'second.json', 'id': 'second.login'}
        self.write('manifests/first.json', first)
        self.assertFalse(self.build()['valid'])

    def test_inventory_group_mismatch_and_missing_group_membership_are_errors(self):
        self.write('other-group.json', {'version': 1, 'provision': 'provision.json', 'manifests': ['manifests/first.json']})
        self.inventory([dict(id='demo.first', title='First', doc='content/first.md', group='other-group.json',
                             manifest='manifests/first.json')])
        self.assertIn('group.mismatch', self.codes(self.build()))
        self.write('group.json', {'version': 1, 'provision': 'provision.json', 'manifests': ['manifests/second.json']})
        self.assertIn('group.missing-membership', self.codes(self.build()))

    def test_manifest_for_wrong_inventory_document_is_reported(self):
        self.inventory([dict(id='wrong', title='Wrong', doc='content/second.md', manifest='manifests/first.json')])
        result = self.build()
        self.assertIn('manifest.document-mismatch', self.codes(result))
        self.assertIn('document.dependency', self.codes(result))

    def test_unresolved_and_external_rows_remain_visible_without_failing(self):
        self.inventory([dict(id='unknown', title='Unknown', automation_status='needs-path'),
                        dict(id='external', title='External', source_page='https://example.test', automation_status='external')])
        result = self.build()
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['documents']), 2)
        self.assertEqual(result['documents'][0]['manifests'], [])

    def test_discovery_is_opt_in_and_never_rewrites_inventory(self):
        inventory = self.root / 'inventory.csv'
        original = inventory.read_bytes()
        (self.root / 'content/new.md').write_text('# New Sunstone page\n![Sunstone](/images/sunstone-light.svg)\n')
        self.assertEqual(len(self.build()['documents']), 3)
        result = self.build(discover=True)
        self.assertEqual(len(result['documents']), 4)
        self.assertIn('document.untracked', self.codes(result))
        self.assertEqual(inventory.read_bytes(), original)

    def test_recipe_only_navigation_stages_are_preserved_without_fake_screenshots(self):
        recipe = self.build()['recipes'][0]
        self.assertEqual(recipe['captures'][1], dict(id='navigation-only', step_count=1, screenshots=[]))

    def test_single_document_scan_matches_existing_content_scanner(self):
        all_refs = scan_content(self.root, Path('content'))
        self.assertEqual(scan_document(self.root, Path('content/first.md')), [r for r in all_refs if r.doc == 'content/first.md'])

    def test_invalid_csv_shape_is_reported(self):
        with (self.root / 'inventory.csv').open('a') as stream:
            stream.write('too,few,columns\n')
        self.assertIn('inventory.invalid-row', self.codes(self.build()))

    def test_absolute_and_outside_repository_paths_are_rejected(self):
        for doc in ('../outside.md', str(self.root.parent / 'outside.md')):
            with self.subTest(doc=doc):
                self.inventory([dict(id='unsafe', title='Unsafe', doc=doc)])
                result = self.build()
                self.assertFalse(result['valid'])
                self.assertTrue({'path.invalid', 'path.outside-repository'} & self.codes(result))

    def test_manifest_paths_are_checked_before_opening_recipes_or_hook_scripts(self):
        outside = self.root.parent / 'outside.json'
        outside.write_text('{"private":"do not read"}')
        first = json.loads((self.root / 'manifests/first.json').read_text())
        first['screenshots'][0]['recipe'] = '../../outside.json'
        first['hooks'] = {'setup': [{'script': '../../outside.json'}]}
        self.write('manifests/first.json', first)
        original = Path.read_text
        def read_text(path, *args, **kwargs):
            self.assertNotEqual(path.resolve(), outside)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read_text):
            self.assertIn('path.outside-repository', self.codes(self.build()))

    def test_symlinks_cannot_read_metadata_outside_the_repository(self):
        outside = self.root.parent / 'private.json'
        outside.write_text('{"password":"not-for-export"}')
        (self.root / 'provision.json').unlink()
        (self.root / 'provision.json').symlink_to(outside)
        result = self.build()
        self.assertIn('path.outside-repository', self.codes(result))
        self.assertNotIn('not-for-export', json.dumps(result))

    def test_cli_exports_json_even_when_invalid_and_has_meaningful_exit_codes(self):
        for filename, exit_code in (('inventory.csv', 0), ('broken.csv', 1)):
            with self.subTest(filename=filename):
                stdout, stderr = StringIO(), StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = cli.main(['--repo-root', str(self.root), 'catalogue', str(self.root / filename)])
                self.assertEqual(result, exit_code)
                self.assertEqual(json.loads(stdout.getvalue())['valid'], exit_code == 0)
                if exit_code:
                    self.assertIn('error:', stderr.getvalue())

    def test_cli_check_and_file_output_are_offline(self):
        for options in (['--check'], ['--output', str(self.root / 'generated/catalogue.json')]):
            stdout = StringIO()
            with redirect_stdout(stdout), redirect_stderr(StringIO()), patch.object(cli.lab, 'provision') as provision:
                result = cli.main(['--repo-root', str(self.root), 'catalogue', str(self.root / 'inventory.csv'), *options])
            self.assertEqual(result, 0)
            provision.assert_not_called()
            if '--check' in options:
                self.assertIn('Catalogue OK', stdout.getvalue())
                self.assertIn('no infrastructure contacted', stdout.getvalue())
            else:
                self.assertTrue(json.loads((self.root / 'generated/catalogue.json').read_text())['valid'])

    def test_export_cannot_overwrite_its_catalogue_sources(self):
        for name in ('inventory.csv', 'content/first.md', 'manifests/first.json', 'recipes/login.json',
                     'group.json', 'provision.json', 'assets/images/sunstone-light.svg'):
            with self.subTest(name=name):
                target = self.root / name
                original = target.read_bytes()
                stderr = StringIO()
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    result = cli.main(['--repo-root', str(self.root), 'catalogue', str(self.root / 'inventory.csv'),
                                       '--output', str(target)])
                self.assertEqual(result, 1)
                self.assertIn('Refusing to overwrite', stderr.getvalue())
                self.assertEqual(target.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
