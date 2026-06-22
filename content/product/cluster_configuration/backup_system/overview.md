---
title: "Overview"
date: "2025-02-17"
description:
categories:
pageintoc: "77"
tags:
weight: "1"
---

<a id="vm-backups-overview"></a>

<!--# Overview -->

Here you will find details on how to configure the available backends for [Virtual Machine Backups]({{% relref "product/virtual_machines_operation/virtual_machine_backups/" %}}). Backups are managed through the datastore and image abstractions, so all of the concepts that apply to these objects, such as access control or quotas, are applicable to backups.

Define backup datastores by using the available options for backends or datastore drivers:

- **Restic**: Based on the [restic backup tool](https://restic.net/).
- **Rsync**: Relies on the [rsync utility](https://rsync.samba.org/) to transfer backup files.
- **OpenNebula-Veeam&reg; Backup Integration**: Provides robust, agentless backup and recovery for OpenNebula VMs using Veeam Backup & Replication.

## Basic Guide Outline

Before reading this guide, you should have installed your [Front-end]({{% relref "frontend_install" %}}), the [KVM Hosts]({{% relref "kvm_node_installation#kvm-node" %}}) and have an OpenNebula cloud up and running with at least one virtualization node.

To configure your backup system, find about datastore driver options to save your VM backups:
* [Restic backend]({{% relref "restic#vm-backups-restic" %}})
* [Rsync datastore]({{% relref "rsync#vm-backups-rsync" %}})
* [OpenNebula-Veeam Backup Integration]({{% relref "veeam#vm-backups-veeam" %}})

Then, consult the [Virtual Machines Operation]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations" %}}) section to find out how to perform, schedule and restore VM backups.

Finally, if you need to backup a large number of VMs you can manage them [effectively through Backup Jobs]({{% relref "product/virtual_machines_operation/virtual_machine_backups/backup_jobs" %}}).

## Hypervisor and Storage Compatibility

Performing a VM backup requires support from the hypervisor and the disk image formats. The following table summarizes the backup modes supported for each hypervisor and storage system.

| **Hypervisor** | **Storage** | **Live (full)** | **Power off (full)** | **Live (incremental)** | **Power off (incremental)** |
| --- | --- | --- | --- | --- | --- |
| **KVM** | File\* (qcow2) | Yes | Yes | Yes | Yes |
| | File\* (raw) | Yes | Yes | No  | No  |
| | Ceph | Yes<sup><strong>†</strong></sup>  | Yes<sup><strong>†</strong></sup>  | Yes<sup><strong>†</strong></sup> | Yes<sup><strong>†</strong></sup>  |
| | LVM | Yes | Yes | Yes | Yes |
| | LVM (File Mode) | Yes<sup><strong>‡</strong></sup> | Yes | Yes<sup><strong>‡</strong></sup> | Yes<sup><strong>‡</strong></sup> |
| **LXC** | File (any format) | No  | Yes | No  | No  |
| | Ceph | No  | Yes | No  | No  |
| | LVM | Yes | Yes | No  | No  |
| | LVM (File Mode) | Yes<sup><strong>‡</strong></sup> | Yes | No  | No  |

<sup>\*</sup> Any datastore based on files with the given format, i.e. NFS/SAN or Local.

<sup>†</sup> Ceph full and incremental backups are currently stored in a different way, see [backup types]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations#backup-types" %}}) for more details.

<sup>‡</sup> Only supported in [thin mode]({{% relref "product/cluster_configuration/lvm/filemode#lvm-thin" %}}).
