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
| `storage` | 1 | NFS server for the shared home directories and the state of the Slurm controller, Squid cache for the EESSI catalogue |
| `portal` | 1 | Open OnDemand, its LDAP directory, Dex, the Slurm controller `slurmctld`, the accounting daemon `slurmdbd` with MariaDB, the Prometheus metrics exporter |
| `worker` | 1 to 6, elastic | `slurmd`, joined to the cluster as a dynamic node, and the user sessions as Slurm jobs |
{.w-100}

{{< image path="/images/open_ondemand/light/architecture.svg" pathDark="/images/open_ondemand/dark/architecture.svg"
alt="The storage, portal and worker roles between the management and compute networks, with the flows between them" align="center" width="100%" mb="20px" >}}

OneFlow starts `storage` first, `portal` when the storage role is ready, and `worker` when both are. Each role reports `READY` through OneGate only when it is actually serving, so the service reaches `RUNNING` when a user can sign in and open a session.

## Networks

Every VM has two network interfaces:

* **Management network**: reaches OneGate and the Internet. The portal publishes its web interface here, and the storage role downloads the software catalogue through it.
* **Compute network**: reserved for the service. NFS, LDAP, the Slurm traffic between the controller and the nodes, the proxied sessions and the software cache run on it.

The roles find each other without fixed addresses. OneFlow passes the compute address of the storage role to the portal and the workers, and the compute address of the portal to the workers, and the storage role asks OneGate which VM is the portal. A worker registers itself with the controller at boot, which learns the address of the node from the registration, and a reconciler on the portal deletes every node that no VM of the service claims, so a VM that is not part of the service never keeps a node in the cluster. The portal derives the worker address range from its own compute interface, the whole /24 around its address, which bounds how many nodes the cluster accepts and tells a session which of its addresses to publish, so keep that network reserved for the service. A compute network larger than a /24 needs an explicit `ONEAPP_POOL_RANGE`, described in [Configuration]({{% relref "platform_services/open_ondemand/configuration/#advanced-attributes" %}}).

## How a Session Runs

1. The user signs in. Dex checks the credentials against the LDAP directory, or against an external OpenID Connect provider, and Open OnDemand starts a per user web server as that Unix user.
2. The user launches an application and chooses its cores, memory and session hours, up to what the largest worker has. The portal submits the session script with `sbatch` as the user, asking for one node, that many cores and that much memory, and for GPUs when the pool has any.
3. Slurm starts the script on a worker with those cores and that memory free, or keeps it in the queue, in which case the card shows it as queued until a worker frees up or OneFlow adds one. The job runs as the user under `slurmd`, with the home directory and the EESSI catalogue mounted, and cgroup v2 fences it to the cores and the memory it asked for, so no other session shares its cores and a process that grows past its memory is stopped.
4. The application listens on a port of the worker and publishes the compute address of the worker, and the portal proxies the browser to it. Desktops run under a TurboVNC server on the worker and reach the browser through noVNC on the portal.
5. Deleting the session cancels the job and reaching the session hours ends it, and either way Slurm stops every process of the job, so nothing of the session stays on the worker.

A job is never requeued on another worker, because the browser connection points at the worker that started it. Every job goes through the accounting database, so **Active Jobs** lists the sessions and the **Job Composer** submits batch jobs of your own to the same cluster.

## How the Pool Grows and Shrinks

Every worker publishes these attributes to OneGate every 30 seconds:

| Attribute | Meaning |
|---|---|
| `SLURM_PENDING` | Jobs waiting for a worker of this role, the same figure on every worker |
| `ACTIVE_SESSIONS` | Jobs running on this worker |
| `IDLE_SECONDS` | Seconds since the last job on this worker ended |
| `OLDEST_IDLE` | `1` when the oldest worker of the role is drained and empty, so OneFlow may remove it |
| `SLURM_IDLE_NODES`, `SLURM_ALLOC_NODES` | Nodes of the cluster without a job and with one |
| `HEALTHY` | `1` when the home mount, the software catalogue, munge and `slurmd` are all in place |
| `SESSION_USERS` | The user and the start time of each job on this worker |
| `SLURM_NODENAME` | The node name of this worker, published once at boot, which the reconciler on the portal matches against the cluster |
{.w-100}

OneFlow evaluates the elasticity policies on the average across the role. It adds one VM when `SLURM_PENDING` stays above 0 for two readings 30 seconds apart, then waits 300 seconds before it reads again, which covers the boot of the new worker, so one pending job adds one worker. A job nobody could run never counts, because Slurm refuses a GPU request at submit on a pool without GPUs, and a job that asks for more cores than any worker has waits with the reason `PartitionConfig`, which the workers leave out.

Scaling down goes one worker at a time. OneFlow always removes the oldest VM of the role and does not drain it first, so the oldest worker drains its own node once it has had no job for `ONEAPP_WORKER_IDLE_SECONDS`, ten minutes by default, with nothing in the queue, and from then on every worker publishes `OLDEST_IDLE` as `1` while that node is drained and empty. OneFlow removes the VM when the average holds above 0.99 for two readings 60 seconds apart, and the node leaves the cluster when the VM shuts down. A worker never drains while the role is at its `min_vms`, and a drained node goes back into service when a job appears in the queue or when OneFlow has not removed it after `ONEAPP_WORKER_DRAIN_SECONDS`, also ten minutes. A reconciler on the portal runs every 30 seconds and deletes any node whose VM has left the service and that holds no job.

The pool changes one VM at a time between 1 and `max_vms`, six in the marketplace template. Measured on 16 September 2026 with two 2 core jobs on a 2 core pool, `SLURM_PENDING` reached 1 within 30 seconds, OneFlow added the worker after 161 seconds and the pending job ran on it at 210 seconds, and a scale down terminated exactly the drained VM while the job on the other worker never left `RUNNING`.

## Ports

| From | To | Port | Purpose |
|---|---|---|---|
| Users | portal, management network | 443, and 80 with Let's Encrypt | The web interface, desktops included |
| workers | portal | 6817 | Registering with the Slurm controller, fetching its configuration and reading the queue |
| portal | workers | 6818 | Starting and cancelling jobs on `slurmd` |
| portal | workers | The port of each session | The proxy from the browser to the application |
| workers | portal | 389 | Resolving users against the directory |
| portal and workers | storage | 2049 | The shared home over NFSv4, and the controller state for the portal |
| portal and workers | storage | 3128 | The software catalogue through the site cache |
| Every role | OneGate endpoint | 5030 by default | Readiness, the munge key and the queue figures |
| Prometheus | portal, management network | 9101 | Service metrics, only if scraped |
| storage | Internet | 80 and 8000 | The EESSI CernVM-FS servers, plain HTTP |
{.w-100}

## Requirements

* OpenNebula 6.10 or later with [OneFlow]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}) and [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}) enabled, and the OneGate endpoint reachable from the service networks.
* The two Virtual Networks above, the compute one reserved for the service and no larger than a /24 unless you set `ONEAPP_POOL_RANGE`. Ports 6817 on the portal and 6818 on the workers must be open on the compute network, along with the session ports the portal proxies.
* Outbound HTTP from the storage role to the EESSI CernVM-FS servers.
* Capacity for three VMs plus the workers you expect. The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal, which runs the Slurm controller and MariaDB beside Open OnDemand and used 710 MB of its 7941 with everything up on 16 September 2026.

## The Munge Key

Slurm authenticates every message between the portal and the workers with munge, and every role shares one key. The portal generates it at first boot, 1024 bytes from `/dev/urandom`, keeps it on the storage export so a replaced portal reuses it, and publishes it base64 encoded as `SLURM_MUNGE_KEY` in the user template of the portal VM through OneGate, where each worker reads it at boot. Anyone who can read the template of the portal VM in OpenNebula can read the key, and with it forge the identity of any user towards the cluster, which is the same exposure the Elastic Slurm service has, so restrict who can see the VMs of the service. On the workers the OneGate token is readable by root only, so a session user cannot read the key from there.
