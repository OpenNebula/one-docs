---
title: "Managing Virtual Machine Instances"
linkTitle: "Instances"
date: "2025-02-17"
description: "Create and manage Virtual Machine instances, schedule actions, control permissions, and recover failed operations."
categories:
pageintoc: "93"
tags:
weight: "3"
---

<a id="vm-guide-2"></a>

<a id="vm-instances"></a>

Use the `onevm` command or Sunstone to create VM instances, manage their lifecycle, schedule actions, and control access. This guide also covers custom metadata and recovery from failed operations. For instructions on defining reusable configurations, see the [Virtual Machine Templates guide]({{% relref "product/virtual_machines_operation/virtual_machines/vm_templates.md" %}}).

For device changes, resizing, snapshots, cloning, and migration, see [Managing Virtual Machine Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md" %}}). For consoles and commands inside the guest, see [Accessing Virtual Machines]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md" %}}).

<a id="vm-life-cycle-and-states"></a>

## Virtual Machine States

The VM lifecycle includes the following states:

{{< alert title="Note" type="info" >}}
This table simplifies the lifecycle. For the complete diagram, see the [Virtual Machine States Reference]({{% relref "product/operation_references/configuration_references/vm_states.md#vm-states" %}}).{{< /alert >}}

| **Short state** | **State** | **Meaning** |
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

To deploy VM `my_vm` (ID `0`) on Host `testbed` (ID `2`), run:

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

| **Action**             | **Arguments**       |
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

Use the following commands to recover a VM from a failed or stuck operation. For Host placement and migration controls, see [Placing and Migrating VMs]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-migration" %}}).

### Troubleshooting

- `recover`: Recover a VM when an operation is stuck or boot fails. For details, see [Virtual Machine Failures]({{% relref "product/operation_references/opennebula_services_configuration/troubleshooting.md#ftguide-virtual-machine-failures" %}}). Use the following options:
  - `--success`: Simulate success of the missing driver action.
  - `--failure`: Simulate failure of the missing driver action.
  - `--retry`: Retry the current driver action. For a Transfer Manager problem, you can combine this with `--interactive`.
  - `--delete`: Delete the VM and move it to `DONE` immediately.
  - `--recreate`: Delete the VM and move it to `PENDING`.
- [`migrate` or `resched`]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-migration" %}}): Boot a VM in `UNKNOWN` on another Host, either manually with `migrate` or through the Scheduler with `resched`. Perform this action only when storage is shared or you have transferred it manually. OpenNebula does not move storage during this migration.

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

## More VM Operations

Use the resource and access guides for the following tasks:

| Task | Guide |
| --- | --- |
| <a id="disk-hotplugging"></a><a id="hotplug-devices-to-a-virtual-machine"></a><a id="hot-plugging-devices-to-a-virtual-machine"></a>Device Hot-plugging | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#hotplug-devices-to-a-virtual-machine" %}}) |
| <a id="disk-hot-plugging"></a><a id="hot-plugging-disks"></a>Disks | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#hot-plugging-disks" %}}) |
| <a id="vm-guide2-nic-hotplugging"></a><a id="nic-hot-plugging"></a><a id="hot-plugging-nics"></a>NICs | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#hot-plugging-nics" %}}) |
| <a id="nic-update"></a><a id="updating-nics"></a>NIC Updates | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#nic-update" %}}) |
| <a id="vm-guide2-sg-hotplugging"></a><a id="security-group-hot-plugging"></a><a id="hot-plugging-security-groups"></a>Security Groups | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#hot-plugging-security-groups" %}}) |
| <a id="vm-guide2-pci"></a><a id="pci-devices"></a><a id="attaching-and-detaching-pci-devices"></a>PCI Devices | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-guide2-pci" %}}) |
| <a id="vm-guide2-snapshotting"></a><a id="virtual-machine-system-snapshots"></a>System Snapshots | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#virtual-machine-system-snapshots" %}}) |
| <a id="vm-guide-2-disk-snapshots"></a><a id="virtual-machine-disk-snapshots"></a>Disk Snapshots | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#virtual-machine-disk-snapshots" %}}) |
| <a id="vm-guide-2-disk-snapshots-managing"></a><a id="managing-disk-snapshots"></a>Managing Disk Snapshots | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#managing-disk-snapshots" %}}) |
| <a id="persistent-images-and-disk-snapshots"></a>Persistent-image Snapshots | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#persistent-images-and-disk-snapshots" %}}) |
| <a id="disk-save-as-action"></a><a id="saving-a-vm-disk-to-an-image-disk-saveas"></a>Saving a Disk to an Image | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#disk-save-as-action" %}}) |
| <a id="vm-guide2-resizing-a-vm"></a><a id="resizing-vm-resources"></a>Capacity Resizing | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-guide2-resizing-a-vm" %}}) |
| <a id="live-resize-of-capacity"></a><a id="resizing-a-running-vm"></a>Running-VM Resizing | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#live-resize-of-capacity" %}}) |
| <a id="vm-guide2-resize-disk"></a><a id="resizing-vm-disks"></a>Disk Resizing | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#resizing-vm-disks" %}}) |
| <a id="vm-updateconf"></a><a id="updating-the-virtual-machine-configuration"></a>Configuration Updates | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-updateconf" %}}) |
| <a id="vm-guide2-clone-vm"></a><a id="cloning-a-virtual-machine"></a>Cloning | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#cloning-a-virtual-machine" %}}) |
| <a id="instantiate-to-persistent"></a><a id="instantiating-to-persistent"></a>Persistent Instantiation | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#instantiate-to-persistent" %}}) |
| <a id="save-a-vm-instance"></a><a id="saving-a-vm-instance"></a>Saving an Instance | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#save-a-vm-instance" %}}) |
| <a id="virtual-machine-datastore-migration"></a><a id="migrating-vm-storage-between-datastores"></a><a id="basic-syntax"></a>Datastore Migration | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#virtual-machine-datastore-migration" %}}) |
| <a id="cold-storage-migration"></a><a id="performing-cold-storage-migration"></a>Cold Storage Migration | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#cold-storage-migration" %}}) |
| <a id="live-storage-migration"></a><a id="performing-live-storage-migration"></a>Live Storage Migration | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#live-storage-migration" %}}) |
| <a id="migration-between-clusters"></a><a id="migrating-between-clusters"></a>Cluster Migration | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#migration-between-clusters" %}}) |
| <a id="scheduling"></a><a id="deployment"></a>Host Placement and Migration | [VM Resources and Storage]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#vm-migration" %}}) |
| <a id="command-execution-inside-the-virtual-machine"></a><a id="executing-commands-inside-a-virtual-machine"></a>Guest Command Execution | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#executing-commands-inside-a-virtual-machine" %}}) |
| <a id="execution-fields"></a>Execution Fields | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#execution-fields" %}}) |
| <a id="executing-a-command-from-sunstone"></a>Executing Commands from Sunstone | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#executing-a-command-from-sunstone" %}}) |
| <a id="executing-a-command-from-the-cli"></a>Executing Commands from the CLI | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#executing-a-command-from-the-cli" %}}) |
| <a id="remote-access-sunstone"></a><a id="accessing-vm-console-and-desktop"></a><a id="accessing-vm-consoles-and-desktops"></a><a id="requirements-remote-access-sunstone"></a>Console Requirements | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#remote-access-sunstone" %}}) |
| <a id="vnc-sunstone"></a><a id="configuring-your-vm-for-vnc"></a><a id="configuring-vms-for-vnc"></a>VNC | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#vnc-sunstone" %}}) |
| <a id="rdp-sunstone"></a><a id="configure-vm-for-rdp"></a><a id="configuring-vms-for-rdp"></a><a id="requirements-guacamole-rdp-sunstone"></a>RDP | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#rdp-sunstone" %}}) |
| <a id="requirements-guacamole-ssh-sunstone"></a><a id="configure-vm-for-ssh"></a><a id="configuring-vms-for-ssh"></a>SSH | [VM Access]({{% relref "product/virtual_machines_operation/virtual_machines/vm_access.md#requirements-guacamole-ssh-sunstone" %}}) |
