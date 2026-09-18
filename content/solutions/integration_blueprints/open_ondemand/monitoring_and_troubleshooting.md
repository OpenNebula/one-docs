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

The Open OnDemand Service reports its state through OneFlow, OneGate and a Prometheus endpoint on the portal.

## Metrics

The portal serves Prometheus metrics on port 9101 of its management address, at `http://<portal management address>:9101/metrics`:

| Metric | Meaning |
|---|---|
| `ood_worker_active_sessions` | Slurm jobs running on the worker, sessions included (labels `vm_id`, `name`, `address`) |
| `ood_worker_idle_seconds` | Seconds since the last job on the worker ended |
| `ood_worker_oldest_idle` | `1` when the oldest worker of the role is drained and empty, so OneFlow may remove it |
| `ood_slurm_pending` | Jobs waiting for a worker of this role, as seen by the worker |
| `ood_slurm_idle_nodes`, `ood_slurm_alloc_nodes` | Idle nodes of the cluster, and nodes with a job, as seen by the worker |
| `ood_worker_healthy` | `1` when the worker passed its last check of the home mount, the software catalogue, munge and slurmd |
| `ood_role_cardinality` | VMs in each role |
| `ood_portal_puns` | Per user web servers running on the portal, one per signed in user |
| `ood_service_state` | The OneFlow state of the service, as its numeric code (`2` is RUNNING) |
| `ood_exporter_scrape_ok` | `1` when the exporter's last read of the service through OneGate succeeded |
{.w-100}

The same values are in the user template of each worker VM, in Sunstone or in `onevm show <worker id>`. The template also holds `SESSION_USERS`, the users with a job on the worker. `SLURM_NODENAME` in the same template is the name of its Slurm node. A worker whose home mount, software catalogue, munge or slurmd fails publishes `HEALTHY=0` until it recovers. On the portal, `sinfo` lists every worker as a node with its role as a feature. `squeue` lists the sessions and the batch jobs.

## Logs

```default
/var/log/ood-appliance-configure.log      what each role did at boot, on every VM
/etc/one-appliance/status                 bootstrap_success when the role is ready
/var/log/ondemand-nginx/<user>/error.log  the user's web server, on the portal
/var/log/apache2/                         the front Apache and the login flow, on the portal
/var/log/slurm/slurmctld.log              the Slurm controller, on the portal
/var/log/slurm/slurmd.log                 the Slurm node daemon, on every worker
~/ondemand/data/sys/dashboard/batch_connect/sys/<app>/output/<session id>/output.log
                                          what a session printed, in the user's home
```

On the workers, `journalctl -t ood-slurm-elastic` shows what the elastic loop published and what the health check found. On the portal, `journalctl -t ood-slurm-reconcile` shows the nodes the reconciler removed.

## A Role Does Not Reach RUNNING

`oneflow show <service_id>` names the role. When a check stops the role, the VM carries the reason in its `ERROR` attribute. Sunstone shows it in a red banner on the VM, and `onevm show <vm id> | grep ERROR` prints it. Fix the value and instantiate the service again. When the attribute is missing, read the last lines of `/var/log/ood-appliance-configure.log` on the VM. The usual causes:

* **A switch enabled with its field empty.** `ONEAPP_HOME_NFS_ENABLED`, `ONEAPP_SLURM_CONTROLLER_ENABLED`, `ONEAPP_AUTH_OIDC_ENABLED` and `ONEAPP_PORTAL_CERTIFICATE_ENABLED` each require their fields, and the message names the missing one. The wizard cannot check this, because Sunstone validates a required field even while the switch hides it.
* **A wrong entry in the initial users.** A duplicate user name or uid, a missing password, a uid under 1000 or a name with capital letters stops the portal. The message quotes the entry.
* **OneGate not reachable.** A role that cannot reach OneGate never declares itself ready. The appliance tries `ONEGATE_ENDPOINT` from the VM context first, then port 5030 on the VM's default gateway. `/var/log/ood-appliance-configure.log` records which one answered. Check that one of the two is reachable from the management network.
* **The storage role cannot reach the EESSI servers.** It needs outbound HTTP on ports 80 and 8000.
* **The portal cannot mount the home.** The storage role grants the portal root on the export through OneGate, within about 20 seconds of the portal VM existing. If the portal still waits after three minutes, check OneGate.
* **The portal cannot mount the Slurm state.** The storage role exports `/export/slurm` to the portal address in the same way. A portal still waiting after three minutes stops with `could not mount` and the export in the message.
* **A worker never receives the munge key.** The portal publishes it as `SLURM_MUNGE_KEY` through OneGate. A worker that has waited 180 seconds for it stops with `the portal has not published SLURM_MUNGE_KEY after 180s`, so check the portal first.
* **The service stays in `DEPLOYING_NETS`.** OneFlow never leaves that state when the VM template of a role no longer exists, for example after the template was deleted and the service template was not updated. `oneflow show` reports nothing, and the exception is only in `journalctl -u opennebula-flow` on the Front-end. Point the service template at an existing VM template and instantiate again.
* **The wrong address range.** The portal takes the worker range from its compute interface, the /24 around its address. A compute network larger than a /24 needs `ONEAPP_POOL_RANGE` set to a /24 slice of it. A standalone portal needs `ONEAPP_POOL_RANGE` to match the network. The range also limits the number of Slurm nodes. A range that is not written as `first-last` stops the portal with `ONEAPP_POOL_RANGE must be "first-last"` in `/var/log/ood-appliance-configure.log`.

## A Session Does Not Start

1. Check that every role is `RUNNING`.
2. On the portal, `squeue -u <user>` shows the job of the session. `PENDING` with reason `Resources` means no worker has the cores or the memory free. The pool is growing, see [The Pool Does Not Scale](#the-pool-does-not-scale). `PartitionConfig` means no worker of the pool could ever run it, so lower the cores or the memory in the form.
3. `sinfo -R` lists the down or drained nodes with the reason. A node `drained` with reason `one-ondemand scale-down` is about to be removed. A node `down*` has stopped answering the controller, see [A Worker Is Missing from sinfo](#a-worker-is-missing-from-sinfo).
4. `sacct -j <job id>` shows how the job ended. `NODE_FAIL` means its worker died, and `OUT_OF_MEMORY` means the session used more memory than it requested.
5. Read `output.log` in the session directory. `module load` errors mean a problem with the software catalogue, and `Permission denied` on the home means a problem with the export. `/var/log/slurm/slurmd.log` on the worker records why a job could not start there.
6. On the worker, `runuser -u <user> -- ls /cvmfs/software.eessi.io/versions` shows whether that user can reach the catalogue.

## Users Cannot Sign In

On the portal, run `systemctl status slapd ondemand-dex` and `ldapsearch -x -H ldap://localhost -b dc=ood,dc=local uid=<user>`. A user who signs in but cannot open a session has no Unix account on the worker. There, `getent passwd <user>` has to answer through `sssd`. `sssd` asks the portal on port 389.

## The Pool Does Not Scale

Check that the workers publish their attributes with `onevm show`, and read `/var/log/one/oneflow.log` on the Front-end. OneFlow writes a `[AE] Checking policies for service: <id>` line for every service every `autoscaler_interval` seconds, 90 by default, and `oneflow show <service_id> --json` keeps the time of the last evaluation in `last_eval` of each policy.

When those lines stop, or `last_eval` stays empty while the workers publish `SLURM_PENDING` above 0, the evaluation thread of OneFlow has died. `systemctl restart opennebula-flow` on the Front-end starts it again without touching the service or its VMs. In OpenNebula 7.4 the thread dies when `oned` returns an empty VM monitoring pool, which happens after a Front-end outage longer than `VM_MONITORING_EXPIRATION_TIME` in `/etc/one/monitord.conf` (12 hours by default) and on a fresh installation before the first monitoring cycle. Nothing reaches `oneflow.log`; the only trace is a `terminated with exception` line from `role.rb` in `journalctl -u opennebula-flow`. After a reboot of the Front-end, check for the `[AE]` line within a few minutes.

The pool grows only while the workers publish `SLURM_PENDING` above 0, and only up to `max_vms`. `SLURM_PENDING` counts the jobs waiting for cores or memory that a worker of the role could give them; a job waiting with reason `PartitionConfig` asks for more cores than the largest worker has and never counts.

The pool shrinks only when the oldest worker publishes `OLDEST_IDLE=1`, plus the five minute cooldown of the scale down policy. The worker publishes it once it has drained its node, after `ONEAPP_WORKER_IDLE_SECONDS` without a job and nothing pending, and the node then shows as `drained` with reason `one-ondemand scale-down` in `sinfo -R`. A single worker never drains, and a drain that OneFlow does not act on within `ONEAPP_WORKER_DRAIN_SECONDS` is undone.

## A Worker Is Missing from sinfo

A worker whose node is missing from `sinfo` on the portal has not registered with the controller. On the worker, `munge -n | unmunge` has to succeed. Success proves it holds the key the portal published as `SLURM_MUNGE_KEY`. `Invalid credential` means the worker holds another key. `munged` loads a reinstalled `/etc/munge/munge.key` only after `systemctl restart munge`. `journalctl -u slurmd` shows why `slurmd` did not start or did not reach the controller. `ood-portal` in `/etc/hosts` has to resolve to the compute address of the portal, and port 6817 there has to answer.

`scontrol delete` and the reconciler both delete a node from the controller. A deleted node never returns on its own. The elastic loop of the worker therefore restarts `slurmd` when its node is absent from `sinfo` while munge and the controller answer. It does this at most once every five minutes, and the node registers again within seconds. A worker that reboots returns to `idle` on its own, 27 seconds after `onevm reboot` on the testbed. A worker that starts before its portal, for example when the VMs are resumed in the wrong order after a host outage, cannot fetch its configuration at first. Its `slurmd` unit retries every 20 seconds until the controller answers, and the elastic loop also restarts a `slurmd` that is down.

## The VMs Are in POWEROFF After a Host Reboot

OpenNebula does not resume the VMs on its own, and OneFlow shows the service in `WARNING`. Resume the storage VM, then the portal, then the workers. The service returns to `RUNNING` by itself, with its users and home directories intact. A worker resumed before the portal joins the cluster once the portal answers, because its `slurmd` keeps retrying.
