---
title: "Virtual Machine Instances"
linkTitle: "Instances"
date: "2025-02-17"
description:
categories:
pageintoc: "93"
tags:
weight: "3"
---

<a id="vm-guide-2"></a>

<a id="vm-instances"></a>

<!--# Managing Virtual Machines Instances -->

This guide may be considered a continuation of the [Virtual Machines Templates]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates" %}}) guide. Once a Template is instantiated to a Virtual Machine, there are a number of operations that can be performed using the `onevm` command.

## Basic Virtual Machine Operations

### Creating and Listing VMs

{{< alert title="Note" type="info" >}}
Read the [Creating Virtual Machines guide]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates#vm-guide" %}}) for more information on how to manage and instantiate VM templates.{{< /alert >}}

{{< alert title="Note" type="info" >}}
Read the complete reference for [Virtual Machine templates]({{% relref "product/operation_references/configuration_references/template#template" %}}).{{< /alert >}}

Assuming we have a VM template registered called **vm-example** with ID 6, then we can instantiate the VM by issuing a:

```shell
onetemplate list
ID USER     GROUP    NAME                         REGTIME
 6 oneadmin oneadmin vm_example            09/28 06:44:07
```
```shell
onetemplate instantiate vm-example --name my_vm
VM ID: 0
```

If the template has [USER INPUTS]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates#vm-guide-user-inputs" %}}) defined, the CLI will prompt the user for these values:

```shell
onetemplate instantiate vm-example --name my_vm
There are some parameters that require user input.
  * (BLOG_TITLE) Blog Title: <my_title>
  * (DB_PASSWORD) Database Password:
VM ID: 0
```

Afterwards, the VM can be listed with the `onevm list` command. You can also use the `onevm top` command to list VMs continuously.

```shell
onevm list
ID USER     GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
 0 oneadmin oneadmin my_vm        pend   0      0K                 00 00:00:03
```

The scheduler will automatically deploy the VM in one of the Hosts with enough resources available. The deployment can also be forced by oneadmin using `onevm deploy`:

```shell
onehost list
ID NAME               RVM   TCPU   FCPU   ACPU   TMEM   FMEM   AMEM   STAT
 2 testbed              0    800    800    800    16G    16G    16G     on

onevm deploy 0 2

onevm list
ID USER     GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
 0 oneadmin oneadmin my_vm        runn   0      0K         testbed 00 00:02:40
```

and details about it can be obtained with `show`:

```shell
onevm show 0
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : my_vm
USER                : oneadmin
GROUP               : oneadmin
STATE               : ACTIVE
LCM_STATE           : RUNNING
START TIME          : 04/14 09:00:24
END TIME            : -
DEPLOY ID:          : one-0

PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : ---

VIRTUAL MACHINE MONITORING
NET_TX              : 13.05
NET_RX              : 0
USED MEMORY         : 512
USED CPU            : 0

VIRTUAL MACHINE TEMPLATE
...

VIRTUAL MACHINE HISTORY
 SEQ        HOSTNAME REASON           START        TIME       PTIME
   0         testbed   none  09/28 06:48:18 00 00:07:23 00 00:00:00
```

<a id="vm-search"></a>

### Searching for VM Instances

You can search for VM instances by using the `--search` option of the `onevm list` command. This is especially useful on large environments with many VMs. The filter must be in a `VM.KEY1=VALUE1&VM.KEY2=VALUE2` format and will return all the VMs which fit the filter. The `&` works as logical AND. You can use `*=VALUE` to search the full VM body or `VM.TEMPLATE=VALUE` to search whole template.

Searching is performed using JSON on the whole body of the VM. You can use the MySQL JSON path without the leading `$.`, information about the path structure can be found in the [MySQL Documentation](https://dev.mysql.com/doc/refman/5.7/en/json.html#json-path-syntax) or [MariaDB Documentation](https://mariadb.com/kb/en/jsonpath-expressions/).  Currently, the value is wrapped in `%` for the query, so it will match if it contains the value provided.

The `VALUE` part of a search query can utilize special characters to create flexible matching patterns:

* `%`: Matches any string, allowing for wildcard searches. For example, `a%a%a` matches names containing three “a”s in any position, with any number of characters between them.
* `_`: Matches any single character, enabling precise pattern matching. For instance, `a_a_a` matches names with three “a”s, each separated by exactly one character.
* `&`: Cannot be used in the `VALUE` part of the search query, as it is always interpreted as logical AND operator and does not support escaping.

To search for strings that contain `%` or `_` literally, escape these characters with a backslash `\`. For example:

* `a\%a` will search for “a%a” as an exact sequence.
* `a\_a` will match “a_a” without interpreting `_` as a single-character wildcard.

For example, for to search for a VM with a specific MAC address:

```shell
onevm list --search 'VM.TEMPLATE.NIC[*].MAC=02:00:0c:00:4c:dd'
ID    USER     GROUP    NAME    STAT UCPU UMEM HOST TIME
21005 oneadmin oneadmin test-vm pend    0   0K      1d 23h11
```

Equivalently, if there is more than one VM instance that matches the result they will be shown. For example, VM's NAME containing a pattern and owned by oneadmin:

```shell
onevm list --search 'VM.NAME=test-vm&VM.UNAME=oneadmin'
 ID    USER     GROUP    NAME     STAT UCPU UMEM HOST TIME
 21005 oneadmin oneadmin test-vm  pend    0   0K       1d 23h13
 2100  oneadmin oneadmin test-vm2 pend    0   0K      12d 17h59
```

{{< alert title="Warning" type="warning" >}}
This feature is only available for **MySQL** backend with version **5.6** or later.{{< /alert >}} 

### Terminating VM Instances

You can terminate an instance with the `onevm terminate` command, from any state. It will shut down (if needed) and delete the VM. This operation will free the resources (images, networks, etc.) used by the VM.

If the instance is running, there is a `--hard` option that has the following meaning:

* `terminate`: Gracefully shuts down and deletes a running VM, sending the ACPI signal. Once the VM is shut down the Host is cleaned and persistent and deferred-snapshot disk will be moved to the associated datastore. If after a given time the VM is still running (e.g., guest ignoring ACPI signals), OpenNebula will return the VM to the `RUNNING` state.
* `terminate --hard`: Same as above but the VM is immediately destroyed. Use this action instead of `terminate` when the VM doesn’t have ACPI support.

### Pausing VM Instances

There are two different ways to temporarily stop the execution of a VM: *short* and *long* term pauses. A **short term** pause keeps all the VM resources allocated to the Hosts so it resumes its operation in the same Hosts quickly. Use the following `onevm` commands or Sunstone actions:

* `suspend`: the VM state is saved in the running Host. When a suspended VM is resumed, it is immediately deployed in the same Host by restoring its saved state.
* `poweroff`: Gracefully powers off a running VM by sending the ACPI signal. It is similar to suspend but without saving the VM state. When the VM is resumed it will boot immediately in the same Host.
* `poweroff --hard`: Same as above but the VM is immediately powered off. Use this action when the VM doesn’t have ACPI support.

{{< alert title="Note" type="info" >}}
When the guest is shut down from within the VM, OpenNebula will put the VM in the `poweroff` state.{{< /alert >}} 

You can also plan a **long term pause**. The Host resources used by the VM are freed and the Host is cleaned. VM disk state is saved in the system datastore. The following actions are useful if you want to preserve network and storage allocations (e.g., IPs, persistent disk images):

* `undeploy`: Gracefully shuts down a running VM, sending the ACPI signal. The Virtual Machine disks are transferred back to the system datastore. When an undeployed VM is resumed it is moved to the pending state and the scheduler will choose where to re-deploy it.
* `undeploy --hard`: Same as above but the running VM is immediately destroyed.
* `stop`: Same as `undeploy` but also the VM state is saved to resume it later.

When the VM is successfully paused you can resume its execution with:

* `resume`: Resumes the execution of VMs in the stopped, suspended, undeployed, and poweroff states.

### Rebooting VM Instances

Use the following commands to reboot a VM:

* `reboot`: Gracefully reboots a running VM, sending the ACPI signal.
* `reboot --hard`: Performs a ‘hard’ reboot.

### Delaying VM Instances

The deployment of a PENDING VM (e.g., after creating or resuming it) can be delayed with:

* `hold`: Sets the VM to hold state. The scheduler will not deploy VMs in the `hold` state. Please note that VMs can be created directly on hold by using ‘onetemplate instantiate –hold’ or ‘onevm create –hold’.

Then you can resume it with:

* `release`: Releases a VM from hold state, setting it to pending. Note that you can automatically release a VM by scheduling the operation as explained below.

<a id="disk-hotplugging"></a>

## Hotplug Devices to a Virtual Machine

{{< alert title="Warning" type="warning" >}}
Hotplugging might not be available for every supported hypervisor. Please check the limitations of the specific virtualization driver you’re using to ensure this feature is available before using it.{{< /alert >}} 

### Disk Hot-plugging

New disks can be hot-plugged to running VMs with the `onevm`, `disk-attach`, and `disk-detach` commands. For example, to attach the Image named **storage** to a running VM:

```shell
onevm disk-attach one-5 --image storage
```

To detach a disk from a running VM, find the disk ID of the Image you want to detach using the `onevm show` command, and then simply execute `onevm detach vm_id disk_id`:

```shell
onevm show one-5
...
DISK=[
  DISK_ID="1",
...
  ]
...

onevm disk-detach one-5 1
```

<a id="vm-guide2-nic-hotplugging"></a>

### NIC Hot-plugging

You can hot-plug network interfaces to VMs in the `RUNNING`, `POWEROFF`, or `SUSPENDED` states. Simply specify the network where the new interface should be attached, for example:

```shell
onevm show 2

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

onevm nic-attach 2 --network net_172
```

After the operation you should see two NICs, 0 and 1:

```shell
onevm show 2
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

It is possible to attach (and live-attach) PCI and SR-IOV interfaces. Simply select the device by its address, id, vendor, or class.

```shell
onevm nic-attach 2 --network net_172 onevm nic-attach 2 --network net_172 --pci '00:06.1'
```

**Important**, predictable PCI addresses for guests will be only generated if PCI bus 1 is present in the Virtual Machine as PCI bridges cannot be hot-plugged.

You can also detach a NIC by its ID. If you want to detach interface 1 (MAC `02:00:ac:10:00:ca`), execute:

```shell
onevm nic-detach 2 1
```

<a id="nic-update"></a>

### NIC Update

Qos attributes can be updated by the command `onevm nic-update`. If the Virtual Machine is running, the action triggers the driver action to live-update the network parameters.

```shell
cat update_nic.txt
NIC = [
    INBOUND_AVG_BW = "512",
    INBOUND_PEAK_BW = "1024"
]

onevm nic-update 0 0 update_nic.txt
```

<a id="vm-guide2-sg-hotplugging"></a>

### Security Group Hot-plugging

You can live attach or detach security groups to VMs. Simply specify the VM, network interface, and security group to attach, for example:

```shell
onevm sg-attach centos-server 0 101
```

Similarly to detach a security group execute:.

```shell
onevm sg-detach centos-server 0 101
```

On Sunstone, you can attach and detach security groups to an NIC on a running or powered off VM by going to the Network tab.

{{< image path="/images/sunstone_sg_main_view.png" alt="Sunstone main view" align="center" width="90%" mb="20px" >}}

To attach a new security group, you need to click on the shield on the NIC row. A dialog will be displayed where you can find all the security groups that do not belong to the selected network.

{{< image path="/images/sunstone_sg_attach.png" alt="Sunstone attach security group" align="center" width="90%" mb="20px" >}}

To detach the security group, you must click on the Trash button next to the security group. A confirm dialog will be displayed to ensure that you want to detach the security group.

<a id="vm-guide2-pci"></a>

### PCI Devices

You can attach or detach a PCI to/from a Virtual Machine in the `POWEROFF` and `UNDEPLOYED` state. For example:

```shell
onevm pci-attach alpine01 --pci_class 0c03 --pci_device 0015 --pci_vendor 1912
onevm pci-detach alpine01 0
```

<a id="vm-guide2-snapshotting"></a>

## Virtual Machine System Snapshots

{{< alert title="Warning" type="warning" >}}
Snapshotting might not be available for every supported hypervisor. Please check the limitations of the specific virtualization driver you’re using to ensure this feature is available before using it.

A system snapshot will contain the current disks and memory state. You can create, delete, and restore snapshots for running VMs.{{< /alert >}}  

```shell
onevm snapshot-create 4 "just in case"

onevm show 4
...
SNAPSHOTS
  ID         TIME NAME                                           HYPERVISOR_ID
   0  02/21 16:05 just in case                                   onesnap-0

onevm snapshot-revert 4 0 --verbose
VM 4: snapshot reverted
```

{{< alert title="Warning" type="warning" >}}
For snapshots for VMs running under the **KVM hypervisor** you should consider the following limitations:

- Snapshots are only available if all the VM disks use the [qcow2 driver]({{% relref "product/operation_references/configuration_references/img_template#img-template" %}}).{{< /alert >}}  

<a id="vm-guide-2-disk-snapshots"></a>

## Virtual Machine Disk Snapshots

There are two kinds of operations related to disk snapshots:

* `disk-snapshot-create`, `disk-snapshot-revert`, `disk-snapshot-delete`, `disk-snapshot-rename`: Allows the user to take snapshots of the disk states and return to them during the VM life-cycle. It is also possible to rename or delete snapshots.
* `disk-saveas`: Exports VM disk (or a previously created snapshot) to an Image in an OpenNebula Datastore. This is a live action.

{{< alert title="Warning" type="warning" >}}
Disk snapshots might have different limitations depending on the hypervisor. Please check the limitations of the specific virtualization driver you’re using to ensure this feature is available before using it.{{< /alert >}} 

<a id="vm-guide-2-disk-snapshots-managing"></a>

### Managing Disk Snapshots

A user can take snapshots of VM disks to create a checkpoint of the state of a specific disk at any time. Depending on the storage backend, these snapshots can be organized:

- In a tree-like structure, meaning that every snapshot has a parent, except for the first snapshot whose parent is `-1`. The active snapshot, the one the user has last reverted to or taken, will act as the parent of the next snapshot. It’s possible to delete snapshots that are not active and that have no children.
- Flat structure, without parent/child relationship. In that case, snapshots can be freely removed.

Disk snapshots are managed with the following commands:

- `disk-snapshot-create <vmid> <diskid> <name>`: Creates a new snapshot of the specified disk.
- `disk-snapshot-revert <vmid> <diskid> <snapshot_id>`: Reverts to the specified snapshot. The snapshots are immutable, therefore users can revert to the same snapshot as many times as they want; the disk will always return to the state of the snapshot at the time it was taken.
- `disk-snapshot-delete <vmid> <diskid> <snapshot_id>`: Deletes a snapshot if it has no children and is not active.

`disk-snapshot-create` can take place when the VM is in `RUNNING` state, provided that the drivers support it, while `disk-snapshot-revert` requires the VM to be in `POWEROFF` or `SUSPENDED`. Live snapshots are only supported for some hypervisors and storage drivers:

- Hypervisor `VM_MAD=kvm` combined with `TM_MAD=qcow2` datastores. In this case OpenNebula will request that the hypervisor executes `virsh snapshot-create`.
- Hypervisor `VM_MAD=kvm` with Ceph datastores (`TM_MAD=ceph`). In this case OpenNebula will initially create the snapshots as Ceph snapshots in the current volume.

With these combinations (CEPH and qcow2 datastores, and KVM hypervisor) you can [enable QEMU Guest Agent]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver#enabling-qemu-guest-agent" %}}). With this agent enabled the filesystem will be frozen while the snapshot is being taken.

{{< alert title="Warning" type="warning" >}}
OpenNebula will not automatically handle live `disk-snapshot-create` and `disk-snapshot-revert` operations for VMs in `RUNNING` state if the virtualization driver does not support it (check the limitations of the corresponding virtualization driver guide to know if this feature is available for your hypervisor). In this case the user needs to suspend or power off the VM before creating the snapshot.{{< /alert >}} 

See the [Storage Driver]({{% relref "product/integration_references/infrastructure_drivers_development/sd#sd-tm" %}}) guide for a reference on the driver actions invoked to perform live and non-live snapshots.

{{< alert title="Warning" type="warning" >}}
Depending on the `DISK/CACHE` attribute the live snapshot may or may not work correctly. To be sure, you can use `CACHE=writethrough`, although this delivers the slowest performance.{{< /alert >}} 

### Persistent Images and Disk Snapshots

These actions are available for both persistent and non-persistent Images. In the case of persistent Images the snapshots **will** be preserved upon VM termination and will be able to be used by other VMs using that Image. See the [snapshots]({{% relref "product/virtual_machines_operation/virtual_machines/images#images-snapshots" %}}) section in the Images guide for more information.

<a id="disk-save-as-action"></a>

### Saving a VM Disk to an Image (`disk-saveas`)

Any VM disk can be saved to a new Image (if the VM is in `RUNNING`, `POWEROFF`, `SUSPENDED`, `UNDEPLOYED`, or `STOPPED` states). This is a live operation that happens immediately. This operation accepts `--snapshot <snapshot_id>` as an optional argument, which specifies a disk snapshot to use as base of the new Image, instead of the current disk state (value by default).

{{< alert title="Warning" type="warning" >}}
This action is not in sync with the hypervisor. If the VM is in `RUNNING` state make sure the disk is unmounted (preferred), synced, or quiesced in some way or another before doing the `disk-saveas` operation.{{< /alert >}} 

<a id="vm-guide2-resizing-a-vm"></a>

## Resizing VM Resources

You may resize the capacity assigned to a Virtual Machine in terms of the virtual CPUs, memory, and CPU allocated. VM resizing can be done in any of the following states:
POWEROFF, UNDEPLOYED and, with some limitations, also live in RUNNING state.

If you have created a Virtual Machine and you need more resources, the following procedure is recommended:

- Perform any operation needed to prepare your Virtual Machine for shutting down, e.g., you may want to manually stop some services
- Power off the Virtual Machine
- Resize the VM
- Resume the Virtual Machine using the new capacity

Note that using this procedure the VM will preserve any resource assigned by OpenNebula, such as IP leases.

The following is an example of the previous procedure from the command line:

```shell
onevm poweroff web_vm
onevm resize web_vm --memory 2G --vcpu 2
onevm resume web_vm
```

### Live Resize of Capacity

If you need to resize the capacity in the RUNNING state you have to set up some extra attributes in the VM template. These attributes **must be set before the VM is started**. These attributes are driver-specific, more info for [KVM]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver#kvm-live-resize" %}}).

{{< alert title="Warning" type="warning" >}}
Hotplug is only implemented for KVM. Added CPUs will be in offline state after the resize. Enable them with `echo 1 > /sys/devices/system/cpu/cpu<ID>/online`{{< /alert >}} 

<a id="vm-guide2-resize-disk"></a>

### Resizing VM Disks

If the disks assigned to a Virtual Machine need more size, this can achieved at instantiation time of the VM. The SIZE parameter of the disk can be adjusted and, if it is bigger than the original size of the Image, OpenNebula will:

- Increase the size of the disk container prior to launching the VM
- Using the [contextualization packages]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates#context-overview" %}}), at boot time the VM will grow the filesystem to adjust to the new size.

You can override the size of a `DISK` in a VM template at instantiation:

```shell
onetemplate instantiate <template> --disk u2104:size=20000 # Image u2104 will be resized to 2 GB
```

You can also resize VM disks for both RUNNING and POWEROFF VMs:

```shell
onevm disk-resize <vm_id> <disk_id> <new_size> # <new_size> must be greater than current disk size
```

This will make the VM disk grow on the hypervisor node. Then the contextualization service running inside the guest OS will expand the filesystem with the newly available free space. The support for this filesystem expansion depends on the Guest OS.

{{< alert title="Important" type="info" >}}
In FreeBSD the resize of the root filesystem inside the guest OS is not performed automatically by the Contextualization Service. This leads to [filesystem corruption](https://github.com/OpenNebula/addon-context-linux/issues/298) and permanent data loss. This only applies to the partition mounted on `/` , partitions with other mountpoints will be resized.{{< /alert >}} 

<a id="vm-updateconf"></a>

## Updating the Virtual Machine Configuration

Some of the VM configuration attributes defined in the VM template can be updated after the VM is created. The `onevm updateconf` command will allow you to change the following attributes:

| Attribute       | Sub-attributes                                                                                                           |
|-----------------|--------------------------------------------------------------------------------------------------------------------------|
| `OS`            | `ARCH`, `MACHINE`, `KERNEL`, `INITRD`, `BOOTLOADER`, `BOOT`,<br/>`KERNEL_CMD`, `ROOT`, `SD_DISK_BUS`, `UUID`, `FIRMWARE`, `FIRMWARE_FORMAT` |
| `FEATURES`      | `ACPI`, `PAE`, `APIC`, `LOCALTIME`, `HYPERV`, `GUEST_AGENT`,<br/>`VIRTIO_SCSI_QUEUES`, `VIRTIO_BLK_QUEUES`, `IOTHREADS`  |
| `INPUT`         | `TYPE`, `BUS`                                                                                                            |
| `GRAPHICS`      | `TYPE`, `LISTEN`, `PASSWD`, `KEYMAP`, `COMMAND`                                                                          |
| `VIDEO`         | `TYPE`, `IOMMU`, `ATS`, `VRAM`, `RESOLUTION`                                                                             |
| `RAW`           | `DATA`, `DATA_VMX`, `TYPE`, `VALIDATE`                                                                                   |
| `CPU_MODEL`     | `MODEL`, `FEATURES`                                                                                                      |
| `BACKUP_CONFIG` | `FS_FREEZE`, `KEEP_LAST`, `BACKUP_VOLATILE`, `MODE`,<br/>`INCREMENT_MODE`                                                |
| `CONTEXT`       | Any value, except `ETH*`. **Variable substitution will be made**                                                         |

Visit the [Virtual Machine Template reference]({{% relref "product/operation_references/configuration_references/template#template" %}}) for a complete description of each attribute. Visit the [VM Update Methods Reference]({{% relref "product/operation_references/configuration_references/vm_update_methods/" %}}) for additional details on all available VM configuration update methods.

{{< alert title="Warning" type="warning" >}}
This action might not be supported for `RUNNING` VMs depending on the hypervisor. Please check the limitation section of the specific virtualization driver.{{< /alert >}} 

{{< alert title="Note" type="info" >}}
In running state only changes in CONTEXT take effect immediately, other values may need a VM restart. Also, the action may fail and the context will not be changed if the VM is running. You can try to manually trigger the action again.{{< /alert >}} 

<a id="vm-guide2-clone-vm"></a>

## Cloning a Virtual Machine

A VM template or VM instance can be copied to a new VM template. This copy will preserve the changes made to the VM disks after the instance is terminated. The template is private and will only be listed to the owner user.

There are two ways to create a persistent private copy of a VM:

- Instantiate a VM template with the *to persistent* option.
- Save an existing VM instance with `onevm save`.

### Instantiate to Persistent

When **instantiating to persistent** the template is cloned recursively (a private persistent clone of each disk Image is created), and that new template is instantiated.

To “instantiate to persistent” use the `--persistent` option:

```shell
onetemplate instantiate web_vm --persistent --name my_vm
VM ID: 31

onetemplate list
  ID USER            GROUP           NAME                                REGTIME
   7 oneadmin        oneadmin        web_vm                       05/12 14:53:11
   8 oneadmin        oneadmin        my_vm                        05/12 14:53:38

oneimage list
  ID USER       GROUP      NAME            DATASTORE     SIZE TYPE PER STAT RVMS
   7 oneadmin   oneadmin   web-img         default       200M OS   Yes used    1
   8 oneadmin   oneadmin   my_vm-disk-0    default       200M OS   Yes used    1
```

To "instantiate multiple persistent" VMs use the options `-m N` **and** `--name`. You **must** provide `--name` when `-m` > 1. Include `%i` in the name to insert the VM index (0..N-1) at a custom place:

```shell
onetemplate instantiate -m 2 --persistent --name 'test'
VM ID: 0
VM ID: 1

onetemplate instantiate -m 2 --persistent --name '%i-test'
VM ID: 2
VM ID: 3

onevm list
  ID USER         GROUP        NAME       STAT     CPU      MEM     HOST      TIME
   3 oneadmin     oneadmin     1-test     hold       1     768M           0d 00h00
   2 oneadmin     oneadmin     0-test     hold       1     768M           0d 00h00
   1 oneadmin     oneadmin     test-1     hold       1     768M           0d 00h00
   0 oneadmin     oneadmin     test-0     hold       1     768M           0d 00h00
```

Equivalently, in Sunstone activate the “Persistent” switch next to the Create button. Include `%i` in the name to insert the VM index (0..N-1) at a custom place.

Please bear in mind the following `ontemplate instantiate --persistent` limitation: volatile disks cannot be persistent. The contents of the disks will be lost when the VM is terminated. The cloned VM template will contain the definition for an empty volatile disk.

### Save a VM Instance

Alternatively, a VM that was not created as persistent can be **saved** before it is destroyed. To do so, the user has to `poweroff` the VM first and then use the `save` operation.

This action clones the VM source template, replacing the disks with copies of the current disks (see the disk-snapshot action). If the VM instance was resized, the current capacity is also used. The new cloned Images can be made persistent with the `--persistent` option. NIC interfaces are also overwritten with the ones from the VM instance, to preserve any attach/detach action.

```shell
onevm save web_vm copy_of_web_vm --persistent
Template ID: 26
```

Please bear in mind the following `onevm save` limitations:

- The VM’s source template will be used. If this template was updated since the VM was instantiated, the new contents will be used.
- Volatile disks cannot be saved and the current contents will be lost. The cloned VM template will contain the definition for an empty volatile disk.
- Disks and NICs will only contain the target Image/Network NAME and UNAME if defined. If your template requires extra configuration, you will need to update the new template.

<a id="vm-guide2-scheduling-actions"></a>

## Scheduled Actions for Virtual Machines

Scheduled actions lets you program operations over a VM to be performed in the future, e.g., *Shutdown the VM after 5 hours*. OpenNebula supports two types of schedule actions:

- punctual, that can be also periodic.
- relative actions.

### One-Time Punctual Actions

Most of the onevm commands accept the `--schedule` option, allowing users to delay the actions until a given date and time.

Here is an usage example:

```shell
onevm suspend 0 --schedule "09/20"
VM 0: suspend scheduled at 2016-09-20 00:00:00 +0200

onevm resume 0 --schedule "09/23 14:15"
VM 0: resume scheduled at 2016-09-23 14:15:00 +0200

onevm show 0
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : one-0

[...]

SCHEDULED ACTIONS
ID    ACTION  ARGS   SCHEDULED REPEAT   END STATUS
 0   suspend     - 09/20 00:00              Next in 12.08 days
 1    resume     - 09/23 14:15              Next in 15.67 days
```

These actions can be deleted or edited using the `onevm sched-delete` and `onevm sched-update` command. The time attributes use Unix time internally.

```shell
onevm sched-update 0 0

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
The attributes `ID`, `PARENT_ID` and `TYPE` are OpenNebula system attributes and can’t be modified. For more details about the attributes which can be modified, see [Scheduled Action Template]({{% relref "product/operation_references/configuration_references/template#template-schedule-actions" %}}){{< /alert >}} 

### Periodic Punctual Actions

To schedule periodic actions you can also use the option –schedule. However this command also needs more options to define the periodicity of the action:

> - `--weekly`: defines a weekly periodicity, so the action will be executed every week on the days that the user defines.
> - `--monthly`: defines a monthly periodicity, so the action will be executed every month, on the days that the user defines.
> - `--yearly`: defines a yearly periodicity, so the action will be executed every year, on the days that the user defines.
> - `--hourly`: defines an hourly periodicity, so the action will be executed each ‘x’ hours.
> - `--end`: defines when you want the relative action to finish.

The option `--weekly`, `--monthly`, and `--yearly` need the index of the days that the users wants to execute the action.

> - `--weekly`: days separated with commas between 0 (Sunday) and 6 (Saturday). [0,6]
> - `--monthly`: days separated with commas between 1 and 31. [1,31]
> - `--yearly`: days separated with commas between 0 and 365. [0,365]

The option `--hourly` needs a number with the number of hours. [0,168] (1 week)

The option `--end` can be a number or a date:

> - Number: defines the number of repetitions.
> - Date: defines the date that the user wants to finish the action.

Here is a usage example:

```shell
onevm suspend 0 --schedule "09/20" --weekly "1,5" --end 5
VM 0: suspend scheduled at 2018-09-20 00:00:00 +0200

onevm resume 0 --schedule "09/23 14:15" --weekly "2,6" --end 5
VM 0: resume scheduled at 2018-09-23 14:15:00 +0200

onevm snapshot-create 0 snap-01 --schedule "09/23" --hourly 5 --end "12/25"
VM 0: snapshot-create scheduled at 2018-09-23 14:15:00 +0200

onevm show 0
VIRTUAL MACHINE 0 INFORMATION
ID                  : 0
NAME                : one-0

[...]

SCHEDULED ACTIONS
ID           ACTION     ARGS    SCHEDULED        REPEAT            END  STATUS
 0          suspend        -  09/20 00:00    Weekly 1,5  After 5 times  Next in 1.08 days
 1           resume        -  09/23 14:15    Weekly 2,6  After 5 times  Next in 4.67 days
 2  snapshot-create  snap-01  09/19 21:16  Each 5 hours    On 12/25/18  Next in 4.78 hours
```

These actions can be deleted or edited using the `onevm sched-delete` and `onevm sched-update` command. The time attributes use Unix time internally.

```shell
onevm sched-update 0 2

ID="2"
PARENT_ID="0"
TYPE="VM"
ACTION="snapshot-create"
ARGS="snap-01"
TIME="1701998190"
REPEAT="3"
DAYS="5"
END_TYPE="2"
END_VALUE="1893452400"
DONE="1701980968"
```

### Relative Actions

Scheduled actions can be also relative to the Start Time of the VM. That is, it can be set on a VM Template and apply to the number of seconds after the VM is instantiated.

For instance, a VM Template with the following SCHED_ACTION will spawn VMs that will automatically shut down after 1 hour of being instantiated:

```shell
onetemplate update 0

SCHED_ACTION=[
   ACTION="terminate",
   ID="0",
   TIME="+3600" ]
```

This functionality is present graphically in Sunstone in the VM template creation and update wizard, on the second step Advanced options, under Schedule Action tab.

<a id="schedule-actions"></a>

The following table summarizes the actions that can be scheduled. Note that some of the above actions need some parameters to run (e.g., a disk ID or a snapshot name).

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

You can pass arguments to the scheduled actions by using the parameter `ARGS` in the action definition. For example:

```shell
onevm sched-update 0 0

ID="2"
PARENT_ID="0"
TYPE="VM"
ACTION="disk-snapshot-create",
ARGS="0, disksnap_example",
DAYS="1,5",
END_TYPE="1",
END_VALUE="5",
ID="0",
REPEAT="0",
TIME="1537653600"
```

In this example, the first argument would be the disk and the second the snapshot name.

{{< alert title="Note" type="info" >}}
The arguments are mandatory. If you use the CLI or Sunstone they are generated automatically for the actions.{{< /alert >}} 

## Command Execution Inside the Virtual Machine
Prerequisites:
* Running commands within a VM rely on the QEMU Guest Agent, which must be installed and running on the VM. 
* The VM must be in the `RUNNING` state.

With OpenNebula, run commands inside a Virtual Machine. Commands are sent to the VM through the QEMU Guest Agent, and results are stored in the VM template under `QEMU_GA_EXEC`. The following diagram depicts how commands are executed within a VM:

{{< image path="/images/vm_exec_architecture.svg" alt="Architecture Outlining How Command Execution Operates Within the VM" align="center" width="70%" mb="20px" border="false" >}}


The `VM_EXEC` monitor probe collects the results and updates the `QEMU_GA_EXEC` block. To find more details on configuring the monitor probe, refer to [Monitoring System]({{% relref "product/cloud_system_administration/resource_monitoring/monitoring_system.md" %}}).

{{< alert title="Warning" type="warning" >}}
Run only one command at a time for every Virtual Machine. If a current command is still in `EXECUTING` status, even if finished but not yet updated by the monitor probe, new commands will not be executed until the current one is fully completed.{{< /alert >}}

### Options
The `QEMU_GA_EXEC` section in the VM template contains the following fields:

| Field         | Description                                                     |
|---------------|-----------------------------------------------------------------|
| `COMMAND`     | The command to be executed in the VM.                           |
| `STDIN`       | Stdin data to pass to the command executed on the VM            |
| `PID`         | (Hypervisor-side) PID handling the exec request.                |
| `RETURN_CODE` | Numeric exit code produced by the command (e.g. `0` = success). |
| `STATUS`      | Execution state: `EXECUTING`, `CANCELLED`, `DONE` or `ERROR`.   |
| `STDOUT`      | Command standard output (base64-encoded).                       |
| `STDERR`      | Command standard error (base64-encoded).                        |


### Executing a command from the CLI

To execute a command inside a VM, use the `onevm exec` command. For example, to list files in the home directory of VM 0:
```bash
onevm exec 0 'ls -l'
```

Check the status of the command with:
```bash
onevm show 0
```

When still executing:

```bash
VIRTUAL MACHINE TEMPLATE
...
QEMU_GA_EXEC=[
  COMMAND="ls -l",
  STDIN="",
  STATUS="EXECUTING" ]
```

After the execution is complete, details are updated:

```bash
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

To retry the execution of the last command executed, use `onevm exec-retry`:
```bash
onevm exec-retry 0
```

To cancel the command being executed, use `onevm exec-cancel`:
```bash
onevm exec-cancel 0
```

<a id="vm-life-cycle-and-states"></a>

## Virtual Machine States

The life-cycle of a Virtual Machine within OpenNebula includes the following stages:

{{< alert title="Note" type="info" >}}
Note that this is a simplified version. If you are a developer you may want to take a look at the complete diagram referenced in the [Virtual Machines States Reference guide]({{% relref "product/operation_references/configuration_references/vm_states#vm-states" %}}).{{< /alert >}} 

| Short state   | State              | Meaning                                                                                                                                                                                                                                                                                                  |
|---------------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pend`        | `Pending`          | By default a VM starts in the pending state, waiting for a resource to run on. It will stay in this state until the scheduler decides to deploy it, or the user deploys it using the `onevm deploy` command.                                                                                             |
| `hold`        | `Hold`             | The owner has held the VM and it will not be scheduled until it is released. It can be deployed manually, however.                                                                                                                                                                                      |
| `clon`        | `Cloning`          | The VM is waiting for one or more disk images to finish the initial copy to the repository (image state still in `lock`).                                                                                                                                                                                 |
| `prol`        | `Prolog`           | The system is transferring the VM files (disk images and the recovery file) to the Host in which the Virtual Machine will be running.                                                                                                                                                                    |
| `boot`        | `Boot`             | OpenNebula is waiting for the hypervisor to create the VM.                                                                                                                                                                                                                                               |
| `runn`        | `Running`          | The VM is running (note that this stage includes the internal virtualized machine booting and shutting down phases). In this state, the virtualization driver will periodically monitor it.                                                                                                              |
| `migr`        | `Migrate`          | The VM is migrating from one resource to another. This can be a life migration or cold migration (the VM is saved, powered off or powered off hard and VM files are transferred to the new resource).                                                                                                    |
| `hotp`        | `Hotplug`          | A disk attach/detach, nic attach/detach, save as, resize or exec operation is in process.                                                                                                                                                                                                                       |
| `snap`        | `Snapshot`         | A system snapshot is being taken.                                                                                                                                                                                                                                                                        |
| `save`        | `Save`             | The system is saving the VM files after a migration, stop, or suspend operation.                                                                                                                                                                                                                          |
| `epil`        | `Epilog`           | In this phase the system cleans up the Host used to virtualize the VM, and additionally disk images to be saved are copied back to the system datastore.                                                                                                                                                 |
| `shut`        | `Shutdown`         | OpenNebula has sent the VM the shutdown ACPI signal and is waiting for it to complete the shutdown process. If after a timeout period the VM does not disappear, OpenNebula will assume that the guest OS ignored the ACPI signal and the VM state will be changed to **running** instead of **done**. |
| `stop`        | `Stopped`          | The VM is stopped. VM state has been saved and it has been transferred back along with the disk images to the system datastore.                                                                                                                                                                          |
| `susp`        | `Suspended`        | Same as stopped, but the files are left in the Host to later resume the VM there (i.e., there is no need to reschedule the VM).                                                                                                                                                                          |
| `poff`        | `PowerOff`         | Same as suspended, but no checkpoint file is generated. Note that the files are left in the Host to later boot the VM there.<br/><br/>When the VM guest is shut down, OpenNebula will put the VM in this state.                                                                                           |
| `unde`        | `Undeployed`       | The VM is shut down. The VM disks are transferred to the system datastore. The VM can be resumed later.                                                                                                                                                                                                   |
| `drsz`        | `Disk Resize`      | The VM disk resize is in progress.                                                                                                                                                                                                                                                                        |
| `back`        | `Backup`           | The VM backup is in progress.                                                                                                                                                                                                                                                                             |
| `rest`        | `Restore`          | The VM disks are restored from backup image.                                                                                                                                                                                                                                                              |
| `fail`        | `Failed`           | The VM failed.                                                                                                                                                                                                                                                                                           |
| `unkn`        | `Unknown`          | The VM couldn’t be reached, it is in an unknown state.                                                                                                                                                                                                                                                   |
| `clea`        | `Cleanup-resubmit` | The VM is waiting for the drivers to clean the Host after a `onevm recover --recreate` action.                                                                                                                                                                                                            |
| `done`        | `Done`             | The VM is done. VMs in this state won’t be shown with `onevm list` but are kept in the database for accounting purposes. You can still get their information with the `onevm show` command.                                                                                                              |

## Virtual Machine Datastore Migration

Datastore Migration allows the transfer of a VM's disk images and associated files from one system datastore to another. This is a critical operation for storage maintenance, balancing disk I/O load across different storage tiers, or evacuating hardware for decommissioning.

Depending on the state of the VM and the underlying storage drivers, OpenNebula supports two primary methods:

* **Cold Storage Migration**: Performed when the VM is in a POWEROFF or UNDEPLOYED state. The disks are moved physically between datastores before the VM is resumed.

* **Live Storage Migration**: Performed while the VM is RUNNING. OpenNebula coordinates with the hypervisor to mirror disk writes to the new destination in real-time, ensuring zero downtime for the workload.

{{< alert title="Note" type="info" >}}
Not all storage drivers support both methods. Check the "Storage migration" column in the [storage portfolio]({{% relref "product/cluster_configuration/storage_system/overview/#storage-portfolio" %}}) table for updated compatibility info.
{{< /alert >}}

### Basic Syntax

You can migrate a VM's disks to a different datastore by specifying the target datastore ID when running `onevm migrate`:

```shell
onevm migrate [--live] <VM_ID> <TARGET_HOST_ID> <TARGET_DATASTORE_ID>
```

If the target Host is the same as the current one, only the datastore changes. If you also change the Host, both the Host and the datastore are migrated simultaneously, although changing both is only supported for offline migrations.

Cold and live migrations cannot be performed between different TM_MAD drivers (for example, from `ceph` to `lvm`).

### Cold Storage Migration

Cold migration is the simplest form of datastore migration. The VM is automatically stopped by OpenNebula before migrating it, saving its running state across the process. OpenNebula copies the disk files from the source datastore to the destination datastore using the Transfer Manager.

```shell
onevm migrate <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID>
```

You can also use `--poff` or `--poff-hard` to power off the VM during migration:

```shell
onevm migrate <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID> --poff
```

As the VM is powered off before any disk operations take place, libvirt is not involved in the actual data transfer. The Transfer Manager handles all file-level operations (copying disk images, updating symlinks, etc.) through the TM_MAD scripts. Once the disk files are in place on the destination datastore, the VM is simply resumed and its disk device paths point to the new location.

### Live Storage Migration

Live storage migration allows the VM disks to be migrated while the VM remains in the `RUNNING` state. OpenNebula coordinates with the hypervisor (KVM) to mirror disk writes to the new destination in real-time.

```shell
onevm migrate --live <VM_ID> <HOST_ID> <TARGET_DATASTORE_ID>
```

At the libvirt level, live datastore migration uses the `virsh blockcopy` command on the same Host. Read-only disks (such as CD-ROM or read-only qcow2 images) are copied by OpenNebula, after which libvirt's `change-media` command is used to update their paths.

There are some limitations to keep in mind when performing live datastore migration:

* You **cannot change both the Host and the datastore simultaneously**. For that case, you need to perform each of those operations in order.
* **Disk snapshots** are only preserved with qcow2-based drivers (`qcow2`, `ssh`, `local`); they are lost with other drivers (LVM, raw disks, shared NFS).

<a id="vm-charter"></a>

## Virtual Machine Charters

This functionality automatically adds scheduling actions in VM templates. To enable the creation of Charters in Sunstone, you only need to add the following to the `vm-tab.yaml` file in the corresponding [Sunstone view]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone-views" %}}):

```default
info-tabs:
  sched_actions:
    enabled: true
    actions:
      charter_create: true
```

{{< image path="/images/sunstone_vm_charter.png" alt="Sunstone VM charter" align="center" width="90%" mb="20px" >}}

After enabling the creation of Charters, you have to define the schedule actions that have a Charter. To do that, you only need to modify the file `sunstone-server.conf` in the [FireEdge configuration]({{% relref "product/operation_references/opennebula_services_configuration/fireedge#fireedge-conf" %}}).

To explain this, we'll use an example:

```default
leases:
  terminate:
    edit: false
    execute_after_weeks: 3
  poweroff:
    edit: true
    execute_after_minutes: 5
```

The previous example will create two schedule actions:

- The Virtual Machine will be terminated 3 weeks after it was instantiated and you cannot edit this action before creating it.
- The Virtual Machine will be powered off after 5 minutes after it was instantiated and you can edit the action before creating it.

So, when the user clicks on the Charter button, the following info will appear:

{{< image path="/images/sunstone_charter_info.png" alt="Sunstone VM charter info" align="center" width="90%" mb="20px" >}}

The first action cannot be edited but in the second one, you can change the action and the time. Also, you can tune the definition of a Charter:

| edit                                                      | If the action could be edited or not. Allow values: true, false                                                                                                                                                                                                                                                                                                                                               |
|-----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| execute_after_<period_type><br/><br/><br/><br/><br/><br/> | Execute the action after the time that is defined. <period_type> allow values: years, months, weeks, days, hours, minutes.<br/><br/><br/>e.g., execute_after_years: 2 -> The action will be executed 2 years after the Virtual Machine was instantiated.<br/><br/><br/>e.g., execute_after_months: 3 -> The action will be executed 3 months after the Virtual Machine was instantiated.<br/><br/> |

This functionality is also available in the CLI through the following commands:

- onevm create-chart
- onevm sched-update
- onevm sched-delete

The Charters can be added into the `onevm` configuration file `/etc/one/cli/onevm.yaml`:

```default
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

The information about the Charters can be checked with the command `onevm show`, the `*` in front of the ID indicates that the warning time passed:

```default
SCHEDULED ACTIONS
ID     ACTION     ARGS    SCHEDULED        REPEAT            END  STATUS
*0  suspend          -  01/01 03:00                               Next in 1.25 hours
 1  terminate        -  15/01 03:00                               Next in 14 days
```

<a id="vm-guide2-user-defined-data"></a>

## User-defined Data

Custom attributes can be added to a VM to store metadata related to this specific VM instance. To add custom attributes simply use the `onevm update` command:

```shell
onevm show 0
...

VIRTUAL MACHINE TEMPLATE
...
VMID="0"

onevm update 0
ROOT_GENERATED_PASSWORD="1234"
~
~

onevm show 0
...

VIRTUAL MACHINE TEMPLATE
...
VMID="0"

USER TEMPLATE
ROOT_GENERATED_PASSWORD="1234"
```

## Virtual Machine VM Permissions

OpenNebula comes with an advanced [ACL rules permission mechanism]({{% relref "product/cloud_system_administration/multitenancy/chmod#manage-acl" %}}) intended for administrators, but each VM object has also [implicit permissions]({{% relref "product/cloud_system_administration/multitenancy/chmod#chmod" %}}) that can be managed by the VM owner. To share a VM instance with other users or to allow them to list and show its information, use the `onevm chmod` command:

```shell
onevm show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : ---

onevm chmod 0 640

onevm show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---
```

Administrators can also change the VM’s group and owner with the `chgrp` and `chown` commands.

<a id="life-cycle-ops-for-admins"></a>

## Advanced Operations for Administrators

There are some `onevm` commands operations meant for cloud administrators:

**Scheduling:**

- `resched`: Sets the reschedule flag for the VM. The Scheduler will migrate (or live-migrate, depending on the [Scheduler configuration]({{% relref "product/cloud_system_administration/scheduler/configuration" %}})) the VM in the next monitorization cycle to a Host that better matches the requirements and rank restrictions. Read more in the [Scheduler documentation]({{% relref "product/cloud_system_administration/scheduler/" %}}).

- `unresched`: Clears the reschedule flag for the VM, canceling the rescheduling operation.

**Deployment:**

- `deploy`: Starts an existing VM in a specific Host.
- `migrate --live`: The Virtual Machine is transferred between Hosts with no noticeable downtime. The VM storage cannot be migrated to other system datastores.
- `migrate`: The VM is stopped and resumed in the target Host. In an infrastructure with multiple system datastores, VM storage can also be migrated (by specifying the datastore ID).

Note: By default, the above operations do not check the target Host capacity. You can use the `--enforce` option to be sure that the Host capacity is not overcommitted.

**Troubleshooting:**

- `recover`: If the VM is stuck in any other state (or the boot operation does not work), you can recover the VM with the following options. Read the [Virtual Machine Failures guide]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting#ftguide-virtual-machine-failures" %}}) for more information.
  - `--success`: simulates the success of the missing driver action
  - `--failure`: simulates the failure of the missing driver action
  - `--retry`: tries to perform the current driver action again. Optionally the `--interactive` can be combined if it's a Transfer Manager problem
  - `--delete`: Deletes the VM, moving it to the DONE state immediately
  - `--recreate`: Deletes the VM and moves it to the PENDING state
- `migrate` or `resched`: A VM in the UNKNOWN state can be booted in a different Host manually (`migrate`) or automatically by the scheduler (`resched`). This action must be performed only if the storage is shared, or manually transferred by the administrator. OpenNebula will not perform any action on the storage for this migration.

<a id="remote-access-sunstone"></a>

## Accessing VM Console and Desktop

Sunstone provides several different methods to access your VM console and desktop: VNC, RDP, and SSH. If configured in the VM, these methods can be used to access the VM console through Sunstone. This section shows how these different technologies can be configured and what each requirement is.

[FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge#fireedge-configuration" %}}) automatically installs dependencies for Guacamole connections which are necessary to use VNC, RDP, and SSH.

{{< alert title="Important" type="info" >}}
The [FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge#fireedge-conf" %}}) server must be running to get Guacamole connections working.{{< /alert >}} 

<a id="requirements-remote-access-sunstone"></a>

<a id="vnc-sunstone"></a>

### Configuring Your VM for VNC

VNC is a graphical console with wide support among many hypervisors and clients.

To enable the VNC console service you must have a `GRAPHICS` section in the VM template,
as stated in the documentation. Make sure the attribute `IP` is set correctly (`0.0.0.0` to allow
connections from everywhere), otherwise no connections will be allowed from the outside.

For example, to configure this in the Virtual Machine template:

```none
GRAPHICS=[
    LISTEN="0.0.0.0",
    TYPE="vnc"
]
```

**Your browser must support websockets**, and have them enabled.

To configure it via Sunstone, you need to update the VM template. In the second step, Advanced options, under the Input/Output tab,
you can see the graphics section where you can add the IP, the port, a connection password,
or define your keymap.

{{< image path="/images/sunstone_guac_vnc.png" alt="Sunstone GUAC VNC" align="center" width="90%" mb="20px" >}}

<a id="rdp-sunstone"></a>

### Configure VM for RDP

Short for **Remote Desktop Protocol**, it allows one computer to connect to another computer
over a network in order to use it remotely.

<a id="requirements-guacamole-rdp-sunstone"></a>

To enable RDP connections to the VM, you must have one `NIC`
with `RDP` attribute equal to `YES` in the template.

Via Sunstone, you need to enable an RDP connection on one of the VM template networks, **after or
before its instantiation**.

{{< image path="/images/sunstone_guac_nic_1.png" alt="Sunstone GUAC NIC 1" align="center" width="90%" mb="20px" >}}

{{< image path="/images/sunstone_guac_nic_2.png" alt="Sunstone GUAC NIC 2" align="center" width="90%" mb="20px" >}}

To configure this in the Virtual Machine template in **advanced mode**:

```none
NIC=[
    ...
    RDP = "YES"
]
```

Once the VM is instantiated, users will be able to **connect via browser**.


{{< image path="/images/sunstone_guac_rdp.png" alt="Sunstone GUAC RDP" align="center" width="90%" mb="20px" >}}

RDP connection permits users to **choose the screen resolution** from Sunstone interface.

{{< image path="/images/sunstone_guac_rdp_interface.png" alt="Sunstone GUAC RDP interface" align="center" width="90%" mb="20px" >}}

{{< alert title="Important" type="info" >}}
**The RDP connection is only allowed to activate on a single NIC**. In any case, the connection will only contain the IP of the first NIC with this property enabled.
The RDP connection will work the **same way for NIC ALIASES**.{{< /alert >}}  

If the VM template has a `PASSWORD` and `USERNAME` set in the contextualization section, this will be reflected in the RDP connection. You can read about them in the [Virtual Machine Definition File reference section]({{% relref "product/operation_references/configuration_references/template#template-context" %}}).

{{< alert title="Note" type="info" >}}
If your Windows VM has a firewall enabled, you can set the following in the start script of the VM (in the Context section of the VM Template):

```shell
netsh advfirewall firewall set rule group="Remotedesktop" new enable=yes
```
{{< /alert >}} 

<a id="requirements-guacamole-ssh-sunstone"></a>

### Configure VM for SSH

Unlike VNC or RDP,
SSH is a text protocol. SSH connections require a hostname or IP address to define
the destination machine. As with the [RDP]({{% relref "#requirements-guacamole-rdp-sunstone" %}}) connections,
you need to enable the SSH connection on one of the VM template networks.

For example, to configure this in the Virtual Machine template in **advanced mode**:

```default
NIC=[
    ...
    SSH = "YES"
]
```

SSH is standardized to use port 22 and this will be the proper value in most cases. You only
need to specify the **SSH port in the contextualization section as** `SSH_PORT` if you are
not using the standard port.

{{< alert title="Note" type="info" >}}
If the VM template has a `PASSWORD` and `USERNAME` set in the contextualization section, this will be reflected in the SSH connection. You can read about them in the [Virtual Machine Definition File reference section]({{% relref "product/operation_references/configuration_references/template#template-context" %}}).{{< /alert >}} 

For example, to allow connection by username and password to a guest VM, first make sure you
have SSH root access to the VM, check more info [here]({{% relref "product/control_plane_configuration/graphical_user_interface/cloud_view#cloudview-ssh-keys" %}}).

After that you can access the VM and configure the SSH service:

```shell
oneadmin@frontend:~$ ssh root@<guest-vm>

# Allow authentication with password: PasswordAuthentication yes
root@<guest-VM>:~$ vi /etc/ssh/sshd_config

# Restart SSH service
root@<guest-VM>:~$ service sshd restart

# Add user: username/password
root@<guest-VM>:~$ adduser <username>
```

{{< image path="/images/fireedge_sunstone_ssh_list.png" alt="Sunstone SSH list" align="center" width="90%" mb="20px" >}}
{{< image path="/images/fireedge_sunstone_ssh_console.png" alt="Sunstone SSH console" align="center" width="90%" mb="20px" >}}

{{< alert title="Note" type="info" >}}
Guacamole SSH uses RSA encryption. Make sure the VM SSH accepts RSA, otherwise you need to explicitly enable it in the VM SSH configuration (HostkeyAlgorithms and PubkeyAcceptedAlgorithms set as ‘+ssh-rsa){{< /alert >}} 

<a id="onevm-command"></a>

## The `onevm` command

The `onevm` command manages OpenNebula Virtual Machines. The general structure of the command is as follows:

 `onevm`<a href="#commands">`command`</a>[<a href="#args">*args*</a>] [<a href="#options">*options*</a>] 


| <h4 id="commands"> Commands </h4>  |
|---------------------------------|:----------------------------------------------|
| `backup vmid`                   | <ul><li>Creates a VM backup on the given datastore</li><li>States: RUNNING, POWEROFF</li><li>Valid options: datastore, end, hourly, monthly, reset, schedule, weekly, yearly</li></ul>|  
| `backup-cancel vmid`            | Cancels an active VM backup operation. States: RUNNING, POWEROFF|
| `backupmode vmid mode`          | Updates the backup mode of a VM. It can be FULL\|INCREMENT |
| `chgrp range\|vmid_list groupid`| Changes the VM group                           |
| `chmod range\|vmid_list octet`  | Changes the VM permissions                     |
| `chown range\|vmid_list userid [groupid]`| Changes the VM owner and group        |
| `create [file]`                 | <ul><li>Creates a new VM from the given description instead of using a previously defined template (see `onetemplate create` and `onetemplate instantiate`).</li><li>Valid options: arch, boot, context, cpu, disk, dry, files_ds, hold, init, memory, multiple, name, net_context, nic, raw, report_ready, spice, spice_keymap, spice_listen, spice_password, ssh, startscript, user_inputs, vcpu, video, video_ats, video_iommu, video_resolution, video_vram, vnc, vnc_keymap, vnc_listen, vnc_password</li><li>Examples:<ul><li>Using a template description file: `onevm create vm_description.tmpl`</li><li>New VM named "arch vm" with a disk and a nic: `onevm create --name "arch vm" --memory 128 --cpu 1 --disk arch \ --network private_lan`</li><li>A vm with two disks: `onevm create --name "test vm" --memory 128 --cpu 1 --disk arch,data`</li></ul></li></ul>|
| `create-chart vmid`             | Adds a charter to the VM; these are some consecutive scheduled actions. You can configure the actions in `onevm.yaml` |
| `delete-chart vmid sched_id`    | Deletes a charter from the VM. Deprecated, use `sched-delete` instead. |
| `deploy range\|vmid_list hostid [datastoreid]` | <ul><li>Deploys the given VM in the specified Host. This command forces the deployment, in a standard installation the Scheduler is in charge of this decision.</li><li>A template can be passed as a file with or the content via STDIN. Bash symbols must be escaped on STDIN passing.</li><li>States: PENDING, HOLD, STOPPED, UNDEPLOYED</li><li>Valid options: enforce, file</li></ul>|
| `disk-attach vmid`              | <ul><li>Attaches a disk to a running VM.</li><li>A template can be passed as a file with or the content via STDIN. Bash symbols must be escaped on STDIN passing. When using a template add only one DISK instance.</li><li>States: RUNNING, POWEROFF</li><li>Valid options: cache, discard, file, image, prefix, target</li> |
| `disk-detach vmid diskid`       | Detaches a disk from a running VM. States: RUNNING, POWEROFF
| `disk-resize vmid diskid size`  | <ul><li>Resizes a VM disk. The new size should be larger than the old one.</li><li>The valid units are: T (TiB), G (GiB), and M (MiB). By default it is MiB.</li><li>States: RUNNING, POWEROFF</li></ul>|
| `disk-saveas vmid diskid img_name` | <ul><li>Saves the specified VM disk as a new Image. The Image is created immediately, and the contents of the VM disk will be saved to it.</li><li>States: ANY</li><li>Valid options: snapshot, type</li></ul> |
| `disk-snapshot-create vmid diskid name` | <ul><li>Takes a new snapshot of the given disk. This operation needs support from the Datastore drivers: QCOW2 or Ceph.</li><li>States: RUNNING, POWEROFF, SUSPENDED</li><li> Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
|  `disk-snapshot-delete vmid diskid disk_snapshot_id` | <ul><li> Deletes a disk snapshot.</li><li>States: RUNNING, POWEROFF, SUSPENDED</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `disk-snapshot-list vmid diskid` | Lists the snapshots of a disk. |
| `disk-snapshot-rename vmid diskid disk_snapshot_id new_snapshot_name` | Renames a disk snapshot. |
| `disk-snapshot-revert vmid diskid disk_snapshot_id` | <ul><li>Reverts disk state to a previously taken snapshot.</li><li>States: POWEROFF, SUSPENDED</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `hold range\|vmid_list`           | <ul><li> Sets the given VM on hold. A VM on hold is not scheduled until it is released. It can be, however, deployed manually; see `onevm deploy`.</li><li>States: PENDING</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly </li></ul> |
| `list [filterflag]`               | <ul><li> Lists VMs in the pool. The default columns and their layout can be configured in *onevm.yaml*</li><li>Valid options: adjust, csv, csv_del, delay, describe, expand, extended, filter, json, kilobytes, list, listconf, no_expand, no_header, no_pager, numeric, operator, search, size, xml, yaml</li></ul>|
| `lock range\|vmid_list`           | <ul><li>Locks a VM to prevent certain actions defined by different levels. The show and monitoring action will never be locked.</li><li>States: All. </li><li> Valid options: all, admin, manage, use. [Admin]: locks only Admin actions. [Manage]: locks Manage and Use actions. [Use]: locks Admin, Manage and Use actions.</li></ul>|
| `migrate range\|vmid_list hostid [datastoreid]` | <ul><li>Migrates the given running VM to another Host. If used with `--live` parameter the migration is done without downtime. Datastore migration is not supported for `--live` flag.</li><li>States: RUNNING</li><li>Valid options: enforce, live, poweroff, poweroff_hard</li></ul>|
| `nic-attach vmid`                  | <ul><li>Attaches a NIC to a VM.</li><li>To attach a nic alias: A template can be passed as a file with or the content via STDIN. Bash symbols must be escaped on STDIN passing. When using a template add only one NIC instance.</li><li>To hotplug a PCI device and use it as a NIC interface in the VM select it with `--pci` (short_address) or `--pci_device` (device ID), `--pci_class` (class ID) and/or `--pci_vendor` (vendor ID).</li><li>States: RUNNING, POWEROFF</li><li>Valid options: alias, file, ip, network, nic_name, pci, pci_class, pci_device, pci_vendor</li></ul> |
|  `nic-detach vmid nicid`            | Detaches a NIC from a running VM. States: RUNNING, POWEROFF |
| `nic-update vmid nicid [file]`      | <ul><li>Updates a NIC for a VM. In case the VM is running, trigger NIC update on the Host.</li><li>States: Almost all, except BOOT*, MIGRATE and HOTPLUG-NIC</li><li>Valid options: append</li></ul>|
| `pci-attach vmid`                   | <ul><li>Attaches a PCI to a VM. You can specify the PCI device with `--pci` (short_address) or `--pci_device` (device ID), `--pci_class` (class ID) and/or `--pci_vendor` (vendor ID).</li><li>States: POWEROFF</li><li>Valid options: file, pci, pci_class, pci_device, pci_vendor</li></ul> |
| `pci-detach vmid pciid`             | Detaches a PCI device from a VM. States: POWEROFF           |
| `port-forward vmid [port]`          | Gets port forwarding from a NIC, e.g: 1.2.3.4@4000 -> 1, means that to connect to VM port 1, you need to connect to IP 1.2.3.4 in port 4000. Valid options: `nic_id` |
| `poweroff range\|vmid_list`         | <ul><li>Powers off the given VM. The VM will remain in the poweroff state, and can be powered on with the `onevm resume` command.</li><li>States: RUNNING</li><li>Valid options: end, hard, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `reboot range\|vmid_list`           | <ul><li>Reboots the given VM, this is equivalent to execute the reboot command from the VM console. The VM will be ungracefully rebooted if `--hard` is used.</li><li> States: RUNNING</li><li>Valid options: end, hard, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `recover range\|vmid_list`          | <ul><li>Recovers a stuck VM that is waiting for a driver operation. The recovery may be done by failing, succeeding or retrying the current operation. *You need to manually check the VM status on the Host*, to decide if the operation was successful or not, or if it can be retried.</li><li>Example: A VM is stuck in *migrate* because of a hardware failure. You need to check if the VM is running in the new Host or not to recover the vm with `--success` or `--failure`, respectively.</li><li>States for success/failure recovers: Any ACTIVE state.</li><li> States for a retry recover: Any FAILURE state</li><li>States for delete: Any</li><li>States for recreate: Any but DONE</li><li>States for delete-db: Any</li><li>Valid options: delete, deletedb, failure, interactive, recreate, retry, success</li></ul>|
| `release range\|vmid_list`           | <ul><li>Releases a VM on hold. See `onevm hold`</li><li>States: HOLD</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `rename vmid name`                   | Renames the VM.                       |
| `resched range\|vmid_list`           | Sets the rescheduling flag for the VM. States: RUNNING, POWEROFF|
| `resize vmid`                        | <ul><li>Resizes the capacity of a Virtual Machine.</li><li> A template can be passed as a file with or the content via STDIN. Bash symbols must be escaped on STDIN passing.</li><li>Valid options: cpu, enforce, file, memory, vcpu</li>|
| `restore vmid imageid`               | Restores the Virtual Machine from the backup Image. The VM must be in poweroff state. Valid options: disk_id, increment |
| `resume range\|vmid_list`            | <ul><li>Resumes the execution of a saved VM</li><li>States: STOPPED, SUSPENDED, UNDEPLOYED, POWEROFF, UNKNOWN</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `save vmid name`                     | <ul><li>Clones the VM's source Template, replacing the disks with live snapshots of the current disks. The VM capacity and NICs are also preserved</li><li>States: POWEROFF</li><li>Valid options: persistent</li></ul>|
| `sched-delete vmid sched_id`         | Deletes a Scheduled Action from the VM. |
| `sched-update vmid sched_id [file]`  | Updates a Scheduled Action from a VM. |
| `sg-attach vmid nicid sgid`          | Attaches a Security Group to a VM. States: All, except BOOT, MIGRATE and HOTPLUG_NIC |
| `sg-detach vmid nicid sgid`          | Detaches a Security Group from a VM. States: All, except BOOT, MIGRATE and HOTPLUG_NIC |
| `show vmid`                          | Shows information for the given VM. Valid options: all, decrypt, json, xml, yaml|
| `snapshot-create range\|vmid_list [name]` | Creates a new VM snapshot. Valid options: end, hourly, monthly, schedule, weekly, yearly |
| `snapshot-delete vmid snapshot_id`   | Deletes a snapshot of a VM. Valid options: end, hourly, monthly, schedule, weekly, yearly |
| `snapshot-list vmid`                 | Lists the snapshots of a VM. |
| `snapshot-revert vmid snapshot_id`   | Reverts a VM to a saved snapshot. Valid options: end, hourly, monthly, schedule, weekly, yearly |
| `ssh vmid [login]`                   | <ul><li>SSH into VM.</li><li>Options example:`-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null`</li><li>Valid options: cmd, nic_id, ssh_opts</li></ul>|
| `stop range\|vmid_list`              | <ul><li> Stops a running VM. The VM state is saved and transferred back to the front-end along with the disk files</li><li>States: RUNNING</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `suspend range\|vmid_list`           | <ul><li>Saves a running VM. Similar to `onevm stop`, but the files are left in the remote machine to later restart the VM there. The resources are not freed and there is no need to re-schedule the VM.</li><li>States: RUNNING</li><li>Valid options: end, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `terminate range\|vmid_list`         | <ul><li>Terminates the given VM. The VM life cycle will end. With `--hard` it unplugs the VM.</li><li>States: valid if no operation is being performed on the VM</li><li>Valid options: end, hard, hourly, monthly, schedule, weekly, yearly</li></ul>|
| `top [filterflag]`                   | Lists Images continuously. Valid options: adjust, csv, csv_del, delay, expand, extended, filter, json, kilobytes, list, listconf, no_expand, no_header, no_pager, numeric, operator, size, xml, yaml |
| `undeploy range\|vmid_list`          | <ul><li>Shuts down the given VM. The VM is saved in the system Datastore. With --hard it unplugs the VM.</li><li>States: RUNNING</li><li>Valid options: end, hard, hourly, monthly, schedule, weekly, yearly</li></ul> |
| `unlock range\|vmid_list`            | Unlocks a Virtual Machine. Valid states: All. |
| `unresched range\|vmid_list`         | Clears the rescheduling flag for the VM. States: RUNNING, POWEROFF |
| `update vmid [file]`                 | Updates the user template contents. If a path is not provided the editor will be launched to modify the current content. Valid options: append |
| `update-chart vmid sched_id [file]`  | Updates a charter from a VM. Deprecated command: use `sched-update` instead. |
| `updateconf vmid [file]`             | <ul><li>Updates the configuration of a VM.</li><li>This command accepts a template or opens an editor. A template can be passed as a file with or the content via STDIN. Bash symbols must be escaped on STDIN passing.</li><li>Valid states are: running, pending, failure, poweroff, undeploy, hold or cloning. In running state only changes in CONTEXT and BACKUP_CONFIG take effect immediately, other values may need a VM restart.</li>Configuration attributes include: <ul><li>OS        = ["ARCH", "MACHINE", "KERNEL", "INITRD", "BOOTLOADER", "BOOT", "KERNEL_CMD", "ROOT", "SD_DISK_BUS", "UUID", "FIRMWARE", "FIRMWARE_FORMAT"]</li><li>FEATURES  = ["ACPI", "PAE", "APIC", "LOCALTIME", "HYPERV", "GUEST_AGENT", "VIRTIO_SCSI_QUEUES", "VIRTIO_BLK_QUEUES", "IOTHREADS"]</li><li>INPUT     = ["TYPE", "BUS"]</li><li>GRAPHICS  = ["TYPE", "LISTEN", "PASSWD", "KEYMAP", "COMMAND"]</li><li>VIDEO     = ["TYPE", "IOMMU", "ATS", "VRAM", "RESOLUTION"]</li><li>RAW       = ["DATA", "DATA_VMX", "TYPE", "VALIDATE"]</li><li>CPU_MODEL = ["MODEL", "FEATURES"]</li><li>BACKUP_CONFIG = ["FS_FREEZE", "KEEP_LAST", "BACKUP_VOLATILE", "MODE", "INCREMENT_MODE"]</li><li>CONTEXT (any value, ETH* if CONTEXT_ALLOW_ETH_UPDATES set in oned.conf, *variable substitution will be made*)</li></ul><li>Valid options: append</li></ul>|
| `vnc vmid`                            | Opens a VNC session to the VM. Valid options include: vnc|

<a href="#onevm-command">Back to The `onevm` Command</a>

| <h4 id="args"> Args </h4> |
|--------------------------------------- | -------------------------------|
| `datastoreid`                          | OpenNebula DATASTORE name or id|
| `disk_snapshot_id`                     | Disk_snapshot name or id       |
| `diskid`                               | Disk id                        |
| `file`                                 | Path to a file                 |
| `filterflag <option>`                  | Option list:<ul><li> a, all: all the known VMs</li><li> m, mine: the VM belonging to the user in ONE_AUTH</li><li> g, group: 'mine' plus the VM belonging to the groups the user is member of</li><li> G, primary group: The VM owned the user's primary group</li><li> uid: VM of the user identified by this uid </li><li> user: VM of the user identified by the username</li><ul>|
| `groupid`                              | OpenNebula GROUP name or id    |
| `hostid`                               | OpenNebula HOST name or id     |
| `imageid`                              | OpenNebula IMAGE name or id    |
| `nicid`                                | NIC name or id                 |
| `pciid`                                | PCI id                         |
| `range`                                | List of id's in the form 1,8..15 |
| `sched_id`                             | Scheduled Action id            |
| `sgid`                                 | Security Group id              |
| `size`                                 | Disk size in MiB               |
| `snapshot_id`                          | Snapshot name or id            |
| `text`                                 | String                         |
| `userid`                               | OpenNebula USER name or id     |
| `vmid`                                 | OpenNebula VM name or id       |
| `vmid_list`                            |Comma-separated list of OpenNebula VM names or ids |

<a href="#onevm-command">Back to The `onevm` Command</a>

| <h4 id="options"> Options </h4> |
|-------------------------------|:----------------------------------------------|
| `--adjust x,y,z`              | Adjusts size to not truncate selected columns  |
| `--admin`                     | Locks admin actions                            |
| `-a, --alias alias`           | Attaches the NIC as an ALIAS                    |
| `--all`                       | Shows all template data                        |
| `-a, --append`                | Appends new attributes to the current template |
| `--arch arch`                 | Lists details of the VM architecture. Example: i386 or x86_64  |
| `--boot device_list`          | Sets boot device list e.g. disk0,disk2,nic0    | 
| `--cache cache_mode`          | Configures hypervisor cache mode: default, none, writethrough, writeback, directsync or unsafe, (Only KVM driver)|
| `--cmd cmd`                   | CMD to run when SSH                           |
| `--context line1,line2,line3` | Replaces the context section with the specified lines |
| `--cpu cpu`                   | Shows CPU percentage reserved for the VM (1=100% one CPU) |
| `--csv`                       | Writes table in csv format                     |
| `--csv-del del`               | Sets delimiter for csv output                  |
| `-d`, `--datastore id\|name`  | Selects the datastore                         |
| `--decrypt`                   | Gets decrypted attributes                      |
| `-d`, `--delay x`             | Sets the delay in seconds for top command     |
| `--delete`                    | Deletes the VM. **Important**: No recovery action possible.    |
| `--delete-db`                 | Deletes the VM from the DB. It does not trigger any action on the hypervisor. **Important**: No recovery action possible.   |
| `--describe`                  | Describes list of columns                         |
| `--discard discard_mode`      | Hypervisor discard mode: ignore or unmap. Only KVM driver. |
| `--disk image0,image1`        | Disks to attach. To use an image owned by other user run `user[disk]`. Add any additional attributes separated by ':' and in the shape of KEY=VALUE. For example, if the disk must be resized, use `image0:size=1000`. Alternatively, `image0:size=1000:target=vda,image1:target=vdb` |
| `--disk-id disk_id`           | Uses only selected disk ID                     |   
| `--dry`                       | Just prints the template                       |
| `--end number\|TIME`          | ----                                          |
| `--endpoint endpoint`         | URL of OpenNebula xmlrpc frontend             |
| `-e`, `--enforce`             | Enforces that the Host capacity is not exceeded|
| `--expand [x=prop,y=prop]`    | Expands column size to fill the terminal. For example: `$onevm list --expand name=0.4,group=0.6` will expand name 40% and group 60%. `$onevm list --expand name,group` expands name and group based on its size. `$onevm list --expand` will expand all columns.    | 
| `--extended`                  | Shows info extended. It only works with xml output. |
| `--failure`                   | Recovers a VM by failing the pending action     |
| `-f`, `--file file`           | Selects the template file                      |
| `--files_ds file1,file2`      | Adds files to the contextualization CD from the files datastore |
| `-f`, `--filter x,y,z`        | Filters data. An array is specified with column=value pairs. Valid operators =,!=,<,<=,>,>=,~. Examples: `NAME=test` matches name with test, and  `NAME~test` matches every NAME containing the substring 'test' |
| `--hard`                      | Does not communicate with the guest OS          |
| `-h`, `--help`                | Shows this message                              |
| `--hold`                      | Creates the new VM on hold state instead of pending |
| `--hourly hour`               | Repeats the schedule action with the given hourly frequency. For example every 5 hours: `onevm resume 0 --schedule "09/23 14:15" --hourly 5` |
| `-i`, `--image id\|name`      | Selects the image                               |  
| `--increment increment_id`    | Uses the given increment ID to restore the backup. If not provided the last one will be used. |
| `--init script1,script2`      | Script or scripts to start in context           |
| `--interactive`               | Enables interactive recovery. Only works alongside the `--retry` option. |
| `-i`, `--ip ip`               | IP address for the new NIC                      |
| `-j`, `--json`                | Shows the resource in JSON format               |
| `-k`, `--kilobytes`           | Shows units in kilobytes                        |
| `-l`, `--list x,y,z`          | Selects columns to display with list command    |
| `-c`, `--listconf conf`       | Selects a predefined column list                |
| `--live`                      | Performs the action while the VM is running     |
| `--manage`                    | Locks manage actions                            | 
| `--memory memory`             | Memory amount given to the VM. By default the unit is megabytes. To use gigabytes add a `g`, floats can be used: 8g=8192, 0.5g=512 |
| `--monthly days`              | Repeats the scheduled action the days of the month specified, it can be a number between 1,31 separated with commas. For example: `onevm resume 0 --schedule "09/23 14:15" --monthly 1,14`|
| `-m`, `--multiple x`          | Instances multiple VMs                          |
| `--name name`                 | Name for the new VM                             |
| `--net_context`               | Adds network contextualization parameters       |
| `-n`, `--network id\|name`    | Selects the virtual network                     |
| `--nic network0,network1`     | Networks to attach. To use a network owned by another user run `user[network]`. Additional attributes are supported like with the `--disk` option. You can also use `auto` to let OpenNebula select the network or `dummy` to add a KVM interface without a Virtual Network |
| `--nic-id nic_id`             | NIC to use when SSH                            |
| `--nic_name name`             | Name of the NIC                                |
| `--no-expand`                 | Disables expand                                 |
| `--no-header`                 | Hides the header of the table                  |
| `--no-pager`                  | Disables pagination                             |  
| `-n`, `--numeric`             | Does not translate user and group IDs            |
| `--operator operator`         | Logical operator used on filters: AND, OR.Default: AND. |
| `--password password`         | Password to authenticate with OpenNebula       |
| `--pci short_address`         | Selects PCI device by its short address         |
| `--pci_class class ID`        | Selects PCI device by its class ID              |
| `--pci_device device ID`      | Selects PCI device by its device ID             |
| `--pci_vendor vendor ID`      | Selects PCI device by its vendor ID             |
| `--persistent`                | Makes the new images persistent                 |
| `--poff`                      | Does the migrate by poweringoff the vm           |
| `--poff-hard`                 | Does the migrate by poweringoff hard the vm      |
| `--prefix prefix`             | Overrides the DEV_PREFIX of the image          | 
| `--raw string`                | Raw string to add to the template. Not to be confused with the RAW attribute. |
| `--recreate`                  | Deletes and recreates the VM. No recovery action possible. |
| `--report_ready`              | Sends READY=YES to OneGate, useful for OneFlow. |
| `--reset`                     | Creates a new backup image, from a new full backup (only for incremental) |
| `--retry`                     | Recovers a VM by retrying the last failed action. |
| `--schedule TIME`             | Schedules this action to be executed after the given time. For example: `onevm resume 0 --schedule "09/23 14:15"` |
| `--search search`             | Queries in PATH=VALUE format. For example: `onevmlist --search "VM.NAME=abc&VM.TEMPLATE.DISK[*].IMAGE=db1"`| 
| `-s`, `--size x=size,y=size`  | Changes the size of selected columns. For example: `$ onevm list --size "name=20"` will make column *name* size 20. |
| `-s`, `--snapshot snapshot`   | ID of the Snapshot to save.                    |
| `--spice`                     | Adds spice server to the VM.                     |
| `--spice-keymap keymap`       | Spice server keyboard layout                           |
| `--spice-listen ip`           | Spice server IP where to listen for connections. By default, it is 0.0.0.0 (all interfaces).|
| `--spice-password password`   | Spice server password                                  | 
| `--ssh [file]`                | Adds an ssh public key to the context. If the file is omitted then the user variable SSH_PUBLIC_KEY will be used. |
| `--ssh-options options`       | SSH options to use                              |
| `--startscript [file]`        | Starts script to be executed                     |
| `--success`                   | Recovers a VM by succeeding the pending action   |
| `-t`, `--target target`       | Device where the image will be attached         |
| `-t`, `--type type`           | Lists type of the new Image                           |
| `--use`                       | Locks use actions                                |
| `--user name`                 | User name to connect to OpenNebula              |
| `--user-inputs ui1,ui2,ui3`   | Specifies the user inputs values when instantiating |
| `--vcpu vcpu`                 | Number of virtualized CPUs                      |
| `-v`, `--verbose`             | Verbose mode                                    |
| `-V`, `--version`             | Shows version and copyright information          |
| `--video type`                | Adds a custom video device (none, vga, cirrus, virtio) |
| `--video-ats`                 | Enables ATS (Address Translation Services) for the video device. |
| `--video-iommu`               | Enables IOMMU (I/O Memory Management Unit) for the video device. |
| `--video-resolution resolution` | Video resolution, in format like: 1280x720 or 1920x1080 |
| `--video-vram vram`           | VRAM allocated to the video device. By default the unit is megabytes. To use gigabytes add a `g`, floats can be used: 8g=8192, 0.5g=512 |
| `--vnc`                       | Adds VNC server to the VM                        |
| `--vnc-keymap keymap`         | VNC keyboard layout                             |
| `--vnc-listen ip`             | VNC IP where to listen for connections. By default it is 0.0.0.0 (all interfaces). |
| `--vnc-password password`     | VNC password                                    |
| `--weekly days`               | Repeats the scheduled action on the specified days of the week. It can be a number between 0 (Sunday) to 6 (Saturday) separated with commas. For example: `onevm resume 0 --schedule "09/23 14:15" --weekly 0,2,4`|
| `-x`, `--xml`                 | Shows the resource in xml format                 |
| `-y`, `--yaml`                | Shows the resource in YAML format                |
| `--yearly days`               | Repeats the scheduled action on the specififed days of the year. It can be a number between 0,365 separated with commas. For example: `onevm resume 0 --schedule "09/23 14:15" --yearly 30,60`|

<a href="#onevm-command">Back to The `onevm` Command</a>
