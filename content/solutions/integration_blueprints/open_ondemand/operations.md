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

This section covers the lifecycle of a running Open OnDemand Service. It explains how to keep the home directories across deployments, upgrade the appliance, and remove the service.

## Keeping the Home Directories

By default the shared home is on the root disk of the storage VM and is deleted with the service. Two options keep it.

**A persistent disk on the storage role.** Create a persistent Datablock and add it to the `template_contents` of the storage role in the service template. List it next to the disk of the appliance image, because a `DISK` entry there replaces the whole disk list of the VM template:

```shell
oneimage create --name ood-home --type DATABLOCK --size 51200 --persistent --datastore default
```

```json
"DISK": [
  { "IMAGE_ID": "<id of the appliance image>" },
  { "IMAGE_ID": "<id of ood-home>" }
]
```

At first boot the storage role formats a blank second disk, labels it `ood-home` and keeps the home directories on it. A disk that already has the label is mounted as it is. If you delete the service and instantiate it again with the same disk, every home directory is restored. A disk with any other filesystem is not touched, and the role stops with an error.

**An NFS server you already run.** At instantiation, enable **NFS server of your own** in the **Home directories** tab (`ONEAPP_HOME_NFS_ENABLED`). Set `ONEAPP_HOME_NFS_SERVER` and `ONEAPP_HOME_NFS_EXPORT`. The portal creates each home directory on first login. The server must therefore export the path with `no_root_squash` for the address the portal uses to reach it. That is the compute address of the portal when the server is on the compute network, and its management address otherwise. The server can keep `root_squash` for the workers. The storage role still runs the software cache.

## Upgrading

A new version of the appliance is a new image and new templates. A running service keeps the old ones. Download the new version and instantiate a new service with the same inputs. Move the home directories as described above. Attach the same persistent disk, or use the same export. You can also save them with `onevm disk-saveas` first. Then point the DNS name of the portal to the new portal VM and delete the old service. Users are created again from `ONEAPP_AUTH_LOCAL_USERS`. Add the others again on the new portal.

## Removing the Service

From **Instances -> Services** in Sunstone, or from the Front-end command line:

```shell
oneflow delete <service_id>
```

This terminates the VMs of every role and their non persistent disks. A persistent home disk is released and keeps its content. An external export is not touched. The imported image and templates stay until you delete them.

## Limitations

* The portal and the storage role are one VM each, with no high availability. A reboot of the portal keeps the running and the pending jobs. This works because the queue, the nodes and the munge key are on the storage export. The accounting database is dumped there every 30 minutes for a replaced portal. Measured on the testbed: munge, MariaDB, `slurmdbd`, `slurmctld` and the timers were active well under a minute after the reboot, and both jobs were still in the queue. A portal that OneFlow replaces with a new VM has not been tested. The workers follow the new address from the service document, and the key and the state are restored from the export. Both are untested.
* The state of the Slurm controller is on NFS, so the storage VM must stay reachable from the portal. During a 33 second pause of the NFS server, `sinfo` still answered and the controller stayed active. The running job was not affected. A longer outage has not been measured.
* Every session and every Job Composer job runs on the cluster of the service. A Slurm Cluster of the site can be attached as a second target for batch jobs. See [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#batch-jobs-with-slurm" %}}).
* GPU workers are prepared but untested.
