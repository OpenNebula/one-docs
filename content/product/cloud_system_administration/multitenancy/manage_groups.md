---
title: "Groups"
date: "2025-02-17"
description:
categories:
pageintoc: "115"
tags:
weight: "3"
---

<a id="manage-groups"></a>

<a id="manage-users-groups"></a>

<!--# Managing Groups -->

A group in OpenNebula makes it possible to isolate users and resources. A user can see and use the [shared resources]({{% relref "chmod#chmod" %}}) of other users.

The group is an authorization boundary for the users, but you can also partition your cloud infrastructure and define which resources are available to each group by using [Virtual Data Centers (VDC)]({{% relref "manage_vdcs#manage-vdcs" %}}). You can read more about OpenNebula’s approach to VDCs and the cloud from the perspective of different user roles in the [Understanding OpenNebula]({{% relref "../../../getting_started/understand_opennebula/opennebula_concepts/cloud_access_model_and_roles#understand" %}}) guide.

## Adding and Deleting Groups

There are two special groups created by default. The `oneadmin` group allows any user in it to perform any operation, allowing different users to act with the same privileges as the `oneadmin` user. The `users` group is the default group where new users are created.

Your can use the `onegroup` command line tool to manage groups in OpenNebula. There are two groups created by default, `oneadmin` and `users`.

To create new groups:

```default
$ onegroup list
  ID NAME
   0 oneadmin
   1 users

$ onegroup create "new group"
ID: 100
```

The new group has ID 100 to differentiate the special groups from the user-defined ones.

{{< alert title="Note" type="info" >}}
When a new group is created, an ACL rule is also created to provide the default behavior, allowing users to create basic resources. You can learn more about ACL rules in [this guide]({{% relref "chmod#manage-acl" %}}), but you don’t need any further configuration to start using the new group.{{< /alert >}} 

## Adding Users to Groups

Use the `oneuser chgrp` command to assign users to groups:

```default
$ oneuser chgrp -v regularuser "new group"
USER 1: Group changed

$ onegroup show 100
GROUP 100 INFORMATION
ID             : 100
NAME           : new group

USERS
ID              NAME
1               regularuser
```

To delete a user from a group, just move the user back to the default `users` group.

<a id="manage-groups-permissions"></a>

## Admin Users and Allowed Resources

Upon group creation, a special admin user account can be defined. This admin user will only have administrative privileges for the new group, not for all the resources in the OpenNebula cloud as the ‘oneadmin’ group users have.

Another aspect that can be controlled when a group is created or updated is the type of resources that group users will be allowed to create or view.

In Sunstone, these permissions are configured in the **Permissions** step of the group creation and update forms. Saving the form creates or updates the corresponding ACL rules automatically, so the ACL tab does not need to be used for these standard group permissions.

Creation permissions can also be configured through the CLI. In this case, details of the group are passed to the `onegroup create` command as arguments. This table lists the description of said arguments.

| Argument            | M / O     | Value              | Description                                                                  |
|---------------------|-----------|--------------------|------------------------------------------------------------------------------|
| -n, –name name      | Mandatory | Any string         | Name for the new group                                                       |
| -u, –admin_user     | Optional  | Any string         | Creates an admin user for the group with the given name                      |
| -p, –admin_password | Optional  | Any string         | Password for the admin user of the group                                     |
| -d, –admin_driver   | Optional  | Any string         | Auth driver for the admin user of the group                                  |
| -r, –resources      | Optional  | “+” separated list | Which resources can be created by group users (VM+IMAGE+TEMPLATE by default) |

An example:

```default
$ onegroup create --name groupA \
--admin_user admin_userA --admin_password somestr \
--resources TEMPLATE+VM
```
{{< image
  pathDark="/images/sunstone/groups/dark/create_group.png"
  path="/images/sunstone/groups/light/create_group.png"
  alt="Create group" align="center" width="90%" mb="20px"
>}}

<a id="add-admin-user-to-group"></a>

## Add Admin Users to an Existing Group

Any user can be configured to be Admin of a group with the commands `onegroup addadmin` and `deladmin`.

{{< image
  pathDark="/images/sunstone/groups/dark/edit_administrators.png"
  path="/images/sunstone/groups/light/edit_administrators.png"
  alt="Edit administrators" align="center" width="90%" mb="20px"
>}}

<a id="manage-groups-virtual-resources"></a>

## Managing Groups and Virtual Resources

You can make the following virtual resources available to group users:

* [Virtual Machine Templates]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#vm-guide" %}})
* [Service Templates]({{% relref "../../virtual_machines_operation/multi-vm_workflows/appflow_use_cli#appflow-use-cli" %}})
* [Images]({{% relref "../../virtual_machines_operation/virtual_machines/images#images" %}})
* [Files & Kernels]({{% relref "../../virtual_machines_operation/virtual_machines/images#img-guide-kernel-and-ramdisk" %}})

To make a virtual resource owned by oneadmin available to users of the new group, you have two options:

* Change the resource’s group and give it `GROUP USE` permissions. This will make the resource available only to users in that group. The recommended practice to assign golden resources to groups is to first clone the resource and then assign it to the desired group for users’ consumption.
* Leave the resource in the oneadmin group and give it `OTHER USE` permissions. This will make the resource available to every user in OpenNebula.

{{< image
  pathDark="/images/sunstone/groups/dark/change_template_group.png"
  path="/images/sunstone/groups/light/change_template_group.png"
  alt="Edit administrators" align="center" width="90%" mb="20px"
>}}

The Virtual Machine and Service Templates are visible to the group users when they want to create a new VM or Service. The Images (including File Images) used by those Templates are not visible to the users but must be also made available, otherwise the VM creation will fail with an error message similar to this one:

```default
[TemplateInstantiate] User [6] : Not authorized to perform USE IMAGE [0].
```

You can read more about OpenNebula permissions in the [Managing Permissions]({{% relref "chmod#chmod" %}}) and [Managing ACL Rules]({{% relref "chmod#manage-acl" %}}) guides.

## Resource Sharing

When a group is created or updated, the cloud administrator can select the resource types that group users will be allowed to view when those resources belong to the same group. These options are available under **View** in the **Permissions** step. Saving the form creates or updates the corresponding ACL rules automatically. Users will be able to access and list the selected resources, but they will not be able to manage them.

{{< image
  pathDark="/images/sunstone/groups/dark/group_permissions.png"
  path="/images/sunstone/groups/light/group_permissions.png"
  alt="Edit administrators" align="center" width="90%" mb="20px"
>}}

<a id="manage-users-primary-and-secondary-groups"></a>

## Primary and Secondary Groups

With the commands `oneuser addgroup` and `delgroup` the administrator can add or delete secondary groups. Users assigned to more than one group will see the resources from all their groups. e.g., a user in the testing and production groups will see VMs from both groups.

The group set with `chgrp` is the primary group and resources (Images, VMs, etc.) created by a user will belong to this primary group. Users can change their primary group to any of their secondary groups without the intervention of an administrator, using `chgrp` again.

<a id="groupwise-configuration-attributes"></a>

## Group-wise Configuration Attributes

When a group is created you can define specific configuration aspects for the group users. These include:

* **Sunstone:** Allow users and group admins to access specific views. The configuration attributes are stored in the group template in the `FIREEDGE` attribute:

| Attribute                | Description                                  |
|--------------------------|----------------------------------------------|
| DEFAULT_VIEW             | Default Sunstone view for regular users      |
| VIEWS                    | List of available views for regular users    |
| GROUP_ADMIN_DEFAULT_VIEW | Default Sunstone view for group admin users  |
| GROUP_ADMIN_VIEWS        | List of available views for the group admins |

The views are defined by a comma-separated list of group names. By default the following views are defined: `groupadmin, cloud, admin, user`

For example:

```default
FIREEDGE=[
  DEFAULT_VIEW = "cloud",
  VIEWS        = "cloud"
  GROUP_ADMIN_DEFAULT_VIEW = "groupadmin",
  GROUP_ADMIN_VIEWS = "groupadmin,cloud",
]
```

* **OpenNebula Core:** Set specific attributes to control certain operations. The configuration attributes are stored in the group template in the `OPENNEBULA` attribute:

| Attribute                    | Description                                                                                                                      |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| DEFAULT_IMAGE_PERSISTENT     | Control the default value for the PERSISTENT attribute on image creation <br/>(clone and disk save-as).                          |
| DEFAULT_IMAGE_PERSISTENT_NEW | Control the default value for the PERSISTENT attribute on image creation <br/>(only new images).                                 |
| API_LIST_ORDER               | Sets order (by ID) of elements in list API calls (e.g. onevm list).<br/>Values: ASC (ascending order) or DESC (descending order) |

The Group template can be used to customize the access level of the `VM_USE_OPERATIONS`, `VM_MANAGE_OPERATIONS` and `VM_ADMIN_OPERATIONS`. For a description of these attributes see [VM Operations Permissions]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-vm-operations" %}})

{{< alert title="Note" type="info" >}}
These values can be overwritten for each user by placing the desired values in the user template.{{< /alert >}} 

If the values are not set, the defaults defined in `oned.conf` are used.

For example:

```default
OPENNEBULA = [
  DEFAULT_IMAGE_PERSISTENT     = "YES",
  DEFAULT_IMAGE_PERSISTENT_NEW = "NO"
]
```

<a id="manage-groups-sunstone"></a>

## Managing Groups in Sunstone

All the described functionality is available graphically using [Sunstone]({{% relref "../../operation_references/opennebula_services_configuration/fireedge#fireedge-setup" %}}):

{{< image
  pathDark="/images/sunstone/groups/dark/sunstone_group_list.png"
  path="/images/sunstone/groups/light/sunstone_group_list.png"
  alt="Sunstone group list" align="center" width="90%" mb="20px"
>}}

In the user’s menu the groups where the user can filter all system resources by `group` appear. When you filter by group, you also change the effective group of the user.

There is the option `Show all` to see all system resources, the option `Show all owned by the user or his groups` to see all resources that belong to the user or one of the user's groups, and the option `Show all owned by the user` to see all resources that belong to the user.

This allows users to work more comfortably on projects by isolating the resources belonging to one group from others.

{{< image
  pathDark="/images/sunstone/groups/dark/group_filters.png"
  path="/images/sunstone/groups/light/group_filters.png"
  alt="Sunstone group filters" align="center" width="90%" mb="20px"
>}}
