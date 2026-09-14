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

* Veeam - Fix multi-network workers. [#8025](https://github.com/OpenNebula/one/issues/8025).
* Veeam - Fix error fetching datacenters by ID. [#8049](https://github.com/OpenNebula/one/issues/8049).
* Veeam - Fix internal error when no credentials are provided. [#8050](https://github.com/OpenNebula/one/issues/8050).
* Veeam - Fix internal error when credentials are incorrect. [#8051](https://github.com/OpenNebula/one/issues/8051).
* Veeam - Fix wrong capabilities for non-persistent disks. [#8052](https://github.com/OpenNebula/one/issues/8052).
* Veeam - Fix disk attachment fetch endpoint. [#8053](https://github.com/OpenNebula/one/issues/8053).
* Veeam - Fix wrong transfer URL. [#8054](https://github.com/OpenNebula/one/issues/8054).
* Veeam - Fix bug in poweroff endpoint. [#8059](https://github.com/OpenNebula/one/issues/8059).
* Veeam - Fix out-of-memory errors during uploads. [#8078](https://github.com/OpenNebula/one/issues/8078).
