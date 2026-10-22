import json
import os
from pathlib import Path
import unittest

from sunstone_screenshots.capture import _run_step


BASE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('SUNSTONE_SCREENSHOTS_BROWSER_TESTS') == '1',
                     'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 to run the Chromium regression test.')
class ConsoleBrowserTests(unittest.TestCase):
    def test_drawer_overflow_hover_opens_vnc_tab_and_returns_to_logout(self):
        from playwright.sync_api import sync_playwright

        recipe = json.loads((BASE / 'groups/getting-started/recipes/alpine-console.json').read_text())
        html = (BASE / 'tests/fixtures/console-menu.html').read_text()
        console_html = '<canvas width="640" height="480"></canvas>'
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for viewport in ({'width': 1440, 'height': 1000}, {'width': 1280, 'height': 720}):
                    with self.subTest(viewport=viewport):
                        context = browser.new_context(viewport=viewport)
                        try:
                            context.set_default_timeout(3000)
                            context.route('http://sunstone.test/**', lambda route: route.fulfill(
                                content_type='text/html',
                                body=console_html if route.request.url.endswith('/vnc/17') else html))
                            original = page = context.new_page()
                            page.goto('http://sunstone.test/vm')
                            self.assertEqual(page.locator("[data-cy^='vms-'] [data-cy$='-vnc']").count(), 0)
                            for step in recipe['captures'][0]['steps']:
                                if step['action'] != 'waitTime':
                                    page = _run_step(page, step, {})
                            self.assertIsNot(page, original)
                            self.assertEqual(page.url, 'http://sunstone.test/vnc/17')
                            self.assertTrue(page.locator('canvas').is_visible())
                            self.assertEqual(len(context.pages), 2)
                            self.assertEqual(original.evaluate('window.consoleEvents'),
                                             ['drawer', 'overflow', 'console', 'vnc'])
                            for step in recipe['teardown']:
                                page = _run_step(page, step, {})
                            self.assertIs(page, original)
                            self.assertEqual(page.evaluate('window.consoleEvents.at(-1)'), 'logout')
                        finally:
                            context.close()
            finally:
                browser.close()
