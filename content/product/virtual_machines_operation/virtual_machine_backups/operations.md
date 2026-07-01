---
title: "VM Backup Operations"
linkTitle: "Operations"
date: "2025-02-17"
description:
categories:
pageintoc: "96"
tags:
weight: "2"
---

<a id="vm-backups-operations"></a>

<!--# Virtual Machine Backup Operations -->

## Overview

### Backup Operations

Backups can be operated in two modes:

- Single VM (described in this guide): Backup operations are defined and managed for a single VM. You can use this method to manage the backups of a few VMs.
- Backup Jobs are described in the [backup jobs guide]({{% relref "backup_jobs#vm-backup-jobs" %}}). They allow you to define backup operations involving multiple VMs and efficiently manage all the backups as a cohesive unit.

### Backup Types

OpenNebula supports two backup types:

- **Full**, each backup contains a full copy of the VM disks. Libvirt version >= 5.5 is required.
- **Incremental**, each backup contains only the changes since the last backup. Incremental backups track changes by creating checkpoints (disk block dirty-bitmaps) using QEMU/Libvirt. Libvirt version >= 7.7 is required.

Incremental backups of **qcow2** disks can use two different modes via the `INCREMENT_MODE` user setting:

- **CBT** (Changed Block Tracking). For each increment OpenNebula creates a block bitmap in the disk image to track which blocks have changed since the last backup.
- **SNAPSHOT**. OpenNebula tracks changes by creating a separate disk snapshot. This snapshot stores all disk changes since the last backup.

Also, for **RBD** disks (Ceph), FULL and INCREMENT backups are currently stored in a different way, although the difference should be transparent to the user:

- **Full** backups (`FORMAT=raw`) store the RBD export converted to a qcow2 file. The restore process involves converting it to a RAW file and importing it to the Ceph pool.
- **Incremental** backups (`FORMAT=rbd`) store the initial RBD export, as well as zero or more increment files, in the native format of Ceph exports (rbd export –export-format 2 / rbd export-diff). The restore process involves importing the initial export and applying the diff files in the same order, one by one.

{{< alert title="Note" type="info" >}}
The `INTERACTIVE` backup workflow is reserved for supported third-party integrations, such as the [OpenNebula-Veeam&reg; Backup Integration]({{% relref "../../../product/cluster_configuration/backup_system/veeam.md#vm-backups-veeam" %}}). It is not a standalone backup backend for users to configure directly. In this workflow, OpenNebula exposes the backup data through OneBEX and the external backup system pulls the data from the hypervisor.

For interactive backup integrations, OpenNebula supports:

- **Full interactive backups** for `qcow2` disks.
- **Incremental interactive backups** for `qcow2` disks using **CBT** mode only.

Interactive incremental backups do not support the `SNAPSHOT` increment mode.
{{< /alert >}}

### The Backup Process

VM backups can be taken live or while the VM is powered off. The operation comprises three steps:

- *Pre-backup*: Disks (or increments) are prepared for backup. When the VM is running the filesystems of the guest are frozen (see below) and temporal disks are created so the VM can continue its normal operation. Note: backups are taken at the same time for all the VM disks (qcow2/raw images) to guarantee **crash consistent backups**.
- *Backup*: The selected backup datastore handles the backup data. Standard backup datastores upload full disk copies or increments to the backup server. Supported backup integrations can use OneBEX to expose the data so an external backup system can pull it from the hypervisor.
- *Post-backup*: Cleans any temporal file in the hypervisor.

{{< alert title="Note" type="info" >}}
In order to save space in the backup system, RAW disk backups are converted and stored always in Qcow2 format.{{< /alert >}} 

## Limitations

- Incremental backups are only available for KVM and qcow2/RBD disks
- Live backups are only supported for KVM
- Attaching a disk to a VM that had an incremental backup previously made will yield an error. The –reset option for the backup operation is required to recreate a new incremental chain
- Incremental backups on VMs with disk or system snapshots is not supported
- `KEEP_LAST` option is not supported for Incremental backups of Ceph disks

## Preparing VMs for Backups

Before making backups you need to configure some aspects of the backup process (e.g., the backup mode). This can be done for VM templates or Virtual Machines.

### Backup Modes

OpenNebula provides three `FS_FREEZE` modes to control how the guest filesystem is handled before taking a backup. Choose the mode that best fits your workload and guest OS capabilities:

- **NONE**: Do not attempt any filesystem freeze. This is the fastest option and requires no guest-side support, but backups may only be crash-consistent (the same as powering off the VM abruptly). Use when guest-agent support is unavailable or when minimal disruption is required.

- **AGENT**: Use the guest agent to handle the filesystem inside the guest prior to backup. On Linux this typically uses the qemu guest agent or fsfreeze to freeze filesystems; on Windows the guest agent triggers the Volume Shadow Copy Service (VSS) to create application and filesystem-consistent snapshots (in this case VSS needs to be properly configured). `AGENT` is the recommended option when you need stronger consistency and the guest supports it.

- **SUSPEND**: Suspend (pause) the VM at the hypervisor level for the brief period of the backup pre-step. This guarantees a consistent on-disk state without relying on guest tools, but it pauses all guest activity and may impact running services.

### Virtual Machine Templates

You can configure backups in the VM Template, so every VM created will have a preconfigured backup setup. The following example shows a VM template with incremental backups configured:

```default
NAME   = "Template  - Backup"
CPU    = "1"
MEMORY = "2048"

DISK = [
  IMAGE_ID = "1" ]

BACKUP_CONFIG = [
  FS_FREEZE = "NONE",
  KEEP_LAST = "4",
  MODE = "INCREMENT" ]
```

To configure using the Sunstone GUI, select the **Backup** tab:

![template_cfg](/images/backup_template_cfg.png)

### Virtual Machines

For running VMs you can set (or update) backup configuration attributes through the `updateconf` API call or CLI command. For example, to configure a VM with the above settings, add the following attribute:

```default
$ onevm updateconf 0

BACKUP_CONFIG = [
   FS_FREEZE = "NONE",
   KEEP_LAST = "4",
   MODE = "INCREMENT"
]
...
```

You should be able to see the configuration of the VM by showing its information with `onevm show` command:

```default
$ onevm show 0

VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : alpine-0
USER                : oneadmin
GROUP               : oneadmin
STATE               : ACTIVE
LCM_STATE           : RUNNING

...

BACKUP CONFIGURATION
BACKUP_VOLATILE="NO"
FS_FREEZE="NONE"
INCREMENTAL_BACKUP_ID="-1"
KEEP_LAST="4"
LAST_INCREMENT_ID="-1"
MODE="INCREMENT"
```

To configure using the Sunstone GUI, click on the virtual machine, select the **Backup** tab and click on the **Backup config** button:

![vm_cfg](/images/backup_vm_configuration.png)

Sunstone will display the screen to update the VM Configuration.

![vm_cfg_tab](/images/backup_vm_configuration_tab.png)

<a id="vm-backups-selected-disks"></a>

### Selecting Disks for Backup

By default, a VM backup includes all disks that are eligible for backup. You can restrict the backup to a subset of VM disks by setting the `DISK_IDS` attribute in `BACKUP_CONFIG`.

The value is a comma-separated list of disk IDs from the VM `DISK` section. For example, to back up only disks `0` and `2`:

```default
$ onevm updateconf 0

BACKUP_CONFIG = [
   DISK_IDS = "0,2"
]
...
```

You can clear `DISK_IDS` by setting it to an empty value. A missing or empty `DISK_IDS` attribute means that all eligible disks are included in the backup:

```default
$ onevm updateconf 0

BACKUP_CONFIG = [
   DISK_IDS = ""
]
...
```

OpenNebula validates `DISK_IDS` when the backup configuration is updated. The value must contain valid non-negative integer disk IDs, and every disk ID must refer to a disk that can be backed up. Disks of type `SWAP`, `CDROM`, `RBD_CDROM`, and `FILESYSTEM` are not included in VM backups. Volatile `FS` disks are included only when `BACKUP_VOLATILE="YES"` is set.

For incremental backups, the effective disk set is part of the incremental chain. Changing `DISK_IDS`, changing `BACKUP_VOLATILE` so that the effective disk set changes, or attaching or detaching an eligible disk when all disks are selected resets the incremental chain. The next backup creates a new full base for the new disk set. If a disk listed in `DISK_IDS` is detached, OpenNebula removes that disk ID from the backup configuration and resets the chain.

<a id="vm-backups-selected-disks-restore"></a>

#### Restoring Selected Disk Backups

A backup that contains only selected disks cannot be restored as a complete VM, because it may not contain all disks needed to boot or reconstruct the original VM. To restore data from this type of backup, restore an individual disk that is part of the backup:

```default
$ oneimage restore -d default --disk_id 2 176
Image: 203
```

The disk ID must be present in the backup image metadata. You can check the backed up disk IDs with `oneimage show`; they are listed in the `BACKUP_DISK_IDS` section.

<a id="vm-backups-config-attributes"></a>

### Reference: Backup Configuration Attributes

| Attribute               | Description                                                                                                      |
|-------------------------|------------------------------------------------------------------------------------------------------------------|
| `BACKUP_VOLATILE`       | Perform backup of the volatile disks of the VM (default: `NO`)                                                   |
| `FS_FREEZE`             | Operation to freeze guest FS: `NONE` do nothing (default), `AGENT` use guest agent, `SUSPEND` suspend the domain |
| `KEEP_LAST`             | Only keep the last N backups (full backups or increments) for the VM (default: none)                             |
| `MODE`                  | Backup type `FULL` (default) or `INCREMENT`                                                                      |
| `INCREMENT_MODE`        | Incremental backup type `CBT` (default) or `SNAPSHOT`                                                            |
| `DISK_IDS`              | Comma-separated list of disk IDs to back up. Empty or missing means all eligible disks                            |
| `INTERACTIVE`           | Enable the OneBEX interactive workflow for supported backup integrations (default: `NO`)                          |
| `INCREMENTAL_BACKUP_ID` | For `INCREMENT` points to the backup image where increment chain is stored (read-only)                           |
| `LAST_INCREMENT_ID`     | For `INCREMENT` the ID of the last incremental backup taken (read-only)                                          |
| `LAST_BRIDGE`           | Hostname of the bridge host used to export the backup to the backup datastore                                    |

## Taking VM Backups

Backup actions may potentially take some time, leaving some resources in use for a long time. In order to make efficient use of resources, backups are planned by the OpenNebula scheduler [through the schedule actions interface]({{% relref "../virtual_machines/vm_instances#schedule-actions" %}}).

### One-shot Backups

You can take backups (one-shot) using the `onevm backup` operation (or the equivalent Sunstone action). The backup will use the configured attributes for the VM (e.g., `MODE`) and two additional arguments:

- **Datastore ID**: The datastore where the backup will be stored
- **Reset** (optional): When doing incremental backups, you can close the current active chain and create a new one by passing this flag

**Important**, only the `oneadmin` account can initiate backups directly, regular users needs to schedule the operation. See example:

```default
$ onevm backup --schedule now -d 100 0
VM 0: backup scheduled at 2022-12-01 13:28:44 +0000
```

Using Sunstone to take one-shot backup:

![vm_backup_action](/images/vm_backup_action.png)

After the backup is complete you should see the backup information in the VM details, as well as the associated backup image. For example:

```default
$ onevm show 0
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : alpine-0
USER                : oneadmin
GROUP               : oneadmin
STATE               : ACTIVE
LCM_STATE           : RUNNING

...

SCHEDULED ACTIONS
   ID ACTION  ARGS   SCHEDULED REPEAT   END STATUS
    0 backup   100 12/01 13:28             Done on 12/01 13:28
    1 backup   100 12/01 13:36             Done on 12/01 13:36

BACKUP CONFIGURATION
BACKUP_VOLATILE="NO"
FS_FREEZE="NONE"
INCREMENTAL_BACKUP_ID="1"
KEEP_LAST="4"
LAST_INCREMENT_ID="1"
MODE="INCREMENT"

VM BACKUPS
IMAGE IDS: 1
```

```default
$ oneimage show 1
IMAGE 1 INFORMATION
ID             : 1
NAME           : 0 01-Dec 13.36.56
USER           : oneadmin
GROUP          : oneadmin
LOCK           : None
DATASTORE      : RBackups
TYPE           : BACKUP
REGISTER TIME  : 12/01 13:36:56
PERSISTENT     : Yes
SOURCE         : 25f4b298
FORMAT         : raw
SIZE           : 172M
STATE          : rdy
RUNNING_VMS    : 1

PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : ---

IMAGE TEMPLATE

BACKUP INFORMATION
VM             : 0
TYPE           : INCREMENTAL

BACKUP INCREMENTS
 ID PID T SIZE                DATE SOURCE
  0  -1 F 172M      12/01 13:36:56 25f4b298
  1   0 I 0M        12/01 14:22:46 6968545c
```

The `SOURCE` attribute in the backup images (and increments) is an opaque reference to the backup in the backup system used by the datastore. For restic, this corresponds to the snapshot ID, for example:

```default
$ restic snapshots
repository d5b1499c opened (repository version 2) successfully, password is correct
ID        Time                 Host                                  Tags        Paths
-----------------------------------------------------------------------------------------------------------------
25f4b298  2022-12-01 13:36:51  ubuntu2204-kvm-local-6-5-e795-2.test  one-0       /var/lib/one/datastores/0/0/backup
6968545c  2022-12-01 14:22:44  ubuntu2204-kvm-local-6-5-e795-2.test  one-0       /var/lib/one/datastores/0/0/backup
-----------------------------------------------------------------------------------------------------------------
```

**Note**: with the restic driver each snapshot is labeled with the VM id in OpenNebula.

### Scheduling Backups

You can program periodic backups [through the schedule actions interface]({{% relref "../virtual_machines/vm_instances#schedule-actions" %}}). Note that in this case, you have to pass the target datastore ID as argument of the action. You can create a periodic backup with the `--schedule` option in the CLI, or through Sunstone in the Schedule Action dialog (to open the dialog, click the Sched Actions tab then click Add action).

![vm_schedule](/images/backup_schedule.png)

**Note**: As with any other schedule action, you can plan for several backup operations or add a pre-set backup schedule in the VM template.

<a id="vm-backups-scheduler"></a>

### Reference: Scheduler Backup Attributes

The schedule actions are in control of OpenNebula core. You can tune the number of concurrent backup operations with the following parameters in `/etc/one/oned.conf`

| Attribute          | Description                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------------|
| `MAX_BACKUPS`      | Max active backup operations in the cloud. No more backups will be started beyond this limit. |
| `MAX_BACKUPS_HOST` | Max number of backups per Host                                                                |

### Cancel Backup

You can cancel an ongoing backup operation by using the `onevm backup-cancel`. The command will try to gracefully terminate backup operation. If the command succeeds the VM will return to running (or poweroff) state. Note that not all stages of the backup operation can be canceled and some files may be left on the VM folder in the system datastore. These files will be cleaned up during a subsequent backup.

If the backup operation is not running but the VM stays in the backup state, use command `onevm recover` to return the VM back to running state.

<a id="vm-backups-restore"></a>

## Restoring Backups

There are two main methods for restoring VM backups:

- In-place restore: This involves replacing the disks of the VM with a backup copy.
- Full restore: This process creates new disk images and templates. Unlike in-place restore, this operation doesn’t require the VM to exist beforehand.

### In-place Restore

In this mode, the disks of an existing VM are replaced with a copy from a backup. This operation requires that the VM is in a powered-off state. During the restoration process, you have the option to restore all disks or only the selected one.

For example, let’s consider a scenario with VM 83 in a powered-off state and an image backup (176) of this VM with three increments. It’s important to note that the VM remains powered off during this process:

```default
$ oneimage show 176
IMAGE 176 INFORMATION
ID             : 176

...

BACKUP INFORMATION
VM             : 83
TYPE           : INCREMENTAL

BACKUP INCREMENTS
 ID PID T SIZE                DATE SOURCE
  0  -1 F 173M      05/06 08:46:08 5f33de
  1   0 I 1M        05/06 08:52:05 a0c4eb
  2   1 I 1M        05/06 08:52:46 046843
```

and the corresponding VM:

```default
$ onevm show 83
VIRTUAL MACHINE 83 INFORMATION
ID                  : 83
NAME                : alpine-83

...

VM DISKS
 ID DATASTORE  TARGET IMAGE                               SIZE      TYPE SAVE
  0 default    vda    alpine                              173M/256M file   NO
  1 -          hda    CONTEXT                             1M/-      -       -

...

BACKUP CONFIGURATION
BACKUP_VOLATILE="NO"
FS_FREEZE="NONE"
INCREMENTAL_BACKUP_ID="176"
INCREMENT_MODE="CBT"
KEEP_LAST="4"
LAST_INCREMENT_ID="2"
MODE="INCREMENT"

VM BACKUPS
IMAGE IDS: 176

...
```

To restore all disks of the VM from the second increment (ID 1), simply execute:

```default
$ onevm restore --increment 1 83 176
```

Note that all snapshots of the VM will be deleted upon restoring the backup.

### Full Restore

When you perform a full restore of a VM backup, OpenNebula will create:

- A Virtual Machine Template, with an equivalent definition to that of the VM when the backup was taken (i.e., NICs, capacity…)
- A disk image for each of the disks stored in the backup.

Note that in this case the VM does not have to exist. This operation is not tied to the original VM where the backup was made.

When you restore the backup you may choose to:

- Not keep the NIC addressing (i.e., IPs, or MAC)
- Not keep any NIC definition
- In the case of incremental backups you can choose which increment to restore (or last by default)
- Pick a base name for the VM templates and disk Images that will be created
- Restore only an individual disk, without the associated VM template

After you restore the VM, we recommend reviewing the restored template to fine-tune any additional parameter. The following example shows the recovery procedure:

```default
$ oneimage restore -d default --no_ip 1
VM Template: 1
Images: 2
```

The API call returns the IDs of the images (2, in the example) and the ID of the VM template (1). As you see, images are named after the VM and snapshot in the form: `<VM_ID>-<SNAPSHOT_ID>-disk-<DISK_ID>`.

```default
$ oneimage show
IMAGE 2 INFORMATION
ID             : 2
NAME           : 0-6968545c-disk-0
USER           : oneadmin
GROUP          : oneadmin
LOCK           : None
DATASTORE      : default
TYPE           : OS
REGISTER TIME  : 12/01 15:03:33
PERSISTENT     : No
SOURCE         : /var/lib/one//datastores/1/d7784b595d33b757bb2593661346c51c
PATH           : restic://100/0:25f4b298,1:6968545c//var/lib/one/datastores/0/0/backup/disk.0
```

The complete list of attributes removed from a template are described in the table below:

#### VM Template attributes removed upon restore

| Attribute                    | Sub-attribute                                                                                             |
|------------------------------|-----------------------------------------------------------------------------------------------------------|
| `DISK`                       | `ALLOW_ORPHANS`, `CLONE`, `CLONE_TARGET`, `CLUSTER_ID`, `DATASTORE`, `DATASTORE_ID`                       |
|                              | `DEV_PREFIX`, `DISK_SNAPSHOT_TOTAL_SIZE`, `DISK_TYPE`, `DRIVER`, `IMAGE`, `IMAGE_ID`                      |
|                              | `IMAGE_STATE`, `IMAGE_UID`, `IMAGE_UNAME`, `LN_TARGET`, `OPENNEBULA_MANAGED`                              |
|                              | `ORIGINAL_SIZE`, `PERSISTENT`, `READONLY`, `SAVE`, `SIZE`, `SOURCE`, `TARGET`, `TM_MAD`, `TYPE`, `FORMAT` |
| `NIC`                        | `AR_ID`, `BRIDGE`, `BRIDGE_TYPE`, `CLUSTER_ID`, `NAME`, `NETWORK_ID`, `NIC_ID`                            |
|                              | `TARGET`, `VLAN_ID`, `VN_MAD`, `MAC`, `VLAN_TAGGED_ID`, `PHYDEV`                                          |
| `GRAPHICS`                   | `PORT`                                                                                                    |
| `CONTEXT`                    | `DISK_ID`, `ETH[0-9]*`, `PCI[0-9]*`                                                                       |
| `NUMA_NODE`                  | `CPUS`, `MEMORY_NODE_ID`, `NODE_ID`                                                                       |
| `PCI`                        | `ADDRESS`, `BUS`, `DOMAIN`, `FUNCTION`, `NUMA_NODE`, `PCI_ID`, `SLOT`, `VM_ADDRESS`                       |
|                              | `VM_BUS`, `VM_DOMAIN`, `VM_FUNCTION`, `VM_SLOT`                                                           |
| `AUTOMATIC_DS_REQUIREMENTS`  |                                                                                                           |
| `AUTOMATIC_NIC_REQUIREMENTS` |                                                                                                           |
| `AUTOMATIC_REQUIREMENTS`     |                                                                                                           |
| `VMID`                       |                                                                                                           |
| `TEMPLATE_ID`                |                                                                                                           |
| `TM_MAD_SYSTEM`              |                                                                                                           |
| `SECURITY_GROUP_RULE`        |                                                                                                           |
| `ERROR`                      |                                                                                                           |

## Advanced Configurations

### Quotas and Access Control

Backup Datastores follow the same datastore abstraction as the Image and System Datastore. Hence the same operations are supported for Backup Datastores. In particular you can easily set quotas to limit:

- The overall size that backups can take from the backup storage for a given group or user
- The number of backups a user can create (**Important**: increments counts just as a single backup)

In the same way, you can limit which backup datastore a given user or group can use by simply adjusting the permissions or, if you need a finer grain, by setting an ACL.

### Multi-tier Backup Policies (Full Backups)

If you are using `FULL` backups you can schedule backups in different servers (i.e., different datastores) using different schedules. For example:

- Schedule a backup in the Datastore “in-house” every Friday.
- Schedule a backup in the Datastore “cloud-storage” once every month.
