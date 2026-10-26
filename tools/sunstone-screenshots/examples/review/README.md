# Browser Review Example

Build the review UI and install `requirements-review.txt` as described in the main
README. The generator copies existing Sunstone screenshots into a fresh ignored
directory. It does not provision anything, edit source images or run recipes.

```bash
python3 tools/sunstone-screenshots/examples/review/create-demo.py
```

Run the `review` command printed by the generator using the Python environment
where the review dependencies are installed. It opens a loopback-only server and
the browser. Add `--no-browser` to print the URL without opening it, or `--port 0`
to let the operating system pick a free port.

The example includes three documents and six image comparisons:

- An identical image with exactly zero structural change.
- Different same-sized wizard screenshots with measurable structural change.
- Images with different dimensions and no misleading resized comparison score.
- A missing replacement and a missing baseline image, reported separately.
- A failed workflow and a not-yet-run workflow; absence alone is not treated as failure.

Open a document, enlarge an image pair and nominate a readable replacement with
Substitute. Reload the page to verify persistence. The saved file is
`<generated-directory>/run/review/substitutions.json`. Repository images remain
unchanged. Selecting the same image again removes the intention.

## Browser Checks

With the example server running and Playwright/Chromium installed:

```bash
python3 tools/sunstone-screenshots/examples/review/verify-ui.py \
  --url http://127.0.0.1:8765 \
  --output .sunstone-screenshots/review-checks
```

This verifies desktop/mobile navigation, image loading, enlarged comparison,
viewport bounds and browser errors. It writes screenshots for visual inspection
but does not nominate any images. Automated API, security, persistence and browser
interaction tests use isolated temporary raster fixtures instead:

```bash
PYTHONPATH=tools/sunstone-screenshots python3 -m unittest discover \
  -s tools/sunstone-screenshots/tests -p test_review.py -v
SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 PYTHONPATH=tools/sunstone-screenshots \
  python3 -m unittest discover -s tools/sunstone-screenshots/tests \
  -p test_review_browser.py -v
```
