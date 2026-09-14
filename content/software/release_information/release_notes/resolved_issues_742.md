---
title: "Resolved Issues in 7.4.2 (EE)"
date: "2026-11-01"
---

A complete list of solved issues for 7.4.2 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/95).

## Backported Features

The following new features have been backported to 7.4.2:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

## Resolved Issues

The following issues have been solved in 7.4.2:

<!-- item structure
One line per issue starting with "Fix ...". Descrive the issue so the user understands the fix. Add link to GH. Example:

* Fix failure of `onegroup create` CLI command with empty `--resource` parameter [#7458](https://github.com/OpenNebula/one/issues/7458).
-->
* Fix update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416).

---

## Updating Sunstone Configuration Files

After upgradte to 7.4.2, check the following settings to enable the new Sunstone functionality in the intended views. All paths below are relative to `/etc/one/fireedge/` on the OpenNebula Front-end Host.

Merge these settings into the existing YAML sections, preserving other settings and actions. Do not create duplicate `info-tabs` or `filters` keys.

### Update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416)

In `sunstone/tabs/40-networks-tab.yaml`, add the following content as part of `routes` attributes:

```yaml
    - title: Update Virtual Network Template
      path: /network-template/update
      Component: CreateVnTemplate
    - title: Update Security Group
      path: /security-group/update
      Component: CreateSecurityGroup
```

In `sunstone/tabs/60-systems-tab.yaml`, add the following content as part of `routes` attributes:

```yaml
    - title: Update Group
      path: /group/update
      Component: CreateGroup
```