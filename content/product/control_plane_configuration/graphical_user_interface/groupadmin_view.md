---
title: "Group Admin View"
date: "2025-02-17"
description:
categories:
pageintoc: "47"
tags:
weight: "3"
---

<a id="vdc-admin-view"></a>

<a id="group-admin-view"></a>

<!--# Group Admin View -->

The role of a **Group Admin is to manage all the virtual resources of the Group**, including the creation of new users. It’s like a limited version of the cloud administrator view. You can read more about OpenNebula’s approach to Groups and VDC’s from the perspective of different user roles in [Cloud Access Models and Roles]({{% relref "../../../getting_started/understand_opennebula/opennebula_concepts/cloud_access_model_and_roles#understand" %}}).

{{< image path="/images/group_admin_view/sunstone_groupadmin_dash.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

{{< alert title="Important!" type="info" >}} 
Group Admin is scoped to the administered group. For user management, this scope applies to users whose primary group is the administered group. Users that belong to a group only as a secondary group are not managed by the Group Admin of the primary group by default, since the user object is still owned by its primary group. Managing such users requires additional ACLs or actions from the cloud administrator.
{{< /alert >}}

## Manage Users

The Group Admin **can create new user accounts** that will belong to the same Group.

{{< image path="/images/group_admin_view/sunstone_groupadmin_create_user.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

They can also see the current resource usage of all the Group users.

{{< image path="/images/group_admin_view/sunstone_groupadmin_users.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

And **set quota limits** for each one of them. Read the Chapter about how to [Usage Quotas]({{% relref "../../cloud_system_administration/capacity_planning/quotas#quota-auth" %}}) for more information.

{{< image path="/images/group_admin_view/sunstone_groupadmin_edit_quota.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

## Manage Resources

The Group Admin can manage the Services, VMs, and Templates of other users in the Group.

{{< image path="/images/group_admin_view/sunstone_groupadmin_list_vms.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

## Create Resources

The Group Admin **can create new resources** in the same way as a regular user does from the [Cloud view]({{% relref "cloud_view#cloud-view" %}}). The creation wizard for the VMs and Services are similar in the `groupadmin` and `cloud` views.

{{< image path="/images/group_admin_view/sunstone_groupadmin_instantiate.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

## Prepare Resources for Other Users

Any user of the Cloud View or Group Admin View **can save the changes** made to a VM back to a new Template and use this Template to instantiate new VMs later. See the [VM persistency options in the Cloud View]({{% relref "cloud_view#cloudview-persistent" %}}) for more information.

The Group Admin **can also share** his own Saved Templates with the rest of the Group.

For example, the Group Admin can instantiate a clean VM prepared by the cloud administrator, install software needed by other users in his Group, save it in a new Template, and make it available for the rest of the Group.

{{< image path="/images/group_admin_view/sunstone_groupadmin_share_template.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

These shared templates will be listed to all the Group users in the VM creation wizard, marked as `group`. A Saved Template created by a regular user is only available for that user and is marked as `mine`.

{{< image path="/images/group_admin_view/sunstone_groupadmin_create_vm_templates_list.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

## Accounting and Showback

### Group Accounting and Showback

The Group info tab provides information about the **resources usage, accounting and showback** reports that can be generated. These records can be configured to report the usage per VM or per user for a specific range of time.

{{< image path="/images/group_admin_view/sunstone_groupadmin_group_acct.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

{{< image path="/images/group_admin_view/sunstone_groupadmin_group_showback.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

### User Accounting and Showback

The detail view of the user provides information on their usage of resources, from this view accounting reports can be also generated for this specific user.

{{< image path="/images/group_admin_view/sunstone_groupadmin_user_acct.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}

## Networking

Group administrators **can create** [Virtual Routers]({{% relref "../../virtual_machines_operation/virtual_machines_networking/vrouter#vrouter" %}}) **from Templates** prepared by the cloud administrator. These virtual routers can be used to connect two or more of the virtual networks assigned to the Group.

{{< image path="/images/group_admin_view/sunstone_groupadmin_create_vrouter.png" alt="Group Admin View" align="center" width="90%" mb="20px">}}
