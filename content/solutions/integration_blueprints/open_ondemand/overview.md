---
title: "Overview"
linkTitle: "Overview"
date: "2026-09-15"
description:
categories:
tags:
weight: "1"
type: docs
---

The Open OnDemand Service deploys an [Open OnDemand](https://openondemand.org/) portal on OpenNebula. A user can sign in from a browser and open JupyterLab, RStudio, Octave, a C++ notebook, VS Code or an Xfce desktop on a compute VM. Scientific software comes from the [EESSI](https://www.eessi.io/) catalogue, and the home directory is the same in every session.

The service is a OneFlow service built from one appliance image. Three roles boot from it, and every session is a job of the service's own Slurm Cluster. OneFlow adds a compute VM when a job waits for one, and removes the oldest worker after it has been idle for a period. The service brings its own Slurm Cluster and needs no other Cluster. It suits teaching environments and notebook access for research groups.

## How Should I Read this Chapter

Start with the [Quick Start Guide]({{% relref "solutions/integration_blueprints/open_ondemand/quick_start/" %}}) to deploy the Open OnDemand service from the Community Marketplace and open a notebook. The [Service Architecture]({{% relref "solutions/integration_blueprints/open_ondemand/architecture/" %}}) explains the roles, the networks and how a session runs. Then, consult the following guides for further details:

* [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/" %}}): Covers inputs, scaling, worker sizes, Slurm, external identity providers and users.
* [Operations]({{% relref "solutions/integration_blueprints/open_ondemand/operations/" %}}): Covers manual scaling, persistent home directories, upgrades and removal.
* [Monitoring and Troubleshooting]({{% relref "solutions/integration_blueprints/open_ondemand/monitoring_and_troubleshooting/" %}}): Covers metrics, logs, and what to check when something fails.

## Usage Model in a Multi-Tenant Cloud

The service suits a cloud where several groups share one OpenNebula Front-end and each group works inside its own Virtual Data Center (VDC). Three actors take part, and only two of them need an OpenNebula account.

* **Infrastructure Admin**: Manages the OpenNebula cloud and downloads the Open OnDemand Service from the Community Marketplace, which makes the image, the VM template and the service template available to every group. The admin also prepares what belongs to the site, including the two Virtual Networks, the quotas of each VDC, the `autoscaler_interval` setting of the Front-end and, for infrastructure including GPUs, the PCI passthrough configuration of the Hosts.
* **Tenant Operator**: Belongs to a group within a VDC. Instantiates the service from Sunstone inside that VDC and chooses the networks and the inputs. Creates the accounts of the end users in Open OnDemand, with `ONEAPP_AUTH_LOCAL_USERS` or through an OpenID Connect provider of the group. Watches the service, scales the worker role by hand when needed, and removes the service when the group no longer needs it. The VMs of the service count against the quotas of the VDC.
* **OnDemand End User**: A researcher of the group. Signs in to the portal from a browser with the account the Tenant Operator created, opens JupyterLab, RStudio, VS Code or a desktop, and submits batch jobs. The OnDemand end user does not require an OpenNebula account and never interacts with Sunstone. Every session runs as a Slurm job under that user, with the cores and the memory requested with the job.

The unit of isolation between groups is the Open OnDemand Service instance, not the portal inside it. Each instance has one list of user accounts, one Slurm Cluster and one shared home export, in which each user has a home directory of their own. Its users share the portal, the workers and the quotas, separated from each other only as Unix users and Slurm jobs. Two groups that must not share users, data or queue should run two instances of the service, each in its own VDC, and OpenNebula keeps them isolated.

## What the Service Manages

Every VM boots from the same image. `ONEAPP_ROLE`, set for each role in the service template, decides what the VM does:

* **storage**: A single VM. It exports the shared home directory, the state of the Slurm controller and the shared software directory over NFS, and caches the EESSI software catalogue.
* **portal**: A single VM. It runs Open OnDemand, the LDAP directory, the Dex login service, and the Slurm controller with its accounting database.
* **worker**: One to six VMs, scaled by OneFlow. Each VM joins the Cluster as a Slurm worker node and runs the user sessions as jobs. Each job gets only the cores and the memory it requested.

The service also creates the initial users at first boot and keeps an accounting record of every session. It gives the portal a TLS certificate, which is self-signed by default. For a public name, the certificate comes from [Let's Encrypt](https://letsencrypt.org/), or you can use one of your own.

## Slurm Components

The service uses Slurm 23.11 as its job scheduler. A job is a request for cores, memory and time, together with the command to run. Every interactive session and every batch job from the Job Composer is a Slurm job. These are the components and where they run.

| **Component** | **Runs on** | **Function** |
|---|---|---|
| `slurmctld`, the controller | portal | Keeps the list of nodes with their free cores and memory, keeps the job queue, and assigns each job to a node that has the requested resources. A job that fits on no node waits in the queue. |
| `slurmd`, the node daemon | every worker | Registers the worker as a node at boot, starts the jobs the controller assigns, as the requesting user, and limits each job to its cores and memory with cgroup v2. |
| `slurmdbd` and MariaDB, the accounting | portal | Record every job with its user, its node and its start and end times. `sacct` reads the record. |
| munge, the authentication | every role | Signs every message between the Slurm daemons and commands with a key shared by all the VMs of the service. A VM without the key cannot join the Cluster or submit jobs. The portal generates the key at first boot and publishes it to the workers through OneGate. |
| OpenMPI and PMIx, multi-node jobs | workers, from EESSI | Let a batch job run processes on several workers at once. The job requests the nodes with `sbatch -N <n>` and starts the processes with `srun --mpi=pmix` or `mpirun`. Interactive sessions use one worker each. |
{.w-100}

## Related Components

* [**OneFlow**]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}): Starts the roles in order and applies the elasticity policies of the worker role.
* [**OneGate**]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}): The channel between the VMs and OpenNebula. Roles report readiness through it, and the portal publishes the Cluster's munge key. The workers publish the queue figures that OneFlow uses to scale. OneGate must be reachable from the service networks.
* [**Open OnDemand**](https://osc.github.io/ood-documentation/latest/): The portal software, from the Ohio Supercomputer Center. The service uses its `slurm` adapter for its own Cluster and for an optional second Slurm Cluster.
* [**Slurm**](https://slurm.schedmd.com/): The workload manager, version 23.11 from Ubuntu 24.04. The portal runs the controller and the accounting daemon. Every worker joins as a dynamic node. Every session is a job, and cgroup v2 limits it to its cores and memory.
* [**EESSI**](https://www.eessi.io/docs/): A shared scientific software catalogue distributed over CernVM-FS. The image ships the CernVM-FS client and a site cache. The software itself is fetched on demand.
* [**Elastic Slurm**]({{% relref "platform_services/slurm/" %}}): The OneSlurm service is optional. The Open OnDemand Service does not use it. A site that already runs one can attach it as a second Cluster for batch jobs, with the same users and home directory, as described in [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#an-external-slurm-cluster" %}}).

## Supported Versions

The appliance ships Open OnDemand 4.2 on Ubuntu 24.04 LTS, with Slurm 23.11.4, munge 0.5.15 and MariaDB 10.11 from the Ubuntu archive. It also ships EESSI 2025.06, Apptainer 1.5, TurboVNC 3.3 and Xfce 4.18. It runs on OpenNebula 6.10 and later with OneFlow and OneGate enabled. Open OnDemand is MIT licensed and the appliance code is Apache 2.0.
