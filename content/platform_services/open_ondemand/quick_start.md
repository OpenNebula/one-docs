---
title: "Quick Start"
linkTitle: "Quick Start"
date: "2026-09-15"
description:
categories:
tags:
weight: "3"
type: docs
---

This quick-start guide uses the Sunstone Web UI to deploy an Open OnDemand Service with one portal, one storage VM and one worker, and to open a JupyterLab notebook on it. Before beginning, check the [Requirements]({{% relref "platform_services/open_ondemand/architecture/#requirements" %}}). You need OneFlow and OneGate enabled, and two Virtual Networks, one with Internet access and one reserved for the service.

Quick-start workflow:

* **Create the compute network**: a Virtual Network reserved for the service, next to one with Internet access that you already have.
* **Download the appliance**: import the image, the VM template and the service template from the Community Marketplace.
* **Instantiate the service**: select the two Virtual Networks and keep the default inputs.
* **Wait for the service**: the service reaches the `RUNNING` state in about four minutes.
* **Open the portal and launch a notebook**: sign in with the initial user and open JupyterLab on the worker VM.

## Before You Start

Every VM of the service has two network interfaces, one on each of the two Virtual Networks the wizard asks for:

* **Management network.** It reaches the Internet and the OneGate endpoint. The portal publishes its web interface on it, and the storage role downloads the software catalogue through it. Any network your VMs already use for Internet access works.
* **Compute network.** Only the VMs of the service live on it. NFS, the LDAP directory, the SSH connections that start sessions and the software cache run on it.

The compute network is separate for two reasons. The directory lookups cross it in the clear, and the workers accept session connections only from addresses on it, so nothing outside the service may live there. The portal also derives the worker address range from its own address on that network, the whole /24 around it, so create the network as a /24 or smaller. On a larger network, reserve a /24 slice of it for the workers and give it as `ONEAPP_POOL_RANGE`, described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/#advanced-attributes" %}}).

To create the compute network, go to **Networks -> Virtual Networks**, click **+ Create Virtual Network** and choose **From scratch**. In **General**, give it a name, `ood-compute` for instance, and select the Cluster of the Hosts that will run the service:

{{< image path="/images/open_ondemand/light/sunstone_vnet_general.png"
alt="Create Virtual Network wizard, General step" align="center" width="90%" mb="20px" >}}

Click **Next** to reach **Advanced options**. In the **Configuration** tab, choose the network mode of your installation. Any mode where the VMs reach each other works, because nothing outside the service uses the network. On a single Host, **Bridged** with **Custom name for bridge** enabled and a bridge name of your choice, `br1` for instance, is enough, and across several Hosts use the mode and physical device of your other private networks, VXLAN for instance:

{{< image path="/images/open_ondemand/light/sunstone_vnet_conf.png"
alt="Create Virtual Network wizard, Configuration tab" align="center" width="90%" mb="20px" >}}

Select the **Addresses** tab and click **+ Add Address Range**. Set the **First IPv4 address**, `172.22.0.50` for instance, and a **Size** that covers the portal, the storage role and the workers you expect and stays inside one /24. A size of 200 is plenty for the quick start. Click **Accept**, then **Finish**:

{{< image path="/images/open_ondemand/light/sunstone_vnet_addresses.png"
alt="Create Virtual Network wizard, Addresses tab" align="center" width="90%" mb="20px" >}}

From the Front-end command line, `onevnet create` creates the same network from a template file, see [Managing Virtual Networks]({{% relref "product/cluster_configuration/networking_system/manage_vnets/" %}}).

## Download the Appliance

Register the [Community Marketplace](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start) once if it is not in your installation. Then, from **Storage -> Apps**, download `Open OnDemand Service` into an image Datastore. The download imports three objects, the image the three roles share, the VM template that boots it and the service template `Open OnDemand Service`. From the Front-end command line:

```shell
onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

The image is about 1.5 GB, so wait until `oneimage list` shows it in the `rdy` state.

## Instantiate the Service

From **Templates -> Service Templates**, select `Open OnDemand Service` and click the **Instantiate** icon, the first one in the toolbar of the detail pane:

{{< image path="/images/open_ondemand/light/sunstone_service_templates.png"
alt="The Open OnDemand Service template in Sunstone" align="center" width="90%" mb="20px" >}}

The wizard has four steps. In **General**, keep the name and one instance:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_general.png"
alt="Instantiate wizard, General step" align="center" width="90%" mb="20px" >}}

In **Networks**, click each entry on the left and select its Virtual Network in the table. `Management` is the network with Internet access, where the portal publishes its web interface. `Compute` is the network you created in [Before You Start](#before-you-start):

{{< image path="/images/open_ondemand/light/sunstone_instantiate_networks.png"
alt="Instantiate wizard, Networks step" align="center" width="90%" mb="20px" >}}

In **Service Inputs**, nothing needs to change for a first start. Every input is optional, and the defaults give a portal with a self-signed certificate on its management address and one local user, `demo1` with password `demo1pass`. The home directories stay on the storage role and no Slurm cluster is attached. The inputs sit in four tabs, one per topic, and every optional feature is a switch that reveals its fields only when it is on. The **Portal** tab looks like this:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_inputs.png"
alt="Instantiate wizard, Service Inputs step, Portal tab" align="center" width="90%" mb="20px" >}}

The **Portal** tab holds the public name and the TLS certificate of the web portal:

| Option | What it does | For a first start |
|---|---|---|
| **Host name**, `ONEAPP_PORTAL_HOST_NAME` | The public name users open the portal at. Empty makes the portal answer on its management address. | Leave it empty. A name can be set on the running portal later, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/#service-inputs" %}}). |
| **Let's Encrypt**, `ONEAPP_PORTAL_LETSENCRYPT_ENABLED` | Requests a certificate for the host name when the portal boots. The name has to resolve to the portal, and ports 80 and 443 have to be reachable from the Internet. | Off. The portal starts with a self-signed certificate. |
| **Your own certificate**, `ONEAPP_PORTAL_CERTIFICATE_ENABLED` | Replaces the self-signed certificate with a PEM chain and a PEM key that you paste in the two boxes the switch reveals. | Off. |
{.w-100}

The **Users and login** tab decides who can sign in:

| Option | What it does | For a first start |
|---|---|---|
| **Local users**, `ONEAPP_AUTH_LOCAL_USERS` | The accounts the portal creates in its directory at first boot, as `user:password:uid` separated by spaces. | Keep `demo1:demo1pass:10001`, or list your own users. |
| **OpenID Connect**, `ONEAPP_AUTH_OIDC_ENABLED` | Adds an institutional login next to the local one, MyAccessID or Keycloak for instance. The switch reveals the issuer URL, the client id, the client secret and the name shown on the login page. | Off. |
{.w-100}

The **Home directories** tab decides where the files of the users live:

| Option | What it does | For a first start |
|---|---|---|
| **NFS server of your own**, `ONEAPP_HOME_NFS_ENABLED` | Mounts the home directories from an NFS server you already run instead of the storage role, which then only keeps the software cache. The switch reveals the address of the server and the export path. | Off. |
{.w-100}

The **Slurm** tab attaches a Slurm cluster for batch jobs:

| Option | What it does | For a first start |
|---|---|---|
| **Controller**, `ONEAPP_SLURM_CONTROLLER_ENABLED` | Submits batch jobs to a Slurm cluster that shares the users and the home, a OneSlurm service on the same compute network. The switch reveals the address of the controller. | Off. The cluster is attached to a running service, see [Batch Jobs with Slurm]({{% relref "platform_services/open_ondemand/configuration/#batch-jobs-with-slurm" %}}). |
{.w-100}

In **Charter**, leave the list empty and click **Finish**. From the Front-end command line, `oneflow-template instantiate 'Open OnDemand Service'` asks for the same values interactively.

## Wait for the Service

The roles start in order, `storage` first and `worker` last, and each one declares itself ready through OneGate only when it is serving. From **Instances -> Services**, the service moves from `DEPLOYING` to `RUNNING` in about four minutes:

{{< image path="/images/open_ondemand/light/sunstone_service_running.png"
alt="The Open OnDemand Service running in Sunstone" align="center" width="90%" mb="20px" >}}

Open the service and select the **Roles** tab to see the three roles, and tick a role to list its VMs:

{{< image path="/images/open_ondemand/light/sunstone_service_roles.png"
alt="The three roles of the running service" align="center" width="90%" mb="20px" >}}

A role that stays in `DEPLOYING` has not declared itself ready, see [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}).

## Open the Portal

The portal publishes its address as `OOD_URL` in the user template of the portal VM. In the **Roles** tab of the service, tick the `portal` role and click its VM in the table, then read it in the **Template** tab, under **User Template**, next to `READY`:

{{< image path="/images/open_ondemand/light/sunstone_portal_ood_url.png"
alt="The user template of the portal VM in Sunstone, with OOD_URL and READY" align="center" width="90%" mb="20px" >}}

The same value is available from the Front-end command line:

```shell
onevm show <portal vm id> | grep OOD_URL
```

```default
OOD_URL="https://192.168.100.165/"
```

It is `https://` followed by the management address of the portal VM, or by `ONEAPP_PORTAL_HOST_NAME` if you gave it a host name. With the default self-signed certificate the browser asks you to accept it. Sign in with the initial user, `demo1` with password `demo1pass` unless you changed `ONEAPP_AUTH_LOCAL_USERS`:

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The home directory is created on first login. The **Interactive Apps** menu lists the six interactive applications, and the dashboard pins five of them:

{{< image path="/images/open_ondemand/light/portal_dashboard.png"
alt="Open OnDemand dashboard" align="center" width="90%" mb="20px" >}}

## Launch a Notebook

From **Interactive Apps -> Jupyter Notebook**, choose the session length and click **Launch**:

{{< image path="/images/open_ondemand/light/jupyter_form.png"
alt="Jupyter launch form" align="center" width="90%" mb="20px" >}}

The session card under **My Interactive Sessions** shows the worker VM it landed on. The first session on a fresh deployment takes longer to start while the site cache fetches the Python module. When the card turns `Running`, click **Open the Jupyter notebook**:

{{< image path="/images/open_ondemand/light/session_card.png"
alt="Session card" align="center" width="90%" mb="20px" >}}

JupyterLab opens through the portal proxy, with the Python and Octave kernels from EESSI:

{{< image path="/images/open_ondemand/light/jupyterlab.png"
alt="JupyterLab running on a compute VM" align="center" width="90%" mb="20px" >}}

Files saved in the notebook go to the user's home directory on the storage role and appear in **Files -> Home Directory** and in every later session. Deleting the session from **My Interactive Sessions** ends it on the worker.

## Next Steps

* [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}): what was deployed and how a session runs.
* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}): host name and certificate, users, worker sizes, Slurm and external identity providers.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}): keeping the home directories across deployments, upgrading and removing the service.
