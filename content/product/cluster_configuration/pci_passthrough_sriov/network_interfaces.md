---
title: "Network Interfaces"
date: "2026-06-30"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "3"
---

This guide describes how to use PCI network devices as OpenNebula network interfaces.

OpenNebula extends the generic PCI passthrough mechanism by integrating PCI network devices with the Virtual Network subsystem. This allows virtual machines to benefit from the performance of direct device assignment while preserving the OpenNebula networking workflow, including IP address management, MAC address allocation, scheduling, and contextualization.

General host preparation, including IOMMU, VFIO, Huge Pages, SR-IOV configuration, and PCI monitoring, is described in the [Host Configuration]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration" %}}) guide.

## Overview

OpenNebula supports assigning both Physical Functions (PFs) and Single Root I/O Virtualization (SR-IOV) Virtual Functions (VFs) as network interfaces.

Unlike generic PCI devices, network interfaces can be fully integrated with OpenNebula Virtual Networks. During deployment, OpenNebula:

* Selects a PCI device matching the requested constraints.
* Allocates networking resources from the selected Virtual Network.
* Assigns MAC and IP addresses.
* Configures VLAN parameters when required.
* Contextualizes the guest operating system.

This provides the performance benefits of PCI passthrough while preserving the operational model of OpenNebula networking.

## Physical Functions and Virtual Functions

Modern network adapters commonly implement Single Root I/O Virtualization (SR-IOV), allowing a single Physical Function (PF) to expose multiple lightweight Virtual Functions (VFs):
* **Physical Functions**: A Physical Function represents the complete PCI device. Assigning a PF gives a virtual machine exclusive access to the network adapter and all of its capabilities.
* **Virtual Functions**: A Virtual Function is an independent PCI function created by the Physical Function. Each VF can be assigned independently to a virtual machine while sharing the underlying hardware resources.

Virtual Functions are typically used for cloud and NFV deployments because they provide excellent performance while allowing multiple virtual machines to share the same physical adapter.

### Legacy and Switchdev Modes

OpenNebula supports both SR-IOV operating modes.

* **Legacy Mode**: In Legacy mode, OpenNebula programs the Virtual Function directly. The following attributes are supported:
    * MAC
    * VLAN_ID
    * TRUST
    * SPOOFCHK
<br>

    These attributes are applied directly by the network adapter.

* **Switchdev Mode**: In Switchdev mode, VF parameters are controlled by Host-side representor interfaces. These representor interfaces can be attached to a virtual switch to establish port-level control.

    In this mode, only the MAC address is applied directly to the VF interface. All other control parameters are managed by the virtual switch driver associated with the Virtual Network.

    OpenNebula automatically configures the representor interface during deployment. As of now, only Open vSwitch is supported for Switchdev mode.

## Host Configuration

If the PCI device supports Single Root I/O Virtualization (SR-IOV), Virtual Functions (VFs) can be created and assigned independently to virtual machines. Determine the maximum number of supported Virtual Functions:

```shell
cat /sys/bus/pci/devices/<PCI_ADDRESS>/sriov_totalvfs
```

Enable the desired number of Virtual Functions:

```shell
echo 8 > /sys/bus/pci/devices/<PCI_ADDRESS>/sriov_numvfs
```

{{< alert title="Note" type="primary" >}}
The configured number of Virtual Functions is typically reset after reboot. Refer to your Linux distribution or hardware vendor documentation to configure persistent SR-IOV devices.{{< /alert >}} 

### Verification

Verify that the Virtual Functions have been created:

```shell
lspci
```

or

```shell
ip link
```

depending on the device type.

Additional SR-IOV configuration for network adapters is described in the **Network Interfaces** guide.

## Host Configuration for DPDK Interfaces

In cases where high network performance is needed but passing through PCI network interfaces to a VM is not possible, Open vSwitch can run with an accelerated datapath by using DPDK userspace libraries. In this mode, the packet processing responsibility is taken away from the kernel and dedicated resources are assigned to the packet processing. This includes CPU threads and huge pages.

The virtual network interfaces of the VM are not passed through, but the uplink backing the virtual switch normally is passed through to OVS, with the use of vfio-pci. In this section there is the host configuration required to set up DPDK.

### Installation

You need a version of OVS that has been compiled with DPDK support. Linux distributions handle the distribution of this version quite differently.

* **Ubuntu and Debian**: Use the openvswitch-switch-dpdk package. The openvswitch-switch package lacks DPDK libraries.
* **Red Hat**:
  * Activate the fast-datapath-for-rhel-<rhel_version_major>-x86_64-rpms repo in subscription manager.
  * Install any of the openvswitch<major.minor> packages. Red Hat distributes multiple versions, each with its own package.
* **Alma**:
  * Install centos-release-nfv-openvswitch to activate the required repo.
  * Install any of the openvswitch<major.minor> packages.

Verify DPDK support by checking the OVS version:

```shell
ovs-vswitchd --version
 ovs-vswitchd (Open vSwitch) 3.5.3-6.el9s
 DPDK 24.11.3
```

### Resource Allocation

It is important to have a clear picture of which resources are going to be exclusively dedicated to DPDK. These resources are effectively a payload, since they are not available to the rest of the system.

### Network Interfaces

Identify which network interfaces are going to be used as DPDK interfaces. When the system has multiple NUMA nodes, it is important to consider the node placement of these interfaces. 

To identify which node the interfaces belong to:

```shell
cat /sys/bus/pci/devices/0000\:01\:00.0/numa_nod
```

### Memory

Each Network Interface in DPDK requires a certain amount of memory in terms of hugepages. This amount of memory depends on the MTU of the interface and the NUMA node location of the interface. Whenever possible, use 1GB hugepages.

A good rule of thumb is to use 1GB per 1500 MTU NIC and 3GB per 9000+ MTU NIC. For a detailed memory calculation refer to the [memory model documentation](https://docs.openvswitch.org/en/stable/topics/dpdk/memory/) in the OpenvSwitch doc. If there are NUMA nodes without a network interface, 1GB of memory should be allocated to said NUMA node.

VMs with their virtual network interfaces backed by a DPDK capable bridge need hugepages to run as well. Therefore, more huge pages are required to consume this feature.

Refer to the Huge Pages section to configure the required amount of pages. Consider that huge pages exist on a per node basis. If the node location is unspecified when requesting hugepages, the pages will be requested evenly. Make sure enough is available per node.

VMs backed by a DPDK bridge also require hugepages. On top of the hugepages required for the OVS daemon, consider also pages for running VMs.

Every memory dedicated to hugepages is effectively memory that is no longer available for running regular non huge page backed VMs. Since dynamic huge page allocation is not guaranteed, especially with 1GB huge pages, it is important to pre-allocate in the kernel command line a reasonable number, based on a typical workload. Alternatively, 2MB huge pages could be used since they are much easier to dynamically allocate.

### CPU

The DPDK PMD driver runs continuous polling threads to process network packets. These threads are assigned to dedicated CPUs from the operating system. By default, one thread per interface in a NUMA node is used. More threads means faster polling. 

After the configuration, regardless of whether there is traffic or not in the switch, the polling processes will be using these threads at 100% usage, so it is effectively removed from the system and the linux scheduler will not use those processes normally.

For added security, you can use the isolcpus kernel parameter to declare those threads as not available to the linux scheduler, however the linux scheduler is mature enough to not need this. The important reservation comes in the OpenNebula scheduler. 

You must set the ISOCLPUS host parameter to prevent a case where the scheduler could pin VCPUs from VMs to those threads.

### Deamon Configuration

After having a clear picture of the resource allocation, it’s time to tell OVS about how to use them.

First, make sure that the daemon is enabled:

```shell
systemctl start openvswitch
systemctl enable openvswitch
```

Then initialize DPDK and signal the huge table mountpount:

```shell
ovs-vsctl set Open_vSwitch . other_config:dpdk-init=true
ovs-vsctl set Open_vSwitch . other_config:dpdk-hugepage-dir="/dev/hugepages"
```

This mountpoint should be automatically managed by a system where libvirt is installed. It is an interface to consume the pages of the size specified in that mountpoint:

```shell
mount | grep -i huge
 hugetlbfs on /dev/hugepages type hugetlbfs 
 (rw,relatime,seclabel,pagesize=1024M)
```
To assign the previously reserved huge pages to DPDK use the` other_config:dpdk-socket-mem` parameter. This is a comma separated list of memory, in MB, to allocate per node, which will then be backed by the huge pages available at `other_config:dpdk-hugepage-dir`. 

### Examples

A system has 2 NUMA nodes. Two network interfaces are going to be used as DPDK interfaces. Each interface is in a different NUMA node. The interfaces will have 1500 MTU. 1GB hugepages are used. 2 pages are required in each node:

```shell
ovs-vsctl set Open_vSwitch . other_config:dpdk-socket-mem=1024,1024
```

A system has 1 NUMA node. Two network interfaces are going to be used as DPDK interfaces. The interfaces will have 9000 MTU. 1GB hugepages are used. 6 pages are required:

```shell
ovs-vsctl set Open_vSwitch . other_config:dpdk-socket-mem=6144
```

A system has 4 NUMA nodes. Two network interfaces are going to be used as DPDK interfaces. Interfaces are located in node0 and node1. The interfaces will have 9000 MTU. 1GB hugepages are used. 3 pages are required in node0 and node1 each.1 page is required in node2 and 3 each.

```shell
ovs-vsctl set Open_vSwitch . other_config:dpdk-socket-mem=3072,3072,1024,1024
```

### PMD Threads

The CPU threads where OVS will pin the PMD threads  are signaled with the parameter `other_config:pmd-cpu-mask`. It is a hex bitmask. Each bit represents a specific logical CPU ID. At least one CPU thread per node is needed. When assigning multiple threads per node, it is recommended to pick threads sharing the same physical CPU core.

To generate the value of the bitmask:

* Inspect the CPUs available in the Operating System. To get a full picture of this, run the command lscpu --all -p=CPU,CORE,NODE. 
* This will yield a list of logical CPU threads ids, their respective parent logical core id and the NUMA node they belong to. 
* Create a comma separated list of the CPU IDs going to be used according to recommendations.
* Create a binary bitmask with each desired CPU thread ID set to 1. 
* Convert to hex.

Example:

```shell
lscpu --all -p=CPU,CORE,NODE
 # The following is the parsable format, which can be fed to other
 # programs. Each different item in every column has an unique ID
 # starting usually from zero.
 # CPU,Core,Node
 0,0,0 # pick
 1,1,1 # pick
 2,2,0
 ...
```

Core 0 in node 0 holds threads 0 and 64. Core 1 in node 1 holds threads 1 and 65. The string `0,1,64,65` should be used as the ISOLCPUS parameter in the hypervisor node configuration.

```shell
echo "ISOLCPUS=\"0,1,64,65\"" > /tmp/dpdk-host.tpl
onehost update sm15 -a /tmp/dpdk-host.tpl
```

The subsequent mask is then applied:

```shell
ovs-vsctl set Open_vSwitch . other_config:pmd-cpu-mask=0x30000000000000003
```

Restart the openvswitch daemon so it loads all of the DPDK related configurations:

```shell
systemctl restart openvswitch
```

### Verification

Check OVS is properly configured. Make sure that DPDK is initialized and the configuration values we established for the OVS daemon are loaded:

```shell
ovs-vsctl get Open_vSwitch . dpdk_initialized
grep DPDK /var/log/openvswitch/ovs-vswitchd.log 
ovs-vsctl get Open_vSwitch . other_config:dpdk-socket-mem 
ovs-vsctl get Open_vSwitch . other_config:pmd-cpu-mask 
ovs-vsctl get Open_vSwitch . other_config:dpdk-hugepage-dir
```

### Bridge Creation

The OVS DPDK bridge must be pre-created before being used in OpenNebula. Besides some extra configuration, most of the normal OVS bridge related configurations apply. There are two elements that distinguish a DPDK bridge from a regular bridge: accelerated datapath and the use of DPDK interfaces.

A DPDK bridge is created as follows:

```shell
ovs-vsctl --may-exist add-br 'ovsbr0' -- set Bridge 'ovsbr0' 'datapath_type=netdev'
```

Then the DPDK interfaces must be assigned to that bridge. Normally, those interfaces need to have their kernel driver unbound and use instead the `vfio-pci` driver used for passthrough. However, there are cases where the kernel driver must not be unbound. This is the case for the `MT27710 Family [ConnectX-4 Lx] 1015` Mellanox network interfaces using the `mlx5_core` driver.

Refer to the PCI Device VFIO binding section for this procedure. Alternatively, use the utility `dpdk-devbind.py` provided by the DPDK related packages. It allows to rebind interfaces as well, without the use of `driverctl` and it also provides a summary of every PCI device related property.

```shell
dpdk-devbind.py --status-dev net

 Network devices using DPDK-compatible driver
 ============================================
 0000:01:00.0 'BCM57416 NetXtreme-E Dual-Media 10G RDMA Ethernet Controller 16d8' numa_node=0 drv=vfio-pci unused=bnxt_en
 0000:01:00.1 'BCM57416 NetXtreme-E Dual-Media 10G RDMA Ethernet Controller 16d8' numa_node=0 drv=vfio-pci unused=bnxt_en
 0000:81:00.2 'MT27710 Family [ConnectX-4 Lx Virtual Function] 1016' numa_node=0 drv=vfio-pci unused=mlx5_core
 ...
```

After the interface is ready, attach it to the bridge:

```shell
ovs-vsctl add-port ovsbr0 dpdk0 -- set Interface dpdk0 \
type=dpdk options:dpdk-devargs=<PCI_ADDR> # replace <PCI_ADDR> with the network interface PCI device address
```

In this case `dpdk0` was the name used for the interface and the port. This name is not important as the interface is referenced by its PCI address. vfio-pci bound interfaces do not even have names. What’s important is that the said name must be unique per interface.

If using multiple interfaces in bond, first create the bond normally, then attach the interfaces to the bond port. For example:

```shell
ovs-vsctl add-bond 'ovsbr0' 'bond0' 'dpdk0' 'dpdk1' 'bond_mode=balance-slb' \
    -- set Interface 'vmnic0' 'type=dpdk' \
    -- set Interface 'vmnic0' 'options:dpdk-devargs=0000:01:00.0' \
    -- set Interface 'vmnic0' 'mtu_request=9126' \
    -- set Interface 'vmnic1' 'type=dpdk' \
    -- set Interface 'vmnic1' 'options:dpdk-devargs=0000:01:00.1' \
    -- set Interface 'vmnic1' 'mtu_request=9126' \
```

After binding interfaces you should now start seeing the PMD threads at 100% CPU usage. This is expected and will happen regardless of whether that bridge is serving traffic to VMs or not.

If the DPDK interface  holds an IP address which is needed, this IP address must be migrated to the OVS bridge internal interface. It has the same name as the bridge. This interface can be configured like regular system interfaces. We recommend setting all of the L2 related configuration in OVS directly and only manage the IP related configuration outside of OVS, you can use manual commands or the system network renderer for this. 

If the interface is a management interface then you must ensure a proper IP migration via a script since binding the network interface and submitting it to a bridge makes it lose connectivity.

### Security Configuration

Depending on your distro, it might be required to tune Selinux or AppArmor to allow proper OVS-QEMU interaction. 

When a VM is created, qemu creates a UNIX socket for each network interface backed by a DPDK capable bridge. OVS then attempts to connect to these sockets. Some operations involving VM states, like migrations and power cycles require qemu also to perform an unlink operation in the socket.

Selinux or AppArmor can, at any given time block any of these operations. This is affected also by how the Operating System distributes the OVS binary. In the case of the Red Hat familiy, OVS runs with a dedicated user. In the case of the Debian family, OVS runs as root. This might cause issues with directory based permissions, depending on the location of the socket. These sockets, starting from OpenNebula 7.2.1+ are located at `/var/run/one/vhost-socks/`.

Below is a reference of the configuration required for Selinux systems. If errors persist after creating VMs, check the system logs, especially the audit logs, for operations being blocked if you still see permission denied errors but permissions look correct:

```shell
sudo chcon -t virt_var_run_t /var/run/one/vhost-socks/

TDIR=$(mktemp -d)
cat << 'EOF' > "$TDIR/dpdk_virt.te"
module dpdk_virt 1.0;
require {
    type openvswitch_t;
    type virt_var_run_t;
    class dir { search getattr read open };
    class sock_file { write getattr append };
}
allow openvswitch_t virt_var_run_t:dir { search getattr read open };
allow openvswitch_t virt_var_run_t:sock_file { write getattr append };
EOF

checkmodule -M -m -o "$TDIR/dpdk_virt.mod" "$TDIR/dpdk_virt.te"
semodule_package -o "$TDIR/dpdk_virt.pp" -m "$TDIR/dpdk_virt.mod"
sudo semodule -i "$TDIR/dpdk_virt.pp"
rm -rf "$TDIR"
sudo setfacl -m u:openvswitch:rx /var/run/one/
sudo setfacl -m u:openvswitch:rx /var/run/one/vhost-socks/
sudo setfacl -d -m u:openvswitch:rwX /var/run/one/vhost-socks/
```

Refer to the OpenvSwitch with DPDK section for the Virtual Network configuration and reference VM Templates.

### Security Configuration

You can use the [openvswitch role](https://github.com/OpenNebula/one-deploy/blob/dbbec90d80a0a6a7e598b9a55169b0050a8c7c9f/roles/openvswitch/README.md#L16) to automate all of the DPDK related configuration and standalone OVS complex configurations as well. 

## Using PCI Devices as Network Interfaces

To use a PCI device as a network interface, set the `TYPE` attribute of the `PCI` element to `NIC`. Example:

```default
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET"
]
```

Unlike generic PCI passthrough, a PCI device configured as a network interface becomes part of the OpenNebula networking subsystem.

During deployment, OpenNebula:

1. Selects a compatible PCI device.  
2. Allocates networking resources from the specified Virtual Network.  
3. Configures the PCI device.  
4. Generates the corresponding NIC context information.  
5. Contextualizes the guest operating system.

As a result, the guest receives a fully configured network interface without additional manual configuration.

## Selecting PCI Devices

PCI devices may be selected explicitly or automatically.

### Automatic Selection

Automatic selection is the recommended approach. Instead of specifying a PCI address, define the required device characteristics.

Example:

```
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",

  CLASS = "0200",
  VENDOR = "15b3"
]
```

The scheduler automatically selects an available PCI device satisfying the specified constraints. Automatic selection improves workload portability across hosts.

### Explicit Device Selection

Specific devices may also be selected using their PCI address.

Example:

```
PCI = [
  TYPE = "NIC",
  DEVICE = "0000:81:00.4"
]
```

Explicit selection should generally be reserved for specialized deployments where the VM needs to be attached to specific networks.

## Virtual Network Integration

Unlike generic PCI passthrough, PCI network interfaces participate fully in OpenNebula Virtual Networks. The selected Virtual Network provides:

* MAC address allocation  
* IPv4 allocation  
* IPv6 allocation  
* VLAN configuration  
* Security Groups  
* Address management

This allows PCI passthrough interfaces to behave consistently with virtual network interfaces from the administrator's perspective.

## Contextualization

When the Context package is installed inside the guest operating system, OpenNebula automatically configures the assigned PCI interface. The guest receives:

* MAC address  
* IPv4 address  
* IPv6 address  
* Network mask  
* Gateway  
* DNS configuration  
* Hostname

No manual network configuration is required inside the guest.

## Supported PCI Attributes

PCI network interfaces support the standard PCI attributes together with networking-specific attributes.

Common PCI attributes include:

* `DEVICE`  
* `CLASS`  
* `VENDOR`  
* `TYPE`

Network-specific attributes include:

* `NETWORK`  
* `NETWORK_UNAME`  
* `MAC`  
* `IP`  
* `IP6`  
* `VLAN_ID`  
* `TRUST`  
* `SPOOFCHK`

Refer to the Virtual Machine Template reference for a complete description of each attribute.

## Supported PCI Attributes

PCI network interfaces support the standard PCI attributes together with networking-specific attributes.

Common PCI attributes include:

* `DEVICE`  
* `CLASS`  
* `VENDOR`  
* `TYPE`

Network-specific attributes include:

* `NETWORK`  
* `NETWORK_UNAME`  
* `MAC`  
* `IP`  
* `IP6`  
* `VLAN_ID`  
* `TRUST`  
* `SPOOFCHK`

Refer to the Virtual Machine Template reference for a complete description of each attribute.

## Guest Verification

After deployment, verify that the guest detects the assigned network adapter.

Display the PCI devices:

```shell
lspci
```

Display the network interfaces:

```shell
ip link
```

The interface should appear as a native PCI network adapter and be configured automatically through contextualization.

## Best Practices

* Prefer automatic PCI device selection whenever possible.  
* Use Virtual Functions instead of Physical Functions for cloud deployments.  
* Reserve Physical Functions for workloads requiring exclusive device ownership.  
* Configure PCI monitoring to expose only passthrough devices.  
* Install the OpenNebula Context package in guest operating systems.  
* Use NUMA-aware placement for latency-sensitive workloads.  
* Prefer Switchdev mode when integrating with Open vSwitch.

## Next Steps

If you have not yet configured the host for PCI passthrough, complete the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). For NVIDIA GPUs, continue with the [NVIDIA GPU Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}).