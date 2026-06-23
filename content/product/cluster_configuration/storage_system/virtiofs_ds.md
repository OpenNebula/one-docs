---
title: "VirtioFS Datastore"
linkTitle: "Filesystem Storage"
date: "2026-02-18"
description:
categories:
pageintoc: "76"
tags:
weight: "10"
---

<a id="virtiofs-ds"></a>

<!--# VirtioFS Datastores -->

## Overview

OpenNebula supports sharing Host directories with Virtual Machines using VirtioFS. This enables high-performance, low-latency file sharing between the Host and guests. The feature is exposed through a dedicated datastore configured to provide directory-based disks, which are attached to VMs and exported via VirtioFS.

Unlike traditional block-based disks, these disks represent Host directories. This makes them suitable for:

- Shared data volumes across VMs
- HPC / AI workloads requiring fast POSIX access
- Container-like storage semantics inside VMs

## Requirements

Before creating and using a VirtioFS Datastore, ensure the following:

- The filesystem to be mounted must already exist and be available at the same path on each compute Host in the Cluster where VMs will be deployed.
- The `virtiofsd` daemon and libvirt/QEMU with VirtioFS support must be installed on each hypervisor node.

## Creating a VirtioFS Datastore

To create a new Image Datastore, define the following template parameters:

| Attribute         | Values       | Description                                                         |
| ----------------- | ------------ | ------------------------------------------------------------------- |
| `NAME`            |              | Name of the datastore                                               |
| `TYPE`            | `IMAGE_DS`   | OpenNebula datastore type                                           |
| `DS_MAD`          | `virtiofs`   | Datastore driver                                                    |
| `TM_MAD`          | `virtiofs`   | Transfer manager driver                                             |
| `RESTRICTED_DIRS` |              | Paths that cannot be registered as filesystem images                |
| `SAFE_DIRS`       |              | Paths that can be registered even when covered by `RESTRICTED_DIRS` |

This can be done either in Sunstone or through the CLI. For example:

```shell
cat ds.conf
NAME      = fs_datastore
TYPE      = IMAGE_DS
DS_MAD    = virtiofs
TM_MAD    = virtiofs
RESTRICTED_DIRS = "/"
SAFE_DIRS       = "/srv/virtiofs"

onedatastore create ds.conf
ID: 100
```

{{< alert title="Note" type="info" >}}
The `RESTRICTED_DIRS` and `SAFE_DIRS` attributes are evaluated when a VirtioFS filesystem image is registered. If the image `PATH` resolves inside a directory listed in `RESTRICTED_DIRS`, the image is rejected unless the path also resolves inside one of the directories listed in `SAFE_DIRS`. In the example above, only paths under `/srv/virtiofs` can be registered.
{{< /alert >}}

## Usage

Once the Image Datastore is created, register an image that represents a Host directory. Typically, only the path and image type need to be defined.

```bash
oneimage create --name fs_data --datastore fs_datastore --persistent --path /srv/virtiofs/data --type filesystem
```

For use cases where the same directory must be shared across multiple VMs simultaneously, create the image as non-persistent. If read-only access is required, set `READONLY="YES"` only when the Host uses `libvirt >= 11.0.0` and `virtiofsd >= 1.13.0` (older versions do not support read-only VirtioFS exports).

After the image is registered, it can be used as any other disk by adding it to the VM template using the `DISK` attribute.

```default
DISK= [ IMAGE = "fs_data" ]
```

By default, OpenNebula generates:

- A mount point (`MOUNT_POINT`), in the form `/mnt/one-fs-<image_id>`
- A mount tag (`MOUNT_TAG`), in the form `one-<image_id>`

Context packages use these values to automatically mount the filesystem inside the VM via VirtioFS. These values can be overridden in the `DISK` or `IMAGE` attributes to define a custom mount point (and tag) inside the guest.

For example, overriding it in a `DISK`:

```default
DISK= [ IMAGE = "fs_data", MOUNT_POINT="/srv/data", MOUNT_TAG="one-tag" ]
```

Or overriding it in an `IMAGE`:

```bash
cat update_image.conf
MOUNT_POINT="/srv/data"
MOUNT_TAG="one-tag"

oneimage update 0 update_image.conf
```

If both are specified, the `DISK` attributes are prioritized.

## Considerations

The VirtioFS Datastore behaves differently from other OpenNebula datastores:

- It does not support disk operations such as `snapshots`, `backups`, `disk-attach`, `resize` or `save-as`.
- The datastore does not store VM disk data. It only stores image metadata. Reported datastore capacity (free, used, total) is always 0.
- It doesn't transfer any images (since it does not use images, only metadata) and has no support for image cloning.
- Image size reflects the size of the directory, as reported by the `du` command, if it is available to the Frontend or Hosts listed in `BRIDGE_LIST`
- If the VM is configured with Hugepages, they are used as the `MemoryBacking` source with `shared` mode. Otherwise, a `memfd` source is used.
- The same image cannot be attached more than once to the same VM.
- Two different images cannot share the same `MOUNT_TAG`.

### User and Group ID mapping

OpenNebula configures VirtioFS UID/GID mapping using a subordinate ID range starting at `100000` with a size of `65536` for the `oneadmin` user. If `/etc/subuid` or `/etc/subgid` already contain an entry for oneadmin, it will be respected and not modified. These entries are created on Hosts during the installation of the `opennebula-node-kvm` package.

Access to the Host directory is performed through this mapping, meaning guest user and group IDs are translated into the configured subordinate range on the Host. The mapping can be adjusted globally in vmm_exec_kvm.conf, or per Host or Cluster using the same attributes defined there. For example:

```default
DISK = [ UID_MAP = "1000", GID_MAP = "1000" ]
```

When customizing these values, ensure that the subordinate ID range configured for oneadmin in `/etc/subuid` and `/etc/subgid` matches the VirtioFS `<idmap>` settings. Mismatched configurations may result in permission errors or unexpected ownership on the shared filesystem.
