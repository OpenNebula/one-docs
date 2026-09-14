---
title: "Operations"
linkTitle: "Operations"
weight: 4
type: docs
---

## Where to look when something is wrong

Each role logs what it did at boot in `/var/log/ood-appliance-configure.log`, and `/etc/one-ondemand/build.env` records what the image was built from. A role that failed to configure shows it in its `motd` and in `/etc/one-appliance/status`, and OneFlow keeps the service out of `RUNNING` until every role has declared itself ready.

On the portal, Open OnDemand writes the per user web server logs under `/var/log/ondemand-nginx/<user>/` and Apache under `/var/log/apache2/`. A session that does not start leaves its output in the session directory under the user's home, `~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log`.

## Keeping the home

By default the shared home lives on the root disk of the storage VM and goes with the service when the service is deleted. Two ways keep it.

**A persistent disk on the storage role.** Create a persistent datablock once and attach it to the storage role of the service template, as a second `DISK` in its `vm_template_contents`:

```shell
$ oneimage create --name ood-home --type DATABLOCK --size 51200 --persistent --datastore default
$ oneflow-template update 'Open OnDemand Service'
```

```text
DISK = [ IMAGE_ID = "<id of ood-home>" ]
```

The storage role formats a blank second disk at first boot, labels it `ood-home` and keeps the homes on it. A disk that already carries the label is mounted as it is, so deleting the service and instantiating it again with the same image brings every home back. A disk with any other filesystem is left alone, and the role stops with an error that says so. Back the homes up with `onevm disk-saveas` or a disk snapshot of the storage VM, whichever your datastore supports.

**An NFS server you already run.** Set `ONEAPP_NFS_SERVER` and `ONEAPP_NFS_EXPORT` and the portal and the workers mount that export instead of the storage role. The server has to export it with `no_root_squash` for the portal address, the role that creates each home on first login, and can keep `root_squash` for the workers. The storage role still runs the software cache, so it stays in the service.

## Removing the service

```shell
$ oneflow delete <service_id>
```

This terminates the three VMs and the non persistent disks. A persistent home disk is released and keeps its content, an external export is untouched. The imported image, VM template and service template stay in your OpenNebula until you delete them.

## Limitations

* Sessions run on VMs without a scheduler. A worker holds every session that lands on it, and a session uses the whole VM, shared with the other sessions on the same VM.
* There is no GPU support in this release.
* The first load of a module on a fresh deployment downloads it through the site cache on the storage role.
