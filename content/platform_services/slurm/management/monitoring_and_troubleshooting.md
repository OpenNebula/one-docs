---
title: "Monitoring and Troubleshooting"
linkTitle: "Troubleshooting"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "7"
---

## Check the Cluster

Connect to the controller and use the Slurm commands.

```shell
$ onevm ssh <controller_vm_id>
```

| Command | Shows |
|---|---|
| `sinfo` | Partitions and the state of each node |
| `scontrol show nodes` | CPUs, memory, GPUs and state of each node |
| `squeue` | Pending and running jobs |
| `onegate service show` | The VMs of the service, as OneGate sees them |
| `systemctl status slurmctld` | The Slurm controller daemon |

On a worker, `systemctl status slurmd` shows the Slurm node daemon.

## Appliance Logs and Status

Every VM of the service writes the same files.

| File | Content |
|---|---|
| `/etc/one-appliance/status` | `bootstrap_success` when the appliance finished without errors |
| `/var/log/one-appliance/configure.log` | Log of the configuration at each boot |
| `/var/log/one-appliance/bootstrap.log` | Log of the last stage |
| `/var/log/one-appliance/install.log` | Log of the image build |

The reconciler of the controller writes to the journal.

```shell
$ journalctl -u oneslurm-reconcile
```

## Common Problems

| Symptom | Cause | Fix |
|---|---|---|
| The service stays in `DEPLOYING` and no worker appears | The controller did not publish `READY=YES` | Read `configure.log` on the controller |
| `onegate service show` prints `Service <id> not found` | OneGate cannot reach OneFlow | Set `:oneflow_server:` in `/etc/one/onegate-server.conf` |
| Worker log shows `Could not discover Slurm controller through OneGate` | The worker cannot read the controller data | Check OneGate from the worker with `onegate service show` |
| Worker log shows `Cannot connect to Slurm controller at <ip>:6817` | Port 6817 is closed between the worker and the controller | Open 6817/TCP in the security groups and firewalls |
| A node stays `DOWN` after a scale down | The worker VM stopped without a normal shutdown | Wait about one minute for the reconciler, then check `journalctl -u oneslurm-reconcile` |
| A node is `DRAIN` with the reason `removed from OneFlow service` | Its VM left the service while jobs were running | Cancel the jobs, or wait for them, then delete the node with `scontrol delete NodeName=<node>` |
| `getent passwd <user>` prints nothing | SSSD does not reach LDAP, or the user is not in `ou=People` | Check `systemctl status sssd` and the LDAP inputs |
| `/home` is not mounted | The NFS export is wrong or not reachable | Check the input format `host:/export` and run `findmnt /home` |

## Check the Optional Features

| Feature | Command on the controller |
|---|---|
| LDAP users | `getent passwd <user>`, `getent group <group>` and `srun -N1 -n1 getent passwd <user>` |
| NFS | `findmnt /home` and `srun -N1 -n1 findmnt /home` |
| GPUs | `srun -N1 -n1 --gres=gpu:1 nvidia-smi -L` |
| InfiniBand | `scontrol show config \| grep MpiDefault` |
