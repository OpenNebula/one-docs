# Offline Catalogue Examples

This directory is a miniature documentation repository. Its text-only SVG assets
are fixture placeholders, not Sunstone screenshots. No VM, browser, SSH, PyOne,
credentials or additional dependencies are needed. The provisioning JSON is
deliberately not a runnable lab configuration.

Run the commands below from the main documentation repository root.

## Example 1: Connected Documents

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots \
  --repo-root tools/sunstone-screenshots/examples/catalogue \
  catalogue tools/sunstone-screenshots/examples/catalogue/inventory.csv --check
```

Expected: exit status `0`, three documents, two manifests, one recipe, two logical
screenshots and no errors. Two warnings are intentional: the third page has no
manifest, and its likely Sunstone image has no capture mapping yet.

The first page produces light/dark variants of one capture. The second page
explicitly reuses that producer with `sharedFrom`. The third page demonstrates
how pending documentation remains visible. The recipe also contains an unmapped
navigation-only stage; this is not a missing screenshot.

Export the graph:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots \
  --repo-root tools/sunstone-screenshots/examples/catalogue \
  catalogue tools/sunstone-screenshots/examples/catalogue/inventory.csv \
  --output .sunstone-screenshots/catalogue/example-valid.json
jq '.summary, .documents[0], .screenshots, .assets' \
  .sunstone-screenshots/catalogue/example-valid.json
```

Follow document `demo.first` to `manifests/first.json`, its screenshot to
`recipes/login.json#login`, and its two assets. Each asset lists all consuming
documents and screenshot mappings, including the shared consumer. File hashes
identify the definitions and baseline image contents used to build the index.

## Example 2: Broken Relationships

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots \
  --repo-root tools/sunstone-screenshots/examples/catalogue \
  catalogue tools/sunstone-screenshots/examples/catalogue/broken.csv \
  --output .sunstone-screenshots/catalogue/example-broken.json
```

Expected: exit status `1`. This deliberately references a missing Markdown file,
image and recipe, plus a capture ID that is not in the existing recipe. JSON is
still exported, with structured diagnostics and the relationships that could be
resolved. Human-readable error output goes to stderr, keeping stdout clean for
JSON exports.

```bash
jq '.valid, .summary, .diagnostics' \
  .sunstone-screenshots/catalogue/example-broken.json
```

## Automated Checks

```bash
PYTHONPATH=tools/sunstone-screenshots python3 -m unittest discover \
  -s tools/sunstone-screenshots/tests -p test_catalogue.py -v
```

These exercise both examples, shared dependencies and ordering, deferred and
disabled screenshots, discovery, missing files, invalid JSON, duplicate IDs,
stale Markdown mappings, path containment, portable exports and CLI exit codes.
