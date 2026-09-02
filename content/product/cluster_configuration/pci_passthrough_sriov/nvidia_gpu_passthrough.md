---
title: "NVIDIA GPU Passthrough"
linkTitle: "NVIDIA GPUs"
date: "2025-10-16"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "5"
---

## Overview

This guide describes how to deploy NVIDIA GPUs using PCI passthrough technologies in OpenNebula. OpenNebula supports multiple NVIDIA GPU deployment models, including conventional PCI passthrough, [NVIDIA vGPU]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_mig_passthrough/" %}}), [MIG-backed vGPU]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_mig_passthrough/" %}}), and [NVIDIA Grace platform virtualization]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_grace_platform/" %}}). While these deployment models share the same scheduling and deployment workflow, each requires a different Host configuration.

The generic PCI passthrough configuration, including IOMMU, VFIO, Huge Pages, PCI monitoring, and device discovery, is described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). This guide focuses exclusively on the NVIDIA-specific configuration and deployment procedures.

## Deployment Models

NVIDIA GPUs can be deployed in OpenNebula using one of the following deployment models.

| Deployment Model | Typical Platforms | VFIO Driver | Additional Configuration |
| ----- | ----- | ----- | ----- |
| Conventional PCI Passthrough | H100 PCIe, H100 SXM, H200, L40, L40S, RTX, A100 | `vfio-pci` | Standard PCI passthrough |
| [NVIDIA vGPU / MIG-backed vGPU]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_mig_passthrough/" %}}) | A100, H100, H200, B200 | NVIDIA vGPU stack | NVIDIA vGPU or MIG-backed vGPU configuration |
| [Grace Platform Virtualization]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_grace_platform/" %}}) | GH200, GB200 | `nvgrace_gpu_vfio_pci` | Grace-specific virtualization configuration |

For **conventional PCI passthrough**, the NVIDIA driver is **not required** on the Host. The GPU is owned exclusively by the guest operating system, where the NVIDIA driver is installed after deployment.

For **NVIDIA vGPU** and **MIG-backed vGPU**, the NVIDIA driver is required on the Host because the Host manages GPU partitioning and virtual GPU creation before assigning GPU resources to Virtual Machines.

---

## Conventional PCI Passthrough

## Overview

Conventional PCI passthrough assigns one or more physical NVIDIA GPUs directly to a Virtual Machine, providing the guest operating system with exclusive access to the assigned devices. In this deployment model, the Host does not use the GPUs, which are instead bound to the `vfio-pci` driver and managed entirely by the guest operating system.

This deployment model is recommended for workloads requiring direct access to the GPU, such as AI training and inference, high-performance computing (HPC), scientific computing, visualization, and CUDA development. It is supported by NVIDIA PCIe and SXM GPUs, including NVIDIA H100, H200, L40, L40S, RTX, and A100 GPUs when Multi-Instance GPU (MIG) is not enabled.

## Requirements

Before deploying NVIDIA GPUs using conventional PCI passthrough, complete the generic PCI passthrough configuration described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

Verify that the Host satisfies the following requirements:

* Hardware-assisted virtualization and the IOMMU are enabled.  
* The GPU is bound to the `vfio-pci` driver.  
* PCI monitoring is configured to discover NVIDIA GPUs.  
* The GPUs have been discovered by OpenNebula.

Verify that the GPU is managed by the `vfio-pci` driver:

```shell
lspci -nnk -d 10de:
```

Example output:

```
81:00.0 3D controller: NVIDIA Corporation H100 PCIe
       Kernel driver in use: vfio-pci

81:00.1 Audio device: NVIDIA Corporation Device xxxx
       Kernel driver in use: vfio-pci
```

Verify that the GPUs have been discovered by OpenNebula:

```shell
onehost show <host>
```

The GPUs should appear in the **PCI Devices** section and be available for scheduling.

{{< alert title="Note" type="primary" >}}
Unlike NVIDIA vGPU or MIG-backed vGPU deployments, the NVIDIA driver is not required on the Host for conventional PCI passthrough. The GPU is owned exclusively by the guest operating system, where the NVIDIA driver is installed after deployment.{{< /alert >}}

---

## Host Configuration

This section describes the NVIDIA-specific configuration required after completing the generic PCI passthrough configuration. If the NVIDIA driver is installed on the Host, prevent it from binding to GPUs intended for passthrough by blacklisting the NVIDIA kernel modules.

Create the following configuration file:

```default
/etc/modprobe.d/blacklist-nvidia.conf
```

Example contents:

```default
blacklist nouveau
blacklist nvidia
blacklist nvidia_drm
blacklist nvidia_modeset
blacklist nvidia_uvm
```

Regenerate the initramfs using the appropriate command for your Linux distribution and reboot the Host.

{{< alert title="Note" type="primary" >}}
This step is only required if the NVIDIA driver is installed on the Host. Hosts dedicated to GPU PCI passthrough typically do not require the NVIDIA driver.{{< /alert >}}

### Verify the GPU Driver

After completing the generic PCI passthrough configuration, verify that all GPU PCI functions are managed by the `vfio-pci` driver.

```shell
lspci -nnk -d 10de:
```

Example output:

```
81:00.0 3D controller: NVIDIA Corporation H100 PCIe
       Kernel driver in use: vfio-pci

81:00.1 Audio device: NVIDIA Corporation Device xxxx
       Kernel driver in use: vfio-pci
```

If any GPU function is still managed by the NVIDIA or Nouveau driver, review the VFIO configuration described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

{{< alert title="Note" type="primary" >}}
NVIDIA GPUs may expose multiple PCI functions, such as audio or USB controllers. All functions belonging to the GPU should be assigned together to the same Virtual Machine.{{< /alert >}}

### Verify GPU Discovery

After the next monitoring cycle, verify that OpenNebula has discovered the GPUs.

```shell
onehost show <host>
```

Example output:

```default
PCI DEVICES

 VM ADDR TYPE           NAME                                              
 e1:00.0 10de:2321:0302 NVIDIA Corporation GH100 [H100L 94GB]
```

The GPUs should appear in the **PCI Devices** section and be available for scheduling.

Alternatively, the detected PCI devices can be inspected from the **PCI Devices** tab in Sunstone.

## Deploying a Virtual Machine

After the Host has been configured and the GPUs have been discovered by OpenNebula, they can be assigned to Virtual Machines using the standard `PCI` attribute in the Virtual Machine Template.

OpenNebula supports both automatic and explicit GPU selection. Automatic selection is recommended because it allows the scheduler to place workloads on any compatible Host, improving workload portability and resource utilization.

### Automatic GPU Selection

The following example requests any available NVIDIA GPU:

```
PCI = [
    CLASS  = "0302",
    VENDOR = "10de"
]
```

During deployment, OpenNebula selects a compatible GPU that matches the requested attributes and assigns it to the Virtual Machine.

Additional `PCI` attributes, such as `DEVICE` or `SHORT_ADDRESS`, can be used to further restrict device selection when required.

### Selecting a Specific GPU

For topology-sensitive deployments, benchmarking, or debugging, a specific GPU can be requested using its PCI address.

For example:

```
PCI = [
    SHORT_ADDRESS = "81:00.0"
]
```

Explicit device selection should be reserved for specialized deployments. In most environments, automatic GPU selection provides greater flexibility and simplifies workload scheduling.

### Assigning Multiple GPUs

Multiple GPUs can be assigned to the same Virtual Machine by including multiple `PCI` sections.

The following example requests two NVIDIA GPUs:

```
PCI = [
    CLASS  = "0302",
    VENDOR = "10de"
]

PCI = [
    CLASS  = "0302",
    VENDOR = "10de"
]
```

Each `PCI` section requests one compatible GPU. During deployment, OpenNebula assigns the requested number of devices to the Virtual Machine.

---

## Example H100 Virtual Machine Template

The following example shows a Virtual Machine Template for an NVIDIA H100 SXM system with eight GPUs assigned through PCI passthrough.

```default
CONTEXT = [
    NETWORK        = "YES",
    SSH_PUBLIC_KEY = "$USER[SSH_PUBLIC_KEY]"
]

CPU    = "208"
VCPU   = "208"
MEMORY = "716800"

CPU_MODEL = [
    MODEL = "host-passthrough"
]

TOPOLOGY = [
    CORES      = "52",
    SOCKETS    = "2",
    THREADS    = "2",
    PIN_POLICY = "THREAD"
]

OS = [
    ARCH            = "x86_64",
    FIRMWARE        = "/usr/share/OVMF/OVMF_CODE_4M.fd",
    FIRMWARE_SECURE = "NO",
    MACHINE         = "pc-q35-jammy"
]

DISK = [
    IMAGE = "ubuntu-24.04-gpu",
    SIZE  = "1572864"
]

NIC = [
    NETWORK = "admin_net"
]

GRAPHICS = [
    LISTEN = "0.0.0.0",
    TYPE   = "vnc"
]

FEATURES = [
    PCIHOLE64 = "2147483648"
]

PCI = [ SHORT_ADDRESS = "1b:00.0" ]
PCI = [ SHORT_ADDRESS = "43:00.0" ]
PCI = [ SHORT_ADDRESS = "52:00.0" ]
PCI = [ SHORT_ADDRESS = "df:00.0" ]
```

The `PCI` entries assign the eight H100 GPUs to the Virtual Machine.


## Guest Configuration

After the Virtual Machine has been deployed, verify that the GPUs are visible inside the guest:

```shell
lspci | grep -i nvidia
```

Example output:

```default
23:00.0 3D controller: NVIDIA Corporation GH100 [H100 SXM5 80GB]
24:00.0 3D controller: NVIDIA Corporation GH100 [H100 SXM5 80GB]
...
46:00.0 3D controller: NVIDIA Corporation GH100 [H100 SXM5 80GB]
```

Install the appropriate NVIDIA driver inside the guest operating system. The selected driver version must support the assigned GPU model and be compatible with the required CUDA software stack.

After installing the driver, verify that all assigned GPUs are detected:

```shell
nvidia-smi
```

Use the output provided in the NVIDIA qualification guide for your platform to verify that all assigned GPUs are present and that no driver or hardware errors are reported. Avoid using placeholder outputs, as driver versions and formatting vary across NVIDIA software releases.

