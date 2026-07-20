---
title: "InfiniBand"
date: "2026-07-10"
categories: ["networking"]
pageintoc: "64"
tags: ["networking"]
weight: "7"
---

InfiniBand is a high-performance networking technology designed for environments where extremely low latency, high throughput, and efficient CPU utilization are critical. It is widely used in High Performance Computing (HPC), AI training and inference Clusters, and other data-intensive workloads that require significantly higher performance than conventional Ethernet networks. InfiniBand achieves this through technologies such as Remote Direct Memory Access (RDMA), allowing applications to exchange data directly between systems with minimal CPU involvement.

OpenNebula supports deployment on infrastructure equipped with InfiniBand fabrics, enabling virtualized and bare-metal workloads to take advantage of high-speed interconnects. Depending on the workload requirements, InfiniBand can be used in several different ways:

* As an IP network using IP over InfiniBand (IPoIB).
* By exposing InfiniBand adapters directly to Virtual Machines using PCI Passthrough or SR-IOV Virtual Functions (VFs).
* For storage and Cluster communication over high-speed fabrics.
* For applications that use RDMA directly.

## Typical Use Cases

InfiniBand is most commonly deployed for workloads such as:

* AI and machine learning training Clusters
* High Performance Computing (HPC)
* Scientific simulations
* High-performance distributed storage
* MPI-based parallel applications
* GPU Clusters requiring low-latency node-to-node communication

These environments benefit from InfiniBand's low latency, high bandwidth, and efficient RDMA transport.

## Deployment Models

OpenNebula does not implement a dedicated InfiniBand networking driver. Instead, InfiniBand is integrated using the standard Linux networking stack and OpenNebula's existing networking and PCI device management capabilities.

## IP over InfiniBand (IPoIB)

The simplest deployment method is IP over InfiniBand (IPoIB), where the InfiniBand fabric behaves as a conventional IP network.

Once the Host operating system has configured the InfiniBand interfaces, they appear as standard Linux network interfaces and can be used throughout OpenNebula just like Ethernet interfaces.

Typical uses include:

* Front-end and back-end Cluster communication
* Storage traffic
* Virtual Network bridges
* VXLAN or VLAN transport over the InfiniBand fabric (where supported by the underlying infrastructure)

From OpenNebula's perspective, no special configuration is required beyond using the appropriate bridge or physical interface when defining Virtual Networks.

## PCI Passthrough

Applications that require native InfiniBand capabilities or RDMA typically require direct access to the InfiniBand Host Channel Adapter (HCA).

OpenNebula supports assigning InfiniBand adapters directly to Virtual Machines using PCI Passthrough. This provides the guest operating system with direct hardware access, allowing it to install the appropriate InfiniBand drivers and use the adapter as if running on bare metal.

Configuration follows the standard PCI Passthrough workflow described in the PCI Passthrough documentation.

## SR-IOV Virtual Functions

Many modern InfiniBand adapters support Single Root I/O Virtualization (SR-IOV), allowing multiple Virtual Functions (VFs) to be created from a single physical adapter.

OpenNebula can schedule and assign these Virtual Functions directly to Virtual Machines, providing:

* Near-native networking performance
* RDMA support
* Lower overhead than emulated virtual NICs
* Efficient sharing of high-performance network adapters

When using SR-IOV network devices, OpenNebula can configure attributes such as:

* MAC address
* VLAN ID
* Spoof checking
* Trust mode

depending on whether the adapter operates in Legacy or Switchdev mode.

## Host Requirements

Before deploying workloads using InfiniBand, ensure that each Host is correctly configured by the operating system.

Typical requirements include:

* Supported InfiniBand Host Channel Adapters (HCAs)
* Vendor drivers and firmware
* RDMA software stack (for example, RDMA Core or vendor-provided drivers)
* A functioning InfiniBand fabric
* An operational Subnet Manager (such as OpenSM), which is required for InfiniBand fabrics to function correctly
* Appropriate kernel modules and IPoIB configuration if using IP networking over InfiniBand

OpenNebula assumes that the InfiniBand infrastructure has already been configured and validated by the operating system.

## Guest Requirements

If Virtual Machines require native InfiniBand functionality, the guest operating system must include:

* InfiniBand drivers
* RDMA libraries (when required)
* Appropriate user-space software for the intended workload

Guests using PCI Passthrough or SR-IOV interact directly with the assigned hardware and are responsible for managing the device.

### Considerations

When planning an InfiniBand deployment, consider the following:

PCI Passthrough and SR-IOV provide the highest performance but may reduce Virtual Machine mobility, including live migration support, depending on the hardware and deployment configuration.

IPoIB offers excellent compatibility with existing networking tools but does not expose all RDMA capabilities to applications.
Applications must be specifically designed or configured to use RDMA in order to benefit from InfiniBand's lowest latency communication.

Network configuration, firmware management, and Subnet Manager deployment remain the responsibility of the underlying operating system and network infrastructure.