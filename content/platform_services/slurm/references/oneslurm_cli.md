---
title: "OneSlurm CLI"
linkTitle: "CLI"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "3"
---

## OpenNebula Commands

Run these on the OpenNebula front-end.

| Command | Purpose |
|---|---|
| `onemarketapp export 'Service OneSlurm' 'Service OneSlurm' --datastore default` | Import the appliance from the Marketplace |
| `onetemplate update <template_id>` | Change a controller or worker VM template |
| `oneflow-template update <service_template_id>` | Change the service template |
| `oneflow-template instantiate 'Service OneSlurm'` | Create a cluster |
| `oneflow list` | List the clusters |
| `oneflow show <service_id>` | Show the roles and VMs of a cluster |
| `oneflow scale <service_id> worker <number>` | Change the number of workers |
| `oneflow delete <service_id>` | Delete a cluster |
| `onevm ssh <vm_id>` | Connect to a VM of the cluster |

## Commands Inside the VMs

| Command | Where | Purpose |
|---|---|---|
| `sinfo` | Controller | Partitions and node states |
| `scontrol show nodes` | Controller | Details of each node |
| `squeue` | Controller | Job queue |
| `srun -N1 hostname` | Controller | Run a test job |
| `scontrol update NodeName=<node> State=DRAIN Reason=<text>` | Controller | Drain a node before you remove it |
| `scontrol update NodeName=<node> State=RESUME` | Controller | Put a drained or down node back in service |
| `scontrol delete NodeName=<node>` | Controller | Delete a dynamic node |
| `journalctl -u oneslurm-reconcile` | Controller | Log of the reconciler |
| `onegate service show` | Any VM | The service, as OneGate sees it |
| `getent passwd <user>` | Any VM | Check an LDAP user |
| `findmnt /home` | Any VM | Check the NFS mount |
| `cat /etc/one-appliance/status` | Any VM | Result of the appliance configuration |
