# Sunstone Screenshot Automation

This directory is an initial local framework for replacing Sunstone screenshots in
the OpenNebula documentation. It is intentionally split into small layers:

- an inventory scanner that finds image references in `content/**/*.md`
- a manifest that records which documentation image is produced by which recipe
- Playwright recipes that drive Sunstone and save replacement screenshots
- a static visual QA report for current-vs-replacement review

The provisioning backend creates a single VM on a local OpenNebula installation,
installs miniONE over SSH, and supplies the resulting Sunstone connection to the
capture runner. See VM Provisioning below.

## Directory Layout

```text
tools/sunstone-screenshots/
├── bin/sunstone-screenshots          # CLI entry point
├── manifest.example.json             # Example screenshot database
├── recipes/                          # Playwright recipe JSON files
├── requirements.txt                  # Optional Playwright dependency
├── schemas/manifest.schema.json      # Manifest shape
└── sunstone_screenshots/             # Python implementation
```

Generated screenshots and QA reports should live under `.sunstone-screenshots/`,
which is ignored by Git.

## Local Workflow

### 1. Seed the screenshot inventory

Scan the documentation for likely Sunstone screenshots and export CSV for the
spreadsheet:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots scan \
  --only-sunstone \
  --format csv \
  --output /tmp/sunstone-screenshots.csv
```

The scanner recognizes Markdown image syntax and Hugo `{{< image >}}`
shortcodes, including `path` and `pathDark` variants. It normalizes `/images/...`
references to `assets/images/...` so the inventory can be checked against files
in this repository.

### 2. Curate the manifest

Use the spreadsheet as the human-friendly working view, then convert approved
rows into a manifest like `manifest.example.json`.

Each manifest row answers:

- `doc`: where the screenshot is referenced in the documentation
- `image` and optional `darkImage`: which repo assets will be replaced
- `environment`: what OpenNebula/Sunstone setup is needed
- `recipe` and `capture`: which Playwright workflow creates the image
- `tags`: useful subsets such as `quickstart`, `oneform`, or `networking`

Validate the manifest before capture:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots validate \
  tools/sunstone-screenshots/manifest.example.json
```

### 3. Run recipes against Sunstone

Install Playwright when you are ready to run captures:

```bash
python3 -m pip install -r tools/sunstone-screenshots/requirements.txt
python3 -m playwright install chromium
```

For the current MVP, point the runner at an already available Sunstone endpoint:

```bash
SUNSTONE_URL=http://localhost:2616 \
SUNSTONE_USER=oneadmin \
SUNSTONE_PASSWORD=opennebula \
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --output-root .sunstone-screenshots/runs/local
```

Recipe captures are executed sequentially within a recipe file, so a wizard can
be represented as one `setup` block followed by ordered `captures`. Manifest
entries point to the capture where the screenshot should be taken.

The sequence example shows this pattern with one recipe and several manifest
entries:

- `manifest.sequence-example.json`
- `recipes/quickstart-vms-sequence.json`

Run the whole sequence with:

```bash
SUNSTONE_URL=http://localhost:2616 \
SUNSTONE_USER=oneadmin \
SUNSTONE_PASSWORD=opennebula \
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.sequence-example.json \
  --tag quickstart-sequence \
  --debug
```

The browser executes the recipe once, in capture order. Each manifest entry
selects one capture point by name, for example `login-page`, `dashboard`,
`instances-menu`, or `vm-templates`.

### Visually debug recipes

To watch a recipe run live in a browser, add `--debug` to the normal capture
command:

```bash
SUNSTONE_URL=http://localhost:2616 \
SUNSTONE_USER=oneadmin \
SUNSTONE_PASSWORD=opennebula \
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --debug
```

`--debug` opens a visible browser, slows Playwright actions down, and prints
each recipe step before it runs. For a lighter version that only shows the
browser, use `--headed`. To tune the speed yourself:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --headed \
  --slow-mo 1000
```

For step-by-step debugging with Playwright Inspector:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --debug \
  --pause-after-step
```

You can also pause around one specific step in the recipe:

```json
{ "action": "hover", "selector": "div[data-cy='sidebar']", "pauseAfter": true }
```

Use this when a recipe fails before you can inspect the page:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --debug \
  --keep-open-on-failure
```

### Debug selectors

Use the selector debugger when a recipe cannot find or fill fields:

```bash
SUNSTONE_URL=http://localhost:2616 \
tools/sunstone-screenshots/bin/debug-selector \
  --recipe tools/sunstone-screenshots/recipes/quickstart-landing.json
```

The debugger opens the page, prints all input-like elements, then reports how
many elements each recipe selector matches with useful attributes such as
`name`, `type`, `placeholder`, labels, visibility, and bounding boxes.

To test a single selector and try filling it:

```bash
SUNSTONE_URL=http://localhost:2616 \
tools/sunstone-screenshots/bin/debug-selector \
  "input[name='user']" \
  "input[name='token'], input[type='password']" \
  --try-fill "input[name='user']" oneadmin \
  --try-fill "input[name='token'], input[type='password']" opennebula
```

Add `--pause` to open Playwright Inspector after the report is printed.

### 4. Review replacements

Generate a static visual QA report:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots qa-report \
  tools/sunstone-screenshots/manifest.example.json \
  --replacement-root .sunstone-screenshots/runs/local \
  --output .sunstone-screenshots/qa/index.html
```

Open `.sunstone-screenshots/qa/index.html` in a browser. The report shows the
current checked-in screenshot next to the replacement. Approve/reject choices
are stored in browser local storage for quick review during a local run.

Once the run is accepted, copy the generated `assets/images/...` tree from the
run directory into the repository and review the Git diff.

## Recipe Format

Recipes are JSON files with optional `setup` steps and ordered `captures`.

```json
{
  "id": "example-workflow",
  "setup": [
    { "action": "goto", "url": "${SUNSTONE_URL}" }
  ],
  "captures": [
    {
      "id": "first-step",
      "steps": [
        { "action": "click", "role": "button", "name": "Create" },
        { "action": "waitForSelector", "selector": "[data-testid='wizard']" }
      ],
      "screenshot": {
        "selector": "body"
      }
    }
  ]
}
```

Supported actions in the initial runner:

- `goto`
- `waitForSelector`
- `waitForURL`
- `waitForLoadState`
- `waitTime`
- `hover`
- `moveMouse`
- `defocus`
- `setColorScheme`
- `pause`
- `click`
- `switchToPage`
- `fill`
- `press`
- `evaluate`

### Locator Format

Recipe steps can locate elements in two different ways.

The recommended style uses Playwright's user-facing locators. These are not
written as one selector string; they use recipe keys that map to Playwright
locator methods:

```json
{ "action": "click", "role": "button", "name": "Sign In Now", "exact": true }
{ "action": "click", "dataCy": "login-button" }
{ "action": "fill", "label": "Username", "value": "${SUNSTONE_USER}" }
{ "action": "fill", "text": "Username", "value": "${SUNSTONE_USER}" }
```

These correspond roughly to Playwright code like:

```js
await page.getByRole("button", { name: "Sign In Now", exact: true }).click();
await page.getByLabel("Username").fill(user);
await page.getByText("Username").fill(user);
```

The `dataCy` key is a convenience added by this screenshot runner for Sunstone
elements that have Cypress-style `data-cy` attributes. This recipe step:

```json
{ "action": "click", "dataCy": "login-button" }
```

is equivalent to this selector step:

```json
{ "action": "click", "selector": "[data-cy='login-button']" }
```

If the `data-cy` attribute is on a specific button, both of these work:

```json
{ "action": "click", "dataCy": "login-button" }
{ "action": "click", "selector": "button[data-cy='login-button']" }
```

If the `data-cy` attribute is on a wrapper around the button, select the button
inside it:

```json
{ "action": "click", "selector": "[data-cy='login-actions'] button:has-text('Sign In Now')" }
```

To discover available Cypress attributes on the current page, run:

```bash
SUNSTONE_URL=http://localhost:2616 \
tools/sunstone-screenshots/bin/debug-selector "[data-cy]"
```

For the Sunstone login button, prefer:

```json
{
  "action": "click",
  "role": "button",
  "name": "Sign In Now",
  "exact": true
}
```

The lower-level style uses a `selector` string. In this runner, `selector` is
passed to Playwright's `page.locator(selector)`, so it uses Playwright CSS/XPath
selector syntax:

```json
{ "action": "click", "selector": "button:has-text('Sign In Now')" }
{ "action": "click", "selector": "[data-cy='login-button']" }
{ "action": "fill", "selector": "input[name='user']", "value": "${SUNSTONE_USER}" }
{ "action": "fill", "selector": "input[type='password']", "value": "${SUNSTONE_PASSWORD}" }
{ "action": "waitForSelector", "selector": "[data-testid='wizard']" }
```

Useful selector string patterns:

- `input[name='user']`: element type plus attribute match.
- `input[type='password']`: password input by type.
- `[data-cy='login-button']`: any element with a Cypress `data-cy` attribute.
- `button[data-cy='login-button']`: a button with that `data-cy` attribute.
- `[data-cy='login-actions'] button`: a button inside a `data-cy` wrapper.
- `[data-testid='login-button']`: any element with a stable test id.
- `button:has-text('Sign In Now')`: button containing visible text.
- `button:has-text('Sign In Now'):visible`: same, but only visible matches.
- `css=button:has-text('Sign In Now')`: explicit CSS selector prefix.
- `xpath=//button[contains(., 'Sign In Now')]`: explicit XPath selector prefix.

In CSS selectors, a comma means "or". For example,
`input[name='user'], input[type='text']` matches the username field and every
text input. Since the runner uses the first match for `click` and `fill`, broad
fallbacks can accidentally fill the wrong field. Prefer a single stable selector
when possible, or use a fallback only when both sides identify the same field.

Good references:

- Playwright locators: https://playwright.dev/docs/locators
- Playwright CSS/XPath and other selector strings:
  https://playwright.dev/docs/other-locators
- MDN CSS selectors reference:
  https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_selectors

Prefer role, label, placeholder, or `data-testid` locators where possible.
Text/CSS selectors are useful for early prototypes, but they are more fragile
during UI copy or DOM structure changes.

### Theme, Defocus, and Cropping

When a manifest entry has both `image` and `darkImage`, the runner captures the
same capture point twice. Before writing each file it now applies the matching
browser color scheme:

- `image` uses Playwright `color_scheme="light"`
- `darkImage` uses Playwright `color_scheme="dark"`

If Sunstone needs extra UI actions to settle or toggle the visible theme, add
`themeSteps` to the recipe, capture, or `screenshot` block. These steps run
immediately before the screenshot for that variant:

```json
{
  "themeSteps": {
    "light": [
      { "action": "waitTime", "timeout": 250 }
    ],
    "dark": [
      { "action": "waitTime", "timeout": 250 }
    ]
  }
}
```

`themeSteps` can use normal recipe actions, so if Sunstone requires clicking a
theme toggle rather than only responding to browser color scheme, put those
clicks in the `dark` or `light` list.

To move the mouse away from hover-opened menus, use viewport percentages:

```json
{ "action": "defocus", "xPercent": 50, "yPercent": 50 }
```

`defocus` and `moveMouse` both move the mouse. They accept either percentages or
pixels:

```json
{ "action": "moveMouse", "xPercent": 95, "yPercent": 50 }
{ "action": "moveMouse", "x": 1200, "y": 500 }
```

Percentage coordinates are based on the current viewport. `xPercent: 0` is the
left edge, `xPercent: 100` is the right edge, `yPercent: 0` is the top, and
`yPercent: 100` is the bottom.

To crop a screenshot to a screen region, add a `clip` object to the screenshot
configuration. Percent bounds are usually best for screenshots that may run at
different viewport sizes:

```json
"screenshot": {
  "selector": "body",
  "clip": {
    "leftPercent": 0,
    "rightPercent": 100,
    "topPercent": 8,
    "bottomPercent": 92
  }
}
```

Pixel bounds are also supported:

```json
"screenshot": {
  "clip": {
    "left": 240,
    "right": 1440,
    "top": 80,
    "bottom": 900
  }
}
```

The bounds are left/right/top/bottom, not x/y/width/height. If `clip` is set,
the crop is taken from the viewport. If `clip` is not set, `selector` and
`buffer` work as before.

### New Tabs

Some Sunstone actions open a new browser tab, such as a VNC console. Mark the
step that opens the tab with `opensPage: true`; the runner will wait for the new
tab and make it the active page for later steps and screenshots:

```json
{
  "action": "click",
  "selector": "button[data-cy$='-vnc']",
  "opensPage": true,
  "newPageWaitForLoadState": "domcontentloaded"
}
```

Any following `waitTime`, `waitForSelector`, or `screenshot` will use the new
tab. If the tab is already open and you just need to switch to it:

```json
{ "action": "switchToPage", "target": "last" }
```

Supported `switchToPage` targets are `last`, `first`, `previous`, or an explicit
zero-based page `index`:

```json
{ "action": "switchToPage", "index": 1 }
```

## VM Provisioning Path

Install `requirements-provision.txt` in your Python environment:

```bash
python3 -m pip install -r tools/sunstone-screenshots/requirements-provision.txt
```

Configure `provision.example.json` for the outer (local) OpenNebula installation:

- `endpoint` and `auth_file`: outer XML-RPC endpoint and credential file.
- `template_id`: replace `null` with a clean supported OS template ID. Its network,
  disk, CPU and memory configuration are used unchanged; start with 4 vCPUs,
  8 GiB RAM and 40 GiB disk for a small lab, adjusting for workloads.
- The template must already contextualize SSH access for `ssh_user`/`ssh_key`.
  Non-root users need passwordless sudo. The runner requires local OpenSSH.
  By default, `ssh_key` is a private key readable by your local runner account, not
  necessarily the OpenNebula service account's key in `/var/lib/one/.ssh`.
  Configure the matching public key in the VM template's SSH contextualization
  for the guest user named by `ssh_user`. Setting a private-key path here does
  not inject its public key into the guest. The outer API credential in
  `auth_file` is separate from SSH authentication.
- The example uses `ssh_local_user: "oneadmin"` to run only the local SSH
  subprocess through `sudo -n -H -u oneadmin -- ssh`. The guest login remains
  `ssh_user: "root"`; API access, downloads and output files still belong to the
  runner. In this mode `ssh_key` and `ssh_known_hosts` must be absolute paths
  accessible to `oneadmin`. The known-hosts file's parent directory must exist
  and be writable by that account. Configuration checks key readability via
  `sudo -n -H -u oneadmin -- test -r /var/lib/one/.ssh/id_rsa` before allocation.
  Sudo must authorize both commands without prompting: for local interactive
  use, run `sudo -v` in the same terminal before provisioning or capture.
  A long installation can outlast cached authorization; unattended runs need
  administrator-configured sudo policy. Do not grant unrestricted passwordless
  sudo merely for this tool. Remove `ssh_local_user` to use your own key instead.
- Enable nested virtualization on the outer host and expose it to the VM.
  Installation fails if `/dev/kvm` is absent; miniONE's emulation fallback is
  not the intended environment for these KVM workflows.
- `management_nic_id`: NIC whose IPv4 address is reachable from the runner.
- `minione_script`: HTTP(S) URL or local path to a miniONE script, preferably
  from a pinned release/commit. For example:
  `https://github.com/OpenNebula/minione/releases/download/v7.4.0/minione`.
  URL downloads follow redirects and are saved as `minione` in the run directory
  before allocating a VM. The source URL and downloaded SHA-256 are recorded in
  state; installation transfers that exact copy over SSH. Download failures stop
  provisioning before allocation. `--check` validates configuration locally and
  does not download or verify URL availability. Local file paths resolve relative
  to the configuration file; `~` works.
- `opennebula_version`: release to install. Optional `repo_base` is passed to
  miniONE's `--repo-base`; internal repository layout must match that installer.
  The example uses the tested Ubuntu 24.04 nightly base
  `http://172.20.0.1/build/7.5-nightly/ubuntu2404/repo`. miniONE appends
  `/Ubuntu/24.04` and, in the pinned installer, derives the version from the
  URL's `build/7.5` component, overriding `--version`.
- `minione_force`: boolean, default `false`. Passes miniONE's `--force` to
  override its supported-version guard for nightly builds. This also affects
  other overridable checks and is not a guarantee of package compatibility.
  For released packages, set `repo_base` to `null`, `minione_force` to `false`
  and `opennebula_version` to the desired supported release.
- `minione_password`: optional password for the guest's `oneadmin` Sunstone
  account. Omit it or use `null` to let miniONE generate a random password.
  For an isolated disposable debugging lab, set `"minione_password": "opennebula"`
  and log in as `oneadmin`. Do not use this simple password on exposed systems.
  The password is stored in the configuration and private `state.json`, may
  appear in miniONE's private `install.log`, and is passed in miniONE's guest
  process arguments. Keep real passwords out of version control and restrict
  local configuration permissions (for example, `chmod 600 <config-file>`).
- `sunstone_port`: HTTP port miniONE configures (default 80).

The guest needs access to package repositories and the miniONE Marketplace
dependencies. A runner-side sshuttle connection alone does not provide guest
access; arrange routing/proxy access separately. Keep inner and outer network
ranges distinct. Configuration files and recipes are trusted executable inputs.

Validate local settings, then provision into a new run directory:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots provision \
  tools/sunstone-screenshots/provision.example.json \
  --run-dir .sunstone-screenshots/labs/minione-01 --check

tools/sunstone-screenshots/bin/sunstone-screenshots provision \
  tools/sunstone-screenshots/provision.example.json \
  --run-dir .sunstone-screenshots/labs/minione-01
```

Provisioning records the VM ID immediately, waits for running state and SSH,
installs miniONE, then checks the inner API, a monitored KVM host and HTTP access
to Sunstone. It retains the lab after success or failure. `state.json` records
progress/configuration; `install.log` includes installer output and the installed
package inventory. Both are private files: miniONE output can include passwords.
By default each run uses a dedicated SSH known-hosts file. With `ssh_local_user`,
the configured `ssh_known_hosts` file is shared across runs instead. New runs
record a unique `host_key_alias` based on the VM name, so recycled IP addresses
do not collide with previous labs. SSH accepts the first key for that alias and
checks it on later connections; changed keys within a run are still rejected.
Older runs without an alias retain their existing IP-based checks. Do not remove
an old key without independently verifying the replacement VM's identity.

Inspect, capture, and destroy that run explicitly:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots status \
  --run-dir .sunstone-screenshots/labs/minione-01

tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.minione.json \
  --run-dir .sunstone-screenshots/labs/minione-01 \
  --output-root .sunstone-screenshots/labs/minione-01/screenshots --debug

tools/sunstone-screenshots/bin/sunstone-screenshots destroy \
  --run-dir .sunstone-screenshots/labs/minione-01
```

Capture reads the inner oneadmin credentials over SSH and sets the three
`SUNSTONE_*` variables for the capture invocation. Outer credentials stay local.
Destroy checks the recorded VM name and ID, requests hard termination of that VM
(including its nested guests), and waits for DONE. Logs and screenshots remain.
Existing run directories cannot be provisioned again: after investigating a
failure, destroy the lab and start a fresh run. An interrupted allocation may
require finding the unique recorded VM name in the outer cloud if no ID was saved.
An SSH installation timeout does not guarantee guest processes have stopped.

### Troubleshooting SSH Readiness

`Timed out waiting for SSH and sudo` means the guest readiness check failed,
before miniONE installation started. The timeout includes the last SSH error,
also retained as `ssh_error` in `state.json`.

- `Permission denied (publickey)`: check that `ssh_user` is the guest account
  receiving the public key corresponding to `ssh_key`. Setting `ssh_key` only
  chooses the local private key; it does not inject its public key into the VM.
  In the source template's Context section, include your `.pub` file's contents
  in `SSH_PUBLIC_KEY`, preserving existing keys that are still needed. The guest
  image must support OpenNebula contextualization. Template changes apply to
  newly instantiated VMs, not automatically to the retained VM.
- Connection timeout or refusal: check the selected management NIC, routing,
  guest boot progress, firewall and SSH service.
- A sudo password or permission error: the configured non-root guest account
  needs passwordless sudo; SSH authentication alone is not sufficient.

Do not make the OpenNebula service account's private key broadly readable or
run the entire automation with sudo to bypass a local key permission problem.
After correcting the template, clean up the failed lab with `destroy` when no
longer needed and provision with a new run directory.

This first backend supports one VM and miniONE. Multi-host installation, automatic
repository tunnels, custom seeding and installation resume are not implemented.
The older manifest `provisionCommand`/`teardownCommand` fields remain descriptive;
the CLI commands above perform provisioning explicitly.

## Authoring Guidelines

### Page Manifests and Shared Labs

`inventory.csv` is the master page inventory imported from the release spreadsheet.
It preserves the source URL, assignment, priority, manual status, comments and
reported UI issues. `automation_status` is separate from the historical `Merged`
status: `pending` means no recipe yet, `draft` means incomplete/unverified,
`needs-path` means the page could not be resolved, and `external` means it is
outside this repository. Paths in `doc` are repository-relative; `group` and
`manifest` are relative to `tools/sunstone-screenshots`. Blank mappings are not
executable workflows. Section records are retained as labels on page rows.

The starter `groups/single-node/` contains a group, a one-page manifest and a
recipe. It captures only the login image for the automated installation page,
not all that page's screenshots. Extend it after validating the workflow.

```text
groups/single-node/
  group.json
  automated.json
  recipes/login.json
```

`group.json` names one provisioning configuration and an explicit ordered list
of page manifests. Paths are relative to the group file. You can move the
provisioning configuration into the group folder and change `provision` to
`provision.json`; keep private configurations out of version control.
Each page manifest links back using `"group": "group.json"`. Each grouped
manifest must refer to exactly one document. Duplicate output image paths are
rejected to prevent one page from silently replacing another page's captures.

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/single-node/group.json \
  --run-dir .sunstone-screenshots/labs/pages-01 --check

sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/single-node/group.json \
  --run-dir .sunstone-screenshots/labs/pages-01 --debug
```

`--check` validates group/manifest/recipe references without SSH or provisioning;
it does not validate live selectors, package access or resource cleanup.
The runner provisions once, injects guest Sunstone credentials, executes pages
in order, and generates numbered visual QA reports in `<run-dir>/qa/`.
Replacements go to `<run-dir>/screenshots/`, never directly into tracked assets.
`workflow.json` records page results and report paths. The VM is retained for
inspection on success or failure; use the existing `destroy` command explicitly.
`--reuse` opts into an existing ready lab with matching provisioning settings.
A previous failed/interrupted group run blocks reuse because cleanliness is
unknown. Group execution stops at the first failure.

### Guest Setup and Cleanup

Page manifests accept hooks executed once per page, not per screenshot/theme:

```json
"hooks": {
  "setup": [{"command": "su - oneadmin -c 'onehost list'", "timeout": 60}],
  "teardown": []
}
```

For changes between screenshots, insert a recipe step:

```json
{ "action": "guestCommand", "command": "su - oneadmin -c 'onevm list'", "timeout": 60 }
```

These examples only inspect resources. Replace them with page-specific creation,
modification and cleanup commands. Commands run as root inside the provisioned
guest via the existing SSH transport, never on the laptop or outer OpenNebula.
Use `su - oneadmin -c '...'` for inner-cloud CLI commands. Each command starts a
new shell; persist resource IDs in guest files when later commands need them.
No screenshot-variable interpolation is applied to shell commands.

Commands are trusted executable input. Only run reviewed manifests/recipes.
Their output is appended to private `<run-dir>/guest-commands.log`; avoid printing
secrets. Timeout defaults to 120 seconds, and timeout does not guarantee remote
process termination. Teardown is attempted after setup or capture failures, and
all teardown commands are attempted even if an earlier cleanup fails. Hard
process termination cannot guarantee cleanup. Use idempotent teardown and delete
only resources created by that page; the runner cannot prove a clean guest.

Standalone `capture MANIFEST --run-dir LAB` also runs hooks and guest steps.
Without `--run-dir`, browser-only recipes still work, but guest commands fail.
Screenshot filtering does not skip intermediate workflow steps or page hooks.

To import a future spreadsheet into a new CSV for manual reconciliation:

```bash
PYTHONPATH=tools/sunstone-screenshots python3 -m sunstone_screenshots.inventory \
  /path/to/export.csv /tmp/new-inventory.csv
```

The importer refuses to overwrite an existing CSV so curated mappings are not
lost. External pages and malformed/missing URLs remain explicitly unresolved;
spreadsheet comments are data, never shell instructions.

- Keep one recipe per documentation workflow, not one recipe per image.
- Use deterministic resource names and reset them during recipe setup.
- Fix viewport, locale, theme, and timezone for every run.
- Prefer API/CLI setup for cloud state, then use Playwright only for the UI path
  that the documentation is showing.
- Capture into `.sunstone-screenshots/runs/<run-id>/assets/images/...` first;
  only promote images to `assets/images/...` after QA.
- Add separate manifest entries when light and dark screenshots need different
  UI setup. A shared `darkImage` field is useful when the same capture state can
  be reused for both variants.
