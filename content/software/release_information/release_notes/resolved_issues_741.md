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
* New parameter `--keep-ha` for CLI command `onezone serversync`, which keeps local [RAFT configuration]({{% relref "frontend_ha.md#server-sync-ha" %}}).

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
* Fix TM migration cleanup with symlinked datastores [#7972](https://github.com/OpenNebula/one/issues/7972).
* Fix cmd_confinement leaking secrets passed via environment [#7823](https://github.com/OpenNebula/one/issues/7823).
* Fix live storage migration with NVRAM [#7770](https://github.com/OpenNebula/one/issues/7770).
* Fix attachment of XFS volatile disks [#7746](https://github.com/OpenNebula/one/issues/7746).
* Fix NFS automount with shared DS and TM_MAD_SYSTEM=ssh [#7758](https://github.com/OpenNebula/one/issues/7758).
* Fix metadata update after LVM persistent image resizing [#7427](https://github.com/OpenNebula/one/issues/7427).
* Fix Isolated CPUS input not updating when switching hosts [#7970](https://github.com/OpenNebula/one/issues/7970).
* Fix interactive LVM incremental backups with more than one dirty extent [#7962](https://github.com/OpenNebula/one/issues/7962)
* Fix parsing of internal Address Range, it will fail to create the network [#7974](https://github.com/OpenNebula/one/issues/7974)
* Fix backup retry after failure for Ceph storage [#7937](https://github.com/OpenNebula/one/issues/7937)
* Fix `vip.sh` return code, make the script more robust [#7980](https://github.com/OpenNebula/one/issues/7980)
* Fix false `POWEROFF` or `UNKNOWN` state after VM deploy [#7975](https://github.com/OpenNebula/one/issues/7975)
* Fix `one.image.restore` reporting success if authorization fails [#7991](https://github.com/OpenNebula/one/issues/7991)
* Fix `one.group.update`, `one.group.addadmin` and `one.group.deladmin` authorization levels [#7987](https://github.com/OpenNebula/one/issues/7987)
* Fix interactive LVM incremental backups with more than one dirty extent [#7962](https://github.com/OpenNebula/one/issues/7962).
* Fix the Virtual machine template form by setting the name to read-only [#7951](https://github.com/OpenNebula/one/issues/7951).
* Fix the Virtual Machine and Host tables by adding the cluster filter [#7994](https://github.com/OpenNebula/one/issues/7994).
* Fix interactive restores producing truncated images when trailing zeroed ranges are skipped during transfer [#8008](https://github.com/OpenNebula/one/issues/8008).
* Fix cluster quota generation in Sunstone [#7538](https://github.com/OpenNebula/one/issues/7538)
