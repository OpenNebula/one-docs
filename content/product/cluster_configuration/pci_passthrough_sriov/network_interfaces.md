---
title: "Network Interfaces with PCI Passthrough"
linkTitle: "Network Interfaces"
date: "2026-06-30"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "4"
---

This guide describes how to use PCI network devices as OpenNebula network interfaces.

OpenNebula extends the generic PCI passthrough mechanism by integrating PCI network devices with the Virtual Network subsystem. This allows virtual machines to benefit from the performance of direct device assignment while preserving the OpenNebula networking workflow, including IP address management, MAC address allocation, scheduling, and contextualization.

General Host preparation, including IOMMU, VFIO, Huge Pages, SR-IOV configuration, and PCI monitoring, is described in the [Host Configuration]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration" %}}) guide.

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
* **Physical Functions (PF)**: A Physical Function represents the complete PCI device. Assigning a PF gives a virtual machine exclusive access to the network adapter and all of its capabilities.
* **Virtual Functions (VF)**: A Virtual Function is an independent PCI function created by the Physical Function. Each VF can be assigned independently to a virtual machine while sharing the underlying hardware resources.

Virtual Functions are typically used for cloud and NFV deployments because they provide excellent performance while allowing multiple virtual machines to share the same physical adapter.

### eSwitch modes

OpenNebula supports **Legacy** and **Switchdev** operating modes on the PF eSwitch. In each mode, the PF is configured according to the following parameters

* `MAC`: Administrative MAC address assigned to the VF.
* `MTU`: Requested MTU, applied according to the eSwitch mode as described below.
* `TRUST`: Allows the VF within the Guest to operate in promiscuous mode.
* `SPOOFCHK`: MAC spoofing filter for the administrative MAC. Separate from the virtual switching spoofing.

#### Legacy Mode

In Legacy mode, VLAN filtering can only be done with access vlans using the `VLAN_ID` parameter.

OpenNebula raises the PF MTU when required and does not lower it for smaller requests. Whether the PF MTU limits its VFs depends on the hardware and PF driver. OpenNebula does not configure separate per-VM MTU caps in Legacy mode.

#### Switchdev mode

In Switchdev mode, VF parameters are controlled by Host-side representor interfaces. These representor interfaces are attached to a virtual switch to establish port-level control. Control parameters are managed by the virtual switch driver associated with the Virtual Network. OpenNebula automatically configures the representor interface during deployment. Only Open vSwitch is supported for Switchdev mode. The following parameters are supported

* `VLAN_ID`
* `VLAN_TAGGED_ID`
* `CVLANS`
* `QINQ_TYPE`

OpenNebula also sets the VF representor MTU to the requested VM NIC MTU. This value can be raised or lowered independently while retaining the higher PF MTU. Its effect on VF traffic depends on the NIC, driver, and offload behavior.

Note that `TRUST` and `SPOOFCHK` might fail depending on the kernel driver controlling the PF, even if setting them to the state they are currently already at. If the attribute is unsupported (refer to the SmartNIC documentation) then it should be ommited from the Virtual Network configuration, otherwise the whole configuration fails.

To use one Virtual Network across multiple switchdev PFs, configure the Virtual Network with:

```text
VN_MAD = "ovswitch"
BRIDGE = "switchdev"
```

Include the usual address ranges and VLAN settings for your network. In the VM template, reference this Virtual Network from a `PCI` device with `TYPE="NIC"`, as shown under [Virtual Machine Template](#virtual-machine-template). Ordinary virtual NICs and direct PF passthrough are not supported with `BRIDGE=switchdev`.

OpenNebula discovers the parent PF of the selected VF on the deployment host, so you do not need to specify `PHYDEV`. It creates an Open vSwitch bridge named `<PF-interface-name>br` and adds the PF and the selected VF's representor as ports. For example, PF interface `ens1f0` uses bridge `ens1f0br`. Additional VFs from the same PF reuse that bridge; VFs from other PFs use separate bridges. VLAN settings are applied to each VF's representor.

The host must already have SR-IOV configured, the PF operating in switchdev mode, and the VF representor available. Setting `BRIDGE=switchdev` does not enable these hardware features. PF interface names must contain at most 13 characters because the generated bridge name is limited to 15 characters. The PF must be unattached to an OVS bridge or already belong to its generated bridge; configuration fails if it belongs to another bridge.


##### Example: One Virtual Network Across Two PFs

Consider a host with two switchdev PFs and the following VF mapping. PCI addresses and interface names are examples; replace them with those from your host.

| VF PCI address | Parent PF interface | VF representor | Generated bridge |
| --- | --- | --- | --- |
| `81:00.2` | `pf0` | `eth8` | `pf0br` |
| `81:02.1` | `pf1` | `eth7` | `pf1br` |

Create a Virtual Network with the following template. Adjust the address range and VLANs to match your network:

```text
NAME = "sriov-switchdev"
VN_MAD = "ovswitch"
BRIDGE = "switchdev"
VLAN_TAGGED_ID = "727,728,729"
AR = [ TYPE = "IP4", IP = "192.0.2.10", SIZE = "10" ]
```

Add both VFs to a VM template, referencing the same Virtual Network:

```text
PCI = [
  TYPE = "NIC",
  NETWORK = "sriov-switchdev",
  SHORT_ADDRESS = "81:00.2"
]
PCI = [
  TYPE = "NIC",
  NETWORK = "sriov-switchdev",
  SHORT_ADDRESS = "81:02.1"
]
```

After deploying the VM, run `sudo ovs-vsctl show` on its host. The relevant parts of the output should look like:

```text
Bridge pf0br
    Port pf0
        Interface pf0
    Port eth8
        trunks: [727, 728, 729]
        Interface eth8
Bridge pf1br
    Port pf1
        Interface pf1
    Port eth7
        trunks: [727, 728, 729]
        Interface eth7
```

Both VFs receive their network configuration from `sriov-switchdev`, while each PF and its VF representor use a separate bridge. Additional VFs from `pf0` reuse `pf0br`; additional VFs from `pf1` reuse `pf1br`.


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

## Using PCI Devices as Network Interfaces

### Sunstone

When creating or editing a Virtual Machine Template, open **Advanced options** and select the **Network** tab. In the network interface's **Hardware** section, set **Device Type** to **SR-IOV** for a VF or **PCI Passthrough** for a physical device. Then choose a **Scheduling mode**:

* **Automatic**: the scheduler selects an available PCI network function matching the selected device characteristics.
* **Manual**: you select the exact PCI address to assign.
* **Physical function** (SR-IOV only): select or enter the parent PF's interface name. OpenNebula allocates an available VF from that PF on the scheduled Host.

The **Physical function** list shows the PF interface names, Hosts, PCI addresses, available/total monitored VF counts, and e-switch modes when available. Entries with the same interface name are grouped across Hosts, and their counts are summed. Selecting an entry stores `PF_IFNAME`; it does not pin the VM to a Host shown in the list. For the monitoring requirements and placement examples, see [Selecting Virtual Functions by Physical Function](#selecting-virtual-functions-by-physical-function).

Select the Virtual Network and configure the remaining interface attributes as required. The same hardware options are available when attaching a network interface to a VM.

{{< image
  pathDark="/images/host/dark/host_vm_nic_passthrough.png"
  path="/images/host/light/host_vm_nic_passthrough.png"
  alt="Configuring a PCI passthrough network interface in Sunstone" align="center" width="90%" mb="20px"
>}}

### Virtual Machine Template

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

The scheduler automatically selects an available PCI device satisfying the specified constraints. Automatic selection improves workload portability across Hosts.

### Explicit Device Selection

Specific devices may also be selected using their PCI address.

Example:

```
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",
  SHORT_ADDRESS = "81:00.4"
]
```

`SHORT_ADDRESS` selects the physical PCI function, while `NETWORK` selects the OpenNebula Virtual Network that provides its network configuration and leases. Explicit device selection should generally be reserved for deployments that require a particular physical interface because of its PCI topology, interconnection, or NUMA locality.

### Selecting Virtual Functions by Physical Function

To allocate an available VF from a particular PF, set one of the following attributes in the VM Template's `PCI` entry:

| **Attribute** | **Description** |
|-------------|-------------------|
| `PF_IFNAME` | Interface name of the parent PF on the Host, for example `pf0`. Copy the PF's `IFNAME` or the VF's monitored `PF_IFNAME`. |
| `PF_ADDRESS` | Full monitored `ADDRESS` of the parent PF, for example `0000:81:00:0`. Copy this value from the Host PCI inventory; it uses a colon before the function number. |

OpenNebula selects a free VF belonging to that PF. You choose the parent PF, and OpenNebula chooses the individual VF. Sunstone's **Physical function** scheduling mode uses `PF_IFNAME`; to select by `PF_ADDRESS`, define the selector in the VM Template text.

Before using this selection:

* Enable enough VFs on each required PF, as described in [Host Configuration](#host-configuration).
* Configure the [PCI monitoring filters]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration.md#step-4-configure-pci-monitoring" %}}) to include both the PF and its VFs. A filter matching only `Virtual Function` excludes the PF and prevents selection by parent PF. Host and Cluster filters must also include the required functions.
* Check the [Host PCI inventory]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts.md#host-pci-devices" %}}). The parent must have `SRIOV="pf"`, and its VFs must report the corresponding `PF_ADDRESS`.

Set only one PF selector per `PCI` entry. Neither `PF_IFNAME` nor `PF_ADDRESS` can be combined with `SHORT_ADDRESS`, `VENDOR`, `DEVICE`, or `CLASS` in the same entry.

The following examples assume an existing Virtual Network named `SRIOV-NET` and monitored PFs named `pf0` and `pf1`. Replace these names with those in your environment.

#### Attaching a VF from the CLI

To attach an available VF from a particular parent PF to an existing VM, use `onevm nic-attach` with `--pf <interface>`, where `<interface>` is the parent PF's interface name:

```shell
onevm nic-attach 2 --network SRIOV-NET --pf pf0
```

#### Affinity: VFs on the Same PF

To place two VFs on the same PF, use the same selector in both entries. The PF must have at least two free VFs:

```text
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",
  PF_IFNAME = "pf0"
]
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",
  PF_IFNAME = "pf0"
]
```

OpenNebula allocates two distinct VFs from `pf0` to the VM.

#### Anti-affinity: VFs on Different PFs

To spread the VFs across two PFs, select a different PF for each entry. Each PF must have at least one free VF:

```text
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",
  PF_IFNAME = "pf0"
]
PCI = [
  TYPE = "NIC",
  NETWORK = "SRIOV-NET",
  PF_IFNAME = "pf1"
]
```

You can instead use `PF_ADDRESS` in each entry, for example `0000:81:00:0` and `0000:81:00:1`. Use the PF's full monitored address rather than a VF's address or `SHORT_ADDRESS`.

These selectors apply on each candidate Host. Use consistent PF names or addresses across eligible Hosts, or restrict VM placement to Hosts with the required PFs. A Host cannot satisfy the request if it lacks a selected PF or enough free VFs.

Affinity and anti-affinity apply at PF level. If you need separate adapter cards or NUMA nodes, select PFs whose hardware topology provides that separation.

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
* `SHORT_ADDRESS`
* `TYPE`

For SR-IOV VFs, `PF_IFNAME` or `PF_ADDRESS` can select the parent PF, as described in [Selecting Virtual Functions by Physical Function](#selecting-virtual-functions-by-physical-function).

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
* Configure PCI monitoring to expose the required passthrough devices and any parent PFs needed for VF selection.
* Install the OpenNebula Context package in guest operating systems.
* Use NUMA-aware placement for latency-sensitive workloads.
* Prefer Switchdev mode when integrating with Open vSwitch.

## Next Steps

If you have not yet configured the Host for PCI passthrough, complete the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). For NVIDIA GPUs, continue with the [NVIDIA GPU Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}).
