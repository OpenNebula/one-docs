---
title: "Sunstone Labels"
linkTitle: "Labels"
date: "2025-02-17"
description:
categories:
pageintoc: "48"
tags:
weight: "4"
---

<a id="sunstone-labels"></a>

<!--# Sunstone Labels -->

Labels can be defined for most of the OpenNebula resources from the Admin view.

Depending on the type of label used, _the label information will be stored under either the_ **user** _or_ **group** _template_.

{{< image pathDark="/images/sunstone/labels/dark/labels_dropdown.png"
          path="/images/sunstone/labels/light/labels_dropdown.png" 
          alt="Sunstone labels" align="center" width="90%" mb="20px">}}

This feature enables the possibility to _group the different resources_ under a given label and filter them in the Admin and Cloud views. The user will be able to easily find the template to instantiate __or select a set of resources_ to apply a given action.

## Label creation

To create a label, select one or more resources, then press the **+ Create New** button.

{{< image pathDark="/images/sunstone/labels/dark/create_new_label.png"
          path="/images/sunstone/labels/light/create_new_label.png" 
          alt="Sunstone create new label" align="center" width="90%" mb="20px">}}

This will open the **New Label** modal, which can be used to create user and group labels.

{{< image pathDark="/images/sunstone/labels/dark/new_label_dialog.png"
          path="/images/sunstone/labels/light/new_label_dialog.png" 
          alt="Sunstone create new label" align="center" width="60%" mb="20px">}}

{{< alert title="Warning" type="warning" >}}
Only group admins can apply and create group labels. However they will still be visible to all members of the group.{{< /alert >}}

## System labels

In order to create a set of labels that will be displayed to all users across all groups, you can define a public group, which will be used to store this information.

```bash
onegroup create "systemLabels"
#ID: 100
```

Then define a broad ACL, allowing all users to access this group with USE permissions:

```bash
oneacl create "* GROUP/#100 USE"
#ID: 10
```

Now all users will have USE permissions on this group, even though they aren't a member of this group. This means they can read the group's template data, which Sunstone uses when displaying labels to users. For more fine-grained control you can create different groups for storing labels and regulate their access level using the ACLs.

{{< alert title="Tip" type="info" >}}
In order to allow a user to control the system labels, they can be added to the "system labels" group with group admin permissions. {{< /alert >}} 

### Default labels

In order to define a set of default labels that will be used to populate either a user or groups template, one can use the following [configuration file](https://github.com/OpenNebula/one/blob/8eae7221946b5003fc9d354d358503828248c6fd/src/fireedge/etc/sunstone/default-labels.yaml).

For example to create a persistent system label, the following configuration can be applied:

```yaml
group:
  system labels:
    public:
      virtual-network:
        - "1"
        - "2"
    private:
      virtual-network:
        - "3"
        - "4"
```

{{< alert title="Tip" type="info" >}}
A user will only see the labels on the resources they have access to, meaning it is fine to be overly-expressive here, as this does not affect the resource permissions in any way.{{< /alert >}} 

The following list of resource names can be used:

* `marketplace-app`
* `backup`
* `datastore`
* `host`
* `image`
* `security-group`
* `virtual-data-center`
* `vrouter`
* `vrouter-template`
* `vm-template`
* `vm`
* `virtual-network`
* `backupjobs`

