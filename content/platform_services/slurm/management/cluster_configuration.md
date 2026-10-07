---
title: "Cluster Configuration"
linkTitle: "Cluster Configuration"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "2"
---

The controller writes the Slurm configuration. The workers download it from the controller at start (configless mode), so they have no configuration files of their own.

## Files on the Controller

| File | Content |
|---|---|
| `/etc/slurm/slurm.conf` | Cluster, scheduler, plugins and partition |
| `/etc/slurm/gres.conf` | `AutoDetect=nvidia`, to find NVIDIA GPUs |
| `/etc/slurm/cgroup.conf` | `CgroupAutomount=yes` and `ConstrainDevices=yes` |

## Default `slurm.conf`

| Setting | Value | Meaning |
|---|---|---|
| `ClusterName` | `one` | Name of the Slurm cluster |
| `SlurmctldHost` | `slurm-one-controller` | Hostname of the controller |
| `AuthType` | `auth/munge` | Munge authentication |
| `SchedulerType` | `sched/backfill` | Backfill scheduling |
| `SelectType` | `select/cons_tres` | Allocates CPUs, memory and GPUs per job |
| `ProctrackType` | `proctrack/cgroup` | Tracks job processes with cgroups |
| `TaskPlugin` | `task/cgroup,task/affinity` | Limits tasks with cgroups and pins them to CPUs |
| `GresTypes` | `gpu` | GPUs as generic resources |
| `SlurmctldParameters` | `enable_configless` | Workers download the configuration |
| `MaxNodeCount` | `100` | Maximum number of dynamic nodes |
| `Nodeset` | `one Feature=one` | Groups all the workers |
| `PartitionName` | `all Nodes=ALL Default=yes` | One partition with all the nodes |

With InfiniBand enabled, the controller also adds `MpiDefault=pmix` and `PropagateResourceLimitsExcept=MEMLOCK`. See [InfiniBand]({{% relref "platform_services/slurm/management/infiniband" %}}).

## Changes to the Configuration

{{< alert title="Important" type="warning" >}}
The controller writes `slurm.conf`, `gres.conf` and `cgroup.conf` again every time it boots. Changes that you make by hand in these files are lost after a reboot of the controller.
{{< /alert >}}

To change the cluster, use the service inputs when you create it. The [Configuration Parameters]({{% relref "platform_services/slurm/references/configuration_parameters" %}}) page lists them all.

| You want | How |
|---|---|
| Shared users | LDAP inputs, see [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| Shared `/home` and `/scratch` | NFS inputs, see [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}) |
| MPI over InfiniBand | InfiniBand inputs, see [InfiniBand]({{% relref "platform_services/slurm/management/infiniband" %}}) |
| More CPU, memory or GPUs per worker | Worker VM template, see [Worker Profiles and Accelerators]({{% relref "platform_services/slurm/management/worker_profiles_and_accelerators" %}}) |

The appliance does not configure accounting (`slurmdbd`), QoS or more partitions.
