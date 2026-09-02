---
title: "NVIDIA vGPU and MIG-backed vGPU"
linkTitle: "NVIDIA vGPU and MIG"
date: "2025-10-16"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "6"
---

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

