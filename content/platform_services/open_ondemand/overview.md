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

The Open OnDemand Service deploys an [Open OnDemand](https://openondemand.org/) portal on OpenNebula. A user signs in from a browser and opens JupyterLab, RStudio, Octave, a C++ notebook, VS Code or an Xfce desktop on a compute VM, with scientific software from the [EESSI](https://www.eessi.io/) catalogue and a home directory that follows them from session to session.

The service is a OneFlow service built from one appliance image. Three roles boot from it, every session is a job of a Slurm cluster the service runs itself, and OneFlow adds a compute VM when a job waits for one and removes the oldest worker once it has been idle. It suits teaching environments, notebook access for research groups, and a browser front end for a Slurm Cluster deployed with the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service.

## How Should I Read this Chapter

Start with the [Quick Start]({{% relref "platform_services/open_ondemand/quick_start/" %}}) to deploy the service from the Community Marketplace and open a notebook. The [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}) explains the roles, the networks and how a session runs. Then:

* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}): inputs, scaling, worker sizes, Slurm, external identity providers, users.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}): manual scaling, persistent home directories, upgrades, removal.
* [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/" %}}): metrics, logs and what to check when something fails.

## What the Service Manages

Every VM boots from the same image and `ONEAPP_ROLE`, set per role in the service template, decides what it does:

* **storage**: One VM. Exports the shared home directory and the state of the Slurm controller over NFS and caches the EESSI software catalogue.
* **portal**: One VM. Runs Open OnDemand, its LDAP directory, Dex, the login service, and the Slurm controller with its accounting database.
* **worker**: One to six VMs, elastic. Joins the cluster as a Slurm node and runs the user sessions as jobs, each one fenced to the cores and the memory it asked for.

The service also creates the initial users at first boot, keeps an accounting record of every session, and gets the portal a TLS certificate, self-signed by default, from Let's Encrypt for a public name, or one of your own.

## Related Components

* [**OneFlow**]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}): starts the roles in order and applies the elasticity policies of the worker role.
* [**OneGate**]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}): the channel between the VMs and OpenNebula. Roles report readiness through it, the portal publishes the munge key of the cluster and the workers publish the queue figures OneFlow scales on. It must be reachable from the service networks.
* [**Open OnDemand**](https://osc.github.io/ood-documentation/latest/): the portal software, by the Ohio Supercomputer Center. The service uses its `slurm` adapter for the cluster of the service and for an optional second Slurm Cluster.
* [**Slurm**](https://slurm.schedmd.com/): the workload manager, version 23.11 from Ubuntu 24.04. The portal runs the controller and the accounting daemon, every worker joins as a dynamic node, and every session is a job with its cores and memory fenced by cgroup v2.
* [**EESSI**](https://www.eessi.io/docs/): a shared scientific software catalogue distributed over CernVM-FS. The image ships the CernVM-FS client and a site cache; the software itself is fetched on demand.
* [**Elastic Slurm**]({{% relref "platform_services/slurm/" %}}): the OneSlurm service can be attached as a second cluster for batch jobs, sharing the users and the home directory.

## Supported Versions

The appliance ships Open OnDemand 4.2 on Ubuntu 24.04 LTS, Slurm 23.11.4, munge 0.5.15 and MariaDB 10.11 from the Ubuntu archive, EESSI 2025.06, Apptainer 1.5, TurboVNC 3.3 and Xfce 4.18. It runs on OpenNebula 6.10 and later with OneFlow and OneGate enabled. Open OnDemand is MIT licensed and the appliance code is Apache 2.0.
