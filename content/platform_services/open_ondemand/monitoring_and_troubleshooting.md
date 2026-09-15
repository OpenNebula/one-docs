---
title: "Monitoring and Troubleshooting"
linkTitle: "Monitoring and Troubleshooting"
date: "2026-09-15"
description:
categories:
tags:
weight: "6"
type: docs
---

The Open OnDemand Service reports its state through OneFlow, OneGate and a Prometheus endpoint on the portal. This section describes what each shows, where the logs are, and what to check when a role or a session fails.

## Metrics

The portal serves Prometheus metrics on port 9101 of its management address, `http://<portal management address>:9101/metrics`:

| Metric | Meaning |
|---|---|
| `ood_worker_active_sessions` | Sessions open on the worker (labels `vm_id`, `name`, `address`) |
| `ood_worker_idle`, `ood_worker_idle_seconds` | Whether the worker is empty, and for how long |
| `ood_worker_healthy` | `1` when the home mount, the software catalogue and sshd are in place |
| `ood_role_cardinality` | VMs in each role |
| `ood_portal_puns` | Per user web servers running on the portal, one per signed in user |
| `ood_service_state` | The OneFlow state of the service, as its numeric code (`2` is RUNNING) |
| `ood_exporter_scrape_ok` | `1` when the exporter's last read of the service through OneGate succeeded |
{.w-100}

The same values are in the user template of each worker VM, in Sunstone or with `onevm show <worker id>`, together with `SESSION_USERS`, who has a session on the worker and since when. A worker whose home mount, software catalogue or sshd fails publishes `HEALTHY=0`, and the portal sends it no new session until it recovers.

## Logs

```default
/var/log/ood-appliance-configure.log      what each role did at boot, on every VM
/etc/one-appliance/status                 bootstrap_success when the role is ready
/var/log/ondemand-nginx/<user>/error.log  the user's web server, on the portal
/var/log/apache2/                         the front Apache and the login flow, on the portal
~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log
                                          what a session printed, in the user's home
```

On the workers, `journalctl -t ood-publish-load` shows what the health check found.

## A Role Does Not Reach RUNNING

`oneflow show <service_id>` names the role. Open a console on its VM and read the last lines of `/var/log/ood-appliance-configure.log`. The usual causes:

* **OneGate not reachable**: a role that cannot reach OneGate never declares itself ready. The appliance tries `ONEGATE_ENDPOINT` from the VM context first and then port 5030 on the VM's default gateway, and `/var/log/ood-appliance-configure.log` records which one answered. Check that one of the two is reachable from the management network.
* **The storage role cannot reach the EESSI servers**: it needs outbound HTTP on ports 80 and 8000.
* **The portal cannot mount the home**: the storage role grants it root on the export through OneGate within about 20 seconds of the portal VM existing. A portal still waiting after three minutes points at OneGate.
* **The wrong address range**: `ONEAPP_POOL_RANGE` does not match the compute network.

## A Session Does Not Start

1. Check that every role is `RUNNING`.
2. On the portal, `cat /var/lib/ood-pool/workers.json` lists the workers the portal will use. A worker missing from it is not answering on port 22 or publishes `HEALTHY=0`.
3. Read `output.log` in the session directory. `module load` errors point at the software catalogue, `Permission denied` on the home at the export, a refused SSH connection at the `from=` restriction on the user's key, which only admits the compute network.
4. On the worker, `runuser -u <user> -- ls /cvmfs/software.eessi.io/versions` tells whether the catalogue is reachable as that user.

## Users Cannot Sign In

On the portal, `systemctl status slapd ondemand-dex` and `ldapsearch -x -H ldap://localhost -b dc=ood,dc=local uid=<user>`. A user who signs in but cannot open a session has no Unix account on the worker: `getent passwd <user>` on the worker has to answer, through `sssd` against the portal on port 389.

## The Pool Does Not Scale

Check that the workers publish their attributes with `onevm show`, and read `/var/log/one/oneflow.log` on the Front-end for the policy evaluation. OneFlow writes a `[AE] Checking policies for service: <id>` line for every service every 90 seconds, and `oneflow show <service_id> --json` keeps the time of the last evaluation in `last_eval` of each policy. If the lines stop, or `last_eval` stays empty while the workers publish `ACTIVE_SESSIONS` above 1, the evaluation thread of OneFlow has died and `systemctl restart opennebula-flow` on the Front-end starts it again; the service and its VMs are not affected. In OpenNebula 7.4 the thread dies when `oned` answers an empty VM monitoring pool, which happens after a Front-end outage longer than `VM_MONITORING_EXPIRATION_TIME` in `/etc/one/monitord.conf` (12 hours by default) and on a fresh installation before the first monitoring cycle. Nothing is written to `oneflow.log`; the only trace is a `terminated with exception` line from `role.rb` in `journalctl -u opennebula-flow`. After a reboot of the Front-end, check for the `[AE]` line within three minutes. The pool grows only up to `max_vms`, and shrinks only after `ONEAPP_WORKER_IDLE_SECONDS` of the oldest worker being empty plus the five minute cooldown of the policy.

## The VMs Are in POWEROFF After a Host Reboot

OpenNebula does not resume the VMs on its own and OneFlow shows the service in `WARNING`. Resume the storage VM, then the portal, then the workers, and the service returns to `RUNNING` by itself with its users and home directories intact.
