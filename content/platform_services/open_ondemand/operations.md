---
title: "Operations"
linkTitle: "Operations"
weight: 4
type: docs
---

## Where to look when something is wrong

Each role logs what it did at boot in `/var/log/ood-appliance-configure.log`, and `/etc/one-ondemand/build.env` records what the image was built from. A role that failed to configure shows it in its `motd` and in `/etc/one-appliance/status`, and OneFlow keeps the service out of `RUNNING` until every role has declared itself ready.

On the portal, Open OnDemand writes the per user web server logs under `/var/log/ondemand-nginx/<user>/` and Apache under `/var/log/apache2/`. A session that does not start leaves its output in the session directory under the user's home, `~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log`.

## Removing the service

```shell
$ oneflow delete <service_id>
```

This terminates the three roles and their disks. The shared home lives on the disk of the storage VM, so it goes with the service unless you copy it out first. The imported image, VM template and service template stay in your OpenNebula until you delete them.

## Limitations

* Sessions run on VMs without a scheduler. A worker holds every session that lands on it, and a session uses the whole VM, shared with the other sessions on the same VM.
* There is no GPU support in this release.
* The first load of a module on a fresh deployment downloads it through the site cache on the storage role.
