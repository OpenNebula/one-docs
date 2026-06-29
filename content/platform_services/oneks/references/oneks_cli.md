---
title: "CLI Reference"
linkTitle: "CLI"
date: "2026-05-12"
description:
categories:
tags:
weight: "2"
type: docs
---

The OneKS CLI is provided by the `oneks` binary.

General form:

```shell
oneks <command> <resource> [<args>] [<options>]
```

Product-facing resources are:

* `cluster`: OneKS K8s Cluster resource.  
* `nodegroup`: Worker-capacity group attached to a K8s Cluster.

The CLI may also expose plural forms:

* `clusters`: List or top K8s Cluster resources.  
* `nodegroups`: List or top node-group resources.

Important command naming note:

Some builds may expose node groups through the lower-level `group` resource in CLI help. Before publication, align this section with the exact shipped CLI behavior. If the shipped CLI uses `group`, the examples must use `group` consistently. If the product-facing resource is `nodegroup`, the CLI help should expose `nodegroup` consistently.

## Common commands

* `oneks list clusters`: List K8s Clusters.  
* `oneks list nodegroups`: List node groups.  
* `oneks top clusters`: Continuously display K8s Cluster status.  
* `oneks top nodegroups`: Continuously display node-group status.  
* `oneks show cluster <cluster_id>`: Show detailed K8s Cluster information.  
* `oneks show nodegroup <nodegroup_id>`: Show detailed node-group information.  
* `oneks create cluster`: Create a cluster.  
* `oneks create nodegroup --cluster-id <cluster_id>`: Create a node group.  
* `oneks recover cluster <cluster_id>`: Recover a K8s Cluster from selected failure states.  
* `oneks recover nodegroup <nodegroup_id>`: Recover a node group from selected failure states.  
* `oneks check cluster <cluster_id>`: Run the OneKS readiness check using the deployment placement from an existing K8s Cluster.
* `oneks delete cluster <cluster_id>`: Delete a K8s Cluster.  
* `oneks delete nodegroup <nodegroup_id>`: Delete a node group.  
* `oneks logs cluster <cluster_id>`: Show K8s Cluster logs.  
* `oneks upgrade cluster <cluster_id> --k8s-version <version>`: Upgrade a K8s Cluster version.  
* `oneks scale nodegroup <nodegroup_id> --target <count>`: Scale a node group.  
* `oneks chgrp cluster <cluster_id> <group_id>`: Change K8s Cluster group ownership.  
* `oneks chown cluster <cluster_id> <user_id> <group_id>`: Change K8s Cluster owner and group.  
* `oneks chmod cluster <cluster_id> <octet>`: Change K8s Cluster permissions.

## Common Examples

Create and access a K8s Cluster:

```shell
oneks create cluster --wait
oneks create cluster --file spec.json --wait
oneks show cluster 42 --kubeconfig > kubeconfig
KUBECONFIG=./kubeconfig kubectl get nodes
```

List and inspect resources:

```shell
oneks list clusters
oneks top clusters
oneks show cluster 42
oneks list nodegroups
oneks show nodegroup 7
```

Manage worker capacity:

```shell
oneks create nodegroup --cluster-id 42
oneks scale nodegroup 7 --target 3
```

Upgrade a K8s Cluster:

```shell
oneks upgrade cluster 42 --k8s-version v1.32.9
```

Recover a K8s Cluster or node group:

```shell
oneks recover cluster 42
oneks recover nodegroup 7
```

Run OneKS readiness checks:

```shell
oneks check cluster 42
oneks check --opennebula-cluster 0 --public-network 105 --private-network 106
```

Inspect logs:

```shell
oneks logs cluster 42
oneks logs cluster 42 --follow
```

Delete a K8s Cluster:

```shell
oneks delete cluster 42
oneks delete cluster 42 --force
```

Administrative K8s Cluster operations:

```shell
oneks rename cluster 42 new-name
oneks chgrp cluster 42 100
oneks chown cluster 42 10 100
oneks chmod cluster 42 640
```