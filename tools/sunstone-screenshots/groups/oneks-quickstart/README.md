# OneKS Quickstart Screenshots

This group covers the 19 Sunstone image pairs in
`content/getting_started/install_opennebula/evaluation/oneks_quickstart.md`.
It creates 38 replacement files in documentation order. The example application
website is not a Sunstone screenshot and is intentionally excluded. No Cloudflare
tunnel is created, no public example application is deployed, and kubectl is not
needed for these captures.

## Provision

The group starts its own disposable miniONE VM, using its own `provision.json`.
It does not reuse the other group's VM and is not automatically added to that
group's four-page run. This configuration starts from the getting-started build
settings but has independent repository/template settings, so update this file
when changing builds. Existing documentation screenshots are never overwritten.

The provisioning config requests 16 GiB RAM, 4 vCPUs and 4 CPU units using
`vm_resources`. These overrides affect only the new VM instance; the underlying
OpenNebula template and other groups are unchanged. The outer cloud must have
enough unallocated capacity to schedule this VM. The template must still provide
nested KVM and enough disk for the OneKS appliance, seed/router, control plane
and worker. Network and disk definitions are inherited without modification.
The guest preflight refuses less than 12 GiB total RAM, 4 vCPUs, working `/dev/kvm`, or
30 GiB free datastore space. Those are minimum checks, not a guarantee that a
busy laptop has enough capacity. The selected control-plane and worker profiles
are the standard `standalone` and `small`, not custom low-resource flavours.

miniONE must provide the `oneks` CLI, `opennebula-ks`, a running OneGate service,
the default OpenNebula cluster and the public `vnet`. OneKS must be configured
with working OneGate, API/TProxy connectivity and internet access from the nested
VMs; the workflow does not rewrite those service/network settings. Setup probes
the CLI API first and leaves a healthy service running. If the API refuses the
connection, setup retries `systemctl restart opennebula-ks` at most three times,
at least a minute apart, while polling readiness with a five-minute deadline.
Authentication/configuration errors are not retried as service-startup errors.
If deployment
stalls, inspect `/var/log/one/oneks.log` and `oneks logs cluster <id>` in the lab.

## Workflow

One browser session performs the whole document flow:

1. Create `private-k8s` through Sunstone with cluster `#0 default`, bridged private
   host networking, and `192.168.200.2` / 100 addresses.
2. Change the public `vnet` DNS to `1.1.1.1` through Sunstone.
3. Create `docs-screenshot-oneks`, selecting the first available supported
   Kubernetes version, `vnet`, `private-k8s` and `Single-Node Control Plane`.
4. Capture the provisioning logs, wait for the real cluster to reach `RUNNING`,
   then capture its VMs. Cluster provisioning has a 30-minute deadline.
5. Create node group `worker1` with the `Small Worker Nodes` flavour and count 1,
   wait up to 20 minutes for its real running state, and capture its details.
6. Capture the Kubeconfig tab with its entire code block masked, then log out.

The mask is applied by Playwright only to the screenshot, not to the live
kubeconfig. A missing or hidden mask target fails the capture. Do not remove the
mask or publish usable cluster credentials to the documentation. The broad block
mask is intentional; realistic-looking placeholder credentials are not generated.

Setup records resource IDs and the original DNS in a mode-0600 invocation marker
inside the guest. Browser checkpoints verify ownership after creating the network
and cluster. Teardown delegates cluster destruction to the OneKS CLI and waits up
to 15 minutes for removal, checks that no live VM/lease still uses the private
network, deletes that network and restores only the original DNS attribute while
preserving other public-network template settings. It does not force-delete
cluster documents, terminate arbitrary VMs, or delete the shared OneKS appliance.
Changed identities, foreign invocation markers and cleanup failures retain the
marker/lab for investigation. The outer VM is destroyed only after capture,
teardown and report generation all succeed.

All captures remain `draft`: selectors were checked against the local OpenNebula
source, but the full workflow still needs live validation against the chosen
nightly build. No VM is provisioned by the automated regression tests.

## Run and Review

From the repository root, with the repository proxy/sshuttle running:

```bash
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/oneks-quickstart/group.json \
  --run-dir .sunstone-screenshots/labs/oneks-check --check

RUN=".sunstone-screenshots/labs/oneks-$(date +%Y%m%d-%H%M%S)"
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/oneks-quickstart/group.json \
  --run-dir "$RUN" --debug --keep-open-on-failure --keep-sudo-alive

.sunstone-screenshots/venv-review/bin/python \
  tools/sunstone-screenshots/bin/sunstone-screenshots review \
  --run-dir "$RUN" --port 0
```

The browser stays open at a failed recipe until Enter is pressed in the terminal.
Guest teardown runs afterwards; a failed run keeps the outer lab. Do not rerun a
partially completed workflow with its existing marker. Inspect/recover it first,
or choose a fresh lab directory. After manual cleanup, you can instead abandon
the previous markers and rerun setup on the same VM:

```bash
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/groups/oneks-quickstart/oneks_quickstart.json \
  --run-dir "$RUN" --output-root "$RUN/screenshots" \
  --force-workflow --debug --keep-open-on-failure --keep-sudo-alive
```

Stop any previous capture first. `--force-workflow` archives this manifest's
OneKS/theme markers under `/root/screenshot-lab/abandoned-<invocation-id>/`;
it does not clean resources or restore settings. Remove the failed cluster and
workflow network and restore public DNS/user settings manually before retrying.
Old resources are not adopted by new-attempt teardown. The JSON dependency
failure must also be fixed independently; forcing does not repair OneKS.

`--id` filters saved images, not the actions:
this single sequential recipe still executes its complete cluster lifecycle.

The group writes `workflow.json`, `screenshots/capture-results.json`,
`guest-commands.log` and `qa/001.html` under the run directory. The standard review
UI reads those results and writes nomination intentions to
`review/substitutions.json`; it does not apply replacements.

## Capacity Check Failures

If setup fails with `OneKS lab needs at least 12 GiB RAM and 4 vCPUs`, the browser
has not started and no workflow network or cluster has been created. Earlier
versions inherited all resources from template 80 and could boot an undersized
VM. The current group config applies the capacity overrides at instantiation.
The diagnostic also reports the memory and vCPUs visible inside the guest.

Choose a new run directory and rerun the group command above. The new settings
do not resize a retained VM, and `--reuse` cannot apply them to a previously
failed group. The old VM remains available for inspection; remove it explicitly
with the existing `destroy --run-dir <old-run-directory>` command when no longer
needed. No old run metadata or workflow markers need to be deleted manually.

## OneKS Startup Failures

A refusal on `localhost:10780` means the OneKS API is not listening; it is
consistent with the miniONE appliance/startup race. Merely starting a unit is
not enough when it is already active but its API is unavailable. Setup now
restarts the unit on connection refusal and waits for a successful
`oneks list clusters --json` before recording its baseline or opening the browser.
Restart failures are bounded and the last systemd diagnostic is retained in the
guest-command log. For persistent failures, inspect `journalctl -u opennebula-ks`
and the appliance download/image status instead of repeatedly reprovisioning.

If this was the first setup failure and the guest log ends with
`No OneKS marker; nothing to clean up.`, no browser actions or OneKS resources
were created by this invocation. Retry only the capture against that installed
lab, for example:

```bash
RUN=.sunstone-screenshots/labs/oneks-20261023-151838
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots capture \
  tools/sunstone-screenshots/groups/oneks-quickstart/oneks_quickstart.json \
  --run-dir "$RUN" --output-root "$RUN/screenshots" \
  --debug --keep-open-on-failure --keep-sudo-alive
```

This does not reinstall miniONE or destroy the lab. It preserves the original
failed `workflow.json` and records the new attempt in
`screenshots/capture-results.json` for the review UI. Do not use this shortcut to
bypass ownership markers after a later, partially completed workflow.
