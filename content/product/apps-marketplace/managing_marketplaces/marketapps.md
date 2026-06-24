---
title: "Managing Marketplace Appliances"
date: "2025-02-17"
description:
categories:
pageintoc: "196"
tags:
weight: "2"
---

> <a id="marketapp"></a>

<!--# Managing MarketPlace Appliances -->

A Marketplace Appliance is a generic resource (an entry on the marketplaceapp pool) that can be of any of the following three types:

* *Image*, a single Image, optionally including a VM template.
* *VM*, a VM template referring to one or more images.
* *Service*, a multi-VM service composed of one or more templates associated with images.

This guide introduces the process to create and manage Marketplace Appliances.

## Exploring Marketplace Appliances

You can list the Marketplace Appliances (apps) with `onemartketapp list` command. OpenNebula pre-configures some Public Marketplaces so in a standard installation you should see some apps already:

```default
$ onemarketapp list
  ID NAME                          VERSION  SIZE STAT TYPE  REGTIME MARKET     ZONE
    74 Alpine Linux 3.20                     6.10.0-2-2  256M  rdy  img 05/14/24 OpenNebula    0
    73 Amazon Linux 2023                     6.10.0-2-2   25G  rdy  img 05/14/24 OpenNebula    0
    72 Service MinIO                         6.10.0-2-2  2.2G  rdy  img 05/31/24 OpenNebula    0
    71 Service Virtual Router                6.10.0-2-2    2G  rdy  img 05/15/24 OpenNebula    0
    70 Service WordPress - KVM               6.10.0-2-2   10G  rdy  img 05/14/24 OpenNebula    0
    69 Service Harbor                        6.10.0-2-2   20G  rdy  img 05/14/24 OpenNebula    0
    68 Custom via netboot.xyz                  2.0.32-1    0M  rdy  tpl 10/27/21 OpenNebula    0
    67 Ttylinux - KVM                        1.0-1.2019  200M  rdy  img 01/01/70 OpenNebula    0
    ...
    23 FreeBSD 13                            6.10.0-2-2    4G  rdy  img 05/14/24 OpenNebula    0
    22 Alpine Linux 3.18                     6.10.0-2-2  256M  rdy  img 05/14/24 OpenNebula    0
    21 Oracle Linux 9                        6.10.0-2-2   37G  rdy  img 05/14/24 OpenNebula    0
    20 ALT Linux p9                          6.8.1-1-20  1.5G  rdy  img 02/01/24 OpenNebula    0
```

To get more details of an Appliance use the `show` option, for example:

```default
$ onemarketapp show 0
MARKETPLACE APP 270 INFORMATION
ID             : 270
NAME           : Service Kubernetes 1.18 - KVM
TYPE           : IMAGE
USER           : oneadmin
GROUP          : oneadmin
MARKETPLACE    : OpenNebula Public
STATE          : rdy
LOCK           : None

PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : u--

DETAILS
SOURCE         : https://marketplace.opennebula.io/appliance/547ecdff-f392-43b9-abc9-5f10a9fa7aff/download/0
MD5            : 398274dadc7ff0f527d530362809f031
PUBLISHER      :
REGISTER TIME  : Fri Nov  6 13:11:22 2020
VERSION        : 1.18.10-5.12.0.2-1.20201106.2
DESCRIPTION    : Appliance with preinstalled Kubernetes for KVM hosts
SIZE           : 4G
ORIGIN_ID      : -1
FORMAT         : qcow2

IMPORT TEMPLATE
DEV_PREFIX="vd"
TYPE="OS"

MARKETPLACE APP TEMPLATE
APPTEMPLATE64="REVWX1BSRUZJWD0idmQiClRZUEU9Ik9TIgo="
DESCRIPTION="Appliance with preinstalled Kubernetes for KVM hosts"
IMPORT_ID="547ecdff-f392-43b9-abc9-5f10a9fa7aff"
LINK="https://marketplace.opennebula.io/appliance/547ecdff-f392-43b9-abc9-5f10a9fa7aff"
PUBLISHER="OpenNebula Systems"
TAGS="kubernetes, service, centos"
VERSION="1.18.10-5.12.0.2-1.20201106.2"
VMTEMPLATE64="Q09OVEVYVCA9IFsgTkV...2x1c3RlcikiXQo="
```

## Create a New Marketplace Appliance

{{< alert title="Important" type="info" >}}
You can only create new Marketplace Appliances on **Private Marketplaces**{{< /alert >}} 

A Marketplace Appliance can be created in (or imported into) a Marketplace out of an existing Image, Virtual Machine, Virtual Machine Template, or Multi-VM Service Template. The following table lists the command to use for each case:

| Object                   | Command                                | Description                                                                                      |
|--------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------|
| Image                    | `onemarketapp create`                  | Imports an Image into the Marketplace, and optionally a VM template to use it                    |
| Virtual Machine          | `onemarketapp vm import`               | Imports a VM into the Marketplace, and recursively all the disks associated                      |
| Virtual Machine Template | `onemarketapp vm-template import`      | Imports a VM template into the Marketplace and recursively all the images associated.            |
| Service Template         | `onemarketapp service-template import` | Imports a service template into the Marketplace and recursively all the VM templates associated. |

These commands use some common options described below:

| Parameter                | Description                                |
|--------------------------|--------------------------------------------|
| `--name name`            | Name of the new Marketplace Application    |
| `--vmname name`          | Name for the new VM Template               |
| `--market market_id`     | Marketplace to import the Application      |
| `--yes`                  | Import everything                          |
| `--no`                   | Import just the main template              |
| `--template template_id` | Use this template with the imported image  |

For example, if you want to import an exiting Image (e.g., with `ID` 0) into the `Backup` Marketplace, you could use:

```default
$ onemarketapp create --name 'Alipe-Vanilla' --image 0 --market "Backup"
ID: 40
```

Importing VMs with multiple disks or Multi-VM Services can be a complex task. In this case the `onemarketapp` command provides an interactive process, although they can run in batch mode (see below). The process of importing a Multi-VM Service is illustrated in the following example:

```default
$ onemarketapp service-template import 0
Do you want to import VM templates too? (yes/no): yes

Available Marketplaces (please enter ID)
- 100: testmarket

Where do you want to import the service template? 100

Available Marketplaces for roles (please enter ID)
- 100: testmarket

Where do you want to import `RoleA`? 100
ID: 440
ID: 441
ID: 442
```

An example of a VM template would be similar to:

```default
$ onemarketapp vm-template import 0
Do you want to import images too? (yes/no): yes

Available Marketplaces (please enter ID)
- 100: testmarket

Where do you want to import the VM template? 100
ID: 443
ID: 444
```

You can use the parameter `--market` together with `--yes` or `--no` to run the command in batch mode:

```default
$ onemarketapp service-template import 0 --market 100 --yes
ID: 445
ID: 446
ID: 447
```

and for VM templates:

```default
$ onemarketapp vm-template import 0 --market 100 --yes
ID: 448
ID: 449
```

{{< alert title="Important" type="info" >}}
If a running VM doesn’t have the `TEMPLATE_ID` attribute set, it cannot be imported into the Marketplace.{{< /alert >}} 

{{< alert title="Note" type="info" >}}
NICs are marked as auto, so they can work when the Marketplace Application is exported to a OpenNebula cloud. If you have NIC_ALIAS in the template, NICs are **not** marked as auto, you need to select the network when you instantiate it.{{< /alert >}} 

{{< alert title="Warning" type="warning" >}}
To avoid clashing names, if no name is specified a hash is added at the end of the main object name. Sub-objects like disks or VM templates in the case of Service Template, always have the hash.{{< /alert >}} 

### Marketplace Appliance Attributes

You can update several attributes of a Marketplace Appliance with the `onemarketapp update` command. For your reference the table below summarizes them:

| Attribute       | Description                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------------|
| `NAME`          | Name of the Appliance.                                                                           |
| `ORIGIN_ID`     | The ID of the source image. -1 if not defined.                                                   |
| `TYPE`          | `IMAGE`, `VMTEMPLATE`, `SERVICE_TEMPLATE`.                                                       |
| `DESCRIPTION`   | Text description of the Marketplace Appliance.                                                   |
| `PUBLISHER`     | If not provided, the username will be used.                                                      |
| `VERSION`       | A string indicating the Marketplace Appliance version.                                           |
| `VMTEMPLATE64`  | Creates this template (encoded in base64) pointing to the base image.                            |
| `APPTEMPLATE64` | This is the associated template (encoded in base64) that will be added to the registered object. |

## Downloading a Marketplace Appliance into your Cloud or Desktop

The command that exports (downloads) the Marketplace Appliance is `onemarketapp export`, which will return the ID of the new Image **and** the ID of the new associated template. If no template has been defined, it will return -1. For example:

```default
$ onemarketapp export 40 from_t1app -d 1
IMAGE
    ID: 1
VMTEMPLATE
    ID: -1
```

When an appliance is downloaded from the Marketplace, short hash values may be appended to object names to ensure uniqueness. This convention also applies to additional objects created during the download process, such as virtual machine templates and disks. To keep names easily identifiable, the original object name is preserved and placed before the appended hash and index. For example:
```default
$ oneimage list
  ID USER     GROUP    NAME                                                                       DATASTORE     SIZE TYPE PER STAT RVMS
  2 oneadmin oneadmin Windows VM Template_0-Contextualization Packages-aa38438e4a-2              default         2M CD    No rdy     0
  1 oneadmin oneadmin Windows VM Template_0-Windows VirtIO Drivers - v0.1.285-e3cf06243b-1       default       754M CD    No rdy     0
  0 oneadmin oneadmin Windows VM Template_0-Empty disk-fcee73d9e5-0                              default         5G OS    No rdy     0
```

<a id="marketapp-download"></a>

You can also download an app to a standalone file in your desktop:

```default
$ onemarketapp download 40 /path/to/app
```

{{< alert title="Warning" type="warning" >}}
This command requires that the ONE_SUNSTONE environment variable is set. Read [here]({{% relref "../../../product/cloud_system_administration/multitenancy/manage_users#manage-users-shell" %}}) for more information.{{< /alert >}} 

## Additional Commands

Like any other OpenNebula Resource, Marketplace Appliances respond to the base actions, namely:

* delete
* update
* chgrp
* chown
* chmod
* enable
* disable

Please take a look at the CLI reference to see how to use these actions. These options are also available in Sunstone.

## Using Sunstone to Manage Marketplace Appliances

You can also import and export Marketplace Appliances using [Sunstone]({{% relref "../../../product/operation_references/opennebula_services_configuration/fireedge#fireedge" %}}). Select the Storage > Apps tab and there you will be able see the available Appliances in a user-friendly way.

![image](/images/show_marketplaceapp.png)
