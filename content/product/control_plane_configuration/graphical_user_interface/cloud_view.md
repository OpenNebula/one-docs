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

{{< image pathDark="/images/sunstone/cloud_view/dark/cloudview_dashboard.png"
          path="/images/sunstone/cloud_view/light/cloudview_dashboard.png" 
          alt="Cloud View Dashboard" align="center" width="90%" mb="20px">}}

## Using the Cloud

### Create VM

In this scenario the cloud administrator must prepare a set of Templates and Images to make them available to the cloud users. These resources must be **ready** to be used.

For example, when template attributes are defined as mandatory, users can optionally **customize the VM capacity**, **resize disks**, **add new Network Interfaces**, and **provide values required by the template**. Read tips on how to [prepare VM Templates for End-Users]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#vm-templates-endusers" %}}).

Include `%i` in the name to insert the VM index (0..N-1) at a custom place when create more than one virtual machine.

{{< image pathDark="/images/sunstone/cloud_view/dark/create_vm.png"
          path="/images/sunstone/cloud_view/light/create_vm.png" 
          alt="Cloud View create VM" align="center" width="90%" mb="20px">}}

<a id="cloudview-ssh-keys"></a>

### Access the VMs with SSH Keys

Any user can provide his own SSH public key to be included in the VMs created through this view. This requires the VM guest to be [contextualized]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#context-overview" %}}), and the Template must have the SSH **contextualization enabled**.

{{< image pathDark="/images/sunstone/cloud_view/dark/ssh_key.png"
          path="/images/sunstone/cloud_view/light/ssh_key.png" 
          alt="Cloud View SSH" align="center" width="90%" mb="20px">}}

### Manage VMs

The status of the Virtual Machines can be monitored from the **Instances -> VMs** view.

{{< image pathDark="/images/sunstone/cloud_view/dark/vm_list.png"
          path="/images/sunstone/cloud_view/light/vm_list.png" 
          alt="Cloud View VM list" align="center" width="90%" mb="20px">}}

Information about the capacity, operating system, ips, creation time, and monitoring graphs for a specific VM are available in the **Detail view**, click on a VM in the list to open the details panel.

{{< image pathDark="/images/sunstone/cloud_view/dark/vm_details.png"
          path="/images/sunstone/cloud_view/light/vm_details.png" 
          alt="Cloud View VM details" align="center" width="90%" mb="20px">}}

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

{{< image pathDark="/images/sunstone/cloud_view/dark/persistent_template.png"
          path="/images/sunstone/cloud_view/light/persistent_template.png" 
          alt="Cloud View instantiate as persistent" align="center" width="90%" mb="20px">}}

Alternatively, a VM that wasn’t created as persistent can be saved before it’s destroyed. To do so, the user has to `power off` the VM first and then use the `save` operation.

{{< image pathDark="/images/sunstone/cloud_view/dark/save_as_template.png"
          path="/images/sunstone/cloud_view/light/save_as_template.png" 
          alt="Cloud View save as template" align="center" width="90%" mb="20px">}}

It will then appear in the list of saved templates:

{{< image pathDark="/images/sunstone/cloud_view/dark/new_template.png"
          path="/images/sunstone/cloud_view/light/new_template.png" 
          alt="Cloud View new template" align="center" width="90%" mb="20px">}}

Any of the these two actions will create a new Template. This Template can be used to **restore the state of a VM after deletion**. This template contains a copy of each one of the original disk images.

{{< alert title="Warning" type="warning" >}}
If you delete this template, all the disk contents will be also lost.{{< /alert >}} 
{{< alert title="Note" type="info" >}}

**Avoid making a persistent copy of a persistent copy!** Although there are use cases where it is justified, this will result in a long list of Templates and the disk usage quota will decrease quickly.{{< /alert >}} 

For more details about the limitations of saved VM, continue to the [Managing Virtual Machines guide]({{% relref "../../virtual_machines_operation/virtual_machines/vm_instances#vm-guide2-clone-vm" %}}).

### Create Service

In the same way as instantiating a VM, the cloud administrator must prepare a set of Service Templates. Before instantiating them, users can optionally **customize the Service cardinality**, **define the network interfaces**, and **provide values required by the template**. In the **Instances -> Services** view select **+ Instantiate Service Template**:


{{< image pathDark="/images/sunstone/cloud_view/dark/instantiate_service.png"
          path="/images/sunstone/cloud_view/light/instantiate_service.png" 
          alt="Cloud View instantiate service" align="center" width="90%" mb="20px">}}

### Manage Services

The status of the Services can be monitored from the Services tab.

{{< image pathDark="/images/sunstone/cloud_view/dark/manage_services.png"
          path="/images/sunstone/cloud_view/light/manage_services.png" 
          alt="Cloud View manage services" align="center" width="90%" mb="20px">}}

Information of the creation time, cardinality, and status for each Role are available in the **details view**, opened by clicking on the service in the list.

{{< image pathDark="/images/sunstone/cloud_view/dark/service_details.png"
          path="/images/sunstone/cloud_view/light/service_details.png" 
          alt="Cloud View service details" align="center" width="90%" mb="20px">}}

Users can perform the following actions from this view:

* Change the cardinality of each Role
* Retrieve the VMs of each Role
* Delete the Service
* Recover the Service from a fail status

### Usage, Accounting, and Showback

From the user settings dialog, users can check their current **change account configuration** like their password, language, SSH key and view:

{{< image pathDark="/images/sunstone/cloud_view/dark/user_settings.png"
          path="/images/sunstone/cloud_view/light/user_settings.png" 
          alt="Cloud View user settings" align="center" width="90%" mb="20px">}}

From the user dialog, users can check their current **quotas**, **accounting**, **showback** information:

{{< image pathDark="/images/sunstone/cloud_view/dark/calculate_showback.png"
          path="/images/sunstone/cloud_view/light/calculate_showback.png" 
          alt="Cloud View user settings" align="center" width="90%" mb="20px">}}
