---
title: "Automated Cluster Installation with OneForm"
linkTitle: "Cluster Installation with OneForm"
date: "2026-04-15"
description:
categories:
pageintoc: "26"
tags: [OneForm, cluster, deployment, automatic]
weight: "2"
---

OneForm is OpenNebula’s automated cloud provisioning tool. It serves as an automated “cloud-on-demand” engine, allowing you to provision resources on-premises, or bare-metal instances from public cloud providers through a simple, streamlined workflow. You can provision Clusters through an OpenNebula Front-end through the the Sunstone user interface, the OneForm CLI, or the OneForm REST API.

## Before Starting

In order to use OneForm, you must first install an OpenNebula Front-end using one of the available deployment options, refer to the [Front-end Installation Documentation]({{% relref "getting_started/install_opennebula/production/minione_frontend_install/" %}}) for details. 

## Provisioning Clusters with OneForm

Automatically Provisioning a Cluster with OneForm consists of the following steps:

### Step 1: Create a OneForm Provider
 
A OneForm Provider handles the credentials, API logic, and configuration for connecting to on-premises or cloud servers. 

#### On-premises Servers
A [Provider for on-premises servers]({{% relref "product/cluster_provisioning/cluster_providers/onprem_provider/" %}}) is pre-installed with the OpenNebula Front-end. See the [On-premises Provider Documentation]({{% relref "product/cluster_provisioning/cluster_providers/onprem_provider/" %}}) for more details.

#### 3rd-party Cloud and Bare-metal Service Providers

To use 3rd-party cloud and bare-metal services you must [install the relevant drivers](https://github.com/OpenNebula/oneform-registry/wiki/OneForm-Driver-Registry) from the [OneForm Registry repository](https://github.com/OpenNebula/oneform-registry). OneForm drivers define the logic for communicating with a 3rd-party IaaS API, enabling OneForm to automatically provision server instances. 

Once you have installed the OneForm driver for your preferred cloud service, refer to the [Provider Documentation](https://github.com/OpenNebula/oneform-registry/wiki) in the OneForm Registry Wiki to configure your OneForm Provider, defining your preferred region and adding credentials.

### Step 2: Provision Clusters with OneForm

Once you have Providers configured for your target infrastructure, you can proceed to provision Clusters with OneForm. OneForm communicates with 3rd-party IaaS APIs to instantiate the requested resources or communicates with on-premises hardware through SSH. Once the resources are available and ready, OneForm proceeds with an automated OpenNebula Cluster deployment, installing the necessary components for the Cluster to support workloads managed through the OpenNebula Front-end. 

Refer to the [Provisioning Documentation](https://github.com/OpenNebula/oneform-registry/wiki) in the OneForm Registry Wiki for your preferred cloud service provider or the On-premises Provisioning Documentation for a [SSH Cluster]({{% relref "product/cluster_provisioning/cluster_provisions/onprem_ssh_cluster/" %}}) or [NFS Cluster]({{% relref "product/cluster_provisioning/cluster_provisions/onprem_nfs_cluster/"%}}).

### Step 3: Manage the Clusters

OneForm provides various operations to manage Clusters once they have been provisioned. This includes deprovisioning, scaling and recovering Clusters. Please refer to the [OneForm Operations Documentation]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations/" %}}).