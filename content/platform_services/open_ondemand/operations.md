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

This section describes the lifecycle operations of the Open OnDemand Service once it is running: scaling the pool by hand, keeping the home directories across deployments, upgrading to a new version of the appliance, and removing the service.

## Scaling the Pool by Hand

The worker pool scales on its own, but you can set its size at any time. From **Instances -> Services** in Sunstone, open the service, select the **Roles** tab and change the cardinality of the `worker` role. From the Front-end command line:

```shell
oneflow scale <service_id> worker <cardinality>
```

OneFlow adds VMs immediately. When it removes VMs it takes the oldest ones of the role first, sessions included, so check `SESSION_USERS` on the workers before shrinking by hand:

```shell
onevm show <worker id> | grep -E 'ACTIVE_SESSIONS|SESSION_USERS'
```

The elasticity policies keep working after a manual change, within `min_vms` and `max_vms` of the role.

## Keeping the Home Directories

By default the shared home lives on the root disk of the storage VM and goes with the service when the service is deleted. Two options keep it.

### A Persistent Disk on the Storage Role

Create a persistent Datablock once and attach it to the storage role of the service template, as a second `DISK` in its `vm_template_contents`:

```shell
oneimage create --name ood-home --type DATABLOCK --size 51200 --persistent --datastore default
oneflow-template update 'Open OnDemand Service'
```

```default
DISK = [ IMAGE_ID = "<id of ood-home>" ]
```

The storage role formats a blank second disk at first boot, labels it `ood-home` and keeps the home directories on it. A disk that already carries the label is mounted as it is, so deleting the service and instantiating it again with the same disk brings every home directory back. A disk with any other filesystem is left alone, and the role stops with an error that says so.

Back the home directories up with `onevm disk-saveas` or a disk snapshot of the storage VM, whichever your Datastore supports.

### An NFS Server You Already Run

Set `ONEAPP_NFS_SERVER` and `ONEAPP_NFS_EXPORT` at instantiation, and the portal and the workers mount that export instead of the storage role. The server has to export it with `no_root_squash` for the compute address of the portal, the role that creates each home directory on first login, and can keep `root_squash` for the workers. The storage role still runs the software cache, so it stays in the service.

{{< alert title="Note" type="primary" >}}
The external server path was tested against the storage role of another instance of the service. It has not been tested against a third party NFS server yet.
{{< /alert >}}

## Upgrading

A new version of the appliance is a new image and new templates, and a running service keeps the old ones. To upgrade:

1. Download the new version from the marketplace. It imports its image and templates beside the old ones.
2. Instantiate a new service from the new service template, with the same inputs. Users are recreated from `ONEAPP_LDAP_USERS`, so pass the same value or add the users again once the new portal is up.
3. Move the home directories. With a persistent disk, delete the old service and attach the same disk to the new one. With an external NFS server, point the new service at the same export. With the home on the root disk of the storage VM, copy it out with `onevm disk-saveas` before deleting the old service.
4. Point the DNS name of the portal at the new portal VM and delete the old service.

## Removing the Service

From **Instances -> Services** in Sunstone, select the service and click **Delete**. From the Front-end command line:

```shell
oneflow delete <service_id>
```

This terminates the VMs of every role and their non persistent disks. A persistent home disk is released and keeps its content, and an external export is untouched. The imported image, VM template and service template stay in your OpenNebula until you delete them.

## Limitations

* Interactive sessions run on VMs without a scheduler. A worker holds every session that lands on it, and the sessions on one VM share its CPU and memory. Batch jobs can go to a Slurm Cluster instead, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/#batch-jobs-with-slurm" %}}).
* The portal and the storage role are one VM each. There is no high availability for either.
* GPU workers and the external identity provider are prepared but untested, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}).
* The first load of a module on a fresh deployment downloads it through the site cache on the storage role, so the first session is slower than the following ones.
