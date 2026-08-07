---
title: "Automated Front-end Installation with miniONE for Production"
linkTitle: "Front-end Installation with miniONE"
date: "2026-04-15"
description:
categories:
pageintoc: "26"
tags: [miniONE, deployment, installation, automatic]
weight: "1"
---

Automatic installation of an OpenNebula Front-end can be achieved using the miniONE rapid installation script. The miniONE installation script automatically configures the target server to deploy OpenNebula with the essential modules to run a cloud. After installing OpenNebula with miniONE, you will be able to deploy Virtual Machines, provision Clusters with on-premises or cloud resources and manage your cloud using the command line, the API or the Sunstone user interface.

This automated miniONE OpenNebula installation is recommended for most users to quickly bootstrap a production cloud deployment. However, if you require more fine-grained control over your installation or require advanced automation options, you may wish to consult the following documentation:

* [Manual Front-end deployment]({{% relref "software/installation_process/frontend_installation/" %}})
* [Advanced deployment with OneDeploy]({{% relref "getting_started/install_opennebula/one_deploy/one_deploy_overview/" %}})

miniONE establishes a network bridge as a convenience measure to simplify network connectivity within the newly installed OpenNebula cloud, enabling quick validation, learning, and testing. This configuration is generally inappropriate for expanding a cloud within a data center. The network configuration should be modified at a later stage to include relevant network interfaces and facilitate network connectivity within a data center. Refer to the [Networking System Guides]({{% relref "product/cluster_configuration/networking_system/" %}}) for details on network configuration. 

## Prerequisites

You may wish to install the miniONE OpenNebula Front-end on its own dedicated machine, which is only intended for management and not workload, in which case you should follow the guidelines for "Front-end only". You may also install the miniONE OpenNebula Front-end on the same machine you intend to use for compute workloads, in which case you should consider your intended use-case, guidance is given below for a small Kubernetes Cluster and an AI Factory. 

You may use on-premises hardware, virtual or bare-metal resources from a cloud provider to install miniONE. If you are intending to use the target machine only for the OpenNebula Front-end and not Cluster workloads, a Virtual Machine meeting the requirements given below would suffice. If you are intending to use the target machine for Cluster workloads, particularly Kubernetes workloads, it is highly recommended to use a bare-metal instance.

To install miniONE it is important to meet the following prerequisites for the machine on which you intend to install miniONE:

 **Supported operating systems**:
* RHEL/AlmaLinux 9 or 10
* Debian 12 or 13
* Ubuntu 24.04 or 26.04
* openSUSE 16.0, SLES 15.7
* See the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes.md" %}}) for further details on compatible operating systems

**Minimum hardware:**
* **Front-end only**:
  * 16 GiB RAM
  * 80 GiB free disk space
* **Kubernetes**:
  * 64 GiB RAM
  * 120 GiB free disk space
* **AI Factory**:
  * 128 GiB RAM
  * 512 GiB free disk space
  * NVIDIA L40S or H100 GPU

**Configuration:**
 - Access to the privileged user (root) account
  - An SSH server running on port 22
  - Open ports:
    - 22 (SSH)
    - 80 (for the Sunstone web UI)

## Installing miniONE

Log in to the machine on which you intend to install miniONE (or use SSH on remote hardware). Open a terminal and switch to the root user with the `sudo` command:

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
{{% if-version is="7.4" %}}
```bash
wget 'https://github.com/OpenNebula/minione/releases/download/v7.4.0/minione'
```
{{% /if-version %}}

Make the `minione` script executable:

```bash
chmod +x minione
```

Now run the installation script, choosing one of the following options as appropriate:

  * **Front-end only**:

    ```bash
    ./minione --frontend
    ```
  * **Front-end and single KVM node**:

    ```bash
    ./minione
    ```

  * **Front-end and single LXC node**:

    ```bash
    ./minione --lxc
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

Finally, if you have installed a local hypervisor node, update the `localhost` status:

```bash
sudo -u oneadmin onehost sync --force
```

This command might take 2-3 minutes to complete, check the status of the `localhost` periodically with `sudo -u oneadmin onehost list` until the `STAT` column of the `localhost` item reads `on`.

At this point, you have successfully installed miniONE. OpenNebula services should be running, and the system is ready for your first login.

## Verify the Installation

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

### Deploy a Virtual Machine Locally

{{< alert title="Note" type="primary" >}}Deploying a Virtual Machine locally will only work if you chose to install a KVM node on the same Host as the Front-end. If you chose to only install the Front-end, or an LXC node, you will first need to [deploy a Cluster with OneForm]({{% relref "getting_started/install_opennebula/production/cluster_oneform/" %}}).{{< /alert >}} 

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

#### Log in to the Virtual Machine

The quickest way to log into the VM is by VNC, available directly in Sunstone. Just click the VNC icon <svg width="1.5em" height="1.5em" stroke-width="1.5" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg" color="rgb(143,147,146)"><path d="M2 15.5V2.6a.6.6 0 01.6-.6h18.8a.6.6 0 01.6.6v12.9m-20 0v1.9a.6.6 0 00.6.6h18.8a.6.6 0 00.6-.6v-1.9m-20 0h20M9 22h1.5m0 0v-4m0 4h3m0 0H15m-1.5 0v-4" stroke="rgb(143,147,146)" stroke-linecap="round" stroke-linejoin="round" fill="white" ></path></svg> and Sunstone will display the VM boot messages screen directly in your browser in another tab. 

{{< image
  pathDark="/images/quickstart/dark/sunstone_vnc_alpine.png"
  path="/images/quickstart/light/sunstone_vnc_alpine.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

Log in as `root` with password `opennebula`. You can then use the command line to explore the VM and run processes:

* Try running `ping 1.1.1.1` to test the internet connection
* Try running `top` to see the processes running on the machine 

If the above procedure works, you have successfully installed miniONE and it is ready to deploy and manage your cloud infrastructure.

## Next Steps

After completing the miniONE installation process and validation, you can proceed to deploy Clusters automatically or manually:

* [Automatically deploy Clusters with OneForm]({{% relref "/getting_started/install_opennebula/production/cluster_oneform" %}})
* Manually install Cluster nodes with [KVM]({{% relref "software/installation_process/cluster_installation/kvm_node_installation/" %}}) or [LXC]({{% relref "software/installation_process/cluster_installation/lxc_node_installation/" %}})
* Try deploying Kubernetes Clusters with the [OneKS Kubernetes Guides]({{% relref "platform_services/oneks/" %}})
* [Modify your network configuration to facilitate connectivity with other hardware]({{% relref "product/cluster_configuration/networking_system/" %}})





