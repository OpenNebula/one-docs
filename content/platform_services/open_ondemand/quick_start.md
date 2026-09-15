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

This quick-start guide uses the Sunstone Web UI to deploy an Open OnDemand Service with one portal, one storage VM and one worker, and to open a JupyterLab notebook on it. Before beginning, check the [Requirements]({{% relref "platform_services/open_ondemand/architecture/#requirements" %}}): OneFlow and OneGate enabled, and two Virtual Networks, one with Internet access and one reserved for the service.

Quick-start workflow:

* **Download the appliance**: import the image, the VM template and the service template from the Community Marketplace.
* **Instantiate the service**: select the two Virtual Networks and the address range of the compute network.
* **Wait for the service**: the service reaches the `RUNNING` state in about four minutes.
* **Open the portal and launch a notebook**: sign in with the initial user and open JupyterLab on the worker VM.

## Download the Appliance

Register the [Community Marketplace](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start) once if it is not in your installation. Then, from **Storage -> Apps**, download `Open OnDemand Service` into an image Datastore. Three objects are imported: the image the three roles share, the VM template that boots it and the service template `Open OnDemand Service`. From the Front-end command line:

```shell
onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

The image is about 1.5 GB. Wait until `oneimage list` shows it in the `rdy` state.

## Instantiate the Service

From **Templates -> Service Templates**, select `Open OnDemand Service` and click the **Instantiate** icon, the first one in the toolbar of the detail pane:

{{< image path="/images/open_ondemand/light/sunstone_service_templates.png"
alt="The Open OnDemand Service template in Sunstone" align="center" width="90%" mb="20px" >}}

The wizard has four steps. In **General**, keep the name and one instance:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_general.png"
alt="Instantiate wizard, General step" align="center" width="90%" mb="20px" >}}

In **Networks**, click each entry on the left and select its Virtual Network in the table. `Management` is the network with Internet access, where the portal publishes its web interface. `Compute` is the network reserved for the service:

{{< image path="/images/open_ondemand/light/sunstone_instantiate_networks.png"
alt="Instantiate wizard, Networks step" align="center" width="90%" mb="20px" >}}

In **Service Inputs**, the only required value is `ONEAPP_POOL_RANGE` in the **others** tab: the address range the compute network assigns to VMs, as `first-last`. It has to match the network you selected as `Compute`. Everything else keeps its default, a self-signed certificate and the user `demo1`. The inputs are described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}):

{{< image path="/images/open_ondemand/light/sunstone_instantiate_inputs.png"
alt="Instantiate wizard, Service Inputs step" align="center" width="90%" mb="20px" >}}

In **Charter**, leave the list empty and click **Finish**. From the Front-end command line, `oneflow-template instantiate 'Open OnDemand Service'` asks for the same values interactively.

## Wait for the Service

The roles start in order, `storage` first and `worker` last, and each one declares itself ready through OneGate only when it is serving. From **Instances -> Services**, the service moves from `DEPLOYING` to `RUNNING` in about four minutes:

{{< image path="/images/open_ondemand/light/sunstone_service_running.png"
alt="The Open OnDemand Service running in Sunstone" align="center" width="90%" mb="20px" >}}

Open the service and select the **Roles** tab to see the three roles and their VMs:

{{< image path="/images/open_ondemand/light/sunstone_service_roles.png"
alt="The three roles of the running service" align="center" width="90%" mb="20px" >}}

A role that stays in `DEPLOYING` has not declared itself ready, see [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}).

## Open the Portal

The portal answers on `https://<management address of the portal VM>/`, the first address shown for the portal VM in the **Roles** tab, or on `https://<ONEAPP_OOD_SERVERNAME>/` if you gave it a host name. With the default self-signed certificate the browser asks you to accept it. Sign in with the initial user, `demo1` with password `demo1pass` unless you changed `ONEAPP_LDAP_USERS`:

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The home directory is created on first login. The dashboard lists the six interactive applications:

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
