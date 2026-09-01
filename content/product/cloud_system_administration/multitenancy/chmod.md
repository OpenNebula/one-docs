---
title: "Permissions and ACLs"
date: "2025-02-17"
description:
categories:
pageintoc: "118"
tags:
weight: "6"
---

<a id="chmod"></a>

<!--# Managing Permissions -->

Most OpenNebula resources have associated permissions for the **owner**, the users in the owner's **group**, and **others**. For each one of these groups there are three rights that can be set: **USE**, **MANAGE**, and **ADMIN**. These permissions are very similar to those of UNIX file system.

The resources with associated permissions are [Templates]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#vm-guide" %}}), [VMs]({{% relref "../../virtual_machines_operation/virtual_machines/vm_instances#vm-guide-2" %}}), [Images]({{% relref "../../virtual_machines_operation/virtual_machines/images#images" %}}) and [Virtual Networks]({{% relref "../../cluster_configuration/networking_system/manage_vnets#manage-vnets" %}}). The exceptions are [Users]({{% relref "manage_users#manage-users" %}}), [Groups]({{% relref "manage_users#manage-users" %}}) and [Hosts]({{% relref "../../cluster_configuration/hosts_and_clusters/overview#hostsubsystem" %}}).

## Managing Permission through the CLI

This is how the permissions look in the terminal:

```default
$ onetemplate show 0
TEMPLATE 0 INFORMATION
ID             : 0
NAME           : vm-example
USER           : oneuser1
GROUP          : users
REGISTER TIME  : 01/13 05:40:28

PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---

[...]
```

The previous output shows that for the Template 0, the owner user `oneuser1` has **USE** and **MANAGE** rights. Users in the group `users` have **USE** rights, and users that are not the owner or in the `users` group don’t have any rights over this Template.

You can check what operations are allowed with each of the **USE**, **MANAGE**, and **ADMIN** rights in the [xml-rpc reference documentation]({{% relref "../../../product/integration_references/system_interfaces/api#api" %}}). In general these rights are associated with the following operations:

* **USE**: Operations that do not modify the resource like listing it or using it (e.g., using an image or a Virtual Network). Typically you will grant **USE** rights to share your resources with other users of your group or with the rest of the users.
* **MANAGE**: Operations that modify the resource like stopping a Virtual Machine, changing the persistent attribute of an image, or removing a lease from a network. Typically you will grant **MANAGE** rights to users that will manage your own resources.
* **ADMIN**: Special operations that are typically limited to administrators, like updating the data of a Host or deleting a user group. Typically you will grant **ADMIN** permissions to those users with an administrator role.

{{< alert title="Important" type="info" >}}
Virtual Machine objects allow you to set the permission level required for each specific action, for example you may want to require USE for the delete-recreate operation instead of the default ADMIN right. You can [overrride the default permissions for each action]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-vm-operations" %}}) in oned.conf.{{< /alert >}} 

{{< alert title="Warning" type="warning" >}}
By default every user can update any permission group (owner, group, or other) with the exception of the admin bit. There are some scenarios where it would be advisable to limit the other set (e.g., OpenNebula Zones so users cannot break the group limits). In these situations the `ENABLE_OTHER_PERMISSIONS` attribute can be set to `NO` in `/etc/one/oned.conf` file{{< /alert >}} 

### Changing Permissions with chmod

The previous permissions can be updated with the chmod command. This command takes an octet as a parameter, following the [octal notation of the Unix chmod command](http://en.wikipedia.org/wiki/File_system_permissions#Octal_notation). The octet must be a three-digit base-8 number. Each digit, with a value between 0 and 7, represents the rights for the **owner**, **group**, and **other**, respectively. The rights are represented by these values:

- The **USE** bit adds 4 to its total (in binary 100)
- The **MANAGE** bit adds 2 to its total (in binary 010)
- The **ADMIN** bit adds 1 to its total (in binary 001)

Let’s see some examples:

```default
$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---

$ onetemplate chmod 0 664 -v
VMTEMPLATE 0: Permissions changed

$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : um-
OTHER          : u--

$ onetemplate chmod 0 644 -v
VMTEMPLATE 0: Permissions changed

$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : u--

$ onetemplate chmod 0 607 -v
VMTEMPLATE 0: Permissions changed

$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : uma
```

### Setting Default Permissions with umask

The default permissions given to newly created resources are:

- 666 for regular users
- 660 for regular users if `ENABLE_OTHER_PERMISSIONS` attribute is set to `NO` in `/etc/one/oned.conf`
- 777 for oneadmin user and group

These permissions are reduced by the UMASK, which can be set:

- Globally, with the **DEFAULT_UMASK** attribute in [oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf" %}})
- Individually for each user, using the [oneuser umask command]({{% relref "../../operation_references/command_line_interface/cli#cli" %}}).

These mask attributes work in a similar way to the [Unix umask command](http://en.wikipedia.org/wiki/Umask). The expected value is a three-digit base-8 number. Each digit is a mask that **disables** permissions for the **owner**, **group**, and **other**, respectively.

This table shows some examples:

|   umask |   permissions (octal) | permissions   |
|---------|-----------------------|---------------|
|     177 |                   600 | `um- --- ---` |
|     137 |                   640 | `um- u-- ---` |
|     113 |                   664 | `um- um- u--` |

## Managing Permissions in Sunstone

Sunstone offers a convenient way to manage resources permissions. This can be done by selecting resources from a view (for example the templates view) and clicking the Info tab. The dialog lets the user conveniently set the resource’s permissions.

{{< image pathDark="/images/sunstone/common/dark/permissions_panel.png"
        path="/images/sunstone/common/light/permissions_panel.png" 
        alt="Sunstone permissions panel" align="center" width="90%" mb="20px">}}

<a id="manage-locks"></a>

## Locking Resources

OpenNebula can lock actions on a resource to prevent unintended operations, e.g.,  to avoid accidentally deleting a VM. By default OpenNebula will lock all operations, but you can provide a fine grain lock by specifying the access level required by the action:

> - **USE**: locks all possible actions. You can use **ALL** as an equivalent keyword.
> - **MANAGE**: locks manage and admin actions.
> - **ADMIN**: locks admin actions.

The following resources can be locked:

> - `VM`
> - `NET`
> - `IMAGE`
> - `TEMPLATE`
> - `DOCUMENT`
> - `VROUTER`
> - `MARKETPLACEAPP`
> - `HOOK`
> - `VMGROUP`
> - `VNTEMPLATE`

For example:

```default
$ oneimage lock 2
$ oneimage delete 2
[one.image.delete] User [4] : Not authorized to perform MANAGE IMAGE [2].
```

```default
$ oneimage unlock 2
```

{{< alert title="Note" type="info" >}}
Only the owner of the lock may unlock the resource. The user ONEADMIN can override any lock.{{< /alert >}} 

<a id="manage-acl"></a>

# Managing ACL Rules

The ACL authorization system enables fine-tuning of the allowed operations for any user or group of users. Each operation generates an authorization request that is checked against the registered set of ACL rules. The core can then grant permission or reject the request.

This allows administrators to tailor the user roles according to their infrastructure needs. For instance, using ACL rules you could create a group of users that can see and use existing virtual resources, but not create any new ones. Or grant permissions to a specific user to manage Virtual Networks for some of the existing groups, but not to perform any other operation in your cloud. Some examples are provided at the end of this guide.

Please note: the ACL rules is an advanced mechanism. For most use cases, you should be able to rely on the built-in [resource permissions]({{% relref "#chmod" %}}) and the ACL Rules created automatically when a [group is created]({{% relref "manage_groups#manage-groups-permissions" %}}), and when [physical resources are added to a VDC]({{% relref "manage_vdcs#manage-vdcs" %}}).

## Understanding ACL Rules

Lets start with an example:

```default
#5 IMAGE+TEMPLATE/@103 USE+MANAGE #0
```

This rule grants the user with ID 5 the right to perform USE and MANAGE operations over all Images and Templates in the group with id 103.

The rule is split in four components, separated by a space:

- **User** component is composed only of an **ID definition**.
- **Resources** is composed of a list of **‘+’** separated resource types, **‘/’** and an **ID definition**.
- **Rights** is a list of Operations separated by the **‘+’** character.
- **Zone** is an **ID definition** of the Zones where the rule applies. This last part is optional and can be ignored unless OpenNebula is configured in a [federation]({{% relref "../../control_plane_configuration/data_center_federation/overview#introf" %}}).

The **ID definition** for a user in a rule is written as:

- `#<id> :` for individual IDs
- `@<id> :` for a group ID
- `* :` for All

The **ID definition** for a resource has the same syntax as the ones for users, but adding:

- `%<id> :` for cluster IDs

Some more examples:

This rule allows all users in group 105 to create new virtual resources:

```default
@105 VM+NET+IMAGE+TEMPLATE/* CREATE
```

The next one allows all users in the group 106 to use the Virtual Network 47. That means that they can instantiate VM templates that use this network.

```default
@106 NET/#47 USE
```

{{< alert title="Note" type="info" >}}
Note the difference between `* NET/#47 USE"` **vs** `* NET/@47 USE`

All users can use NETWORK with ID 47 **vs** All users can use NETWORKS belonging to the group whose ID is 47.{{< /alert >}}  

The following one allows users in group 106 to deploy VMs in Hosts assigned to the cluster 100

```default
@106 HOST/%100 MANAGE
```

## Managing ACL Rules via Console

The ACL rules are managed using the [oneacl command]({{% relref "../../operation_references/command_line_interface/cli#cli" %}}). The ‘oneacl list’ output looks like this:

```default
$ oneacl list
   ID     USER RES_VHNIUTGDCOZSvRMAPtB   RID OPE_UMAC  ZONE
    0       @1     V--I-T---O-S-------     *     ---c     *
    1        *     ----------Z--------     *     u---     *
    2        *     --------------MA---     *     u---     *
    3       @1     -H-----------------     *     -m--    #0
    4       @1     --N----D-----------     *     u---    #0
    5     @106     ---I---------------   #31     u---    #0
```

The rules shown correspond to the following ones:

```default
@1      VM+IMAGE+TEMPLATE+DOCUMENT+SECGROUP/*   CREATE  *
*       ZONE/*                                  USE     *
*       MARKETPLACE+MARKETPLACEAPP/*            USE     *
@1      HOST/*                                  MANAGE  #0
@1      NET+DATASTORE/*                         USE     #0
@106    IMAGE/#31                               USE     #0
```

The first five were created on bootstrap by OpenNebula and the last one was created using oneacl:

```default
$ oneacl create "@106 IMAGE/#31 USE"
ID: 5
```

The **ID** column identifies each rule’s ID. This ID is needed to delete rules, using **‘oneacl delete <id>’**.

The next column is **User**, which can be an individual user (#) or group (@) id; or all (\*) users.

The **Resources** column lists the existing Resource types initials. Each rule fills the initials of the resource type it applies to.

- `V : VM`
- `H : HOST`
- `N : NET`
- `I : IMAGE`
- `U : USER`
- `T : TEMPLATE`
- `G : GROUP`
- `D : DATASTORE`
- `C : CLUSTER`
- `O : DOCUMENT`
- `Z : ZONE`
- `S : SECURITY GROUP`
- `v : VDC`
- `R : VROUTER`
- `M : MARKETPLACE`
- `A : MARKETPLACEAPP`
- `P : VMGROUP`
- `t : VNTEMPLATE`
- `B : BACKUPJOB`

**RID** stands for Resource ID, it can be an individual object (#), group (@) or cluster (%) id; or all (\*) objects.

The **Operations** column lists the initials of allowed operations.

- `U : USE`
- `M : MANAGE`
- `A : ADMIN`
- `C : CREATE`

And the last column, **Zone**, shows the Zone(s) where the rule applies. It can be an individual Zone id (#), or all (\*) Zones.

## Managing ACLs via Sunstone

Sunstone offers a very intuitive and easy way of managing ACLs.

Select ACLs in the left-side menu to access a view of the current ACLs defined in OpenNebula:

{{< image pathDark="/images/sunstone/common/dark/sunstone_acl_list.png"
        path="/images/sunstone/common/light/sunstone_acl_list.png" 
        alt="Sunstone ACL list" align="center" width="90%" mb="20px">}}

This view is designed to easily understand what the purpose of each ACL is. You can create new ACLs in two different ways.

The first way is to use the **Create from string** functionality. Select **+ Create ACL** in the top right hand corner and select **From String** in the modal:

{{< image pathDark="/images/sunstone/common/dark/acl_from_string.png"
        path="/images/sunstone/common/light/acl_from_string.png" 
        alt="Sunstone ACL list" align="center" width="70%" mb="20px">}}

In the creation dialog you can type the string ACL rule in the same way as the CLI. After typing the rule, Sunstone will validate whether the string has the correct format and will show the user the meaning of the rule.

If we use the following example:

```default
#3 IMAGE+TEMPLATE/@100 USE+MANAGE #0
```

Sunstone will validate the rule and show its meaning:

{{< image pathDark="/images/sunstone/common/dark/create_acl_string_validation.png"
        path="/images/sunstone/common/light/create_acl_string_validation.png" 
        alt="Sunstone ACL string validation" align="center" width="90%" mb="20px">}}

If the rule does not have a valid format, Sunstone will show an error:

{{< image pathDark="/images/sunstone/common/dark/acl_rule_not_valid.png"
        path="/images/sunstone/common/light/acl_rule_not_valid.png" 
        alt="Sunstone ACL string validation" align="center" width="90%" mb="20px">}}

The alternative way to create a rule it is to use the **Create From Form** functionality. In this case, the user will be guided through different steps to create the rule. For example, to create the rule:

```default
#3 IMAGE+TEMPLATE/@100 USE+MANAGE #0
```

The following steps are needed:

- Click on **+ Create ACL** and choose **From Form** in the modal dialog:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form.png"
        path="/images/sunstone/common/light/create_acl_form.png" 
        alt="Sunstone create ACL from form" align="center" width="70%" mb="20px">}}

- Select whom the rule will apply to. It could be an individual user, a group, or all users:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_1.png"
        path="/images/sunstone/common/light/create_acl_form_1.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

- Select resources affected by the rule:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_2.png"
        path="/images/sunstone/common/light/create_acl_form_2.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

- Select resource owners. These could be an individual user, a group of users, a cluster, or all users:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_3.png"
        path="/images/sunstone/common/light/create_acl_form_3.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

- Select the allowed operations that this rule will enable:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_4.png"
        path="/images/sunstone/common/light/create_acl_form_4.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

- Select the Zone where the rule will apply. Optional unless OpenNebula is configured in a federation:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_5.png"
        path="/images/sunstone/common/light/create_acl_form_5.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

- Finally, the summary step will show the user the rule in string format and its meaning:

{{< image pathDark="/images/sunstone/common/dark/create_acl_form_6.png"
        path="/images/sunstone/common/light/create_acl_form_6.png" 
        alt="Sunstone create ACL from form" align="center" width="90%" mb="20px">}}

In both ways, to create the rule the user will have to click on the Finish button.

## Default ACL Rules for Group

When a new group is created, the following ACL rules are created:

```default
ID     USER RES_VHNIUTGDCOZSvRMAPtB   RID OPE_UMAC  ZONE
 6     @100     -H-----------------     *     -m--    #0
 7     @100     --N----------------     *     u---    #0
 8     @100     -------D-----------     *     u---    #0
 9     @100     V--I-T---O-S-R--P-B     *     ---c     *
```

Which means that users of this group have **MANAGE** permissions for Hosts and **USE** permissions for Virtual Networks and Datastores. Users can create Virtual Machines, Images, Templates, Documents, Security Groups, Virtual Routers, VMGroups, and Backup Jobs.

Default ACL rules for group admin are:

```default
ID     USER RES_VHNIUTGDCOZSvRMAPtB   RID OPE_UMAC  ZONE
10       #2     ----U--------------  @100     umac     *
11       #2     V-NI-T---O-S-R--P-B  @100     um--     *
12       #2     -------------R-----     *     ---c     *
13       #2     ------G------------  #100     -m--     *
```

## How Permission is Granted or Denied

{{< alert title="Note" type="info" >}}
Visit the [XML-RPC API reference documentation]({{% relref "../../../product/integration_references/system_interfaces/api#api" %}}) for a complete list of the permissions needed by each OpenNebula command.{{< /alert >}} 

For the internal Authorization in OpenNebula, there is an implicit rule:

- The oneadmin user or users in the oneadmin group are authorized to perform any operation.

If the resource is one of the following types: `VM`, `NET`, `IMAGE`, `TEMPLATE`, or `DOCUMENT`, the object’s permissions are checked. For instance, this is an example of the oneimage show output:

```default
$ oneimage show 2
IMAGE 2 INFORMATION
ID             : 2
[...]

PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---
```

The output above shows that the owner of the image has **USE** and **MANAGE** rights.

If none of the above conditions are true then the set of ACL rules is iterated until one of the rules allows the operation.

An important concept about the ACL set is that each rule adds new permissions and they can’t restrict existing ones: if any rule grants permission, the operation is allowed.

This is important because you have to be aware of the rules that apply to a user and the user's group. Consider the following example: if a user **#7** is in the group **@108**, with the following existing rule:

```default
@108 IMAGE/#45 USE+MANAGE
```

Then the following rule won’t have any effect:

```default
#7 IMAGE/#45 USE
```

<a id="manage-acl-vnet-reservations"></a>

### Special Authorization for Virtual Network Reservations

There is a special sub-type of Virtual Network: [reservations]({{% relref "../../virtual_machines_operation/virtual_machines_networking/self_provision#vgg-vn-reservations" %}}). For these Virtual Networks the ACL system makes the following exceptions:

- ACL rules that apply to ALL (\*) are ignored
- ACL rules that apply to a cluster (%) are ignored

The other ACL rules are enforced: individual (#) and group (@). The Virtual Network object’s permissions are also enforced as usual.
