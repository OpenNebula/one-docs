---
title: "Resolved Issues in 7.4.1 (EE)"
date: "2026-09-09"
---

Issues tracked for 7.4.1 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/94?closed=1).

## Upgrading to 7.4.1

{{< alert title="Important" type="warning" >}}
OpenNebula 7.4.1 includes changes to the stock configuration files and ships `onecfg` migrators from 7.4.0 to 7.4.1. After upgrading the packages, you **must run** `onecfg upgrade` on the Front-end command line to migrate your configuration, as described in the [upgrade guide]({{% relref "software/upgrade_process/upgrade_guide/upgrading_single#step-7-update-configuration-files" %}}).

You may also need to update the Sunstone configuration files to expose the Sunstone features backported to 7.4.1, please see the [configuration instructions]({{% relref "software/release_information/release_notes/resolved_issues_741.md#updating-sunstone-configuration-files" %}}) at the end of this document.
{{< /alert >}}

## Backported Features

The following new features have been backported to 7.4.1:

<!-- item structure
Include a high-level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

* Add an [option to block OneDRS migrations]({{% relref "product/cloud_system_administration/scheduler/drs/#blocking-vm-migrations" %}}) in Sunstone [#7783](https://github.com/OpenNebula/one/issues/7783).
* Allow [assignment of deployed VMs to VM Groups]({{% relref "affinity#dynamic-vmg" %}}) in Sunstone [#4159](https://github.com/OpenNebula/one/issues/4159).
* Add an [Exec tab]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances.md#executing-a-command-from-sunstone" %}}) in Sunstone to run, monitor, retry, and cancel commands inside VMs and copy their output [#7559](https://github.com/OpenNebula/one/issues/7559).
* Allow [permissions editing when updating groups]({{% relref "manage_groups#manage-groups-permissions" %}}) in Sunstone [#6394](https://github.com/OpenNebula/one/issues/6394).
* Add support for creating and configuring [Restic backup datastores with AWS S3 and S3-compatible backends]({{% relref "product/cluster_configuration/backup_system/restic#sunstone" %}}) in Sunstone [#7906](https://github.com/OpenNebula/one/issues/7906).
* Add the `--keep-ha` option to `onezone serversync` to preserve the local [RAFT configuration]({{% relref "frontend_ha.md#server-sync-ha" %}}) [#7936](https://github.com/OpenNebula/one/issues/7936).
* Add an [option to log HA heartbeat and replication messages]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting/#configure-logging-system" %}}) at log level 5 [#7977](https://github.com/OpenNebula/one/issues/7977).
* Allow the default lease allocation policy for internal Address Ranges to be configured globally using `REUSE_ADDRESS` in [oned.conf]({{% relref "oned#virtual-networks" %}}) [#7971](https://github.com/OpenNebula/one/issues/7971).
* Add support for [OneKS deployments in air-gapped environments]({{% relref "platform_services/oneks/management/configuration/#air-gapped-environments" %}}) by allowing appliance auto-import to be disabled and manually imported appliances to be discovered [#7984](https://github.com/OpenNebula/one/issues/7984).
* Extend [PCI network Physical Function (PF) control]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces#legacy-and-switchdev-modes" %}}) to support PF flags in switchdev mode [#7679](https://github.com/OpenNebula/one/issues/7679).
* Bring up network [Physical Functions when using Virtual Functions]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces#physical-functions-and-virtual-functions" %}}) as PCI network interfaces, regardless of the SR-IOV mode [#7679](https://github.com/OpenNebula/one/issues/7679).

## Resolved Issues

The following issues have been resolved in 7.4.1:

* Fix Veeam VM creation and restoration failing when VM ID 0 does not exist. [#7949](https://github.com/OpenNebula/one/issues/7949).
* Fix ARP table updates during HA leader election on RHEL-based distributions [#7935](https://github.com/OpenNebula/one/issues/7935).
* Fix duplicate attributes in Cluster templates [#7941](https://github.com/OpenNebula/one/issues/7941).
* Fix the use of PCI NIC devices for `onevm ssh` and `onevm port-forward` commands [#7925](https://github.com/OpenNebula/one/issues/7925).
* Prevent negative values in numeric fields that require non-negative values [#7135](https://github.com/OpenNebula/one/issues/7135).
* Fix incorrect ownership of templates saved from instances in Sunstone [#7393](https://github.com/OpenNebula/one/issues/7393).
* Fix `ACPI=yes` not being applied for some UEFI configurations [#7792](https://github.com/OpenNebula/one/issues/7792).
* Fix storage migrations to prevent Open vSwitch ports from being removed [#7947](https://github.com/OpenNebula/one/issues/7947).
* Fix TM migration cleanup with symlinked datastores [#7972](https://github.com/OpenNebula/one/issues/7972).
* Fix `cmd_confinement` leaking secrets passed through environment variables [#7823](https://github.com/OpenNebula/one/issues/7823).
* Fix live storage migration with NVRAM [#7770](https://github.com/OpenNebula/one/issues/7770).
* Fix attachment of XFS volatile disks [#7746](https://github.com/OpenNebula/one/issues/7746).
* Fix NFS automount with shared datastores and `TM_MAD_SYSTEM=ssh` [#7758](https://github.com/OpenNebula/one/issues/7758).
* Fix metadata update after LVM persistent image resizing [#7427](https://github.com/OpenNebula/one/issues/7427).
* Fix the Isolated CPUs field not updating when switching Hosts [#7970](https://github.com/OpenNebula/one/issues/7970).
* Fix interactive LVM incremental backups with more than one dirty extent [#7962](https://github.com/OpenNebula/one/issues/7962).
* Reject invalid internal Address Ranges when creating a Virtual Network [#7974](https://github.com/OpenNebula/one/issues/7974).
* Fix backup retry after failure for Ceph storage [#7937](https://github.com/OpenNebula/one/issues/7937).
* Improve `vip.sh` error handling and return codes [#7980](https://github.com/OpenNebula/one/issues/7980).
* Fix false `POWEROFF` or `UNKNOWN` state after VM deployment [#7975](https://github.com/OpenNebula/one/issues/7975).
* Fix `one.image.restore` reporting success if authorization fails [#7991](https://github.com/OpenNebula/one/issues/7991).
* Fix `one.group.update`, `one.group.addadmin` and `one.group.deladmin` authorization levels [#7987](https://github.com/OpenNebula/one/issues/7987).
* Fix user quota corruption when `onevm recover --recreate` fails because of group quota limits [#7989](https://github.com/OpenNebula/one/issues/7989).
* Fix missing error details when MySQL database initialization fails [#2173](https://github.com/OpenNebula/one/issues/2173).
* Fix `onedb change-body` removing the `CDATA` enclosure from updated values [#3998](https://github.com/OpenNebula/one/issues/3998).
* Fix VLAN authorization being required when VLAN values remain unchanged [#7938](https://github.com/OpenNebula/one/issues/7938).
* Fix `one.vm.vmgroupadd` allowing a VM to join more than one VM Group [#8016](https://github.com/OpenNebula/one/issues/8016).
* Fix VM configuration updates when the `CONTEXT` contains an unchanged `FILES_DS` value [#7732](https://github.com/OpenNebula/one/issues/7732).
* Fix quotes being retained in context file names by the local transfer driver [#8017](https://github.com/OpenNebula/one/issues/8017).
* Make the VM Template name field read-only in Sunstone [#7951](https://github.com/OpenNebula/one/issues/7951).
* Fix Backup Exporter service error reporting to cover additional error conditions [#8004](https://github.com/OpenNebula/one/issues/8004), [#7986](https://github.com/OpenNebula/one/issues/7986).
* Fix Sunstone Virtual Network tab to include inputs for SR-IOV `TRUST` and `SPOOFCHK` attributes [#7933](https://github.com/OpenNebula/one/issues/7933).
* Fix the Virtual Machine and Host tables by adding the Cluster filter [#7994](https://github.com/OpenNebula/one/issues/7994).
* Fix blank page in the Host NUMA tab when a physical CPU is assigned to a VM [#7969](https://github.com/OpenNebula/one/issues/7969).
* Allow updates to the VM’s `RAW` hypervisor configuration in Sunstone [#7613](https://github.com/OpenNebula/one/issues/7613).
* Fix interactive restores producing truncated images when trailing zeroed ranges are skipped during transfer [#8008](https://github.com/OpenNebula/one/issues/8008), [#8036](https://github.com/OpenNebula/one/issues/8036).
* Fix persistent image creation when saving a VM as a template in Sunstone [#7425](https://github.com/OpenNebula/one/issues/7425).
* Fix Cluster quota generation in Sunstone [#7538](https://github.com/OpenNebula/one/issues/7538).
* Fix missing VM monitoring section in Sunstone [#8014](https://github.com/OpenNebula/one/issues/8014).
* Fix customized `hooks/ft/fence_host.sh` being overwritten on upgrade. Fencing is now enabled by creating `fence_host.sh` from the shipped `fence_host.sh.example`; see [Enabling Fencing]({{% relref "vm_ha.md#enabling-fencing" %}}) [#7996](https://github.com/OpenNebula/one/issues/7996).
* Fix Prometheus datasource patching on systems with older Ruby versions [#7997](https://github.com/OpenNebula/one/issues/7997).
* Fix interactive backup cancellation while waiting for the external server to finish [#8009](https://github.com/OpenNebula/one/issues/8009).
* Fix Sunstone’s custom time zone setting [#7575](https://github.com/OpenNebula/one/issues/7575).
* Fix VM monitoring graphs not refreshing in Sunstone [#7571](https://github.com/OpenNebula/one/issues/7571).
* Fix truncated Y-axis labels in Sunstone monitoring graphs when values contain multiple digits [#7572](https://github.com/OpenNebula/one/issues/7572).
* Fix forecast values distorting the Y-axis scale and making actual usage difficult to read in Sunstone monitoring graphs [#7573](https://github.com/OpenNebula/one/issues/7573).
* Fix current Host and datastore selection in the Sunstone migration dialog [#7995](https://github.com/OpenNebula/one/issues/7995).
* Fix VM configuration update call in Sunstone [#7502](https://github.com/OpenNebula/one/issues/7502).
* Fix filesystem freezing on the wrong Host during live Ceph backups [#8011](https://github.com/OpenNebula/one/issues/8011).
* Fix stale symlink after detaching a persistent disk with `TM_MAD=shared` [#8000](https://github.com/OpenNebula/one/issues/8000).
* Fix the Add NIC form to include the DNS field [#7916](https://github.com/OpenNebula/one/issues/7916).
* Fix disk UUIDs truncating VM IDs in oVirtAPI [#7965](https://github.com/OpenNebula/one/issues/7965).
* Fix floating-only Virtual Router NIC attachment exceeding network lease quotas [#8015](https://github.com/OpenNebula/one/issues/8015).
* Fix VM template instantiation when an SSH public key follows `$USER[SSH_PUBLIC_KEY]` on a new line [#7517](https://github.com/OpenNebula/one/issues/7517).
* Fix Open vSwitch access-only NICs allowing unrestricted VLAN trunk traffic [#8028](https://github.com/OpenNebula/one/issues/8028).
* Fix Open vSwitch port updates when the MTU is cleared [#8033](https://github.com/OpenNebula/one/issues/8033).
* Fix OneKS Cluster deployment to use the configured datastore [#8012](https://github.com/OpenNebula/one/issues/8012).
* Fix `opennebula-exporter` returning incomplete VM metrics when processing malformed VM data [#7781](https://github.com/OpenNebula/one/issues/7781).
* Improve VirtIO driver injection to prevent Windows blue-screen errors during OneSwap conversions [#7343](https://github.com/OpenNebula/one/issues/7343).
* Include OpenNebula API call errors in OneSwap logs [#7334](https://github.com/OpenNebula/one/issues/7334).
* Run `virt-v2v` commands with `sudo` where required by the operating system when using OneSwap [#7336](https://github.com/OpenNebula/one/issues/7336).
* Add warning about conflicting OVS VLAN configuration [#7658](https://github.com/OpenNebula/one/issues/7658).
* Fix PCI device list including devices from all Hosts in attach dialog in Sunstone [#7950](https://github.com/OpenNebula/one/issues/7950).
* Fix performance degradation from repeated column width calculations in Sunstone [#7946](https://github.com/OpenNebula/one/issues/7946).
* Fix `FireEdgetoken` generation for FireEdge remote authentication [#7730](https://github.com/OpenNebula/one/issues/7730).

---

## Updating Sunstone Configuration Files

After running `onecfg upgrade`, check the following settings to enable the new Sunstone functionality in the intended views. All paths below are relative to `/etc/one/fireedge/` on the OpenNebula Front-end Host.

Merge these settings into the existing YAML sections, preserving other settings and actions. Do not create duplicate `info-tabs` or `filters` keys.

### VM Group Assignment and Command Execution

In `sunstone/views/*/vm-tab.yaml`, enable the VM Group and Exec tabs under `info-tabs`. This change should be completed in the `vm-tab.yaml` file found in each of the various view directories found in `sunstone/views`, replacing the wildcard (`*`) in the path accordingly:

```yaml
info-tabs:
  vm_group:
    enabled: true
    actions:
      vmgroup-add: true
      vmgroup-del: true
  exec:
    enabled: true
    actions:
      exec: true
      exec-retry: true
      exec-cancel: true
```

### Date Format

To customize the displayed date format, set `dateFormat` in `sunstone/sunstone-server.conf`. For example:

```yaml
dateFormat: 'dd/MM/yyyy'
```

### Cluster Filters

In `sunstone/views/admin/host-tab.yaml` and the applicable `sunstone/views/*/vm-tab.yaml` files, enable the Cluster filter under `filters`:

```yaml
filters:
  cluster: true
```
