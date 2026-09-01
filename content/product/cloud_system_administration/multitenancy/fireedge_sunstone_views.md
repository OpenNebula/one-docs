---
title: "Sunstone Views"
date: "2025-02-17"
description:
categories:
pageintoc: "117"
tags:
weight: "5"
---

<a id="fireedge-suns-views"></a>

<!--# Sunstone Views -->

Using the OpenNebula FireEdge Sunstone Views you will be able to provide a simplified UI aimed at end users of an OpenNebula cloud. The OpenNebula FireEdge Sunstone Views are fully customizable, so you can easily enable or disable specific information tabs or action buttons. [You can define multiple views for different user groups]({{% relref "#fireedge-sunstone-views-define-new" %}}). You can define multiple views for different user groups. Each view defines a set of UI components, so each user just accesses and views the relevant parts of the cloud for their role. Default views:

- [Admin View]({{% relref "#fireedge-admin-view" %}})
- [User View]({{% relref "#fireedge-user-view" %}})
- [Group Admin View]({{% relref "#fireedge-groupadmin-view" %}})
- [Cloud View]({{% relref "#fireedge-cloud-view" %}})

Each of these views is defined on a folder in `/etc/one/fireedge/sunstone/views` that contains as many yaml files as tabs are enabled in this view. On this path, there is also a file `/etc/one/fireedge/sunstone/views/sunstone-views.yaml` where the default configuration is defined (see [Defining a New OpenNebula Sunstone View or Customizing an Existing one]({{% relref "#fireedge-sunstone-views-define-new" %}}) for more information about configuring or creating a view).

<a id="fireedge-suns-views-default-views"></a>

## Default Views

<a id="fireedge-admin-view"></a>

### Admin View

This view provides full control of the cloud. Details can be configured in the `/etc/one/fireedge/sunstone/views/admin/*.yaml` files.

{{< image pathDark="/images/sunstone/common/dark/admin_view.png"
          path="/images/sunstone/common/light/admin_view.png" 
          alt="Sunstone admin view" align="center" width="60%" mb="20px">}}

<a id="fireedge-user-view"></a>

### User View

Based on the Admin View; it is an advanced user view. It is intended for users that need access to more actions than the limited set available in the cloud view. Users will not be able to manage nor retrieve the Hosts and clusters of the cloud. They will be able to see datastores and Virtual Networks in order to use them when creating a new Image or Virtual Machine, but they will not be able to create new ones. Details can be configured in the `/etc/one/fireedge/sunstone/views/user/*.yaml` file.

{{< image pathDark="/images/sunstone/common/dark/user_view.png"
          path="/images/sunstone/common/light/user_view.png" 
          alt="Sunstone user view" align="center" width="60%" mb="20px">}}


<a id="fireedge-groupadmin-view"></a>

### Group Admin View

Based on the User View; this view has the same tabs as the User View plus the Groups and Users tabs to manage the group and the users of the groups where this user is an administrator. Details can be configured in the `/etc/one/fireedge/sunstone/views/groupadmin/*.yaml` files.

{{< image pathDark="/images/sunstone/common/dark/group_admin_view.png"
          path="/images/sunstone/common/light/group_admin_view.png" 
          alt="Sunstone group admin view" align="center" width="60%" mb="20px">}}

<a id="fireedge-cloud-view"></a>

### Cloud View

This is a simplified view mainly intended for end users that just require a portal where they can provision new Virtual Machines easily from pre-defined Templates. For more information about this view, please check the `/etc/one/fireedge/sunstone/views/cloud/*.yaml` files.

{{< image pathDark="/images/sunstone/common/dark/cloud_view_dashboard.png"
          path="/images/sunstone/common/light/cloud_view_dashboard.png" 
          alt="Sunstone cloud view dashboard" align="center" width="90%" mb="20px">}}

<a id="fireedge-suns-views-configuring-access"></a>

## Configuring Access to the Views

By default, the `admin` view is only available to the `oneadmin` group. New users will use the default `cloud` view. The views assigned to a given group can be defined in the group creation form or by updating an existing group to implement different OpenNebula models. For more information on the different OpenNebula models please check the [Understanding OpenNebula documentation]({{% relref "../../../getting_started/understand_opennebula/opennebula_concepts/cloud_access_model_and_roles#understand" %}}).

{{< image pathDark="/images/sunstone/common/dark/group_view_configuration.png"
          path="/images/sunstone/common/light/group_view_configuration.png" 
          alt="Sunstone group view configuration" align="center" width="90%" mb="20px">}}

<a id="fireedge-suns-views-usage"></a>

## Usage

FireEdge Sunstone users can change their current view from the top-right drop-down menu (the one with four squares):

{{< image pathDark="/images/sunstone/common/dark/view_dropdown.png"
          path="/images/sunstone/common/light/view_dropdown.png" 
          alt="Sunstone view dropdown" align="center" width="60%" mb="20px">}}

These options are saved in the group template, as well as other hidden settings. If not defined, defaults views from `/etc/one/fireedge/sunstone/views/sunstone-views.yaml` are taken.

<a id="fireedge-sunstone-views-define-new"></a>

## Views configuration on `sunstone-views.yaml`

The file `sunstone-views.yaml` configures:

- Default views if a group does not have [Sunstone configuration attributes]({{% relref "manage_groups#groupwise-configuration-attributes" %}}):
  ```yaml
  # This file describes which Sunstone views are available according to the
  # primary group a user belongs to
  groups:
      oneadmin:
          - admin
          - user
  default:
      - user
  ```

  Users that belong to oneadmin group will use admin and user views while users that do not belong to oneadmin group will use user view only (that configuration only applies if the group that the user belongs to [does not have the FIREEDGE attribute on the template]({{% relref "manage_groups#groupwise-configuration-attributes" %}})):
- Name and description that will be showed on Sunstone:
  ```yaml
  # Name and description of each view.
  #
  # More views could be added creating a new object under views attribute.
  # Example:
  #   customview:
  #     name: Name of the custom view
  #     description: Description of the custom view

  views:
    admin:
      name: groups.view.admin.name
      description: groups.view.admin.description
    cloud:
      name: groups.view.cloud.name
      description: groups.view.cloud.description
    groupadmin:
      name: groups.view.groupadmin.name
      description: groups.view.groupadmin.description
    user:
      name: groups.view.user.name
      description: groups.view.user.description
    customview:
      name: Custom view
      description: Description for custom view
  ```

  The views attribute is used to add readable names and description to the views. If we use the previous configuration, the result on Sunstone will be:

  {{< image pathDark="/images/sunstone/common/dark/custom_group_views.png"
            path="/images/sunstone/common/light/custom_group_views.png" 
            alt="Sunstone custom group views" align="center" width="80%" mb="20px">}}
            
## Defining a New OpenNebula Sunstone View or Customizing an Existing One

View definitions are placed in the `/etc/one/fireedge/sunstone/views` directory. Each view is defined by a folder which contains one yaml file for each tab that will be in the view. The structure of this folder will be as follows:

```default
/etc/one/fireedge/sunstone/views
|-- admin/
|   |-- acl-tab.yaml                   <--- Enable ACL tab and define its actions
|   |-- backupjobs-tab.yaml            <--- Enable Backup jobs tab and define its actions
|   |-- backup-tab.yaml                <--- Enable Backup tab and define its actions
|   |-- cluster-tab.yaml               <--- Enable Cluster tab and define its actions
|   |-- datastore-tab.yaml             <--- Enable Datastore tab and define its actions
|   |-- file-tab.yaml                  <--- Enable Files tab and define its actions
|   |-- group-tab.yaml                 <--- Enable Groups tab and define its actions
|   |-- host-tab.yaml                  <--- Enable Host tab and define its actions
|   |-- image-tab.yaml                 <--- Enable Images tab and define its actions
|   |-- marketplace-app-tab.yaml       <--- Enable Apps tab and define its actions
|   |-- marketplace-tab.yaml           <--- Enable Marketplace tab and define its actions
|   |-- sec-group-tab.yaml             <--- Enable Security groups tab and define its actions
|   |-- service-tab.yaml               <--- Enable Service tab and define its actions
|   |-- service-template-tab.yaml      <--- Enable Service template tab and define its actions
|   |-- support-tab.yaml               <--- Enable Support tab and define its actions
|   |-- user-tab.yaml                  <--- Enable User tab and define its actions
|   |-- vdc-tab.yaml                   <--- Enable VDC tab and define its actions
|   |-- vm-group-tab.yaml              <--- Enable Virtual Machine groups tab and define its actions
|   |-- vm-tab-tab.yaml                <--- Enable Virtual Machine tab and define its actions
|   |-- vm-template-tab.yaml           <--- Enable Virtual Machine templates tab and define its actions
|   |-- vnet-tab.yaml                  <--- Enable Virtual Networks tab and define its actions
|   |-- vnet-template-tab.yaml         <--- Enable Virtual Networks templates tab and define its actions
|   |-- vrouter-tab.yaml               <--- Enable Virtual Router tab and define its actions
|   |-- vrouter-template-tab.yaml      <--- Enable Virtual Router template tab and define its actions
|   |-- zone-tab.yaml                  <--- Enable Zone tab and define its actions
|-- user/
|   |-- backup-tab.yaml                <--- Enable Backup tab and define its actions
|   |-- file-tab.yaml                  <--- Enable Files tab and define its actions
|   |-- image-tab.yaml                 <--- Enable Images tab and define its actions
|   |-- marketplace-app-tab.yaml       <--- Enable Apps tab and define its actions
|   |-- sec-group-tab.yaml             <--- Enable Security groups tab and define its actions
|   |-- vm-tab-tab.yaml                <--- Enable Virtual Machine tab and define its actions
|   |-- vm-template-tab.yaml           <--- Enable Virtual Machine templates tab and define its actions
|   |-- vnet-tab.yaml                  <--- Enable Virtual Networks tab and define its actions
|-- groupadmin/
|   |-- backup-tab.yaml                <--- Enable Backup tab and define its actions
|   |-- file-tab.yaml                  <--- Enable Files tab and define its actions
|   |-- group-tab.yaml                 <--- Enable Groups tab and define its actions
|   |-- image-tab.yaml                 <--- Enable Images tab and define its actions
|   |-- marketplace-app-tab.yaml       <--- Enable Apps tab and define its actions
|   |-- sec-group-tab.yaml             <--- Enable Security groups tab and define its actions
|   |-- user-tab.yaml                  <--- Enable User tab and define its actions
|   |-- vm-tab-tab.yaml                <--- Enable Virtual Machine tab and define its actions
|   |-- vm-template-tab.yaml           <--- Enable Virtual Machine templates tab and define its actions
|   |-- vnet-tab.yaml                  <--- Enable Virtual Networks tab and define its actions
|-- cloud/
|   |-- vm-tab-tab.yaml                <--- Enable Virtual Machine tab and define its actions
|   |-- vm-template-tab.yaml           <--- Enable Virtual Machine templates tab and define its actions
`-- sunstone-views.yaml
...
```

{{< alert title="Note" type="info" >}}
The easiest way to create a custom view is to copy the admin folder and modify or delete tab files as needed. Also, configure sunstone-views.yaml if needed.{{< /alert >}} 

<a id="fireedge-sunstone-views-custom"></a>

### Tabs Customization

The contents of a tab file are organized in six sections:

* resource: Name of the resource.
* features: Which features are enabled on this tab.
* actions: Which buttons are visible to operate over the resources.
* filters: List of criteria to filter the resources.
* info-tabs: Which info tabs are used to show extended information.
* dialogs: Enable or disable different actions on a dialog that is enabled in the actions section.

Each section has some attributes that can be disabled or enabled by changing their value to false or true.

An example of a tab with the vm-template-tab.yaml file:

```yaml
# This file describes the information and actions available in the VM Template tab

# Resource

resource_name: "VM-TEMPLATE"

# Features - Enable features on vm templates

features:

  # True to hide the CPU setting in the dialogs
  hide_cpu: false

  # False to not scale the CPU.
  # An integer value would be used as a multiplier as follows:
  #     CPU = cpu_factor * VCPU
  # Set it to 1 to tie CPU and vCPU.
  cpu_factor: false

# Actions - Which buttons are visible to operate over the resources

actions:
  create_dialog: true
  import_dialog: true
  update_dialog: true
  instantiate_dialog: true
  create_app_dialog: true
  clone: true
  delete: true
  chown: true
  chgrp: true
  lock: true
  unlock: true
  share: true
  unshare: true
  edit_labels: true

# Filters - List of criteria to filter the resources

filters:
  label: true
  owner: true
  group: true
  locked: true
  vrouter: true


# Info Tabs - Which info tabs are used to show extended information

info-tabs:
  info:
    enabled: true
    information_panel:
      enabled: true
      actions:
        rename: true
    permissions_panel:
      enabled: true
      actions:
        chmod: true
    ownership_panel:
      enabled: true
      actions:
        chown: true
        chgrp: true

  template:
    enabled: true

# Dialogs - Enable or disable different actions on a dialog that it is enabled on the actions section

dialogs:
  instantiate_dialog:
    information: true
    ownership: true
    capacity: true
    vm_group: true
    network: true
    storage: true
    placement: true
    sched_action: true
    booting: true
    backup: true
  create_dialog:
    ownership: true
    capacity: true
    showback: true
    vm_group: true
    network: true
    storage: true
    placement: true
    input_output: true
    sched_action: true
    context: true
    booting: true
    numa:
      enabled: true
      not_on:
        - lxc
    backup: true
```

### Create new view

To create a new view:

> 1. Create a folder with the name of the view in `/etc/one/fireedge/sunstone/views`.
> 2. Add the yaml files for each tab that the view will show.
> 3. Configure `sunstone-views.yaml` if needed.
> 4. Update or create a group to use the new view.
