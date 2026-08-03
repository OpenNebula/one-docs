---
title: "Self-service Cloud View"
date: "2025-02-17"
description:
categories:
pageintoc: "46"
tags:
weight: "2"
---

<a id="cloud-view"></a>

<!--# Self-service Cloud View -->

This is a simplified view intended for cloud consumers that just require a portal where they can provision new VMs easily. To create new VMs and Services, they just have to select one of the available Templates prepared by the administrators.

{{< image
  path="images/sunstone/cloud_view/light/cloud_view_dashboard.jpg"
  alt="Sunstone cloud dashboard" align="center" width="90%" mb="20px"
>}}

## Using the Cloud

### Create VM

In this scenario the cloud administrator must prepare a set of Templates and Images to make them available to the cloud users. These resources must be **ready** to be used.

For example, when template attributes are defined as mandatory, users can optionally **customize the VM capacity**, **resize disks**, **add new Network Interfaces**, and **provide values required by the template**. Read tips on how to [prepare VM Templates for End-Users]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#vm-templates-endusers" %}}).

Include `%i` in the name to insert the VM index (0..N-1) at a custom place when create more than one virtual machine.

{{< image
  path="images/sunstone/cloud_view/light/cloud_view_instantiate_vm_template.jpg"
  alt="Sunstone cloud instantiate VM" align="center" width="90%" mb="20px"
>}}

<a id="cloudview-ssh-keys"></a>

### Access the VMs with SSH Keys

Any user can provide his own SSH public key to be included in the VMs created through this view. This requires the VM guest to be [contextualized]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#context-overview" %}}), and the Template must have the SSH **contextualization enabled**.

{{< image
  path="/images/sunstone/cloud_view/dark/ssh_contextualization.jpg"
  alt="Sunstone cloud SSH" align="center" width="90%" mb="20px"
>}}

### Manage VMs

The status of the Virtual Machines can be monitored from the **VMs tab**.

{{< image
  path="/images/sunstone/cloud_view/light/cloud_view_vms_list.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Information about the capacity, operating system, ips, creation time, and monitoring graphs for a specific VM are available in the **detail view**.

{{< image
  path="/images/sunstone/cloud_view/light/cloud_view_vms_detail.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Users can perform the following actions from this view:

* Access the VNC console, but only if it’s configured in the Template.
* Reboot the VM: the user can send the reboot signal (`reboot`) or reboot the machine (`reboot hard`).
* Power off the VM: the user can send the power off signal (`poweroff`) or power off the machine (`poweroff hard`).
* Terminate the VM.
* Save the VM into a new Template.
* Power on the VM.

<a id="save-vm-as-template-cloudview"></a>

<a id="cloudview-persistent"></a>

### Make the VM Changes Persistent

Users can create a persistent private copy of the available templates. A **persistent copy will preserve the changes** made to the VM disks after the instance is terminated. This **template is private** and will only be listed to the owner user.

To create a persistent copy, use the **Persistent** switch. Include `%i` in the name to insert the VM index (0..N-1) at a custom place when create more than one virtual machine:

{{< alert title="Warning" type="warning" >}}
When creating more than one virtual machine marked as persistent, user must specify `%i` in the name in order to avoid conflicts in the creation of templates and images.
{{< /alert >}} 

{{< image
  path="/images/sunstone/cloud_view/dark/instantiate_as_persistent.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Alternatively, a VM that wasn’t created as persistent can be saved before it’s destroyed. To do so, the user has to `power off` the VM first and then use the `save` operation.

{{< image
  path="/images/sunstone/cloud_view/light/cloud_view_save_as_template.jpg"
  alt="Sunstone cloud VMs" align="center" width="60%" mb="20px"
>}}

It will then appear in the list of saved templates:

{{< image
  path="/images/sunstone/cloud_view/dark/saved_templates_list.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Any of the these two actions will create a new Template. This Template can be used to **restore the state of a VM after deletion**. This template contains a copy of each one of the original disk images.

{{< alert title="Warning" type="warning" >}}
If you delete this template, all the disk contents will be also lost.{{< /alert >}} 
{{< alert title="Note" type="info" >}}

**Avoid making a persistent copy of a persistent copy!** Although there are use cases where it is justified, this will result in a long list of Templates and the disk usage quota will decrease quickly.{{< /alert >}} 

For more details about the limitations of saved VM, continue to the [Managing Virtual Machines guide]({{% relref "../../virtual_machines_operation/virtual_machines/vm_instances#vm-guide2-clone-vm" %}}).

### Create Service

In the same way as instantiating a VM, the cloud administrator must prepare a set of Service Templates. Before instantiating them, users can optionally **customize the Service cardinality**, **define the network interfaces**, and **provide values required by the template**.

{{< image
  path="/images/sunstone/cloud_view/dark/instantiate_service.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

### Manage Services

The status of the Services can be monitored from the Services tab.

{{< image
  path="/images/sunstone/cloud_view/light/manage_services.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Information of the creation time, cardinality, and status for each Role are available in the **detail view**.

{{< image
  path="/images/sunstone/cloud_view/light/service_detail.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

Users can perform the following actions from this view:

* Change the cardinality of each Role
* Retrieve the VMs of each Role
* Delete the Service
* Recover the Service from a fail status

### Usage, Accounting, and Showback

From the user settings dialog, users can check their current **change account configuration** like their password, language, SSH key and view:

{{< image
  path="/images/sunstone/cloud_view/light/user_settings.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}

From the user dialog, users can check their current **quotas**, **accounting**, **showback** information:

{{< image
  path="/images/sunstone/cloud_view/dark/showback_panel.jpg"
  alt="Sunstone cloud VMs" align="center" width="90%" mb="20px"
>}}
