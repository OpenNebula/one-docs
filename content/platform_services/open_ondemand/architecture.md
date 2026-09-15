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

This section describes the three roles of the Open OnDemand Service, the two Virtual Networks they use, how a session runs and how the pool of compute VMs grows and shrinks.

## Roles

| Role | Cardinality | What it runs |
|---|---|---|
| `storage` | 1 | NFS server for the shared home directories, Squid cache for the EESSI catalogue |
| `portal` | 1 | Open OnDemand, its LDAP directory, Dex, the Prometheus metrics exporter |
| `worker` | 1 to 6, elastic | User sessions, one Apptainer container per session |
{.w-100}

{{< image path="/images/open_ondemand/light/architecture.svg" pathDark="/images/open_ondemand/dark/architecture.svg"
alt="The storage, portal and worker roles between the management and compute networks, with the flows between them" align="center" width="100%" mb="20px" >}}

OneFlow starts `storage` first, `portal` when the storage role is ready, and `worker` when both are. Each role reports `READY` through OneGate only when it is actually serving, so the service reaches `RUNNING` when a user can sign in and open a session.

## Networks

Every VM has two network interfaces:

* **Management network**: reaches OneGate and the Internet. The portal publishes its web interface here, and the storage role downloads the software catalogue through it.
* **Compute network**: reserved for the service. NFS, LDAP, the session SSH connections and the software cache run on it.

The roles find each other without fixed addresses. OneFlow passes the compute address of the storage role to the portal and the workers, and the storage role asks OneGate which VM is the portal. `ONEAPP_POOL_RANGE` is the address range of the compute network, and the portal treats every live address in it as a worker, apart from its own and the storage role's, so nothing else may live on that network.

## How a Session Runs

1. The user signs in. Dex checks the credentials against the LDAP directory, or against an external OpenID Connect provider, and Open OnDemand starts a per user web server as that Unix user.
2. The user launches an application. The portal picks the least loaded healthy worker from its OneGate roster and, among equals, the youngest, so a VM the autoscaler just added receives work.
3. The portal connects to the worker over SSH as the user and starts the session inside an Apptainer container that sees the VM filesystem, the home directory and the EESSI catalogue.
4. The application listens on a port of the worker and the portal proxies the browser to it. Desktops run under a TurboVNC server on the worker and reach the browser through noVNC on the portal.
5. Deleting the session, or reaching its walltime, stops the container.

There is no scheduler on the pool. A worker holds up to `ONEAPP_WORKER_MAX_SESSIONS` sessions, which share its CPU and memory.

## How the Pool Grows and Shrinks

Every worker publishes these attributes to OneGate every ten seconds:

| Attribute | Meaning |
|---|---|
| `ACTIVE_SESSIONS` | Sessions open on this worker |
| `AT_CAPACITY` | `1` when the worker holds `ONEAPP_WORKER_MAX_SESSIONS` sessions |
| `OLDEST_IDLE` | `1` when the oldest worker of the role has been empty for `ONEAPP_WORKER_IDLE_SECONDS` |
| `HEALTHY` | `1` when the home mount, the software catalogue and sshd are all in place |
| `SESSION_USERS` | Who has a session on this worker and since when, as `user:epoch` |
{.w-100}

OneFlow evaluates the elasticity policies on the average across the role. It adds one VM when the average of `ACTIVE_SESSIONS` passes 1 or when every worker is at capacity, and removes the oldest VM when it has been empty for `ONEAPP_WORKER_IDLE_SECONDS`, ten minutes by default. The pool changes one VM at a time between 1 and `max_vms`, six in the marketplace template. A new worker is serving about 40 seconds after OneFlow creates it.

## Ports

| From | To | Port | Purpose |
|---|---|---|---|
| Users | portal, management network | 443, and 80 with `letsencrypt` | The web interface, desktops included |
| portal | workers | 22 | Starting and stopping sessions |
| workers | portal | 389 | Resolving users against the directory |
| portal and workers | storage | 2049 | The shared home over NFSv4 |
| portal and workers | storage | 3128 | The software catalogue through the site cache |
| Every role | OneGate endpoint | 5030 by default | Readiness and session counts |
| Prometheus | portal, management network | 9101 | Service metrics, only if scraped |
| storage | Internet | 80 and 8000 | The EESSI CernVM-FS servers, plain HTTP |
{.w-100}

## Requirements

* OpenNebula 6.10 or later with [OneFlow]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}) and [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}) enabled, and the OneGate endpoint reachable from the service networks.
* The two Virtual Networks above, the compute one reserved for the service.
* Outbound HTTP from the storage role to the EESSI CernVM-FS servers.
* Capacity for three VMs plus the workers you expect. The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal.
