import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sunstone_screenshots.review import ReviewSession
from sunstone_screenshots.review_server import make_server, UI_DIRECTORY
from review_fixture import create_review_fixture


ENABLED = (os.environ.get('SUNSTONE_SCREENSHOTS_BROWSER_TESTS') == '1'
           and importlib.util.find_spec('skimage') is not None)


@unittest.skipUnless(ENABLED, 'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 and install review dependencies.')
class ReviewHTTPTests(unittest.TestCase):
    def setUp(self):
        if not (UI_DIRECTORY / 'index.html').exists():
            self.skipTest('Build review-ui first.')
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = create_review_fixture(self.root)
        self.session = ReviewSession(self.root, self.run, self.root / 'inventory.csv')
        self.server = make_server(self.session, port=0)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.stop_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join()

    def request(self, path, payload=None, headers=None):
        request = Request(self.url + path, headers=headers or {},
                          data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, response.read(), response.headers
        except HTTPError as response:
            return response.code, response.read(), response.headers

    def test_http_api_serves_only_registered_images_and_rejects_cross_origin_writes(self):
        status, body, _ = self.request('/api/review')
        self.assertEqual(status, 200)
        data = json.loads(body)
        item = next(i for i in data['comparisons'].values() if i['can_substitute'])
        payload = dict(id=item['id'], selected=True, baseline_sha256=item['baseline']['sha256'], candidate_sha256=item['candidate']['sha256'])
        self.assertEqual(self.request('/api/substitutions', payload, {'Content-Type': 'application/json'})[0], 403)
        headers = {'Content-Type': 'application/json', 'X-Review-Token': data['csrf_token']}
        self.assertEqual(self.request('/api/substitutions', payload, dict(headers, Origin='https://untrusted.example'))[0], 403)
        self.assertEqual(self.request('/api/review', headers={'Host': 'untrusted.example'})[0], 421)
        self.assertEqual(self.request('/api/substitutions', payload, headers)[0], 200)
        status, image, image_headers = self.request(f"/api/images/{item['id']}/baseline?thumbnail=1")
        self.assertEqual(status, 200)
        self.assertTrue(image.startswith(b'\x89PNG'))
        self.assertEqual(image_headers['Content-Type'], 'image/png')
        self.assertNotEqual(self.request('/api/images/unknown/baseline')[0], 200)
        self.assertNotEqual(self.request('/../inventory.csv')[0], 200)
        self.assertNotEqual(self.request('/state.json')[0], 200)
        status, exported, _ = self.request('/api/substitutions')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(exported)['selections'][0]['asset'], item['asset'])

    def test_cancelled_image_responses_do_not_attempt_an_error_response(self):
        handler = object.__new__(self.server.RequestHandlerClass)
        for error in (BrokenPipeError, ConnectionResetError):
            with self.subTest(error=error.__name__):
                handler.write_response = Mock(side_effect=error())
                handler.close_connection = False
                handler.send_bytes(200, b'png', 'image/png')
                handler.write_response.assert_called_once()
                self.assertTrue(handler.close_connection)


@unittest.skipUnless(ENABLED, 'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 and install review dependencies.')
class ReviewBrowserTests(ReviewHTTPTests):
    def test_desktop_master_detail_modal_selection_and_reload(self):
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(self.url)
                expect(page.get_by_role('heading', name='Documents', exact=True)).to_be_visible()
                expect(page.get_by_role('link', name='Sunstone first', exact=True)).to_be_visible()
                page.get_by_role('button', name='Failed', exact=True).click()
                expect(page.get_by_role('link', name='Sunstone second', exact=True)).to_be_visible()
                expect(page.get_by_role('link', name='Sunstone first', exact=True)).to_have_count(0)
                page.get_by_role('button', name='All', exact=True).click()
                page.get_by_role('link', name='Sunstone first', exact=True).click()
                expect(page.get_by_role('heading', name='Sunstone first', exact=True)).to_be_visible()
                expect(page.locator('.image-row')).to_have_count(3)
                for image in page.locator('.image-row').first.locator('img').all():
                    expect(image).to_have_js_property('complete', True)
                    self.assertGreater(image.evaluate('(image) => image.naturalWidth'), 0)
                row = page.locator('.image-row').first
                row.get_by_role('button', name='Substitute', exact=True).click()
                expect(row.get_by_role('button', name='Substitute selected')).to_have_attribute('aria-pressed', 'true')
                page.reload()
                expect(page.locator('.image-row').first.get_by_role('button', name='Substitute selected')).to_be_visible()
                page.locator('.image-row').first.get_by_role('button', name='Enlarge Sunstone same', exact=True).click()
                dialog = page.get_by_role('dialog')
                expect(dialog).to_be_visible()
                expect(dialog.get_by_role('button', name='Substitute selected')).to_be_visible()
                dialog.get_by_role('button', name='Next image', exact=True).click()
                expect(dialog.get_by_role('heading', name='Sunstone changed', exact=True)).to_be_visible()
                dialog.get_by_role('button', name='Zoom in', exact=True).click()
                expect(dialog.get_by_role('button', name='125%', exact=True)).to_be_visible()
                from PIL import Image
                Image.new('RGB', (96, 64), 'black').save(self.run / 'screenshots/assets/images/changed.png')
                dialog.get_by_role('button', name='Substitute', exact=True).click()
                expect(dialog.get_by_role('alert')).to_contain_text('contents changed')
                dialog.get_by_role('button', name='Refresh comparison', exact=True).click()
                expect(dialog.get_by_role('alert')).to_have_count(0)
                dialog.get_by_role('button', name='Close comparison', exact=True).click()
                expect(dialog).to_have_count(0)
                self.assertEqual(errors, [])
                self.assertEqual(len(json.loads(self.session.selection_file.read_text())['selections']), 1)
            finally:
                browser.close()

    def test_mobile_layout_and_missing_image_comparison(self):
        from playwright.sync_api import sync_playwright, expect
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
                page.goto(self.url)
                expect(page.get_by_role('heading', name='Documents', exact=True)).to_be_visible()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.get_by_role('link', name='Sunstone second', exact=True).click()
                expect(page.get_by_text('Workflow failed', exact=True)).to_be_visible()
                expect(page.get_by_text('Missing replacement', exact=True)).to_be_visible()
                expect(page.locator('.image-row').first.get_by_role('button', name='Substitute', exact=True)).to_be_disabled()
                page.locator('.image-row').first.get_by_role('button', name='Enlarge Sunstone missing-new', exact=True).click()
                dialog = page.get_by_role('dialog')
                expect(dialog).to_be_visible()
                expect(dialog.get_by_text('Missing replacement', exact=True)).to_be_visible()
                self.assertTrue(page.evaluate("document.querySelector('dialog').getBoundingClientRect().right <= innerWidth"))
                self.assertTrue(page.evaluate("document.querySelector('dialog').getBoundingClientRect().bottom <= innerHeight"))
                page.keyboard.press('Escape')
                expect(dialog).to_have_count(0)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
