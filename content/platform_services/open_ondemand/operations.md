---
title: "Operations"
linkTitle: "Operations"
weight: 4
type: docs
---

## Metrics

The portal serves Prometheus metrics for the whole service on port 9101, `http://<portal management address>:9101/metrics`. Per worker it exposes `ood_worker_active_sessions`, `ood_worker_idle`, `ood_worker_idle_seconds` and `ood_worker_healthy`, read from what the workers publish to OneGate, plus `ood_role_cardinality` per role and `ood_portal_puns`, the per user web servers running on the portal. The same values are in the user template of each worker VM:

```shell
$ onevm show <worker id> | grep -E 'ACTIVE_SESSIONS|IDLE|HEALTHY'
```

A worker checks its home mount, the software catalogue and sshd before every report and publishes `HEALTHY=0` when one of them is missing. The portal sends no new session to a worker in that state, and the log of the check is on the worker, `journalctl -t ood-publish-load`.

## Where to look when something is wrong

Each role logs what it did at boot in `/var/log/ood-appliance-configure.log`, and `/etc/one-ondemand/build.env` records what the image was built from. A role that failed to configure shows it in its `motd` and in `/etc/one-appliance/status`, and OneFlow keeps the service out of `RUNNING` until every role has declared itself ready.

On the portal, Open OnDemand writes the per user web server logs under `/var/log/ondemand-nginx/<user>/` and Apache under `/var/log/apache2/`. A session that does not start leaves its output in the session directory under the user's home, `~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log`.

## When a session does not start

1. `oneflow show <service_id>` says whether every role is `RUNNING`. A worker in a different state has not declared itself ready, and its `/var/log/ood-appliance-configure.log` says at which step it stopped.
2. On the portal, `cat /var/lib/ood-pool/workers.json` lists the workers the portal will use. `"source":"onegate"` means the list comes from the service; `"rango"` means OneGate did not answer and the portal probed the address range instead. A worker missing from the list is either not answering on port 22 or publishing `HEALTHY=0`.
3. The session directory under the user's home has `connection.yml`, with the worker the session ran on, and `output.log`, with what failed there. `module load` errors point at the software catalogue, `Permission denied` on the home points at the export, and a refused SSH connection at the `from=` restriction on the user's key, which only admits connections from the compute network.
4. On the worker, `journalctl -t ood-publish-load` shows what the health check found, and `runuser -u <user> -- ls /cvmfs/software.eessi.io/versions` whether the catalogue is reachable as that user.

## Upgrading

A new version of the appliance is a new image and new templates, and the running service keeps the old ones. Download the new version from the marketplace, which imports them beside the old ones, and instantiate a new service from the new service template. The home survives the change when it lives on a persistent disk or on an NFS server of your own, as the next section describes: delete the old service, attach the same disk to the new one or point it at the same export, and the users find their files. With the home on the storage VM's root disk, copy it out with `onevm disk-saveas` before deleting the old service. Users, the LDAP directory, are recreated from `ONEAPP_LDAP_USERS`, so pass the same value or add the users again once the new portal is up.

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

* Interactive sessions run on VMs without a scheduler. A worker holds every session that lands on it, and a session uses the whole VM, shared with the other sessions on the same VM. Batch jobs can go to a Slurm cluster instead, see Configuration.
* There is no GPU support in this release.
* The first load of a module on a fresh deployment downloads it through the site cache on the storage role.
