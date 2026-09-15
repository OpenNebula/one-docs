---
title: "Service Architecture"
linkTitle: "Service Architecture"
date: "2026-09-15"
description:
categories:
tags:
weight: "2"
type: docs
---

This section describes the architecture of the Open OnDemand Service: the three roles, the two Virtual Networks they use, how a session runs and how the pool of compute VMs grows and shrinks. Read it after the [Quick Start]({{% relref "platform_services/open_ondemand/quick_start/" %}}) and before changing the [Configuration]({{% relref "platform_services/open_ondemand/configuration/" %}}).

## Roles

The service is one OneFlow service with three roles. All of them boot from the same appliance image, and `ONEAPP_ROLE`, set per role in the service template, decides what a VM does at boot:

| Role | Cardinality | What it runs |
|---|---|---|
| `storage` | 1 | NFS server for the shared home directories, Squid cache for the EESSI software catalogue |
| `portal` | 1 | Open OnDemand, its LDAP directory, Dex for authentication, the Prometheus metrics exporter |
| `worker` | 1 to 6, elastic | User sessions, one Apptainer container per session |

{{< image path="/images/open_ondemand/light/architecture.svg" pathDark="/images/open_ondemand/dark/architecture.svg"
alt="The three roles of the service on the management and compute networks" align="center" width="90%" mb="20px" >}}

OneFlow starts the roles in order: `storage` first, `portal` when the storage role is ready, and `worker` when both are. Every role reports `READY` through OneGate only when it is actually serving, so the service reaches `RUNNING` when a user can sign in and open a session.

## Networks

Every VM of the service has two network interfaces, on the two Virtual Networks selected at instantiation:

* **Management network**: Reaches OneGate and the Internet. The portal publishes its web interface on this network, and the storage role downloads the software catalogue through it.
* **Compute network**: Reserved for the service. The three roles talk to each other on it: NFS, LDAP, SSH for the sessions and the software cache.

The roles find each other without fixed addresses. OneFlow passes the compute address of the storage role to the portal and the workers, and the storage role asks OneGate which VM plays the portal and grants root on the home export to that address alone. The compute network address range is given as `ONEAPP_POOL_RANGE`, and the portal treats every live address in that range as a worker, apart from its own and the storage role's, so nothing else may live on that network. Directory lookups travel on it in the clear, which is the other reason it stays reserved.

## How a Session Runs

1. The user signs in on the portal. Dex checks the credentials against the LDAP directory of the portal role, and Open OnDemand starts a per user web server, the PUN, as that Unix user.
2. The user chooses an application and presses **Launch**. The portal reads its roster of workers, kept up to date from OneGate, and picks the least loaded healthy worker. Among equals it picks the youngest, so a VM added by the autoscaler receives work as soon as it is ready and the oldest one drains as its sessions end.
3. The portal connects to that worker over SSH as the user, with a key it keeps in the user's home, and starts the session inside an Apptainer container. The container sees the VM filesystem, the shared home and the EESSI catalogue mounted from CernVM-FS.
4. The application listens on a port of the worker, and the portal proxies the browser to it. The user works in JupyterLab, RStudio or VS Code as if it were local.
5. When the user deletes the session, or its walltime runs out, the container stops and the worker reports one session fewer.

There is no batch scheduler on the pool. A worker holds every session that lands on it, up to `ONEAPP_WORKER_MAX_SESSIONS`, and the sessions on one VM share its CPU and memory.

## How the Pool Grows and Shrinks

Every worker publishes its state to OneGate every ten seconds, as attributes of its own VM:

| Attribute | Meaning |
|---|---|
| `ACTIVE_SESSIONS` | Sessions open on this worker |
| `AT_CAPACITY` | `1` when the worker holds `ONEAPP_WORKER_MAX_SESSIONS` sessions |
| `OLDEST_IDLE` | `1` when the oldest worker of the role has been empty for `ONEAPP_WORKER_IDLE_SECONDS` |
| `HEALTHY` | `1` when the home mount, the software catalogue and sshd are all in place |
| `SESSION_USERS` | Who has a session on this worker and since when, as `user:epoch` |

OneFlow evaluates the elasticity policies of the worker role on the average of those attributes across the role:

* **Grow**: one VM is added when the average of `ACTIVE_SESSIONS` passes 1, or when every worker reports `AT_CAPACITY`.
* **Shrink**: one VM is removed when the oldest worker has been empty for `ONEAPP_WORKER_IDLE_SECONDS`, ten minutes by default. OneFlow removes the oldest VM of the role, and the placement rule above keeps that VM empty once its last session ends.

The pool changes one VM at a time and never goes below one worker or above the `max_vms` of the role, six in the marketplace template. A new worker is serving about 40 seconds after OneFlow creates it.

## Ports

If a firewall sits between the networks, these are the flows the service needs:

| From | To | Port | Purpose |
|---|---|---|---|
| Users | portal, management network | 443, and 80 with `letsencrypt` | The web interface |
| portal | workers | 22 | Starting and stopping sessions |
| workers | portal | 389 | Resolving users against the directory |
| portal and workers | storage | 2049 | The shared home over NFSv4 |
| portal and workers | storage | 3128 | The software catalogue through the site cache |
| Every role | OneGate endpoint | 5030 by default | Readiness and session counts |
| Prometheus | portal, management network | 9101 | Service metrics, only if scraped |
| storage | Internet | 80 and 8000 | The EESSI CernVM-FS servers, plain HTTP |

## Requirements

* OpenNebula 6.10 or later, with [OneFlow]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}) and [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}) enabled, and the OneGate endpoint reachable from the service networks.
* Two Virtual Networks as described above, the compute one reserved for the service.
* Outbound HTTP access from the storage role to the EESSI CernVM-FS servers.
* Capacity for three VMs plus the workers you expect. The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal. Size the worker role for the sessions it will hold, see [Configuration]({{% relref "platform_services/open_ondemand/configuration/#sizing-the-roles" %}}).
