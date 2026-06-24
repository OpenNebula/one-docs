---
title: "Deploy OpenNebula On-prem with miniONE"
linkTitle: "Install miniONE On-prem"
date: "2025-02-17"
#description: "Install an OpenNebula Front-end and a KVM hypervisor on a single server in a few minutes, using **miniONE**, the installation script provided by OpenNebula."
categories: [Introduction, Evaluation, Learning]
pageintoc: "15"
tags: [miniONE]
type: docs
weight: "1"
---

<a id="create-an-emulated-environment-with-minione"></a>

<!--# Create an Emulated Environment with miniONE -->

In this tutorial, we will install an OpenNebula Front-end in under ten minutes, using the **miniONE** installation tool provided by OpenNebula.

miniONE is a straightforward tool for deploying an evaluation version of OpenNebula. After running the miniONE script, all the OpenNebula services needed to use, manage and run a small cloud deployment will be installed on a single server.

This tutorial covers installation of a Front-end and KVM hypervisor node on a local machine with a screen attached. If you are installing miniONE on remote infrastructure you may need to use SSH and port forwarding to access user interfaces in your local browser, please refer to the [port forwarding instructions](#ssh-and-port-forwarding) before continuing.

During this tutorial we will complete the following steps:

1. Ensure that the Host server meets the installation requirements.
2. Download and run the miniONE installation script.
3. Verify the installation.
4. Instantiate a Virtual Machine (VM) with Alpine Linux.

Once you have completed this tutorial, you will have an evaluation version of OpenNebula installed on your machine and you will understand how to use the [Sunstone User Interface]({{% relref fireedge_sunstone %}}) to instantiate a VM.  

## Before Starting

It is recommended to perform the installation on a machine capable of running KVM virtualization. If KVM virtualization is not available, miniONE will automatically fall back on QEMU emulation; however, running in full emulation mode will decrease performance.

To quickly check that your machine is capable of KVM emulation, run the `kvm-ok` command:
```
kvm-ok
INFO: /dev/kvm exists
KVM acceleration can be used
```
On Debian-based Linux, install `kvm-ok` by installing the `cpu-checker` package:

```bash
sudo apt install cpu-checker
```

## Step 1: Verify Installation Requirements

To run the miniONE script, you will need a physical server with a fresh installation of a supported operating system, with the latest software updates and without any customizations. The server will need a stable internet connection to download software packages during installation. 

**Supported operating systems:**
: - RHEL/AlmaLinux 9 or 10
  - Debian 12 or 13
  - Ubuntu 22.04 or 24.04
  - openSUSE 16.0, SLES 15.7

**Minimum hardware:**
: - 32 GiB RAM
  - 80 GiB free disk space

**Configuration:**
: - Access to the privileged user (root) account
  - An SSH server running on port 22
  - Open ports:
    : - 22 (SSH)
      - 80 (for the web UI)

This tutorial was tested on on Ubuntu 22.04 and 24.04. We strongly advise to use a physical server rather than a Virtual Machine (VM). If you choose to follow this installation on a VM you may experience instability due to nested virtualization during the follow-up [Kubernetes Installation Guides]({{% relref try_kubernetes_on_opennebula %}}). You may also need to use [port forwarding](#ssh-and-port-forwarding) to access the Sunstone UI.

## Step 2: Download and Install miniONE

Open a terminal and switch to the root user with the `sudo` command:

```bash
sudo -i
```

Download miniONE, run:

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

Make the `minione` script executable:

```bash
chmod +x minione
```

Now run the installation script:

```bash
./minione
```

{{< alert title="Tip" type="primary" >}} miniONE will create credentials with a randomized password for logging into the Sunstone UI. You can use the `--password` option to enter a secure and memorable password of your own: `./minione --password <password>`{{< /alert >}} 

The miniONE script executes the installation while logging output to the terminal. Installation usually takes between one and three minutes on most machines. Once finished, miniONE displays a report in the terminal with connection parameters and login credentials:

```default
### Report
OpenNebula 7.0 was installed
Sunstone is running on:
  http://192.168.1.130/
Use following to login:
  user: oneadmin
  password: ZMCoOWUsBg
```

Please take a note of the IP address and login credentials, you will need them later.

Finally update the ``localhost`` status:

```bash
sudo -u oneadmin onehost sync --force
```

This command might take 2-3 minutes to complete, check the status of the `localhost` periodically with `sudo -u oneadmin onehost list` until the `STAT` column of the `localhost` item reads `on`.

At this point, you have successfully installed miniONE. OpenNebula services should be running, and the system is ready for your first login.

## Step 3: Verify the Installation

Now verify the installation by logging in to OpenNebula's Sunstone UI.

Point your browser to the Edge IP and port provided by the miniONE report, in this case `192.168.1.130`, or simply to `http://localhost`. You should be greeted with the Sunstone login screen:

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

Sunstone will display the **Virtual Networks** screen. Click the item labelled `vnet` to display information about this network:

{{< image
  pathDark="/images/quickstart/dark/sunstone_network_details.png"
  path="/images/quickstart/light/sunstone_network_details.png"
  alt="Sunstone vnet screen" align="center" width="90%" mb="20px"
>}}

During installation, a KVM virtualization Host was automatically configured on the local machine. To inspect the KVM host, in Sunstone open the left-hand menu, then click **Infrastructure** -> **Hosts**.

## Step 4: Deploying a Virtual Machine Locally

miniONE automatically downloaded the template for a VM with Alpine Linux 3.20 preinstalled. Through the Sunstone UI, we can now instantiate this VM on the local KVM Host with a few clicks.

To deploy the Alpine Linux VM, in the left-hand sidebar go to **Templates** -> **VM Templates**. This screen displays a list of all VM templates installed on the system. In this case, only the **Alpine Linux 3.20** template is installed:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_templates_alpine.png"
  path="/images/quickstart/light/sunstone_vm_templates_alpine.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

To instantiate the VM template, click the template item and click the **Instantiate** icon <svg width="1.5em" height="1.5em" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;"><circle cx="12" cy="12" r="12" fill="rgba(218, 218, 218, 1)" /><path d="M9 7.5v9l7-4.5-7-4.5z" stroke="rgb(143,147,146)" /></svg> at the top.

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

The quickest way to log into the VM is by VNC, available directly in Sunstone. Just click the VNC icon <svg width="1.5em" height="1.5em" stroke-width="1.5" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg" color="rgb(143,147,146)"><path d="M2 15.5V2.6a.6.6 0 01.6-.6h18.8a.6.6 0 01.6.6v12.9m-20 0v1.9a.6.6 0 00.6.6h18.8a.6.6 0 00.6-.6v-1.9m-20 0h20M9 22h1.5m0 0v-4m0 4h3m0 0H15m-1.5 0v-4" stroke="rgb(143,147,146)" stroke-linecap="round" stroke-linejoin="round" fill="white" ></path></svg> and Sunstone will display the VM boot messages screen directly in your browser in another tab. 

{{< image
  pathDark="/images/quickstart/dark/sunstone_vnc_alpine.png"
  path="/images/quickstart/light/sunstone_vnc_alpine.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

Log in as `root` with password `opennebula`. You can then use the command line to explore the VM and run processes:

* Try running `ping 1.1.1.1` to test the internet connection
* Try running `top` to see the processes running on the machine 

Congratulations! You've now installed an OpenNebula Front-end with a KVM hypervisor and Virtual Network, then deployed a VM.

{{< alert title="Tip" color="primary" >}}Please note that miniONE is an evaluation version of OpenNebula and is intended for experimentation and learning. You should not use miniONE for a production cloud deployment. Please refer to the [Production Installation Guide]({{% relref installation_process %}}) for details on deploying in a production environment.{{< /alert >}} 

## Next Steps

Now that you have a working miniONE OpenNebula installation, we suggest that you explore OpenNebula's functionality further with the following guides:

* [Deploy a WordPress Virtual Machine]({{% relref "/getting_started/try_opennebula/opennebula_sandbox_deployment/validate_the_environment.md#downloading-and-deploying-a-virtual-machine" %}})
* [Deploy a Kubernetes Cluster using Rancher and the Cluster API]({{% relref "/getting_started/try_opennebula/try_kubernetes_on_opennebula/managing_k8s_with_rancher" %}})
* [Further validate your miniONE Installation]({{% relref "/getting_started/try_opennebula/opennebula_sandbox_deployment/validate_the_environment.md" %}}) and learn how to download appliances from the [OpenNebula Marketplace](https://marketplace.opennebula.io/)

## SSH and Port Forwarding

If you are deploying miniONE on remote infrastructure (or a VM) it may be necessary to use SSH to tunnel into the remote server and access the command line. You also need to use port forwarding in order to access the Sunstone UI through your local browser. 

In order to access the Sunstone UI, you will need to set up port forwarding on your remote machine. Choose a port that is available on your local machine, you can check this by running the following command:

```bash
lsof -i :8443
```

In this example we are choosing port 8443. This command should give no output. Any output suggests another process is using that port, `Ctrl-C` and choose another.

Open a terminal in your local machine and run the following command, inserting your chosen port (8443 in this case, 80 is the port to access Sunstone, do not change it):

```bash
ssh -L 8443:localhost:80 <username>@<REMOTE_IP_ADDRESS>
```

This command will take you to the command line of the remote server and establish the port forwarding. You can use this command prompt to run commands on the remote server, including the installation steps detailed above.

Now to access the Sunstone UI (after the successful installation of miniONE) direct your browser to `localhost:8443`, where you will find the Sunstone UI.
