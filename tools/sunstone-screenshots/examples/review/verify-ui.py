"""Check the local React review app and save desktop/mobile screenshots without nominating images."""

import argparse
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright, expect


def verify(url, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height, device in ((1440, 1000, 'desktop'), (390, 844, 'mobile')):
                page = browser.new_page(viewport=dict(width=width, height=height))
                failures = []
                page.on('pageerror', lambda error: failures.append(str(error)))
                page.goto(url)
                expect(page.get_by_role('heading', name='Documents', exact=True)).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Page overflow'
                page.screenshot(path=str(output / f'{device}-documents.png'), full_page=False)
                data = page.request.get(url + '/api/review').json()
                document = next(d for d in data['documents'] if any(data['comparisons'][i['id']]['can_substitute'] for i in d['images']))
                page.goto(url + '#/document/' + quote(document['id'], safe=''))
                expect(page.get_by_role('heading', name=document['title'], exact=True)).to_be_visible()
                row_index = next(i for i, row in enumerate(document['images']) if data['comparisons'][row['id']]['can_substitute'])
                row = page.locator('.image-row').nth(row_index)
                row.scroll_into_view_if_needed()
                for image in row.locator('img').all():
                    expect(image).to_have_js_property('complete', True)
                    assert image.evaluate('(image) => image.naturalWidth') > 0, 'Thumbnail did not render'
                page.screenshot(path=str(output / f'{device}-images.png'), full_page=False)
                row.get_by_role('button', name=f"Enlarge {document['images'][row_index]['title']}", exact=True).click()
                dialog = page.get_by_role('dialog')
                expect(dialog).to_be_visible()
                for image in dialog.locator('img').all():
                    expect(image).to_have_js_property('complete', True)
                    assert image.evaluate('(image) => image.naturalWidth') > 0, 'Full-size image did not render'
                assert dialog.locator('img').count() == 2, 'Both full-size images must render'
                assert page.evaluate("document.querySelector('dialog').getBoundingClientRect().right <= innerWidth"), 'Dialog overflow'
                page.screenshot(path=str(output / f'{device}-comparison.png'), full_page=False)
                dialog.get_by_role('button', name='Close comparison', exact=True).click()
                assert not failures, failures
                page.close()
        finally:
            browser.close()
    print(f'Desktop/mobile review verified. Screenshots: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8765')
    parser.add_argument('--output', default='.sunstone-screenshots/review-checks')
    args = parser.parse_args()
    verify(args.url.rstrip('/'), args.output)
