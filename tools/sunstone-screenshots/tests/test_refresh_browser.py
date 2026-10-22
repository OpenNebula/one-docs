import json
import os
from pathlib import Path
import unittest

from sunstone_screenshots.capture import _run_step


BASE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('SUNSTONE_SCREENSHOTS_BROWSER_TESTS') == '1',
                     'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 to run the Chromium regression test.')
class RefreshBrowserTests(unittest.TestCase):
    def test_vm_can_become_running_while_refresh_stays_disabled(self):
        from playwright.sync_api import sync_playwright

        recipe = json.loads((BASE / 'groups/getting-started/recipes/minione.json').read_text())
        steps = next(c['steps'] for c in recipe['captures'] if c['id'] == 'running')
        wait = next(step for step in steps if step['action'] == 'waitForSelector')
        html = """<!doctype html>
            <button data-cy="refresh" disabled>Refresh</button>
            <div data-cy="vms-0" hidden>docs-screenshot-alpine RUNNING</div>
            <script>
              setTimeout(() => { document.querySelector('div').hidden = false; }, 11000);
            </script>"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content(html)
                # The old helper failed at ten seconds, before the row became visible.
                self.assertIs(_run_step(page, dict(wait, timeout=15000), {}), page)
                self.assertTrue(page.locator(wait['selector']).is_visible())
                self.assertTrue(page.locator(wait['refreshSelector']).is_disabled())
            finally:
                browser.close()
