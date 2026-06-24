---
title: "Deploy OpenNebula on AWS with miniONE"
linkTitle: "Install miniONE on AWS"
date: "2025-02-17"
description:
categories: [Introduction, Learning, Deployment, Evaluation]
pageintoc: "19"
tags: ['Quick Start', AWS, Tutorial, miniONE]
type: docs
weight: "2"
---

<a id="try-opennebula-on-kvm"></a>

<!--# Deploy an OpenNebula Front-end on AWS -->

## Overview

In this tutorial, we will install an OpenNebula Front-end and a KVM hypervisor node on an AWS bare metal instance in under ten minutes using the **miniONE** installation tool from OpenNebula.

miniONE is a straightforward tool for deploying an evaluation version of OpenNebula. After running the miniONE script, all the OpenNebula services needed to use, manage and run a small cloud deployment will be installed on a single AWS instance.

This tutorial covers installation of a Front-end and KVM hypervisor node on an AWS instance. To complete the procedures detailed in the following [Kubernetes quickstart guides]({{% relref "getting_started/try_opennebula/try_kubernetes_on_opennebula/" %}}) it is necessary to complete this installation using a `c5.metal` "bare metal" AWS instance.

During this tutorial we will complete the following steps:

1. Launch a properly configured `c5.metal` instance on AWS.
2. Access the AWS instance command line through SSH.
2. Download and run the miniONE installation script.
3. Verify the installation.
4. Instantiate a Virtual Machine (VM) with Alpine Linux.

Once you have completed this tutorial, you will have an evaluation version of OpenNebula installed on your AWS instance and you will understand how to use the Sunstone user interface to instantiate a VM.

## Before Starting

To complete this tutorial, you need to login to a remote Linux AWS instance via SSH. If you are using MacOS or Linux, you can achieve this through a native terminal. If you are working on a Windows machine, you need to install an SSH client application such as [PuTTY](https://putty.software/).

## Step 1. Prepare a Virtual Machine Instance in AWS

If you don't already have an AWS account, [create one](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/). Login to the AWS console then Navigate to the [EC2 dashboard](https://console.aws.amazon.com/ec2) and [choose your region](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html). 

Click on **Launch instance**, this will take you to the [Launch Instance Wizard](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance-wizard.html). In the name and tags section enter an appropriate and memorable name such as `minione-test`:

{{< image
  pathDark="/images/quickstart/dark/minione_aws_instance_name.png"
  path="/images/quickstart/light/minione_aws_instance_name.png"
  alt="Name instance" align="center" width="90%" mb="20px"
>}}

Choose the **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** Amazon Machine Image (AMI). Leave the architecture as **64-bit (x86)**:

{{< image
  pathDark="/images/quickstart/dark/minione_aws_os_image.png"
  path="/images/quickstart/light/minione_aws_os_image.png"
  alt="AMI" align="center" width="90%" mb="20px"
>}}

Choose the `c5.metal` instance type:
+
{{< image
  pathDark="/images/quickstart/dark/minione_aws_instance_type.png"
  path="/images/quickstart/light/minione_aws_instance_type.png"
  alt="Instance type" align="center" width="90%" mb="20px"
>}}

If you don't already have a key pair (a `.pem` or `.ppk` file), select **Create new key pair** in the **Key pair (login)** section. Choose a sensible name for the key pair, it cannot be renamed later. You may either use your name or a context such as `minione-admin`. Select EC25519 for **Key pair type** and choose the format: 

* `.pem` (Linux/Mac)
* `.ppk` (Windows with PuTTY). 

{{< image
  pathDark="/images/quickstart/dark/minione_aws_key_pair.png"
  path="/images/quickstart/light/minione_aws_key_pair.png"
  alt="Key pair" align="center" width="50%" mb="20px"
>}}

Click **Create key pair**. A `.pem` or `.ppk` file will be downloaded to your computer through the browser. Store the key in a secure and memorable location on your local machine, you will need it to access the AWS instance. It is recommended to change the permissions on the file such that only your user can access the key file.

In **Network settings** click **Edit** in the top right corner of the section and select **Create security group**:

{{< image
  pathDark="/images/quickstart/dark/minione_aws_network_settings_upper.png"
  path="/images/quickstart/light/minione_aws_network_settings_upper.png"
  alt="Network settings" align="center" width="90%" mb="20px"
>}}

In the section labelled **Inbound Security Group Rules** click **Add security group rule** (leave the existing settings for port 22). In the **Port range** field enter port 80 and change the **Source type** field to **Anywhere**.

{{< image
  pathDark="/images/quickstart/dark/minione_aws_network_settings_lower.png"
  path="/images/quickstart/light/minione_aws_network_settings_lower.png"
  alt="Network settings" align="center" width="90%" mb="20px"
>}}

In the **Configure storage** section select **80 GiB** of `gp3` storage. You do not need to edit the **Advanced details** section.

{{< image
  pathDark="/images/quickstart/dark/minione_aws_configure_storage.png"
  path="/images/quickstart/light/minione_aws_configure_storage.png"
  alt="Configure storage" align="center" width="90%" mb="20px"
>}}

Now click **Launch instance**. AWS will now schedule your instance. Note that `c5.metal` instances can take several minutes to be scheduled depending on availability and account settings. Contact your DevOps team or system administrator if you have trouble launching your instance. 

## Step 2. Access the AWS Instance through SSH

To access the command line of your newly created AWS instance, you must use SSH or PuTTY. When you launch your AWS instance, it will be assigned a public IPv4 address. You can find this in the instance details page of your new instance. Locate your instance by going to **EC2** -> **Instances** -> **Instances**. Locate your instance in the list using the name you entered earlier and scroll horizontally to the **Public IPv4 Address** column. This is the address you will use to access your instance in the following commands.

### Linux:

Open a terminal and enter the following command, replacing the IP and location of the PEM file:

```bash
ssh <public IP of the AWS instance> -l ubuntu -i <PEM file>
```

For example:

```bash
ssh 3.143.176.142 -l ubuntu -i ~/.ssh/minione-admin.pem
```

### Windows:

Open a command prompt 

```bash
putty.exe ubuntu@<public IP of the AWS instance> -i <PEM file>
```

For example:

```bash
putty.exe ubuntu@3.143.176.142 -i minione-admin.ppk
```

## Step 3. Update the VM Operating System

Once you have logged in to the VM as user `ubuntu`, use the `sudo` command to switch to the root user (no password is required):

```bash
sudo -i
```

Then, update the system to its latest software packages by running the following command:

```bash
apt update && apt upgrade
```

After updating, you may need to restart the VM to run the latest kernel. Check the output of the `apt upgrade` command for lines similar to the following:

```default
Pending kernel upgrade!
Running kernel version:
  6.8.0-1012-aws
Diagnostics:
  The currently running kernel version is not the expected kernel version 6.8.0-1014-aws.
```

In this example, a restart is required to upgrade to kernel version `6.8.0-1014-aws`. 

If you receive a message indicating that the kernel is up-to-date, you may skip the following restart procedure and continue with step 4. Otherwise, to restart the VM, run:

```bash
shutdown -r now
```

You will be immediately logged out of the VM as it restarts. Wait a few moments for the VM to finish rebooting, then login again using the same procedure as before. After logging back into the VM, you can check the running kernel version with:

```bash
uname -a
```

For example, in this case:

```default
$ uname -a
Linux ip-172-31-3-252 6.8.0-1014-aws #15-Ubuntu SMP Thu Aug  8 19:13:06 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

Your AWS VM is now ready. In the next step we’ll download the miniONE script to the VM and run the installation.

## Step 4: Download and install miniONE

From the command line of your AWS VM instance, use the `sudo` command to become the `root` user (this will not require a password):

```bash
sudo -i
```

Download the miniONE installation script to your current directory:

{{% if-version is="7.0" %}}
```bash
wget 'https://github.com/OpenNebula/minione/releases/download/v7.0.1/minione'
```
{{% /if-version %}}
{{% if-version is="7.1" %}}
```bash
wget 'https://github.com/OpenNebula/minione/releases/latest/download/minione'
```
{{% /if-version %}}
{{% if-version is="7.2" %}}
```bash
wget 'https://github.com/OpenNebula/minione/releases/download/v7.2.0/minione'
```
{{% /if-version %}}
{{% if-version is="7.3" %}}
```bash
wget 'https://github.com/OpenNebula/minione/releases/latest/download/minione'
```
{{% /if-version %}}

Now make the `minione` script executable:

```bash
chmod +x minione
```

Run the miniONE installation script:

```bash
./minione
```

{{< alert title="Tip" type="primary" >}} miniONE will create credentials with a randomized password for logging into the Sunstone UI. You can use the `--password` option to enter a secure and memorable password of your own: `./minione --password <password>`{{< /alert >}} 

The miniONE script executes the installation while logging output to the terminal. Installation usually takes between one and three minutes. Once finished, miniONE displays a report in the terminal with connection parameters and login credentials:

```default
### Report
OpenNebula 7.0 was installed
Sunstone is running on:
  http://[omitted]/
FireEdge is running on:
  http://[omitted]
Use following to login:
  user: oneadmin
  password: lCmPUb5Gwk
```

Make sure to save these credentials somewhere secure (including the IP address), you will need them to login to the Sunstone UI.

### Synchronize the Host

Once installation is finished, synchronize the KVM Host on the AWS VM instance.

Switch to the `oneadmin` user:

```bash
su - oneadmin
```

Sync the KVM Host:

```bash
onehost sync --force
```

Verify that the Host is in sync:

```bash
onehost list
```

The Host may take several minutes to synchronize. continue running the `onehost list` command until the `STAT` column of the output displays `on`:

```default
ID NAME                       CLUSTER    TVM      ALLOCATED_CPU      ALLOCATED_MEM STAT
 0 localhost                  default      0      0 / 9600 (0%)   0K / 188.5G (0%) on
```

At this point, you have successfully installed miniONE. OpenNebula services should be running, and the system should be ready for your first login.

{{< alert title="Important" type="info" >}}
In this configuration, Sunstone exposes its HTTP endpoint on a public network interface. miniONE is an evaluation tool, and this configuration should not be used in production environments.{{< /alert >}}

## Step 5: Verify the Installation

Now verify the installation by logging in to OpenNebula's Sunstone UI.

Point your browser to the Edge IP and port provided by the miniONE report, which is normally the same as the public IP of the AWS instance. You should be greeted with the Sunstone login screen:

{{< image
  pathDark="/images/quickstart/dark/sunstone_login_page.png"
  path="/images/quickstart/light/sunstone_login_page.png"
  alt="Sunstone login" align="center" width="50%" mb="20px"
>}}

In the **Username** input field, type `oneadmin`. For **Password**, enter the password provided by miniONE at the end of the report (in this example, `ZMCoOWUsBg`) then press `Enter` or click **SIGN IN NOW**.

The screen will display the Sunstone Dashboard:

{{< image
  pathDark="/images/quickstart/dark/sunstone_dashboard.png"
  path="/images/quickstart/light/sunstone_dashboard.png"
  alt="Sunstone dashboard" align="center" width="90%" mb="20px"
>}}

As you can see, the Dashboard indicates the following installed components:

- 1 VM template
- 1 image
- 1 Virtual Network

The existing Virtual Network is a bridged network attached to a local interface named `vnet`. To inspect this network, in Sunstone open the left-hand menu (hover the mouse over the left-hand sidebar), then click **Networks** --> **Virtual Networks**:

{{< image
  pathDark="/images/quickstart/dark/sunstone_select_vnetwork.png"
  path="/images/quickstart/light/sunstone_select_vnetwork.png"
  alt="Sunstone select vnet" align="center" width="90%" mb="20px"
>}}


Sunstone will display the **Virtual networks** screen. Click the item labelled `vnet` to display information about this network:

{{< image
  pathDark="/images/quickstart/dark/sunstone_network_details.png"
  path="/images/quickstart/light/sunstone_network_details.png"
  alt="Sunstone vnet screen" align="center" width="90%" mb="20px"
>}}

During installation, a KVM virtualization Host was automatically configured on the local machine. To inspect the KVM Host, in Sunstone open the left-hand menu, then click **Infrastructure** -> **Hosts**.

## Step 6: Deploying a Virtual Machine on the AWS instance

miniONE automatically downloaded the template for a VM with Alpine Linux 3.20 preinstalled. Through the Sunstone UI, we can now instantiate this VM on the local KVM Host with a few clicks.

To deploy the Alpine Linux VM, in the left-hand sidebar go to **Templates** -> **VM Templates**. This screen displays a list of all VM templates installed on the system. In this case, only the **Alpine Linux 3.20** template is installed:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_templates_alpine.png"
  path="/images/quickstart/light/sunstone_vm_templates_alpine.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

To instantiate the VM template, click the template item and click the **Instantiate** icon <svg width="1.5em" height="1.5em" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <circle cx="12" cy="12" r="12" fill="rgba(218, 218, 218, 1)" />
  <path d="M9 7.5v9l7-4.5-7-4.5z" stroke="rgb(143,147,146)" />
</svg> at the top.

Sunstone will display the first screen of the **Instantiate VM Template** wizard:

{{< image
  pathDark="/images/quickstart/dark/sunstone_instantiate_vm_1.png"
  path="/images/quickstart/light/sunstone_instantiate_vm_1.png"
  alt="Sunstone instantiate VM 1" align="center" width="90%" mb="20px"
>}}

Leave the **Capacity**, **Ownership** and **VM Group** parameters with their default values. Click **Next**.

The next screen allows you to see and modify further parameters for the VM, including selecting the Virtual Network or scheduling actions.

{{< image
  pathDark="/images/quickstart/dark/sunstone_instantiate_vm_2.png"
  path="/images/quickstart/light/sunstone_instantiate_vm_2.png"
  alt="Sunstone instantiate VM 2" align="center" width="90%" mb="20px"
>}}

Click **Finish**.

OpenNebula will instantiate the VM template. For the Alpine Linux VM, this should take just a few seconds. Once instantiation is complete, Sunstone should display the **Instances** -> **VMs** screen, with the Alpine Linux VM as the sole instance:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instances.png"
  path="/images/quickstart/light/sunstone_vm_instances.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

The green dot to the left of the VM name indicates that the VM is running. Note that you may need to click the **Refresh** icon <svg width="1.5em" height="1.5em" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="rgb(0,112,153)">
<circle cx="12" cy="12" r="11" fill="rgba(218, 218, 218, 1)" stroke="rgb(0,112,153)"/>
<g transform="translate(6, 6) scale(0.5)">
<path d="M21.168 8A10.003 10.003 0 0012 2C6.815 2 2.55 5.947 2.05 11" stroke="rgb(0,112,153)" stroke-linecap="round" stroke-linejoin="round"></path><path d="M17 8h4.4a.6.6 0 00.6-.6V3M2.881 16c1.544 3.532 5.068 6 9.168 6 5.186 0 9.45-3.947 9.951-9" stroke="rgb(0,112,153)" stroke-linecap="round" stroke-linejoin="round"></path>
<path d="M7.05 16h-4.4a.6.6 0 00-.6.6V21" stroke="rgb(0,112,153)" stroke-linecap="round" stroke-linejoin="round"></path>
<g>
</svg> at top left for the VM to display the running state.

### Logging into the Virtual Machine

The quickest way to login to the VM is by VNC, available directly in Sunstone. Just click the VNC icon <svg width="1.5em" height="1.5em" stroke-width="1.5" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg" color="rgb(143,147,146)"><path d="M2 15.5V2.6a.6.6 0 01.6-.6h18.8a.6.6 0 01.6.6v12.9m-20 0v1.9a.6.6 0 00.6.6h18.8a.6.6 0 00.6-.6v-1.9m-20 0h20M9 22h1.5m0 0v-4m0 4h3m0 0H15m-1.5 0v-4" stroke="rgb(143,147,146)" stroke-linecap="round" stroke-linejoin="round" fill="white" ></path></svg> and Sunstone will display the VM boot messages screen directly in your browser in another tab. 

{{< image
  pathDark="/images/quickstart/dark/sunstone_vnc_alpine.png"
  path="/images/quickstart/light/sunstone_vnc_alpine.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

Login as root with password `opennebula`. You can then use the command line to explore the VM and run processes:

* Try running `ping 1.1.1.1` to test the internet connection
* Try running `top` to see the processes running on the machine 

Congratulations! You've now installed an OpenNebula Front-end on an AWS instance with a KVM hypervisor and Virtual Network, then deployed a VM.

{{< alert title="Tip" type="primary" >}}Please note that miniONE is an evaluation version of OpenNebula and is intended for experimentation and learning. You should not use miniONE for a production cloud deployment. Please refer to the [Production Installation Guide](/software/installation_process.md) for details on deploying in a production environment.{{< /alert >}} 

## Next Steps

Now that you have a working miniONE OpenNebula installation, we suggest that you explore OpenNebula's functionality further with the following guides:

* [Deploy a WordPress Virtual Machine]({{% relref "/getting_started/try_opennebula/opennebula_sandbox_deployment/validate_the_environment.md#downloading-and-deploying-a-virtual-machine" %}})
* [Deploy a Kubernetes Cluster using Rancher and the Cluster API]({{% relref "/getting_started/try_opennebula/try_kubernetes_on_opennebula/managing_k8s_with_rancher" %}})
* [Further validate your miniONE installation]({{% relref "/getting_started/try_opennebula/opennebula_sandbox_deployment/validate_the_environment.md" %}}) and learn how to download appliances from the [OpenNebula Marketplace](https://marketplace.opennebula.io/)
