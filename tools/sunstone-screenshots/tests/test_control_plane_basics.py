import csv
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from sunstone_screenshots.docs_scan import scan_document
from sunstone_screenshots.manifest import screenshot_variants
from sunstone_screenshots.workflow import load_group
from sunstone_screenshots import cli


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'tools/sunstone-screenshots'
GROUP = BASE / 'groups/control-plane-basics'


class ControlPlaneBasicsTests(unittest.TestCase):
    def test_group_covers_document_screenshots_in_order_and_links_inventory(self):
        provision, paths, destroy = load_group(GROUP / 'group.json', ROOT)
        self.assertEqual(provision, BASE / 'groups/getting-started/provision.json')
        self.assertTrue(destroy)
        with (BASE / 'inventory.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        count = 0
        for path in paths:
            manifest = json.loads(path.read_text())
            doc = manifest['screenshots'][0]['doc']
            references = scan_document(ROOT, Path(doc))
            expected = [v.asset_path for r in references for v in r.variants
                        if not v.asset_path.endswith('.svg')]
            actual = [asset for shot in manifest['screenshots'] for _, asset in screenshot_variants(shot)]
            self.assertEqual(actual, expected)
            count += len(actual)
            row = next(r for r in rows if r['doc'] == doc)
            self.assertEqual(BASE / row['manifest'], path)
            self.assertEqual(row['automation_status'], 'draft')
            recipe = json.loads((path.parent / manifest['screenshots'][0]['recipe']).read_text())
            self.assertEqual([s['capture'] for s in manifest['screenshots']], [c['id'] for c in recipe['captures']])
            self.assertEqual(recipe['themeSteps']['dark'][0]['timeout'], 1000)
        self.assertEqual(count, 8)

    def test_labels_does_not_submit_or_apply_changes(self):
        recipe = json.loads((GROUP / 'recipes/labels.json').read_text())
        actions = [s for c in recipe['captures'] for s in c['steps']]
        self.assertFalse(any(s.get('dataCy') in ('label-create-accept', 'label-panel-apply') for s in actions))
        self.assertFalse(any(s['action'] == 'guestCommand' for s in actions))
        self.assertEqual(recipe['teardown'][-1]['selector'], "input[type='password']")

    def test_offline_preflight_never_provisions(self):
        with patch.object(cli.lab, 'provision') as provision:
            self.assertEqual(cli.main(['run-group', str(GROUP / 'group.json'),
                                       '--run-dir', '/tmp/control-plane-preflight-only', '--check']), 0)
        provision.assert_not_called()
