---
title: "Shared Storage"
linkTitle: "Shared Storage"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "5"
---

A job can run on any worker, so users need the same files on the controller and on every worker. OneSlurm can mount two NFS exports in every VM of the cluster.

| Parameter | Mount point | Example |
|---|---|---|
| `ONEAPP_SLURM_NFS_HOME` | `/home` | `10.125.0.1:/srv/nfs/slurm/home` |
| `ONEAPP_SLURM_NFS_SCRATCH` | `/scratch` | `10.125.0.1:/srv/nfs/slurm/scratch` |

Both are optional. An empty value skips the mount.

## Before You Start

The controller and worker images already include the NFS client.


* Create the NFS server and the exports outside OneSlurm.
* The controller and all the workers must reach the NFS server.
* Do not attach another disk at `/home` or `/scratch` when you set the matching input.

## How It Works

The `net-12-mount-nfs` script runs in every VM when the network is configured.

| Item | Value |
|---|---|
| Format of the input | `host:/export` |
| Filesystem type | `nfs4` |
| Mount options | `sec=sys,_netdev` |
| Persistence | Adds a line to `/etc/fstab` after a successful mount, only once |

If a mount point is already mounted, the script skips it.

## Check the Mounts

On the controller.

```shell
$ findmnt /home
TARGET SOURCE                       FSTYPE OPTIONS
/home  192.168.100.222:/export/home nfs4   rw,relatime,vers=4.2,...,sec=sys,...
```

On a worker, through Slurm.

```shell
$ srun -N1 -n1 findmnt /home
$ srun -N1 -n1 findmnt /scratch
```

## User Directories

* `/home` holds the home directory of each user. Create it after the user exists in LDAP, owned by the UID and GID of the user. See [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}).
* `/scratch` has no structure. Create a directory for each user, for example `/scratch/alice`, owned by the user.
* Create these directories on the NFS server. With the default `root_squash` export option, root on the cluster VMs cannot write to the exports.
