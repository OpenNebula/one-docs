import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sunstone_screenshots.capture import _take_screenshot, CaptureError


@unittest.skipUnless(os.environ.get('SUNSTONE_SCREENSHOTS_BROWSER_TESTS') == '1'
                     and importlib.util.find_spec('PIL') is not None,
                     'Set SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 and install Pillow to run the Chromium mask test.')
class MaskBrowserTests(unittest.TestCase):
    def test_native_mask_redacts_pixels_without_modifying_the_live_page(self):
        from PIL import Image
        from playwright.sync_api import sync_playwright
        with TemporaryDirectory() as tmp, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 240, 'height': 140})
                page.set_content('<style>body{margin:0}#capture{width:200px;height:100px}'
                                 '#secret{position:absolute;left:20px;top:20px;width:140px;'
                                 'height:30px;background:red}</style><div id="capture">'
                                 '<div id="secret">PRIVATE CREDENTIAL</div></div>')
                for index, options in enumerate(({}, {'selector': '#capture'},
                                                {'selector': '#capture', 'buffer': 5},
                                                {'clip': {'leftPercent': 0, 'rightPercent': 100,
                                                          'topPercent': 0, 'bottomPercent': 80}})):
                    target = Path(tmp) / f'{index}.png'
                    _take_screenshot(page, dict(options, maskSelectors=['#secret']), target, {})
                    with Image.open(target) as image:
                        self.assertEqual(image.convert('RGB').getpixel((25, 25)), (220, 229, 231))
                    self.assertEqual(page.locator('#secret').inner_text(), 'PRIVATE CREDENTIAL')
                target = Path(tmp) / 'refused.png'
                with self.assertRaisesRegex(CaptureError, 'refusing an unredacted'):
                    _take_screenshot(page, {'maskSelectors': ['#missing']}, target, {})
                self.assertFalse(target.exists())
            finally:
                browser.close()
