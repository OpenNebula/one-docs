---
title: "Host Configuration for PCI Passthrough and SR-IOV"
linkTitle: "Host Configuration"
date: "2026-06-30"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "2"
---

This guide describes the common host configuration required to enable PCI passthrough in OpenNebula. These requirements apply independently of the type of PCI device being assigned to virtual machines. Device-specific configuration is covered in the corresponding guides.
The guide assumes a Linux host running the OpenNebula KVM hypervisor. While the examples use common Linux utilities and a GRUB-based bootloader, equivalent procedures can be used with other Linux distributions and bootloaders.

## Prerequisites

Before configuring PCI passthrough, verify that the host satisfies the following requirements:
* Hardware-assisted virtualization enabled in the system firmware.
* An IOMMU implementation supported by the processor:
    * Intel VT-d
    * AMD-Vi
    * Arm SMMUv3
* OpenNebula host packages installed, including KVM, QEMU, and libvirt support.

---

## Step 1. Enable the IOMMU

PCI passthrough requires the Input-Output Memory Management Unit (IOMMU) to isolate DMA accesses performed by assigned devices.

### Enable the IOMMU in the Firmware

Access your system's BIOS or UEFI setup and enable the corresponding IOMMU option. Typical firmware options include:

* Intel VT-d
* AMD IOMMU
* Arm SMMU

Save the changes and reboot the system.

### Enable the IOMMU in the Kernel

{{< tabpane text=true right=false >}}
{{% tab header="**Arch**:" disabled=true /%}}
{{% tab header="Intel"%}}
```shell
intel_iommu=on iommu=pt
```
{{% /tab %}}
{{% tab header="AMD"%}}
```shell
amd_iommu=on iommu=pt
```
{{% /tab %}}
{{% tab header="ARM"%}}
Most Arm platforms enable the SMMU automatically. Refer to the platform documentation if additional kernel parameters are required.

After modifying the kernel command line, regenerate the bootloader configuration using the appropriate command for your Linux distribution and reboot the host.
{{% /tab %}}
{{< /tabpane >}}

### Verification

Display the kernel command line:

```shell
cat /proc/cmdline
```

Verify that the IOMMU has been initialized:

```shell
dmesg | grep -Ei "iommu|dmar|smmu"
```

Typical output:

```default
DMAR: IOMMU enabled
```

or:

```default
AMD-Vi: Initialized
```

or:

```default
arm-smmu-v3 ...
```

## Step 2. Configure VFIO Device Binding

PCI devices assigned to virtual machines must be managed by a VFIO driver instead of their native host driver. OpenNebula supports any mechanism that binds devices to VFIO. The recommended approach is to use the **driverctl** utility, which provides persistent per-device driver overrides using the Linux kernel `driver_override` interface.

For Linux Containers, the PCI device driver shouldn’t be changed. Skip this section entirely if using passthrough in Linux Containers.

{{< alert title="Note" type="primary" >}}This step is not needed for NVIDIA GPUs in MIG or vGPU mode. In these cases you can continue to [Step 3](#step-3-configure-huge-pages-optional).{{< /alert >}}

### Install driverctl

Install the driverctl package using your Linux distribution package manager.

### Load the VFIO Modules

Load the required kernel modules:

```shell
modprobe vfio
modprobe vfio-pci
```

To load them automatically after reboot, create:

```default
/etc/modules-load.d/vfio.conf
```

With contents:

```default
vfio
vfio-pci
```

### Identify the PCI Device

List the available PCI devices:

```shell
lspci -nn
```

Example output:

```default
43:00.0 3D controller: NVIDIA Corporation GH100 ...
43:00.1 Audio device: NVIDIA Corporation ...
```

Display the current driver:

```shell
lspci -nnk -s 43:00.0
```

Example output:

```default
Kernel driver in use: nvidia
```

### Bind the Device

Assign the device to the `vfio-pci` driver:

```shell
driverctl set-override 0000:43:00.0 vfio-pci
```

Many PCI devices expose multiple functions. For example, GPUs often expose both a graphics controller and an audio controller. Repeat the command for every PCI function that will be assigned to the virtual machine. The override is persistent and is automatically restored after reboot.

{{< alert title="Note" type="primary" >}}
Once a device is bound to a VFIO driver, it is no longer available to the host operating system until the override is removed.
{{< /alert >}}

### Verification

Verify that the device is managed by VFIO:

```shell
lspci -nnk -s 43:00.0
```

Expected output:

```default
Kernel driver in use: vfio-pci
```

Verify that libvirt can detect the device:

```shell
virsh nodedev-list | grep pci
```

List the configured driver overrides:

```shell
driverctl list-overrides
```

### Removing an Override

To restore the default host driver:

```shell
driverctl unset-override 0000:43:00.0
```

{{< alert title="Note" type="primary" >}}
Some hardware platforms require a platform-specific VFIO driver instead of `vfio-pci`. For example, NVIDIA Grace systems use the `nvgrace_gpu_vfio_pci` driver. These platform-specific procedures are described in the corresponding device guides.
{{< /alert >}}

### VFIO Device Ownership

For OpenNebula to manage the VFIO device files in `/dev/vfio/`, the files must be owned by user `root` and group `kvm` (`root:kvm`). This is achieved by creating a `udev` rule.

1. **Identify the IOMMU group for your GPU using its PCI address**:

    ```shell
    find /sys/kernel/iommu_groups/ -type l | grep 43:00.0

    /sys/kernel/iommu_groups/85/devices/0000:43:00.0
    ```

    In this example, the IOMMU group is 85. The IOMMU group is the minimum device-ownership unit used by VFIO. All devices in the same group must be configured for passthrough and assigned together to the same virtual machine. Modern server platforms usually provide suitable per-device or per-slot isolation, but verify the group membership before continuing:

    ```shell
    ls -1 /sys/kernel/iommu_groups/85/devices/
    ```

2. **Create a udev rule**: Create the file /etc/udev/rules.d/99-vfio.rules with the following content:

    ```default
    SUBSYSTEM=="vfio", GROUP="kvm", MODE="0660"
    ```

3. **Reload udev rules**:

    ```shell
    udevadm control --reload
    udevadm trigger
    ```

4. **Verify ownership**: Check the ownership of the device file corresponding to your GPU’s IOMMU group.

    ```shell
    ls -la /dev/vfio/
    crw-rw---- 1 root kvm 509, 0 Oct 16 10:00 85
    ```

## Step 3. Configure Huge Pages (Optional)

Huge Pages reduce memory translation overhead and are recommended for memory-intensive workloads such as GPUs and high-performance networking.

Edit the bootloader configuration and append the appropriate Huge Page parameters to the kernel command line.

Example:

```default
hugepages=1024 default_hugepagesz=1G hugepagesz=1G
```

The appropriate Huge Page size depends on the processor architecture and workload. On x86 platforms, common Huge Page sizes are 2 MB and 1 GB.

Regenerate the bootloader configuration using the appropriate command for your Linux distribution and reboot the host.

**Notes**:

* Ensure sufficient free memory is available before reserving Huge Pages.
* The selected Huge Page size must be supported by both the processor and the kernel.
* Display the supported Huge Page size:
    ```shell
    grep Hugepagesize /proc/meminfo
    ```

OpenNebula allows virtual machines to request Huge Pages directly from the VM Template.

### Verification

Display the current Huge Page configuration:

```shell
grep Huge /proc/meminfo
```

## Step 4. Configure PCI Monitoring

OpenNebula discovers PCI devices through the host monitoring subsystem. PCI monitoring is disabled by default to avoid exposing unnecessary hardware resources.

Before PCI devices can be assigned to virtual machines, configure the monitoring subsystem to discover the devices intended for passthrough.

### Configure System-wide PCI Monitoring

The default monitoring configuration is stored on the Front-end:

```default
/var/lib/one/remotes/etc/im/kvm-probes.d/pci.conf
```

The configuration supports three filtering mechanisms:

* **filter** — Select devices using PCI vendor, device and class identifiers.
* **short_address** — Restrict discovery to specific PCI addresses.
* **device_name** — Select devices matching one or more regular expressions.

The filters are applied sequentially.

Example:

```default
filter:

  - "10de:*"

short_address: []

device_name: []
```

To monitor a specific PCI device:

```default
filter:

  - "10de:*"

short_address:

  - "43:00.0"

device_name: []
```

To discover SR-IOV Virtual Functions:

```default
filter:

  - "*:*"

device_name:

  - "Virtual Function"
```

### Override Monitoring at Cluster or Host Level

The system-wide configuration can be overridden for individual clusters or hosts using the corresponding template attributes:

| Parameter | Description |
|-----------|-------------|
| PCI_FILTER | (List) Filters by PCI vendor:device:class patterns (same as for lspci) |
| PCI_SHORT_ADDRESS | (List) Filters by short PCI address bus:device.function |
| PCI_DEVICE_NAME | (List) Filters by the PCI device name reported by the Host  |

This allows different clusters to expose different classes of PCI devices while sharing the same frontend configuration.

{{< alert title="Recommendation" type="primary" >}}
Configure the narrowest possible filters to expose only devices intended for passthrough.{{< /alert >}}

### Synchronize the Monitoring Probes

After modifying `pci.conf`, synchronize the updated monitoring probes to all hosts (run as oneadmin):

```shell
onehost sync --force
```

Then trigger a new monitoring cycle:

```shell
onehost forceupdate <host>
```

Alternatively, wait for the next scheduled monitoring cycle.

## Step 5. Verify PCI Device Discovery

After the monitoring cycle completes, verify that OpenNebula has discovered the expected PCI devices.
Display the monitored devices:

```shell
onehost show <host>
```

Alternatively, inspect the PCI Devices tab from the Sunstone interface.

Verify that:

* The expected PCI devices are listed.
* Vendor and device identifiers are correct.
* Driver information is correct.
* NUMA information is reported.
* SR-IOV Virtual Functions are detected, when applicable.
* Device availability matches the host configuration.

If a device does not appear:

* Verify that it matches the configured monitoring filters.
* Verify that pci.conf has been synchronized to the hosts.
* Verify that the host has completed a monitoring cycle.
* Verify that the device is visible using lspci.
* Verify that the device is bound to the appropriate VFIO driver.
* Verify that the OpenNebula monitoring service is running.

## Configuration Checklist

Before deploying virtual machines using PCI passthrough, verify that the following requirements have been completed:
* &#10004; Hardware virtualization enabled
* &#10004; IOMMU enabled
* &#10004; VFIO modules loaded
* &#10004; PCI devices bound to VFIO
* &#10004; Huge Pages configured (if required)
* &#10004; SR-IOV configured (if required)
* &#10004; PCI monitoring configured
* &#10004; PCI devices discovered by OpenNebula

Once these checks are complete, the host is ready to assign PCI devices to virtual machines.

## Next Steps

After completing the host configuration:

* Continue with the [Generic PCI Devices Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/generic_devices/" %}}) to assign storage controllers, USB controllers, audio devices, and other generic PCI devices.
* Continue with the [Network Interfaces Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces/" %}}) to configure PCI passthrough or SR-IOV network devices.
* Continue with the [NVIDIA GPUs Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) for NVIDIA GPU passthrough, mediated devices (vGPU), and platform-specific GPU configuration.
* Continue with the [NVIDIA Fabric Manager Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/one_fabricmanager/" %}}) when deploying supported NVSwitch-based systems.
