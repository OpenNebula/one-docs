---
title: "Generic PCI Devices"
linkTitle: "Generic Devices"
date: "2026-09-02"
description:
categories:
pageintoc: "58"
tags:
weight: "3"
---

This guide describes how to assign generic PCI devices directly to Virtual Machines. Examples include NVMe controllers, SATA or SAS host bus adapters, USB controllers, audio devices, FPGAs, and other accelerators. For network adapters and GPUs, use the corresponding device-specific guides.

PCI passthrough operates on PCI functions. For example, passing through a storage controller gives the Virtual Machine control of the controller and its attached disks; passing through a USB controller gives it control of the controller and its downstream USB devices. It does not pass an individual non-PCI disk or USB peripheral.

{{< alert title="Warning" type="warning" >}}
Do not assign a device required by the Host, such as its boot storage controller or management interface. The device becomes unavailable to the Host while it is assigned to a Virtual Machine.{{< /alert >}}

## Requirements

Before assigning a PCI device:

* Complete the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}).
* Configure PCI monitoring so that OpenNebula discovers the device.
* Verify that every device in the same IOMMU group is prepared for passthrough and can be assigned to the same Virtual Machine.
* Ensure that the guest operating system provides a driver for the device.

## Inspecting Available Devices

Display the PCI devices discovered on a Host:

```shell
onehost show <host>
```

The **PCI Devices** section reports each device's PCI address, vendor, device and class identifiers, and the ID of the Virtual Machine using it. Refer to the [Host PCI Devices reference]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts#host-pci-devices" %}}) for the complete set of monitored attributes.

In Sunstone, select **Infrastructure**, **Hosts**, the required Host, and then the **PCI** tab:

{{< image
  pathDark="/images/host/dark/host_pci.png"
  path="/images/host/light/host_pci.png"
  alt="PCI devices discovered on an OpenNebula Host" align="center" width="90%" mb="20px"
>}}

## PCI Device Selection

OpenNebula can select a compatible device automatically or assign a specific PCI address.

### Automatic Selection

Automatic selection allows the scheduler to choose any available device matching the requested identifiers. Use `CLASS` for the device type, `VENDOR` for the manufacturer, and `DEVICE` for a specific hardware model. OpenNebula requires a candidate device to match every specified attribute.

The following example requests any monitored USB controller:

```default
PCI = [
  CLASS = "0c03"
]
```

Adding `VENDOR` narrows the request to any monitored USB controller manufactured by Renesas Electronics:

```default
PCI = [
  VENDOR = "1912",
  CLASS  = "0c03"
]
```

Adding `DEVICE` selects a specific model. This example requests any available Renesas uPD720202 USB 3.0 Host Controller:

```default
PCI = [
  VENDOR = "1912",
  DEVICE = "0015",
  CLASS  = "0c03"
]
```

Any combination of `VENDOR`, `DEVICE`, and `CLASS` can be used to control the selection scope. Configure narrow PCI monitoring filters before using broad selection criteria. This prevents OpenNebula from assigning a Host device that was not intended for passthrough.

### Explicit Selection

Use `SHORT_ADDRESS` to request a specific PCI function:

```default
PCI = [
  SHORT_ADDRESS = "81:00.0"
]
```

The short address uses the `bus:device.function` format without the PCI domain. Explicit selection restricts scheduling to a Host on which that address is available. Use it when the workload requires a particular device because of its physical interconnection, PCI topology, NUMA locality, or another hardware-specific constraint.

`DEVICE` identifies the PCI hardware device ID; it must not be used for a PCI address.

### Selecting a PCI Device in Sunstone

When creating or editing a Virtual Machine Template, open **Advanced options**, select **PCI Devices**, and click **Attach PCI device**:

{{< image
  pathDark="/images/host/dark/host_vm_pci.png"
  path="/images/host/light/host_vm_pci.png"
  alt="Adding a PCI device to an OpenNebula Virtual Machine Template" align="center" width="90%" mb="20px"
>}}

Select the vendor, device, and class constraints for automatic scheduling, or select a specific PCI address when the workload requires a particular device.

## Assigning Multiple Devices

Add one `PCI` section for each requested PCI function:

```default
PCI = [
  SHORT_ADDRESS = "81:00.0"
]

PCI = [
  SHORT_ADDRESS = "81:00.1"
]
```

Devices belonging to the same IOMMU group must be assigned together to the same Virtual Machine, as described in the [VFIO Device Ownership section]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration#vfio-device-ownership" %}}).

## Scheduling

OpenNebula deploys the Virtual Machine only on a Host that has every requested PCI device available. If no Host satisfies the request, the Virtual Machine remains pending and the Scheduler log reports that no suitable Host was found.

Automatic selection is recommended because it allows the scheduler to place the workload on any compatible Host. Use `SHORT_ADDRESS` only when device topology or another hardware constraint requires an exact PCI function.

## Existing Virtual Machines

PCI devices can also be attached to or detached from an existing Virtual Machine in a supported power state. Refer to [PCI Devices in the Virtual Machine Instances Guide]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances#vm-guide2-pci" %}}) for the `onevm pci-attach` and `onevm pci-detach` commands.

## Guest Verification

After deployment, verify that the guest detects the assigned PCI device:

```shell
lspci -nn
```

Use a device-specific utility when appropriate. For example, use `lsblk` for an assigned storage controller or `lsusb` for devices connected through an assigned USB controller.

## Next Steps

* Continue with the [Network Interfaces Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces/" %}}) for PCI network interfaces and SR-IOV Virtual Functions.
* Continue with the [NVIDIA GPU Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) for NVIDIA GPU passthrough.
