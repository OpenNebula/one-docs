---
title: "Core Concepts"
linkTitle: "Core Concepts"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "4"
---

## Controller and Workers

| | **Controller** | **Worker** |
|---|---|---|
| Slurm daemon | `slurmctld` | `slurmd` |
| Number of VMs | 1 | 1 or more |
| Hostname | `slurm-one-controller` | The VM name, for example `worker-0--service-233` |
| Role in the Cluster | Schedules jobs, keeps the configuration, hosts the optional local LDAP | Runs jobs |

Users connect to the controller to compile code and submit jobs with `srun` or `sbatch`.

## Configless Slurm

The controller is the only VM that has the Slurm configuration files. The workers start `slurmd` with `--conf-server slurm-one-controller:6817` and download the configuration from the controller. A change on the controller reaches every worker, and new workers need no configuration.

## Dynamic Nodes

Workers join Slurm as dynamic nodes (`slurmd -Z`). Each worker reports to the controller what it has.

* Its CPUs, from `nproc`
* Its memory, from `/proc/meminfo`
* Its NVIDIA GPUs, from `nvidia-smi`, as the `gpu` GRES

The nodes are not listed in `slurm.conf`.

## OneGate Coordination

The controller and the workers share their data through OneGate, which keeps data on each VM of the service.

1. The controller starts, configures Slurm and publishes `READY=YES` and the Munge key.
2. OneFlow waits for `READY=YES` before it creates the workers. This is the `ready_status_gate` option of the service. The VM templates also set `REPORT_READY=YES`, so one-context reports readiness too.
3. Each worker reads the controller IP, the Munge key and the LDAP settings from OneGate.
4. Each worker checks that port 6817 of the controller answers, then starts `slurmd`.
5. Each worker publishes its Slurm node name as `SLURM_NODENAME`.

Refer to [Service Architecture]({{% relref "platform_services/slurm/references/service_architecture" %}}) for a list of every attribute that the VMs publish.

## Munge Key

Slurm uses [Munge](https://dun.github.io/munge/) to authenticate the messages between the daemons. All the VMs of a Cluster need the same key.

* The controller creates the key at its first boot and keeps it.
* It publishes the key in base64 to OneGate as `SLURM_MUNGE_KEY`.
* Each worker installs the key and checks that Munge works before it starts `slurmd`.

## Scaling and Cleanup

When you remove workers, two mechanisms remove them from Slurm.

* Each worker deletes its own node from Slurm when it shuts down normally.
* The controller checks every 60 seconds, starting 2 minutes after boot, for nodes that have no VM anymore and that Slurm sees as down. It deletes them, or drains them if they still have running jobs.

Refer to [Cluster Lifecycle Management]({{% relref "platform_services/slurm/management/cluster_lifecycle_management" %}}) for more details.
