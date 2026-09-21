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

This guide demonstrates the deployment of an Open OnDemand Service through the Sunstone Web UI, with one portal, one storage VM and one worker, exposing a JupyterLab notebook to a user through the service. Check the [Requirements]({{% relref "solutions/integration_blueprints/open_ondemand/architecture/#requirements" %}}) before beginning this guide. You will need OneFlow and OneGate enabled, along with two Virtual Networks, one with Internet access and one reserved for the service.

Quick-start workflow:

* **Create the Networks**: Create a management network with Internet access (or choose an existing one), and a compute network reserved for the service.
* **Download the Appliance**: Import the image, the VM template and the service template from the Community Marketplace.
* **Instantiate the Service**: Select the two Virtual Networks and keep the default inputs.
* **Wait for the Service**: It reaches the `RUNNING` state within about four minutes.
* **Open the Portal and Launch a Notebook**: Sign in with the initial user and open JupyterLab as a Slurm job on the worker VM.

## Before You Start

The service requires two Virtual Networks. The service wizard requests both of the following networks during instantiation:

* **Management Network**: The network your VMs already use to reach the Internet. The portal publishes its web interface on it, and OneGate must be reachable from it.
* **Compute Network**: A private network for intercommunication among the VMs of this service and nothing else. It carries the shared home directory, the user directory, the software cache and the Slurm traffic between the portal and the workers.

Keep the compute network private and small, a `/24` subnet or smaller. Its traffic is not encrypted. The workers join the Slurm Cluster through it and the portal treats every address of that `/24` subnet as a possible worker. A larger network needs `ONEAPP_POOL_RANGE`, described in [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#advanced-attributes" %}}).

Create both networks from the **Networks -> Virtual Networks** view with **+ Create Virtual Network** and select **From scratch**. Most installations already have a management network, so skip the first one if yours does. From the Front-end command line, `onevnet create` creates the same networks from a template file. See [Managing Virtual Networks]({{% relref "product/cluster_configuration/networking_system/manage_vnets/" %}}).

## Step 1: Create the Networks

### Create the Management Network

Your cloud may already have a public network suitable for the management network, if this is the case, skip the following steps and proceed to [Create the Compute Network](#create-the-compute-network)

1. **General**: Give it a name, for example `ood-management`. Select the Cluster of the Hosts that will run the service. Click **Next**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_general.png"
alt="Create Virtual Network wizard, General step of the management network" align="center" width="90%" mb="20px" >}}

2. **Configuration**: Choose the network mode of your Hosts. On a single Host, select **Bridged** and **Custom name for bridge**. Enter the name of the bridge that reaches the Internet, for instance `br0`.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_conf.png"
alt="Create Virtual Network wizard, Configuration tab of the management network" align="center" width="90%" mb="20px" >}}

3. **Addresses**: Click **+ Add Address Range**. Set the first free address of the network and the number of addresses, for instance `192.168.100.50` and `200`. Click **Accept**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_addresses.png"
alt="Create Virtual Network wizard, Addresses tab of the management network" align="center" width="90%" mb="20px" >}}

4. **Context**: Set the network address, the network mask, the gateway and the DNS server, so the VMs reach the Internet. Use for instance `192.168.100.0`, `255.255.255.0`, `192.168.100.1` and `1.1.1.1`. Click **Finish**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_context.png"
alt="Create Virtual Network wizard, Context tab of the management network" align="center" width="90%" mb="20px" >}}

### Create the Compute Network

1. **General**: Give it a name, for instance `ood-compute`, and select the same Cluster. Click **Next**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_general.png"
alt="Create Virtual Network wizard, General step of the compute network" align="center" width="90%" mb="20px" >}}

2. **Configuration**: Any mode where the VMs of the Cluster reach each other works. On a single Host, select **Bridged** and **Custom name for bridge**. Enter a new bridge name, for instance `br1`. Across several Hosts, use the mode and physical device of your other private networks, for instance VXLAN.

{{< image path="/images/open_ondemand/light/sunstone_vnet_conf.png"
alt="Create Virtual Network wizard, Configuration tab of the compute network" align="center" width="90%" mb="20px" >}}

3. **Addresses**: Click **+ Add Address Range**. Set a first address and a size inside one `/24` subnet, for instance `172.22.0.50` and `200`. Click **Accept**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_addresses.png"
alt="Create Virtual Network wizard, Addresses tab of the compute network" align="center" width="90%" mb="20px" >}}

4. **Context**: Leave it empty. This network has no gateway, because its traffic never leaves the Hosts. Click **Finish**.

## Step 2. Download the Appliance

Register the [Community Marketplace](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start) once if your installation does not already have it. Then, from **Storage -> Apps**, search for and download `Open OnDemand Service` into an available image datastore with sufficient space. The download imports three objects: image that the three roles share, the VM template that boots that image, and the service template `Open OnDemand Service`. Alternatively, you can register the marketplace from the Front-end command line using the following command:

```shell
onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

The image is about 1.6 GB, so wait until `oneimage list` reports the image in the `rdy` state.

## Step 3. Instantiate the Service

From **Templates -> Service Templates**, select `Open OnDemand Service`. Click the **Instantiate** icon (the play button icon).

{{< image path="/images/open_ondemand/light/sunstone_service_templates.png"
alt="The Open OnDemand Service template in Sunstone" align="center" width="90%" mb="20px" >}}

The wizard has four steps. In **General**, keep the name and one instance.

{{< image path="/images/open_ondemand/light/sunstone_instantiate_general.png"
alt="Instantiate wizard, General step" align="center" width="90%" mb="20px" >}}

In **Networks**, click the **Management** entry on the left and select its relevant Virtual Network in the table. The Management Network is the network with Internet access described [earlier](#before-you-start), where the portal publishes its web interface. Then click the **Compute** entry and select the Compute Network you created [earlier](#create-the-compute-network).

{{< image path="/images/open_ondemand/light/sunstone_instantiate_networks.png"
alt="Instantiate wizard, Networks step" align="center" width="90%" mb="20px" >}}

In **Service Inputs**, nothing needs to change for this quick-start guide. Every input is optional. The default values give a portal with a self-signed certificate on its management address, and one local user with username `demo1` and password `demo1pass`. The home directories and the software cache stay on the storage role, and the Slurm Cluster of the service needs no input. The inputs sit in four tabs, one per topic. Each section has a help icon with its explanation. Every optional feature is a switch that shows its fields only when it is on. The **Portal** tab looks like this:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_inputs.png"
alt="Instantiate wizard, Service Inputs step, Portal tab" align="center" width="90%" mb="20px" >}}

The **Portal** tab holds the public name and the TLS certificate of the web portal. For this guide, leave the name empty and both toggles off:

| **Option** | **What it does** |
|---|---|
| **Host name**<br>`ONEAPP_PORTAL_HOST_NAME` | The public name at which users open the portal. If empty, the portal answers on its management address. You can set the name of an already running portal later, see [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#service-inputs" %}}). |
| **Let's Encrypt**<br>`ONEAPP_PORTAL_LETSENCRYPT_ENABLED` | Requests a certificate for the Host name when the portal boots. The name must resolve to the portal, and ports 80 and 443 must be reachable from the Internet. When off, the portal starts with a self-signed certificate. |
| **Your own certificate**<br>`ONEAPP_PORTAL_CERTIFICATE_ENABLED` | Replaces the self-signed certificate with a PEM chain and a PEM key. Paste them into the two boxes revealed when this option is chosen. |
{.w-100}

The **Users and login** tab decides who can sign in. For this guide, keep the default user and the option off:

| **Option** | **What it does** |
|---|---|
| **Local users**<br>`ONEAPP_AUTH_LOCAL_USERS` | The accounts the portal creates in its directory at first boot, as `user:password` separated by spaces. The default is `demo1:demo1pass`. A uid may follow, as `user:password:uid`, to match accounts that exist elsewhere. |
| **OpenID Connect**<br>`ONEAPP_AUTH_OIDC_ENABLED` | Adds an institutional login next to the local one, for instance MyAccessID or Keycloak. The switch reveals the issuer URL, the client id, the client secret and the name shown on the login page. |
{.w-100}

The **Home directories** tab decides where the files of the users live. For this guide, leave the option off:

| **Option** | **What it does** |
|---|---|
| **NFS server of your own**<br>`ONEAPP_HOME_NFS_ENABLED` | Mounts the home directories from an NFS server you already run, instead of the storage role. The storage role then only keeps the software cache. The switch reveals the address of the server and the export path. |
{.w-100}

The **Software catalogue** tab decides where the EESSI files come from. For this guide, leave the option off:

| **Option** | **What it does** |
|---|---|
| **CernVM-FS proxy of your own**<br>`ONEAPP_SOFTWARE_PROXY_ENABLED` | Points the portal and the workers at a CernVM-FS proxy the site already runs, instead of the cache on the storage role. The switch reveals the URL of the proxy. |
{.w-100}

In **Charter**, leave the list empty and click **Finish**. From the Front-end command line, `oneflow-template instantiate 'Open OnDemand Service'` requests the same values interactively.

## Step 4: Wait for the Service

The roles start in order, `storage` first and `worker` last. Each role declares itself ready through OneGate only when it is serving. From **Instances -> Services**, the service normally moves from `DEPLOYING` to `RUNNING` within about four minutes.

{{< image path="/images/open_ondemand/light/sunstone_service_running.png"
alt="The Open OnDemand Service running in Sunstone" align="center" width="90%" mb="20px" >}}

Click on the service in the list and select the **Roles** tab to see the three roles. Select a role to list its VMs.

{{< image path="/images/open_ondemand/light/sunstone_service_roles.png"
alt="The three roles of the running service" align="center" width="90%" mb="20px" >}}

A role that remains in `DEPLOYING` has not declared itself ready, see [Monitoring and Troubleshooting]({{% relref "solutions/integration_blueprints/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}).

## Step 5. Open the Portal

The portal publishes its address as `OOD_URL` in the user template of the portal VM. In the **Roles** tab of the service, tick the `portal` role and click its VM in the table. Then read the value in the **Template** tab, under **User Template**, next to `READY`.

{{< image path="/images/open_ondemand/light/sunstone_portal_ood_url.png"
alt="The user template of the portal VM in Sunstone, with OOD_URL and READY" align="center" width="90%" mb="20px" >}}

The same value is available from the Front-end command line:

```shell
onevm show <PORTAL_VM_ID> | grep OOD_URL
```

```default
OOD_URL="https://192.168.100.165/"
```

The value is `https://` followed by the management address of the portal VM, or by `ONEAPP_PORTAL_HOST_NAME` if you set a Host name. With the default self-signed certificate, the browser asks you to accept it.

The address belongs to the management network. If your computer reaches that network, open the address as it is. If it does not, follow [the instructions below](#reach-the-portal-from-outside).

### Reach the Portal from Outside

There are three things that give the portal a public name:

* A public address that forwards to the portal VM, 
* A DNS name for that address
* The DNS name as the portal Host name

In the following example, the Front-end of a single-host cloud owns the public address `51.159.138.137`. The portal VM is at `192.168.100.184` on the management network.

1. **A DNS Name**: Point a name of your domain at the public address, or use [sslip.io](https://sslip.io). This public DNS service resolves any name with an IP address written within it, so `ood.51-159-138-137.sslip.io` resolves to `51.159.138.137` without the need to register the name.

2. **Port Forwarding to the Portal**: On a cloud provider, use a floating address or a port forwarding rule of the provider to the management address of the portal VM. On a Linux Host that owns the public address, two NAT rules forward ports 443 and 80. Port 80 only matters for Let's Encrypt. Save the rules so they survive a reboot:

   ```shell
   iptables -t nat -A PREROUTING -i ens2 -p tcp --dport 443 -j DNAT --to-destination 192.168.100.184:443
   iptables -t nat -A PREROUTING -i ens2 -p tcp --dport 80 -j DNAT --to-destination 192.168.100.184:80
   iptables-save > /etc/iptables/rules.v4
   ```

   `ens2` is the interface that carries the public address. The VMs of the management network need a route back through that Host. A network with the Host as gateway already has that route.

3. **The Name as Host Name of the Portal**: Set it at instantiation, in the **Portal** tab, or on a running portal. A running portal reconfigures itself in under a minute and issues a self-signed certificate for the name:

   ```shell
   onevm updateconf <PORTAL_VM_ID> --append <<EOT
   CONTEXT = [ ONEAPP_PORTAL_HOST_NAME = "ood.51-159-138-137.sslip.io" ]
   EOT
   ```

`OOD_URL` on the portal VM changes to `https://ood.51-159-138-137.sslip.io/`. The **Let's Encrypt** switch at instantiation gives a certificate the browser trusts. It needs the name to resolve and ports 80 and 443 reachable from the Internet. **Your own certificate** uses one you already have. A portal VM replaced by OneFlow gets a new management address, so the forwarding rule must follow it. Sign in with the initial user, `demo1` with password `demo1pass`, unless you changed `ONEAPP_AUTH_LOCAL_USERS`.

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The home directory is created on first login. The **Interactive Apps** menu lists the six interactive applications, and the dashboard pins five of them.

{{< image path="/images/open_ondemand/light/portal_dashboard.png"
alt="Open OnDemand dashboard" align="center" width="90%" mb="20px" >}}

## Launch a Notebook

From **Interactive Apps -> Jupyter Notebook**, keep one core, 2 GB of memory and one hour, or raise them. The limits are what the largest worker has. Click **Launch**. A **GPUs** field appears only when a worker has a GPU. A **Worker size** field appears only when the service has several worker roles, see [Worker Sizes]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#worker-sizes" %}}).

{{< image path="/images/open_ondemand/light/jupyter_form.png"
alt="Jupyter launch form" align="center" width="90%" mb="20px" >}}

The session is a job of the Slurm Cluster of the service. Its card under **My Interactive Sessions** shows the Cluster, the job id and the worker it runs on. An example is `Runs on: Slurm, job 1 on ood-worker-128`. A session that finds no free cores shows `Queued` on its card. It waits until a session ends or OneFlow adds a worker, a couple of minutes with the Front-end setting the [Requirements]({{% relref "solutions/integration_blueprints/open_ondemand/architecture/#requirements" %}}) recommend. The first session on a fresh deployment takes longer to start, while the site cache fetches the Python module. When the card turns `Running`, click **Open the Jupyter notebook**.

{{< image path="/images/open_ondemand/light/session_card.png"
alt="Session card" align="center" width="90%" mb="20px" >}}

JupyterLab opens through the portal proxy, with the Python and Octave kernels from EESSI.

{{< image path="/images/open_ondemand/light/jupyterlab.png"
alt="JupyterLab running on a compute VM" align="center" width="90%" mb="20px" >}}

Files saved in the notebook go to the user's home directory on the storage role. They appear in **Files -> Home Directory** and in every later session. Deleting the session from **My Interactive Sessions** cancels its job on the worker.

## Next Steps

* [Service Architecture]({{% relref "solutions/integration_blueprints/open_ondemand/architecture/" %}}) describes what was deployed and how a session runs.
* [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/" %}}) covers the Host name and certificate, users, worker sizes, Slurm and external identity providers.
* [Operations]({{% relref "solutions/integration_blueprints/open_ondemand/operations/" %}}) covers keeping the home directories across deployments, upgrading and removing the service.
