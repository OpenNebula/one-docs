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

The Open OnDemand Service has three roles and uses two Virtual Networks. Each user session runs as a Slurm job on a pool of compute VMs that grows and shrinks.

## Roles

| **Role** | **Cardinality** | **What it runs** |
|---|---|---|
| `storage` | 1 | NFS server for the shared home directories, the state of the Slurm controller and the shared software directory. Squid cache for the EESSI catalogue, unless the service uses a proxy of the site |
| `portal` | 1 | Open OnDemand, its LDAP directory, Dex, the Slurm controller `slurmctld`, the accounting daemon `slurmdbd` with MariaDB, the Prometheus metrics exporter |
| `worker` | 1 to 6, elastic | `slurmd`, joined to the Cluster as a dynamic node, and the user sessions as Slurm jobs |
{.w-100}

{{< image path="/images/open_ondemand/light/architecture.svg" pathDark="/images/open_ondemand/dark/architecture.svg"
alt="The storage, portal and worker roles between the management and compute networks, with the flows between them" align="center" width="100%" mb="20px" >}}

OneFlow starts `storage` first. It starts `portal` when the storage role is ready, and `worker` when both are ready. Each role reports `READY` through OneGate only when it is actually serving. The service therefore reaches `RUNNING` when a user can sign in and open a session.

## Networks

Every VM has two network interfaces:

* **Management network**: Facilitates communication with OneGate and the Internet. The portal publishes its web interface here, and the storage role downloads the software catalogue through it.
* **Compute network**: Reserved for the service. It carries NFS, LDAP, the Slurm traffic between the controller and the nodes, along with the proxied sessions and the software cache.

No address is fixed in advance. OneFlow provides each role the compute addresses of the roles it depends on. The storage role queries OneGate which VM is the portal.

A worker joins the Slurm Cluster of its own accord at boot. A reconciler on the portal removes the node of any VM that has left the service.

The portal uses the whole `/24` subnet containing its compute address as the worker range, so keep that network reserved for the service. For larger subnets, configure `ONEAPP_POOL_RANGE` as described in [Configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/#advanced-attributes" %}}).

## How a Session Runs

1. The user signs in. Dex checks the credentials against the LDAP directory, or against an external OpenID Connect provider. Open OnDemand then starts a web server for that user, running as their Unix account.
2. The user launches an application and picks cores, memory and session hours. Cores and memory are limited to the capacity of the largest worker. The portal submits the session script with `sbatch` as the user. It requests one node, the cores and memory chosen, and GPUs if the pool has any.
3. Slurm starts the script on a worker with sufficient cores and memory free. If no adequate worker is available, the job remains in the queue and the card shows it as queued until a worker becomes available or OneFlow adds one. The job runs as the user under `slurmd`, with the home directory and the EESSI catalogue mounted. Slurm uses cgroup v2 to limit the job to the cores and memory it requested. No other session shares its cores, and any process that uses more memory than requested is terminated.
4. The application listens on a specific port of the worker and publishes the compute address of the worker. The portal proxies the browser to it. Desktops run under a TurboVNC server on the worker and reach the browser through noVNC on the portal.
5. Deleting the session cancels the job. Reaching the session hours ends it. In both cases Slurm stops every process of the job, so no trace of the session stays on the worker.

A job is never transferred to another worker, since the browser connection points to the worker that started it. Every job is recorded in the accounting database. **Active Jobs** lists the sessions, and the **Job Composer** submits batch jobs of your own to the same Cluster.

## How the Worker Pool Grows and Shrinks

Every worker publishes the following attributes to OneGate every 30 seconds:

| **Attribute** | **Meaning** |
|---|---|
| `SLURM_PENDING` | Jobs waiting for a worker of this role, the same figure on every worker |
| `ACTIVE_SESSIONS` | Jobs currently running on this worker |
| `IDLE_SECONDS` | Seconds since the last job on this worker ended |
| `OLDEST_IDLE` | `1` when the oldest worker of the role is drained and empty, so OneFlow may remove it |
| `SLURM_IDLE_NODES`, `SLURM_ALLOC_NODES` | Nodes of the Cluster without a job, and nodes with one |
| `HEALTHY` | `1` when the home mount, the software catalogue, munge and `slurmd` are all ready |
| `SESSION_USERS` | The user and the start time of each job on this worker |
| `SLURM_NODENAME` | The node name of this worker, published once at boot. The reconciler on the portal matches it against the Cluster |
{.w-100}

OneFlow reads the figures of every worker and applies the rules of the worker role. The numbers are from the marketplace template.

### Scaling Up 

OneFlow adds one worker when `SLURM_PENDING` is above 0 in two consecutive reads, and then waits 120 seconds before it reads again, so one pending job adds one VM and that VM has time to boot. OneFlow reads the figures every `autoscaler_interval` seconds, 90 by default in `/etc/one/oneflow-server.conf` on the Front-end. With the 30-second interval that the [Requirements](#requirements) recommend, a pending job normally receives its worker within about a minute and a half, and each further pending job a few minutes later. A job that no worker could ever run does not count. A GPU request on a pool without GPUs is refused at submit time, and a job that asks for more cores than any worker has waits with the reason `PartitionConfig`, which the workers leave out of `SLURM_PENDING`.

### Scaling Down

OneFlow always removes the oldest VM of a role, without draining it, so the appliance drains first. When the oldest worker has had no job for `ONEAPP_WORKER_IDLE_SECONDS` (ten minutes by default) and the queue is empty, it drains its own Slurm node. While that node is drained and empty, every worker publishes `OLDEST_IDLE` as `1`, and OneFlow removes the VM when the average remains above 0.99 in two reads 60 seconds apart. The node leaves the Cluster when the VM shuts down.

Three guards apply:

* A worker never drains while the role is at `min_vms`.
* A drained node returns to service when a job appears, or when OneFlow has not removed it after `ONEAPP_WORKER_DRAIN_SECONDS` (ten minutes by default).
* A reconciler on the portal runs every 30 seconds and deletes any node whose VM has left the service and holds no job.

On the testbed a scale down removed exactly the drained VM, and the job on the other worker kept running. The pool changes one VM at a time between 1 and `max_vms`. 6 is set as default in the Open OnDemand marketplace template.

## Requirements

* OpenNebula 6.10 or later with [OneFlow]({{% relref "product/operation_references/opennebula_services_configuration/oneflow/" %}}) and [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}) enabled, and the OneGate endpoint reachable from the service networks.
* The two Virtual Networks defined [above](#networks). The compute network is reserved for the service and no larger than a `/24` subnet, unless you set `ONEAPP_POOL_RANGE`. If a firewall sits between the networks, the roles need NFS (2049) and the software cache (3128) on the storage VM, LDAP (389) and the Slurm controller (6817) on the portal, `slurmd` (6818) and the session ports on the workers, and OneGate (5030 by default) from every VM.
* Outbound HTTP from the storage role to the EESSI CernVM-FS servers.
* Capacity for three VMs plus the workers you expect. The marketplace template gives every VM 2 vCPU and 4 GB of memory, and 8 GB to the portal, which runs the Slurm controller and MariaDB along with Open OnDemand. The portal used 710 MB of its 7941 MB with everything running on the testbed. The VM template passes the CPU of the Host through to the VMs (`CPU_MODEL` set to `host-passthrough`), so EESSI loads the software built for that CPU family. Every worker of a role has the same size, and a session is prohibited from requesting more resources than a single worker is allocated.
* For a faster scale-up, set `:autoscaler_interval: 30` in `/etc/one/oneflow-server.conf` on the Front-end and restart `opennebula-flow`. OneFlow then reads the figures of the workers every 30 seconds instead of 90. This is a setting of the Front-end, made once for every service that runs on it. It cannot be set through the appliance.

## The Munge Key

Munge is how the portal and the workers manage credentials. Every Slurm message carries a token signed with one secret key that all VMs share. The portal creates the key at first boot (1024 random bytes) and keeps it on the storage export, so a replaced portal uses the same key. It also publishes the key, base64 encoded, as `SLURM_MUNGE_KEY` in the user template of the portal VM through OneGate, and every worker reads it from there at boot.

Anyone who can read the template of the portal VM in OpenNebula can read the key, and with the key they can interact with the Cluster as if they were any given user. The Elastic Slurm service has the same exposure. Therefore it is important to restrict who can inspect the VMs of the service. Inside the VMs the key and the OneGate token are readable by root only. Therefore a session user cannot read them.
