---
title: "Axelera GPU Passthrough"
linkTitle: "Axelera GPUs"
date: "2025-10-16"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "9"
---

{{< alert title="Work In Progress" type="primary" >}} GPU passthrough functionality for Axelera GPUs is currently under active development. If you would like to discuss a demonstration, please contact the [OpenNebula sales and customer support team](https://opennebula.io/contact/).{{< /alert >}}

## Overview

This guide describes how to assign an Axelera Metis AI Processing Unit (AIPU) directly to an OpenNebula Virtual Machine using PCI passthrough. The device is exclusively owned by the guest while the Virtual Machine is running; the Axelera driver and Voyager SDK are therefore installed in the guest, not on the Host.

The generic PCI passthrough configuration, including IOMMU, VFIO device ownership, and PCI monitoring, is described in the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/" %}}). Complete the Host configuration guide before commencing this guide.

The installation commands below reproduce a validated environment using Ubuntu 24.04, `metis-dkms` 1.5.7, and the Axelera runtime and development kit 1.6.0. Refer to the [Voyager SDK installation guide](https://github.com/axelera-ai-hub/voyager-sdk/blob/release/v1.7/docs/user-guides/sdk-install.md) before using a different software combination.

## Requirements

Before continuing, verify that:

* The Metis AIPU is installed and visible on the Host.
* [IOMMU]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/#step-2-enable-the-iommu" %}}) and [VFIO]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/#step-3-configure-vfio-device-binding" %}}) are configured on the Host.
* The OpenNebula [PCI monitoring probe is configured]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration/#step-5-configure-pci-monitoring" %}}).
* The guest uses Ubuntu 22.04 or Ubuntu 24.04 and has Internet access.
* The guest disk has at least 30 GB of capacity.
* The VM CPU model is `host-passthrough`.
* The VM **does not use** a Q35 machine type.

{{< alert title="Important" type="warning" >}}
The Voyager SDK operator build requires CPU features exposed by `host-passthrough`. With a generic CPU model, `make operators` can fail because NumPy requires the x86-64-v2 (`X86_V2`) instruction baseline. In the validated environment, the operator build also failed with a Q35 machine type. Leave the `OS/MACHINE` attribute unset so OpenNebula uses its default machine type.
{{< /alert >}}

## Configure the Host

### Identify and Bind the Metis Devices

List the Metis devices installed on the Host:

```shell
lspci -d 1f9d:
```

Example output:

```default
63:00.0 Processing accelerators: Axelera AI Metis AIPU (rev 02)
64:00.0 Processing accelerators: Axelera AI Metis AIPU (rev 02)
65:00.0 Processing accelerators: Axelera AI Metis AIPU (rev 02)
66:00.0 Processing accelerators: Axelera AI Metis AIPU (rev 02)
```

{{< alert title="Note" type="info" >}}
Systems with an outdated PCI ID database may display the devices using only their numeric identifiers:

```default
e3:00.0 Processing accelerators [1200]: Device [1f9d:1100]
e4:00.0 Processing accelerators [1200]: Device [1f9d:1100]
e5:00.0 Processing accelerators [1200]: Device [1f9d:1100]
e6:00.0 Processing accelerators [1200]: Device [1f9d:1100]
```

Update the database and then run the above `lspci` command again:

```shell
sudo update-pciids
```

Both outputs represent the same `1f9d:1100` device. The `-nn` option can be used to display the numeric class and device IDs together with the device name.
{{< /alert >}}

Bind each device intended for passthrough to `vfio-pci`. For example:

```shell
driverctl set-override 0000:e3:00.0 vfio-pci
driverctl set-override 0000:e4:00.0 vfio-pci
driverctl set-override 0000:e5:00.0 vfio-pci
driverctl set-override 0000:e6:00.0 vfio-pci
```

After setting the overrides, verify the binding on the Host before deploying a Virtual Machine:

```shell
lspci -nnk -d 1f9d:
```

In the output of this command, every device intended for passthrough must report `vfio-pci` as the kernel driver in use. For example:

```default
63:00.0 Processing accelerators [1200]: Axelera AI Metis AIPU (rev 02) [1f9d:1100]
        Kernel driver in use: vfio-pci
```

### Configure OpenNebula Monitoring

On the Front-end, add the Axelera vendor ID to the `filter` list in `/var/lib/one/remotes/etc/im/kvm-probes.d/pci.conf`:

```default
filter:
  - "1f9d:*"
```

Synchronize the monitoring probes and request a new monitoring cycle:

```shell
onehost sync --force
onehost flush <host>
```

Verify that OpenNebula discovered the devices:

```shell
onehost show <host>
```

The Metis devices must appear in the **PCI Devices** section. Device details may take more than one monitoring cycle to become available.

## Deploy the Virtual Machine

The following excerpt shows the relevant Virtual Machine Template attributes for a specific Metis device:

```default
CPU_MODEL = [
  MODEL = "host-passthrough"
]

DISK = [
  IMAGE = "Ubuntu 24.04",
  SIZE  = "30720"
]

PCI = [
  SHORT_ADDRESS = "e3:00.0"
]

NIC = [
  NETWORK = "host-only"
]
```

Replace the Image, network, and PCI address with values from your environment. The `SIZE` value is expressed in MB and expands the guest disk to 30 GB.

For automatic device selection, request a device by its vendor, device, and class IDs instead:

```default
PCI = [
  VENDOR = "1f9d",
  DEVICE = "1100",
  CLASS  = "1200"
]
```

Repeat the `PCI` section to assign multiple Metis devices to the same Virtual Machine.

{{< alert title="Important" type="warning" >}}
Do not add a Q35 value to `OS/MACHINE`. Use the OpenNebula default machine type for this configuration.
{{< /alert >}}

## Configure the Guest

After deploying the Virtual Machine, verify that the guest can see the assigned device:

```shell
lspci -nn -d 1f9d:
```

### Install the Metis Driver

Create the APT keyring directory and install the Axelera repository signing key:

```shell
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://software.axelera.ai/artifactory/api/security/keypair/axelera/public \
  | sudo gpg --dearmor -o /etc/apt/keyrings/axelera.gpg
```

Configure the repository matching the guest operating system:

{{< tabpane text=true right=false >}}
{{% tab header="**Ubuntu version**:" disabled=true /%}}
{{% tab header="**Ubuntu 22.04**" %}}
```shell
echo "deb [signed-by=/etc/apt/keyrings/axelera.gpg] https://software.axelera.ai/artifactory/axelera-apt-source ubuntu22 main" \
  | sudo tee /etc/apt/sources.list.d/axelera.list
```
{{% /tab %}}
{{% tab header="**Ubuntu 24.04**" %}}
```shell
echo "deb [signed-by=/etc/apt/keyrings/axelera.gpg] https://software.axelera.ai/artifactory/axelera-apt-source ubuntu24 main" \
  | sudo tee /etc/apt/sources.list.d/axelera.list
```
{{% /tab %}}
{{< /tabpane >}}

Install the kernel headers and the validated Metis driver, then load the module:

```shell
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r) metis-dkms=1.5.7
sudo modprobe metis
```

Verify that the module is loaded:

```shell
lsmod | grep metis
```

### Install the Voyager SDK

Clone the SDK release matching the validated 1.6.0 runtime and install its system dependencies:

```shell
git clone --branch v1.6.0 https://github.com/axelera-ai-hub/voyager-sdk.git
cd voyager-sdk
./install-dependencies.sh
sudo apt-get install -y python3-venv
```

Create and activate a Python virtual environment, then install the runtime and development kit:

```text
python3 -m venv axelera-env16
source axelera-env16/bin/activate
pip install --extra-index-url https://software.axelera.ai/artifactory/api/pypi/axelera-pypi/simple \
  axelera-rt==1.6.0 'axelera-devkit[all]==1.6.0'
make operators
```

Activate this environment again with `source axelera-env16/bin/activate` in each new shell before using the SDK.

Verify that the SDK detects the device:

```shell
axdevice
```

## Run the Inference Pipeline

As the final verification step, still within the `voyager-sdk` directory and with the loaded virtual environment, run an inference pipeline with a local video file:

```shell
./inference.py -v yolov5s-v7-coco video.mp4
```

Replace `video.mp4` with the path to the input video.

## Troubleshooting

### IOMMU Group Is Not Viable

If QEMU reports that the device's IOMMU group is not viable, another device in the same group is still using a Host driver. A typical error in `/var/log/one/oned.log` is:

```default
vfio 0000:e3:00.0: group 32 is not viable
Please ensure all devices within the iommu_group are bound to their vfio bus driver.
```

Identify the IOMMU group and inspect every device in it:

```shell
group=$(basename "$(readlink /sys/bus/pci/devices/0000:e3:00.0/iommu_group)")

for device in /sys/kernel/iommu_groups/"$group"/devices/*; do
  echo "== $(basename "$device") =="
  lspci -nnk -s "$(basename "$device")"
done
```

On systems where a PCI switch in the same group is managed by the `switchtec` module, unloading that module may allow the group to be assigned:

```shell
sudo modprobe -r switchtec
```

Retry the deployment after verifying that no remaining device in the group uses a Host driver.

{{< alert title="Warning" type="warning" >}}
Unload `switchtec` only after confirming that the Host does not require it to manage other hardware. This change lasts until the module is loaded again or the Host reboots. Consult the hardware vendor before blacklisting the module permanently.
{{< /alert >}}

### X11 Forwarding

To display the Voyager SDK graphical output through SSH, connect to the guest with X11 forwarding as appropriate for your security policy and install the X11 authentication tools:

```shell
sudo apt-get install -y xauth x11-apps
```

For example, through a jump Host:

```shell
ssh -X -J <jump-host> <user>@<guest-address>
```
