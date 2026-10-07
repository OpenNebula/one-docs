---
title: "Overview"
linkTitle: "Overview"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "1"
aliases:
  - /platform_services/slurm/overview/
---

[Slurm](https://slurm.schedmd.com/documentation.html) is an open source workload manager and job scheduler for AI and HPC workloads on Linux clusters. It gives jobs access to compute nodes, starts and monitors them, and keeps pending jobs in a queue.

OneSlurm deploys a Slurm cluster on OpenNebula as a OneFlow service. The service has two roles:

| Role | Appliance | What it does |
|---|---|---|
| `controller` | [Service Slurm Controller](https://marketplace.opennebula.io/appliance/db17c081-969f-45e0-9c8b-e0f7236c15aa) | Runs `slurmctld`, schedules jobs and owns the Slurm configuration. Users log in here to submit jobs |
| `worker` | [Service Slurm Worker](https://marketplace.opennebula.io/appliance/c03f8c40-39bb-42cd-a9d5-781f59846b57) | Runs `slurmd` and executes jobs. You can add or remove workers at any time |

Both roles come together in the [Service OneSlurm](https://marketplace.opennebula.io/appliance/8ce164d5-3cce-42a7-b9a7-0e8133ef92c6) appliance of the OpenNebula Public Marketplace. The controller publishes the cluster data through OneGate, and each worker reads it and joins the cluster without manual steps.

Optional features are set when you create the service.

* Shared user accounts through a local or an external LDAP directory.
* Shared `/home` and `/scratch` from NFS exports.
* NVIDIA GPUs attached to the workers.
* InfiniBand for MPI jobs.

## How Should I Read This Chapter

1. Check [Requirements and Preparation]({{% relref "platform_services/slurm/getting_started/requirements" %}}).
2. Deploy a first cluster with the [Quick Start]({{% relref "platform_services/slurm/getting_started/quick_start" %}}).
3. Read [Core Concepts]({{% relref "platform_services/slurm/getting_started/core_concepts" %}}) to understand how the controller and the workers work together.

Then use the Management pages for daily operation.

* [Cluster Lifecycle Management]({{% relref "platform_services/slurm/management/cluster_lifecycle_management" %}})
* [Cluster Configuration]({{% relref "platform_services/slurm/management/cluster_configuration" %}})
* [Worker Profiles and Accelerators]({{% relref "platform_services/slurm/management/worker_profiles_and_accelerators" %}})
* [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}})
* [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}})
* [InfiniBand and High-Performance Networking]({{% relref "platform_services/slurm/management/infiniband" %}})
* [Monitoring and Troubleshooting]({{% relref "platform_services/slurm/management/monitoring_and_troubleshooting" %}})

The References pages list the [Service Architecture]({{% relref "platform_services/slurm/references/service_architecture" %}}), every [Configuration Parameter]({{% relref "platform_services/slurm/references/configuration_parameters" %}}) and the [CLI]({{% relref "platform_services/slurm/references/oneslurm_cli" %}}) commands.

There is also a [OneSlurm tutorial]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/nvidia_slurm/" %}}) with NVIDIA GPUs in the AI Factory Blueprints.

{{< alert title="Note" type="info" >}}
An **OpenNebula Cluster** groups Hosts, datastores and Virtual Networks. A **Slurm cluster** is a group of VMs that run Slurm. A Slurm cluster deployed by OneSlurm runs as a workload on top of OpenNebula resources, and you can run several Slurm clusters in one OpenNebula Cluster.
{{< /alert >}}

## Release Notes

| Item | Value |
|---|---|
| Appliance version | `7.4.0-1-20260807` |
| Guest OS | Ubuntu 26.04 LTS |
| Architectures | `x86_64` and `aarch64` |
| Slurm | 25.11, from the Ubuntu packages |
| OpenNebula | 7.0, 7.2 and 7.4 |

The [one-apps release page](https://github.com/OpenNebula/one-apps/releases) lists the changes of each version.

## Known Limitations

| Limitation | Effect |
|---|---|
| No `slurmdbd` | No job accounting, job history or usage statistics through SlurmDB |
| Munge only | Munge is the only Slurm authentication method |
| One controller | The controller has no failover. If it stops, no new jobs start until it is back |
| Up to 100 workers | `slurm.conf` sets `MaxNodeCount=100` |
| LDAP without TLS | The LDAP clients connect with plain `ldap://`. See [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}) |
