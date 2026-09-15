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

The Open OnDemand Service reports its state through OneFlow, OneGate and a Prometheus endpoint on the portal. This section describes what each of them shows, where the logs of every role are, and what to check when a role does not start or a session does not open.

## Service States

The service and its roles follow the OneFlow states. Two of them matter in daily operation:

* `RUNNING`: Every role has declared itself ready through OneGate. The portal is serving and at least one worker accepts sessions.
* `DEPLOYING`: A role has not declared itself ready yet. The storage role takes about a minute, the portal about two and a worker about 40 seconds. A role that stays in this state failed to configure itself, see [A Role Does Not Reach RUNNING](#a-role-does-not-reach-running).

OneFlow keeps the service out of `RUNNING` until every role is ready, because the service template sets `ready_status_gate`. A role is ready when its configuration finished and its service answers, not when its VM boots.

## Metrics

The portal serves Prometheus metrics for the whole service on port 9101 of its management address, `http://<portal management address>:9101/metrics`:

| Metric | Labels | Meaning |
|---|---|---|
| `ood_worker_active_sessions` | `vm_id`, `role` | Sessions open on the worker |
| `ood_worker_idle` | `vm_id`, `role` | `1` when the worker has no session |
| `ood_worker_idle_seconds` | `vm_id`, `role` | How long the worker has been empty |
| `ood_worker_healthy` | `vm_id`, `role` | `1` when the home mount, the software catalogue and sshd are in place |
| `ood_role_cardinality` | `role` | VMs in each role |
| `ood_portal_puns` | | Per user web servers running on the portal, one per signed in user |
| `ood_service_state` | | The OneFlow state of the service |
| `ood_exporter_scrape_ok` | | `1` when the exporter could read OneGate on the last scrape |

The worker values come from what the workers publish to OneGate every ten seconds, so they are also in the user template of each worker VM, in Sunstone or from the command line:

```shell
onevm show <worker id> | grep -E 'ACTIVE_SESSIONS|IDLE|HEALTHY|SESSION_USERS'
```

```default
ACTIVE_SESSIONS="1"
AT_CAPACITY="0"
HEALTHY="1"
IDLE="0"
IDLE_SECONDS="0"
OLDEST_IDLE="0"
OLDEST_IDLE_SECONDS="0"
SESSION_USERS="demo1:1789460071"
```

`SESSION_USERS` lists who has a session on the worker and since when, as `user:epoch` entries, so the VM accounting of OpenNebula can be attributed to users.

## Worker Health

A worker checks three things before every report: that the home directory is mounted, that the software catalogue answers under `/cvmfs`, and that sshd listens on port 22. When one of them fails it publishes `HEALTHY=0`, and the portal sends no new session to it until it recovers. The check logs a line only when the state changes:

```shell
journalctl -t ood-publish-load
```

The portal keeps its roster of workers in `/var/lib/ood-pool/workers.json`. The `source` field says where the list came from: `onegate` when the service answered, `rango` when OneGate did not and the portal probed the address range instead. A worker missing from the list is either not answering on port 22 or publishing `HEALTHY=0`.

## Logs

Each role logs what it did at boot in the same file, and the image records what it was built from:

```default
/var/log/ood-appliance-configure.log    what the role did at boot, step by step
/etc/one-ondemand/build.env             version, build date and components of the image
/etc/one-appliance/status               the one-apps status, bootstrap_success when the role is ready
```

A role that failed to configure shows it in its `motd` at login and in the status file. On the portal, Open OnDemand writes the per user web server logs and the Apache logs under:

```default
/var/log/ondemand-nginx/<user>/error.log   the user's web server, one directory per user
/var/log/apache2/                          the front Apache, including the Dex login flow
```

A session leaves its output in the session directory under the user's home:

```default
~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log
~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/connection.yml
```

`output.log` has what the container printed, and `connection.yml` the worker it ran on and the port it listened on.

## Troubleshooting

### A Role Does Not Reach RUNNING

Check which role is stuck:

```shell
oneflow show <service_id>
```

Open a console on its VM, from Sunstone or with `onevm ssh` if the management network reaches it, and read the last lines of the configuration log:

```shell
tail -n 30 /var/log/ood-appliance-configure.log
```

The log names the step that failed. The most common causes are:

* **OneGate not reachable**: Every role reports through OneGate, and a role that cannot reach it never declares itself ready. Check that the OneGate endpoint in the VM context, `ONEGATE_ENDPOINT`, is reachable from the management network, and see the [OneGate configuration]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}).
* **The storage role cannot reach the EESSI servers**: The software cache needs outbound HTTP on ports 80 and 8000 from the storage role. The log shows the probe of the catalogue failing.
* **The portal cannot mount the home**: The storage role has not granted root on the export to the portal yet. It does so through OneGate once the portal VM exists, within about 20 seconds. A portal that waits for the mount beyond three minutes points at OneGate again.
* **The wrong address range**: `ONEAPP_POOL_RANGE` does not match the compute network, so the portal finds no workers when OneGate is not available. Check the range of the Virtual Network and the value given at instantiation.

### A Session Does Not Start

1. Check that every role is `RUNNING` with `oneflow show <service_id>`.
2. On the portal, list the workers the portal will use:

   ```shell
   cat /var/lib/ood-pool/workers.json
   ```

   A worker missing from the list is not answering on port 22 or publishes `HEALTHY=0`.
3. Read `output.log` in the session directory under the user's home. `module load` errors point at the software catalogue, `Permission denied` on the home points at the export, and a refused SSH connection at the `from=` restriction on the user's key, which only admits connections from the compute network.
4. On the worker, check what the health check found and whether the catalogue is reachable as the user:

   ```shell
   journalctl -t ood-publish-load
   runuser -u <user> -- ls /cvmfs/software.eessi.io/versions
   ```

### Users Cannot Sign In

The login page is served by Dex, which checks the credentials against the LDAP directory of the portal. On the portal VM:

```shell
systemctl status slapd ondemand-dex
ldapsearch -x -H ldap://localhost -b dc=ood,dc=local uid=<user>
```

A user who exists in the directory but cannot open a session has no Unix account on the worker. The workers resolve users through `sssd` against the portal's directory over port 389 of the compute network. On the worker, `getent passwd <user>` has to answer.

### The Pool Does Not Scale

OneFlow evaluates the elasticity policies on the average of the attributes the workers publish. Check that the workers publish them, with `onevm show` as above, and read the OneFlow log on the Front-end for the policy evaluation:

```default
/var/log/one/oneflow.log
```

The pool grows only up to `max_vms` of the role, six by default, and shrinks only after `ONEAPP_WORKER_IDLE_SECONDS` of the oldest worker being empty, plus the cooldown of the policy, five minutes.

### The VMs Are in POWEROFF After a Host Reboot

After a reboot of the Host, OpenNebula does not resume the VMs of the service on its own, and OneFlow shows the service in `WARNING`. Resume the roles in order and the service returns to `RUNNING` by itself:

```shell
onevm resume <storage vm id>
onevm resume <portal vm id>
onevm resume <worker vm ids>
```

The roles keep their configuration across a reboot, so the resumed service is the same one, with the same users and home directories.
