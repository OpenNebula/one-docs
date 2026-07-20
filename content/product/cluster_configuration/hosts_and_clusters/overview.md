---
title: "Overview"
date: "2025-02-17"
description:
categories:
pageintoc: "52"
tags:
weight: "1"
---

<a id="hostsubsystem"></a>

<!--# Overview -->

A **Host** is a server (physical or virtual) that provides compute capacity for cloud workloads, such as Virtual Machines or Kubernetes Clusters. Hosts must be connected to and controlled by one or more OpenNebula Front-end servers. To learn how to prepare Hosts, read the [Cluster section of the installation guides]({{% relref "software/installation_process/cluster_installation/" %}}). A **Cluster** is a logical grouping of OpenNebula resources including Hosts, Virtual Networks and datastores. Hosts are usually logically grouped within **Clusters**, but may exist independently of a Cluster object.

## How Should I Read This Chapter

In this chapter there are four guides describing these objects.

* **Host Management**: Host management is achieved through the `onehost` CLI command or through the **Infrastructure** section of the Sunstone GUI. You can read about Host Management in more detail in the [Host Management]({{% relref "hosts#hosts-guide" %}}) guide.
* **Cluster Management**: Hosts can be grouped in Clusters. These Clusters are managed with the `onecluster` CLI command or through the **Infrastructure** section of the Sunstone GUI. You can read about Cluster Management in more detail in the [Cluster Management]({{% relref "cluster_guide#cluster-guide" %}}) guide.

You should read all the guides in this chapter to familiarize yourself with the details of Host and Cluster objects. For small and homogeneous clouds you may not need to create new Clusters.

### PCI Passthrough and SR-IOV

If you intend to use specialized PCI hardware, such as GPUs or PCI network interfaces, it is necessary to complete additional configuration to ensure that workloads deployed within OpenNebula Hosts or Clusters have proper access to the devices. Refer to the [PCI Passthrough and SR-IOV]({{% relref "product/cluster_configuration/pci_passthrough_sriov/" %}}) section for more details. 

### Networking

Virtual Machines deployed by OpenNebula on Hosts and Clusters within a cloud deployment must be connected to a Virtual Network to facilitate communication within the cloud and to the internet. Refer to the [Networking System Section]({{% relref "product/cluster_configuration/networking_system/" %}}) for details on configuring Virtual Networks within an OpenNebula cloud.

### Storage and Backups

OpenNebula supports multiple options for cloud storage, including Ceph storage and SAN storage and backup solutions from multiple vendors. Refer to the [Storage System Guides]({{% relref "product/cluster_configuration/storage_system/" %}}) and the [Backup System Section]({{% relref "product/cluster_configuration/backup_system/" %}}) for further details. 

## Hypervisor Compatibility

These guides are compatible with all hypervisors.
