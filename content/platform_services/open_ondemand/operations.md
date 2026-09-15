---
title: "Operations"
linkTitle: "Operations"
date: "2026-09-15"
description:
categories:
tags:
weight: "5"
type: docs
---

This section covers the lifecycle of a running Open OnDemand Service, from keeping the home directories across deployments to upgrading to a new version of the appliance and removing the service.

## Keeping the Home Directories

By default the shared home lives on the root disk of the storage VM and goes with the service when the service is deleted. Two options keep it.

**A persistent disk on the storage role.** Create a persistent Datablock and add it to the `template_contents` of the storage role in the service template, next to the disk of the appliance image, because a `DISK` entry there replaces the whole disk list of the VM template:

```shell
oneimage create --name ood-home --type DATABLOCK --size 51200 --persistent --datastore default
```

```json
"DISK": [
  { "IMAGE_ID": "<id of the appliance image>" },
  { "IMAGE_ID": "<id of ood-home>" }
]
```

The storage role formats a blank second disk at first boot, labels it `ood-home` and keeps the home directories on it. A disk that already carries the label is mounted as it is, so deleting the service and instantiating it again with the same disk brings every home directory back. A disk with any other filesystem is left alone and the role stops with an error.

**An NFS server you already run.** Set `ONEAPP_NFS_SERVER` and `ONEAPP_NFS_EXPORT` at instantiation. The server has to export the path with `no_root_squash` for the address the portal reaches it from (its compute address when the server is on the compute network, its management address otherwise), because the portal creates each home directory on first login, and can keep `root_squash` for the workers. The storage role still runs the software cache.

## Upgrading

A new version of the appliance is a new image and new templates, and a running service keeps the old ones. Download the new version, instantiate a new service with the same inputs, move the home directories as described above (attach the same persistent disk, or point at the same export, or copy them out with `onevm disk-saveas` first), point the DNS name of the portal at the new portal VM and delete the old service. Users are recreated from `ONEAPP_LDAP_USERS`; add the others again on the new portal.

## Removing the Service

From **Instances -> Services** in Sunstone, or from the Front-end command line:

```shell
oneflow delete <service_id>
```

This terminates the VMs of every role and their non persistent disks. A persistent home disk is released and keeps its content, and an external export is untouched. The imported image and templates stay until you delete them.

## Limitations

* Interactive sessions run on VMs without a scheduler, and the sessions on one VM share its CPU and memory. Batch jobs can go to a Slurm Cluster, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/#batch-jobs-with-slurm" %}}).
* The portal and the storage role are one VM each, with no high availability.
* GPU workers are prepared but untested.
