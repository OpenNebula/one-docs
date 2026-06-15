---
title: "NVIDIA Spectrum-X Integration (AE)"
linkTitle: "NVIDIA Spectrum-X (AE)"
date: "2025-12-17"
categories: ["networking"]
pageintoc: "64"
tags: ["networking", "hpc", "ai", "nvidia", "spectrum-x", "evpn"]
weight: "8"
---

<a id="spectrumx"></a>

This guide provides a high-level overview of the OpenNebula integration with the NVIDIA Spectrum-X&trade; Ethernet networking platform. This integration allows OpenNebula to act as a single pane of glass for managing an entire AI factory, from compute and storage to the high-performance network fabric.

The integration works by mapping OpenNebula's logical resource constructs (like Users and Virtual Networks) directly to the Spectrum-X fabric's tenant segments, which are based on a routed L3EVPN architecture to deliver isolated, high-bandwidth East-West (E/W) traffic for demanding AI and HPC workloads.

## The Spectrum-X Platform

NVIDIA Spectrum-X is the first Ethernet fabric built from the ground up to accelerate AI workloads. It delivers advanced performance, scalability, and network intelligence, ensuring consistent, predictable results in a multi-tenant AI cloud.

The platform is built on two key components:
*   **NVIDIA Spectrum-4 Switches**: High-bandwidth, low-latency switches that provide RoCE-optimized routing and advanced congestion control.
*   **NVIDIA BlueField-3 SuperNICs**: A new class of network adapter that accelerates and secures the network, moving networking and security tasks from the CPU to the DPU.

The fabric uses a routed L3EVPN architecture to create isolated tenant environments. Each tenant is assigned a separate Virtual Routing and Forwarding (VRF) instance on the leaf switches, ensuring traffic from one tenant is logically separated from another.

## OpenNebula Integration Concepts

The integration between OpenNebula and Spectrum-X is achieved by creating a clear mapping between OpenNebula's resource management constructs and the physical network's tenant architecture.

### Resource Mapping

*   **Tenant Mapping**: An AI Factory tenant is directly mapped to a **User** in OpenNebula. This user is then granted access to a specific set of isolated resources (N/S vNet, BlueField-3 PCI Device and GPU PCI Device).
<br>
<br>
*   **Network Mapping**: The integration distinguishes between two traffic patterns:
    *   **North-South (N/S) Network**: This is the standard management and external access network for a VM. It is implemented in OpenNebula as a regular **Virtual Network (vNet)**.
    *   **East-West (E/W) Network**: This is the high-performance Spectrum-X fabric used for GPU-to-GPU communication.The link between these two networks is established by storing the tenant E/W **VXLAN Network Identifier (VNI)** as a custom attribute, `SPX_VNI`, within the N/S Virtual Network template in OpenNebula. A tenant can attach a VM to its own E/W segment by attaching a specific BlueField-3 PCI device to the VM.
<br>
<br>
*   **Hardware Access**:
    *   NVIDIA GPUs and BlueField-3 SuperNICs are represented in OpenNebula as **PCI Devices**.
    *   Access is granted to tenants by assigning ownership or group access to these PCI devices.
    *   To enable dynamic E/W fabric configuration, the PCI device template for each SuperNIC must store critical networking information as custom attributes:
        *   `SPX_NIC_IP`: The static IP address of the SuperNIC's interface. This IP address must remain static due to the routed L3EVPN nature of the E/W fabric.
        *   `SPX_LEAF_IP`: The IP address of the leaf switch the SuperNIC is connected to.
        *   `SPX_LEAF_PORT`: The physical port name on the leaf switch where the SuperNIC is connected.

### Dynamic Fabric Configuration

OpenNebula orchestrates the Spectrum-X fabric dynamically using network hooks. When a user deploys a VM, these hooks execute scripts on the hypervisor that configure the Spectrum-X leaf switches.

The high-level workflow is as follows:
1.  A tenant instantiates a VM Template containing both a standard N/S network interface and one or more E/W PCI passthrough devices (the BlueField-3 SuperNICs).
2.  The VM's context contains all the necessary attributes: `SPX_VNI` (from the N/S vNet) and the `SPX_*` attributes (from the PCI devices).
3.  Upon deployment, an OpenNebula network hook runs on the target hypervisor. This hook establishes an SSH connection to the corresponding leaf switches.
4.  The hook uses `NVUE` commands on the switch to build the tenant E/W datapath, allowing fully tenant-isolated GPU-to-GPU connectivity.

## Current Status and Considerations

{{< alert title="Important" color="info" >}}
This is a high-level overview of the integration. Customers interested in a detailed technical discussion and production deployment should contact OpenNebula Systems.
{{< /alert >}}

*   **Availability**: This integration is part of the OpenNebula Enterprise Edition and is available as a reference implementation.
*   **Validation Environment**: The integration has been fully developed and validated in the **NVIDIA Air** cloud simulation platform, which provides a faithful, large-scale simulation of a Spectrum-X hardware environment.