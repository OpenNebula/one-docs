---
title: "Host Management"
date: "2025-02-17"
description:
categories:
pageintoc: "53"
tags:
weight: "2"
---

<a id="hosts"></a>

<a id="hosts-guide"></a>

In order to use a physical or virtual server as a Host, you must first prepare the server with a hypervisor and configure it to be added to OpenNebula as a Host, refer to the guides to prepare a [KVM node]({{% relref "software/installation_process/cluster_installation/kvm_node_installation/" %}}) or an [LXC node]({{% relref "software/installation_process/cluster_installation/lxc_node_installation/" %}}).

Once you have prepared your physical or virtual nodes, you can add them to OpenNebula as Hosts. To add a Host only its hostname and type is needed. 

{{< alert title="Warning" type="warning" >}}
Before adding a Linux Host check that you can SSH to it without being prompted for a password.{{< /alert >}}

## Creating and Deleting Hosts

Hosts are the servers managed by OpenNebula responsible for running VMs. To use these Hosts in OpenNebula you need to register them so they are monitored and made available to the scheduler.

Creating a Host:

```shell
onehost create host01 --im kvm --vm kvm
ID: 0
```

The parameters are:

* `--im`: Information Manager driver.
* `--vm`: Virtual Machine Manager driver.

{{< alert title="Note" type="info" >}}
In the examples included in this guide we’ll use KVM as the hypervisor. Note that the procedure will be the same for any other hypervisor; only the name will need to be changed.{{< /alert >}}

To remove a Host you can either specify it by ID or by name. The following commands are equivalent:

```shell
onehost delete host01
onehost delete 0
```

## Showing and Listing Hosts

To display information about a single Host, use the `show` command:

```shell
onehost show server

HOST 0 INFORMATION
ID                    : 0
NAME                  : server
CLUSTER               : default
STATE                 : MONITORED
IM_MAD                : kvm
VM_MAD                : kvm
LAST MONITORING TIME  : -

HOST SHARES
RUNNING VMS           : 0
MEMORY
  TOTAL               : 31.1G
  TOTAL +/- RESERVED  : 31.1G
  USED (REAL)         : 0K
  USED (ALLOCATED)    : 0K
CPU
  TOTAL               : 800
  TOTAL +/- RESERVED  : 800
  USED (REAL)         :
  USED (ALLOCATED)    : 0

LOCAL SYSTEM DATASTORE #0 CAPACITY
TOTAL:                : 467.7G
USED:                 : 113.5G
FREE:                 : 354.2G

MONITORING INFORMATION
ARCH="x86_64"
CPUSPEED="3350"
HOSTNAME="pc-ruben"
HYPERVISOR="kvm"
IM_MAD="kvm"
KVM_CPU_MODEL="Skylake-Client-noTSX-IBRS"
KVM_CPU_FEATURES="vme,ds,acpi,ss,ht,tm,pbe,dtes64,monitor,ds_cpl,vmx,smx,est,tm2,xtpr,pdcm,pcid,dca,osxsave,arat,md-clear,stibp,ssbd,xsaveopt,pdpe1gb,invtsc"
KVM_CPU_MODELS="486 pentium pentium2 pentium3 pentiumpro coreduo n270 core2duo qemu32 kvm32 cpu64-rhel5 cpu64-rhel6 qemu64 kvm64 Conroe Penryn Nehalem Nehalem-IBRS Westmere Westmere-IBRS SandyBridge SandyBridge-IBRS IvyBridge IvyBridge-IBRS Haswell-noTSX Haswell-noTSX-IBRS Haswell Haswell-IBRS Broadwell-noTSX Broadwell-noTSX-IBRS Broadwell Broadwell-IBRS Skylake-Client Skylake-Client-IBRS Skylake-Client-noTSX-IBRS Skylake-Server Skylake-Server-IBRS Skylake-Server-noTSX-IBRS Cascadelake-Server Cascadelake-Server-noTSX Icelake-Client Icelake-Client-noTSX Icelake-Server Icelake-Server-noTSX Cooperlake Snowridge athlon phenom Opteron_G1 Opteron_G2 Opteron_G3 Opteron_G4 Opteron_G5 EPYC EPYC-IBPB EPYC-Rome Dhyana"
KVM_MACHINES="pc-i440fx-5.2 pc pc-q35-5.2 q35 pc-i440fx-2.12 pc-i440fx-2.0 pc-q35-4.2 pc-i440fx-2.5 pc-i440fx-4.2 pc-i440fx-1.5 pc-q35-2.7 pc-i440fx-2.2 pc-1.1 pc-i440fx-2.7 pc-q35-2.4 pc-q35-2.10 pc-i440fx-1.7 pc-q35-5.1 pc-q35-2.9 pc-i440fx-2.11 pc-q35-3.1 pc-q35-4.1 pc-i440fx-2.4 pc-1.3 pc-i440fx-4.1 pc-i440fx-5.1 pc-i440fx-2.9 isapc pc-i440fx-1.4 pc-q35-2.6 pc-i440fx-3.1 pc-q35-2.12 pc-i440fx-2.1 pc-1.0 pc-i440fx-2.6 pc-q35-4.0.1 pc-i440fx-1.6 pc-q35-5.0 pc-q35-2.8 pc-i440fx-2.10 pc-q35-3.0 pc-q35-4.0 microvm pc-i440fx-2.3 pc-1.2 pc-i440fx-4.0 pc-i440fx-5.0 pc-i440fx-2.8 pc-q35-2.5 pc-i440fx-3.0 pc-q35-2.11"
MODELNAME="Intel(R) Core(TM) i7-10510U CPU @ 1.80GHz"
RESERVED_CPU=""
RESERVED_MEM=""
VERSION="7.0.0"
VM_MAD="kvm"

NUMA NODES

  ID CORES        USED FREE
   0 -- -- -- --  0    8

NUMA MEMORY

 NODE_ID TOTAL    USED_REAL            USED_ALLOCATED       FREE
       0 31.1G    0K                   0K                   0K

NUMA HUGEPAGES

 NODE_ID SIZE     TOTAL    FREE     USED
       0 2M       0        0        0
       0 1024M    0        0        0

WILD VIRTUAL MACHINES

NAME                                                      DEPLOY_ID  CPU     MEMORY

VIRTUAL MACHINES

ID USER     GROUP    NAME            STAT UCPU    UMEM HOST             TIME
13 oneadmin oneadmin kvm1-13         runn  0.0   1024M server       8d 06h14
```

The information of a Host contains:

* **General information** of the Host including its name and the drivers used to interact with it.
* **Capacity** (*Host Shares*) for CPU and memory.
* **Local datastore information** (*Local System Datastore*) if the Host is configured to use a local datastore (e.g., in Local transfer mode).
* **Monitoring Information**, including PCI devices and NUMA information of the node. You can also find hypervisor specific information here.
* **Virtual Machines** allocated to the Host. *Wild* are Virtual Machines running on the Host but not started by OpenNebula.

To see a list of all the Hosts:

```shell
onehost list
  ID NAME            CLUSTER   RVM      ALLOCATED_CPU      ALLOCATED_MEM STAT
   0 server          server      1    100 / 400 (25%) 1024M / 7.3G (13%) on
   1 kvm1            kvm         0                  -                  - off
   2 kvm2            kvm         0                  -                  - off
```

The above information can be also displayed in XML, JSON, or CSV format using `-x` or `-j` or `-c`, respectively.

<a id="host-lifecycle"></a>

## Host States

In order to manage the life cycle of a Host it can be set to different operation modes: enabled (`on`), disabled (`dsbl`), and offline (`off`). The different operation status for each mode is described in the following table:

<!-- Markdown doesn't support merged cells in tables, so as a temporary workaround these are inserted in HTML -->

<table class="docutils align-default">
<thead>
<tr class="row-odd"><th class="head" rowspan="2"><p><b>OP. MODE<b></p></th>
<th class="head" rowspan="2"><p><b>MONITORING</b></b></p></th>
<th class="head" colspan="2"><p><b>VM DEPLOYMENT</b></p></th>
<th class="head" rowspan="2"><p><b>MEANING</b></p></th>
</tr>
<tr class="row-even"><th class="head"><p><b>MANUAL</b></p></th>
<th class="head"><p><b>SCHED</b></p></th>
</tr>
</thead>
<tbody>
<tr class="row-odd"><td><p>ENABLED (on)</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>The Host is fully operational</p></td>
</tr>
<tr class="row-even"><td><p>UPDATE (update)</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>The Host is being monitored</p></td>
</tr>
<tr class="row-odd"><td><p>DISABLED (dsbl)</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>No</p></td>
<td><p>Disabled, e.g. to perform maintenance operations</p></td>
</tr>
<tr class="row-even"><td><p>OFFLINE (off)</p></td>
<td><p>No</p></td>
<td><p>No</p></td>
<td><p>No</p></td>
<td><p>The Host is totally offline</p></td>
</tr>
<tr class="row-odd"><td><p>ERROR (err)</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>No</p></td>
<td><p>Error while monitoring the Host, use <code class="docutils literal notranslate"><span class="pre">onehost</span> <span class="pre">show</span></code> for the error description.</p></td>
</tr>
<tr class="row-even"><td><p>RETRY (retry)</p></td>
<td><p>Yes</p></td>
<td><p>Yes</p></td>
<td><p>No</p></td>
<td><p>Monitoring a Host in error state</p></td>
</tr>
</tbody>
</table>

## Host Operations

The `onehost` tool provides commands to set the operation mode of a Host: `disable`, `offline`, and `enable`, for example:

```shell
onehost disable 0
```

To re-enable the Host, use the `enable` command:

```shell
onehost enable 0
```

Similarly, to take the Host offline:

```shell
onehost offline 0
```

{{< alert title="Note" type="info" >}}
`onehost disable` and `onehost offline` do not change the state of VMs already running on the Host. If you need to automatically migrate running VMs use `onehost flush`.{{< /alert >}}

Apart from the commands above, the `onehost` tool also provides some commands that allow you to easily perform common operations on a Host.

You can use `forceupdate` subcommand to reset the monitoring process on the Host:

```shell
onehost forceupdate 0
```

The `flush` command will migrate all the active VMs in the specified Host to another server with enough capacity. At the same time, the specified Host will be disabled so no more Virtual Machines are deployed in it. This command is useful to clean a Host of active VMs. The migration process can be done by a `resched` action or by a recover `delete-recreate` action; it can be configured in `/etc/one/cli/onehost.yaml` by setting the field `default_actions\flush` to `delete-recreate` or to `resched`. Here is an example:

```shell
:default_actions:
  - :flush: delete-recreate
```

<a id="host-guide-information"></a>

### Custom Host Attributes

You can add custom attributes either by [creating a probe in the host]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-im#devel-im" %}}) or by updating the Host information with: `onehost update`.

For example, to label a Host as *production* we can add a custom tag *TYPE*:

```shell
onehost update
...
TYPE="production"
```

This tag can be used at a later time for scheduling purposes, [see more details here]({{% relref "../../cloud_system_administration/scheduler" %}}).

<a id="host-guide-sync"></a>

### Updating Host Files

When OpenNebula monitors a Host it copies driver files to `/var/tmp/one`. When these files are updated they need to be copied again to the Hosts with the `sync` command. To keep track of the probes version there’s a file in `/var/lib/one/remotes/VERSION`. By default this holds the OpenNebula version (e.g., ‘7.0.0’). This version can be seen in the Hosts by using `onehost show <host>`:

```shell
onehost show 0
HOST 0 INFORMATION
ID                    : 0
[...]
MONITORING INFORMATION
VERSION="7.0.0"
[...]
```

The command `onehost sync` only updates the Hosts with `VERSION` lower than the one in the file `/var/lib/one/remotes/VERSION`. In case you modify the probes this `VERSION` file should be modified with a greater value, for example “7.0.0.1”.

In case you want to force an upgrade, that is, without any `VERSION` checking, you can do it by using the `--force` option:

```shell
onehost sync --force
```

You can also select which Hosts you want to upgrade by naming them or selecting a Cluster:

```shell
onehost sync host01,host02,host03
onehost sync -c myCluster
```

<a id="host-pci-devices"></a>

### PCI Devices

The monitoring information for a Host includes details about all PCI devices detected on the node. This is particularly useful for [PCI passthrough]({{% relref "pci_passthrough" %}}) configurations, where specific devices need to be assigned to Virtual Machines. PCI devices are discovered by the Information Manager probe and can be filtered using the configuration in `/var/lib/one/remotes/etc/im/kvm-probes.d/pci.conf`.

Each PCI device reported by the monitor contains the following attributes:

| Attribute       | Type    | Present             | Description                                                                                                    |
| ---             | ---     | ---                 | ---                                                                                                            |
| `ADDRESS`       | String  | Always              | Full PCI address including domain (e.g., `0000:81:02:1`)                                                       |
| `BUS`           | String  | Always              | PCI bus number (e.g., `81`)                                                                                    |
| `CLASS`         | String  | Always              | PCI class code in hexadecimal (e.g., `0300` for VGA controller)                                                |
| `CLASS_NAME`    | String  | Always              | Human-readable class name (e.g., "VGA compatible controller")                                                  |
| `DEVICE`        | String  | Always              | PCI device ID (e.g., `10f9`)                                                                                   |
| `DEVICE_NAME`   | String  | Always              | Human-readable device name (e.g., "Tu104 Graphics Controller")                                                 |
| `DOMAIN`        | String  | Always              | PCI domain number (e.g., `0000`)                                                                               |
| `FUNCTION`      | String  | Always              | PCI function number (e.g., `1`)                                                                                |
| `NUMA_NODE`     | String  | Always              | NUMA node where the PCI device is attached (`-` if undetermined)                                               |
| `SHORT_ADDRESS` | String  | Always              | Short PCI address without domain (e.g., `81:02:1`)                                                             |
| `SLOT`          | String  | Always              | PCI slot name (e.g., `02`)                                                                                     |
| `TYPE`          | String  | Always              | PCI device type (`VENDOR:DEVICE:CLASS`)                                                                        |
| `VENDOR`        | String  | Always              | PCI vendor ID (e.g., `10de` for NVIDIA)                                                                        |
| `VENDOR_NAME`   | String  | Always              | Human-readable vendor name (e.g., "NVIDIA Corporation")                                                        |
| `VMID`          | Integer | Always              | ID of the Virtual Machine currently using this PCI device (`-1` if unassigned)                                 |
| `IFNAME`        | String  | Always              | Network interface name bound to the PCI device (e.g., `eth0`, `ens1f0`). For non-network devices, this is `-`. |
| `SRIOV`         | String  | Always              | SR-IOV role: `pf` (Physical Function), `vf` (Virtual Function), or `-` (neither)                               |
| `SRIOV_NUM`     | String  | SRIOV NIC  only     | Available Virtual Functions within a given Physical Function                                                   |
| `PROFILES`      | String  | NVIDIA vGPU VF only | Available hardware profile(s), comma-separated (e.g., `1145 (NVIDIA L40S-1B),1146 (NVIDIA L40S-2B)`)           |
| `UUID`          | String  | NVIDIA vGPU VF only | Deterministic SHA1-based identifier derived from the PCI address                                               |

#### IFNAME Resolution

The `IFNAME` attribute is resolved using multiple methods, following this precedence (first match is used):

1. **udev rules** — reads `/etc/udev/rules.d/99-rename.rules`, looking for specially formatted comments. This file is automatically generated by [OneDeploy]({{% relref "../../../solutions/ai_factory_blueprints/deployment/cd_on-premises.md" %}}) and is not intended to be edited manually. It is used to assign persistent names to network interfaces, either for convenience (custom names) or to prevent losing the standard name after VFIO takes control of the device.
2. **File cache** — consults `/var/tmp/one_db/pci_net_names/<PCI_ADDRESS>`, where each file (named as the PCI address) contains the interface name. Created automatically on first resolution.
3. **Direct sysfs lookup** — reads the directory `/sys/bus/pci/devices/<PCI_ADDRESS>/net/` to find the kernel interface name.

The cache is cleared when the monitoring daemon restarts.

<a id="import-wild-vms"></a>

## Wild VMs

The monitoring mechanism in OpenNebula reports all VMs found in a hypervisor, even those not launched through OpenNebula. These VMs are referred to as Wild VMs. The Wild VMs can be spotted through the `onehost show` command:

```shell
onehost show 3
HOST 3 INFORMATION
ID                    : 3
NAME                  : MyAWSHost
CLUSTER               : -
STATE                 : MONITORED
[...]
WILD VIRTUAL MACHINES
                    NAME                            DEPLOY_ID  CPU     MEMORY
           Ubuntu14.04VM 4223f951-243a-b31a-018f-390a02ff5c96    1       2048
                 CentOS7 422375e7-7fc7-4ed1-e0f0-fb778fe6e6e0    1       2048
```

{{< alert title="Warning" type="warning" >}}
Wild VMs’ support and limitations may differ depending on the virtualization driver used (e.g., KVM or LXC). In order to find more specific information for the virtualization driver you’re using, please check the corresponding driver guide.{{< /alert >}}

## Using Sunstone to Manage Hosts

You can also manage your Hosts using [Sunstone UI Interface]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}). Select **Infrastructure > Hosts** to create, enable, disable, delete, and see information about your Hosts in a user-friendly way.

{{< image
  pathDark="/images/host/dark/host_tab.png"
  path="/images/host/light/host_tab.png"
  alt="Sunstone Host tab" align="center" width="90%" mb="20px"
>}}

Click **Create Host** and complete the wizard to create the host.

{{< image
  pathDark="/images/host/dark/host_create.png"
  path="/images/host/light/host_create.png"
  alt="Sunstone Host create" align="center" width="90%" mb="20px"
>}}
