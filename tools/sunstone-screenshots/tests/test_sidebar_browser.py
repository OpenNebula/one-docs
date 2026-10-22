import json
import os
from pathlib import Path
import unittest

from sunstone_screenshots.capture import _run_step


BASE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('SUNSTONE_SCREENSHOTS_BROWSER_TESTS') == '1',
                     'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 to run the Chromium regression test.')
class SidebarBrowserTests(unittest.TestCase):
    def test_recipe_expands_drawer_with_zero_sized_wrapper_and_hidden_copy(self):
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

        recipe = json.loads((BASE / 'groups/getting-started/recipes/minione.json').read_text())
        steps = next(c['steps'] for c in recipe['captures'] if c['id'] == 'network-menu')
        html = (BASE / 'tests/fixtures/sidebar.html').read_text()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for viewport in ({'width': 1440, 'height': 1000}, {'width': 1280, 'height': 720}):
                    with self.subTest(viewport=viewport):
                        page = browser.new_page(viewport=viewport)
                        try:
                            page.set_default_timeout(3000)
                            page.set_content(html)
                            wrapper = page.locator("[data-cy='sidebar']")
                            self.assertFalse(wrapper.is_visible())
                            with self.assertRaises(PlaywrightTimeoutError):
                                wrapper.hover(timeout=200)
                            self.assertEqual(page.locator("[data-cy='sidebar-paper']").count(), 2)
                            for step in steps:
                                page = _run_step(page, step, {})
                            self.assertTrue(page.locator("[data-cy='main-menu-item']:visible").is_visible())
                            self.assertEqual(page.locator('#drawer').bounding_box()['width'], 241)
                            _run_step(page, {'action': 'defocus'}, {})
                            self.assertFalse(page.locator("[data-cy='main-menu-item']:has-text('Virtual Networks')").is_visible())
                        finally:
                            page.close()
            finally:
                browser.close()

    def test_post_instantiation_redirect_does_not_close_active_instances_menu(self):
        from playwright.sync_api import sync_playwright

        recipe = json.loads((BASE / 'groups/getting-started/recipes/minione.json').read_text())
        steps = next(c['steps'] for c in recipe['captures'] if c['id'] == 'running')
        html = (BASE / 'tests/fixtures/sidebar.html').read_text()
        start_url = 'http://sunstone.test/fireedge/sunstone/vm-template/instantiate'
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for viewport in ({'width': 1440, 'height': 1000}, {'width': 1280, 'height': 720}):
                    with self.subTest(viewport=viewport):
                        page = browser.new_page(viewport=viewport)
                        try:
                            page.set_default_timeout(3000)
                            page.route('http://sunstone.test/**', lambda route: route.fulfill(content_type='text/html', body=html))
                            page.goto(start_url)
                            page.locator('#finish').click()
                            page.wait_for_url('**/vm')
                            _run_step(page, {'action': 'hover', 'selector': "[data-cy='sidebar-paper']:visible .sidebar-header"}, {})
                            self.assertTrue(page.locator('#vms-menu').is_visible())
                            _run_step(page, {'action': 'click', 'selector': "[data-cy='instances']:visible"}, {})
                            self.assertFalse(page.locator('#vms-menu').is_visible())

                            page.goto(start_url)
                            for step in steps:
                                page = _run_step(page, step, {})
                            self.assertTrue(page.url.endswith('/vm'))
                            self.assertTrue(page.locator("[data-cy='vms-1']:has-text('RUNNING')").is_visible())
                            self.assertEqual(page.locator('#drawer').get_attribute('data-instances-clicks'), '0')
                        finally:
                            page.close()
            finally:
                browser.close()
