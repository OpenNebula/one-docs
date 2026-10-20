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

Run these on the OpenNebula Front-end.

| **Command** | **Purpose** |
|---|---|
| `onemarketapp export 'Service OneSlurm' 'Service OneSlurm' --datastore default` | Import the appliance from the Marketplace |
| `onetemplate update <TEMPLATE_ID>` | Change a controller or worker VM template |
| `oneflow-template update <SERVICE_TEMPLATE_ID>` | Change the service template |
| `oneflow-template instantiate 'Service OneSlurm'` | Create a Cluster |
| `oneflow list` | List the Clusters |
| `oneflow show <SERVICE_ID>` | Show the roles and VMs of a Cluster |
| `oneflow scale <SERVICE_ID> worker <NUMBER>` | Change the number of workers |
| `oneflow delete <SERVICE_ID>` | Delete a Cluster |
| `onevm ssh <VM_ID>` | Connect to a VM of the Cluster |

## Commands Inside the VMs

| **Command** | **Where** | **Purpose** |
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
