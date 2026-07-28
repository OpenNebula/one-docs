---
title: "Affinity Groups"

description:
categories:
pageintoc: ""
tags:
weight: "5"
---

<a id="vmgroups"></a>

<!--# Virtual Machine Affinity -->

A VM Group defines a set of related VMs and associated placement constraints for the VMs in the group. A VM Group allows you to place together (or separately) certain VMs (or VM classes, called Roles). VM Groups will help you to optimize the performance (e.g., not placing all the CPU-bound VMs in the same Host) or improve the fault tolerance (e.g., not placing all your Front-ends in the same Host) of your multi-VM applications.

## Defining a VM Group

A VM Group consists of two parts: a set of Roles and a set of placement constraints for the Roles. In a VM Group, a Role defines a class of Virtual Machines that are subject to the same placement constraints and rules. Usually, you will put VMs implementing a given functionality of a multi-VM application in the same Role, e.g., the Front-ends or the database VMs. Additionally, you can define placement constraints for the VMs in the VM Group, with placement rules that can refer to the VMs within a Role or VMs across Roles.

A role is defined with the following attributes:

| Attribute           | Mandatory   | Description                                                                                  |
|---------------------|-------------|----------------------------------------------------------------------------------------------|
| `NAME`              | **YES**     | The name of the Role. It must be unique within the VM Group.                                 |
| `POLICY`            | **NO**      | Placement policy for the VMs of the Role. Possible values are: `AFFINED` and `ANTI_AFFINED`. |
| `HOST_AFFINED`      | **NO**      | Defines a set of Hosts (by their ID) where the VMs of the Role can be executed.              |
| `HOST_ANTI_AFFINED` | **NO**      | Defines a set of Hosts (by their ID) where the VMs of the Role cannot be executed.           |

You can impose additional placement constraints on the VMs of a Role by using the following attributes:

| Attribute      | Mandatory   | Description                                                                  |
|----------------|-------------|------------------------------------------------------------------------------|
| `AFFINED`      | **NO**      | List of Roles (comma-separated) whose VMs has to be placed in the same Host. |
| `ANTI_AFFINED` | **NO**      | List of Roles (comma-separated) whose VMs cannot be placed in the same Host. |

To create a VM Group, use the Sunstone web interface or create a template file following this example:

```default
$ cat ./vmg.txt

NAME = "multi-tier server"

ROLE = [
    NAME   = "front-end",
    POLICY = "ANTI_AFFINED"
]

ROLE = [
    NAME         = "apps",
    HOST_AFFINED = "2,3,4"
]

ROLE = [ NAME = "db" ]

AFFINED = "db, apps"

$ onevmgroup create ./vmg.txt
ID: 0
```

## Placement Policies

The following placement policies can be applied to the VMs of a VM Group.

### VM to Host Affinity

Specifies a set of Hosts where the VMs of a Role can be allocated. This policy is set on a Role basis using the `HOST_AFFINED` and `HOST_ANTI_AFFINED` attributes. Host affinity rules are compatible with any other rules applied to the Role VMs.

For example, if you want to place the VMs implementing the database for your application in high performance Hosts, you could use:

```default
ROLE = [
    NAME         = "database",
    HOST_AFFINED = "1,2,3,4"
]
```

### VM to VM Affinity

Specifies whether the VMs of a Role have to be placed together in the same Host (`AFFINED`) or scattered across different Hosts (`ANTI_AFFINED`). The VM to VM affinity is set per Role with the `POLICY` attribute.

For example, you may want to spread CPU-bound VMs across Hosts to prevent contention:

```default
ROLE = [
    NAME   = "workers",
    POLICY = "ANTI_AFFINED"
]
```

### Role to Role Affinity

Specifies whether the VMs of a Role have to be placed together or separately with the VMs of another Role. This useful to combine the Host-VM and VM-VM policies. Affinity rules for Roles are set with the `AFFINED` and `ANTI_AFFINED` attributes.

For example, consider that you need the VMs of a database to run together so they access the same storage. At the same time, you need all the backup VMs to run in a separate Host; and you need database and backups to also be in different Hosts. Finally, you may have some constraints about where the database and backups can run:

```default
ROLE = [
    NAME  = "databases",
    HOST_AFFINED = "1,2,3,4,5,6,7"
    POLICY = "AFFINED"
]

ROLE = [
    NAME = "backup",
    HOST_ANTI_AFFINED = "3,4"
    POLICY = "ANTI_AFFINED"
]

ANTI_AFFINED = "databases, backup"
```

{{< alert title="Important" type="info" >}}
Note that a Role policy has to be coherent with any Role-Role policy, i.e., a Role with an `ANTI_AFFINED` policy cannot be included in any `AFFINED` Role-Role rule.{{< /alert >}}

### Scheduler Configuration and Remarks

VM Groups are placed by dynamically generating the requirement (`SCHED_REQUIREMENTS`) of each VM and re-evaluating these expressions. Moreover, the following is also considered:

* The scheduler will look for a Host with enough capacity for an affined set of VMs. If there is no such Host all the affined VMs will remain pending.
* If new VMs are added to an affined Role, it will pick one of the Hosts where the VMs are running. By default, all should be running in the same Host but if you manually migrate a VM to another Host it will be considered feasible for the role.
* The scheduler does not have any synchronization point with the state of the VM group, it will start scheduling pending VMs as soon as they show up.
* Re-scheduling of VM Groups works as for any other VM, it will look for a different Host considering the placement constraints.

## Using a VM Group

Once you have defined your VM Group you can start adding VMs to it, either by picking a Role and VM group at instantiation, by setting it in the VM Template, or dynamically add VM Group for an existing VM. To apply a VM Group to your Virtual Machines either use the Sunstone wizard or set the `VM_GROUP` attribute:

```default
$ onetemplate update 0
...
VMGROUP = [ VMGROUP_NAME = "muilt-tier app", ROLE = "db" ]
```

You can also specify the `VM_GROUP` by its id (`VMGROUP_ID`), and in case of multiple groups with the same name you can select it by owner with `VMGROUP_UID`, as with any other resource in OpenNebula.

{{< alert title="Note" type="info" >}}
You can also add the `VMGROUP` attribute when a VM is created (`onevm create`) or when the associated template is instantiated (`onetemplate instantiate`). This way the same VM template can be associated with different Roles.{{< /alert >}}

<a id="dynamic-vmg"></a>

## Dynamic VM Group Management

You can dynamically add or remove a Virtual Machine from a VM Group without needing to recreate the VM or update its template.

To add a VM to a VM Group and Role:

```default
$ onevm vmgroup-add <vmid> <vmgroupid> <role>
```

If the Virtual Machine is already running on a Host, OpenNebula will check if the VM's current Host complies with the affinity rules of the target VM Group and Role. If the rules are not met, the operation will fail.

To remove a VM from its current VM Group:

```default
$ onevm vmgroup-del <vmid>
```

## VM Group Management

VM Groups can be updated to edit or add new rules. Currently only Role-to-Role rules can be updated if there are no VMs in the Roles. All base operations are supported for the VM Group object: `create`, `delete`, `chgrp`, `chown`, `chmod`, `update`, `rename`, `list`, `show`, `lock`, and `unlock`. For managing Roles, use `onevmgroup` commands `role-add`, `role-delete`, and `role-update`.

Note also that the same ACL/permission system is applied to VM Groups, so use access is required to place VMs in a group.

## Managing VM Groups with Sunstone

You can also manage VM Groups using [Sunstone]({{% relref "../../control_plane_configuration/graphical_user_interface/overview" %}}), through the VM Group tab.

{{< image
  pathDark="/images/capacity/dark/vmgroup-role-definition.png"
  path="/images/capacity/light/vmgroup-role-definition.png"
  alt="VM Group role definition" align="center" width="90%" mb="20px"
>}}

{{< image
  pathDark="/images/capacity/dark/vm-group-role-affinity.png"
  path="/images/capacity/light/vm-group-role-affinity.png"
  alt="VM Group role affinity" align="center" width="90%" mb="20px"
>}}
