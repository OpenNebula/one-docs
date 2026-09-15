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

This quick-start guide uses the Sunstone Web UI to deploy an Open OnDemand Service with one portal, one storage VM and one worker, and to open a JupyterLab notebook on it. The CLI equivalents are shown along the way. Before beginning, check the [Requirements]({{% relref "platform_services/open_ondemand/architecture/#requirements" %}}): OneFlow and OneGate enabled, and two Virtual Networks, one with Internet access and one reserved for the service.

Quick-start workflow:

* **Register the Community Marketplace**: Make the appliance visible in your OpenNebula.
* **Download the appliance**: Import the image, the VM template and the service template.
* **Instantiate the service**: Select the two Virtual Networks and the address range of the compute network.
* **Wait for the service**: Wait until the service reaches the `RUNNING` state.
* **Open the portal**: Sign in with the initial user.
* **Launch a notebook**: Open JupyterLab on the worker VM.

## Register the Community Marketplace

The appliance is published in the [OpenNebula Community Marketplace](https://community-marketplace.opennebula.io/). Register the marketplace once in your installation, from **Storage -> Marketplaces** in Sunstone or from the Front-end command line, as described in the [marketplace instructions](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start).

## Download the Appliance

From **Storage -> Apps**, search for `Open OnDemand Service` and download it into an image Datastore. The download imports three objects: the image the three roles share, the VM template that boots it, and the service template `Open OnDemand Service`.

From the Front-end command line:

```shell
onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

The image is about 1.4 GB, so the import takes a few minutes. Check that it reaches the `READY` state:

```shell
oneimage list
```

```default
  ID USER     GROUP    NAME            DATASTORE     SIZE TYPE PER STAT RVMS
  49 oneadmin oneadmin Open OnDemand   default        20G OS    No rdy     0
```

## Instantiate the Service

From **Templates -> Service Templates**, select `Open OnDemand Service`. The **Roles** tab shows the three roles, the VM template they share and the limits of the worker pool. Click the **Instantiate** icon, the first one in the toolbar of the detail pane:

{{< image path="/images/open_ondemand/light/sunstone_service_templates.png"
alt="The Open OnDemand Service template in Sunstone" align="center" width="90%" mb="20px" >}}

The wizard guides you through four steps:

* **General**: Service name and number of instances.
* **Networks**: The two Virtual Networks of the service.
* **Service Inputs**: The `ONEAPP_*` values described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}).
* **Charter**: Scheduled actions. Leave it empty.

In **General**, keep the name or choose your own, and leave the number of instances at `1`:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_general.png"
alt="Instantiate wizard, General step" align="center" width="90%" mb="20px" >}}

In **Networks**, select the Virtual Network for each of the two entries. `Management` is the network with Internet access, where the portal publishes its web interface. `Compute` is the network reserved for the service. Click the entry on the left, then the network in the table:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_networks.png"
alt="Instantiate wizard, Networks step" align="center" width="90%" mb="20px" >}}

In **Service Inputs**, the values are grouped in tabs by name. The only required one is in the **others** tab, `ONEAPP_POOL_RANGE`, the address range the compute network assigns to VMs as `first-last`. It has to match the address range of the network you selected as `Compute`. The rest keep their defaults, a self-signed certificate and the user `demo1`:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_inputs.png"
alt="Instantiate wizard, Service Inputs step" align="center" width="90%" mb="20px" >}}

{{< alert title="Note" type="primary" >}}
The service does not take any fixed address. OneFlow hands the storage address to the portal and the workers, and the storage role asks OneGate which VM plays the portal. The address range is the only network value you provide, and the portal uses it to find its workers when OneGate is not available.
{{< /alert >}}

In **Charter**, leave the list empty and click **Finish**.

From the Front-end command line, the same instantiation asks for the networks and the inputs interactively:

```shell
oneflow-template instantiate 'Open OnDemand Service'
```

## Wait for the Service

The roles start in order, `storage` first and `worker` last, and each one declares itself ready through OneGate only when it is actually serving. From **Instances -> Services**, the service moves from `DEPLOYING` to `RUNNING` in about four minutes:

{{< image path="/images/open_ondemand/light/sunstone_service_running.png"
alt="The Open OnDemand Service running in Sunstone" align="center" width="90%" mb="20px" >}}

Open the service and select the **Roles** tab to see the three roles and their VMs:

{{< image path="/images/open_ondemand/light/sunstone_service_roles.png"
alt="The three roles of the running service" align="center" width="90%" mb="20px" >}}

From the Front-end command line:

```shell
oneflow list
```

```default
  ID USER     GROUP    NAME                  STARTTIME STAT
  61 oneadmin oneadmin Open OnDemand S  09/15 07:21:27 RUNNING
```

A role that stays in `DEPLOYING` has not declared itself ready. See [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}) for where to look.

## Open the Portal

The portal answers on `https://<management address of the portal VM>/`, or on `https://<ONEAPP_OOD_SERVERNAME>/` if you gave it a host name. Find the address from the **VMs** tab of the service, or from the command line:

```shell
onevm list -l ID,NAME,IP --filter NAME~portal
```

```default
  ID NAME            IP
 359 portal_0_(servi 192.168.100.145,172.21.0.83
```

The first address is the management one. With the default self-signed certificate, the browser asks you to accept it. Sign in with the initial user from `ONEAPP_LDAP_USERS`, by default `demo1` with password `demo1pass`:

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The home directory is created on first login. The dashboard lists the five interactive applications:

{{< image path="/images/open_ondemand/light/portal_dashboard.png"
alt="Open OnDemand dashboard" align="center" width="90%" mb="20px" >}}

## Launch a Notebook

From **Interactive Apps -> Jupyter Notebook**, keep the target `OpenNebula VM (Apptainer)`, choose the session length in hours and click **Launch**:

{{< image path="/images/open_ondemand/light/jupyter_form.png"
alt="Jupyter launch form" align="center" width="90%" mb="20px" >}}

The session card under **My Interactive Sessions** shows the worker VM the session landed on. The session is `Starting` while the container loads the Python kernel from the software catalogue, which takes longer the first time on a fresh deployment, while the site cache fills. When it turns `Running`, click **Open the Jupyter notebook**:

{{< image path="/images/open_ondemand/light/session_card.png"
alt="Session card" align="center" width="90%" mb="20px" >}}

JupyterLab opens through the portal proxy, with the Python and Octave kernels served from EESSI:

{{< image path="/images/open_ondemand/light/jupyterlab.png"
alt="JupyterLab running on a compute VM" align="center" width="90%" mb="20px" >}}

Files saved in the notebook land in the user's home on the storage role, and are visible from **Files -> Home Directory** and from any later session. Deleting the session from **My Interactive Sessions** ends it on the worker and frees it for the next one.

Completing this quick-start guide validates that the three roles talk to each other, that the portal can start sessions on the pool, and that the software catalogue is reachable from a session.

## Next Steps

Once the service is running, read the [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}) to understand what was deployed. Then consult the following references:

* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}): host name and certificate, users, worker sizes, Slurm and external identity providers.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}): scaling by hand, keeping the home directories across deployments, upgrading and removing the service.
* [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/" %}}): metrics, worker health and logs.
