---
title: "Requirements and Preparation"
linkTitle: "Requirements"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "2"
---

## Requirements

| Requirement | Details |
|---|---|
| OpenNebula | 7.0, 7.2 or 7.4 |
| OneFlow | Running. OneSlurm is a OneFlow service |
| OneGate | Running and reachable from the controller and worker VMs |
| OneGate to OneFlow | OneGate can reach the OneFlow API |
| Virtual Network | One network for the service. The controller and the workers attach to it |
| Port 6817/TCP | Open from the workers to the controller, for `slurmctld` and configless Slurm |

### OneGate Details

* The controller publishes the cluster data through [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate" %}}), and the workers read it. Without OneGate, no worker joins the cluster.
* The VMs can reach OneGate directly or through the [transparent proxies]({{% relref "product/virtual_machines_operation/virtual_machines_networking/tproxy" %}}).
* OneGate must reach the active OneFlow server. The `:oneflow_server:` setting in `/etc/one/onegate-server.conf` sets it.

To check it, run this command in any VM of the service. It must print the service, not `Service <id> not found`.

```shell
$ onegate service show
```

### VM Size

The Marketplace templates use these defaults. They cover the Slurm daemons only, so size the workers for your jobs.

| Role | CPU | Memory | Disk |
|---|---|---|---|
| Controller | 2 | 2 GB | 10 GB |
| Worker | 1 | 1 GB | 10 GB |

## Optional Features

Prepare these before you create the service, only for the features you want.

| Feature | What you need first | Guide |
|---|---|---|
| Shared users | Nothing for the local LDAP on the controller. For an external LDAP, its URL and its domain or base DN | [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| Shared storage | NFS exports for `/home` and `/scratch`, reachable from all the VMs | [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}) |
| GPUs | NVIDIA GPUs on the Hosts, with PCI passthrough configured | [Worker Profiles and Accelerators]({{% relref "platform_services/slurm/management/worker_profiles_and_accelerators" %}}) |
| InfiniBand | An InfiniBand HCA for each worker, and a subnet manager already running on the fabric | [InfiniBand]({{% relref "platform_services/slurm/management/infiniband" %}}) |
