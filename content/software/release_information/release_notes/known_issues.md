---
title: "Known Issues"
date: "2025-10-06"
description:
categories:
pageintoc: "248"
tags:
weight: "6"
---

<a id="known-issues"></a>

<!--# Known Issues -->

Open accepted bug reports are tracked in [GitHub](https://github.com/OpenNebula/one/issues?q=is%3Aopen%20is%3Aissue%20type%3ABug%20label%3A%22Status%3A%20Accepted%22). Check each report for affected versions.

This page will be updated with relevant information about bugs affecting OpenNebula, as well as possible workarounds until a patch is officially published.

## VM Configuration

### Partial Updates Can Erase Secure Boot Configuration

Updating only part of a VM configuration with `onevm updateconf` without `--append` can [erase omitted configuration sections](https://github.com/OpenNebula/one/issues/8231), including attributes such as `OS/FIRMWARE_SECURE` that the command cannot restore. A VM can subsequently boot without Secure Boot.

Use `--append` for partial configuration updates and verify the resulting VM configuration before booting.

## VM Migration

### Recovery After a Failed Migration

A failed VM migration can leave OpenNebula's recorded [Host](https://github.com/OpenNebula/one/issues/7662) or [System Datastore](https://github.com/OpenNebula/one/issues/8040) inconsistent with the VM's actual location. After a migration fails, verify the VM's disk locations and hypervisor state before recovering it or attempting another migration.

Use `onevm recover --success` only after confirming that the operation completed. Forcing success after an incomplete transfer can cause subsequent migration cleanup to delete the remaining disk copy. See [Recover from VM Failure]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting.md#ftguide-virtual-machine-failures" %}}) for recovery options.

## Host Monitoring

### Long-Term Forecasting Can Block Monitoring

Long-term resource forecasting in OpenNebula 7.4 EE can [keep a KVM Host monitoring cycle busy for hours](https://github.com/OpenNebula/one/issues/8257). Host monitoring timestamps stop advancing while VM monitoring continues.

To prevent subsequent long-term calculations, set `enabled` to `false` under `host` > `forecast_far` in `/var/lib/one/remotes/etc/im/kvm-probes.d/forecast.conf`, preserving the other configuration values:

```yaml
host:
  forecast_far:
    enabled: false
```

Run `onehost sync --force` to distribute the configuration to the Hosts. This change does not stop a calculation that is already running.

## LVM Datastores

### Leftover Backup Snapshots After Upgrading to 7.4.2

Failed LVM backups in versions earlier than OpenNebula 7.4.2 can leave backup snapshots active. OpenNebula 7.4.2 [fixes failed-backup cleanup](https://github.com/OpenNebula/one/issues/8226). A subsequent successful backup cleans obsolete snapshots for the disks included in that backup. Upgrading the packages alone does not immediately remove existing snapshots.

Before migrating an affected VM, verify that its LVM thin pools are inactive on the destination Host. Migrating while its thin pool is active there can load stale metadata and cause guest data loss. After upgrading, run a new backup that includes the affected disks to clean their obsolete snapshots on the source Host.

### Image Imports Use `/var/tmp`

The LVM Image Datastore driver [ignores `STAGING_DIR`](https://github.com/OpenNebula/one/issues/8114) during image imports and writes the temporary image to `/var/tmp/one_img<ID>.<random>`. When `BRIDGE_LIST` is configured, this path is on the selected bridge Host. Otherwise, it is on the Front-end Host. This affects both RAW and QCOW2 image imports.

Before importing an image, ensure that `/var/tmp` on the applicable Host has enough free space for the complete image. A [failed or interrupted download](https://github.com/OpenNebula/one/issues/8187) can leave a partial `one_img...` file in `/var/tmp`. After confirming that no image import is using it, remove the stale file to recover the occupied space.

## Ceph Datastores

### Failed Image Imports Leave Temporary Files

Failed or interrupted image imports can [leave temporary files in `STAGING_DIR`](https://github.com/OpenNebula/one/issues/8187) on the selected bridge Host. QCOW2 conversions may require space for both the downloaded image and a RAW temporary copy.

Before retrying an import, check the staging directory on the bridge Host. Remove leftover files only after confirming that no active import uses them.

## NetApp Datastores

### Multiple Aggregates Cause Image Imports to Fail

Configuring more than one aggregate in `NETAPP_AGGREGATES` can [cause image imports to fail](https://github.com/OpenNebula/one/issues/8239). ONTAP creates a FlexGroup volume, and the subsequent LUN creation fails, sometimes with a misleading minimum-size error.

Configure a single aggregate UUID per datastore.

## PureFA Datastores

### Same-Host Transfers Can Leave Disk Links Missing

VM deployment from a PureFA datastore can [fail with a missing `disk.N` path](https://github.com/OpenNebula/one/issues/8222) when a disk link or clone operation has the same source and destination Host. The driver can report the transfer as successful without scanning for the device or creating its symlink.

Verify the device mapping and symlink before retrying deployment.

## Networking

### Overlapping Updates Can Fail

Network, port-mirroring, or Security Group updates can [fail for a VM while another NIC operation is in progress](https://github.com/OpenNebula/one/issues/8246), leaving the VM in `ERROR_VMS` with the requested change unapplied.

Avoid overlapping these operations. For failed Security Group updates, wait for the NIC operation to finish and retry with `onesecgroup commit <SG_ID> --recover`.

## LXC

### AppArmor Settings Prevent Deployment on RHEL 10

LinuxContainers Marketplace templates containing `lxc.apparmor.profile` can [fail to start on RHEL 10 Hosts](https://github.com/OpenNebula/one/issues/7391) because their LXC packages lack AppArmor support.

Remove this setting from the template's `RAW` section when deploying on these Hosts.

## Veeam Backups

### Missing `interactive` Datastore Configuration

Veeam worker deployment can fail if the required [`interactive` datastore driver configuration](https://github.com/OpenNebula/one/issues/8074) is missing from `/etc/one/oned.conf`, producing the following error:

```default
Datastore driver 'interactive' not available
```

Ensure that the `interactive` driver is included in the `DATASTORE_MAD` driver list under the `-d` option:

```default
DATASTORE_MAD = [
    EXECUTABLE = "one_datastore",
    ARGUMENTS  = "-t 15 -d dummy,fs,lvm,ceph,dev,iscsi_libvirt,restic,rsync,netapp,purefa,virtiofs,interactive -s dummy,lvm,shared,ssh,local,ceph,fs_lvm,fs_lvm_ssh,qcow2,netapp,purefa"
]
```

The corresponding `DS_MAD_CONF` entry must also be present:

```default
DS_MAD_CONF = [
    NAME = "interactive",
    REQUIRED_ATTRS = "",
    PERSISTENT_ONLY = "NO",
    DATASTORE_CAPACITY_CHECK = "NO"
]
```

After modifying `/etc/one/oned.conf`, restart OpenNebula:

```shell
systemctl restart opennebula
```

## OneSwap

### Conversions Fail When Preserving Guest IP Addresses

OneSwap conversions using `--network` can [fail with `undefined method '[]' for nil`](https://github.com/OpenNebula/one/issues/8237) when vCenter reports guest IP addresses and `--skip-ip` is not set. Imported Images and an added address range may remain after the failure.

As a workaround, use `--skip-ip` to skip importing IP addresses from vCenter, and configure the required addressing separately.

## Sunstone

### Disk Removal Disabled for Regular Users

In OpenNebula 7.4.2, Sunstone can [disable disk removal when a regular user edits a VM Template](https://github.com/OpenNebula/one/issues/8248), even when the disk attributes in the original template are not restricted. The check uses the extended template, which includes restricted attributes such as `ORIGINAL_SIZE`.

### Cleared VM Group Field Prevents Instantiation

Clearing the **VM Group** field after entering a value can [block VM instantiation with `VM Group ID must be a string type`](https://github.com/OpenNebula/one/issues/8250).

Cancel the instantiation wizard and start again, leaving the field untouched if no VM Group is required.

### Legacy Configuration Keys in Sunstone Views

Several Sunstone view files [use legacy action and tab keys](https://github.com/OpenNebula/one/issues/7766). These mismatches can hide or disable controls.

As a workaround, edit the affected files and replace the legacy action names in red with the updated names in green as follows, preserving all other existing entries. Paths are relative to `/etc/one/fireedge/sunstone/views/`:

* `/admin/backupjobs-tab.yaml`

  ```diff
  info-tabs:
    sched_actions:
      actions:
  -      sched_action_create: true
  -      sched_action_update: true
  -      sched_action_delete: true
  +      sched-add: true
  +      sched-update: true
  +      sched-delete: true
  ```

* `/cloud/vm-tab.yaml`

  ```diff
  actions:
  -  migrate_live: false
  +  live-migrate: false

  info-tabs:
    storage:
      actions:
  -      disk-attach:
  -        enabled: true
  +      disk-attach-image: true
  +      disk-attach-volatile: true
        disk-detach: true
        disk-resize: true
  -      disk_saveas:
  -        enabled: true
  +      disk-saveas: true
  ```

* `/groupadmin/group-tab.yaml`

  ```diff
  info-tabs:
  -  'VLAN Group':
  +  vlanrules:
      enabled: true
  ```

* `/groupadmin/vm-group-tab.yaml`

  ```diff
  info-tabs:
    info:
      ownership_panel:
        actions:
  -        cgrp: true
  +        chgrp: true
  ```

* `/groupadmin/vm-tab.yaml`

  ```diff
  actions:
  -  migrate_live: true
  +  live-migrate: true

  info-tabs:
    info:
      capacity_panel:
        actions:
  -        resize_capacity: true
  +        resize: true
    storage:
      actions:
  -      attach_disk:
  -        enabled: true
  +      disk-attach-image: true
  +      disk-attach-volatile: true
        disk-detach: true
  -      snapshot_disk_create: true
  -      snapshot_disk_rename: true
  -      snapshot_disk_revert: true
  -      snapshot_disk_delete: true
  -      resize_disk: true
  -      disk_saveas:
  -        enabled: true
  +      disk-snapshot-create: true
  +      disk-snapshot-rename: true
  +      disk-snapshot-revert: true
  +      disk-snapshot-delete: true
  +      disk-resize: true
  +      disk-saveas: true
    network:
      actions:
  -      attach_nic: true
  -      detach_nic: true
  -      update_nic: true
  -      attach_secgroup: true
  -      detach_secgroup: true
  +      nic-attach: true
  +      nic-detach: true
  +      nic-update: true
  +      sg-attach: true
  +      sg-detach: true
    sched_actions:
      actions:
  -      sched_action_create: true
  -      sched_action_update: true
  -      sched_action_delete: true
  +      sched-add: true
  +      sched-update: true
  +      sched-delete: true
        charter_create: true
  ```

After updating and saving the affected files, restart the FireEdge service:

```shell
systemctl restart opennebula-fireedge
```
