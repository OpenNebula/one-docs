---
title: "NFS/NAS Datastore"
linkTitle: "NFS/NAS"
date: "2025-02-17"
description:
categories:
pageintoc: "69"
tags:
weight: "3"
---

<a id="nas-ds"></a>

<!--# NFS/NAS Datastores -->

This storage configuration assumes that your Hosts can access and mount a shared volume located on a NAS (Network Attached Storage) server. You will use this shared volume to store VM disk images files. The Virtual Machines will also boot from the shared volume.

The scalability of this solution will be bound to the performance of your NAS server. However, you can use multiple NAS servers simultaneously to improve the scalability of your OpenNebula cloud. The use of multiple NFS/NAS Datastores will allow you to:

- Balance I/O operations between storage servers.
- Apply different SLA policies (e.g., backup) to different VM types or users.
- Easily add new storage.

Using an NFS/NAS Datastore provides a straightforward solution for implementing thin provisioning for VMs, which is enabled by default when using the **qcow2** image format.

Datastore setup can be done either manually or automatically:

## Manual Front-end Setup

Simply mount the **Image** Datastore directory in the Front-end in `/var/lib/one/datastores/<datastore_id>`. Note that if all the Datastores are of the same type you can mount the whole `/var/lib/one/datastores` directory.

{{< alert title="Note" type="info" >}}
The Front-end only needs to mount the Image Datastores and **not** the System Datastores.{{< /alert >}}

{{< alert title="Note" type="info" >}}
**NFS volumes mount tips**. NFS version 4.2 is the supported and tested protocol version. The following options are recommended to mount NFS shares: `soft, intr, rsize=32768, wsize=32768`. With the documented configuration of libvirt/kvm, the image files can be accessed as the `oneadmin` user. If the files must be read by `root`, the option `no_root_squash` must be added.{{< /alert >}}

## Manual Host Setup

The configuration is the same as for the Front-end above: simply mount in each Host the datastore directories in `/var/lib/one/datastores/<datastore_id>`.

<a id="automatic-nfs-setup"></a>

## Automatic Setup

Automatic NFS setup is an opt-in feature in the NFS drivers. It’s controlled via the `NFS_AUTO_*` family of datastore attributes documented [below]({{% relref "#anfs-attributes" %}}). If enabled, OpenNebula will lazily mount the NFS share on demand (either on Hosts or the Front-end) before an operation requires it. Also, for the transfer operations where it makes sense (for example, when deploying a VM which uses a NFS-backed system image), the mounting information is persisted to the Host’s `/etc/fstab`.

The unmounting/fstab cleanup is performed in a lazy way, similar to mounting. This means regular VM operations (e.g., deploy or terminate) will check whether the current machine has mounted a datastore which either has `NFS_AUTO_ENABLE` set to `no`, or does not exist anymore, and clean it up.

{{< alert title="Warning" type="warning" >}}
It is recommended to not to delete the shared filesystem from the NFS server until you are sure that no Hosts still have it mounted.{{< /alert >}}

Other than that, the system state at the end will be similar to the way specified in the Manual Setup sections; each datastore will mount its own NFS share in `/var/lib/one/datastores/<datastore_id>`. In fact, there is no issue in mixing operations between datastores (i.e., managing some of them manually and some others automatically).

## OpenNebula Configuration

Once Host and Front-end storage have been is set up, the OpenNebula configuration comprises the creation of the Image and System Datastores.

### Create System Datastore

To create a new System Datastore, you need to set following (template) parameters:

| Attribute     | Description                                          |
| ------------- | ---------------------------------------------------- |
| `NAME`        | Name of datastore                                    |
| `TYPE`        | `SYSTEM_DS`                                          |
| `TM_MAD`      | `shared` for shared transfer mode                    |
|               | `qcow2` for qcow2 transfer mode                      |
| `BRIDGE_LIST` | Space-separated list of hosts with system DS mounted |

This can be done either in Sunstone or through the CLI; for example, to create a System Datastore using the shared mode simply enter:

```default
$ cat systemds.txt
NAME    = nfs_system
TM_MAD  = shared
TYPE    = SYSTEM_DS

$ onedatastore create systemds.txt
ID: 101
```

{{< alert title="Note" type="info" >}}
When different System Datastores are available the `TM_MAD_SYSTEM` attribute will be set after picking the datastore.{{< /alert >}}

### Create Image Datastore

To create a new Image Datastore, you need to set the following (template) parameters:

#### Configuration Attributes for NFS/NAS Datastores

| Attribute | Values                  | Description                                                                                                                                                          |
| --------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `NAME`    |                         | Name of datastore                                                                                                                                                    |
| `DS_MAD`  | `fs`                    | Datastore driver to use                                                                                                                                              |
| `TM_MAD`  | `shared` or `qcow2`     | Transfer driver, `qcow2` uses specialized operations for `qcow2` files                                                                                               |
| `CONVERT` | `yes` (default) or `no` | If `DRIVER` is set on the image datastore, this option controls whether the images in different formats are internally converted into the `DRIVER` format on import. |

For example, the following illustrates the creation of a Filesystem Datastore using the shared transfer drivers:

```default
$ cat ds.conf
NAME   = nfs_images
DS_MAD = fs
TM_MAD = shared
TYPE   = IMAGE_DS

$ onedatastore create ds.conf
ID: 100
```

Also note that there are additional attributes that can be set. Check the [datastore template attributes]({{% relref "datastores#datastore-common" %}}).

{{< alert title="Warning" type="warning" >}}
Be sure to use the same `TM_MAD` for both the System and Image Datastores. When combining different transfer modes, check the section below.{{< /alert >}}

### Additional Configuration

- `QCOW2_OPTIONS`: Custom options for the `qemu-img` clone action. Images are created through the `qemu-img` command using the original image as a backing file. Custom options can be sent to `qemu-img` clone action through the variable `QCOW2_OPTIONS` in `/etc/one/tmrc`.
- `DD_BLOCK_SIZE`: Block size for dd operations (default: 64kB) can be set in `/var/lib/one/remotes/etc/datastore/fs/fs.conf`.
- `SUPPORTED_FS`: Comma-separated list with every filesystem supported for creating formatted datablocks. Can be set in `/var/lib/one/remotes/etc/datastore/datastore.conf`.
- `FS_OPTS_<FS>`: Options for creating the filesystem for formatted datablocks. Can be set in `/var/lib/one/remotes/etc/datastore/datastore.conf` for each filesystem type.
- `SPARSE`: If set to `NO` the images and disks in the Image and System Datastores, respectively, won't be sparsed (i.e., the files will use all assigned space on the Datastore filesystem). It is mandatory to set `QCOW2_STANDALONE = YES` on the System Datastore for this setting to apply.
- `QCOW2_STANDALONE`: If set to `YES` the standalone qcow2 disk is created during [CLONE]({{% relref "../../../product/integration_references/infrastructure_drivers_development/sd#clone" %}}) operation (default: QCOW2_STANDALONE=”NO”). Unlike previous options, this one is defined in the Image Datastore template and inherited by the disks.

<a id="anfs-attributes"></a>

Attributes related to NFS auto configuration can’t be changed after datastore creation unless it is empty:

- `NFS_AUTO_ENABLE`: If set to `YES` the automatic NFS mounting functionality is enabled (default: `no`).
- `NFS_AUTO_HOST`: (Required if `NFS_AUTO_ENABLE=yes`) Hostname or IP address of the NFS server.
- `NFS_AUTO_PATH`: (Required if `NFS_AUTO_ENABLE=yes`) NFS share path. This share will be mounted in
  the hosts at the datastore path (`/var/lib/one/datastores/<dsid>/`).
- `NFS_AUTO_OPTS`: Comma-separated options (fstab-like) used for mounting the NFS shares (default: `defaults`).

Here's a sample configuration for an automatically mounted image datastore:

```default
$ cat ds.conf
NAME            = nfs_images_share1
DS_MAD          = fs
TM_MAD          = shared
NFS_AUTO_ENABLE = yes
NFS_AUTO_HOST   = 192.168.150.10
NFS_AUTO_PATH   = /srv/share1
NFS_AUTO_OPTS   = "soft,intr,rsize=32768,wsize=32768"
TYPE            = IMAGE_DS

$ onedatastore create ds.conf
ID: 102
```

{{< alert title="Warning" type="warning" >}}
Before adding a new filesystem to the `SUPPORTED_FS` list make sure that the corresponding `mkfs.<fs_name>` command is available in the Front-end and hypervisor Hosts. If an unsupported FS is used by the user the default one will be used.
{{< /alert >}}

<a id="shared-ssh-mode"></a>

## NFS/NAS and Local Storage

When using the NFS/NAS Datastore, you can improve VM performance by placing the disks in the Host’s local storage area. In this way, you will have a repository of images (distributed across the Hosts using a shared FS) but the VMs running from the local disks. This effectively combines NFS/NAS and [Local Storage datastores]({{% relref "local_ds#local-ds" %}}).

{{< alert title="Warning" type="warning" >}}
This setup will increase performance at the cost of increasing deployment times.{{< /alert >}}

To configure this scenario, simply configure a shared Image and System Datastores as described above (`TM_MAD=shared`). Then, add a Local Storage System Datastore (`TM_MAD=ssh`). Any image registered in the Image Datastore can now be deployed using any of these Datastores.

{{< alert title="Warning" type="warning" >}}
If you added the NFS/NAS Datastores to the cluster, you need to add the new Local Storage System Datastore to the very same clusters.{{< /alert >}}

To select the (alternate) deployment mode, add the following attribute to the Virtual Machine template:

- `TM_MAD_SYSTEM="ssh"`

## Datastore Internals

Images are saved into the corresponding datastore directory (`/var/lib/one/datastores/<DATASTORE ID>`). Also, for each running Virtual Machine there is a directory (named after the `VM ID`) in the corresponding System Datastore. These directories contain the VM disks and additional files, e.g., checkpoint or snapshots.

For example, a system with an Image Datastore (`1`) with three images and three Virtual Machines (VM 0 and 2 running, and VM 7 stopped) running from System Datastore `0` would present the following layout:

```default
/var/lib/one/datastores
|-- 0/
|   |-- 0/
|   |   |-- disk.0
|   |   `-- disk.1
|   |-- 2/
|   |   `-- disk.0
|   `-- 7/
|       |-- checkpoint
|       `-- disk.0
`-- 1
    |-- 05a38ae85311b9dbb4eb15a2010f11ce
    |-- 2bbec245b382fd833be35b0b0683ed09
    `-- d0e0df1fb8cfa88311ea54dfbcfc4b0c
```

{{< alert title="Note" type="info" >}}
The canonical path for `/var/lib/one/datastores` can be changed in [/etc/one/oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf" %}}) with the `DATASTORE_LOCATION` configuration attribute{{< /alert >}}

The `shared` transfer driver assumes that the datastore is mounted on all the Hosts (Front-end and Hosts) of the cluster. Typically this is achieved through a **shared filesystem**, e.g., NFS, GlusterFS, or Lustre. This transfer mode usually reduces VM deployment times, but it can also become a bottleneck in your infrastructure and degrade your Virtual Machines’ performance if the virtualized services perform disk-intensive workloads. Usually, this limitation may be overcome by:

- Using different filesystem servers for the Image Datastores so the actual I/O bandwidth is balanced.
- Using the Host local storage.
- Tuning or improving the filesystem servers.

When a VM is created, its disks (the `disk.i` files) are copied or linked in the corresponding directory of the System Datastore. These file operations are always performed remotely on the target Host.

{{< image path="/images/fs_shared.svg" alt="VM disks linked in the System Datastore directory" align="center" width="70%" mb="20px" border="false" >}}

