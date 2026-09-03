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

* Add new OneDRS block in Sunstone [#7783](https://github.com/OpenNebula/one/issues/7783)
* Assign deployed VMs to VM Groups in Sunstone [#4159](https://github.com/OpenNebula/one/issues/4159)
* Virtual Machine Command Execution. An optional [Exec tab]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances.md#executing-a-command-from-sunstone" %}}) lets users run, monitor, retry, and cancel commands inside Virtual Machines and copy their output directly from Sunstone.
* Edit permissions on update group form in Sunstone [#6394](https://github.com/OpenNebula/one/issues/6394)
* New parameter `--keep-ha` for CLI command `onezone serversync`, which keeps local [RAFT configuration]({{% relref "frontend_ha.md#server-sync-ha" %}})
* Log HA heartbeat and replication messages at log level 5 [#7977](https://github.com/OpenNebula/one/issues/7977).
* Option to configure network lease policy for internal Address Ranges. The policy can be set globally in [oned.conf]({{% relref "oned#virtual-networks" %}}).
* Extend Network PCI physical functions (PF) card control with link state management and flags in switchdev mode.
* Extend link state management for network Physical Functions when using Virtual Functions as PCI network interfaces.

## Resolved Issues
<!-- item structure
One line per issue starting with "Fix ...". Descrive the issue so the user understands the fix. Add link to GH. Example:

* Fix failure of `onegroup create` CLI command with empty `--resource` parameter [#7458](https://github.com/OpenNebula/one/issues/7458).
-->

The following issues have been solved in 7.4.1:

* Fix ARP tables not being updated on HA leader election [#7920](https://github.com/OpenNebula/one/issues/7920).
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
* Fix OneKS deployments in air-gapped environments by allowing appliance auto-import to be disabled and manually imported appliances to be discovered [#7984](https://github.com/OpenNebula/one/issues/7984).
* Fix false `POWEROFF` or `UNKNOWN` state after VM deploy [#7975](https://github.com/OpenNebula/one/issues/7975)
* Fix `one.image.restore` reporting success if authorization fails [#7991](https://github.com/OpenNebula/one/issues/7991)
* Fix `one.group.update`, `one.group.addadmin` and `one.group.deladmin` authorization levels [#7987](https://github.com/OpenNebula/one/issues/7987)
* Fix user quota corruption when `onevm recover --recreate` fails because of group quota limits [#7989](https://github.com/OpenNebula/one/issues/7989).
* Fix missing error details when MySQL database initialization fails [#2173](https://github.com/OpenNebula/one/issues/2173).
* Fix `onedb change-body` removing the `CDATA` enclosure from updated values [#3998](https://github.com/OpenNebula/one/issues/3998).
* Fix VLAN authorization being required when VLAN values remain unchanged [#7938](https://github.com/OpenNebula/one/issues/7938).
* Fix `one.vmgroup.add` allowing a VM to join more than one VM Group [#8016](https://github.com/OpenNebula/one/issues/8016).
* Fix VM configuration updates when the `CONTEXT` contains an unchanged `FILES_DS` value [#7732](https://github.com/OpenNebula/one/issues/7732).
* Fix quotes being retained in context file names by the local transfer driver [#8017](https://github.com/OpenNebula/one/issues/8017).
* Fix interactive LVM incremental backups with more than one dirty extent [#7962](https://github.com/OpenNebula/one/issues/7962).
* Fix the Virtual machine template form by setting the name to read-only [#7951](https://github.com/OpenNebula/one/issues/7951).
* Fix Backup Exporter service error reporting to cover additional error conditions [#8004](https://github.com/OpenNebula/one/issues/8004), [#7986](https://github.com/OpenNebula/one/issues/7986).
* Fix Sunstone Virtual Network tab to include inputs for SR-IOV `TRUST` and `SPOOFCHK` attributes [#7933](https://github.com/OpenNebula/one/issues/7933).
* Fix the Virtual Machine and Host tables by adding the cluster filter [#7994](https://github.com/OpenNebula/one/issues/7994).
* Fix blank page in the host NUMA tab when a physical CPU is assigned to a VM [#7969](https://github.com/OpenNebula/one/issues/7969).
* Fix allow RAW hypervisor VM configuration update [#7613](https://github.com/OpenNebula/one/issues/7613).
* Fix interactive restores producing truncated images when trailing zeroed ranges are skipped during transfer [#8008](https://github.com/OpenNebula/one/issues/8008).
* Fix persistent image creation when saving a VM as a template in Sunstone [#7425](https://github.com/OpenNebula/one/issues/7425).
* Fix cluster quota generation in Sunstone [#7538](https://github.com/OpenNebula/one/issues/7538)
* Fix missing VM monitoring section in Sunstone [#8014](https://github.com/OpenNebula/one/issues/8014)
* Fix customized `hooks/ft/fence_host.sh` being overwritten on upgrade. Fencing is now enabled by creating `fence_host.sh` from the shipped `fence_host.sh.example`, see [Enabling Fencing]({{% relref "vm_ha.md#enabling-fencing" %}}) [#7996](https://github.com/OpenNebula/one/issues/7996).
* Fix Prometheus datasource patching on systems with older Ruby versions [#7997](https://github.com/OpenNebula/one/issues/7997).
* Fix interactive backup cancellation while waiting for the external server to finish [#8009](https://github.com/OpenNebula/one/issues/8009).
* Fix custom timezone setting option [#7575](https://github.com/OpenNebula/one/issues/7575).
* Fix various graph related issues in Sunstone [#7571](https://github.com/OpenNebula/one/issues/7571).
* Fix current host and datastore selection in the Sunstone migration dialog [#7995](https://github.com/OpenNebula/one/issues/7995).
* Fix VM configuration update call in Sunstone [#7502](https://github.com/OpenNebula/one/issues/7502).
* Fix FS freeze for live Ceph backups [#8011](https://github.com/OpenNebula/one/issues/8011).
* Fix stale symlink after TM_MAD=shared persistent disk detach [#8000](https://github.com/OpenNebula/one/issues/8000).
* Fix the Add NIC form to include the DNS field [#7916](https://github.com/OpenNebula/one/issues/7916).
* Fix ovirtAPI issue with truncated disk UUIDs [#7965](https://github.com/OpenNebula/one/issues/7965).
* Fix floating-only Virtual Router NIC attachment exceeding network lease quotas [#8015](https://github.com/OpenNebula/one/issues/8015).
* Fix VM template instantiation when an SSH public key follows `$USER[SSH_PUBLIC_KEY]` on a new line [#7517](https://github.com/OpenNebula/one/issues/7517).
* Fix OVS access mode VLAN [#8028]https://github.com/OpenNebula/one/issues/8028.
* Fix OVS update when unsetting MTU [#8033](https://github.com/OpenNebula/one/issues/8033).
