# Control Plane Basics

Draft single-node workflows for the next hardware-independent inventory pages:
OpenNebula Overview (dashboard) and Sunstone Labels (dropdown, Create New action,
and New Label dialog). Four captures produce eight light/dark images.

The group shares the standard public-release provisioning configuration from
getting-started, but provisions its own VM. Each page saves/restores the lab
oneadmin template using the existing theme hooks. The labels recipe selects
the existing `vnet` and opens the label dialog without submitting or applying
labels; no resource cleanup is required. Theme changes settle for one second.
The menu may initially contain no labels on a clean installation; populated
label examples can be added after the initial UI path has been validated.

Federation, Cloud View, Group Admin and Configuration remain pending. They are
not covered by this initial batch; role-specific and multi-zone prerequisites
need dedicated workflows. Diagrams in Overview are not browser captures.

```bash
RUN=".sunstone-screenshots/labs/control-plane-$(date +%Y%m%d-%H%M%S)"
sudo -v
tools/sunstone-screenshots/bin/sunstone-screenshots run-group \
  tools/sunstone-screenshots/groups/control-plane-basics/group.json \
  --run-dir "$RUN" --debug --keep-open-on-failure --keep-sudo-alive
```

The VM is destroyed after success and retained on failure. Recipe failures open
the interactive `recipe-debug>` prompt before teardown. The recipes are draft
until tested against the running release; selectors were checked against local
Sunstone source and existing recipes, not a live lab.

Review outputs with `sunstone-screenshots review --run-dir "$RUN" --port 0`.
