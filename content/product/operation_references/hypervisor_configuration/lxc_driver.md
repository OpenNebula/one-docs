---
title: "LXC Driver"
date: "2025-02-17"
description:
categories:
pageintoc: "181"
tags:
weight: "3"
---

<a id="lxdmg"></a>

<a id="lxcmg"></a>

<!--# LXC Driver -->

## Requirements

- LXC version >= 3.0.3 installed on the Host.
- cgroup version 1 or 2 Hosts are required to implement resource control operations (e.g., CPU pinning, memory or swap limitations).

## Considerations & Limitations

### Privileged Containers and Security

In order to ensure security in a multitenant environment, by default the containers created by the LXC driver will be unprivileged. The unprivileged containers will be deployed as `root`. Sub UID/GID range `600100001-600165537` will be used for mapping users/groups in order to increase security in case a malicious agent is able to escape the container.

To create a privileged container, the attribute `LXC_UNPRIVILEGED = "no"` needs to be added to the VM template. The generated container will include a file with a set of container configuration parameters for privileged containers. This file is located in the Front-end at **/var/lib/one/remotes/etc/vmm/lxc/profiles/profile_privileged** (see below for its contents). You can be fine-tune this file if needed (don’t forget to sync the file using the command onehost sync).

```default
lxc.mount.entry = 'mqueue dev/mqueue mqueue rw,relatime,create=dir,optional 0 0'
lxc.cap.drop = 'sys_time sys_module sys_rawio'
lxc.mount.auto = 'proc:mixed'
lxc.mount.auto = 'sys:mixed'
lxc.cgroup.devices.deny = 'a'
lxc.cgroup.devices.allow = 'b *:* m'
lxc.cgroup.devices.allow = 'c *:* m'
lxc.cgroup.devices.allow = 'c 136:* rwm'
lxc.cgroup.devices.allow = 'c 1:3 rwm'
lxc.cgroup.devices.allow = 'c 1:5 rwm'
lxc.cgroup.devices.allow = 'c 1:7 rwm'
lxc.cgroup.devices.allow = 'c 1:8 rwm'
lxc.cgroup.devices.allow = 'c 1:9 rwm'
lxc.cgroup.devices.allow = 'c 5:0 rwm'
lxc.cgroup.devices.allow = 'c 5:1 rwm'
lxc.cgroup.devices.allow = 'c 5:2 rwm'
lxc.cgroup.devices.allow = 'c 10:229 rwm'
lxc.cgroup.devices.allow = 'c 10:200 rwm'
```

### CPU and NUMA Pinning

You can pin containers to Host CPUs and NUMA nodes simply by adding a `TOPOLOGY` attribute to the VM template, [see the use Virtual Topology and CPU Pinning guide]({{% relref "../../cluster_configuration/hosts_and_clusters/numa#numa" %}})

### Supported Storage Formats

- Datablocks require formatting with a file system in order to be attached to a container.
- Disk images must be a file system, they cannot have partition tables.

<a id="lxc-unsupported-actions"></a>

### Container Actions

Some of the VM actions available in the OpenNebula API are not implemented yet for the LXC driver:

- [live migration](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#advanced-operations-for-administrators)
- [live disk resize](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#resizing-vm-disks)
- [vm state save and restore](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#save-a-vm-instance)
- [system snapshots](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#virtual-machine-system-snapshots)
- [live disk snapshots](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#virtual-machine-disk-snapshots) with qcow2 disks.
- [live disk save](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#saving-a-vm-disk-to-an-image)
- [live capacity resize](../../virtual_machines_operation/virtual_machine_instances/vm_instances.md#live-resize-of-capacity)

### PCI Passthrough

You can perform NIC PCI Passthrough on containers. The PCI NICs must first be monitored on the LXC hosts. The configuration file for PCI device detection is `/var/lib/one/remotes/etc/im/lxc-probes.d/pci.conf`. Once monitoring is successful, add the PCI NIC to the VM Template or hot-plug it. See [Using PCI Devices as Network Interfaces]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces#using-pci-devices-as-network-interfaces" %}}) for PCI selection syntax.

Example PCI device monitoring

```bash
onehost show 1 -j | jq .HOST.HOST_SHARE.PCI_DEVICES.PCI[-1]
{
  "ADDRESS": "0000:00:08:0",
  "BUS": "00",
  "CLASS": "0200",
  "CLASS_NAME": "Ethernet controller",
  "DEVICE": "100e",
  "DEVICE_NAME": "82540EM Gigabit Ethernet Controller",
  "DOMAIN": "0000",
  "FUNCTION": "0",
  "NUMA_NODE": "-",
  "SHORT_ADDRESS": "00:08.0",
  "SLOT": "08",
  "TYPE": "8086:100e:0200",
  "VENDOR": "8086",
  "VENDOR_NAME": "Intel Corporation",
  "VMID": "-1"
}
```

NIC declaration in VM Template

```
PCI=[
  NETWORK="public",
  NETWORK_ID="0",
  NETWORK_UID="0",
  NETWORK_UNAME="oneadmin",
  SHORT_ADDRESS="00:08.0",
  TYPE="NIC" ]
```

Hot-plug that device with `onevm nic-attach $VM_ID -n $VNET_ID --pci "00:08.0"`
### Wild Containers

Importing wild containers that weren’t deployed by OpenNebula is not currently supported.

## Configuration

### OpenNebula

The LXC driver is enabled by default in OpenNebula `/etc/one/oned.conf` on your Front-end Host with reasonable defaults. Read the [oned Configuration]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-virtualization-drivers" %}}) to understand these configuration parameters and [Virtual Machine Drivers Reference]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-vmm#devel-vmm" %}}) to know how to customize and extend the drivers.

### Driver

LXC driver-specific configuration is available in `/var/lib/one/remotes/etc/vmm/lxc/lxcrc` on the OpenNebula Front-end node. The following list contains the supported configuration attributes and a brief description of each:

| Parameter             | Description                                                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `:vnc`                | Options to customize the VNC access to the<br/>microVM. `:width`, `:height`, `:timeout`, and<br/>`:command` can be set          |
| `:datastore_location` | Default path for the datastores. This only needs to be<br/>changed if the corresponding value in oned.conf has<br/>been modified |
| `:default_lxc_config` | Path to the LXC default configuration file. This file<br/>will be included in the configuration of every LXC<br/>container      |

Mount options configuration section also in lxcrc:

| `:bindfs`     | Comma-separated list of mount options used when shifting the<br/>uid/gid with bindfs. See <bindfs -o> command help   |
|---------------|----------------------------------------------------------------------------------------------------------------------|
| `:dev_<fs>`   | Mount options for disk devices (in the Host). Options are set per<br/>fs type (e.g. dev_xfs, dev_ext3…)              |
| `:disk`       | Mount options for data DISK in the container (lxc.mount.entry)                                                       |
| `:rootfs`     | Mount options for root fs in the container (lxc.rootfs.options)                                                      |
| `:mountpoint` | Default Path to mount data disk in the container. This can be<br/>set per DISK using the TARGET attribute            |

## Storage

LXC containers need a root file system image in order to boot. This image can be downloaded directly to OpenNebula from [Linux Containers](https://images.linuxcontainers.org/) Marketplace. Check the [Public Marketplaces]({{% relref "../../apps-marketplace/public_marketplaces/index#public-marketplaces" %}}) chapter for more information. You can use LXC with NAS (file-based), SAN (lvm) or Ceph Datastores.

When using XFS images it is recommended to use images with a block size of 4K as it is the default block size for mounting the file system. Otherwise it's possible you will get an error like the one below:

```none
Mon Apr  4 22:20:25 2022 [Z0][VMM][I]: mount: /var/lib/one/datastores/0/30/mapper/disk.1: mount(2) system call failed: Function not implemented.
```

{{< alert title="Note" type="info" >}}
Custom images can also be created by using common linux tools like the `mkfs` command for creating the file system and `dd` for copying an existing file system inside the new one. Also, OpenNebula will preserve any custom id map present on the filesystem.{{< /alert >}}

## Networking

LXC containers are fully integrated with every OpenNebula networking driver.

## Usage

### Container Template

Container templates can be defined by using the same attributes described in [Virtual Machine Template section]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#vm-templates" %}}).

```default
CPU="1"
MEMORY="146"
CONTEXT=[
  NETWORK="YES",
  SSH_PUBLIC_KEY="$USER[SSH_PUBLIC_KEY]" ]
DISK=[
  IMAGE="Alpine Linux 3.11",
  IMAGE_UNAME="oneadmin" ]
GRAPHICS=[
  LISTEN="0.0.0.0",
  TYPE="VNC" ]
NIC=[
  NETWORK="vnet",
  NETWORK_UNAME="oneadmin",
  SECURITY_GROUPS="0" ]
```

The LXC driver will create a swap limitation equal to the amount of memory defined in the VM template. The attribute `LXC_SWAP` can be used to declare extra swap for the container.

### Remote Access

Containers support remote access via VNC protocol which allows easy access to them. The following section must be added to the Container template to configure the VNC access:

```default
GRAPHICS=[
  LISTEN="0.0.0.0",
  TYPE="VNC" ]
```

### Additional Attributes

The `RAW` attribute allows us to add raw LXC configuration attributes to the final container deployment file. This permits us to set configuration attributes that are not directly supported by OpenNebula:

```default
RAW = [
  TYPE = "lxc",
  DATA = "lxc.signal.reboot = 9" ]
```

{{< alert title="Note" type="info" >}}
Each line of the `DATA` attribute must contain only an LXC configuration attribute and its corresponding value. If a provided attribute is already set by OpenNebula, it will be discarded and the original value will take precedence.{{< /alert >}}

The `LXC_PROFILES` attribute implements a similar behavior to [LXD profiles](https://linuxcontainers.org/lxd/advanced-guide/#profiles). It allows users to include pre-defined LXC configuration to a container. In order to use a profile, the corresponding LXC configuration file must be available at `/var/lib/one/remotes/etc/vmm/lxc/profiles`.

For example, if you want to use the profiles `production` and `extra-performance`, you need to create the corresponding files containing the LXC configuration attributes (using lxc config syntax):

```default
$ ls -l /var/lib/one/remotes/etc/vmm/lxc/profiles
...
-rw-r--r-- 1 oneadmin oneadmin 40 abr 26 12:35 extra-performance
-rw-r--r-- 1 oneadmin oneadmin 35 abr 26 12:35 production
```

{{< alert title="Warning" type="warning" >}}
After defining the profiles, make sure `oneadmin` user has enough permission to read them. Also, remember to use `onehost sync` command to make sure the changes are synced in the Host. If the profile is not available in the Host, the container will be deployed without including the corresponding profile configuration.{{< /alert >}}

After defining the profiles they can be used by adding the `PROFILES` attribute to the VM template:

```default
PROFILES = "extra-performance, production"
```

Profiles are implemented by using the LXC `include` configuration attribute. Note that the profiles will be included in the provided order and this order might affect the final configuration of the container.

### Troubleshooting

On top of the regular OpenNebula logs at `/var/log/one` the LXC driver generates additional logs for more specific LXC operations. Sometimes a container might fail to start or not behave as intended. You can find out more about what happened by inspecting the log files at `/var/log/lxc/`

- `one-<vm_id>.console` - Contains the console output seen when starting a container. This contains information regarding how the init process within the container starts. It can also help identify problems that occur after a successful start yet a failed initialization.
- `one-<vm_id>.log` - Contains information about how LXC handles different container operations.

You can also verify the low level configuration of the container generated by OpenNebula when inspecting the file `/var/lib/lxc/one-<vm_id>/config`.

#### Common issues

- Sometimes it might happen that the Guest OS refuses to start completely or some systemd services fail to start. In this cases it might be worth using [Privileged Containers](#privileged-containers-and-security)
- When running Linux distributions with [AppArmor](https://documentation.ubuntu.com/server/how-to/security/apparmor/index.html), it might be necessary to relax this configuration, otherwise services like [one-context]({{% relref "kvm_contextualization#kvm-contextualization" %}}) have dependencies which do not start. For this you can set the following [RAW configuration](#additional-attributes)

```
RAW = [
  TYPE = "lxc",
  DATA = "lxc.apparmor.profile=unconfined" ]
```
