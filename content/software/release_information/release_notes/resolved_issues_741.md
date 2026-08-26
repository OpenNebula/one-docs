---
title: "Resolved Issues in 7.4.1 (EE)"
date: "2026-10-01"
---

A complete list of solved issues for 7.4.1 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/94).

## Backported Issues

The following new features have been backported to 7.4.1:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

* Edit permissions on update group form in Sunstone [#6394](https://github.com/OpenNebula/one/issues/6394)

## Resolved Issues
<!-- item structure
One line per issue starting with "Fix ...". Descrive the issue so the user understands the fix. Add link to GH. Example:

* Fix failure of `onegroup create` CLI command with empty `--resource` parameter [#7458](https://github.com/OpenNebula/one/issues/7458).
-->

The following issues have been solved in 7.4.1:

* Fix VM configuration update call in Sunstone [#7502](https://github.com/OpenNebula/one/issues/7502).
* Fix Veeam not being able to fetch VM with ID 0 [#7949](https://github.com/OpenNebula/one/issues/7949).
* Fix ARP tables not being updated on HA leader election [#7935](https://github.com/OpenNebula/one/issues/7935).
* Fix repeated attributes in Cluster template [#7941](https://github.com/OpenNebula/one/issues/7941).
* Fix use of PCI NIC device for `onevm ssh` and `onevm port-forward` commands [#7925](https://github.com/OpenNebula/one/issues/7925).
* Fix preventing users from entering negative numbers in non-negative fields [#7135](https://github.com/OpenNebula/one/issues/7135).
* Fix incorrect ownership of templates saved from instances in Sunstone [#7393](https://github.com/OpenNebula/one/issues/7393)
* Fix "ACPI=yes" not being applied for some UEFI configurations [#7792](https://github.com/OpenNebula/one/issues/7792).
* Fix storage migrations to prevent Open vSwitch ports from being removed [#7947](https://github.com/OpenNebula/one/issues/7947).
* Fix Isolated CPUS input not updating when switching hosts [#7970](https://github.com/OpenNebula/one/issues/7970).
* Fix interactive LVM incremental backups with more than one dirty extent [#7962](https://github.com/OpenNebula/one/issues/7962).
* Fix the Virtual machine template form by setting the name to read-only [#7951](https://github.com/OpenNebula/one/issues/7951).
* Fix the Virtual Machine and Host tables by adding the cluster filter [#7994](https://github.com/OpenNebula/one/issues/7994).
* Fix interactive restores producing truncated images when trailing zeroed ranges are skipped during transfer [#8008](https://github.com/OpenNebula/one/issues/8008).
