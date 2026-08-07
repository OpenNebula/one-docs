---
title: "Validate the Production Deployment"
linkTitle: "Validate the Production Deployment"
date: "2025-02-17"
#description: "Explore the resources deployed with **miniONE** or the **ISO**, and download and install appliances from the **OpenNebula Marketplace**"
categories: [Learning, Evaluation, Introduction, Deployment]
pageintoc: "24"
tags: ['Quick Start', 'Edge Cluster']
type: docs
weight: "3"
---

The previous guides in this section detail how to deploy an [OpenNebula Front-end automatically with miniONE]({{% relref "/getting_started/install_opennebula/production/minione_frontend_install" %}}) and deploy [OpenNebula Clusters automatically with OneForm]({{% relref "/getting_started/install_opennebula/production/cluster_oneform" %}}). Follow this guide to validate that the expected resources are installed and functional.

## Installed Resources

After following the instructions for [installing an OpenNebula Front-end automatically with miniONE]({{% relref "/getting_started/install_opennebula/production/minione_frontend_install" %}}), the following resources are already created and configured:

- Datastores for storing files and Virtual Machine images

The following resources are installed if the default miniONE installation is chosen (i.e. `--frontend` or `--lxc` options are not used):

- A KVM Host on the local machine
- A virtualization Cluster to which the Host belongs
- A Virtual Network for the Virtual Machines

Below you will find brief descriptions for these resources, with examples of their visual representation in the Sunstone UI and links to complete references for each resource.

### Hosts

A Host is any entity that is capable of running a VM or a container. Besides running them, it retrieves all monitoring information. A Host has two important attributes:

* `VM_MAD`: The virtualization technology used on the Host.
* `IM_MAD`: The driver that retrieves all monitoring metrics from the Host.

As mentioned above, miniONE installs a KVM Host and following the ISO deployment the KVM Host is added in `onefemenu`.

The screenshot below displays the information about the Host. The important information here is:

* The **State** of the Host: **MONITORED** indicates that the Host is currently being monitored.
* The **Attributes** section displays the monitoring metrics.
* The tabs to the right of the **Info** tab display additional information, such as the VMs running on the Host.

{{< image
  pathDark="/images/quickstart/dark/minione_kvm_host.png"
  path="/images/quickstart/light/minione_kvm_host.png"
  alt="Sunstone KVM Host" align="center" width="90%" mb="20px"
>}}

The basic operations you can perform on the Host are:

* **Offline**: Take the Host totally offline.
* **Disable**: Disable the Host, for example to perform maintenance operations.
* **Enable**: Enable the Host, so that OpenNebula monitors it and it switches back to MONITORED state.

For a complete overview of Hosts management, see [Hosts]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts#hosts" %}}).

### Cluster

A Cluster is the main object that groups all the physical resources and ensures that everything works correctly in terms of scheduling and the resources required. In this very simple scenario the Cluster includes only the local KVM Host, the Virtual Network, and datastores.

{{< image
  pathDark="/images/quickstart/dark/minione_cluster.png"
  path="/images/quickstart/light/minione_cluster.png"
  alt="Sunstone Clusters" align="center" width="90%" mb="20px"
>}}

For a complete overview of Cluster management, see [Clusters]({{% relref "product/cluster_configuration/hosts_and_clusters/cluster_guide#cluster-guide" %}}).

### Datastores

There are three types of datastores:

* **System**: Contains the information of running VMs, such as disks or context CD-ROM.
* **Image**: Stores the images in your cloud.
* **Files**: Stores plain files used in contextualization or VM kernels used by some hypervisors.

In the on-prem Cluster the `default` datastore is the Image datastore.

{{< image
  pathDark="/images/quickstart/dark/minione_datastores.png"
  path="/images/quickstart/light/minione_datastores.png"
  alt="Sunstone Datastores" align="center" width="90%" mb="20px"
>}}

For a complete overview of Datastore management, see [Datastores]({{% relref "product/cluster_configuration/storage_system/datastores#datastores" %}}).

### Virtual Networks

A Virtual Network in OpenNebula basically resembles the physical network in the data center. Virtual Networks allow VMs to have connectivity between them and with the rest of the world. The default miniONE installation creates a private network, by default called `vnet` with a base address of 172.16.100.1, with access to public networks via NAT. In the ISO deployment, this network is created manually and the gateway and the NAT must be configured.

{{< image
  pathDark="/images/quickstart/dark/minione_vnet.png"
  path="/images/quickstart/light/minione_vnet.png"
  alt="Sunstone Virtual Networks" align="center" width="90%" mb="20px"
>}}

<a id="edge-private"></a>

For a complete overview, see [Virtual Network Templates]({{% relref "product/virtual_machines_operation/virtual_machines_networking/vn_templates#vn-templates" %}}).

## Downloading and Deploying a Virtual Machine

{{< alert title="Important" type="info" >}}
If you have used the default miniONE installation that deploys a KVM node, you can try deploying a Virtual Machine to validate your OpenNebula cloud is functioning correctly. If you chose to only install the Front-end or install an LXC node, you will need to adjust the following instructions accordingly.{{< /alert >}}

We’ll follow these high-level steps:

1. Download the WordPress appliance from the OpenNebula Marketplace.
2. Instantiate the Virtual Machine for the appliance.
3. Verify the Installation by Connecting to WordPress.

### Step 1. Download the WordPress Appliance from the OpenNebula Marketplace

The [OpenNebula Public Marketplace](https://marketplace.opennebula.io) is a repository of Virtual Machines and appliances which are curated, tested, and certified by OpenNebula.

To access the Marketplace, first log in to Sunstone on your OpenNebula Front-end, as user `oneadmin`.

Open the left-hand pane (by hovering the mouse over the icons on the left), then select **Storage**, then **Apps**:

{{< image
  pathDark="/images/quickstart/dark/sunstone_select_apps.png"
  path="/images/quickstart/light/sunstone_select_apps.png"
  alt="Sunstone Apps" align="center" width="60%" mb="20px"
>}}

Sunstone will display the **Apps** screen, showing the first page of apps that are available for download:

{{< image
  pathDark="/images/quickstart/dark/sunstone_apps_list.png"
  path="/images/quickstart/light/sunstone_apps_list.png"
  alt="Sunstone Apps List" align="center" width="90%" mb="20px"
>}}

Search for the app called **Service WordPress - KVM**. If it’s not on the list, type `wordpress` in the search field at the top to filter by name:

{{< image
  pathDark="/images/quickstart/dark/sunstone_apps_wordpress.png"
  path="/images/quickstart/light/sunstone_apps_wordpress.png"
  alt="Sunstone Apps Wordpress" align="center" width="90%" mb="20px"
>}}

Click **Service WordPress - KVM** to select it, then click the **Import into Datastore** ![icon1](/images/icons/sunstone/import_into_datastore.png) icon:

{{< image
  pathDark="/images/quickstart/dark/sunstone_import_wordpress.png"
  path="/images/quickstart/light/sunstone_import_wordpress.png"
  alt="Sunstone Import Wordpress" align="center" width="90%" mb="20px"
>}}

Sunstone will display the **Download App to OpenNebula** dialog:

{{< image
  pathDark="/images/quickstart/dark/sunstone_download_app.png"
  path="/images/quickstart/light/sunstone_download_app.png"
  alt="Sunstone Download Wordpress App" align="center" width="90%" mb="20px"
>}}

Click **Next**. The next screen prompts us to select a datastore, which in this case is the `default` Image datastore installed locally:

{{< image
  pathDark="/images/quickstart/dark/minione_import_to_datastore.png"
  path="/images/quickstart/light/minione_import_to_datastore.png"
  alt="Sunstone Download Wordpress App" align="center" width="90%" mb="20px"
>}}

Click **Finish**. Sunstone will download the appliance template and display basic information for the appliance, shown below in the **Info** tab:

{{< image
  pathDark="/images/quickstart/dark/wordpress_imported.png"
  path="/images/quickstart/light/wordpress_imported.png"
  alt="Sunstone Imported Wordpress App" align="center" width="90%" mb="20px"
>}}

Wait for the appliance **State** to indicate **READY**. When it does, the VM will be ready to be instantiated.

### Step 2. Instantiate the VM

The Wordpress appliance VM was imported as a Virtual Machine template. To instantiate, follow these steps:

In the left-hand pane click **Templates**, then **VM Templates**:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_templates.png"
  path="/images/quickstart/light/sunstone_vm_templates.png"
  alt="Sunstone VM Templates" align="center" width="90%" mb="20px"
>}}

Select **Service WordPress - KVM**, then click the **Instantiate** ![icon2](/images/icons/sunstone/instantiate.png) icon at the top:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instantiate.png"
  path="/images/quickstart/light/sunstone_vm_instantiate.png"
  alt="Sunstone VM Instantiate" align="center" width="90%" mb="20px"
>}}

Sunstone will display the first screen of the **Instantiate VM Template** wizard:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instantiate_wiz1.png"
  path="/images/quickstart/light/sunstone_vm_instantiate_wiz1.png"
  alt="Sunstone VM Instantiate Wizard 1" align="center" width="90%" mb="20px"
>}}

Feel free to modify the VM’s capacity according to your requirements, or leave the default values.

Click **Next**. Sunstone displays the **User Inputs** screen, where you can modify parameters such as the security credentials for the site administrator, or SSL certificates:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instantiate_wiz2.png"
  path="/images/quickstart/light/sunstone_vm_instantiate_wiz2.png"
  alt="Sunstone VM Instantiate Wizard 2" align="center" width="90%" mb="20px"
>}}

Click **Next**. Sunstone displays the last screen of the wizard, **Advanced Options**:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instantiate_wiz3.png"
  path="/images/quickstart/light/sunstone_vm_instantiate_wiz3.png"
  alt="Sunstone VM Instantiate Wizard 3" align="center" width="90%" mb="20px"
>}}

In this screen we need to specify what network the VM will connect to. Select the **Network** tab, then click the **Attach NIC** button:

{{< image
  pathDark="/images/quickstart/dark/sunstone_vm_instantiate_wiz4.png"
  path="/images/quickstart/light/sunstone_vm_instantiate_wiz4.png"
  alt="Sunstone VM Instantiate Wizard 4" align="center" width="90%" mb="20px"
>}}

Sunstone will display a wizard with network parameters:

{{< image
  pathDark="/images/quickstart/dark/minione_attach_nic_1.png"
  path="/images/quickstart/light/minione_attach_nic_1.png"
  alt="Sunstone Attach NIC 1" align="center" width="90%" mb="20px"
>}}

Click **Next**. Sunstone displays the **Select a network** screen:

{{< image
  pathDark="/images/quickstart/dark/minione_attach_nic_2.png"
  path="/images/quickstart/light/minione_attach_nic_2.png"
  alt="Sunstone Attach NIC 2" align="center" width="90%" mb="20px"
>}}

Click **Next**. Sunstone displays the **Network values** screen:

{{< image
  pathDark="/images/quickstart/dark/minione_attach_nic_3.png"
  path="/images/quickstart/light/minione_attach_nic_3.png"
  alt="Sunstone Attach NIC 3" align="center" width="90%" mb="20px"
>}}


Select `vnet`, then click **Next**. Sunstone displays the final screen, **Select QoS**:

{{< image
  pathDark="/images/quickstart/dark/minione_select_qos.png"
  path="/images/quickstart/light/minione_select_qos.png"
  alt="Sunstone Attach NIC 4" align="center" width="90%" mb="20px"
>}}

To instantiate the VM, click **Finish**. Sunstone will take you to the last screen of the **Instantiate VM Template** wizard. To deploy the VM, click **Finish**.

Sunstone will deploy the VM to KVM Host and display the **VMs** screen with the status of the VM. When the VM is running — as indicated by the green dot — it will be ready for your first login.

The image below shows the newly instantiated WordPress VM and the Alpine VM that was bundled by default with miniONE:

{{< image
  pathDark="/images/quickstart/dark/minione_vm_wordpress.png"
  path="/images/quickstart/light/minione_vm_wordpress.png"
  alt="Word " align="center" width="90%" mb="20px"
>}}

As you can see in the image above, its IP address is 172.16.100.3. Note: This IP will only be reachable from localhost, bridged networks, or another instance in the same VNet.  

### Step 3. Connect to WordPress

To log into WordPress, simply enter the IP address in your browser and you’ll be greeted by the famous five-minute WordPress installation process.

{{< image path="/images/quickstart/light/wordpress_install_page.png"
  alt="Sunstone Attach NIC 4" align="center" width="60%" mb="20px"
>}}

That’s it — you have a working OpenNebula cloud with a WordPress up and running. Congratulations!
