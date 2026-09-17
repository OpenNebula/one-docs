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

The Open OnDemand Service deploys an [Open OnDemand](https://openondemand.org/) portal on OpenNebula. A user signs in from a browser and opens JupyterLab, RStudio, Octave, a C++ notebook, VS Code or an Xfce desktop on a compute VM. Scientific software comes from the [EESSI](https://www.eessi.io/) catalogue, and the home directory is the same in every session.

The service is a OneFlow service built from one appliance image. Three roles boot from it, and every session is a job of the service's own Slurm cluster. OneFlow adds a compute VM when a job waits for one, and removes the oldest worker once it has been idle. The service brings its own Slurm cluster and needs no other cluster. It suits teaching environments and notebook access for research groups.

## How Should I Read this Chapter

Start with the [Quick Start]({{% relref "platform_services/open_ondemand/quick_start/" %}}) to deploy the service from the Community Marketplace and open a notebook. The [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}) explains the roles, the networks and how a session runs. Then:

* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}) covers inputs, scaling, worker sizes, Slurm, external identity providers and users.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}) covers manual scaling, persistent home directories, upgrades and removal.
* [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/" %}}) covers metrics, logs, and what to check when something fails.

## What the Service Manages

Every VM boots from the same image. `ONEAPP_ROLE`, set for each role in the service template, decides what the VM does:

* **storage**. One VM. It exports the shared home directory and the state of the Slurm controller over NFS, and caches the EESSI software catalogue.
* **portal**. One VM. It runs Open OnDemand, the LDAP directory, the Dex login service, and the Slurm controller with its accounting database.
* **worker**. One to six VMs, scaled by OneFlow. Each one joins the cluster as a Slurm node and runs the user sessions as jobs. Each job gets only the cores and the memory it requested.

The service also creates the initial users at first boot and keeps an accounting record of every session. It gives the portal a TLS certificate, which is self-signed by default. For a public name the certificate comes from Let's Encrypt, or you can use one of your own.

## Slurm in Plain Words

Slurm is the program that decides where each job runs. A job is a request, for example 2 cores and 4 GB of memory for 3 hours, plus the command to run. The controller (`slurmctld`) on the portal keeps a list of the nodes, the free cores and memory on each one, and a queue of jobs. When a job fits on a node, the controller sends it to the `slurmd` program on that node. `slurmd` starts the job as the user and limits it to the cores and memory requested, with Linux cgroups. When nothing fits, the job waits in the queue. Every session in the portal is such a job, and so is every batch job from the Job Composer. The accounting daemon (`slurmdbd`) writes every job to a MariaDB database, so `sacct` shows who ran what, where and for how long.

Munge is the service that lets the portal and the workers trust each other. Every message between the Slurm programs carries a token signed with a secret key that all the VMs of the service share. A VM without the key cannot join the cluster or submit jobs. The portal creates the key at first boot and gives it to each worker through OneGate.

MPI (Message Passing Interface) is the library that programs use to run on several nodes at the same time and exchange data. The EESSI catalogue provides OpenMPI. A batch job requests several workers with `sbatch -N 2` and starts its processes with `srun --mpi=pmix` or `mpirun`. The VMs see the CPU of the host, so EESSI loads the software built for that CPU family and the MPI library starts. Interactive sessions use one worker each.

## Related Components

* [**OneFlow**]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}) starts the roles in order and applies the elasticity policies of the worker role.
* [**OneGate**]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}) is the channel between the VMs and OpenNebula. Roles report readiness through it, and the portal publishes the cluster's munge key. The workers publish the queue figures that OneFlow uses to scale. OneGate must be reachable from the service networks.
* [**Open OnDemand**](https://osc.github.io/ood-documentation/latest/) is the portal software, from the Ohio Supercomputer Center. The service uses its `slurm` adapter for its own cluster and for an optional second Slurm Cluster.
* [**Slurm**](https://slurm.schedmd.com/) is the workload manager, version 23.11 from Ubuntu 24.04. The portal runs the controller and the accounting daemon. Every worker joins as a dynamic node. Every session is a job, and cgroup v2 limits it to its cores and memory.
* [**EESSI**](https://www.eessi.io/docs/) is a shared scientific software catalogue distributed over CernVM-FS. The image ships the CernVM-FS client and a site cache. The software itself is fetched on demand.
* [**Elastic Slurm**]({{% relref "platform_services/slurm/" %}}), the OneSlurm service, is optional. The Open OnDemand Service does not use it. A site that already runs one can attach it as a second cluster for batch jobs, with the same users and home directory, as described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/#an-external-slurm-cluster" %}}).

## Supported Versions

The appliance ships Open OnDemand 4.2 on Ubuntu 24.04 LTS, with Slurm 23.11.4, munge 0.5.15 and MariaDB 10.11 from the Ubuntu archive. It also ships EESSI 2025.06, Apptainer 1.5, TurboVNC 3.3 and Xfce 4.18. It runs on OpenNebula 6.10 and later with OneFlow and OneGate enabled. Open OnDemand is MIT licensed and the appliance code is Apache 2.0.
