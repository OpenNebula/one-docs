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

If a restore fails, the restored Image remains in `LOCKED` state and should be removed manually:

{{< alert title="Important" type="info" >}}
Get the restore transfer port from the Image `PATH` attribute, which has the form `onebex://<IMAGE_DS_ID>:<PORT_ID>`, and terminate the writer process associated with that port:

```shell
PORT=<PORT_ID>
pgrep -f "onebex_writer.rb .* ${PORT} " | xargs -r kill -TERM
oneimage delete --force <IMAGE_ID>
```
{{< /alert >}}

## OneBEX API Reference

The OneBEX API is consumed by backup integrations. The current API is:

### API Endpoints

| Endpoint | Method | Purpose | HTTP Status Code |
|----------|--------|---------|------------------|
| `/` | `GET` | Returns basic server information and the available API routes. | `200` |
| `/status` | `GET` | Returns the current export status for a VM. Requires `VM_ID`. | `200`, `400` |
| `/exporters` | `GET` | Lists the exporter backends available in OneBEX. | `200` |
| `/export` | `POST` | Starts one or more disk exports for a VM. Requires `VM_ID` and `DS_ID`. `DISKS` is optional. | `200`, `400`, `404`, `500` |
| `/transfers/:TRANSFER_ID/info` | `GET` | Returns size and format information for a transfer. | `200`, `404`, `500` |
| `/images/:TRANSFER_ID` | `OPTIONS` | Returns supported image transfer features and concurrency limits. | `200` |
| `/images/:TRANSFER_ID/extents` | `GET` | Returns block extent information for a transfer. | `200`, `404`, `500` |
| `/images/:TRANSFER_ID` | `GET` | Reads a byte range from a transfer. Requires an HTTP `Range` header. | `206`, `400`, `404`, `416`, `500` |
| `/images/:TRANSFER_ID` | `PUT` | Image write operation. Currently not implemented. | `501` |
| `/images/:TRANSFER_ID` | `PATCH` | Accepts a flush operation when the request body uses `op=flush`. | `200`, `400`, `404` |
| `/transfer/:TRANSFER_ID/finalize` | `POST` | Finalizes a transfer and releases its exporter resources. | `200`, `400`, `404` |
| `/vms/:VM_ID/cancel` | `POST` | Cancels all active transfers for a VM. | `200`, `400` |
| `/vms/:VM_ID/finish` | `POST` | Finishes the VM backup session after all transfers have been finalized. | `200`, `409` |

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200 OK` | Request completed successfully. |
| `206 Partial Content` | Requested byte range returned successfully. |
| `400 Bad Request` | Invalid request, missing parameters, malformed JSON, invalid range format, or unsupported operation. |
| `404 Not Found` | Transfer, disk, export metadata, or endpoint not found. |
| `409 Conflict` | VM backup cannot finish while transfers are still pending. |
| `416 Range Not Satisfiable` | Required byte range is missing or invalid. |
| `500 Internal Server Error` | Unexpected server-side error, invalid export metadata, or exporter/backend failure. |
| `501 Not Implemented` | Operation exists but is not implemented. |

### Responses

#### `GET /`

**`200 OK`**

```json
{
  "NAME": "OpenNebula OneBEX Server",
  "VERSION": "0.1",
  "ROUTES": {
    "STATUS": "GET /status",
    "EXPORTERS": "GET /exporters",
    "EXPORT": "POST /export",
    "EXPORT_FINISH": "POST /vms/:VM_ID/finish",
    "EXPORT_CANCEL": "POST /vms/:VM_ID/cancel",
    "TRANSFER_INFO": "GET /transfers/:TRANSFER_ID/info",
    "IMAGE_OPTIONS": "OPTIONS /images/:TRANSFER_ID",
    "IMAGE_EXTENTS": "GET /images/:TRANSFER_ID/extents",
    "IMAGE_READ": "GET /images/:TRANSFER_ID",
    "IMAGE_WRITE": "PUT /images/:TRANSFER_ID",
    "IMAGE_FLUSH": "PATCH /images/:TRANSFER_ID",
    "IMAGE_FINALIZE": "POST /transfer/:TRANSFER_ID/finalize"
  }
}
```

#### `GET /status`

**`200 OK`**

```json
{
  "VM_ID": 123,
  "STATUS": "executing",
  "SUCCESS": true,
  "TRANSFERS": [
    {
      "TRANSFER_ID": "one-123-0-ab12cd34",
      "DISK_ID": 0,
      "EXPORTER": "nbd",
      "STATUS": "ready",
      "RC": true
    }
  ]
}
```

**`400 Bad Request`**

```json
{
  "error": "Missing VM_ID"
}
```

#### `GET /exporters`

**`200 OK`**

```json
{
  "EXPORTERS": [
    "nbd",
    "lvm"
  ]
}
```

#### `POST /export`

**`200 OK`**

```json
{
  "VM_ID": 123,
  "DS_ID": 100,
  "TRANSFERS": [
    {
      "TRANSFER_ID": "one-123-0-ab12cd34",
      "DISK_ID": 0,
      "EXPORTER": "nbd",
      "STATUS": "ready",
      "RC": true
    }
  ]
}
```

**`400 Bad Request`**

```json
{
  "error": "Missing VM_ID or DS_ID"
}
```

or:

```json
{
  "error": "Unsupported exporter: <exporter>"
}
```

**`404 Not Found`**

```json
{
  "error": "Disk 0 not found"
}
```

or:

```json
{
  "error": "Export file not found: <path>"
}
```

**`500 Internal Server Error`**

```json
{
  "error": "Invalid interactive_exports.json: <error>"
}
```

#### `GET /transfers/:TRANSFER_ID/info`

**`200 OK`**

Example for an NBD transfer:

```json
{
  "TRANSFER_ID": "one-123-0-ab12cd34",
  "SIZE": 10240,
  "FORMAT": "qcow2"
}
```

`SIZE` is returned in MiB.

**`404 Not Found`**

```json
{
  "error": "Transfer not found"
}
```

#### `OPTIONS /images/:TRANSFER_ID`

**`200 OK`**

```json
{
  "features": [
    "checksum",
    "extents",
    "flush",
    "zero"
  ],
  "max_readers": 1,
  "max_writers": 1
}
```

#### `GET /images/:TRANSFER_ID/extents`

**`200 OK`**

Returns block extent information as JSON. For example:

```json
[
  {
    "start": 0,
    "length": 1048576,
    "dirty": true,
    "zero": false,
    "hole": false
  }
]
```

**`404 Not Found`**

```json
{
  "error": "Transfer not found"
}
```

#### `GET /images/:TRANSFER_ID`

Requires a range in the following format:

```text
Range: bytes=start-end
```

**`206 Partial Content`**

Returns the requested byte range as binary `application/octet-stream` data.

**`400 Bad Request`**

```json
{
  "error": "Invalid Range format. Expected: bytes=start-end"
}
```

**`404 Not Found`**

```json
{
  "error": "Transfer not found"
}
```

**`416 Range Not Satisfiable`**

When the `Range` header is missing:

```json
{
  "error": "Missing Range header"
}
```

When the end byte is lower than the start byte:

```json
{
  "error": "Invalid Range header"
}
```

#### `PUT /images/:TRANSFER_ID`

**`501 Not Implemented`**

```json
{
  "error": "Write operation not implemented"
}
```

#### `PATCH /images/:TRANSFER_ID`

Request:

```json
{
  "op": "flush"
}
```

**`200 OK`**

The flush request is accepted. The response has no JSON body.

**`400 Bad Request`**

```json
{
  "error": "Unsupported operation"
}
```

**`404 Not Found`**

```json
{
  "error": "Transfer not found"
}
```

#### `POST /transfer/:TRANSFER_ID/finalize`

Optional request body:

```json
{
  "SUCCESS": true,
  "MESSAGE": "Transfer completed"
}
```

`SUCCESS` defaults to `true`.

**`200 OK`**

```json
{
  "VM_ID": 123,
  "TRANSFER_ID": "one-123-0-ab12cd34",
  "STATUS": "finished",
  "SUCCESS": true,
  "PENDING_TRANSFERS": []
}
```

**`400 Bad Request`**

Returned when the request body contains invalid JSON.

**`404 Not Found`**

```json
{
  "error": "Transfer not found"
}
```

#### `POST /vms/:VM_ID/cancel`

Optional request body:

```json
{
  "MESSAGE": "Backup cancelled by an Administrator"
}
```

`MESSAGE` defaults to `Backup cancelled`.

**`200 OK`**

```json
{
  "VM_ID": 123,
  "STATUS": "cancelled",
  "SUCCESS": false,
  "PENDING_TRANSFERS": []
}
```

**`400 Bad Request`**

Returned when the request body contains invalid JSON.

#### `POST /vms/:VM_ID/finish`

**`200 OK`**

```json
{
  "VM_ID": 123,
  "STATUS": "finished",
  "SUCCESS": true,
  "PENDING_TRANSFERS": []
}
```

If transfers are still pending:

**`409 Conflict`**

```json
{
  "VM_ID": 123,
  "STATUS": "executing",
  "SUCCESS": true,
  "PENDING_TRANSFERS": [
    "one-123-0-ab12cd34"
  ]
}
```

### Common Error Responses

Malformed JSON request bodies return **`400 Bad Request`**:

```json
{
  "error": "Invalid JSON body: <error>"
}
```

When a transfer does not exist or is no longer available, endpoints that look up an existing transfer return **`404 Not Found`**:

```json
{
  "error": "Transfer not found"
}
```

Unsupported endpoints return **`404 Not Found`**:

```json
{
  "error": "Unsupported endpoint"
}
```

Unexpected server errors and exporter/backend failures return **`500 Internal Server Error`**:

```json
{
  "error": "<error message>"
}
```

## Exporters

OneBEX uses exporters to expose VM disk data to external backup systems.

| Exporter | VM disk storage | Transport | Description |
|----------|-----------------|-----------|-------------|
| `nbd` | File-based `qcow2` disks | Network Block Device | Exposes the backup disk through NBD. OneBEX starts a read-only `qemu-nbd` process and serves the disk export through a Unix socket. |
| `lvm` | Disks on LVM datastores | Direct block-device reads | Exposes the prepared LVM block device directly. Full backups return the full device extent. Incremental backups use `thin_delta` to return changed extents from LVM thin metadata. |

{{< alert title="Note" type="info" >}}
The `nbd` exporter reads disk data with the `nbdsh` tool from the `python3-libnbd` package. This package is installed automatically as a dependency of `opennebula-node-kvm` on all supported platforms except SLES 15, where it is not available in the SUSE repositories. To use the `nbd` exporter on SLES 15 hosts, install `python3-libnbd` manually, for example from the openSUSE Leap 15.6 repositories, together with the matching `libnbd0` package. {{< /alert >}}
