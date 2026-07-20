---
title: "Overview"
date: "2026-06-30"
description:
categories:
pageintoc: "52"
tags:
weight: "1"
---


Overview
PCI passthrough allows virtual machines to access physical PCI devices directly, bypassing device emulation. This approach enables workloads to use the full capabilities of specialized hardware such as GPUs, high-performance network adapters, storage controllers, and other accelerators while maintaining the flexibility of virtualization.

This guide introduces the PCI passthrough architecture in OpenNebula and provides an overview of the supported device types. Detailed configuration procedures are covered in the following guides.

## PCI Passthrough Architecture

A PCI passthrough deployment relies on coordinated hardware and software support. Modern processors provide an Input-Output Memory Management Unit (IOMMU), such as Intel VT-d, AMD-Vi, or Arm SMMUv3, to safely map device access to guest memory. The Linux kernel exposes this capability through the VFIO framework, allowing libvirt and QEMU to securely assign physical PCI devices directly to virtual machines. 

OpenNebula manages this process by discovering available PCI devices on each Host, exposing them as Host resources that can be scheduled for virtual machines, selecting suitable Hosts during scheduling, and generating the appropriate virtualization configuration as part of its integrated scheduling, monitoring, and virtual machine management infrastructure.

OpenNebula abstracts this complexity and allows administrators to manage PCI devices using standard Host and virtual machine templates.

## Supported Device Types

OpenNebula supports assigning a wide variety of PCI devices to virtual machines. PCI passthrough is a generic mechanism that can be applied to many types of hardware. However, two categories are of particular relevance and OpenNebula provides enhanced integration and configuration capabilities:

* **Graphics Processing Units (GPUs)**: GPU passthrough enables virtual machines to use physical GPUs for compute-intensive workloads such as Artificial Intelligence (AI), High Performance Computing (HPC), visualization, and graphics acceleration. OpenNebula supports NVIDIA GPUs through both full PCI passthrough and mediated devices (vGPU), depending on the GPU model and virtualization technology.
* **Network Interfaces**: PCI passthrough can be used with high-performance network adapters to provide direct access to physical networking hardware from virtual machines. OpenNebula supports assigning both Physical Functions (PFs) and Single Root I/O Virtualization (SR-IOV) Virtual Functions (VFs), while maintaining centralized management through OpenNebula.

## PCI Device Lifecycle in OpenNebula

OpenNebula manages PCI devices throughout their lifecycle, allowing administrators to manage PCI devices using the same workflow as other OpenNebula resources:

1. **Host Discovery**: The monitoring subsystem automatically discovers PCI devices available on each virtualization Host and collects information such as vendor, device identifiers, class, NUMA locality, and virtualization capabilities.
2. **Device Scheduling**: PCI devices become schedulable Host resources. During deployment, the scheduler selects a Host satisfying both the virtual machine requirements and the requested PCI devices.
3. **Virtual Machine Deployment**: When a virtual machine is deployed, OpenNebula generates the corresponding libvirt domain configuration, attaches the requested PCI devices, configures the required virtual PCI topology, and enables additional virtualization features when required by the hardware platform.
        * The PCI device can also be configured in the VM post VM deployment. Network interfaces can be hot-plugged.
4. **Device Release**: When the virtual machine is terminated, the PCI devices are automatically released and become available for future deployments.

## Supported Virtualization Features

OpenNebula supports several PCI virtualization technologies, including:

* Direct PCI passthrough using VFIO
* SR-IOV Virtual Functions (VFs) in switchdev and legacy mode
* NVIDIA mediated devices (vGPU) and MIG

Depending on the hardware platform, OpenNebula also supports additional virtualization capabilities, including:

* IOMMUFD-based device assignment
* NUMA-aware device placement
* Huge Page-backed memory
* Advanced PCI topology generation
* Platform-specific features such as Arm SMMUv3, ACPI Generic Initiator nodes, and dedicated IOMMU devices for NVIDIA Grace platforms

Not all features are applicable to every device type or hardware platform. Refer to the device-specific guides for detailed compatibility information.

## Documentation Structure

The PCI passthrough documentation is organized into the following guides:

| **Guide** | **Description** |
|-------|-------------|
| [Host Configuration]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}) | Configure virtualization Hosts for PCI passthrough, including IOMMU, VFIO, Huge Pages, SR-IOV, and other common Host requirements. |
| [Network Interfaces]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces/" %}}) | Configure PCI passthrough and SR-IOV for network adapters. |
| [Device Passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/pci_passthrough/" %}}) | Configure the passthrough configuration of a given device. |
| [NVIDIA GPUs]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) | Configure NVIDIA GPUs for passthrough and vGPU deployments, including platform-specific features such as Grace and Grace Blackwell. | 
| [AMD GPUs]({{% relref "product/cluster_configuration/pci_passthrough_sriov/amd_gpu_passthrough/" %}}) | Configure AMD GPUs for passthrough. | 
| [Axelera GPUs]({{% relref "product/cluster_configuration/pci_passthrough_sriov/axelera_gpu_passthrough/" %}}) | Configure Axelera GPUs for passthrough. | 
| [NVIDIA Fabric Manager]({{% relref "product/cluster_configuration/pci_passthrough_sriov/one_fabricmanager/" %}}) | Configure NVIDIA Fabric Manager for supported GPU platforms. |

## Next Steps

Before assigning PCI devices to Virtual Machines, configure the virtualization Hosts by following the [Host Configuration guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

Additional configuration required for specific device types is described in the corresponding device-specific guides.
