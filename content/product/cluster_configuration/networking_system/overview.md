---
title: "Overview"
date: "2025-02-17"
description:
categories:
pageintoc: "59"
tags:
weight: "1"
---

<a id="nm"></a>

<!--# Overview -->

When a new Virtual Machine is launched, OpenNebula will connect its virtual network interfaces (defined by `NIC` attributes) to hypervisor network link devices as defined in the corresponding [Virtual Network]({{% relref "manage_vnets#manage-vnets" %}}). This will allow the VM to have access to public and private networks.

OpenNebula supports the following networking modes:

* [Bridged]({{% relref "bridged#bridged" %}}): The VM NIC is added to a Linux bridge on the Host. This mode can be configured to use Security Groups and network isolation.
* [802.1Q VLAN]({{% relref "vlan#hm-vlan" %}}): The VM NIC is added to a Linux bridge on the Host and the Virtual Network is configured to handle 802.1Q VLAN isolation.
* [VXLAN]({{% relref "vxlan#vxlan" %}}): The VM NIC is added to a Linux bridge on the Host and the Virtual Network implements isolation using the VXLAN encapsulation.
* [Open vSwitch]({{% relref "openvswitch#openvswitch" %}}): The VM NIC is added to a Open vSwitch bridge on the Host and the Virtual Network optionally handles 802.1Q VLAN isolation.
* [Open vSwitch on VXLAN]({{% relref "openvswitch#openvswitch-vxlan" %}}): The VM NIC is added to a Open vSwitch bridge on the Host and the Virtual Network is configured to provide both isolation with VXLAN encapsulation and optionally 802.1Q VLAN.

The attribute `VN_MAD` of a Virtual Network determines which of the above networking modes is used.

{{< alert title="Note" type="info" >}}
Security Groups are not supported in the Open vSwitch modes.{{< /alert >}} 

## Accelerated Networking

OpenNebula supports accelerated networking and interconnect technologies for AI and HPC environments. These technologies complement the standard Virtual Network modes by providing high-bandwidth, low-latency communication, direct device access, hardware offload, and optimized communication between GPUs and compute nodes.

* [InfiniBand]({{% relref "product/cluster_configuration/networking_system/infiniband/" %}}): Provides a high-throughput, low-latency network fabric for distributed AI and HPC workloads. InfiniBand devices can be exposed to Virtual Machines through mechanisms such as PCI passthrough or SR-IOV.

* [NVIDIA Spectrum-X]({{% relref "product/cluster_configuration/networking_system/spectrumx/" %}}): Provides an accelerated Ethernet fabric optimized for AI workloads, combining NVIDIA Spectrum switches and high-performance network adapters to improve communication between compute nodes.

* [NVIDIA BlueField DPU]({{% relref "product/cluster_configuration/networking_system/nvidia_bluefield_dpu/" %}}): Offloads networking, security, encryption, and infrastructure services from the Host CPU. BlueField devices can be integrated into the infrastructure to provide accelerated and isolated data paths for tenant workloads.

* [NVIDIA Fabric Manager]({{% relref "product/cluster_configuration/pci_passthrough_sriov/one_fabricmanager/" %}}): Manages and monitors the NVSwitch fabric used for high-speed communication between multiple NVIDIA GPUs within a Host. It initializes the fabric and coordinates GPU connectivity for supported multi-GPU systems.

## How Should I Read This Chapter

Before reading this Chapter make sure you are familiar with the [Open Cloud Storage]({{% relref "../storage_system/overview#storage" %}}). It’s necessary to be aware of requirements for your selected storage solution in order to be able to design the network architecture of your hypervisor nodes.

In each specific section, you will find instructions to configure nodes and the procedures to deploy the networking mode of your interest.

Additionally, if you are interested in optional integration with the IP Address Manager (IPAM), the external mechanism that allocates and assigns the IP addresses for the Virtual Machines, you can consult [IPAM driver]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-ipam" %}}) in the [Integration References]({{% relref "integration_references" %}}).

## Hypervisor Compatibility

This Chapter applies to KVM and LXC.
