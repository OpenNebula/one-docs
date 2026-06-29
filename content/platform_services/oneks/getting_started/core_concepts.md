---
title: "Core Concepts"
linkTitle: "Core Concepts"
date: "2026-05-12"
description:
categories:
tags:
weight: "4"
type: docs
---

This section explains the main concepts behind OpenNebula Elastic Kubernetes Service (OneKS). This service exposes Kubernetes Clusters as high-level resources while orchestrating the OpenNebula, Cluster API, CAPONE, and runtime components required to provision and operate them.

Users mainly interact with:

* **K8s Clusters**: Top-level resources representing Kubernetes Clusters deployed on OpenNebula.
* **Node Groups**: Scalable worker-capacity groups attached to K8s Clusters.
* **Profiles, Families, and Flavours**: Reusable configuration models that define the deployment options exposed to users.
* **Lifecycle Operations**: Create, inspect, access, scale, upgrade, recover, and delete operations exposed through Sunstone, the CLI, and the API.

Lower-level resources such as OpenNebula VMs, templates, images, networks, virtual routers, Cluster API objects, and CAPONE resources are managed internally through these abstractions.

## OpenNebula Documents

The OneKS model is based on OpenNebula JSON documents. Each main OneKS resource is persisted in the OpenNebula database, allowing OneKS to reuse the platform's resource model, ownership, permissions, and storage mechanisms while defining Kubernetes-specific abstractions.

This means that OneKS resources are managed like OpenNebula resources from an authorization and persistence perspective. Users need permissions not only for the underlying infrastructure resources, such as VMs, Virtual Networks, images, and templates, but also for the OpenNebula document resources where OneKS stores K8s Clusters and node groups.

For more information about permissions, see [User Permissions]({{% relref "platform_services/oneks/getting_started/basic_configuration/#user-permissions" %}}).

## K8s Clusters

A OneKS K8s Cluster is the top-level resource exposed to users. It represents a Kubernetes Cluster deployed on OpenNebula and stores the information required to manage it throughout its lifecycle.

A K8s Cluster includes:

| **Attribute**              | **Description** |
|------------------------|-------------|
| `name`                 | K8s Cluster name. |
| `description`          | Optional human-readable description. |
| `kubernetes_version`   | Kubernetes version used by the K8s Cluster. |
| `deployment`           | OpenNebula placement used by the K8s Cluster, including the target OpenNebula Cluster and public and private Virtual Networks. |
| `spec`                 | Control-plane profile selection and input values. |
| `state`                | Current K8s Cluster lifecycle state. |
| `control_plane`        | Reference to the logical control-plane group. |
| `node_groups`          | References to worker node groups attached to the K8s Cluster. |
| `registration_time`    | K8s Cluster creation timestamp. |
| `historic`             | Lifecycle events and state transition history. |

A K8s Cluster has one logical control-plane group and zero or more node groups. The control plane is created as part of K8s Cluster provisioning. Node groups can be added later to provide worker capacity.

The full state list and reconciliation behavior are documented in [Monitoring and Troubleshooting]({{% relref "platform_services/oneks/management/monitoring_and_troubleshooting/" %}}).

## Control-plane Group

The control-plane group is the Kubernetes group implementation that manages the K8s Cluster control plane. Depending on the selected flavour, it can represent either a single-node control plane or a multi-node high-availability control plane.

Even in an HA deployment, users do not create multiple control-plane groups. OneKS represents the control plane as one logical group and uses the selected profile family and flavour to decide the topology and capacity behind it.

The control-plane group includes:

| **Attribute**              | **Description** |
|------------------------|-------------|
| `name`                 | Control-plane group name. |
| `description`          | Optional human-readable description. |
| `cluster_id`           | Identifier of the parent OneKS K8s Cluster. |
| `family`               | Profile family used by the control-plane group. |
| `flavour`              | Selected flavour within the family. |
| `type`                 | Group type, in this case control plane. |
| `state`                | Current group lifecycle state. |
| `vms`                  | OpenNebula VMs associated with the group. |
| `endpoint`             | Kubernetes API endpoint exposed by the control plane. |
| `kubeconfig`           | Kubeconfig data used to access the Kubernetes Cluster. |
| `dependencies`         | Dependencies required by the group, such as Seed VM or K8s Cluster Router. |
| `user_inputs_values`   | Effective input values after applying defaults and overrides. |
| `registration_time`    | Control-plane group creation timestamp. |
| `historic`             | Group lifecycle events and state transition history. |

The control-plane group owns the dependencies required to bootstrap and operate the Kubernetes control plane. During provisioning, it moves through bootstrap and provisioning states before reaching `RUNNING`. If the Seed VM fails or times out during bootstrap, the group may enter `BOOTSTRAPPING_FAILURE`. For more information about this dependency, see [Seed VM](#seed-vm).

## Node Groups

A Node Group is the Kubernetes group implementation that manages worker capacity. It belongs to a parent K8s Cluster and represents a scalable set of worker nodes defined by the selected family and flavour.

Worker nodes host application workloads. When a node group is created, OneKS provisions the requested number of worker nodes and joins them to the Kubernetes Cluster.

A node group includes:

| **Attribute**             | **Description** |
|------------------------|-------------|
| `name`                 | Node-group name. |
| `description`          | Optional human-readable description. |
| `cluster_id`           | Identifier of the parent OneKS K8s Cluster. |
| `family`               | Profile family used by the node group. |
| `flavour`              | Selected flavour within the family. |
| `type`                 | Group type, in this case node group. |
| `state`                | Current node-group lifecycle state. |
| `vms`                  | OpenNebula VMs associated with the node group. |
| `dependencies`         | Dependencies required by the node group, if any. |
| `user_inputs_values`   | Effective input values after applying defaults and overrides. |
| `registration_time`    | Node-group creation timestamp. |
| `historic`             | Node-group lifecycle events and state transition history. |

Scaling is performed against node groups, not directly against the K8s Cluster control plane. For example, scaling a node group to three nodes means that OneKS reconciles that node group until it contains three worker nodes.

A K8s Cluster can have:

* **Zero node groups**: A control-plane-only K8s Cluster.
* **One node group**: A simple K8s Cluster with one worker capacity group.
* **Multiple node groups**: A K8s Cluster with separate worker pools for different workload types or capacity profiles.

## Profiles, Families, and Flavours

Profiles define the configuration model used to create OneKS K8s Cluster components. In OneKS, profiles are exposed through families and flavours.

| **Concept**     | **Description** |
|-------------|-------------|
| Profile     | Configuration model used to create K8s Cluster components. Profiles define accepted inputs, validation rules, templates, defaults, and metadata. |
| Family      | Concrete configuration intended for a specific use case, including specification files and scripts. |
| Flavour     | Capacity and characteristics of the machines within a family, such as topology, CPU, memory, disk size, or node count. |

This mechanism allows cloud administrators to expose predefined Kubernetes deployment options with controlled choices for topology, resource sizing, and placement. Users select a family and a flavour instead of manually defining every low-level infrastructure detail.

Profile objects can include user inputs, validation rules, template definitions, defaults, dependencies, and additional metadata. For details on how to modify profile specs, add inputs, or change the capacities exposed by each flavour, see [K8s Cluster Profiles Customization]({{% relref "platform_services/oneks/management/customizing_specs/" %}}).

## User Inputs and Defaults

Profiles may define user inputs. These inputs are collected during K8s Cluster or node-group creation and are combined with the defaults defined by the selected flavour.

Common inputs include:

| **Input**        | **Description** |
|--------------|-------------|
| `count`      | Number of nodes or instances to create. |
| `cpu`        | CPU capacity assigned to each node. |
| `vcpu`       | Virtual CPU value assigned to each node. |
| `memory`     | Memory assigned to each node. |
| `disk_size`  | Disk size assigned to each node. |

A flavour can also control whether user-provided values are allowed to override its defaults through the `override_defaults` setting. When enabled, user-provided values can override the flavour defaults. When disabled, the flavour defaults take precedence. For configuration examples, see [K8s Cluster Profiles Customization]({{% relref "platform_services/oneks/management/customizing_specs/" %}}).

## Group Dependencies

Group dependencies are auxiliary resources required by a Kubernetes group implementation. Dependencies are orchestrated beneath the group abstraction, allowing OneKS to keep the user-facing model focused on K8s Clusters and node groups.

The current OneKS implementation provides two dependency types used by the control-plane group during provisioning:

| **Dependency**          | **Description** |
|---------------------|-------------|
| Seed VM             | Temporary bootstrap VM used to initialize the control-plane provisioning workflow. |
| K8s Cluster Router  | Routing component required by the control plane to provide connectivity between the Kubernetes Cluster and external networks. |

Dependency options are defined in the OneKS profile specs. For details on how to configure dependencies and their options, see [K8s Cluster Profiles Customization]({{% relref "platform_services/oneks/management/customizing_specs/" %}}).

### Seed VM

The Seed VM is a temporary OpenNebula VM used during control-plane bootstrap. It is managed internally and is not created or managed directly by users.

During control-plane provisioning, OneKS creates the Seed VM from the OpenNebula VM template generated from the OneKS appliance that is imported automatically when the service starts. For more information about this appliance import process, see [Automatically Generated Resources]({{% relref "platform_services/oneks/getting_started/basic_configuration/#automatically-generated-resources" %}}).

OneKS injects the rendered control-plane and Cluster API specification into the VM context, attaches the Seed VM to the K8s Cluster public network, and monitors its bootstrap state.

The Seed VM performs the bootstrap and Cluster API pivoting workflow. It starts a temporary management environment, applies the Cluster API and RKE2 resources, waits for the workload control plane, retrieves the workload kubeconfig, initializes the providers in the workload K8s Cluster, and moves the Cluster API objects.

OneKS monitors the Seed VM through its `ONEKS_STATE` value. When `ONEKS_STATE=RUNNING`, OneKS marks the dependency as ready and removes the Seed VM automatically, depending on the configured dependency behavior. If the Seed VM reports a failure state or does not become ready before the timeout, the control-plane group may enter `BOOTSTRAPPING_FAILURE`. For more information about group states, see [Node Group States]({{% relref "platform_services/oneks/management/monitoring_and_troubleshooting/#node-group-states" %}}).

The Seed VM is a critical part of the control-plane creation process, but it remains an implementation detail hidden from normal user workflows.

### K8s Cluster Router

The K8s Cluster Router is the routing dependency used by the control plane to provide connectivity between the Kubernetes Cluster, the OpenNebula networking layer, and external networks.

In a typical OneKS topology, the router is connected to both the public and private networks selected during K8s Cluster creation. The public network provides external access where required, while the private network connects the control-plane and worker-node VMs.

Users normally do not create or manage the router directly. OneKS creates and monitors it as part of the control-plane group dependencies.

## Topologies

A topology describes how a OneKS K8s Cluster is assembled from its control plane, node groups, networks, and runtime dependencies.

A topology is determined by:

* **Kubernetes Version**: The Kubernetes version deployed in the K8s Cluster.
* **Public and Private Networks**: The OpenNebula networks selected during K8s Cluster creation.
* **Control-plane Family and Flavour**: The selected configuration for the Kubernetes control plane.
* **Node-group Family, Flavour, and Count**: The worker capacity profile and number of workers, if additional capacity is required.
* **Runtime Dependencies**: Supporting components such as the Seed VM and K8s Cluster Router.

Users do not build the topology manually. They select the Kubernetes version, networks, family, flavour, and input values. OneKS translates those choices into the corresponding OpenNebula, Cluster API, CAPONE, and Kubernetes resources.
