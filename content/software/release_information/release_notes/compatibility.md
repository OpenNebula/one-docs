---
title: "Compatibility Guide"
date: "2025-02-17"
description:
categories:
pageintoc: "247"
tags:
weight: "5"
---

<a id="compatibility"></a>

<!--# Compatibility Guide -->

This guide is aimed at OpenNebula 7.2.x users and administrators who want to upgrade to the latest version. The following sections summarize the new features and usage changes that should be taken into account or could perhaps cause confusion. You can check the upgrade process in the [corresponding section]({{% relref "software/upgrade_process/" %}}). If upgrading from previous versions, please make sure you read all the intermediate versions’ Compatibility Guides for possible pitfalls.

Visit the [Features list]({{% relref "/getting_started/understand_opennebula/opennebula_concepts/key_features" %}}) and the [What’s New guide]({{% relref "whats_new#whats-new" %}}) for a comprehensive list of what’s new in OpenNebula 7.4.

## Sunstone Interface Redesign

The Sunstone interface has been completely redesigned in the OpenNebula 7.4 release to improve useability. The redesign significantly changes the look and feel of Sunstone. While the interface has been significantly redesigned, the underlying concepts, workflows, and features remain the same. Existing users will primarily need to familiarize themselves with the new layout and the location of interface elements.

## Virtual Network MAC Address Allocation

OpenNebula 7.4 adds round-robin Address Range lease assignment. New NIC allocations no longer always start from the beginning of the Address Range, reducing immediate reuse of recently released addresses. Environments that relied on immediate MAC reuse after VM termination should review any external DHCP, IPAM, or static MAC mapping workflows.

OpenNebula 7.4 also adds an optional global MAC address space generation mode through the [`MAC_GLOBAL_SPACE`]({{% relref "product/operation_references/opennebula_services_configuration/oned.md#virtual-networks" %}}) setting in `oned.conf`. This setting defaults to `NO`. When set to `YES`, generated MAC addresses are allocated from a global pool to prevent collisions across Virtual Networks. This mode does not apply to IP networks and limits the generated global space to 2<sup>20</sup> Virtual Networks and up to 2<sup>20</sup> leases per Virtual Network.

## VM Backup Disk Selection

OpenNebula 7.4 adds [`BACKUP_CONFIG/DISK_IDS`]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks" %}}) to back up only selected VM disks. Existing backup configurations continue backing up all eligible disks unless `DISK_IDS` is set. For incremental backups, changing the effective disk set resets the incremental chain and the next backup creates a new full base. Backups that contain only selected disks cannot be restored as complete VMs; restore them as [individual disks]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks-restore" %}}).

## Veeam Backup Integration Architecture

The Veeam Backup integration architecture has changed in OpenNebula 7.4. Veeam now connects to OpenNebula through the Front-end oVirtAPI service, while backup data is pulled directly from hypervisors through OneBEX. Existing deployments should migrate to the new [Veeam architecture]({{% relref "product/cluster_configuration/backup_system/veeam.md#architecture" %}}) and verify that the Veeam server and workers can reach the Front-end and the OneBEX endpoint on every hypervisor that can run protected VMs.

## Daemon Logs Are No Longer Truncated on Start

The OpenNebula daemons (`oned`, the monitor, and the scheduler) now open their log files in append mode instead of truncating them on start. Previously the log was reset on every service start and relied on the forced log rotation (see below) to preserve its contents; with that rotation no longer triggered on start, restarts would otherwise have discarded the existing log. No action is required.

## Log Rotation No Longer Triggered on Service Start

OpenNebula systemd services no longer force a log rotation on start. The `ExecStartPre=-/usr/sbin/logrotate -f ...` directive has been removed from all services (`opennebula`, `opennebula-hem`, `opennebula-flow`, `opennebula-gate`, `opennebula-form`, `opennebula-fireedge`, and `opennebula-ks`). Logs under `/var/log/one/` are still rotated by the files in `/etc/logrotate.d/` via the system's own `logrotate` timer/cron, so no action is required.

To keep the old behavior for a service, add a systemd drop-in, e.g. for `opennebula`:

```default
# /etc/systemd/system/opennebula.service.d/logrotate.conf
[Service]
ExecStartPre=-/usr/sbin/logrotate -f /etc/logrotate.d/opennebula -s /var/lib/one/.logrotate.status
```

Then run `systemctl daemon-reload`.

## Template Instantiation Permissions

A bug was identified in Template instantiation where `CREATE` permissions on the Template object were erroneously required. This requirement has been dropped, now it requires only `USE` permissions on the Template. Users with default ACL rules are unaffected.
