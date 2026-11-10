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

This guide is aimed at OpenNebula users and administrators upgrading from 7.2.x to 7.4, or from 7.4.0 or 7.4.1 to 7.4.2. The following sections summarize the new features and usage changes that should be taken into account or could perhaps cause confusion. You can check the upgrade process in the [corresponding section]({{% relref "software/upgrade_process/" %}}). If upgrading from previous versions, please make sure you read all the intermediate versions’ Compatibility Guides for possible pitfalls.

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

## Rotate the serveradmin Password

The `serveradmin` password generated by previous versions had limited randomness. Upgrading does not replace an existing password. After upgrading, rotate it using the [serveradmin credential procedure]({{% relref "product/cloud_system_administration/multitenancy/manage_users/#change-credentials-for-oneadmin-or-serveradmin" %}}). Update all five service credential files and restart OpenNebula and the affected services as described there.

## OneKS Appliance and Monitoring

After upgrading to OpenNebula 7.4.2, delete the previously imported OneKS appliance and reimport the latest version from the Marketplace to use the new monitoring and application management features. See [Appliance Configuration]({{% relref "platform_services/oneks/management/configuration.md#appliance-configuration" %}}) for import details.

These features also require enabling the `:monitor` section in `/etc/one/oneks-server.conf` and restarting the OneKS service. Follow the [Monitor Configuration]({{% relref "platform_services/oneks/management/configuration.md#monitor-configuration" %}}) instructions, including the required transparent proxy settings.

Reimporting the appliance does not affect existing Kubernetes clusters. The monitor is deployed in new clusters created after it has been enabled.

## OneKS Worker Sizes

OpenNebula 7.4.2 changes the default worker flavors in the `general` family. The `small`, `medium`, and `large` flavors now allocate twice their previous CPU, memory, and disk resources. To preserve the previous sizes when creating node groups, change flavor selections from `small` to `extra-small`, `medium` to `small`, and `large` to `medium`. Review automation that selects these flavors before creating new node groups. Existing node groups retain their stored resource values. See [Changing Flavour Capacity]({{% relref "platform_services/oneks/management/customizing_specs.md#changing-flavour-capacity" %}}) for customization details.

## LVM Live Migration

In OpenNebula 7.4.2, live migration with `TM_MAD=lvm`, or with `TM_MAD=fs_lvm_ssh` and `LVM_THIN_ENABLE=YES`, pauses the guest throughout memory transfer and storage handover to prevent thin-pool metadata inconsistencies and data loss. Application interruption can therefore be substantially longer, especially for VMs with large memory allocations or slow migration links. Account for this pause when planning migrations.

## Datastore Migration with Internal Snapshots

OpenNebula 7.4.2 rejects live datastore migration of VMs with system snapshots or qcow2 disks containing internal snapshots to prevent disk corruption and data loss. Use [cold datastore migration]({{% relref "product/virtual_machines_operation/virtual_machines/vm_resources.md#cold-storage-migration" %}}) when these snapshots must be preserved. Host-only live migration remains supported.

## OneForm Recovery Commands and API

OpenNebula 7.4.2 changes the OneForm recovery interfaces. Replace `oneprovision retry` in automation with `oneprovision recover`, and replace requests to `POST /api/v1/provisions/<id>/retry` with `POST /api/v1/provisions/<id>/recover`. Review integrations against the updated [OneForm API Reference]({{% relref "product/integration_references/system_interfaces/oneform_api.md" %}}).

OneForm now persists unfinished operations and resumes their processing after a service restart. Failed operations require [explicit recovery]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations.md#recovering-failed-provisions" %}}) after correcting the cause of the failure.

## Interactive Restore Integrations

OpenNebula 7.4.2 changes the TCP framing used by interactive restore writers. Custom integrations must prefix each data frame with the one-byte `DATA` type (`0x00`) before its existing 24-byte header and payload. After sending the data, open a final connection and send the one-byte `FINISH` frame (`0x01`). Send `FINISH` when a restore is cancelled or fails as well, and do not send more data afterward. Update custom senders to the [interactive restore protocol]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}) before using them with the new writer.

## oVirtAPI Service

In OpenNebula 7.4.2, oVirtAPI runs through the `opennebula-ovirtapi` systemd service using Puma. Its default configuration listens directly on ports 80 and 443 and writes logs to `/var/log/one/ovirtapi.log`. Review existing Apache listeners, Passenger customizations, and local service-management procedures before enabling the new service. Puma settings are configured in `/etc/one/ovirtapi-puma.rb`.

## Guacamole Console Configuration

OpenNebula 7.4.2 moves Guacamole console connection defaults from FireEdge code and its bridge into the `guacamole` section of `/etc/one/fireedge-server.conf`. Merge the new section into your configuration using the [7.4.2 configuration instructions]({{% relref "software/release_information/release_notes/resolved_issues_742.md#configure-guacamole-connection-defaults-and-enforced-settings" %}}) and restart FireEdge.

Review the supplied enforced policy before applying it: it disables clipboard copy/paste and SFTP for VNC, SSH, and RDP connections. For RDP, it also disables drive and printer redirection and requires Network Level Authentication (NLA). VM/NIC and browser settings cannot override enforced values. See [Connection Defaults and Enforced Settings]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#fireedge-guacamole-connections" %}}) for configuration details.

## SR-IOV MTU Configuration

OpenNebula 7.4.2 applies the requested NIC `MTU` to its shared parent Physical Function (PF). It raises the PF MTU when necessary and does not lower it for smaller requests. In switchdev mode, it also sets the VF representor MTU to the NIC value. Review existing Virtual Network MTU settings and the physical network configuration; a smaller NIC MTU does not lower the shared PF MTU. See [eSwitch modes]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#eswitch-modes" %}}) for hardware-dependent behavior.

## HA Configuration Synchronization

In OpenNebula 7.4.2, `onezone serversync` also synchronizes `/etc/one/oneform-server.conf`, `/etc/one/oneks-server.conf`, and `/etc/one/fireedge-server.conf` when each file exists on both Front-ends. Differing local files are replaced by the remote versions, and their corresponding services are restarted. Review any settings that differ between nodes before synchronizing. See [Synchronize Configuration Files Across Servers]({{% relref "product/control_plane_configuration/high_availability/frontend_ha.md#server-sync-ha" %}}).

## Veeam Incremental Checkpoints

OpenNebula 7.4.2 marks deleted oVirtAPI checkpoints invalid and rejects incremental backups based on invalid or outdated checkpoints. Custom integrations must use the latest OpenNebula checkpoint. If that checkpoint has been invalidated or is unavailable, request a new full backup instead.
