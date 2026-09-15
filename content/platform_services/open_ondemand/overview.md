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

The Open OnDemand Service deploys a complete [Open OnDemand](https://openondemand.org/) portal on OpenNebula. A user signs in from a browser, chooses an application and gets a JupyterLab notebook, RStudio, Octave, a C++ notebook or VS Code running on a compute VM, with scientific software served from the [EESSI](https://www.eessi.io/) catalogue and a home directory that follows them from session to session.

The service is designed for teams that want to offer interactive computing on their own OpenNebula cloud without running a batch scheduler first. Typical use cases include teaching and training environments, notebook access for research groups, and a self-service front end for a Slurm Cluster deployed with the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service.

The service is a OneFlow service built from a single appliance image. Three roles start from that image, and OneFlow adds and removes compute VMs from the pool as sessions open and close. Users interact with the portal only. OpenNebula, OneFlow and OneGate details are handled underneath.

## How Should I Read this Chapter

If you have not used the service before, start with the [Quick Start]({{% relref "platform_services/open_ondemand/quick_start/" %}}), where you deploy the service from the Community Marketplace and open a notebook. Then read the [Service Architecture]({{% relref "platform_services/open_ondemand/architecture/" %}}) to understand the three roles, the two networks and how a session runs.

After the introductory pages, the following references cover the day to day operation of the service:

* [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}): the service inputs, scaling, worker sizes, Slurm, external identity providers and users.
* [Operations]({{% relref "platform_services/open_ondemand/operations/" %}}): scaling by hand, keeping the home directories, upgrading and removing the service.
* [Monitoring and Troubleshooting]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/" %}}): metrics, worker health, logs and what to check when a session does not start.

## Interfaces

The service can be reached through the following interfaces:

* **Sunstone Web UI**: Instantiate, inspect and scale the service from **Instances -> Services**.
* **OneFlow CLI**: `oneflow` and `oneflow-template` for the same operations from the Front-end command line.
* **The portal**: The Open OnDemand web interface where users open sessions, browse files and submit jobs. It answers on HTTPS on the management network.
* **Prometheus metrics**: The portal serves the state of the whole service on `/metrics`, for an existing monitoring stack.

## What the Service Manages

The service is one OneFlow service with three roles. Every role boots from the same image and `ONEAPP_ROLE` decides what a VM does:

* **storage**: One VM. Exports the shared home directory over NFS and runs the site cache that serves the EESSI software catalogue over CernVM-FS.
* **portal**: One VM. Runs Open OnDemand, its own LDAP directory and Dex, the authentication service that Open OnDemand uses for the login page.
* **worker**: One to six VMs, elastic. Runs the user sessions. Each session is an Apptainer container on a worker VM, started over SSH by the portal.

The service also manages:

* **Session placement**: The portal keeps a roster of healthy workers from OneGate and sends every new session to the least loaded one.
* **Elasticity**: Workers report their open sessions to OneGate, and OneFlow adds a VM when the pool fills up and removes the oldest one when it has been empty for a while.
* **Users**: The initial users are created in the portal's LDAP directory at first boot, and a home directory is created on first login.
* **TLS**: A self-signed certificate by default, Let's Encrypt for a public host name, or a certificate of your own.

## Related Components

The service should be understood together with the following components:

* [**OneFlow**]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}): Orchestrates the three roles, starts them in order and applies the elasticity policies of the worker role.
* [**OneGate**]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}): The channel between the VMs and OpenNebula. Every role reports its readiness through it, the workers publish their session counts, and the storage and portal roles discover each other through it. OneGate must be reachable from the service networks.
* [**Open OnDemand**](https://osc.github.io/ood-documentation/latest/): The portal software, developed by the Ohio Supercomputer Center. The service uses its `linux_host` adapter for the VM pool and its `slurm` adapter for an optional Slurm Cluster.
* [**EESSI**](https://www.eessi.io/docs/): The European Environment for Scientific Software Installations, a shared software catalogue distributed over CernVM-FS. Sessions load their software from it, so the image does not age with the software it serves.
* [**Apptainer**](https://apptainer.org/docs/user/latest/): The container runtime that isolates each session on a worker VM.
* [**Elastic Slurm**]({{% relref "platform_services/slurm/" %}}): The OneSlurm service can be attached as a second cluster for batch jobs. It shares the users and the home directory with the portal.

## Supported Versions

The current appliance ships Open OnDemand 4.2 on Ubuntu 24.04 LTS, with EESSI 2025.06 and Apptainer 1.5. It runs on OpenNebula 6.10 and later, with OneFlow and OneGate enabled. Open OnDemand is MIT licensed and the appliance code is Apache 2.0.
