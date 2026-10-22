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
{ "action": "hover", "selector": "[data-cy='sidebar-paper']:visible .sidebar-header", "pauseAfter": true }
```

Use this when a recipe fails before you can inspect the page:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/manifest.example.json \
  --tag quickstart \
  --debug \
  --keep-open-on-failure
```

The failure details are printed before pausing. Press Enter in the terminal when
inspection is finished so logout and guest cleanup can run before another attempt.

The same option works for complete `run-group` and `run-suite` executions. For
example, to provision a new getting-started lab and stop at a failing browser step:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/getting-started/group.json \
  --run-dir ".sunstone-screenshots/labs/getting-started-$(date +%Y%m%d-%H%M%S)" \
  --debug --keep-open-on-failure --keep-sudo-alive
```

While paused, the browser remains at the failed state: recipe logout, browser
closure and manifest guest teardown have not run. Inspect it before pressing
Enter; cleanup then runs and the failed lab is retained. Do not start another
workflow against that lab while inspection is paused. This option does not
open or retain a browser for provisioning/guest-setup errors before browser
launch, or for guest-teardown errors after the browser has closed.

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

For the current Sunstone sidebar, hover its visible drawer header:

```json
{ "action": "hover", "selector": "[data-cy='sidebar-paper']:visible .sidebar-header" }
```

`[data-cy='sidebar']` is a layout wrapper and can have an empty bounding box even
while the fixed-position drawer is visible. Adding `:visible` to that wrapper
does not give it a hover target. The header inside `sidebar-paper` is visible
and owns the event that expands the menu. The drawer center can be empty space
without an expansion handler. `:visible` also excludes any hidden drawer copy
before the runner selects its first match. Increasing the timeout or forcing a
hover on a non-visible wrapper will not fix this target mismatch.

Sidebar parent items are toggles, not idempotent "open" commands. Successful VM
instantiation already redirects to `/vm` and expands the active Instances menu.
Clicking Instances again closes it. After Finish, use
`{ "action": "waitForURL", "url": "**/vm", "timeout": 60000 }` and then wait for
the VM row to reach RUNNING instead of repeating the sidebar navigation.

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
  A long installation, appliance download or browser inspection can outlast
  cached authorization. For interactive local runs, add `--keep-sudo-alive`
  after running `sudo -v` in the same terminal. This option is supported by
  `provision`, `capture`, `run-group` and `run-suite`. It validates the existing
  authorization with noninteractive `sudo -n -v`, then refreshes it every minute
  until the command exits, including through guest teardown. The refresh thread
  stops on completion, errors or interrupts; it never prompts for a background
  password or changes sudo policy. `--check` does not start a refresh thread.
  If renewal is denied, a warning is printed and later guest commands can still
  fail. Normal sudo cache expiry applies again after the command exits.
  Unattended runs need administrator-configured sudo policy. Do not grant
  unrestricted passwordless sudo merely for this tool. Remove `ssh_local_user`
  to use your own key instead.
- Enable nested virtualization on the outer host and expose it to the VM.
  Installation fails if `/dev/kvm` is absent; miniONE's emulation fallback is
  not the intended environment for these KVM workflows.
- `disable_automatic_updates`: optional boolean, default `false`. The supplied
  Ubuntu lab configurations enable it to prevent unattended upgrades from
  restarting OpenNebula, MariaDB, SSH or networking during capture. After
  cloud-init completes and before miniONE installation, the guard sets
  `APT::Periodic::Enable "0"`, stops APT scheduling timers, masks those timers
  and their services, and waits for any running scheduled APT job to finish.
  It does not stop the package services, kill package processes, remove locks,
  or change the laptop's update policy. Waiting uses the existing
  `install_timeout` budget and is recorded in `install.log`.
  This currently covers APT guests only; other distributions are logged as
  skipped. The configuration and masks persist in the guest, including across
  reboots. Use this only for disposable screenshot labs, not production VMs.
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

### Troubleshooting Inner Readiness

After miniONE completes, provisioning requires a responding inner API and at
least one KVM host in MONITORED state (`STATE=2`). A host in INIT (`STATE=0`)
has not completed initial monitoring, even if Sunstone login works. The timeout
includes the last check's error and saves it as `services_error` in `state.json`:
SSH/sudo failures, invalid XML and missing or unmonitored hosts are reported
separately. Host monitoring errors are included when available in the host XML.

Inside the retained lab VM, inspect the host and monitor logs as root:

```bash
su - oneadmin -c 'onehost show 0'
tail -n 80 /var/log/one/monitor.log
tail -n 80 /var/log/one/oned.log
```

To request another monitoring update for the miniONE localhost host:

```bash
su - oneadmin -c 'onehost forceupdate 0'
```

The host must actually become MONITORED before browser workflows can proceed.
A failed suite remains stopped while the guest is investigated. Sudo credentials
can also expire during installation; a `sudo: a password is required` diagnostic
refers to the SSH transport when using local `ssh_local_user: "oneadmin"`.

This first backend supports one VM and miniONE. Multi-host installation, automatic
repository tunnels, custom seeding and restarting a partial installation are not
implemented. A suite can resume after a completed installation stops at readiness
checks, as described below.
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

### Getting Started Pages (Inventory Rows 2-5)

`groups/getting-started/group.json` contains one manifest per documentation page
and shares one disposable miniONE VM between these ordered workflows:

| Manifest | Captures |
| --- | --- |
| `deploy_opennebula_onprem_with_minione.json` | Login, dashboard, network navigation/details, Alpine template and instantiation wizard, running VM, VNC console: nine captures with light/dark variants. |
| `deploy_opennebula_on_aws.json` | References the same nine image pairs through `sharedFrom`; no AWS resources are provisioned and the Alpine workflow is not repeated. |
| `deploy_opennebula_onprem_with_poc_iso.json` | VXLAN configuration, IPv4 address range, context, and vLLM marketplace selection. Three GPU-instantiation screenshots are explicitly deferred. |
| `validate_the_environment.json` | Host, cluster, datastore and network details, followed by the complete WordPress import and instantiation workflow: 22 captures. |

All entries start as `draft` until tested against the target build and visually
approved. Coverage is checked against the Markdown image references in tests.
The group produces 44 distinct replacement files and four per-page QA reports.
AWS console images, ISO boot/installer screens, inline button icons, and the
WordPress website screenshot are outside this Sunstone automation's scope.
Existing documentation image files are not modified during capture.

Review this group's **own** `provision.json` before running: set the outer VM
template and internal build repository as needed. It starts with the same
settings as `provision.example.json` but does not track later changes to that
file. Start sshuttle and the repository proxy as required by your setup.
Allow disk space and download time for the WordPress appliance, and enough
nested-virtualization capacity to run WordPress and Alpine together.

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/getting-started/group.json \
  --run-dir .sunstone-screenshots/labs/getting-started-01 --check

sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/getting-started/group.json \
  --run-dir .sunstone-screenshots/labs/getting-started-01 --debug
```

Review `<run-dir>/qa/001.html` through `004.html` against the originals.
The VM is destroyed only after every page, cleanup hook and report succeeds;
a failure retains the lab and its logs. Use a new run directory for a fresh run.
This documentation group is separate from `groups/example-suite.json`.

The miniONE page creates one Alpine VM and removes it after the VNC capture.
The VNC recipe opens the VM's information drawer, clicks the overflow menu,
hovers over **Console**, and selects **VNC**. It switches to the newly opened
tab, captures the console, then returns to the Sunstone tab to log out.
The validation page imports WordPress
through Sunstone, waits for the **local image** to reach READY, attaches `vnet`,
deploys WordPress and creates an Alpine VM to match the two-VM final image.
Guest teardown checks the workflow invocation, baseline IDs, owner and
VM/template/image dependencies before terminating the WordPress VM and deleting
its template/image. Alpine cleanup uses the existing guarded helper scripts.
No pre-existing WordPress resource with the intended name is silently reused.

The ISO network recipe fills an unsubmitted form; it does not install the ISO,
enable FRR/EVPN, or create an operational VXLAN network. Its `enp0s3` field is
an illustrative value matching the original screenshot, not an assertion about
the lab interface. The vLLM recipe selects its catalog entry without importing
the large image. GPU screenshots are listed under `deferredScreenshots`, with
reasons, and also appear as deferred in the QA report. They need a provision
with real passthrough GPU inventory before automation can capture them.

Page setup temporarily sets the lab oneadmin user's Sunstone scheme to `system`
so browser color-scheme emulation applies even to wizard captures. Other user
settings are preserved and the original template is restored at teardown.
Do not change that user's settings concurrently during a page capture.

If an earlier version stopped at the first setup hook with
`oneuser update 0 /dev/stdin` and `argument 1 must be one of file`, both theme
hooks now use `oneuser update 0` with the template piped to standard input.
Omitting the optional filename selects the CLI's stdin support; passing
`/dev/stdin` explicitly incorrectly triggers regular-file validation. To recover
that specific failure without provisioning another VM:

```bash
sudo -v
python3 tools/sunstone-screenshots/groups/getting-started/scripts/recover-theme.py \
  --run-dir .sunstone-screenshots/labs/getting-started-01

tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/getting-started/group.json \
  --run-dir .sunstone-screenshots/labs/getting-started-01 --reuse --debug
```

Recovery requires the first failed page, no captured files, the known CLI error,
the recorded running VM/address, and no Alpine/WordPress resource markers. It
refuses unrelated user-setting changes, restores and verifies the saved user
template, and only then archives the failed `workflow.json`. It does not delete
VMs, templates or images, and is not a general retry for partially run recipes.

For selector debugging on a retained, ready lab, rerun only the affected page:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/groups/getting-started/deploy_opennebula_onprem_with_minione.json \
  --run-dir .sunstone-screenshots/labs/getting-started-01 \
  --output-root .sunstone-screenshots/labs/getting-started-01/screenshots \
  --debug --keep-open-on-failure
```

This runs the page's setup and cleanup hooks on the existing VM without
provisioning or destroying it. It overwrites that page's replacement images,
not the tracked documentation assets. It does not run the other pages or reset
the failed group's `workflow.json`; the group reuse safeguard still applies.

To isolate just `recipes/alpine-console.json`, select its screenshot ID and
skip the page's guest hooks. First finish any older paused capture, then ensure
a VM named **docs-screenshot-alpine** is RUNNING in the inner miniONE lab. You
can instantiate the existing Alpine template manually in Sunstone with that
name. The normal page teardown removes it, so a completed page run will not
leave it available for this debug command.

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/groups/getting-started/deploy_opennebula_onprem_with_minione.json \
  --run-dir .sunstone-screenshots/labs/getting-started-01 \
  --output-root .sunstone-screenshots/debug/alpine-console \
  --id minione.console --skip-hooks --debug --keep-open-on-failure
```

`--id` runs only recipes containing selected screenshots. Within each selected
recipe, all workflow steps still run in order. Here that means console login,
navigation, VNC capture and logout, without the other page recipes.
`--skip-hooks` is an explicit debugging override for **manifest guest setup and
teardown only**: recipe setup/teardown and inline `guestCommand` actions still
run. It does not create or delete the Alpine VM, restore user settings, or
clear stale markers. This console-only recipe has no inline guest commands.
Add `--pause-before-step` for step-by-step inspection. Use the normal capture
without `--skip-hooks` for a complete, reproducible page workflow.

If setup reports `Previous theme marker exists`, cleanup from an earlier
invocation did not finish. For example, local sudo authorization may have
expired during browser inspection. Fresh runs deliberately cannot remove
another invocation's markers. Finish any paused capture first, then recover
the interrupted miniONE page before retrying:

```bash
sudo -v
python3 tools/sunstone-screenshots/groups/getting-started/scripts/recover-theme.py \
  --run-dir .sunstone-screenshots/labs/getting-started-01 --include-alpine
```

This mode permits existing screenshots and does not require the old
`/dev/stdin` error. It verifies the first failed page, the original running
lab/address, matching theme and Alpine invocation IDs, and unchanged user
settings. It retries the guarded Alpine teardown (which may terminate that
workflow's VM), restores the saved user settings, verifies both markers are
gone, and archives the failed group result. Existing screenshots and the outer
lab are retained. It refuses a WordPress marker or unrelated resource/user
changes. Do not delete the marker files manually: they hold the ownership
baseline and original settings needed for cleanup.

For a validation-page/WordPress run whose teardown failed, for example after sudo expired,
use the WordPress recovery mode instead. Finish any paused capture before recovery:

```bash
sudo -v
python3 tools/sunstone-screenshots/groups/getting-started/scripts/recover-theme.py \
  --run-dir .sunstone-screenshots/labs/getting-started-20261022-125938 \
  --include-wordpress --keep-sudo-alive
```

This requires the first three group pages to be complete and the validation
page to be failed. It checks the recorded running outer VM/address and the
ownership ID and baseline structure of every remaining WordPress and Alpine
marker before cleanup. When a theme snapshot remains, it also checks that user
settings have not changed outside the workflow. It uses the existing
dependency/ownership-checked scripts in this order: WordPress, Alpine, then theme
restoration. If theme teardown already completed, the remaining WordPress marker
identifies the interrupted invocation; current user settings are left unchanged
and verified again after resource cleanup. It never guesses a missing snapshot.
All markers must be gone and user settings verified before `workflow.json` is
archived as `workflow.failed-wordpress-<id>.json`. Existing screenshots, reports
and the outer lab are retained. Any ownership mismatch or cleanup failure leaves
the failed group result in place for inspection.

WordPress image imports and disk releases can still be running when teardown
starts. Cleanup waits up to two minutes for a deletable image state and image
deletion, rechecking ownership while it waits. It does not use `oneimage delete
--force`. If this times out, the marker is retained and the log identifies the
image ID and last state. Inspect the import/datastore operation before retrying
recovery; a failed WordPress cleanup may leave its marker even after Alpine and
theme teardown succeeded. New captures deliberately refuse that stale marker.

Standalone `capture` does not create a new `workflow.json`. If recovery succeeded
but a later standalone WordPress capture was interrupted, pass the preserved
group archive explicitly:

```bash
sudo -v
python3 tools/sunstone-screenshots/groups/getting-started/scripts/recover-theme.py \
  --run-dir .sunstone-screenshots/labs/getting-started-20261022-125938 \
  --include-wordpress --keep-sudo-alive \
  --workflow-record .sunstone-screenshots/labs/getting-started-20261022-125938/workflow.failed-wordpress-5f0f3d64d8e54e9eab986538bb49816e.json
```

Use the archive path printed by the previous recovery. It must be a WordPress
archive in the same run directory, and `workflow.json` must be absent. The helper
still checks the running VM, current markers, ownership and user settings. It
preserves the earlier archive and writes a separate record for the newly
recovered invocation only after cleanup and verification succeed.

Capture and recovery take an exclusive per-lab `.capture.lock`. A paused browser
still holds this lock: press Enter in its terminal and let teardown finish before
starting another command for the same lab. The operating system releases the
lock when the process exits; do not delete the lock file to bypass it.

After successful recovery, retry only the WordPress recipe with guest hooks
enabled and sudo renewal active:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/groups/getting-started/validate_the_environment.json \
  --run-dir .sunstone-screenshots/labs/getting-started-20261022-125938 \
  --output-root .sunstone-screenshots/debug/wordpress \
  --id validation.running \
  --debug --keep-open-on-failure --keep-sudo-alive
```

All WordPress workflow steps run, but only the final screenshot is saved.
Do not use `--skip-hooks`: the recipe's Alpine guest command requires the
current invocation's setup marker, and teardown owns the imported resources.

If guest teardown reports `Failed to open TCP connection to localhost:2633`
with `Connection refused`, SSH reached the lab, but its inner OpenNebula API
was unavailable. In that message `localhost` is the lab VM, not the laptop.
A disabled Sunstone refresh button can accompany the outage; retrying UI
clicks does not restore the API. Inspect the retained VM before launching
another lab. Run these commands as root **inside the retained VM**:

```bash
systemctl status opennebula --no-pager -l
journalctl -u opennebula -n 80 --no-pager
tail -n 80 /var/log/one/oned.log
```

Establish why the service stopped before restarting it. A guest memory or disk
shortage is one possibility, not something the refresh error alone proves.
Restore API availability before running the recovery helper above; both
Alpine cleanup and theme restoration need it. Keep the ownership markers and
failed workflow result until recovery succeeds.

One observed cause was unattended OS upgrades overlapping capture: the journal
showed `apt-daily-upgrade.service` clients reloading/reexecuting systemd and
restarting services while Alpine entered PROLOG. The disposable-lab
`disable_automatic_updates` guard prevents this scheduled-update race in new
provisions. It does not prove that every PROLOG stall is caused by upgrades.
Neither `capture` nor `run-group --reuse` applies the guard retroactively to an
old lab. Enabling the option changes the recorded provisioning configuration,
so an older lab will fail the reuse configuration check. Use a fresh run
directory to test the updated provisioning; do not edit old `state.json` files
to claim the guard has run.

#### Shared Image References

When two documents use the same asset, keep a screenshot entry in each page
manifest and make the later entry an explicit reference to the producer:

```json
"sharedFrom": {
  "manifest": "deploy_opennebula_onprem_with_minione.json",
  "id": "minione.dashboard"
}
```

The consumer keeps its own `id` and `doc`; its `image`, `darkImage`, `recipe`,
`capture` and manifest defaults must match the source. The producer must occur
earlier in the same group. References cannot be chained. The runner checks the
replacement files exist, skips duplicate browser actions and still produces
the consumer's own QA report. Standalone capture requires the producer's files
in the same `--output-root`; it never substitutes the old tracked images.

The starter `groups/single-node/` runs two workflows on the same provision:

1. `automated.json`: log in, instantiate the existing Alpine template as
   `docs-screenshot-alpine`, wait up to five minutes for RUNNING in the VMs view,
   capture that view and log out. Guest teardown terminates only that workflow's
   VM with `onevm terminate --hard` and waits for DONE before continuing.
2. `marketplace-apps.json`: log in again, open Storage > Apps, search for
   `wordpress`, open Service WordPress - KVM, capture its details and log out.

These examples cover one screenshot per page. WordPress is inspected without
downloading or instantiating the appliance. The marketplace replacement remains
a draft because the current documentation image shows a different app/view;
review its suitability before promotion.

```text
groups/single-node/
  group.json
  automated.json
  marketplace-apps.json
  recipes/login.json
  recipes/wordpress.json
  scripts/prepare-alpine.sh
  scripts/cleanup-alpine.sh
```

`group.json` names one provisioning configuration and an explicit ordered list
of page manifests. Paths are relative to the group file. You can move the
provisioning configuration into the group folder and change `provision` to
`provision.json`; keep private configurations out of version control.
Each page manifest links back using `"group": "group.json"`. Each grouped
manifest must refer to exactly one document. Duplicate output image paths are
rejected unless they are explicitly linked using `sharedFrom`, preventing one
page from silently replacing another page's captures.

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
`workflow.json` records page results, report paths and `lab_status`. The VM is
retained by default; use the existing `destroy` command explicitly. Groups can
opt into `"destroyOnSuccess": true` to terminate their recorded VM after all
page captures, guest teardown and QA report generation succeed. A failure keeps
the lab for inspection; failed destruction is recorded as `destroy-failed`.
`--reuse` opts into an existing ready lab with matching provisioning settings.
A previous failed/interrupted group run blocks reuse because cleanliness is
unknown. Group execution stops at the first failure.

### Second Group: Services and Hosts

`groups/service-and-hosts/group.json` provisions a separate miniONE VM using its
own `provision.json`. This configuration starts from the same outer OS template
as the first group but creates a distinct VM and has independent build settings.
Update its repository URL when changing builds; it is not linked to changes in
the root `provision.example.json`.

Its ordered workflows are:

1. `oneslurm.json`: log in, search Storage > Apps for the x86_64 Service OneSlurm
   appliance, import it to the `default` image datastore as
   `docs-screenshot-oneslurm`, open Templates > Service Templates and start its
   instantiation wizard. Capture the first step, cancel and log out. Guest
   teardown deletes only the newly imported service template, checking the
   invocation marker and prior template IDs. The service is never deployed.
2. `host-pci.json`: log in, open Infrastructure > Hosts, select `localhost`, open
   PCI in the information drawer, capture and log out.

The group then destroys its VM because `destroyOnSuccess` is enabled. Imported
controller/worker VM templates and disk images remain inside that disposable lab
until destruction; the OneFlow cleanup does not recursively delete shared role
assets. OneSlurm import needs access to the public Marketplace and disk space for
its associated appliances. It can take up to 15 minutes for the import UI to
finish. The host capture shows the real inventory, which can be empty without
PCI passthrough configured on the outer VM.

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/service-and-hosts/group.json \
  --run-dir .sunstone-screenshots/labs/services-01 --check

sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/service-and-hosts/group.json \
  --run-dir .sunstone-screenshots/labs/services-01 --debug
```

Run each group with its own run directory. Both example groups set
`destroyOnSuccess` and destroy their labs after success. Both keep local screenshots,
logs and QA reports. `--reuse` on a group with `destroyOnSuccess` also opts that
reused lab into automatic destruction. Keep the repository tunnel running during
provisioning, and ensure local sudo authorization lasts through any long imports.
The inventory entries remain `draft` until the example captures are reviewed
against the corresponding documentation.

### Running Both Groups in Sequence

`groups/example-suite.json` lists the two groups in order. Run the suite to
provision the first VM, capture Alpine and WordPress, destroy that VM, then
provision a fresh VM for OneSlurm and host PCI and destroy it afterward:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots run-suite \
  tools/sunstone-screenshots/groups/example-suite.json \
  --run-dir .sunstone-screenshots/suites/example-01 --check

sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-suite \
  tools/sunstone-screenshots/groups/example-suite.json \
  --run-dir .sunstone-screenshots/suites/example-01 --debug
```

Use a new suite run directory each time. Group paths are relative to the suite
file. Every suite group must set `destroyOnSuccess` to `true`. All group files
are validated before execution, and local provisioning settings are checked for
both groups before allocating the first VM. `--check` remains offline.

Each group gets a separate subdirectory such as `01-single-node/` and
`02-service-and-hosts/`, containing its own `state.json`, screenshots, logs and
QA reports. The suite-level `suite.json` records group status, run directories
and the distinct outer VM IDs. The runner waits for destruction to finish and
checks the recorded phase is `destroyed` before starting the next group. A
capture, teardown or destruction failure stops the suite; later groups remain
pending and the affected lab is retained for inspection. The suite does not
reuse or destroy labs from other run directories.

If miniONE finished but the suite stopped while waiting for the inner API,
monitored host or Sunstone, fix that guest issue and resume the existing run:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-suite \
  tools/sunstone-screenshots/groups/example-suite.json \
  --run-dir .sunstone-screenshots/suites/example-01 --resume --debug
```

`--resume` rechecks readiness on the recorded VM, preserving its installation.
It verifies the provisioning configuration, VM ownership and management address
before running screenshots. Completed groups are skipped only when their VM is
recorded as destroyed; later pending groups get new VMs as usual. Add `--check`
to validate the saved resume state offline without changing it.

Resume is limited to readiness failures or interruptions before screenshot
workflows start. It refuses partial installations, changed group paths/order or
provisioning settings, and groups with an existing `workflow.json`. Failures after
screenshot setup can leave guest resources behind and require their workflow
cleanup rather than automatic replay.

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

For longer guest hooks, use `{"script": "scripts/prepare-alpine.sh", "timeout": 30}`
instead of `command`. Script paths are relative to the page manifest and their
contents run through Bash inside the guest. The CLI validates that script files
exist before provisioning. Recipe `guestCommand` steps still use inline `command`.
All guest commands in a page invocation share the exported `SUNSTONE_WORKFLOW_ID`.
The Alpine scripts use that ID, the existing VM IDs and the source template ID
to identify their own resources. A pre-existing VM with the test name blocks setup;
cleanup leaves another invocation's resources untouched.

Recipes can also define a `teardown` list of browser actions, which runs after
the final screenshot and before the browser context closes, including on failure.
The examples use it for explicit logout. Manifest guest teardown runs afterward.
For asynchronous UI state, `waitForSelector` supports `refreshSelector`: it tries
that refresh control after each five-second selector wait, bounded by the shared
`timeout` in milliseconds. A refresh click can wait up to five seconds within
that budget. If the control stays disabled, hidden or busy, its click timeout
does not abort the longer wait for the target state. Other browser errors still
fail the recipe. This lets the Alpine example wait for the visible RUNNING
status without relying on a fixed boot delay.
The optional `state` field accepts Playwright's `visible`, `hidden`, `attached`
and `detached` states. The OneSlurm recipe waits for its import modal to become
`hidden` before navigating to Service Templates.

To repeat both examples on an existing ready lab after a successful group run:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/single-node/group.json \
  --run-dir .sunstone-screenshots/labs/pages-03 --reuse --debug
```

Commands are trusted executable input. Only run reviewed manifests/recipes.
Their output is appended to private `<run-dir>/guest-commands.log`; avoid printing
secrets. Timeout defaults to 120 seconds, and timeout does not guarantee remote
process termination. Teardown is attempted after setup or capture failures, and
all teardown commands are attempted even if an earlier cleanup fails. Hard
process termination cannot guarantee cleanup. Use idempotent teardown and delete
only resources created by that page; the runner cannot prove a clean guest.

If this example stops at Alpine teardown with a template mismatch, note that
`onevm list -x` omits `TEMPLATE_ID` in abbreviated pool records. Cleanup checks the
full record from `onevm show <id> -x` before terminating the VM. To retry cleanup
for a retained run, execute this helper on the laptop:

```bash
sudo -v
python3 tools/sunstone-screenshots/groups/single-node/scripts/recover-alpine.py \
  --run-dir .sunstone-screenshots/labs/pages-03
```

The helper verifies the recorded outer VM, uses the failed invocation's ownership
marker and runs the current cleanup script. Only after successful cleanup and
marker removal does it archive `workflow.json` as `workflow.failed-<id>.json`,
allowing `run-group --reuse` to rerun the group. It refuses runs stopped on other
pages. If SSH or cleanup fails, the failed result remains in place.

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

## Tests

Run the unit tests without contacting infrastructure:

```bash
PYTHONPATH=tools/sunstone-screenshots python3 -m unittest discover \
  -s tools/sunstone-screenshots/tests
```

The opt-in browser regression uses a local HTML fixture with a zero-sized
sidebar wrapper and a hidden drawer copy. It runs the actual recipe navigation
steps in headless Chromium at two desktop viewport sizes:

```bash
SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 PYTHONPATH=tools/sunstone-screenshots \
  python3 -m unittest discover -s tools/sunstone-screenshots/tests \
  -p test_sidebar_browser.py -v
```

This requires Playwright and its Chromium installation but no Sunstone VM.

The console-menu and disabled-refresh regressions are also opt-in local browser
tests. To run all browser regressions:

```bash
SUNSTONE_SCREENSHOTS_BROWSER_TESTS=1 PYTHONPATH=tools/sunstone-screenshots \
  python3 -m unittest discover -s tools/sunstone-screenshots/tests \
  -p 'test_*_browser.py' -v
```
