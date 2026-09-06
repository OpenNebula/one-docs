---
title: "ARM-based Cloud"
linkTitle: "ARM-based Cloud"
description: "Reference OpenNebula on Ampere hardware for certifying deployment. Includes HW specifications, OpenNebula architecture, and verification instructions."
weight: 2
---

[Ampere](https://amperecomputing.com/) is a semiconductor design company that develops server-grade processors for cloud environments, with a focus on high performance and energy efficiency.

You can deploy and verify an OpenNebula cloud on Ampere hardware, by using [Certified Ampere Hardware with OpenNebula software](https://github.com/OpenNebula/certified-hardware-ampere), a set of Ansible playbooks that allows you to deploy and verify an OpenNebula cloud with a few simple commands.

This guide provides a reference Ampere hardware specification that has been used to verify OpenNebula. It includes instructions on how to perform a ZeroTouch deployment of OpenNebula on the certified hardware, and provides a reference architecture and configuration.

Following this guide, you can:

- Perform a Zero-touch deployment of OpenNebula over these resources.
- Ensure the correct operation of the resulting cloud using an automated verification procedure.

Additionally, this guide includes a brief description of how to instantiate a Virtual Machine, to help you get started on your OpenNebula Cloud.

## Basic Outline of the Deployment Procedure

Performing the deployment involves these high-level steps:

1. Clone the dedicated OpenNebula on Ampere GitHub repository on your deployment machine.
1. Modify the repository with the parameters for your Ampere servers.
1. Perform the automated deployment to the Ampere servers.
1. Verify the deployment by running the automated verification command.

## Additional Information Resources

 - [Certified Ampere Hardware with OpenNebula software](https://github.com/OpenNebula/certified-hardware-ampere)
 - [Ampere Resource Library](https://amperecomputing.com/resource-library)

## Hardware Specification and Architecture

This section contains the specification of the used Ampere hardware and software resources for the reference OpenNebula deployment.

## Architecture

The target high-level cloud architecture overview is shown below. Two Ampere servers are used: the first for hosting the OpenNebula Front-end services and VMs, the second for hosting VMs only. A simple VXLAN networking is configured for the communication between the VMs, so all deployed VMs are attached to the same logical LAN.

![><][high-level]

[high-level]: /images/solutions/ampere/high-level-architecture.png

## Hardware Specification

The tables below detail the characteristics for the Front-end, virtualization host, storage, networking and provisioning model.

### Front-end Requirements

Two identical servers were used. One of them acts as Front-end and both of them acts as hosts.

| FRONT-END  |
| :---- | :---- |
| Number of Zones | 1 |
| Cloud Manager | OpenNebula {{< release >}} |
| Server Specs | Ampere(R) Altra(R), details in the [table below](#server-specifications) |
| Operating System | Ubuntu 24.04.2 LTS |
| High Availability | No (1 Front-end) |
| Authorization | Builtin |


### Host Requirements

| VIRTUALIZATION HOSTS  |
| :---- | :---- |
| Number of Nodes | 2 |
| Server Specs | Ampere(R) Altra(R), details in the [table below](#server-specifications) |
| Operating System | Ubuntu 24.04.2 LTS |
| Hypervisor | KVM |
| Special Devices | None |

### Storage Specification

| STORAGE   |
| :---- | :---- |
| Type | Local disk |
| Capacity | 1 Datastore |


### Network Requirements

| NETWORK   |
| :---- | :---- |
| Networking | VXLAN |
| Number of Networks | 1 networks: VXLAN |

### Provisioning Model

| PROVISIONING MODEL  |
| :---- | :---- |
| Manual on-prem | The two servers have been manually provisioned and configured on-prem. |


### Server Specifications

| Parameter                | Ampere Server                                                                              |
|--------------------------|-------------------------------------------------------------------------------------------|
| **Architecture**         | aarch64 (ARM 64-bit)                                                                      |
| **CPU Model**            | Ampere(R) Altra(R) Processor Q80-30 CPU @ 3.0GHz (Neoverse-N1)                            |
| **CPU Vendor**           | Ampere(R)                                                                                 |
| **CPU Cores**            | 160 (2 sockets × 80 cores, 1 thread per core)                                             |
| **CPU Frequency**        | 1000 MHz (min), 3000 MHz (max)                                                            |
| **NUMA Nodes**           | 2 (Node0: CPUs 0-79, Node1: CPUs 80-159)                                                  |
| **L1d Cache**            | 10 MiB (160 × 64 KiB)                                                                     |
| **L1i Cache**            | 10 MiB (160 × 64 KiB)                                                                     |
| **L2 Cache**             | 160 MiB (160 × 1 MiB)                                                                     |
| **Vulnerabilities**      | All major mitigated or not affected                                                        |
| **BIOS Vendor**          | Ampere(R)                                                                                 |
| **BIOS Version**         | 0ACOD014 (SCP: 2.10.20230126)                                                             |
| **BIOS Release Date**    | 12/12/2023                                                                                |
| **BIOS Revision**        | 5.15                                                                                      |
| **Firmware Revision**    | 2.10                                                                                      |
| **ROM Size**             | 7936 kB                                                                                   |
| **Boot Mode**            | UEFI, ACPI supported                                                                      |
| **Disks**                | 1 × NVMe (Samsung SM981/PM981/PM983, 894.3G)                                              |
| **Partitions**           | /boot/efi (1G), /boot (2G), LVM root (891.2G)                                             |
| **Network**              | 2 × Intel I350 Gigabit Ethernet                                                           |
| **USB Controllers**      | Hitachi, Renesas uPD720201 USB 3.0, Linux Foundation root hubs                            |
| **VGA Controller**       | ASPEED Technology, Inc. ASPEED Graphics Family (server management, not for computation)    |
| **PCI Devices**          | Multiple Ampere PCIe root complexes, bridges, and controllers                             |
| **RAM**                  | 32 GiB                                                                                   |
| **Other**                | No high-performance GPU detected                                                          |

## Automated Deployment and Configuration

To perform the automated deployment of an OpenNebula cloud, the Ampere infrastructure of connected servers must be previously configured and available. This guide provides guidance on how to extract the list of required parameters of the provisioned infrastructure -- which will later be used for the automation of the OpenNebula deployment -- and an outline of the process for the automated deployment of an OpenNebula cloud.

## Ampere Infrastructure Provisioning

Provisioning the Ampere infrastructure on premises is out of the scope of this guide. To perform the automated deployment of an OpenNebula cloud, the Ampere infrastructure must meet the following conditions:

- Servers are provisioned
- Networking is configured
- Storage is configured
- The required operating system is installed
- Servers in the infrastructure are reachable from the machine where the deployment commands will be run

For the reference architecture and HW/SW specifications, please refer to the [Hardware Specification and Architecture](#hardware-specification-and-architecture) section.

## Save Required Parameters

To proceed with OpenNebula deployment, we need to extract and save some required parameters that the deployment automation relies on.

| Description | How to obtain the parameter |
| :----- | :----- |
| Front-end Host IP | A reachable IP on the server, that will be used by the automated deployment. |
| KVM Host IP | A reachable IP on the server, that will be used by the automated deployment. |
| `VXLAN PHYDEV` | Interface name of the private LAN on all servers. To find out the name of the interface, run `ip address` in each server's command line. |
| GUI password for user `oneadmin` | Specified by the administrator performing the deployment steps. |

## Deployment and Automated Verification Procedure

The complete OpenNebula deployment procedure and all of the required resources are available in the [Certified Hardware Ampere for OpenNebula](https://github.com/OpenNebula/certified-hardware-ampere), also referred to as the **deployment repository**. For instructions on how to use the required parameters extracted from the provisioned Ampere servers, please check the `README` file in the repo.

The deployment procedure consists of the following high-level steps:

1. Clone the deployment repository.
1. Update the deployment repository with the required parameters gathered above.
1. Launch the deployment automation commands.
1. Launch the verification automation command.

{{< alert title="Note" type="info" >}}
For detailed information about how to use the required parameters and which configuration files to modify, please refer to the `README` of the [Certified Hardware Ampere for OpenNebula](https://github.com/OpenNebula/certified-hardware-ampere).
{{< /alert >}}

## Validate Certified Hardware Deployments

<a id="validate-certified-hardware"></a>

{{< alert title="Tip" type="tip" >}}
This guide provides the basic steps. If you wish to see a more detailed guide, please refer to [Deploying a Virtual Machine Locally]({{% relref "deploy_opennebula_onprem_with_minione#deploying-a-virtual-machine-locally" %}}).
{{< /alert >}}

After successfully verifying the infrastructure deployed by the automations, to run a Virtual Machine access the OpenNebula web UI at:

`http://<Front-end IP>:2616/fireedge/sunstone`

To log in, use the default username `oneadmin`, and the password specified in the `one_pass` variable of the inventory file.

The image below shows the **Alpine Linux 3.20** Virtual Machine included in the OpenNebula installation:

<a id="one-marketplace"></a>

{{< image
    pathDark="/images/sunstone/misc/dark/alpine_320_marketplace.png"
    path="/images/sunstone/misc/light/alpine_320_marketplace.png"
    alt="Alpine 3.20 in marketplace" align="center" width="90%" mb="20px"
  >}}

{{< alert title="Warning" type="warning" >}}
Make sure to choose the correct variant of the image, which fits the certified hardware's architecture. For example for ARM-based architectures the correct Alpine Linux 3.20 Virtual Machine template is **Alpine Linux 3.20 (aarch64)**.
{{< /alert >}}

To instantiate the VM, in the Sunstone UI's left-hand menu go to **Instances** --> **VMs**. Click the **Create** icon highlighted below, then select the Virtual Machine template. Follow the steps of the VM instantiation wizard. For this basic guide, all values can be left empty or at their defaults.

<a id="one-new-vm"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/create_vm.png"
    path="/images/sunstone/misc/light/create_vm.png"
    alt="Create VM" align="center" width="90%" mb="20px"
  >}}

In the **Instances -> VMs** view select the new VM in the list to open the details page **Configuration** tab. Select **Update configuration**.

<a id="one-vm-config"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/update_vm_config.png"
    path="/images/sunstone/misc/light/update_vm_config.png"
    alt="Create VM" align="center" width="90%" mb="20px"
  >}}

In the **Context** tab of the modal dialog that opens, scroll down to the **Context Custom Variables** section and expand it. Find the `PASSWORD` field and select **Update** (the pencil icon), then specify the desired root password for the VM, then click **Accept**, as shown below, then press **Continue**.

{{< image
    pathDark="/images/sunstone/misc/dark/update_vm_password.png"
    path="/images/sunstone/misc/light/update_vm_password.png"
    alt="Update VM password" align="center" width="90%" mb="20px"
  >}}

Log in to the VM via VNC, go to the ellipsis drop-down menu and select **Console -> VNC**. Log in as user `root` with the password that you specified in the previous step.

<a id="one-vnc-connect"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/vm_vnc.png"
    path="/images/sunstone/misc/light/vm_vnc.png"
    alt="VNC" align="center" width="90%" mb="20px"
  >}}

After accessing the deployed VM's command line interface, verify that the terminal is responsive. For example, change to the home folder of user `root`:

```bash
root@vm:~# cd ~
root@vm:~# pwd
/root
```

Finally, as a cleanup step, terminate the VM by clicking the red “Trash can” icon, then verify that the VM transitions to state `DONE`, as shown below.

<a id="one-terminate-vm"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/shutdown_done.png"
    path="/images/sunstone/misc/light/shutdown_done.png"
    alt="Shutdown" align="center" width="90%" mb="20px"
  >}}

[one-marketplace]: /images/guides/common_101_ui/one-marketplace.png
[one-new-vm]: /images/guides/common_101_ui/one-new-vm.png
[one-vm-config]: /images/guides/common_101_ui/one-vm-config.png
[one-vnc-connect]: /images/guides/common_101_ui/one-vnc-connect.png
[one-terminate-vm]: /images/guides/common_101_ui/one-terminate-vm.png
