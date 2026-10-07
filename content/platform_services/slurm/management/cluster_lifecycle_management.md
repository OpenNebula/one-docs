---
title: "Slurm Cluster Lifecycle Management"
linkTitle: "Cluster Lifecycle"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "1"
---

A OneSlurm cluster is a OneFlow service. You create, scale and delete it with the `oneflow` commands.

| Task | Command |
|---|---|
| Create a cluster | `oneflow-template instantiate 'Service OneSlurm'` |
| List clusters | `oneflow list` |
| Show the VMs of a cluster | `oneflow show <service_id>` |
| Change the number of workers | `oneflow scale <service_id> worker <number>` |
| Delete a cluster | `oneflow delete <service_id>` |

The [Quick Start]({{% relref "platform_services/slurm/getting_started/quick_start" %}}) shows how to create a cluster.

## Add Workers

```shell
$ oneflow scale <service_id> worker 4
```

OneFlow creates the new VMs. Each new worker reads the cluster data from OneGate and joins Slurm as a dynamic node, as described in [Core Concepts]({{% relref "platform_services/slurm/getting_started/core_concepts" %}}). Check the new nodes from the controller.

```shell
$ sinfo
```

| Limit | Value |
|---|---|
| Recommended minimum of workers | 1 |
| Maximum number of nodes in Slurm | 100 (`MaxNodeCount` in `slurm.conf`) |
| Cooldown after a scale operation | 30 seconds. During the cooldown you cannot scale or delete the service |

## Remove Workers

```shell
$ oneflow scale <service_id> worker 1
```

OneFlow deletes the extra worker VMs. Two mechanisms then remove the nodes from Slurm.

| Mechanism | Where it runs | When | What it does |
|---|---|---|---|
| Self-drain | Each worker, `oneslurm-self-drain.service` | When the VM shuts down normally | Sets the node `DOWN` and deletes it from Slurm |
| Reconciler | Controller, `oneslurm-reconcile.timer` | 2 minutes after boot, then every 60 seconds | Removes nodes that have no VM anymore |

The reconciler is a safety net for VMs that stop without a normal shutdown. It acts on a node only when all three conditions are true.

1. The node is registered in Slurm.
2. No worker VM of the service publishes this node name in OneGate.
3. Slurm sees the node as `DOWN` or `NOT_RESPONDING`.

Then it deletes the node. If the node still has running jobs, it drains the node instead, with the reason `removed from OneFlow service`.

If OneGate does not answer, or no worker has published its name yet, the reconciler changes nothing. Keep at least one worker in the service.

{{< alert title="Note" type="info" >}}
Scaling down deletes worker VMs even when they run jobs. Drain the nodes you want to remove first and wait for their jobs to finish. `scontrol update NodeName=<node> State=DRAIN Reason=<text>` drains a node.
{{< /alert >}}

## Delete the Cluster

```shell
$ oneflow delete <service_id>
```

This deletes all the VMs of the cluster. Data stored inside the VMs is lost, including the users of the local LDAP on the controller. Data on external NFS exports stays.
