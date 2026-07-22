---
title: "Datastores"
date: "2025-02-17"
description:
categories:
pageintoc: "68"
tags:
weight: "2"
---

<a id="datastores"></a>

<!--# Datastores -->

## Types

OpenNebula features three different datastore types:

* The **Image Datastore** stores the Image repository.
* The **System Datastore** holds disk for running Virtual Machines, usually cloned from the Image Datastore.
* The **Files & Kernels Datastore** to store plain files used in contextualization, or VM kernels used by some hypervisors.

By default, OpenNebula will create an image (`default`), system (`system`), and files datastore (`files`). These datastores are configured to use the SSH protocol to transfer images.  You can list the datastores in your cloud with the `onedatastore list` command:

```default
$ onedatastore list
  ID NAME                SIZE AVA CLUSTERS IMAGES TYPE DS      TM      STAT
   2 files                50G 86% 0             0 fil  fs      local   on
   1 default              50G 86% 0             2 img  fs      local   on
   0 system                 - -   0             0 sys  -       local   on
```

<a id="datastore-common"></a>

## Attributes

### Image and Files & Kernels Datastores

You can access the information about each datastore using the `onedatastore show` command. For example the information of your `default` datastore may look like:

```default
$ onedatastore show 1
DATASTORE 1 INFORMATION
ID             : 1
NAME           : default
USER           : oneadmin
GROUP          : oneadmin
CLUSTERS       : 0
TYPE           : IMAGE
DS_MAD         : fs
TM_MAD         : local
BASE PATH      : /var/lib/one//datastores/1
DISK_TYPE      : FILE
STATE          : READY

DATASTORE CAPACITY
TOTAL:         : 50G
FREE:          : 43.2G
USED:          : 6.8G
LIMIT:         : -

PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---

DATASTORE TEMPLATE
ALLOW_ORPHANS="YES"
CLONE_TARGET="SYSTEM"
DISK_TYPE="FILE"
DS_MAD="fs"
LN_TARGET="SYSTEM"
RESTRICTED_DIRS="/"
SAFE_DIRS="/"
TM_MAD="local"
TYPE="IMAGE_DS"

IMAGES
0
1
```

There are four important sections:

> * **General Information** includes basic information like the name, the file path of the datastore, or its type (`IMAGE`). It also includes the set of drivers (`DS_MAD` and `TM_MAD`) used to store and transfer images. In this example, the datastore uses a file-based driver (`DS_MAD="fs"`) and the Local protocol for transfers (`TM_MAD=local`).
> * **Capacity** includes basic usage metrics like total, used, and free space.
> * **Generic Attributes**, under `DATASTORE TEMPLATE` you can find configuration attributes and custom tags (see below).
> * **Images**, the list of images currently stored in this datastore.

{{< alert title="Note" type="info" >}}
The example above shows what a basic image datastore looks like. A Files and Kernels Datastore will look mostly the same but with different values in the type fields.{{< /alert >}} 

### System Datastore

In the case of System Datastore the information is similar:

```default
$ onedatastore show system
DATASTORE 0 INFORMATION
ID             : 0
NAME           : system
USER           : oneadmin
GROUP          : oneadmin
CLUSTERS       : 0
TYPE           : SYSTEM
DS_MAD         : -
TM_MAD         : local
BASE PATH      : /var/lib/one//datastores/0
DISK_TYPE      : FILE
STATE          : READY

DATASTORE CAPACITY
TOTAL:         : -
FREE:          : -
USED:          : -
LIMIT:         : -

PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---

DATASTORE TEMPLATE
ALLOW_ORPHANS="YES"
DISK_TYPE="FILE"
DS_MIGRATE="YES"
RESTRICTED_DIRS="/"
SAFE_DIRS="/var/tmp"
SHARED="NO"
TM_MAD="local"
TYPE="SYSTEM_DS"

IMAGES
```

Note the differences in this case:
: * Only the transfer driver (`TM_MAD`) is defined.
  * For the datastore of this example, there are no overall usage figures. The `local` driver uses the local storage area of each Host. To check the available space in a specific Host you need to check the Host details with `onehost show` command. Note that this behavior may be different for other drivers.
  * Images cannot be registered in System Datastores.

## Basic Configuration

Configuring a datastore usually requires you to add some specific attributes that depend on the storage driver and your infrastructure. Check the [Open Cloud Storage Guide]({{% relref "overview#storage" %}}) for specific details.

Also, there are a set of common attributes that can be used in any datastore to tune its behavior. The following table describes each attribute:

| Attribute                  | Description                                                                                                                                                                                                                |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `RESTRICTED_DIRS`          | Paths that **cannot** be used to register images. A space separated list of paths.                                                                                                                                         |
| `SAFE_DIRS`                | If you need to allow a directory listed under RESTRICTED_DIRS. A space separated list of paths.                                                                                                                            |
| `NO_DECOMPRESS`            | Do not try to untar or decompress the file to be registered. Useful for specialized Transfer Managers                                                                                                                      |
| `LIMIT_TRANSFER_BW`        | Specify the maximum transfer rate in bytes/second when downloading images from a http/https URL. Suffixes K, M or G can be used.                                                                                           |
| `DATASTORE_CAPACITY_CHECK` | If `yes`, the available capacity of the Datastore is checked before creating a new image                                                                                                                                   |
| `LIMIT_MB`                 | The maximum capacity allowed for the Datastore in `MB`. Works both ways, to reserve some Datastore capacity to be unused<br/>when `LIMIT_MB` < `TOTAL_MB` or allows Datastore overcommitment when `LIMIT_MB` > `TOTAL_MB`. |
| `BRIDGE_LIST`              | Space separated list of hosts that have access to the storage to add new images to the datastore.                                                                                                                          |
| `STAGING_DIR`              | Path in the storage bridge host to copy an Image before moving it to its final destination. Defaults to `/var/tmp`.                                                                                                        |
| `DRIVER`                   | Specific image mapping driver enforcement. If present it overrides image `DRIVER` set in the image attributes and VM template.                                                                                             |
| `COMPATIBLE_SYS_DS`        | Only for Image Datastores. Set the System Datastores that can be used with an Image Datastore, e.g. “0,100”                                                                                                                |
| `CONTEXT_DISK_TYPE`        | Specifies the disk type used for context devices (`BLOCK` or `FILE`). If not specified, `FILE` is used by default.                                                                                                         |

The Files & Kernels Datastore is a special datastore type to store plain files to be used as kernels, ram-disks, or context files. [See here to learn how to define them]({{% relref "file_ds#file-ds" %}}).

{{< alert title="Important" type="info" >}}
If you  are using `BRIDGE_LIST` you need to install any tool needed to access the underlying storage (e.g., Ceph `BRIDGE_LIST` servers need Ceph client tools), as well as generic tools like `qemu-img`.{{< /alert >}} 

## Disable a System Datastore

System Datastores can be disabled to prevent the scheduler from deploying new VM in them. Datastores in the `disabled` state are monitored as usual and the existing VM will continue to run.

```default
$ onedatastore disable system

$ onedatastore show system
DATASTORE 0 INFORMATION
ID             : 0
NAME           : system
...
STATE          : DISABLED
...
```

## Using Sunstone to Manage Datastores

You can also manage your Datastores using the [Sunstone GUI]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}). Select the **Storage -> Datastores** to create, enable, disable, delete, and inspect information about your datastores in a user-friendly way:

{{< image
  pathDark="/images/storage/dark/sunstone_datastores.png"
  path="/images/storage/light/sunstone_datastores.png"
  alt="Datastores" align="center" mb="20px"
>}}
