---
title: "Overview"
linkTitle: "Overview"
date: "2026-05-12"
categories:
pageintoc: "168"
tags:
weight: "1"
type: docs
---

OneKS provides Managed Kubernetes as a Service on OpenNebula. It offers a structured way to create, access, operate, extend with managed applications, upgrade, recover, and deprovision Kubernetes Clusters (K8s Clusters) by combining a user-facing service layer with Cluster API-based infrastructure provisioning through CAPONE, the Cluster API provider for OpenNebula.

OneKS is designed for teams that need a simple and repeatable way to consume Kubernetes inside OpenNebula. Typical use cases include development and test environments, self-service Kubernetes delivery in private cloud environments, and standardized Cluster offerings for different sizes and topologies.

OneKS builds on CAPONE to expose a K8s Cluster-centric lifecycle model for users. Users interact mainly with OneKS K8s Clusters and node groups, while lower-level OpenNebula, Cluster API, and dependency-management details are handled underneath.

## How Should I Read this Chapter

If you have not used OneKS before, you should start by reading the [Basic Configuration Guide]({{% relref "platform_services/oneks/getting_started/basic_configuration/" %}}) to set up OneKS then follow the [Quick-start Guide]({{% relref "platform_services/oneks/getting_started/quick_start/" %}}) where you will learn to set up a basic K8s Cluster with OneKS. After completing the Quick-start Guide, move on to [Core Concepts]({{% relref "platform_services/oneks/getting_started/core_concepts/" %}}) to familiarize yourself with key OneKS concepts.

Once you have a K8s Cluster up and running and ready for workloads, you can then deploy applications. The [OneKS Application Catalog]({{% relref "platform_services/oneks/catalog/" %}}) provides validated Helm-based applications that can be managed through Sunstone or the CLI.

After completing the introductory documentation, you can find more information about managing K8s Clusters with OneKS in the following reference documentation:
* [K8s Cluster Lifecycle Management]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/" %}})
* [Monitoring and Troubleshooting]({{% relref "platform_services/oneks/management/monitoring_and_troubleshooting/" %}})
* [Configuration]({{% relref "platform_services/oneks/management/configuration/" %}})
* [Profiles Customization]({{% relref "platform_services/oneks/management/customizing_specs/" %}})
* [Creating Custom Applications]({{% relref "platform_services/oneks/references/creating_custom_applications/" %}})
* [Application Catalog]({{% relref "platform_services/oneks/catalog/" %}})
* [Service Architecture]({{% relref "platform_services/oneks/references/architecture/" %}})
* [OneKS REST API]({{% relref "platform_services/oneks/references/oneks_api/" %}})
* [OneKS CLI]({{% relref "platform_services/oneks/references/oneks_cli/" %}})

{{< alert title="Note" type="primary" >}}
It is important while reading this documentation to differentiate the concepts of **OpenNebula Clusters** and **Kubernetes (K8s) Clusters**:
* **OpenNebula Clusters**: Logical groupings of OpenNebula resources (Hosts, datastores and Virtual Networks) that provide compute capacity for cloud workloads.
* **K8s Clusters**: Collections of node instances (VMs) managed by a K8s control plane to automate the deployment, scaling and management of containerized applications. 

K8s Clusters provisioned by OneKS run as a guest workload on top of OpenNebula resources and should be considered as distinct entities to OpenNebula Clusters. It is possible, for example, to deploy *multiple* independent K8s Clusters within a *single* OpenNebula Cluster.
{{< /alert >}} 

## Interfaces

OneKS can be accessed through the following interfaces:

* **OneKS CLI**: Used for manual K8s Cluster, node-group, and application operations from the command line.
* **OneKS REST API**: Exposed under `/api/v1` for automation and programmatic integration.  
* **Sunstone Web UI**: Provides graphical workflows for creating, accessing, and managing OneKS K8s Clusters.

## What OneKS Manages

OneKS manages K8s Clusters as top-level resources. A K8s Cluster owns or coordinates:

* **Control Plane**: One logical control-plane group, containing one or more control-plane nodes depending on the selected control-plane flavour.  
* **Node Groups**: Zero or more worker-capacity groups attached to the K8s Cluster.  
* **Applications**: Managed Helm releases selected from the OneKS application catalog, including their component dependencies and runtime state.
* **Supporting Infrastructure**: Networks, images, VM templates, temporary seed VMs, virtual routers, and related OpenNebula resources.  
* **Lifecycle State**: The current operational state of the K8s Cluster and its groups.  
* **Historical Events**: Lifecycle actions and state transitions.  
* **Access Information**: kubeconfig retrieval for Kubernetes API access.  
* **Logs**: K8s Cluster-level and group-level lifecycle logs.

OneKS users interact primarily with the K8s Cluster, node-group, and application domains. Lower-level OpenNebula, CAPONE, Cluster API, Helm, and Kubernetes resources are orchestrated beneath those abstractions.

## Related Components

OneKS should be understood together with the following adjacent components:

* [**CAPONE**]({{% relref "product/integration_references/kubernetes/kubernetes_cluster_api/" %}}): The Cluster API provider for OpenNebula. It provides the lower-level declarative lifecycle integration between Kubernetes Cluster API and OpenNebula infrastructure.  
* [**OpenNebula Cloud Resources**]({{% relref "product/virtual_machines_operation/" %}}): VM templates, networks, images, virtual routers, and related infrastructure resources used to provision and operate the K8s Cluster.  
* [**RKE2**](https://docs.rke2.io/): The Kubernetes distribution used by the current OneKS implementation.  
* [**OneKS API**]({{% relref "platform_services/oneks/references/oneks_api/" %}}): The programmatic interface for K8s Cluster and node-group lifecycle operations.  
* [**Kubernetes Cloud Provider**]({{% relref "product/integration_references/kubernetes/kubernetes_cloud_provider/" %}}): The in-cluster integration layer for OpenNebula infrastructure behavior.  
* [**OneGate**]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}): The OpenNebula service used by Virtual Machines to communicate with OpenNebula during bootstrap and runtime configuration. In a OneKS deployment, OneGate must be configured and reachable so the K8s Cluster bootstrap process can complete successfully.  
* [**Transparent Proxy**]({{% relref "product/virtual_machines_operation/virtual_machines_networking/tproxy/" %}}) `tproxy`: The OpenNebula networking configuration used to expose OneGate, the XML-RPC API, and the OneKS API through the Front-end public network. OneKS deployments require TProxy rules for ports **5030**, **2633**, and **10780**; the in-cluster monitor uses port **10780** to report to OneKS.
* [**Cluster API References**]({{% relref "product/integration_references/kubernetes/kubernetes_cluster_api/" %}}): Useful when understanding the lower-level declarative lifecycle and CAPONE integration details.

## Supported Versions

OneKS supports the K8s versions exposed by the configured K8s Cluster profiles. Refer to the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes/#kubernetes" %}}) to see the Kubernetes versions currently supported bye OneKS.
