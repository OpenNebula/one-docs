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

* **Create the networks**: a management network with Internet access, which you probably have, and a compute network reserved for the service.
* **Download the appliance**: import the image, the VM template and the service template from the Community Marketplace.
* **Instantiate the service**: select the two Virtual Networks and keep the default inputs.
* **Wait for the service**: the service reaches the `RUNNING` state in about four minutes.
* **Open the portal and launch a notebook**: sign in with the initial user and open JupyterLab as a Slurm job on the worker VM.

## Before You Start

The service needs two Virtual Networks, and the wizard asks for both:

* **Management network.** The network your VMs already use to reach the Internet. The portal publishes its web interface on it, and OneGate has to be reachable from it.
* **Compute network.** A private network for the VMs of this service and nothing else. The shared home, the user directory, the software cache and the Slurm traffic between the portal and the workers use it.

Keep the compute network private and small, a /24 or smaller. Its traffic is not encrypted, the workers join the Slurm cluster through it, and the portal takes every address of that /24 as a possible worker. A larger network needs `ONEAPP_POOL_RANGE`, described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/#advanced-attributes" %}}).

Both networks are created from **Networks -> Virtual Networks** with **+ Create Virtual Network** and **From scratch**. Most installations already have a management network, so skip the first one if yours does. From the Front-end command line, `onevnet create` creates the same networks from a template file, see [Managing Virtual Networks]({{% relref "product/cluster_configuration/networking_system/manage_vnets/" %}}).

### Create the Management Network

1. **General.** Give it a name, `ood-management` for instance, and select the Cluster of the Hosts that will run the service. Click **Next**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_general.png"
alt="Create Virtual Network wizard, General step of the management network" align="center" width="90%" mb="20px" >}}

2. **Configuration.** Choose the network mode of your Hosts. On a single Host, **Bridged** with **Custom name for bridge** and the name of the bridge that reaches the Internet, `br0` for instance.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_conf.png"
alt="Create Virtual Network wizard, Configuration tab of the management network" align="center" width="90%" mb="20px" >}}

3. **Addresses.** Click **+ Add Address Range**, set the first free address of the network and the number of addresses, `192.168.100.50` and `200` for instance, and click **Accept**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_addresses.png"
alt="Create Virtual Network wizard, Addresses tab of the management network" align="center" width="90%" mb="20px" >}}

4. **Context.** Set the network address, the network mask, the gateway and the DNS server, so the VMs reach the Internet, `192.168.100.0`, `255.255.255.0`, `192.168.100.1` and `1.1.1.1` for instance. Click **Finish**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_management_context.png"
alt="Create Virtual Network wizard, Context tab of the management network" align="center" width="90%" mb="20px" >}}

### Create the Compute Network

1. **General.** Give it a name, `ood-compute` for instance, and select the same Cluster. Click **Next**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_general.png"
alt="Create Virtual Network wizard, General step of the compute network" align="center" width="90%" mb="20px" >}}

2. **Configuration.** Any mode where the VMs of the Cluster reach each other works. On a single Host, **Bridged** with **Custom name for bridge** and a new bridge name, `br1` for instance. Across several Hosts, use the mode and physical device of your other private networks, VXLAN for instance.

{{< image path="/images/open_ondemand/light/sunstone_vnet_conf.png"
alt="Create Virtual Network wizard, Configuration tab of the compute network" align="center" width="90%" mb="20px" >}}

3. **Addresses.** Click **+ Add Address Range**, set a first address and a size inside one /24, `172.22.0.50` and `200` for instance, and click **Accept**.

{{< image path="/images/open_ondemand/light/sunstone_vnet_addresses.png"
alt="Create Virtual Network wizard, Addresses tab of the compute network" align="center" width="90%" mb="20px" >}}

4. **Context.** Leave it empty. This network has no gateway, because its traffic never leaves the Hosts. Click **Finish**.

## Download the Appliance

Register the [Community Marketplace](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start) once if it is not in your installation. Then, from **Storage -> Apps**, download `Open OnDemand Service` into an image Datastore. The download imports three objects, the image the three roles share, the VM template that boots it and the service template `Open OnDemand Service`. From the Front-end command line:

```shell
onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

The image is about 1.6 GB, so wait until `oneimage list` shows it in the `rdy` state.

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

In **Service Inputs**, nothing needs to change for a first start. Every input is optional, and the defaults give a portal with a self-signed certificate on its management address and one local user, `demo1` with password `demo1pass`. The home directories stay on the storage role, and the Slurm cluster of the service needs no input. The inputs sit in three tabs, one per topic, each section carries a help icon with its explanation, and every optional feature is a switch that reveals its fields only when it is on. The **Portal** tab looks like this:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_inputs.png"
alt="Instantiate wizard, Service Inputs step, Portal tab" align="center" width="90%" mb="20px" >}}

The **Portal** tab holds the public name and the TLS certificate of the web portal. For a first start leave the name empty and both switches off:

| Option | What it does |
|---|---|
| **Host name**<br>`ONEAPP_PORTAL_HOST_NAME` | The public name users open the portal at. Empty makes the portal answer on its management address. A name can be set on the running portal later, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/#service-inputs" %}}). |
| **Let's Encrypt**<br>`ONEAPP_PORTAL_LETSENCRYPT_ENABLED` | Requests a certificate for the host name when the portal boots. The name has to resolve to the portal, and ports 80 and 443 have to be reachable from the Internet. Off, the portal starts with a self-signed certificate. |
| **Your own certificate**<br>`ONEAPP_PORTAL_CERTIFICATE_ENABLED` | Replaces the self-signed certificate with a PEM chain and a PEM key that you paste in the two boxes the switch reveals. |
{.w-100}

The **Users and login** tab decides who can sign in. For a first start keep the default user and the switch off:

| Option | What it does |
|---|---|
| **Local users**<br>`ONEAPP_AUTH_LOCAL_USERS` | The accounts the portal creates in its directory at first boot, as `user:password` separated by spaces. The default is `demo1:demo1pass`. A uid may follow, `user:password:uid`, to match accounts that exist elsewhere. |
| **OpenID Connect**<br>`ONEAPP_AUTH_OIDC_ENABLED` | Adds an institutional login next to the local one, MyAccessID or Keycloak for instance. The switch reveals the issuer URL, the client id, the client secret and the name shown on the login page. |
{.w-100}

The **Home directories** tab decides where the files of the users live. For a first start leave the switch off:

| Option | What it does |
|---|---|
| **NFS server of your own**<br>`ONEAPP_HOME_NFS_ENABLED` | Mounts the home directories from an NFS server you already run instead of the storage role, which then only keeps the software cache. The switch reveals the address of the server and the export path. |
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

It is `https://` followed by the management address of the portal VM, or by `ONEAPP_PORTAL_HOST_NAME` if you gave it a host name. With the default self-signed certificate the browser asks you to accept it.

The address belongs to the management network. When your desk reaches that network, open it as it is. When it does not, follow [Reach the Portal from Outside](#reach-the-portal-from-outside) below.

### Reach the Portal from Outside

Three things give the portal a public name, a public address that forwards to the portal VM, a DNS name for that address, and that name set as the host name of the portal. The example uses the public address `51.159.138.137` of a single-host cloud whose Front-end owns it, and the portal VM at `192.168.100.184` on the management network.

1. **A DNS name.** Point a name of your domain at the public address, or use [sslip.io](https://sslip.io), a public DNS service that resolves any name with an address written in it, so `ood.51-159-138-137.sslip.io` resolves to `51.159.138.137` with nothing to register.

2. **Port forwarding to the portal.** On a cloud provider, a floating address or a port forwarding rule of the provider to the management address of the portal VM does it. On a Linux host that owns the public address, two NAT rules forward ports 443 and 80 (80 only matters for Let's Encrypt), saved so they survive a reboot:

   ```shell
   iptables -t nat -A PREROUTING -i ens2 -p tcp --dport 443 -j DNAT --to-destination 192.168.100.184:443
   iptables -t nat -A PREROUTING -i ens2 -p tcp --dport 80 -j DNAT --to-destination 192.168.100.184:80
   iptables-save > /etc/iptables/rules.v4
   ```

   `ens2` is the interface that carries the public address. The VMs of the management network need a route back through that host, which a network with the host as gateway already has.

3. **The name as host name of the portal.** At instantiation, in the **Portal** tab, or on a running portal, which reconfigures itself in under a minute and issues a self-signed certificate for the name:

   ```shell
   onevm updateconf <portal vm id> --append <<EOT
   CONTEXT = [ ONEAPP_PORTAL_HOST_NAME = "ood.51-159-138-137.sslip.io" ]
   EOT
   ```

`OOD_URL` on the portal VM changes to `https://ood.51-159-138-137.sslip.io/`. With the name resolving and ports 80 and 443 reachable from the Internet, the **Let's Encrypt** switch at instantiation gives a certificate the browser trusts, and **Your own certificate** takes one you already have. A portal VM replaced by OneFlow gets a new management address, so the forwarding rule has to follow it. Sign in with the initial user, `demo1` with password `demo1pass` unless you changed `ONEAPP_AUTH_LOCAL_USERS`:

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The home directory is created on first login. The **Interactive Apps** menu lists the six interactive applications, and the dashboard pins five of them:

{{< image path="/images/open_ondemand/light/portal_dashboard.png"
alt="Open OnDemand dashboard" align="center" width="90%" mb="20px" >}}

## Launch a Notebook

From **Interactive Apps -> Jupyter Notebook**, keep one core, 2 GB of memory and one hour, or raise them up to what the largest worker has, and click **Launch**. A **GPUs** field appears only when a worker has a GPU, and a **Worker size** field only when the service has several worker roles, see [Worker Sizes]({{% relref "platform_services/open_ondemand/configuration/#worker-sizes" %}}):

{{< image path="/images/open_ondemand/light/jupyter_form.png"
alt="Jupyter launch form" align="center" width="90%" mb="20px" >}}

The session is a job of the Slurm cluster of the service, and its card under **My Interactive Sessions** shows the cluster, the job id and the worker it runs on, `Runs on: Slurm, job 1 on ood-worker-128` for instance. A session that finds no free cores shows `Queued` on its card until a session ends or OneFlow adds a worker, under three minutes on the testbed. The first session on a fresh deployment takes longer to start while the site cache fetches the Python module. When the card turns `Running`, click **Open the Jupyter notebook**:

{{< image path="/images/open_ondemand/light/session_card.png"
alt="Session card" align="center" width="90%" mb="20px" >}}

JupyterLab opens through the portal proxy, with the Python and Octave kernels from EESSI:

{{< image path="/images/open_ondemand/light/jupyterlab.png"
alt="JupyterLab running on a compute VM" align="center" width="90%" mb="20px" >}}

Files saved in the notebook go to the user's home directory on the storage role and appear in **Files -> Home Directory** and in every later session. Deleting the session from **My Interactive Sessions** cancels its job on the worker.

## Next Steps

* [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}): what was deployed and how a session runs.
* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}): host name and certificate, users, worker sizes, Slurm and external identity providers.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}): keeping the home directories across deployments, upgrading and removing the service.
