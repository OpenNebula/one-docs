---
title: "NVIDIA Grace Platform Virtualization (AF)"
linkTitle: "NVIDIA Grace Platforms (AF)"
date: "2026-07-09"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "9"
toc_hide: true
---

## Overview

NVIDIA Grace Hopper and Grace Blackwell platforms implement a virtualization architecture that differs from conventional PCI passthrough systems. In addition to assigning GPUs to virtual machines, Grace platforms require a specific PCI topology based on dedicated PCI Root Complexes, SMMUv3 devices, IOMMUFD, and ACPI Generic Initiator NUMA nodes.

OpenNebula automates the creation of this virtual hardware topology during deployment. From the administrator's perspective, GPU assignment uses the standard `PCI` attribute while OpenNebula generates the libvirt configuration required by the Grace virtualization architecture.

### Requirements

Before configuring Grace platform virtualization, ensure that the Host has already been configured following the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

In addition, verify that the Host satisfies the following Grace-specific requirements:

* A Linux kernel supporting NVIDIA Grace virtualization.  
* NVIDIA QEMU and libvirt packages with Grace virtualization support.  
* QEMU configured with `CAP_IPC_LOCK`.  
* GPUs bound to the `nvgrace_gpu_vfio_pci` driver.

The installation and configuration of the virtualization software stack is outside the scope of this guide. Refer to the NVIDIA Grace Virtualization documentation for platform-specific installation instructions.

### Host Configuration

Only the Grace-specific configuration required after completing the generic Host configuration is described in this section.

### Configure QEMU Memory Locking

Grace platforms require QEMU to lock large GPU memory mappings.

Grant the `CAP_IPC_LOCK` capability to the QEMU binary:

```shell
sudo setcap cap_ipc_lock=ep /usr/bin/qemu-system-aarch64
```

Verify the capability:

```shell
getcap /usr/bin/qemu-system-aarch64
```

The capability must be restored whenever the QEMU binary is replaced during a package upgrade.

### Bind GPUs to the Grace VFIO Driver

Load the Grace VFIO driver:

```shell
sudo modprobe nvgrace-gpu-vfio-pci
```

Register the NVIDIA GB200 device ID with the driver:

```shell
echo "10de 2941" | sudo tee /sys/bus/pci/drivers/nvgrace_gpu_vfio_pci/new_id
```

Verify that the GPUs are bound to the `nvgrace_gpu_vfio_pci` driver:

```shell
lspci -nnkk | grep -i 3D -A2
```

Example output:

```default
0008:01:00.0 3D controller [0302]: NVIDIA Corporation Device [10de:2941] (rev a1)
        Subsystem: NVIDIA Corporation Device [10de:2046]
        Kernel driver in use: nvgrace_gpu_vfio_pci
--
0009:01:00.0 3D controller [0302]: NVIDIA Corporation Device [10de:2941] (rev a1)
        Subsystem: NVIDIA Corporation Device [10de:2046]
        Kernel driver in use: nvgrace_gpu_vfio_pci
--
0018:01:00.0 3D controller [0302]: NVIDIA Corporation Device [10de:2941] (rev a1)
        Subsystem: NVIDIA Corporation Device [10de:2046]
        Kernel driver in use: nvgrace_gpu_vfio_pci
--
0019:01:00.0 3D controller [0302]: NVIDIA Corporation Device [10de:2046]
        Kernel driver in use: nvgrace_gpu_vfio_pci
```
### Deploying a Virtual Machine

Grace platform virtual machines are deployed using the standard OpenNebula `PCI` attribute together with the CPU and NUMA configuration required by the workload.

The following example shows the relevant sections of a Virtual Machine Template configured with two Grace CPU NUMA nodes and four NVIDIA GB200 GPUs.

```
TOPOLOGY = [
    SOCKETS       = "2",
    CORES         = "72",
    THREADS       = "1",
    PIN_POLICY    = "THREAD",
    MEMORY_ACCESS = "shared",
    HUGEPAGE_SIZE = "512"
]

NUMA_NODE = [
    MEMORY     = "192000",
    TOTAL_CPUS = "72",
    DISTANCE   = "2-17:254"
]

NUMA_NODE = [
    MEMORY     = "192000",
    TOTAL_CPUS = "72",
    DISTANCE   = "2-17:254"
]

PCI=[
  ACPI_NODES="2-9",
  CLASS="0302",
  DEVICE="2941",
  IOMMU="YES",
  IOMMUFD="YES",
  ROOT="dedicated",
  VENDOR="10de" 
]

PCI=[
  ACPI_NODES="10-17",
  CLASS="0302", 
  ...
  

FEATURES=[
  ACPI="yes",
  APIC="yes",
  GIC="3",
  PCIHOLE64="4294967296",
  RAS="yes" 
]

IOMMU=[
  MODE="device",
  MODEL="smmuv3",
  OPTIONS="accel=on ats=on ril=off pasid=on oas=48" 
]
```

The `PCI` attributes request two NVIDIA GB200 GPUs using dedicated PCI Root Complexes and dedicated IOMMU contexts.

During deployment, OpenNebula automatically generates the Grace virtualization topology required by the guest, including:

* PCI Root Complexes and PCI Root Ports.  
* Virtual SMMUv3 devices.  
* IOMMUFD objects.  
* ACPI Generic Initiator NUMA nodes.  
* Guest NUMA topology.  
* NUMA distance matrices.

This topology follows the NVIDIA Grace virtualization architecture and preserves CPU and GPU NUMA locality.

{{< alert title="Note" type="primary" >}}
When using automatic GPU selection, OpenNebula computes the required `ACPI_NODES` assignment automatically. Explicit `ACPI_NODES` values are only required when selecting specific devices and defining a fixed virtual topology.{{< /alert >}} 

### Guest Configuration

Install the NVIDIA data center driver inside the guest operating system following the NVIDIA documentation.

After installation, the GPUs are exposed as native Grace devices and CUDA applications require no additional configuration.

A correctly configured guest exposes:

* The configured CPU NUMA nodes.  
* Eight ACPI Generic Initiator NUMA nodes for each assigned GPU.  
* Preserved NVLink connectivity.  
* GPU affinity matching the physical Grace topology.

The NUMA topology can be inspected using:

```shell
numactl -H
```

Example output:

```
available: 32 nodes (0-4,6-7,9-33)

node 0 cpus: 0-71
node 0 size: 191674 MB

node 1 cpus: 72-143
node 1 size: 191741 MB

...

node distances:
node   0   1   2   3   4 ...
0:    10  20 254 254 254 ...
1:    20  10 254 254 254 ...
2:   254 254  10  20  20 ...
...
```

This topology reflects the virtual hardware generated by OpenNebula. NUMA nodes 0 and 1 correspond to the Grace CPU memory domains, while the remaining nodes represent the ACPI Generic Initiator nodes associated with the assigned GPUs.

Verify that the GPUs are visible inside the guest:

```shell
nvidia-smi
```

Example output:

```default
+-----------------------------------------------------------------+
| NVIDIA-SMI 595.71.05      Driver Version: 595.71.05             |
|  CUDA Version: 13.2                                             |
+-----------------------------------------------------------------+
| GPU  Name     Persistence-M | Bus-Id Disp.A       | Vol ECC     | 
| Fan  Temp Perf Pwr:Usage/Cap|        Memory-Usage | GPU Compute | 
|                             |                     |       MIG M |
|=============================+=====================+=============|
|   0  NVIDIA GB200       Off |   00000000:A1:00.0 Off |        0 |
| N/A   38C    P0  163W/1200W |   0MiB / 189471MiB     | 0% Def   | 
|                             |                        | Disabled |
+-----------------------------+------------------------+----------+
|   1  NVIDIA GB200       Off |   00000000:A9:00.0 Off |        0 |
| N/A   38C    P0  164W/1200W |   0MiB / 189471MiB     | 0% Def   | 
|                             |                        | Disabled |
+-----------------------------+------------------------+----------+
|   2  NVIDIA GB200       Off |   00000000:B1:00.0 Off |        0 |
| N/A   38C    P0  206W/1200W |   0MiB / 189471MiB     | 0% Def   | 
|                             |                        | Disabled |
+-----------------------------+------------------------+----------+
|   3  NVIDIA GB200       Off |   00000000:B9:00.0 Off |        0 |
| N/A   38C    P0  221W/1200W |   0MiB / 189471MiB     | 0% Def   | 
|                             |                        | Disabled |
+-----------------------------+------------------------+----------+
```

Inspect the GPU topology:

```shell
nvidia-smi topo -m
```

Example output:

```default
        GPU0 GPU1 GPU2 GPU3 CPU Affinity NUMA Affinity GPU NUMA ID
GPU0     X   NV18 NV18 NV18     0-71          0            4
GPU1   NV18   X   NV18 NV18     0-71          0            3
GPU2   NV18 NV18   X   NV18    72-143         1            9
GPU3   NV18 NV18 NV18   X      72-143         1            2
```

This output confirms that:

* The GPUs are correctly detected inside the guest 
* NVLink connectivity is preserved
* GPU affinity matches the corresponding CPU NUMA node and the virtual topology generated by OpenNebula reproduces the physical Grace platform topology.
