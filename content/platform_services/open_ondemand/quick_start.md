---
title: "Quick Start"
linkTitle: "Quick Start"
weight: 2
type: docs
---

This guide deploys an Open OnDemand service with one portal, one storage VM and one worker, and opens a JupyterLab notebook on it.

## Register the Community Marketplace

The appliance is published in the OpenNebula Community Marketplace. Register it once in your installation, as described in the [marketplace instructions](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start), from Sunstone or from the CLI.

## Download the appliance

Download the `Open OnDemand Service` appliance. This imports the service template, the VM template and the image that the three roles share:

```shell
$ onemarketapp export 'Open OnDemand Service' 'Open OnDemand Service' --datastore default
```

## Instantiate the service

From Sunstone, go to **Instances -> Services** and click **Instantiate Service Template**, or from the CLI:

```shell
$ oneflow-template instantiate 'Open OnDemand Service'
```

The template asks for the two Virtual Networks, management and compute, and for the inputs described in [Configuration]({{% relref "configuration" %}}). The defaults deploy one worker; raise the worker cardinality in the template to start with more.

{{< alert title="Note" type="primary" >}}
`ONEAPP_POOL_RANGE` has to match the address range of the network you select as Compute. The roles find each other without fixed addresses: OneFlow hands the storage address to the portal and the workers, and the storage role asks OneGate which VM plays the portal and grants root on the home export to that address alone.
{{< /alert >}}

The roles start in order, storage first and the workers last, and each one declares itself ready only when it is actually serving. The whole service is running about four minutes after instantiation:

```shell
$ oneflow list
  ID USER     GROUP    NAME                  STARTTIME STAT
  41 oneadmin oneadmin one-ondemand     09/09 10:48:38 RUNNING
```

{{< image path="/images/open_ondemand/light/sunstone_service_running.png"
alt="The Open OnDemand service running in Sunstone" align="center" width="90%" mb="20px" >}}

## Open the portal

The portal answers on `https://<ONEAPP_OOD_SERVERNAME>/`, or on the management address of the portal VM if you left the name empty:

```shell
$ onevm list -f NAME~portal -l ID,NAME,IP
```

Sign in with one of the users given in `ONEAPP_LDAP_USERS`, by default `demo1` with password `demo1pass`. The home directory is created on first login.

{{< image path="/images/open_ondemand/light/portal_login.png"
alt="Open OnDemand login" align="center" width="90%" mb="20px" >}}

The dashboard lists the five interactive applications:

{{< image path="/images/open_ondemand/light/portal_dashboard.png"
alt="Open OnDemand dashboard" align="center" width="90%" mb="20px" >}}

## Launch a notebook

Open **Interactive Apps -> Jupyter Notebook**, choose the session length and click **Launch**:

{{< image path="/images/open_ondemand/light/jupyter_form.png"
alt="Jupyter launch form" align="center" width="90%" mb="20px" >}}

The session card shows the worker VM it landed on. When the notebook is ready, click **Open the Jupyter notebook**:

{{< image path="/images/open_ondemand/light/session_card.png"
alt="Session card" align="center" width="90%" mb="20px" >}}

JupyterLab opens through the portal proxy, with the Python and Octave kernels served from EESSI:

{{< image path="/images/open_ondemand/light/jupyterlab.png"
alt="JupyterLab running on a compute VM" align="center" width="90%" mb="20px" >}}

Deleting the session from **My Interactive Sessions** ends it on the worker and frees it for the next one.

## Next steps

* [Configuration]({{% relref "configuration" %}}) for the service inputs, scaling and users.
* [Operations]({{% relref "operations" %}}) for logs, troubleshooting and removal.
