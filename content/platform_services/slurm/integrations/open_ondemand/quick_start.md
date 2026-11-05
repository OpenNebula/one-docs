---
title: "Quick Start"
linkTitle: "Quick Start"
date: "2026-10-14"
categories:
tags:
type: docs
weight: "3"
aliases:
  - /solutions/integration_blueprints/open_ondemand/quick_start/
---

This guide deploys the portal from Sunstone in the following steps:

1. Import the appliance.
2. Start the wizard.
3. Fill in the user inputs.
4. Attach the network of the Clusters.
5. Check that the portal is ready.

## Step 1: Import the Appliance

In Sunstone:

1. Go to **Storage -> Apps**.
2. Search for **Open OnDemand** and select it.
3. Click **Import** and choose the image datastore.

Or, with the CLI on the Front-end:

```shell
onemarketapp export "Open OnDemand" "Open OnDemand" --datastore default
```

This imports an image and a VM template, both called **Open OnDemand**.

## Step 2: Start the Wizard

1. Go to **Templates -> VM Templates**.
2. Select the **Open OnDemand** template and click **Instantiate**.
3. Enter a name for the VM and click **Next**.

## Step 3: Fill in the User Inputs

The wizard has three tabs: **LDAP**, **Home** and **Slurm**.

### LDAP Tab

* In **LDAP URL**, enter the LDAP server of the Clusters, for example `ldap://10.0.0.20`.
* In **LDAP domain or base DN**, keep `slurm.local`, the default of OneSlurm, or enter the domain of your LDAP server. The base DN is the root of the directory. A domain such as `slurm.local` becomes the base DN `dc=slurm,dc=local`, and the portal looks for users under `ou=People` of that base DN.

{{< image path="/images/slurm/open_ondemand/light/ood_wizard_ldap.png"
   pathDark="/images/slurm/open_ondemand/dark/ood_wizard_ldap.png"
alt="LDAP tab of the Open OnDemand wizard" align="center" width="90%" mb="30px" >}}

### Home Tab

* In **NFS export for /home**, enter the export with the home directory of the users, for example `10.0.0.10:/export/home`.

{{< image path="/images/slurm/open_ondemand/light/ood_wizard_home.png"
   pathDark="/images/slurm/open_ondemand/dark/ood_wizard_home.png"
alt="Home tab of the Open OnDemand wizard" align="center" width="90%" mb="30px" >}}

### Slurm Tab

* In **Slurm Clusters**, enter one line for each Cluster as `name:IP`, for example `cpu:10.0.0.20`. The name is what users see in the portal and must be unique. The IP is the IPv4 address of the controller. **Every Cluster must use the same LDAP server and the same `/home` as the portal.**

{{< image path="/images/slurm/open_ondemand/light/ood_wizard_slurm.png"
   pathDark="/images/slurm/open_ondemand/dark/ood_wizard_slurm.png"
alt="Slurm tab of the Open OnDemand wizard" align="center" width="90%" mb="30px" >}}

## Step 4: Attach the Network of the Clusters

1. Click **Next**.
2. In **Advanced options**, open the **Network** tab.
3. Click **Attach NIC** and select the Virtual Network of the Clusters.
4. Click **Finish**.

{{< image path="/images/slurm/open_ondemand/light/ood_wizard_network.png"
   pathDark="/images/slurm/open_ondemand/dark/ood_wizard_network.png"
alt="Network tab of the Open OnDemand wizard with the NIC of the Clusters" align="center" width="90%" mb="30px" >}}

The portal uses the IPv4 address of the first NIC. Users must be able to reach that address with their web browser.

## Step 5: Check That the Portal Is Ready

Open the VM in Sunstone and go to **Info -> Attributes**. With the CLI, run `onevm show <VM_ID>`:

| **Attribute** | **Meaning** |
|-----------|---------|
| `READY` = `YES` | The portal is ready. |
| `OOD_URL` | The address of the portal, for example `https://10.0.0.50/`. |
| `OOD_ERROR` | The configuration failed. The value says why, and the portal stays closed. |

Examples of `OOD_ERROR`:

* `Cannot mount 10.0.0.10:/export/nope on /home`
* `The controller 10.0.0.30 does not answer on the SSH port`

| **Cause of the error** | **How to fix it** |
|--------------------|---------------|
| A service was down | Fix the service and reboot the VM. |
| A value was wrong | Change it as shown in [Change the Clusters]({{% relref "platform_services/slurm/integrations/open_ondemand/operations#change-the-clusters" %}}), then reboot the VM so that OneGate shows the new result. |

## Deploy with the CLI

Instead of Steps 2 to 4, you can pass the same values with `--user-inputs`. Separate the Clusters with spaces:

```shell
onetemplate instantiate "Open OnDemand" --name open-ondemand --nic <network> \
    --user-inputs "ONEAPP_LDAP_SERVER_URL=ldap://10.0.0.20,ONEAPP_LDAP_SERVER_DOMAIN=slurm.local,ONEAPP_HOME_NFS_EXPORT=10.0.0.10:/export/home,ONEAPP_SLURM_CLUSTERS_LIST=cpu:10.0.0.20 gpu:10.0.0.30"
```

Then check the portal as in Step 5.

## Next Steps

To sign in to the portal and add users, refer to [Operations]({{% relref "platform_services/slurm/integrations/open_ondemand/operations" %}}).
