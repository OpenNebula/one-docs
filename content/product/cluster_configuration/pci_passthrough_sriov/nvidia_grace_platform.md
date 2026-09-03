---
title: "NVIDIA Grace Platform Virtualization (AI)"
linkTitle: "NVIDIA Grace (AI)"
date: "2026-07-09"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "7"
---


{{< alert title="NVIDIA-Certified Hypervisor" color="primary" >}}
OpenNebula is an [**NVIDIA-Certified Hypervisor**](https://docs.nvidia.com/certification-programs/certified-hypervisors/latest/nvidia-certified-hypervisors.html) for the Grace Blackwell platform. This certification validates that OpenNebula correctly exposes NVIDIA GPUs and associated PCIe resources to Virtual Machines while preserving the topology, high-performance data paths, and near bare-metal performance required for accelerated AI and compute workloads. For users deploying NVIDIA Grace Blackwell infrastructure, this ensures that OpenNebula has been tested against NVIDIA-defined requirements for running GPU-accelerated workloads in virtualized environments.{{< /alert >}}

## Overview

NVIDIA Grace Hopper and Grace Blackwell platforms implement a virtualization architecture that differs from conventional PCI passthrough systems. In addition to assigning GPUs to virtual machines, Grace platforms require a specific PCI topology based on dedicated PCI Root Complexes, SMMUv3 devices, IOMMUFD, and ACPI Generic Initiator NUMA nodes.

OpenNebula automates the creation of this virtual hardware topology during deployment. From the administrator's perspective, GPU assignment uses the standard `PCI` attribute while OpenNebula generates the libvirt configuration required by the Grace virtualization architecture.

## Requirements

Before configuring Grace platform virtualization, ensure that the Host has already been configured following the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

In addition, verify that the Host satisfies the following Grace-specific requirements:

* A Linux kernel supporting NVIDIA Grace virtualization.
* NVIDIA QEMU and libvirt packages with Grace virtualization support.
* NVIDIA GB200 firmware version 1.3 or later.
* QEMU configured with `CAP_IPC_LOCK`.
* GPUs bound to the `nvgrace_gpu_vfio_pci` driver.

The installation and configuration of the virtualization software stack is outside the scope of this guide. Refer to the NVIDIA Grace Virtualization documentation for platform-specific installation instructions.

## Versions Used for Verification

The configuration described in this guide was verified with the following software stack:

| Component | Version |
|-----------|---------|
| Host operating system | Ubuntu 24.04 |
| Host kernel | `6.17.0-1014-nvidia-64k` |
| QEMU | `1:10.1.0+nvidia1egmfix-1` |
| libvirt | `11.9.0+nvidia4-1` |
| NVIDIA GB200 firmware | 1.3 or later |
| Guest NVIDIA driver | `595.71.05` |
| Guest CUDA | 13.2 |

Use the NVIDIA-provided QEMU and libvirt packages. The corresponding upstream versions do not necessarily include all the Grace virtualization extensions.

## Host Configuration

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

Before unloading the NVIDIA drivers, ensure that GPU memory has finished onlining after the Host reboot. The following command reports the number of system RAM ranges backed by GPU memory; wait until the value is non-zero and stable:

```shell
grep -i "System RAM (NVIDIA)" /proc/iomem | wc -l
```

Stop the services that may be using the GPUs:

```shell
sudo systemctl stop nvidia-persistenced
sudo systemctl stop nvidia-dcgm
sudo systemctl stop nvidia-fabricmanager
sudo systemctl stop nvidia-mig-manager
sudo systemctl stop nvidia-imex
sudo systemctl stop --all 'nvsm*'
```

Wait until GPU memory is completely offlined. The following command must report `0` before continuing:

```shell
grep -i "System RAM (NVIDIA)" /proc/iomem | wc -l
```

Unload the NVIDIA drivers:

```shell
sudo rmmod mods
sudo rmmod nouveau
sudo rmmod nvidia_vgpu_vfio nvidia_drm nvidia_modeset nvidia_uvm \
    nvidia_peermem nvidia_fs nvidia nvidiafb
```

An error indicating that a module is not loaded can be ignored. Verify that no NVIDIA module remains loaded:

```shell
lsmod | grep nvidia
```

The command must produce no output. If a module remains loaded, identify and stop the process using it before retrying:

```shell
sudo lsof /dev/nvidia*
```

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
```

### Configure Huge Pages for vCMDQ

vCMDQ requires the virtual machine to use physically contiguous Host memory. When EGM is not used, back the virtual machine with HugeTLB pages. NVIDIA Grace systems using a 64 KiB base page support 512 MiB huge pages; 1 GiB huge pages are not supported with this kernel page size.

The example in the next section assigns 512 GiB of memory and therefore requires at least 1024 free 512 MiB huge pages. Add the following parameters to the Host kernel command line:

```default
hugepages=1024 default_hugepagesz=512M
```

Regenerate the bootloader configuration, reboot the Host and verify the reserved pool:

```shell
grep -i '^HugePage' /proc/meminfo
```

The output must report a huge page size of `524288 kB` and at least 1024 free huge pages before deploying the virtual machine.

### Deploying a Virtual Machine

Grace platform virtual machines are deployed using the standard OpenNebula `PCI` attribute together with the CPU and NUMA configuration required by the workload.

{{< alert title="SMMUv3 Topology Limitation" type="warning" >}}
OpenNebula currently creates one guest SMMUv3 device for each passthrough GPU when `IOMMU/MODE="device"` is used. Consequently, this configuration is supported only when each selected GPU is connected to a different physical SMMU. Passing through multiple GPUs that share the same physical SMMU is not supported. Verify the Host PCI/SMMU topology before creating the template. When using automatic selection, ensure that every GPU exposed to OpenNebula satisfies this restriction; otherwise, select one GPU from each physical SMMU explicitly with `SHORT_ADDRESS`.{{< /alert >}}

Each GPU requires eight dedicated, zero-memory guest NUMA nodes. These nodes must not be shared with CPUs, memory or another GPU. Set `ACPI_NODES` explicitly in every `PCI` attribute; OpenNebula does not generate this assignment automatically.

The following complete Virtual Machine Template configures two Grace CPU NUMA nodes and two NVIDIA GB200 GPUs. It enables vCMDQ with `cmdqv=on` and backs the 512 GiB virtual machine with 512 MiB huge pages. The `ubuntu24.nvidia595` image denotes an Ubuntu 24.04 guest with the NVIDIA 595 driver already installed.

```default
NAME="grace-2gpu-vcmdq"

CONTEXT=[
  NETWORK="YES",
  SSH_PUBLIC_KEY="$USER[SSH_PUBLIC_KEY]",
  TOKEN="YES" ]

CPU="142"

CPU_MODEL=[
  MODEL="host-passthrough" ]

DISK=[
  IMAGE="ubuntu24.nvidia595" ]

FEATURES=[
  ACPI="yes",
  APIC="yes",
  GIC="3",
  PCIHOLE64="4294967296",
  RAS="yes" ]

GRAPHICS=[
  LISTEN="0.0.0.0",
  TYPE="VNC" ]

IOMMU=[
  MODE="device",
  MODEL="smmuv3",
  OPTIONS="accel=on ats=on ril=off pasid=on oas=48 cmdqv=on" ]

MEMORY="524288"

NUMA_NODE=[
  DISTANCE="2-17:254",
  MEMORY="262144",
  TOTAL_CPUS="71" ]

NUMA_NODE=[
  DISTANCE="2-17:254",
  MEMORY="262144",
  TOTAL_CPUS="71" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

NUMA_NODE=[
  DISTANCE="0-1:254",
  MEMORY="0",
  TOTAL_CPUS="0" ]

OS=[
  ARCH="aarch64",
  FIRMWARE="/usr/share/AAVMF/AAVMF_CODE.fd",
  FIRMWARE_SECURE="NO",
  MACHINE="virt-10.1" ]

PCI=[
  ACPI_NODES="2-9",
  CLASS="0302",
  DEVICE="2941",
  IOMMU="YES",
  IOMMUFD="YES",
  ROOT="dedicated",
  VENDOR="10de" ]

PCI=[
  ACPI_NODES="10-17",
  CLASS="0302",
  DEVICE="2941",
  IOMMU="YES",
  IOMMUFD="YES",
  ROOT="dedicated",
  VENDOR="10de" ]

SCHED_REQUIREMENTS="HYPERVISOR=kvm & ARCH=aarch64"

TOPOLOGY=[
  CORES="71",
  HUGEPAGE_SIZE="512",
  MEMORY_ACCESS="shared",
  PIN_POLICY="THREAD",
  SOCKETS="2",
  THREADS="1" ]

VCPU="142"
```

The `PCI` attributes request two NVIDIA GB200 GPUs using dedicated PCI buses and dedicated IOMMU contexts. `ACPI_NODES="2-9"` associates the first GPU with guest NUMA nodes 2 through 9, while `ACPI_NODES="10-17"` associates the second GPU with nodes 10 through 17.

During deployment, OpenNebula automatically generates the Grace virtualization topology required by the guest, including:

* PCI Root Complexes and PCI Root Ports.
* Virtual SMMUv3 devices.
* IOMMUFD objects.
* ACPI Generic Initiator objects for the explicitly configured `ACPI_NODES`.
* The explicitly configured guest NUMA topology and distance relationships.

This topology follows the NVIDIA Grace virtualization architecture and preserves CPU and GPU NUMA locality.

## Guest Configuration

Install the NVIDIA data center driver R580 or later inside the guest operating system following the NVIDIA documentation.

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

For the example template, NUMA nodes 0 and 1 are the Grace CPU memory domains, while nodes 2 through 17 are the ACPI Generic Initiator nodes associated with the two assigned GPUs. Verify that the distance from each CPU node to nodes 2 through 17 is 254.

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
```

Inspect the GPU topology:

```shell
nvidia-smi topo -m
```

The exact affinity and GPU NUMA IDs depend on the physical GPUs selected. Use the output to confirm that:

* The GPUs are correctly detected inside the guest.
* NVLink connectivity is preserved.
* GPU affinity matches the corresponding CPU NUMA node and the virtual topology generated by OpenNebula reproduces the physical Grace platform topology.
