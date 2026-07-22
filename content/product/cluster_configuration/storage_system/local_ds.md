---
title: "Local Storage Datastore"
linkTitle: "Local Storage"
date: "2025-02-17"
description:
categories:
pageintoc: "70"
tags:
weight: "4"
---

<a id="local-ds"></a>

<!--# Local Storage Datastore -->

This storage configuration uses the local storage area of each Host to run VMs. Additionally you’ll need a storage area for the VM disk image repository. Disk images are transferred from the repository to the Hosts using the SSH protocol.

## Front-end Setup

The Front-end needs to prepare the storage area for:

- **Image Datastores** to store the image repository.
- **System Datastores** to hold temporary disks and files for VMs `stopped` and `undeployed`.

Simply make sure that there is enough space under `/var/lib/one/datastores` to store images and the disks of the `stopped` and `undeployed` Virtual Machines. Note that `/var/lib/one/datastores` **can be mounted from any NAS/SAN server in your network**.

## Host Setup

Just make sure that there is enough space under `/var/lib/one/datastores` to store the disks of running VMs on that Host.

{{< alert title="Warning" type="warning" >}}
Local datastore requires that:
- The **Frontend hostnames are resolvable** from all Hosts.
- Every Host (including the Front-end) can **SSH to every other Host**, including themselves.
{{< /alert >}}

## OpenNebula Configuration

Once the Hosts and Front-end storage is set up, configuring OpenNebula comprises the creation of an Image and System Datastores.

### Create System Datastore

To create a new System Datastore, you need to set the following (template) parameters:

| Attribute | Description       |
| --------- | ----------------- |
| `NAME`    | Name of datastore |
| `TYPE`    | `SYSTEM_DS`       |
| `TM_MAD`  | `local`           |

You can do this either in Sunstone or through the CLI; for example, to create a local System Datastore simply enter:

```default
$ cat systemds.txt
NAME    = local_system
TM_MAD  = local
TYPE    = SYSTEM_DS

$ onedatastore create systemds.txt
ID: 101
```

{{< alert title="Note" type="info" >}}
When different System Datastores are available, select one to have the the `TM_MAD_SYSTEM` attribute set.{{< /alert >}}

### Create Image Datastore

To create a new Image Datastore, you need to set the following (template) parameters:

| Attribute | Description                                              |
| --------- | -------------------------------------------------------- |
| `NAME`    | Name of datastore                                        |
| `DS_MAD`  | `fs`                                                     |
| `TM_MAD`  | `local`                                                  |
| `CONVERT` | `yes` (default) or `no`. Change Image format to `DRIVER` |

For example, the following illustrates the creation of a Local Datastore:

```default
$ cat ds.conf
NAME   = local_images
DS_MAD = fs
TM_MAD = local

$ onedatastore create ds.conf
ID: 100
```

Also note that there are additional attributes that can be set. Check the [datastore template attributes]({{% relref "datastores#datastore-common" %}}).

{{< alert title="Warning" type="warning" >}}
Be sure to use the same `TM_MAD` for both the System and Image datastores. When combining different transfer modes, check the section below.{{< /alert >}}

### Additional Configuration

- `DD_BLOCK_SIZE`: Block size for dd operations (default: 64kB). Configured in `/var/lib/one/remotes/etc/datastore/fs/fs.conf`.
- `SUPPORTED_FS`: Comma-separated list of every filesystem supported for creating formatted datablocks. Configured in `/var/lib/one/remotes/etc/datastore/datastore.conf`.
- `FS_OPTS_<FS>`: Options for creating the filesystem for formatted datablocks. Configured in `/var/lib/one/remotes/etc/datastore/datastore.conf` for each filesystem type.
- `SPARSE`: When the value is `NO`, the images and disks in the image and System Datastore, respectively, will not be sparsed (i.e. the files will use all assigned space on the Datastore filesystem).

{{< alert title="Warning" type="warning" >}}
Before adding a new filesystem to the `SUPPORTED_FS` list make sure that the corresponding `mkfs.<fs_name>` command is available in the Front-end and hypervisor Hosts. If an unsupported FS is used by the user the default one will be used.{{< /alert >}}

{{< alert title="Note" type="info" >}}
When using a Local Storage Datastore, the `QCOW2_OPTIONS` attribute is ignored because the cloning script uses the `tar` command instead of `qemu-img`.{{< /alert >}}

## Datastore Drivers

<a id="local-ds-drivers"></a>

There are currently two Local transfer drivers:

- **local**: reference Local driver since OpenNebula 6.10.2, used by default for newly-created datastores. Supports operations such as thin provisioning for images in qcow2 format.
- **ssh**: legacy but still supported for compatibility reasons. Unable to leverage advanced qcow2 features.

## Datastore Internals

Images are saved into the corresponding datastore directory (`/var/lib/one/datastores/<DATASTORE ID>`). Also, for each running Virtual Machine there is a directory (named after the `VM ID`) in the corresponding System Datastore. These directories contain the VM disks and additional files, e.g., checkpoint or snapshots.

For example, a system with an Image Datastore (`1`) with three images and three Virtual Machines (VMs 0 and 2 running, and VM 7 stopped) running from System Datastore `0` would present the following layout:

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
The canonical path for `/var/lib/one/datastores` can be changed in [/etc/one/oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf" %}}) by modifying the `DATASTORE_LOCATION` configuration attribute.{{< /alert >}}

In this case, the System Datastore is distributed among the Hosts. The **local** transfer driver uses the Hosts' local storage to place the images of running Virtual Machines. All of the operations are then performed locally, but images still need to be copied to the Hosts, which can be a very resource-demanding operation.

{{< image path="/images/fs_ssh.svg" alt="Overview of Datastore Internals" align="center" width="90%" mb="20px" border="false" >}}

## Distributed Cache

OpenNebula can speed up VM provisioning and reduce bandwidth usage when using Local Storage Datastores by using a **two-level distributed cache**. This section explains what the distributed cache is, how to enable it, and how it works.

### What is the Distributed Cache?

The distributed cache stores VM disk images in two levels:

1. **Local Cache (per Host)**: Each compute host keeps a small cache of the images it has already retrieved.

2. **Central (Upstream) Cache**: One or more “central” cache nodes (usually the hosts with the most resources) store a larger pool of images shared by the entire cluster.

When a VM is launched:

- The host first checks its _local cache_.
- If the image is not there, it checks the _central cache_.
- If the image is not in either cache, the host retrieves it from the Image Datastore on the Front-end.

Once the cache manager downloads the image, this is stored in both the _local_ and _central_ caches for future use.

{{< image path="/images/local_ds_cache.svg" alt="Speeding up VM provisioning with Distributed Cache" align="center" width="90%" mb="20px" border="false" >}}

## How to Enable and Configure the Cache

The cache is configured **per Image Datastore**. As a result, each datastore has its own cache settings. The cache settings are described in the next table:

| Attribute         | Description                                                                                                                                                                          | Deault value         |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| `CACHE_ENABLE`    | Set to `yes` to enable the distributed cache , or `no` to disable it.                                                                                                                | `NO`                 |
| `CACHE_PATH`      | Directory where cached images are stored.                                                                                                                                            | `/var/lib/one/cache` |
| `CACHE_MAX_SIZE`  | Maximum percentage (integer value) of the local filesystem (where `CACHE_PATH` is located) that can be used for caching. For example, `10` means up to 10% of that disk can be used. | `10`                 |
| `CACHE_UPSTREAMS` | Comma-separated list of one or more “central” cache hostnames or IPs (e.g., `'hostname0,hostname1'`). Leave empty (`''`) to disable central caches.                                  | `''` (no upstreams)  |
| `CACHE_MIN_AGE`   | Minimum time in seconds before a cached image can be evicted. For example, `3600` means images used within the last hour cannot be removed from cache.                               | `900`                |

For example, to configure a Distributed Cache update the image datastore template with the following parameters:

```default
ENABLE_CACHE    = "YES"
CACHE_PATH      = "/var/lib/one/cache"
CACHE_MAX_SIZE  = "10"
CACHE_UPSTREAMS = "hostname0,hostname2"
CACHE_MIN_AGE   = "3600"
```

When you create a new Datastore in Sunstone, you can configure these settings in the **Configuration attributes** step of the **Create Datastore** workflow:

{{< image
  pathDark="/images/storage/dark/sunstone_ds_cache_config.png"
  path="/images/storage/light/sunstone_ds_cache_config.png"
  alt="Datastore cache configuration" align="center" mb="20px"
>}}


{{< alert title="Warning" type="warning" >}}
For the distributed cache to work, the `oneadmin` user (see [Node installation]({{% relref "../../../product/operation_references/hypervisor_configuration" %}})) must have SSH passwordless authentication configured on all Hosts.{{< /alert >}}

## Using the Cache

When you launch or migrate a VM, the cache manager performs the following steps:

1. **Check Local Cache:** Looks for the image in the host's local cache. If found and valid, it returns the local path.

2. **Check Upstream Cache:** If the image is missing locally (or invalid), the cache manager checks each host in `CACHE_UPSTREAMS`. If found, it copies the image locally and returns that path.

3. **Fallback to Front-end:** If not found in any cache, retrieves the image from the Image Datastore on the Front-end. Then stores it locally and on the central cache.

Cached images are stored in the cache directory (e.g., `/var/lib/one/cache/`) like this:

```default
/var/lib/one/cache/1/
├── c3af91e2b1d2ab9f64a25d99f9a2fbd2
└── c3af91e2b1d2ab9f64a25d99f9a2fbd2-metadata
```

The metadata file (YAML) contains:

```default
last_used: "2025-05-30T14:22:10Z"       # ISO 8601 timestamp of the most recent cache hit
modtime:   "1725552553"                 # Last OpenNebula image modification time
```

## Eviction Policy

If the total cache size exceeds `CACHE_MAX_SIZE`, the cache manager removes the Least Recently Used (LRU) images until there is enough space.

If there is still not enough space after eviction, the new image is fetched directly from the Front-end without caching.

{{< alert title="Warning" type="warning" >}}
Images used within the last `CACHE_MIN_AGE` seconds cannot be evicted.{{< /alert >}}

