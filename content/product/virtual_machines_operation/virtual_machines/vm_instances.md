---
title: "Virtual Machine Instances"
linkTitle: "Instances"
date: "2025-02-17"
description: "Manage Virtual Machine instances, including lifecycle operations, resources, snapshots, scheduled actions, and guest access."
categories:
pageintoc: "93"
tags:
weight: "3"
---

<a id="vm-guide-2"></a>

<a id="vm-instances"></a>

This guide describes how to manage Virtual Machine instances, including lifecycle operations, device and resource changes, snapshots, scheduled actions, and guest access. Use the `onevm` command or Sunstone to manage an instantiated VM. For instructions on creating and instantiating VM Templates, see the [Virtual Machine Templates guide]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates" %}}).

## Basic Virtual Machine Operations

### Creating and Listing VMs

{{< alert title="Note" type="info" >}}
For more information on managing and instantiating VM Templates, see the [Creating Virtual Machines guide]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates.md#vm-guide" %}}).{{< /alert >}}

{{< alert title="Note" type="info" >}}
For a complete description of VM Template attributes, see the [Virtual Machine Template reference]({{% relref "product/operation_references/configuration_references/template.md#template" %}}).{{< /alert >}}

To list the registered VM Templates, run:

```shell
onetemplate list
```

```default
ID USER     GROUP    NAME                         REGTIME
 6 oneadmin oneadmin vm-example            09/28 06:44:07
```

To instantiate the VM Template `vm-example` (ID `6`), run:

```shell
onetemplate instantiate vm-example --name my_vm
```

```default
VM ID: 0
```

If the Template defines [user inputs]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates.md#vm-guide-user-inputs" %}}), the CLI prompts you for their values:

```shell
onetemplate instantiate vm-example --name my_vm
```

```default
There are some parameters that require user input.
  * (BLOG_TITLE) Blog Title: <my_title>
  * (DB_PASSWORD) Database Password:
VM ID: 0
```

To list VMs, run `onevm list`. Use `onevm top` to refresh the list continuously.

```shell
onevm list
```

```default
ID USER     GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
 0 oneadmin oneadmin my_vm        pend   0      0K                 00 00:00:03
```

The scheduler automatically deploys the VM on a Host with enough available resources. To force deployment as `oneadmin`, use `onevm deploy`:

```shell
onehost list
```

```default
ID NAME               RVM   TCPU   FCPU   ACPU   TMEM   FMEM   AMEM   STAT
 2 testbed              0    800    800    800    16G    16G    16G     on
```

```shell
onevm deploy 0 2

onevm list
```

```default
ID USER     GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
 0 oneadmin oneadmin my_vm        runn   0      0K         testbed 00 00:02:40
```

To view the VM details, run:

```shell
onevm show 0
```

```default
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : my_vm
USER                : oneadmin
GROUP               : oneadmin
STATE               : ACTIVE
LCM_STATE           : RUNNING
...
```

<a id="vm-search"></a>

### Searching for VM Instances

To search for VM instances, use the `--search` option of `onevm list`. This is especially useful in large environments with many VMs. Use the filter format `VM.KEY1=VALUE1&VM.KEY2=VALUE2` to return VMs that match all conditions. The `&` operator acts as a logical AND. Use `*=VALUE` to search the full VM body or `VM.TEMPLATE=VALUE` to search the whole Template.

Searches use the JSON representation of the whole VM body. Specify a MySQL JSON path without the leading `$.`. For details on the path structure, see the [MySQL documentation](https://dev.mysql.com/doc/refman/5.7/en/json.html#json-path-syntax) or [MariaDB documentation](https://mariadb.com/kb/en/jsonpath-expressions/). OpenNebula wraps the value in `%`, so the query matches fields that contain the specified value.

The `VALUE` part of a search query supports these special characters:

* `%`: Matches any string, allowing for wildcard searches. For example, `a%a%a` matches names containing three “a”s in any position, with any number of characters between them.
* `_`: Matches any single character, enabling precise pattern matching. For instance, `a_a_a` matches names with three “a”s, each separated by exactly one character.
* `&`: Always acts as a logical AND operator. You cannot use it in `VALUE` or escape it.

To search for strings that contain `%` or `_` literally, escape these characters with a backslash `\`. For example:

* `a\%a` searches for the literal sequence `a%a`.
* `a\_a` matches `a_a` without interpreting `_` as a single-character wildcard.

To search for a VM with a specific MAC address, run:

```shell
onevm list --search 'VM.TEMPLATE.NIC[*].MAC=02:00:0c:00:4c:dd'
```

```default
ID    USER     GROUP    NAME    STAT UCPU UMEM HOST TIME
21005 oneadmin oneadmin test-vm pend    0   0K      1d 23h11
```

The command displays all matching VM instances. For example, to find VMs whose `NAME` contains `test-vm` and whose owner is `oneadmin`, run:

```shell
onevm list --search 'VM.NAME=test-vm&VM.UNAME=oneadmin'
```

```default
 ID    USER     GROUP    NAME     STAT UCPU UMEM HOST TIME
 21005 oneadmin oneadmin test-vm  pend    0   0K       1d 23h13
 2100  oneadmin oneadmin test-vm2 pend    0   0K      12d 17h59
```

{{< alert title="Warning" type="warning" >}}
This feature requires **MySQL 5.7.8** or later, or **MariaDB 10.2.0** or later. It is not available with the SQLite backend.{{< /alert >}}

### Terminating VM Instances

To terminate an instance, use `onevm terminate` when no conflicting operation is in progress. This command shuts down the VM if needed, deletes it, and frees its resources, such as Images and Virtual Networks. If an operation is stuck, see the [Virtual Machine Failures guide]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting.md#ftguide-virtual-machine-failures" %}}).

For a running instance, choose one of these options:

* `terminate`: Sends the ACPI signal to shut down and delete the VM gracefully. After the VM shuts down, OpenNebula cleans the Host and moves persistent and deferred-snapshot disks to the associated Datastore. If the VM is still running after the timeout, for example because the guest ignores ACPI signals, OpenNebula returns it to the `RUNNING` state.
* `terminate --hard`: Same as above but the VM is immediately destroyed. Use this action instead of `terminate` when the VM doesn’t have ACPI support.

### Pausing VM Instances

You can pause a VM for the short or long term. A *short-term pause* keeps all VM resources allocated to the Host so the VM can resume quickly on the same Host. Use these `onevm` commands or Sunstone actions:

* `suspend`: Saves the VM state on the running Host. When you resume the VM, OpenNebula restores its saved state on the same Host.
* `poweroff`: Gracefully powers off a running VM by sending the ACPI signal. It is similar to `suspend`, but does not save the VM state. When you resume the VM, it boots on the same Host.
* `poweroff --hard`: Same as above but the VM is immediately powered off. Use this action when the VM doesn’t have ACPI support.

{{< alert title="Note" type="info" >}}
When you shut down the guest from within the VM, OpenNebula puts the VM in the `POWEROFF` state.{{< /alert >}}

For a *long-term pause*, OpenNebula frees the VM's Host resources, cleans the Host, and saves the VM disk state in the System Datastore. Use these actions to preserve network and storage allocations, such as IP addresses and persistent disk Images:

* `undeploy`: Sends the ACPI signal to shut down a running VM gracefully and transfers its disks back to the System Datastore. When you resume an undeployed VM, OpenNebula moves it to the `PENDING` state and the scheduler chooses where to deploy it again.
* `undeploy --hard`: Same as above but the running VM is immediately destroyed.
* `stop`: Same as `undeploy` but also the VM state is saved to resume it later.

To resume a paused VM, use:

* `resume`: Resumes VMs in the `STOPPED`, `SUSPENDED`, `UNDEPLOYED`, and `POWEROFF` states.

### Rebooting VM Instances

Use the following commands to reboot a VM:

* `reboot`: Gracefully reboots a running VM, sending the ACPI signal.
* `reboot --hard`: Performs a hard reboot.

### Delaying VM Instances

To delay deployment of a `PENDING` VM, for example after creating or resuming it, use:

* `hold`: Sets the VM to the `HOLD` state. The scheduler does not deploy VMs in this state. To create a VM directly on hold, use `onetemplate instantiate <template> --hold` or `onevm create <file> --hold`.

To allow the scheduler to deploy the VM, use:

* `release`: Moves a VM from `HOLD` to `PENDING`. You can schedule this action to release a VM automatically, as explained below.

<a id="disk-hotplugging"></a>

<a id="hotplug-devices-to-a-virtual-machine"></a>

## Hot-plugging Devices to a Virtual Machine

{{< alert title="Warning" type="warning" >}}
Hot-plugging might not be available for every supported hypervisor. Before using it, check the limitations of your virtualization driver.{{< /alert >}}

<a id="disk-hot-plugging"></a>

### Hot-plugging Disks

To attach or detach disks on running VMs, use `onevm disk-attach` or `onevm disk-detach`. For example, to attach the Image named `storage` to a running VM, run:

```shell
onevm disk-attach one-5 --image storage
```

To detach a disk from a running VM, find its disk ID with `onevm show --all`, then run `onevm disk-detach <VM_ID> <DISK_ID>`:

```shell
onevm show one-5 --all
```

```default
...
DISK=[
  DISK_ID="1",
...
  ]
...
```

```shell
onevm disk-detach one-5 1
```

<a id="vm-guide2-nic-hotplugging"></a>

<a id="nic-hot-plugging"></a>

### Hot-plugging NICs

You can hot-plug network interfaces to VMs in the `RUNNING` or `POWEROFF` states. Specify the Virtual Network for the new interface:

```shell
onevm show 2
```

```default
VIRTUAL MACHINE 2 INFORMATION
ID                  : 2
NAME                : centos-server
STATE               : ACTIVE
LCM_STATE           : RUNNING

...

VM NICS
ID NETWORK      VLAN BRIDGE   IP              MAC
 0 net_172        no vbr0     172.16.1.201    02:00:ac:10:0

...
```

```shell
onevm nic-attach 2 --network net_172
```

After the operation, run `onevm show` again. You should see two NICs, with IDs `0` and `1`:

```shell
onevm show 2
```

```default
VIRTUAL MACHINE 2 INFORMATION
ID                  : 2
NAME                : centos-server
STATE               : ACTIVE
LCM_STATE           : RUNNING

...


VM NICS
ID NETWORK      VLAN BRIDGE   IP              MAC
 0 net_172        no vbr0     172.16.1.201    02:00:ac:10:00:c9
                              fe80::400:acff:fe10:c9
 1 net_172        no vbr0     172.16.1.202    02:00:ac:10:00:ca
                              fe80::400:acff:fe10:ca
...
```

You can also attach PCI and SR-IOV interfaces, including while the VM is running. Select the device by its address, ID, vendor, or class:

```shell
onevm nic-attach 2 --network net_172 --pci '00:06.1'
```

PCI hotplug support and guest addresses depend on the VM's machine type and PCI topology. For KVM q35 VMs, configure the PCIe topology before starting the VM; see `Q35_ROOT_PORTS` and `Q35_NUMA_PCIE` in the [KVM driver defaults]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver.md#kvmg-default-attributes" %}}).

To detach a NIC, specify its ID. For example, to detach interface `1` (MAC `02:00:ac:10:00:ca`), run:

```shell
onevm nic-detach 2 1
```

<a id="nic-update"></a>

### Updating NICs

To update NIC QoS attributes, use `onevm nic-update <VM_ID> <NIC_ID> [file]`. If the VM is running, the driver updates the network parameters while the VM runs.

Create `update_nic.txt` with this content:

```text
NIC = [
    INBOUND_AVG_BW = "512",
    INBOUND_PEAK_BW = "1024"
]
```

Review the file and apply the configuration:

```shell
cat update_nic.txt
onevm nic-update 0 0 update_nic.txt
```

If the file argument is omitted, the existing NIC configuration will be opened in an editor.

<a id="vm-guide2-sg-hotplugging"></a>

<a id="security-group-hot-plugging"></a>

### Hot-plugging Security Groups

You can attach or detach Security Groups while a VM is running. Specify the VM, NIC, and Security Group. For example, to attach a Security Group, run:

```shell
onevm sg-attach centos-server 0 101
```

To detach the Security Group, run:

```shell
onevm sg-detach centos-server 0 101
```

In Sunstone, you can attach or detach Security Groups on a running or powered-off VM. Open the **Network** tab, select the NIC, open its ellipsis menu, then select **Security Groups**:

{{< image
  pathDark="/images/virtual_machines/management/dark/vm_instance_security_groups.png"
  path="/images/virtual_machines/management/light/vm_instance_security_groups.png"
  alt="VM Instance Security Groups" align="center" width="90%" mb="20px"
>}}

To attach a new Security Group, click **Add Security Group** in the **Security Groups** dialog, then select an available group.

{{< image
  pathDark="/images/virtual_machines/management/dark/add_security_group.png"
  path="/images/virtual_machines/management/light/add_security_group.png"
  alt="VM Instance Security Groups" align="center" width="90%" mb="20px"
>}}

To detach a Security Group, click **Trash** next to the group, then confirm the action.

<a id="vm-guide2-pci"></a>

<a id="pci-devices"></a>

### Attaching and Detaching PCI Devices

You can attach or detach PCI devices when the VM is in the `POWEROFF` or `UNDEPLOYED` state. For example:

```shell
onevm pci-attach alpine01 --pci_class 0c03 --pci_device 0015 --pci_vendor 1912
onevm pci-detach alpine01 0
```

<a id="vm-guide2-snapshotting"></a>

## Virtual Machine System Snapshots

{{< alert title="Warning" type="warning" >}}
Snapshotting might not be available for every supported hypervisor. Before using it, check the limitations of your virtualization driver.

A system snapshot contains the current disk and memory state. You can create, delete, and restore snapshots for running VMs.{{< /alert >}}

```shell
onevm snapshot-create 4 "just in case"

onevm show 4
```

```default
...
SNAPSHOTS
  ID         TIME NAME                                           HYPERVISOR_ID
   0  02/21 16:05 just in case                                   onesnap-0
```

```shell
onevm snapshot-revert 4 0 --verbose
```

```default
VM 4: snapshot reverted
```

{{< alert title="Warning" type="warning" >}}
For KVM snapshots, all VM disks must use the [`qcow2` driver]({{% relref "product/operation_references/configuration_references/img_template.md#img-template" %}}).{{< /alert >}}

<a id="vm-guide-2-disk-snapshots"></a>

## Virtual Machine Disk Snapshots

Disk snapshots support two types of operations:

* `disk-snapshot-create`, `disk-snapshot-revert`, `disk-snapshot-delete`, and `disk-snapshot-rename`: Create, restore, delete, or rename disk snapshots during the VM lifecycle.
* `disk-saveas`: Export a VM disk or an existing snapshot to an Image in an OpenNebula Datastore. This is a live action.

{{< alert title="Warning" type="warning" >}}
Disk snapshot limitations depend on the hypervisor. Before using snapshots, check the limitations of your virtualization driver.{{< /alert >}}

<a id="vm-guide-2-disk-snapshots-managing"></a>

### Managing Disk Snapshots

Use disk snapshots to create checkpoints of a disk's state. Depending on the storage backend, snapshots use one of these structures:

- Tree: Every snapshot has a parent, except for the first snapshot, whose parent is `-1`. The active snapshot, which you last created or restored, becomes the parent of the next snapshot. Deletion rules depend on the storage backend and its `ALLOW_ORPHANS` mode.
- Flat: Snapshots have no parent/child relationship and can be freely removed.

To manage disk snapshots, use these commands:

- `disk-snapshot-create <VM_ID> <DISK_ID> <name>`: Create a snapshot of the specified disk.
- `disk-snapshot-revert <VM_ID> <DISK_ID> <SNAPSHOT_ID>`: Restore the disk to the specified snapshot. Snapshots are immutable, so restoring the same snapshot always returns the disk to the state captured when you created it.
- `disk-snapshot-delete <VM_ID> <DISK_ID> <SNAPSHOT_ID>`: Delete a snapshot subject to the storage backend's constraints. With `ALLOW_ORPHANS=MIXED`, the snapshot must have no children and must not be active. With `ALLOW_ORPHANS=NO`, you can also delete active leaf snapshots and some snapshots with a single child, but cannot delete snapshot `0` of a persistent disk.

You can run `disk-snapshot-create` when the VM is in the `RUNNING` state if the drivers support it, or in `POWEROFF` or `SUSPENDED`. To run `disk-snapshot-revert`, the VM must be in `POWEROFF`. These KVM storage combinations support live snapshots:

- KVM (`VM_MAD=kvm`) with `qcow2` Datastores (`TM_MAD=qcow2`): OpenNebula asks the hypervisor to run `virsh snapshot-create`.
- KVM (`VM_MAD=kvm`) with Ceph Datastores (`TM_MAD=ceph`): OpenNebula creates Ceph snapshots in the current volume.

With either combination, you can [enable QEMU Guest Agent]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver.md#enabling-qemu-guest-agent" %}}) to freeze the filesystem while creating the snapshot.

{{< alert title="Warning" type="warning" >}}
If the drivers do not support live `disk-snapshot-create`, suspend or power off the VM before creating the snapshot. Check the corresponding virtualization and storage driver guides for support and limitations. Reverting a disk snapshot always requires the VM to be powered off.{{< /alert >}}

For the driver actions used for live and non-live snapshots, see the [Storage Driver guide]({{% relref "product/integration_references/infrastructure_drivers_development/sd.md#sd-tm" %}}).

{{< alert title="Warning" type="warning" >}}
Live snapshot support can depend on `DISK/CACHE` and the installed storage driver, libvirt, and QEMU versions. Use a cache mode supported by that combination; `CACHE=writethrough` alone does not establish snapshot compatibility.{{< /alert >}}

### Persistent Images and Disk Snapshots

These actions support both persistent and non-persistent Images. For persistent Images, OpenNebula preserves snapshots after VM termination when the storage driver supports it and `PERSISTENT_SNAPSHOTS` is enabled. Other VMs using that Image can then use the snapshots. The `fs_lvm_ssh` driver sets `PERSISTENT_SNAPSHOTS=NO` by default. For more information, see [Snapshots]({{% relref "product/virtual_machines_operation/virtual_machines/images.md#images-snapshots" %}}) in the Images guide.

<a id="disk-save-as-action"></a>

### Saving a VM Disk to an Image (`disk-saveas`)

To save a VM disk to a new Image, use `disk-saveas` when the VM is in the `RUNNING`, `POWEROFF`, `SUSPENDED`, `UNDEPLOYED`, or `STOPPED` state. This live operation starts immediately. By default, it uses the current disk state. To use an existing disk snapshot instead, add `--snapshot <SNAPSHOT_ID>`.

{{< alert title="Warning" type="warning" >}}
This action is not synchronized with the hypervisor. Before running `disk-saveas` on a `RUNNING` VM, unmount the disk if possible, or sync or quiesce it.{{< /alert >}}

<a id="vm-guide2-resizing-a-vm"></a>

## Resizing VM Resources

You can resize a VM's virtual CPUs, memory, and allocated CPU capacity. Resize a VM in the `PENDING`, `HOLD`, `CLONING`, `CLONING_FAILURE`, `POWEROFF`, or `UNDEPLOYED` state, or with some limitations in the `RUNNING` state.

To increase a VM's resources, use this procedure:

- Prepare the VM for shutdown. For example, stop any services that require a manual shutdown.
- Power off the VM and wait until it reaches the `POWEROFF` state.
- Resize the VM.
- Resume the VM with the new capacity.

This procedure preserves resources assigned by OpenNebula, such as IP leases.

For example, power off the VM:

```shell
onevm poweroff web_vm
```

Poweroff is asynchronous. Use `onevm show web_vm` to check the state and wait until it is `POWEROFF`. Then resize the VM and resume it after the resize succeeds:

```shell
onevm resize web_vm --memory 2G --vcpu 2
onevm resume web_vm
```

<a id="live-resize-of-capacity"></a>

### Resizing a Running VM

To resize a VM in the `RUNNING` state, configure the required driver-specific VM Template attributes before starting the VM. For details, see [KVM Live Resize]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver.md#kvm-live-resize" %}}).

{{< alert title="Warning" type="warning" >}}
CPU hotplug is supported by KVM. CPU activation depends on the guest operating system. If a hot-added CPU remains offline in a Linux guest, bring it online as root with `echo 1 > /sys/devices/system/cpu/cpu<ID>/online`, replacing `<ID>` with its CPU number.{{< /alert >}}

<a id="vm-guide2-resize-disk"></a>

### Resizing VM Disks

To increase a VM disk's size at instantiation, set its `SIZE` attribute to a value larger than the source Image. Then:

- OpenNebula increases the disk container's size before launching the VM.
- With the [Context Packages]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates.md#context-overview" %}}) installed, supported guests can grow the filesystem at boot to use the new size. This depends on the guest OS, filesystem layout, and Context Package.

To override a disk's size when instantiating a VM Template, run:

```shell
onetemplate instantiate <template> --disk u2104:size=2048 # Resize the VM disk to 2 GiB if the source Image is smaller
```

To resize an existing VM disk, run this command when the VM is in the `RUNNING`, `POWEROFF`, or `UNDEPLOYED` state:

```shell
onevm disk-resize <VM_ID> <DISK_ID> <SIZE> # <SIZE> must be greater than current disk size
```

This grows the virtual disk. Expand the guest filesystem to use the additional space. Automatic expansion depends on the guest OS, filesystem layout, and Context Package. Start a powered-off or undeployed guest before its Contextualization Service can run. If automatic expansion is unavailable, expand the filesystem manually with the guest OS tools.

{{< alert title="Important" type="info" >}}
On FreeBSD, automatic expansion of the root filesystem is disabled in the Contextualization Service to avoid [filesystem corruption and data loss](https://github.com/OpenNebula/addon-context-linux/issues/298). After increasing the disk size, expand the filesystem mounted on `/` manually. Filesystems with other mount points can be expanded by the Contextualization Service.{{< /alert >}}

<a id="vm-updateconf"></a>

## Updating the Virtual Machine Configuration

To change a VM's configuration after creating it, use `onevm updateconf`. This command supports these VM Template attributes:

| Attribute       | Sub-attributes                                                                                                           |
|-----------------|--------------------------------------------------------------------------------------------------------------------------|
| `OS`            | `ARCH`, `MACHINE`, `KERNEL`, `INITRD`, `BOOTLOADER`, `BOOT`,<br/>`KERNEL_CMD`, `ROOT`, `SD_DISK_BUS`, `UUID`, `FIRMWARE`, `FIRMWARE_FORMAT` |
| `FEATURES`      | `ACPI`, `PAE`, `APIC`, `LOCALTIME`, `HYPERV`, `GUEST_AGENT`,<br/>`VIRTIO_SCSI_QUEUES`, `VIRTIO_BLK_QUEUES`, `IOTHREADS`, `GIC`, `RAS`,<br/>`MIGRATE_AUTO_CONVERGE`, `MIGRATE_COMPRESSED` |
| `INPUT`         | `TYPE`, `BUS`                                                                                                            |
| `GRAPHICS`      | `TYPE`, `LISTEN`, `PASSWD`, `KEYMAP`, `COMMAND`                                                                          |
| `VIDEO`         | `TYPE`, `IOMMU`, `ATS`, `VRAM`, `RESOLUTION`                                                                             |
| `RAW`           | `DATA`, `TYPE`, `VALIDATE`                                                                                               |
| `CPU_MODEL`     | `MODEL`, `FEATURES`                                                                                                      |
| `BACKUP_CONFIG` | `FS_FREEZE`, `KEEP_LAST`, `BACKUP_VOLATILE`, `MODE`,<br/>`INCREMENT_MODE`, `DISK_IDS`, `INTERACTIVE`                     |
| `CONTEXT`       | Any value, except `ETH*` by default. Variable substitution applies.                                                       |

Manual overrides of generated `ETH*` network context require `CONTEXT_ALLOW_ETH_UPDATES=YES` in `oned.conf`; the default is `NO`. Prefer updating the NIC configuration to keep it consistent with the generated network context.

For descriptions of these attributes, see the [Virtual Machine Template reference]({{% relref "product/operation_references/configuration_references/template.md#template" %}}). For all available methods, see the [VM Update Methods Reference]({{% relref "product/operation_references/configuration_references/vm_update_methods/" %}}).

{{< alert title="Warning" type="warning" >}}
Support for this action on `RUNNING` VMs depends on the hypervisor. Check the limitations of your virtualization driver.{{< /alert >}}

{{< alert title="Note" type="info" >}}
In the `RUNNING` state, changes to `CONTEXT` and `BACKUP_CONFIG` take effect immediately. Other values may require a VM restart. If a live context update fails, try triggering the action again.{{< /alert >}}

<a id="vm-guide2-clone-vm"></a>

## Cloning a Virtual Machine

You can copy a VM Template or VM instance to a new VM Template. This copy preserves changes to the VM disks after you terminate the instance. The new Template is private and appears only in its owner's list.

To create a persistent private copy of a VM, use either method:

- Instantiate a VM Template with the *to persistent* option.
- Save an existing VM instance with `onevm save`.

<a id="instantiate-to-persistent"></a>

### Instantiating to Persistent

When you *instantiate to persistent*, OpenNebula clones the Template recursively, creates a private persistent clone of each disk Image, and instantiates the new Template.

To instantiate to persistent, use `--persistent`:

```shell
onetemplate instantiate web_vm --persistent --name my_vm
```

```default
VM ID: 31
```

```shell
onetemplate list
```

```default
  ID USER            GROUP           NAME                                REGTIME
   7 oneadmin        oneadmin        web_vm                       05/12 14:53:11
   8 oneadmin        oneadmin        my_vm                        05/12 14:53:38
```

```shell
oneimage list
```

```default
  ID USER       GROUP      NAME            DATASTORE     SIZE TYPE PER STAT RVMS
   7 oneadmin   oneadmin   web-img         default       200M OS   Yes used    1
   8 oneadmin   oneadmin   my_vm-disk-0    default       200M OS   Yes used    1
```

To instantiate multiple persistent VMs, use both `-m N` and `--name`. You must provide `--name` when `-m` is greater than `1`. Include `%i` in the name to choose where to insert the VM index (`0` through `N-1`):

```shell
onetemplate instantiate web_vm -m 2 --persistent --hold --name 'test'
```

```default
VM ID: 0
VM ID: 1
```

```shell
onetemplate instantiate web_vm -m 2 --persistent --hold --name '%i-test'
```

```default
VM ID: 2
VM ID: 3
```

```shell
onevm list
```

```default
  ID USER         GROUP        NAME       STAT     CPU      MEM     HOST      TIME
   3 oneadmin     oneadmin     1-test     hold       1     768M           0d 00h00
   2 oneadmin     oneadmin     0-test     hold       1     768M           0d 00h00
   1 oneadmin     oneadmin     test-1     hold       1     768M           0d 00h00
   0 oneadmin     oneadmin     test-0     hold       1     768M           0d 00h00
```

In Sunstone, enable **Persistent** next to **Create**. Include `%i` in the name to choose where to insert the VM index (`0` through `N-1`).

Volatile disks cannot be persistent. When you terminate the VM, their contents are lost. The cloned VM Template contains the definition of an empty volatile disk.

<a id="save-a-vm-instance"></a>

### Saving a VM Instance

To save a VM that you did not create as persistent, power it off first, then use `onevm save` before terminating it.

This action clones the VM's source Template and replaces its disks with copies of the current VM disks; see the [`disk-saveas` action]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances.md#disk-save-as-action" %}}). If you resized the VM, the new Template uses its current capacity. To make the cloned Images persistent, add `--persistent`. The action also copies the VM instance's NICs to preserve any attach or detach changes.

```shell
onevm save web_vm copy_of_web_vm --persistent
```

```default
Template ID: 26
```

Keep these `onevm save` limitations in mind:

- The action uses the VM's source Template. If you updated it after instantiating the VM, the action uses the updated contents.
- Volatile disks cannot be saved, and their contents are lost. The cloned VM Template contains the definition of an empty volatile disk.
- The action retains disk and NIC configuration attributes except for generated allocation details, such as disk targets, IP addresses, and MAC addresses. Saved Image-backed disks reference their Images by ID.

<a id="vm-guide2-scheduling-actions"></a>

<a id="scheduled-actions-for-virtual-machines"></a>

## Scheduling Actions for Virtual Machines

Use scheduled actions to run VM operations in the future, such as shutting down a VM after five hours. OpenNebula supports two types of scheduled actions:

- Punctual actions, which run at a specified date and time and can repeat periodically.
- Relative actions, which run after a specified interval from VM instantiation.

<a id="one-time-punctual-actions"></a>

### Scheduling One-time Actions

Use `--schedule` with supported `onevm` commands to delay an action until a specified date and time. For example:

```shell
onevm suspend 0 --schedule "09/20"
```

```default
VM 0: suspend scheduled at 2016-09-20 00:00:00 +0200
```

```shell
onevm resume 0 --schedule "09/23 14:15"
```

```default
VM 0: resume scheduled at 2016-09-23 14:15:00 +0200
```

```shell
onevm show 0
```

```default
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : one-0

[...]

SCHEDULED ACTIONS
ID    ACTION  ARGS   SCHEDULED REPEAT   END STATUS
 0   suspend     - 09/20 00:00              Next in 12.08 days
 1    resume     - 09/23 14:15              Next in 15.67 days
```

To delete or edit an action, use `onevm sched-delete` or `onevm sched-update`. The time attributes use Unix time internally. To edit action 0 on VM 0, run:

```shell
onevm sched-update 0 0
```

The editor displays the action attributes:

```text
ID="0"
PARENT_ID="0"
TYPE="VM"
ACTION="suspend"
TIME="1703164454"
REPEAT="-1"
END_TYPE="-1"
END_VALUE="-1"
DONE="-1"
```

{{< alert title="Note" type="info" >}}
You cannot modify the OpenNebula system attributes `ID`, `PARENT_ID`, and `TYPE`. For editable attributes, see [Scheduled Action Template]({{% relref "product/operation_references/configuration_references/template.md#template-schedule-actions" %}}).{{< /alert >}}

<a id="periodic-punctual-actions"></a>

### Scheduling Periodic Actions

To schedule a periodic action, combine `--schedule` with an option that defines its frequency:

- `--weekly`: Run the action every week on the specified days.
- `--monthly`: Run the action every month on the specified days.
- `--yearly`: Run the action every year on the specified days.
- `--hourly`: Run the action at a specified interval in hours.

For `--weekly`, `--monthly`, and `--yearly`, specify day indexes separated by commas:

- `--weekly`: 0 (Sunday) through 6 (Saturday).
- `--monthly`: 1 through 31.
- `--yearly`: 0 through 365.

The option `--hourly` accepts an integer interval from 1 to 167 hours.

To set when the periodic action ends, use `--end` with either:

- A number, to specify the number of repetitions.
- A date, to specify the end date.

Here is a usage example for November 2026. The `onevm show` output assumes the actions are inspected on November 1 at 00:00 (+0100):

```shell
onevm suspend 0 --schedule "2026-11-02 00:00" --weekly "1,5" --end 5
```

```default
VM 0: suspend scheduled at 2026-11-02 00:00:00 +0100
```

```shell
onevm resume 0 --schedule "2026-11-03 14:15" --weekly "2,6" --end 5
```

```default
VM 0: resume scheduled at 2026-11-03 14:15:00 +0100
```

```shell
onevm snapshot-create 0 snap-01 --schedule "2026-11-03 00:00" --hourly 5 --end "2026-12-25"
```

```default
VM 0: snapshot-create scheduled at 2026-11-03 00:00:00 +0100
```

```shell
onevm show 0
```

```default
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : one-0

[...]

SCHEDULED ACTIONS
ID           ACTION     ARGS    SCHEDULED        REPEAT            END  STATUS
 0          suspend        -  11/02 00:00    Weekly 1,5  After 5 times  Next in 24.0 hours
 1           resume        -  11/03 14:15    Weekly 2,6  After 5 times  Next in 2.59 days
 2  snapshot-create  snap-01  11/03 00:00  Each 5 hours    On 12/25/26  Next in 2.0 days
```

To delete or edit a periodic action, use `onevm sched-delete` or `onevm sched-update`. The time attributes use Unix time internally. For example:

```shell
onevm sched-update 0 2
```

```text
ID="2"
PARENT_ID="0"
TYPE="VM"
ACTION="snapshot-create"
ARGS="snap-01"
TIME="1793660400"
REPEAT="3"
DAYS="5"
END_TYPE="2"
END_VALUE="1798153200"
DONE="-1"
```

<a id="relative-actions"></a>

### Scheduling Relative Actions

Define relative scheduled actions in a VM Template to run operations a specified number of seconds after VM instantiation. For example, add the following `SCHED_ACTION` to shut down VMs one hour after instantiation:

```shell
onetemplate update 0
```

```text
SCHED_ACTION=[
   ACTION="terminate",
   ID="0",
   TIME="+3600" ]
```

In Sunstone, create or update a VM Template, open the second step, **Advanced options**, and select the **Schedule Action** tab.

<a id="schedule-actions"></a>

The following table lists the actions you can schedule. Some actions require arguments, such as a disk ID or snapshot name.

| Action                 | Arguments           |
|------------------------|---------------------|
| `terminate [--hard]`   |                     |
| `undeploy [--hard]`    |                     |
| `hold`                 |                     |
| `release`              |                     |
| `stop`                 |                     |
| `suspend`              |                     |
| `resume`               |                     |
| `reboot [--hard]`      |                     |
| `poweroff [--hard]`    |                     |
| `snapshot-create`      | name                |
| `snapshot-revert`      | snap ID             |
| `snapshot-delete`      | snap ID             |
| `disk-snapshot-create` | disk ID, name       |
| `disk-snapshot-revert` | disk ID, snap ID    |
| `disk-snapshot-delete` | disk ID, snap ID    |
| `backup`               | datastore ID, reset |

To pass arguments to an action, set `ARGS` in the action definition. For example:

```shell
onevm sched-update 0 0
```

```text
ID="0"
PARENT_ID="0"
TYPE="VM"
ACTION="disk-snapshot-create"
ARGS="0, disksnap_example"
DAYS="1,5"
END_TYPE="1"
END_VALUE="5"
REPEAT="0"
TIME="1793574000"
```

In this example, the first argument identifies the disk, and the second specifies the snapshot name.

In the `sched-update` editor, put each attribute on a separate line without trailing commas. The CLI adds the separators when it constructs the scheduled action.

{{< alert title="Note" type="info" >}}
Arguments listed in the table are mandatory. The CLI and Sunstone generate them automatically for the actions.{{< /alert >}}

<a id="command-execution-inside-the-virtual-machine"></a>

## Executing Commands Inside a Virtual Machine

Before running commands, check the following prerequisites:

* Enable the QEMU Guest Agent communication channel in the VM Template by setting `GUEST_AGENT = "YES"` in `FEATURES`. Install and start the agent inside the VM. See [Enabling QEMU Guest Agent]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver.md#enabling-qemu-guest-agent" %}}) for more information.
* Check that the VM is in the `RUNNING` state.

OpenNebula sends commands to the VM through the QEMU Guest Agent and stores the results under `QEMU_GA_EXEC` in the VM template. The following diagram shows this process:

{{< image path="/images/vm_exec_architecture.svg" alt="Architecture Outlining How Command Execution Operates Within the VM" align="center" width="70%" mb="20px" border="false" >}}

The `vm/execution` monitor probe collects the results and updates the `QEMU_GA_EXEC` block. The `EXEC_VM` setting controls its interval. For configuration details, see [Monitoring System]({{% relref "product/cloud_system_administration/resource_monitoring/monitoring_system.md" %}}).

{{< alert title="Warning" type="warning" >}}
Run only one command at a time per VM. OpenNebula rejects new commands while the current command has `EXECUTING` status. This restriction also applies after the command finishes, until the monitor probe updates its status.{{< /alert >}}

### Execution Fields

The `QEMU_GA_EXEC` section in the VM template contains the following fields:

| Field         | Description                                                     |
|---------------|-----------------------------------------------------------------|
| `COMMAND`     | The command to be executed in the VM.                           |
| `STDIN`       | Standard input data passed to the command inside the VM.        |
| `PID`         | Process ID of the command inside the guest.                     |
| `RETURN_CODE` | Numeric exit code produced by the command (for example, `0` means success). |
| `STATUS`      | Execution state: `EXECUTING`, `CANCELLED`, `DONE` or `ERROR`.   |
| `STDOUT`      | Command standard output (base64-encoded).                       |
| `STDERR`      | Command standard error (base64-encoded).                        |

### Executing a Command from Sunstone

The **Exec** tab in the Virtual Machine details view lets you execute commands inside a VM from Sunstone. Enter a command in the **Command** field and click **Run**. The tab displays the execution status, return code, when the command was executed, and its standard output and standard error. You can also copy the output, re-run the last command, or cancel a command that is still running.

The prerequisites and restriction of one command at a time also apply in Sunstone. You must have `VM:MANAGE` permission for the VM.

{{< alert title="Note" type="info" >}}
The default Sunstone views do not enable the **Exec** tab. Enable it in each view where you need it.{{< /alert >}}

To enable the tab, add the following block under `info-tabs` in the `vm-tab.yaml` file of the corresponding [Sunstone view]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone.md#fireedge-sunstone-views" %}}):

```yaml
info-tabs:
  # Other information tabs

  exec:
    enabled: true
    actions:
      exec: true
      exec-retry: true
      exec-cancel: true
```

The standard view configuration files are:

* `/etc/one/fireedge/sunstone/views/admin/vm-tab.yaml`
* `/etc/one/fireedge/sunstone/views/cloud/vm-tab.yaml`
* `/etc/one/fireedge/sunstone/views/groupadmin/vm-tab.yaml`
* `/etc/one/fireedge/sunstone/views/user/vm-tab.yaml`

The `enabled` attribute controls whether Sunstone displays the **Exec** tab. Configure the actions independently: `exec` displays the command form and **Run** button, `exec-retry` displays the **Re-run** button, and `exec-cancel` displays the **Cancel** button while a command is running. An omitted action behaves as if it were set to `false`.

After modifying the view configuration, reload Sunstone in the browser to fetch the updated view.

### Executing a Command from the CLI

To execute a command inside a VM, use the `onevm exec` command. For example, to list files in VM 0:

```shell
onevm exec 0 'ls -l'
```

To check the command status, run:

```shell
onevm show 0
```

While the command is running, the template contains:

```default
VIRTUAL MACHINE TEMPLATE
...
QEMU_GA_EXEC=[
  COMMAND="ls -l",
  STDIN="",
  STATUS="EXECUTING" ]
```

After the command finishes, the monitor probe updates the details:

```default
VIRTUAL MACHINE TEMPLATE
...
QEMU_GA_EXEC=[
  COMMAND="ls -l",
  STDIN="",
  PID="3864",
  RETURN_CODE="0",
  STATUS="DONE",
  STDERR="",
  STDOUT="dG90Y..." ]
```

To rerun the last command, use `onevm exec-retry`:

```shell
onevm exec-retry 0
```

To cancel a running command, use `onevm exec-cancel`:

```shell
onevm exec-cancel 0
```

<a id="vm-life-cycle-and-states"></a>

## Virtual Machine States

The VM lifecycle includes the following states:

{{< alert title="Note" type="info" >}}
This table simplifies the lifecycle. For the complete diagram, see the [Virtual Machine States Reference]({{% relref "product/operation_references/configuration_references/vm_states.md#vm-states" %}}).{{< /alert >}}

| Short State | State | Meaning |
| --- | --- | --- |
| `pend` | `Pending` | By default, a new VM starts in `PENDING` and waits for resources. It remains in this state until the Scheduler deploys it or you deploy it with `onevm deploy`. |
| `hold` | `Hold` | The owner has held the VM. The Scheduler will not schedule it until you release it, but you can deploy it manually. |
| `clon` | `Cloning` | The VM is waiting for one or more disk images to finish the initial copy to the repository. The image state is still `lock`. |
| `prol` | `Prolog` | The system is transferring VM files, including disk images and the recovery file, to the target Host. |
| `boot` | `Boot` | OpenNebula is waiting for the hypervisor to create the VM. |
| `runn` | `Running` | The VM is running, including guest boot and shutdown phases. The virtualization driver monitors it periodically. |
| `migr` | `Migrate` | The VM is migrating to another resource. For live migration, it keeps running. For cold migration, OpenNebula saves or powers off the VM before transferring its files. |
| `hotp` | `Hotplug` | A disk or NIC attach/detach, save-as, resize, or exec operation is in progress. |
| `snap` | `Snapshot` | A system snapshot is being taken. |
| `save` | `Save` | The system is saving VM files during a migration, stop, or suspend operation. |
| `epil` | `Epilog` | During termination, the system cleans up the Host and returns disk images marked for saving to their Image Datastore. During stop or undeploy, VM files are transferred to the System Datastore. |
| `shut` | `Shutdown` | OpenNebula has sent the ACPI shutdown signal and is waiting for the guest to shut down. If the VM does not disappear before the timeout, OpenNebula assumes the guest OS ignored the signal and returns the VM to `RUNNING` instead of `DONE`. |
| `stop` | `Stopped` | The VM is stopped. OpenNebula has saved its state and transferred it, along with the disk images, to the System Datastore. |
| `susp` | `Suspended` | Like `STOPPED`, but VM files remain on the Host so you can resume the VM there without rescheduling it. |
| `poff` | `PowerOff` | Like `SUSPENDED`, but without a checkpoint file. VM files remain on the Host for the next boot. OpenNebula also uses this state when the guest shuts down. |
| `unde` | `Undeployed` | The VM is shut down, and its disks have been transferred to the System Datastore. You can resume the VM later. |
| `drsz` | `Disk Resize` | A VM disk resize is in progress. |
| `back` | `Backup` | A VM backup is in progress. |
| `rest` | `Restore` | The system is restoring VM disks from a backup image. |
| `fail` | `Failed` | The VM failed. |
| `unkn` | `Unknown` | OpenNebula cannot reach the VM, so its state is unknown. |
| `clea` | `Cleanup-resubmit` | The VM is waiting for the drivers to clean the Host after `onevm recover --recreate`. |
| `done` | `Done` | The VM has finished. `onevm list` omits VMs in this state, but the database retains them for accounting. Use `onevm show` to view their information. |

<a id="virtual-machine-datastore-migration"></a>

## Migrating VM Storage Between Datastores

Use datastore migration to move VM disk images and associated files between System Datastores. You can migrate storage for maintenance, balance disk I/O across storage tiers, evacuate hardware for decommissioning, or move a VM to a Host in another Cluster.

Depending on the state of the VM and the capabilities of the underlying storage drivers, OpenNebula supports two primary methods:

* **Cold Storage Migration**: A running VM is saved or powered off before its files are moved. VMs already in `POWEROFF` or `SUSPENDED` can also be migrated and retain their state afterward.

* **Live Storage Migration**: Performed while the VM is `RUNNING`. OpenNebula coordinates with the hypervisor to migrate the VM storage while the workload continues running.

{{< alert title="Note" type="info" >}}
Not all storage drivers support both cold and live datastore migration. Check the **Storage migration** column in the [Storage Portfolio]({{% relref "product/cluster_configuration/storage_system/overview.md#storage-portfolio" %}}) table for compatibility information.
{{< /alert >}}

### Basic Syntax

To migrate VM disks to another System Datastore, specify its ID when running `onevm migrate`:

```shell
onevm migrate [--live] <VM_ID> <TARGET_HOST_ID> <TARGET_DATASTORE_ID>
```

If the target Host is the same as the current one, only the datastore changes. If you also change the Host, both the Host and the datastore are migrated simultaneously, although changing both is only supported for offline migrations.

Cold and live migrations cannot cross different `TM_MAD` drivers, such as `ceph` and `lvm`.

<a id="cold-storage-migration"></a>

### Performing Cold Storage Migration

For a running VM, cold migration saves the execution state before transferring the VM files, then restores it after the transfer. OpenNebula uses the Transfer Manager to move the files from the source datastore to the destination datastore.

```shell
onevm migrate <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID>
```

You can also use `--poff` or `--poff-hard` to power off the VM during migration:

```shell
onevm migrate <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID> --poff
```

The Transfer Manager handles the file operations, including moving disk images and updating symlinks, through the `TM_MAD` scripts. For a VM that was running, OpenNebula restores the saved state, or boots the VM if `--poff` or `--poff-hard` was used. A VM that was already in `POWEROFF` or `SUSPENDED` remains in that state; use `onevm resume` when you want to start it.

VMs in `UNDEPLOYED` cannot use `onevm migrate`. Use `onevm deploy` with the desired Host and System Datastore instead.

<a id="live-storage-migration"></a>

### Performing Live Storage Migration

Live storage migration moves VM disks while the VM remains in `RUNNING`. OpenNebula coordinates with KVM to mirror disk writes to the new destination in real time.

```shell
onevm migrate --live <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID>
```

Live datastore migration uses `virsh blockcopy` on the same Host. OpenNebula copies read-only disks in raw format, such as CD-ROM images, then uses libvirt's `change-media` command to update their paths.

Live datastore migration has the following limitations:

* You cannot change both the Host and the System Datastore simultaneously. Perform these operations separately.
* **Disk snapshots** require the target System Datastore to support snapshot migration (`DS_MIGRATE_SNAP="YES"`). If the VM has disk snapshots and the driver does not support migrating them, OpenNebula rejects the migration. The default `shared`, `qcow2`, `ssh`, and `local` drivers support this capability.

<a id="migration-between-clusters"></a>

### Migrating Between Clusters

To migrate a VM between Hosts in different Clusters, make its resources available to the destination Cluster:

* Every Image Datastore used by the VM's disks must belong to the destination Cluster.
* Every Virtual Network used by the VM must belong to the destination Cluster, including networks attached through PCI NICs. NICs using `NETWORK_MODE="DUMMY"` are excluded from this requirement.
* If the VM kernel or initrd is provided by an OpenNebula File Datastore, that datastore must also belong to the destination Cluster.
* The System Datastore used after migration must be available to the destination Cluster. If you retain the current System Datastore, it must include the destination Cluster. If you select another System Datastore, it must use the same transfer driver (`TM_MAD`) and support datastore migration and any existing disk snapshots.
* Live migration between Clusters requires the VM's current System Datastore to be available to both the source and destination Clusters. The Host and System Datastore cannot both be changed in the same live migration operation.

A System Datastore with no Cluster associations is available to all Clusters for these checks.

<a id="vm-charter"></a>

<a id="virtual-machine-charters"></a>

## Creating Virtual Machine Charters

Charters add a configured set of scheduled actions to a VM. To enable Charter creation in Sunstone, add the following to `vm-tab.yaml` in the corresponding [Sunstone view]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone.md#fireedge-sunstone-views" %}}):

```yaml
info-tabs:
  sched_actions:
    enabled: true
    actions:
      charter_create: true
```

{{< image
  pathDark="/images/virtual_machines/management/dark/add_charter.png"
  path="/images/virtual_machines/management/light/add_charter.png"
  alt="VM Instance Charters" align="center" width="90%" mb="20px"
>}}

Next, define the Charter's scheduled actions in `sunstone-server.conf` in the [FireEdge configuration]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#fireedge-conf" %}}).

For example:

```yaml
leases:
  terminate:
    edit: false
    execute_after_weeks: 3
  poweroff:
    edit: true
    execute_after_minutes: 5
```

When you add a Charter to an existing VM, Sunstone calculates the delays from the time you open the Charter form. The example creates two scheduled actions:

- Terminate the VM three weeks after you open the Charter form. You cannot edit this action before creating it.
- Power off the VM five minutes after you open the Charter form. You can edit this action before creating it.

Charters configured in a VM Template use relative scheduled actions, with delays measured from VM instantiation.

Click **Charter** to open the form:

{{< image
  pathDark="/images/virtual_machines/management/dark/charter_info.png"
  path="/images/virtual_machines/management/light/charter_info.png"
  alt="VM Instance Charter Info" align="center" width="60%" mb="20px"
>}}

The first action is fixed. For the second action, you can change both the action and its time. Use the following attributes to configure a Charter:

| Attribute | Description |
| --- | --- |
| `edit` | Whether you can edit the action in the form. Accepts `true` or `false`. |
| `execute_after_<period_type>` | Delay before executing the action. `<period_type>` accepts years, months, weeks, days, hours, and minutes. For example, `execute_after_years: 2` sets a delay of 2 years, and `execute_after_months: 3` sets a delay of 3 months. For an existing VM, the delay starts when the Charter form is opened; for a VM Template, it starts at VM instantiation. |

To manage Charters from the CLI, use:

- `onevm create-chart`
- `onevm sched-update`
- `onevm sched-delete`

Add Charter definitions to the `onevm` configuration file, `/etc/one/cli/onevm.yaml`:

```yaml
:charters:
  :suspend:
    :time: "+1209600"
    :warning:
        :time: "+1123200"
  :terminate:
    :time: "+1209600"
    :warning:
        :time: "+1123200"
```

To view Charters, run `onevm show`. An asterisk (`*`) before an action ID means its warning time has passed:

```default
SCHEDULED ACTIONS
ID     ACTION     ARGS    SCHEDULED        REPEAT            END  STATUS
*0  suspend          -  01/01 03:00                               Next in 1.25 hours
 1  terminate        -  15/01 03:00                               Next in 14 days
```

<a id="vm-guide2-user-defined-data"></a>

<a id="user-defined-data"></a>

## Managing User-defined Data

Add custom attributes to store metadata for a VM instance. To view the existing template, run:

```shell
onevm show 0
```

```default
...

VIRTUAL MACHINE TEMPLATE
...
VMID="0"
```

To add attributes, run `onevm update`:

```shell
onevm update 0
```

Enter the attributes in the editor:

```text
ROOT_GENERATED_PASSWORD="1234"
```

To view the updated user template, run:

```shell
onevm show 0
```

```default
...

VIRTUAL MACHINE TEMPLATE
...
VMID="0"

USER TEMPLATE
ROOT_GENERATED_PASSWORD="1234"
```

<a id="virtual-machine-vm-permissions"></a>

## Managing Virtual Machine Permissions

Administrators can manage access through [ACL rules]({{% relref "product/cloud_system_administration/multitenancy/chmod.md#manage-acl" %}}). As a VM owner, you can also manage its [implicit permissions]({{% relref "product/cloud_system_administration/multitenancy/chmod.md#chmod" %}}). To share a VM or allow other users to list and view its information, use `onevm chmod`.

First, check the current permissions:

```shell
onevm show 0
```

```default
...
PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : ---
```

To grant the VM's group use permission, run:

```shell
onevm chmod 0 640
```

Check the updated permissions:

```shell
onevm show 0
```

```default
...
PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---
```

Administrators can also change the VM's group and owner with `onevm chgrp` and `onevm chown`.

<a id="life-cycle-ops-for-admins"></a>

## Advanced Operations for Administrators

Use the following `onevm` commands for administration tasks.

### Scheduling

- `resched`: Set the VM's reschedule flag. In the next monitoring cycle, the Scheduler migrates the VM to a Host that better matches its requirements and rank restrictions. Depending on the [Scheduler configuration]({{% relref "product/cloud_system_administration/scheduler/configuration.md" %}}), it can use live migration. For more information, see [Scheduling]({{% relref "product/cloud_system_administration/scheduler/_index.md" %}}).

- `unresched`: Clear the VM's reschedule flag to cancel rescheduling.

### Deployment

- `deploy`: Start an existing VM on a specific Host.
- `migrate --live`: Transfer a running VM to another Host, or migrate its storage to another System Datastore on the current Host when the driver supports live datastore migration. The Host and System Datastore cannot both be changed in one live migration.
- `migrate`: Migrate the VM to the target Host and, optionally, another System Datastore. A running VM is saved and restored; a VM already powered off or suspended retains its state.

By default, these operations do not check the target Host's capacity. Use `--enforce` to prevent overcommitting it.

### Troubleshooting

- `recover`: Recover a VM when an operation is stuck or boot fails. For details, see [Virtual Machine Failures]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting.md#ftguide-virtual-machine-failures" %}}). Use the following options:
  - `--success`: Simulate success of the missing driver action.
  - `--failure`: Simulate failure of the missing driver action.
  - `--retry`: Retry the current driver action. For a Transfer Manager problem, you can combine this with `--interactive`.
  - `--delete`: Delete the VM and move it to `DONE` immediately.
  - `--recreate`: Delete the VM and move it to `PENDING`.
- `migrate` or `resched`: Boot a VM in `UNKNOWN` on another Host, either manually with `migrate` or through the Scheduler with `resched`. Perform this action only when storage is shared or you have transferred it manually. OpenNebula does not move storage during this migration.

<a id="remote-access-sunstone"></a>

<a id="accessing-vm-console-and-desktop"></a>

## Accessing VM Consoles and Desktops

Use VNC, RDP, or SSH in Sunstone to access your VM's console or desktop. This section describes the requirements and configuration for each connection method.

[FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#fireedge-configuration" %}}) uses Guacamole for VNC, RDP, and SSH connections. The OpenNebula binary packages install the `opennebula-guacd` proxy daemon alongside FireEdge.

{{< alert title="Important" type="info" >}}
The [FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#fireedge-conf" %}}) server and its configured Guacamole proxy daemon must be running. The proxy must be able to reach the hypervisor's VNC port or the guest's RDP or SSH port, depending on the connection method. See [Configure Guacamole]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#configure-guacamole" %}}) for proxy configuration.
{{< /alert >}}

<a id="requirements-remote-access-sunstone"></a>

<a id="vnc-sunstone"></a>

<a id="configuring-your-vm-for-vnc"></a>

### Configuring VMs for VNC

VNC provides a graphical console supported by many hypervisors and clients.

To enable the VNC console service, add a `GRAPHICS` section to the VM Template.
Set `LISTEN` to an address on the hypervisor that the Guacamole proxy can reach.
The value `0.0.0.0` listens on all IPv4 interfaces; network and firewall rules must also permit the connection.

For example, add the following to the VM Template:

```text
GRAPHICS=[
    LISTEN="0.0.0.0",
    TYPE="vnc"
]
```

Your browser must support WebSockets and have them enabled.

To configure VNC in Sunstone, update the VM Template. In **Advanced options**, open the **Input/Output** tab. In the graphics section, set the IP address, port, connection password, and keymap as needed.

{{< image
  pathDark="/images/virtual_machines/management/dark/sunstone_guac_vnc.png"
  path="/images/virtual_machines/management/light/sunstone_guac_vnc.png"
  alt="VNC settings in the VM Template wizard" align="center" width="90%" mb="20px"
>}}

<a id="rdp-sunstone"></a>

<a id="configure-vm-for-rdp"></a>

### Configuring VMs for RDP

Remote Desktop Protocol (RDP) provides access to another computer's desktop over a network.

<a id="requirements-guacamole-rdp-sunstone"></a>

To enable RDP connections, set `RDP="YES"` on one `NIC` in the VM Template.

The guest must also have an RDP server enabled and allow connections from the Guacamole proxy to its RDP port (3389 by default). Setting `RDP="YES"` selects the connection interface; it does not enable the RDP service inside the guest.

In Sunstone, enable RDP before instantiation in the VM Template or when attaching a NIC to an existing VM. In the **Network** tab, select **Attach NIC** and enable **RDP**:

{{< image
  pathDark="/images/virtual_machines/management/dark/sunstone_nic_rdp.png"
  path="/images/virtual_machines/management/light/sunstone_nic_rdp.png"
  alt="RDP setting for a VM network interface" align="center" width="90%" mb="20px"
>}}

In the VM Template's advanced editor, add the attribute to the selected NIC:

```text
NIC=[
    ...
    RDP = "YES"
]
```

After instantiating the VM, open its actions menu (the ellipsis icon), then select **Console** > **RDP** to connect in your browser:

{{< image
  pathDark="/images/virtual_machines/management/dark/vm_rdp.png"
  path="/images/virtual_machines/management/light/vm_rdp.png"
  alt="RDP console action in Sunstone" align="center" width="90%" mb="20px"
>}}

You can choose the RDP screen resolution in Sunstone.

{{< image path="/images/sunstone_guac_rdp_interface.png" alt="Sunstone GUAC RDP interface" align="center" width="90%" mb="20px" >}}

{{< alert title="Important" type="info" >}}
Enable RDP on only one NIC. Sunstone uses the IP address of the first NIC with RDP enabled. NIC aliases work the same way.
{{< /alert >}}

Sunstone uses `PASSWORD` and `USERNAME` from the VM Template's `CONTEXT` section for the RDP connection, if set. See the [VM Template contextualization reference]({{% relref "product/operation_references/configuration_references/template.md#template-context" %}}).

{{< alert title="Note" type="info" >}}
On an English-language Windows guest, enable the Remote Desktop firewall rules from an elevated command prompt, or include the following in a start script that runs with administrative privileges:

```shell
netsh advfirewall firewall set rule group="remote desktop" new enable=yes
```

On other Windows language editions, use the corresponding localized firewall group name. This command opens the firewall rules; the guest's RDP service must also be enabled.
{{< /alert >}} 

<a id="requirements-guacamole-ssh-sunstone"></a>

<a id="configure-vm-for-ssh"></a>

### Configuring VMs for SSH

SSH provides a text console and requires the destination's hostname or IP address. As with [RDP]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances.md#requirements-guacamole-rdp-sunstone" %}}), enable SSH on one of the VM Template's network interfaces.

In the VM Template's advanced editor, add `SSH="YES"` to the selected NIC:

```text
NIC=[
    ...
    SSH = "YES"
]
```

SSH uses port 22 by default. To use another port, set `SSH_PORT` in the VM Template's `CONTEXT` section. The guest's SSH service must listen on that port and accept connections from the Guacamole proxy.

{{< alert title="Note" type="info" >}}
When `CONTEXT/SSH_PUBLIC_KEY` is absent, Sunstone uses `CONTEXT/USERNAME` and `CONTEXT/PASSWORD` for the SSH connection. When `CONTEXT/SSH_PUBLIC_KEY` is present, Sunstone uses the authenticated OpenNebula user's `SSH_PRIVATE_KEY` and optional `SSH_PASSPHRASE`. The private key must match a public key authorized in the guest. See the [VM Template contextualization reference]({{% relref "product/operation_references/configuration_references/template.md#template-context" %}}).
{{< /alert >}}

For password authentication, connect to the guest using an existing administrative account and a working authentication method, such as an [SSH key]({{% relref "product/control_plane_configuration/graphical_user_interface/cloud_view.md#cloudview-ssh-keys" %}}). Follow the guest operating system's instructions to configure the SSH service and account.

For example, on an Ubuntu guest with OpenSSH Server installed:

1. Create an account inside the guest. The command prompts for the new user's password:

   ```shell
   sudo adduser vmuser
   ```

2. Enable `PasswordAuthentication yes` in the guest's OpenSSH server configuration, accounting for any settings in `/etc/ssh/sshd_config.d/`. See the [Ubuntu OpenSSH Server configuration guide](https://documentation.ubuntu.com/server/how-to/security/openssh-server/).

3. Restart the SSH service inside the guest:

   ```shell
   sudo systemctl restart ssh.service
   ```

Use the guest account's username and password to connect through Sunstone. Other distributions may use a different SSH service name or account-creation procedure.

{{< image
  pathDark="/images/virtual_machines/management/dark/vm_ssh_dropdown.png"
  path="/images/virtual_machines/management/light/vm_ssh_dropdown.png"
  alt="SSH console action in Sunstone" align="center" width="90%" mb="20px"
>}}

The SSH console opens in another tab:

{{< image
  path="/images/virtual_machines/management/light/vm_ssh_console.png"
  alt="SSH console in Sunstone" align="center" width="90%" mb="20px"
>}}

{{< alert title="Note" type="info" >}}
SSH key and signature algorithm support depends on the Guacamole proxy and its SSH libraries. If SSH negotiation fails, check the Guacamole and guest SSH logs and verify that their supported algorithms overlap. An RSA key does not by itself require the legacy `ssh-rsa` (RSA/SHA-1) signature algorithm.
{{< /alert >}}

<a id="onevm-command"></a>

## The `onevm` Command

<a id="commands"></a>
<a id="args"></a>
<a id="options"></a>

The `onevm` command manages OpenNebula Virtual Machines. See the [`onevm` command reference](https://docs.opennebula.io/doc/{{< version >}}/cli/onevm.1.html) for its commands, arguments, and options, and the [Command Line Interface guide]({{% relref "product/operation_references/command_line_interface/cli" %}}) for related tools and CLI configuration.

To inspect the syntax and options available in your installed client, use the help option:

```shell
onevm --help
onevm disk-attach --help
```
