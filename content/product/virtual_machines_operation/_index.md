---
title: "Workload Operation"
linkTitle: "Workload Operation"
date: "2025-02-17"
description: "Complete information for creating and managing Virtual Machines. These guides include VM definitions, configurations for the supported networking architectures, creating VM backups, operating system parameters, and services comprising coordinated multiple Virtual Machines."
categories:
pageintoc: "80"
tags:
weight: "4"
---

<a id="virtual-machines-operation"></a>

<!--# Virtual Machines Operation -->

<a id="vm-management-overview"></a>

<!--# Overview -->

This Chapter contains documentation on how to create and manage Virtual Machines and their associated objects.

{{< alert title="Important" type="info" >}}
Through these guides Virtual Machine or VM is used as a generic abstraction that may represent real VMs, micro-VMs, or system containers.{{< /alert >}} 

## How Should I Read This Chapter

Before reading this Chapter, you should have already installed your [Front-end]({{% relref "software/installation_process/frontend_installation/frontend_install.md" %}}), the [KVM Hosts]({{% relref "software/installation_process/cluster_installation/kvm_node_installation.md" %}}) or [LXC Hosts]({{% relref "../../software/installation_process/cluster_installation/kvm_node_installation.md" %}}) and have an OpenNebula cloud up and running with at least one virtualization node.

## Hypervisor Compatibility

These guides are compatible with all hypervisors.
