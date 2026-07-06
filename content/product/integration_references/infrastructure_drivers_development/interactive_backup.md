---
title: "Interactive Backup Integrations"
linkTitle: "Interactive Backups"
date: "2026-06-17"
description:
categories:
pageintoc: "299"
tags:
weight: "9"
---

<a id="interactive-backup-integration"></a>

<!--# Interactive Backup Integrations -->

This page describes the OpenNebula interactive backup workflow for backup integrations. It is intended for integration developers and for administrators following a specific integration guide, such as the [OpenNebula-Veeam&reg; Backup Integration]({{% relref "../../../product/cluster_configuration/backup_system/veeam.md#vm-backups-veeam" %}}).

The `interactive` backup datastore driver is a coordination driver. It is not a general-purpose backup backend where users store and manage backup payloads directly. For regular OpenNebula backup storage, use the [Restic]({{% relref "../../../product/cluster_configuration/backup_system/restic.md#vm-backups-restic" %}}) or [Rsync]({{% relref "../../../product/cluster_configuration/backup_system/rsync.md#vm-backups-rsync" %}}) backup datastore guides. For Veeam deployments, follow the [Veeam guide]({{% relref "../../../product/cluster_configuration/backup_system/veeam.md#vm-backups-veeam" %}}), which explains the datastore attributes required by that integration.

Interactive backups use the OpenNebula Backup Exporter (OneBEX). OneBEX is started on demand on the hypervisor that is running the VM backup operation. OpenNebula prepares the disk export, OneBEX exposes the export through an HTTP API, and the external backup system reads the backup data from the hypervisor. The external backup product stores the backup payload in its own repository, while OpenNebula keeps the backup image metadata needed to track and restore the backup.

## How It Works

When a VM backup is created through an interactive backup integration, OpenNebula performs the following actions:

1. The VM backup workflow prepares the selected disks for export. Full backups and CBT incremental backups are supported.
2. OpenNebula writes the export metadata to `interactive_exports.json` in the VM backup directory on the hypervisor.
3. OneBEX is started on the hypervisor if it is not already running.
4. The external backup system requests the export from OneBEX, discovers the available disk transfers, and reads disk data ranges and block extents.
5. The external backup system finalizes each transfer and then finishes the VM backup session.
6. OpenNebula records the backup metadata as a backup image in the integration datastore.

OneBEX stops automatically when the backup session is finished or when it remains idle for longer than the configured timeout.

## Compatibility

The current interactive backup implementation supports the following configuration:

| Component | Support |
|-----------|---------|
| Hypervisor | KVM |
| VM disk storage | File-based `qcow2` disks and disks on LVM datastores |
| Backup types | Full and incremental |
| Incremental mode | CBT only (`INCREMENT_MODE="CBT"`) |
| VM state | Running and powered off VMs |
| OneBEX exporter | NBD, LVM |

{{< alert title="Important" type="info" >}}
Interactive incremental backups do not support the `SNAPSHOT` increment mode. OpenNebula rejects this combination when the backup configuration is updated.
{{< /alert >}}

## Network Requirements

The external backup system must be able to connect to OneBEX on every hypervisor that can run VMs backed up by the integration.

Make sure that:

- The OneBEX listen address and port are reachable from the external backup system.
- Firewalls allow the configured OneBEX port on the hypervisors.
- OpenNebula remotes are synchronized after changing the OneBEX configuration.
- The standard OpenNebula Front-end to Host connectivity is working.

## Configuring OneBEX

OneBEX is configured from the OpenNebula remotes directory on the Front-end:

```default
/var/lib/one/remotes/etc/onebex/onebex-server.conf
```

After changing this file, synchronize the remotes to the Hosts:

```default
$ onehost sync -f
```

{{< alert title="Note" type="info" >}}
OneBEX logs are written on each hypervisor to `/var/log/one/onebex.log`.
{{< /alert >}}

The configuration file defines the OneBEX listen address, shutdown behavior, logging settings, and Puma web server concurrency limits.

### Server Configuration

| Parameter | Default value | Description |
|-----------|---------------|-------------|
| `:host:` | `0.0.0.0` | Address where OneBEX listens for HTTP requests. By default, it listens on all available interfaces. |
| `:port:` | `13014` | TCP port where OneBEX listens for HTTP requests. |
| `:shutdown_delay:` | `2` | Delay, in seconds, after the final `/vms/:VM_ID/finish` request before stopping OneBEX. |
| `:idle_timeout:` | `300` | Maximum time, in seconds, without receiving any HTTP request before OneBEX stops automatically. |
| `:onebex_timeout:` | `1800` | Maximum time, in seconds, that OpenNebula waits for an interactive export to finish after it has started. |

### Log Configuration

| Parameter | Default value | Description |
|-----------|---------------|-------------|
| `:log: :level:` | `2` | Log verbosity level. Supported values are `0` for `ERROR`, `1` for `WARNING`, `2` for `INFO`, and `3` for `DEBUG`. |
| `:log: :system:` | `file` | Logging backend used by OneBEX. Supported values are `file` and `syslog`. |

### Puma Configuration

| Parameter | Default value | Description |
|-----------|---------------|-------------|
| `:puma: :min_threads:` | `1` | Minimum number of Puma threads used to handle concurrent OneBEX HTTP requests. |
| `:puma: :max_threads:` | `4` | Maximum number of Puma threads used to handle concurrent OneBEX HTTP requests. |

## Integration Datastore

An interactive backup integration needs a `BACKUP_DS` datastore using `DS_MAD="interactive"`. This datastore records OpenNebula backup metadata and lets the integration identify which backups belong to it. The backup payload itself is stored by the external backup system.

Do not create this datastore as a standalone backup target. Create it only when required by an integration guide. Integrations can require additional marker attributes. For example, the Veeam integration requires `VEEAM_DS="YES"` so the oVirtAPI server can select the datastore used by Veeam.

The minimal datastore shape is:

```default
NAME   = "Integration Backups"
TYPE   = "BACKUP_DS"

DS_MAD = "interactive"
TM_MAD = "-"

DATASTORE_CAPACITY_CHECK="NO"
```

The datastore must be added to every cluster that contains VMs managed by the integration.

```default
$ onecluster adddatastore <cluster_name> <datastore_name>
```

## Restoring Interactive Backups

During interactive restores, OpenNebula passes the Image Datastore downloader a OneBEX URL in the following form:

```default
onebex://<IMAGE_DS_ID>:<PORT_ID>
```

`IMAGE_DS_ID` is the destination Image Datastore ID where the restored disk image will be created. `PORT_ID` is the restore transfer port allocated for the interactive restore session.

## OneBEX API Reference

The OneBEX API is consumed by backup integrations. The current API is:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | `GET` | Returns basic server information and the available API routes. |
| `/status` | `GET` | Returns the current export status for a VM. Requires `VM_ID`. |
| `/exporters` | `GET` | Lists the exporter backends available in OneBEX. |
| `/export` | `POST` | Starts one or more disk exports for a VM. Requires `VM_ID` and `DS_ID`. `DISKS` is optional. |
| `/transfers/:TRANSFER_ID/info` | `GET` | Returns size and format information for a transfer. |
| `/images/:TRANSFER_ID` | `OPTIONS` | Returns supported image transfer features and concurrency limits. |
| `/images/:TRANSFER_ID/extents` | `GET` | Returns block extent information for a transfer. |
| `/images/:TRANSFER_ID` | `GET` | Reads a byte range from a transfer. Requires an HTTP `Range` header. |
| `/images/:TRANSFER_ID` | `PATCH` | Flushes a transfer when the request body uses `op=flush`. |
| `/transfer/:TRANSFER_ID/finalize` | `POST` | Finalizes a transfer and releases its exporter resources. |
| `/vms/:VM_ID/finish` | `POST` | Finishes the VM backup session after all transfers have been finalized. |

## Exporters

OneBEX uses exporters to expose VM disk data to external backup systems.

| Exporter | VM disk storage | Transport | Description |
|----------|-----------------|-----------|-------------|
| `nbd` | File-based `qcow2` disks | Network Block Device | Exposes the backup disk through NBD. OneBEX starts a read-only `qemu-nbd` process and serves the disk export through a Unix socket. |
| `lvm` | Disks on LVM datastores | Direct block-device reads | Exposes the prepared LVM block device directly. Full backups return the full device extent. Incremental backups use `thin_delta` to return changed extents from LVM thin metadata. |
