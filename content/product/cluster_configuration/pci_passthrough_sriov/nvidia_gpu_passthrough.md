---
title: "NVIDIA GPU Passthrough"
linkTitle: "NVIDIA GPU (vGPU, MIG, Passthrough)"
date: "2025-10-16"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "5"
---

## Overview

This guide describes how to deploy NVIDIA GPUs using PCI passthrough technologies in OpenNebula. OpenNebula supports multiple NVIDIA GPU deployment models, including conventional PCI passthrough, NVIDIA vGPU, MIG-backed vGPU, and NVIDIA Grace platform virtualization. While these deployment models share the same scheduling and deployment workflow, each requires a different Host configuration.

The generic PCI passthrough configuration, including IOMMU, VFIO, Huge Pages, PCI monitoring, and device discovery, is described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). This guide focuses exclusively on the NVIDIA-specific configuration and deployment procedures for each supported deployment model.

## Deployment Models

NVIDIA GPUs can be deployed in OpenNebula using one of the following deployment models.

| Deployment Model | Typical Platforms | VFIO Driver | Additional Configuration |
| ----- | ----- | ----- | ----- |
| Conventional PCI Passthrough | H100 PCIe, H100 SXM, H200, L40, L40S, RTX, A100 | `vfio-pci` | Standard PCI passthrough |
| NVIDIA vGPU / MIG-backed vGPU | A100, H100, H200, B200 | NVIDIA vGPU stack | NVIDIA vGPU or MIG-backed vGPU configuration |
| Grace Platform Virtualization | GH200, GB200 | `nvgrace_gpu_vfio_pci` | Grace-specific virtualization configuration |

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

## NVIDIA vGPU and MIG-backed vGPU

### Overview

NVIDIA vGPU enables multiple Virtual Machines to share the resources of a physical GPU by exposing one or more virtual GPU (vGPU) profiles that can be independently assigned to guest operating systems.

Depending on the GPU generation, vGPU profiles can be created using one of two deployment models:

* **NVIDIA vGPU**, where virtual GPU profiles are created directly by the NVIDIA AI Enterprise software stack.  
* **MIG-backed vGPU**, where the GPU is first partitioned using NVIDIA Multi-Instance GPU (MIG), and one or more vGPU profiles are created from the resulting GPU Instances.

Regardless of how the profiles are created, OpenNebula automatically discovers the available vGPU profiles during Host monitoring and schedules them as GPU resources that can be assigned to Virtual Machines.

Before deploying NVIDIA vGPU devices, complete the generic PCI passthrough configuration described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).

---

## Requirements

Before continuing, verify that the Host satisfies the following requirements:

* A supported NVIDIA GPU is installed.  
* The NVIDIA Host driver is installed and operational.  
* PCI monitoring is configured.  
* The GPU has been discovered by OpenNebula.

Verify that the NVIDIA driver is correctly installed:

```shell
nvidia-smi
```

Verify that the GPU has been discovered by OpenNebula:

```shell
onehost show <host>
```

The GPU should appear in the **PCI Devices** section.

### Host Configuration

Depending on the GPU model, configure either **NVIDIA vGPU** or **MIG-backed vGPU**.

#### Configure NVIDIA vGPU

Conventional NVIDIA vGPU is supported on GPUs that expose vGPU profiles directly through the NVIDIA AI Enterprise software stack.

Install the NVIDIA AI Enterprise software stack and the NVIDIA vGPU Manager according to the NVIDIA documentation.

After installation, verify that the NVIDIA driver is operational:

```shell
nvidia-smi
```

Display the supported vGPU profiles:

```shell
nvidia-smi vgpu -s -v
```

The command lists all vGPU profiles supported by the GPU.

After the next monitoring cycle, OpenNebula automatically discovers the available vGPU profiles.

## Configure MIG-backed vGPU

Hopper and newer GPUs support creating vGPU profiles from GPU partitions created using NVIDIA Multi-Instance GPU (MIG).

### Enable MIG Mode

Display the current MIG configuration:

```shell
nvidia-smi -i 0 -q | grep MIG -A2
```

Enable MIG mode:

```shell
sudo nvidia-smi -i 0 -mig 1
```

Verify that MIG mode has been enabled:

```shell
nvidia-smi -i 0 -q | grep MIG -A2
```

Example output:

```default
MIG Mode
    Current                  : Enabled
    Pending                  : Enabled
```

Some GPU models require a reboot before MIG mode becomes active.

### Display Available GPU Instance Profiles

Display the supported GPU Instance profiles:

```shell
nvidia-smi mig -lgip
```

Example output:

```shell
+-----------------------------------------------------------------------------+
| GPU instance profiles:                                                      |
| GPU   Name             ID    Instances   Memory     SM    DEC   ENC   OFA   |
|       Profile                Free/Total  GiB        CE                      |
|=============================================================================|
|   0  MIG 1g.10gb        19     7/7        9.62       16     0     0     0   |
|   0  MIG 2g.20gb        14     3/3       19.50       32     1     0     0   |
|   0  MIG 3g.40gb         9     2/2       39.25       60     2     0     0   |
+-----------------------------------------------------------------------------+
```

Display the supported GPU Instance placements:

```shell
nvidia-smi mig -lgipp
```

### Create GPU and Compute Instances

Create the desired GPU Instances.

For example, the following command creates four **1g.10gb** GPU Instances together with their default Compute Instances:

```shell
sudo nvidia-smi mig -cgi 19,19,19,19 -C
```

Verify the resulting MIG devices:

```shell
nvidia-smi -L
```

Example output:

```
GPU 0: NVIDIA H100 PCIe

  MIG 1g.10gb Device 0: (UUID: MIG-xxxxxxxx)
  MIG 1g.10gb Device 1: (UUID: MIG-xxxxxxxx)
  MIG 1g.10gb Device 2: (UUID: MIG-xxxxxxxx)
  MIG 1g.10gb Device 3: (UUID: MIG-xxxxxxxx)
```

### Configure vGPU Profiles

After creating the GPU and Compute Instances, configure the required NVIDIA vGPU profiles according to the NVIDIA AI Enterprise documentation.

Verify the available profiles:

```shell
nvidia-smi vgpu -s -v
```

### Refresh OpenNebula Monitoring

Once the GPU configuration has been completed, refresh Host monitoring:

```shell
onehost forceupdate <hostid>
```

Verify that the configured vGPU profiles have been discovered:

```shell
onehost show <host>
```

The configured profiles should appear in the **PCI Devices** section and be available for scheduling.

---

### Deploying a Virtual Machine

Virtual machines request NVIDIA vGPU resources by selecting one of the vGPU profiles discovered during Host monitoring.

The available profiles can be inspected from the **PCI Devices** tab in Sunstone or using:

```shell
onehost show <host>
```

Each discovered profile reports the profile name together with the number of available instances.

---

**Example Virtual Machine Template**

Virtual machines request NVIDIA vGPU resources using the `PCI` attribute. The `PROFILE` attribute must match one of the profiles discovered during Host monitoring.

The following example requests an NVIDIA L40S-2B vGPU profile:

```
PCI = [
    CLASS   = "0302",
    DEVICE  = "26b9",
    PROFILE = "1146 (NVIDIA L40S-2B)",
    VENDOR  = "10de"
]
```

When the Virtual Machine is deployed, OpenNebula allocates a compatible GPU exposing the requested profile.

For MIG-backed vGPU deployments, the deployment workflow is identical. The available profiles are generated from the configured GPU Instances and automatically discovered during Host monitoring.

### Guest Configuration

After the Virtual Machine has been deployed, install the NVIDIA guest driver corresponding to the selected NVIDIA vGPU software release.

Refer to the NVIDIA AI Enterprise documentation or your Linux distribution for instructions on installing the appropriate guest driver.

After the installation completes, verify that the assigned virtual GPU is detected:

```shell
nvidia-smi
```

Use the output provided by the NVIDIA vGPU software stack for your selected profile to verify that:

* the assigned virtual GPU is detected correctly;  
* the reported GPU name matches the selected vGPU profile;  
* no driver or hardware errors are reported.

The guest configuration is identical for conventional NVIDIA vGPU and MIG-backed vGPU deployments. Once deployed, the guest operating system interacts with the assigned virtual GPU transparently, regardless of how the profile was created.

---

## NVIDIA Grace Platforms (AE)

### Overview

NVIDIA Grace Hopper and Grace Blackwell platforms are based on the Arm architecture and implement a virtualization model that differs from conventional x86 PCI passthrough systems. In addition to assigning GPUs to Virtual Machines, Grace platforms require a specific PCI topology based on dedicated PCI Root Complexes, SMMUv3 devices, IOMMUFD, and ACPI Generic Initiator NUMA nodes.

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

#### Configure QEMU Memory Locking

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

#### Bind GPUs to the Grace VFIO Driver

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
0019:01:00.0 3D controller [0302]: NVIDIA Corporation Device [10de:2046]
        Kernel driver in use: nvgrace_gpu_vfio_pci
```
#### Deploying a Virtual Machine

Grace platform Virtual Machines are deployed using the standard OpenNebula `PCI` attribute together with the CPU and NUMA configuration required by the workload.

The following example shows the relevant sections of a Virtual Machine Template configured with two Grace CPU NUMA nodes and four NVIDIA GB200 GPUs.

```default
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
