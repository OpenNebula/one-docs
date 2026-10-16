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

From OpenNebula's point of view, an interactive backup has **three phases**:

1. **Pre-backup (Transfer Manager / TM driver).** The TM driver prepares the VM disks for export. Depending on the storage backend, it may create snapshots or temporary devices to provide a consistent source. It writes an `interactive_exports.json` file describing each prepared disk and starts OneBEX on the hypervisor. The export session is initialized through `POST /export`.
2. **Backup (Datastore / DS driver).** After the external backup application has retrieved the disk data and completed the export session, the DS driver creates a backup image containing the metadata OpenNebula needs to identify and restore that backup. The actual disk data remains in the external application's repository.
3. **Post-backup (TM driver).** The TM driver removes the temporary snapshots, devices, and files created during pre-backup. These storage resources are distinct from any sockets, processes, or connections managed by a OneBEX exporter.

**Between Step 1 and Step 2**, OneBEX serves the prepared disks over HTTP. The external backup application checks the VM status, obtains each transfer's disk information and block extents, and requests the byte ranges it needs. It then finalizes each disk transfer and finishes the VM export session. OneBEX releases exporter-owned resources and stops when there are no remaining transfers.

### Export Description and Exporter Selection

During pre-backup, the TM driver writes `<backup_dir>/interactive_exports.json`. The file contains a JSON object indexed by VM disk ID. Each disk entry tells OneBEX which exporter can read the prepared source and provides the information needed by that exporter.

For example:

```json
{
  "0": {
    "exporter": "nbd",
    "source": "/var/lib/one/datastores/100/123/disk.0",
    "format": "qcow2"
  },
  "1": {
    "exporter": "lvm",
    "source": "/dev/vg-one/lv-one-123-1",
    "format": "raw"
  }
}
```

The `exporter` selects one of the OneBEX available [exporters](#exporters), `source` identifies the prepared image or device, and `format` describes its disk format. The file can also include exporter-specific fields, for example snapshot identifiers or an incremental block map.

When OneBEX receives `POST /export`, it reads this file from the supplied `BACKUP_DIR`, selects the requested disks (or all disks when `DISKS` is omitted), and looks up the `exporter` name in its registry. OneBEX creates a separate transfer and exporter instance for each disk. The backup application then accesses those transfers through the HTTP API described [below](#onebex-api-reference).

To add a new storage backend, the corresponding TM driver must prepare its disk source and describe it in this file. A custom OneBEX exporter then implements the storage-specific reads. See [Developing OneBEX Exporters]({{% relref "onebex-exporter#onebex-exporter-development" %}}) for the Ruby interface, example implementation, installation, and testing instructions.

## Compatibility

The current interactive backup implementation supports the following configuration:

| **Component** | **Support** |
|-----------|---------|
| Hypervisor | KVM |
| VM disk storage | File-based `qcow2` disks, disks on LVM datastores, and Ceph RBD disks |
| Backup types | Full and incremental |
| Incremental mode | CBT only (`INCREMENT_MODE="CBT"`) |
| VM state | Running and powered off VMs |
| OneBEX exporter | NBD, LVM, RBD |

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

{{< alert title="Network Security Risk" type="warning" >}}
OneBEX uses unauthenticated HTTP by default and transfers VM disk data during backups. Unencrypted traffic can be intercepted, and reachable endpoints can be queried during active exports.

Enable TLS using the integration's supported proxy or equivalent on each hypervisor; OneBEX does not terminate TLS. For an example with Veeam, see [Configuring SSL in the Hosts]({{% relref "product/cluster_configuration/backup_system/veeam.md#41-configuring-ssl-in-the-hosts" %}}).

Restrict access to OneBEX and proxy ports to the Front-end and required backup components on every eligible hypervisor. If TLS terminates at a local proxy, keep its HTTP connection to OneBEX local to the host.
{{< /alert >}}

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

The configuration file defines the OneBEX listen address, logging settings, and Puma web server concurrency limits.

### Server Configuration

| **Parameter** | **Default value** | **Description** |
|-----------|---------------|-------------|
| `:host:` | `0.0.0.0` | Address where OneBEX listens for HTTP requests. By default, it listens on all available interfaces. |
| `:port:` | `13014` | TCP port where OneBEX listens for HTTP requests. |

### Log Configuration

| **Parameter** | **Default value** | **Description** |
|-----------|---------------|-------------|
| `:log: :level:` | `2` | Log verbosity level. Supported values are `0` for `ERROR`, `1` for `WARNING`, `2` for `INFO`, and `3` for `DEBUG`. |
| `:log: :system:` | `file` | Logging backend used by OneBEX. Supported values are `file` and `syslog`. |

### Puma Configuration

| **Parameter** | **Default value** | **Description** |
|-----------|---------------|-------------|
| `:puma: :min_threads:` | `1` | Minimum number of Puma threads used to handle concurrent OneBEX HTTP requests. |
| `:puma: :max_threads:` | `4` | Maximum number of Puma threads used to handle concurrent OneBEX HTTP requests. |

These limits apply to HTTP requests, not to the number of VM sessions or exported disks.

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

{{< alert title="Network Security Risk" type="warning" >}}
By default, the restore writer listens on all interfaces (`0.0.0.0`). Set the `ONE_BEX_WRITER_ADDR` environment variable in the Front-end to constrain it to listen on a specific address. Since the writer accepts raw image data without authentication or encryption, restrict the restore transfer ports at the firewall to the integration components that send restore data.
{{< /alert >}}

The writer accepts one frame per TCP connection. Each frame starts with a one-byte type:

| Type | Name | Payload |
|------|------|---------|
| `0x00` | `DATA` | Three unsigned 64-bit big-endian integers containing the start byte, payload size, and total image size, followed by the image data. |
| `0x01` | `FINISH` | No payload. Stops the writer and lets OpenNebula finalize the restore transfer. |

After sending all the image data, the integration must open one final connection to the restore transfer port and send the `FINISH` frame. The integration must also send this frame when a restore is cancelled or fails. Do not send more data after the `FINISH` frame.

If a restore fails, the restored Image remains in `LOCKED` state and should be removed manually:

{{< alert title="Note" type="info" >}}
Get the restore transfer port from the Image `PATH` attribute and send the `FINISH` frame to the writer. This stops the writer gracefully and allows OpenNebula to complete the transfer cleanup. Use a Front-end address that is reachable from the system where you run the command. If you run it directly on the Front-end, you can use `127.0.0.1`. The restore transfer port must be allowed by any intervening firewall:

```shell
python3 -c 'import socket, sys; s = socket.create_connection((sys.argv[1], int(sys.argv[2]))); s.sendall(b"\x01"); s.close()' <FRONTEND_ADDRESS> <PORT_ID>
```

After the writer finishes, delete the incomplete Image:

```shell
oneimage delete <IMAGE_ID>
```
{{< /alert >}}

## OneBEX API Reference

The OneBEX API is consumed by backup integrations. The current API is:

### API Endpoints

| **Endpoint** | **Method** | **Purpose** | **HTTP Status Code** |
|----------|--------|---------|------------------|
| `/` | `GET` | Returns basic server information and the available API routes. | `200` |
| `/status` | `GET` | Returns the current export status for a VM. Requires `VM_ID`. | `200`, `400` |
| `/exporters` | `GET` | Lists the exporter backends available in OneBEX. | `200` |
| `/export` | `POST` | Starts one or more disk exports for a VM. Requires `VM_ID`, `DS_ID`, and `BACKUP_DIR`. `DISKS` is optional. | `200`, `400`, `404`, `409`, `500`, `503` |
| `/transfers/:TRANSFER_ID/info` | `GET` | Returns size and format information for a transfer. | `200`, `404`, `500` |
| `/images/:TRANSFER_ID` | `OPTIONS` | Returns supported image transfer features and concurrency limits. | `200` |
| `/images/:TRANSFER_ID/extents` | `GET` | Returns block extent information for a transfer. | `200`, `404`, `500` |
| `/images/:TRANSFER_ID` | `GET` | Reads a byte range from a transfer. Requires an HTTP `Range` header. | `206`, `400`, `404`, `416`, `500` |
| `/images/:TRANSFER_ID` | `PUT` | Image write operation. Currently not implemented. | `501` |
| `/images/:TRANSFER_ID` | `PATCH` | Accepts a flush operation when the request body uses `op=flush`. | `200`, `400`, `404` |
| `/transfer/:TRANSFER_ID/finalize` | `POST` | Finalizes a transfer and releases its exporter resources. | `200`, `400`, `404` |
| `/vms/:VM_ID/cancel` | `POST` | Cancels VM export preparation and active transfers, waiting for cleanup. | `200`, `400`, `500` |
| `/vms/:VM_ID/finish` | `POST` | Publishes the VM result after preparation and all transfer cleanup have completed. | `200`, `409`, `500` |

### HTTP Status Codes

| **Code** | **Description** |
|------|-------------|
| `200 OK` | Request completed. Check `SUCCESS` in lifecycle responses for the backup result. |
| `206 Partial Content` | Requested byte range returned successfully. |
| `400 Bad Request` | Invalid request, missing parameters, malformed JSON, invalid range format, or unsupported operation. |
| `404 Not Found` | Transfer, disk, export metadata, or endpoint not found. |
| `409 Conflict` | An export already exists or was cancelled/failed in the current process, or a VM cannot finish while preparation or transfer cleanup is pending. |
| `416 Range Not Satisfiable` | Required byte range is missing or invalid. |
| `500 Internal Server Error` | Unexpected server-side error, invalid export metadata, or exporter/backend failure. |
| `501 Not Implemented` | Operation exists but is not implemented. |
| `503 Service Unavailable` | OneBEX is stopping because the export was not admitted. |

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
    "lvm",
    "rbd"
  ]
}
```

#### `POST /export`

Request:

```json
{
  "VM_ID": 123,
  "DS_ID": 100,
  "BACKUP_DIR": "/var/lib/one/datastores/100/123/backup",
  "DISKS": [
    0
  ]
}
```

`BACKUP_DIR` is the VM backup directory that contains `interactive_exports.json`. When `DISKS` is omitted, OneBEX starts exports for all disks listed in `interactive_exports.json`.

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
  "error": "Missing VM_ID, DS_ID or BACKUP_DIR"
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

**`409 Conflict`**

A second export cannot replace a VM's active or preparing export:

```json
{
  "error": "VM 123 already has an export"
}
```

If the VM was cancelled, or its previous export failed in the current process:

```json
{
  "error": "Backup cancelled"
}
```

**`503 Service Unavailable`**

```json
{
  "error": "OneBEX is stopping"
}
```

No export was admitted for this response. TM waits up to 60 seconds for the server to stop and retries once, starting a new server if necessary.

**`500 Internal Server Error`**

Invalid export metadata or an unexpected preparation/exporter error returns its error message:

```json
{
  "error": "<error message>"
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
  "MESSAGE": "Backup cancelled by an Administrator",
  "FORCE": true
}
```

`MESSAGE` defaults to `Backup cancelled`.

`FORCE` defaults to `true`. When `true`, OneBEX cancels immediately, without waiting for export preparation, active read operations, or another finalizer. Set it to `false` to wait for in-progress operations and stop exporter processes gracefully.

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

If export preparation or transfer cleanup is still pending:

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

OneBEX selects a storage-specific exporter for each prepared disk, as described in [Export Description and Exporter Selection](#export-description-and-exporter-selection). The built-in implementations are listed below.

To implement and register another storage backend, see [Developing OneBEX Exporters]({{% relref "onebex-exporter#onebex-exporter-development" %}}).

| **Exporter** | **VM disk storage** | **Transport** | **Description** |
|----------|-----------------|-----------|-------------|
| `nbd` | File-based `qcow2` disks | Network Block Device | Exposes the backup disk through NBD. OneBEX starts a read-only `qemu-nbd` process and serves the disk export through a Unix socket. |
| `lvm` | Disks on LVM datastores | Direct block-device reads | Exposes the prepared LVM block device directly. Full backups return the full device extent. Incremental backups use `thin_delta` to return changed extents from LVM thin metadata. |
| `rbd` | Ceph RBD disks | Direct RBD reads | Exposes the prepared Ceph RBD snapshot directly. Full backups return the full image extent, while incremental backups return the changed extents between RBD snapshots. |

{{< alert title="Note" type="info" >}}
The `nbd` exporter reads disk data with the `nbdsh` tool from the `python3-libnbd` package. This package is installed automatically as a dependency of `opennebula-node-kvm` on all supported platforms except SLES 15, where it is not available in the SUSE repositories. To use the `nbd` exporter on SLES 15 hosts, install `python3-libnbd` manually, for example from the openSUSE Leap 15.6 repositories, together with the matching `libnbd0` package. {{< /alert >}}

## Example: Backing Up and Restoring a VM with OneBEX

This example shows how an external backup application can retrieve **full or incremental backups** of VM `132` and restore a disk to an OpenNebula Image. Replace the example IDs, hostnames, and ports with those in your environment. OneBEX runs on the hypervisor at `http://host:13014`. The restore writer runs on the **Front-end**.

### Retrieving a Backup (Full or Incremental)

For additional configuration details, see the [OpenNebula VM Backup Operations](https://docs.opennebula.io/7.4/product/virtual_machines_operation/virtual_machine_backups/operations/) guide.

1. **Configure the VM backup.** Set `BACKUP_CONFIG` in the VM Template, or update an existing VM with `onevm updateconf 132`.

    For a **full backup**:

    ```text
    BACKUP_CONFIG = [
        INTERACTIVE = "YES",
        MODE        = "FULL",
        DISK_IDS    = "0"
    ]
    ```

    For **incremental backups** (CBT):

    ```text
    BACKUP_CONFIG = [
        INTERACTIVE    = "YES",
        MODE           = "INCREMENT",
        INCREMENT_MODE = "CBT",
        DISK_IDS       = "0"
    ]
    ```

    `DISK_IDS` is optional: omit it to back up all eligible disks, or provide a comma-separated list such as `"0,2"`. Select disks here, **not through `POST /export`**. The first backup of an incremental chain is a full base backup. Later backups contain changes **only since the latest successful backup/increment in that chain**. You cannot choose an older increment as the source for the next incremental backup. Changing the selected disk set resets the chain and requires a new full base. Interactive incrementals support CBT, not `SNAPSHOT`.

2. **Use an interactive Backup Datastore.** The target Backup Datastore must have `TYPE="BACKUP_DS"` and `DS_MAD="interactive"` and be available to the VM's cluster. It stores backup metadata; the external backup application stores the disk data. See [Integration Datastore](#integration-datastore).

3. **Start a VM backup** through the integration's OpenNebula API workflow. An equivalent CLI example is:

    ```shell
    onevm backup --schedule now -d 100 132
    ```

    The Transfer Manager (TM) prepares the disks and calls `POST /export` automatically. **The external backup application must not call `/export` again.**

4. **Discover the ready transfer** on the hypervisor:

    ```shell
    curl -sS 'http://host:13014/status?VM_ID=132' | jq
    ```

    ```json
    {
      "VM_ID": 132,
      "STATUS": "executing",
      "SUCCESS": true,
      "TRANSFERS": [
        {
          "TRANSFER_ID": "one-132-0-0bbaeb42",
          "DISK_ID": 0,
          "EXPORTER": "nbd",
          "STATUS": "ready",
          "RC": true
        }
      ]
    }
    ```

    Each disk has its own `TRANSFER_ID`, and each backup run generates new transfer IDs.


5. **Retrieve disk information and extents.** Once the transfer is ready, retrieve the disk size, format, and extent map:

    ```shell
    curl -sS 'http://host:13014/transfers/one-132-0-0bbaeb42/info' | jq
    curl -sS 'http://host:13014/images/one-132-0-0bbaeb42/extents' | jq
    ```

    The `info` endpoint returns the virtual disk size in MiB and its format. For example, a 7 GiB disk returns:

    ```json
    {
      "TRANSFER_ID": "one-132-0-0bbaeb42",
      "SIZE": 7168,
      "FORMAT": "qcow2"
    }
    ```

    The `extents` endpoint returns the disk regions to process. Its response depends on the backup type:

    - **Full backup:** The extent map describes the disk regions required for a complete backup. For example, a single extent covering the entire 7 GiB disk:

      ```json
      [
        {
          "start": 0,
          "length": 7516192768,
          "dirty": true,
          "zero": false,
          "hole": false
        }
      ]
      ```

      In this example, the complete disk must be read, starting at byte `0` for a total of `7516192768` bytes. Depending on the storage backend, the extent map may contain multiple regions, including zeroed or unallocated areas.

    - **Incremental backup:** The extent map identifies only the disk regions changed since the previous backup in the incremental chain. For example:

      ```json
      [
        {
          "start": 1048576,
          "length": 2097152,
          "dirty": true,
          "zero": false,
          "hole": false
        }
      ]
      ```

      In this example, only 2 MiB of the 7 GiB disk has changed, starting at offset 1 MiB. The backup solution only needs to retrieve the changed data rather than reading the entire disk.

    All offsets and lengths are expressed in **bytes**. The `dirty`, `zero`, and `hole` flags indicate whether a region has changed, contains zeroes, or is unallocated, respectively.


6. **Read the required extents** with `GET /images/:TRANSFER_ID` and an inclusive `Range` header. For the incremental extent above:

    ```shell
    curl -sS --fail \
      -H 'Range: bytes=1048576-3145727' \
      'http://host:13014/images/one-132-0-0bbaeb42' \
      --output changed-blocks.bin
    ```

    The response is `206 Partial Content` with raw virtual-disk bytes. Repeat for all required extents, splitting large ranges into manageable requests. Save each extent **at its original disk offset**, preserving zero/hole information. A full backup needs the entire required extent map; an incremental backup needs the changed extents and a reference to its preceding backup. Keep the complete chain in the external repository for restores.


7. **Finalize each disk transfer.** After storing all required data for a disk, notify OneBEX that the transfer completed successfully:

   ```shell
   curl -sS -X POST 'http://host:13014/transfer/one-132-0-0bbaeb42/finalize' \
     -H 'Content-Type: application/json' \
     -d '{"SUCCESS":true}' | jq
   ```

   **Every disk transfer must be finalized individually.** Repeat this request for each `TRANSFER_ID` returned by `GET /status`.

   If a disk backup fails, finalize its transfer with `SUCCESS=false`:

   ```shell
   curl -sS -X POST 'http://host:13014/transfer/one-132-0-0bbaeb42/finalize' \
     -H 'Content-Type: application/json' \
     -d '{"SUCCESS":false,"MESSAGE":"Failed to store disk data"}' | jq
   ```

   If one disk fails, the remaining transfers must still be finalized. Do not report success until the external backup application has safely stored all required data.

8. **Finish the VM backup.** Once **all disk transfers have been finalized**, notify OneBEX that the VM backup session is complete:

    ```shell
    curl -sS -X POST 'http://host:13014/vms/132/finish' | jq
    ```

    If all transfers succeeded, the response is:

    ```json
    {
      "VM_ID": 132,
      "STATUS": "finished",
      "SUCCESS": true,
      "PENDING_TRANSFERS": []
    }
    ```

    If any transfer failed, the VM backup result reflects that failure. If transfers are still pending, the endpoint returns `409 Conflict` with `STATUS="executing"` instead of completing the session.

    **Cancellation:** Alternatively, to cancel the entire VM backup and clean up its transfers, use:

    ```shell
    curl -sS -X POST 'http://host:13014/vms/132/cancel' \
      -H 'Content-Type: application/json' \
      -d '{"FORCE":true}' | jq
    ```

    Cancellation handles the transfer cleanup and completes the cancelled VM session. There is no need to call the VM finish endpoint afterwards.


### Restoring a Disk with OneBEX

1. **Create an Image** in the destination Image Datastore using the OneBEX restore URL as its `PATH`:

    ```text
    onebex://<IMAGE_DS_ID>:<PORT_ID>
    ```

    For example, using an available restore port `49001` and Image Datastore `1`:

    ```shell
    oneimage create --datastore 1 --name restored-vm132-disk0 \
      --type OS --path 'onebex://1:49001'
    ```

    The port must be available and assigned to this restore session. Inspect the newly created Image with `oneimage show <IMAGE_ID>` to confirm its `PATH` and restore port. OpenNebula starts a TCP restore writer on the **Front-end**; the Image remains `LOCKED` while data is being received.

2. **Send the restored virtual-disk contents** to `<FRONTEND_ADDRESS>:<PORT_ID>`. The external application reconstructs the requested restore point from its full/incremental chain, then sends the disk data as **DATA frames**, one TCP connection per frame:

    | Field | Size | Value |
    |---|---|---|
    | Frame type | 1 byte | `0x00` (`DATA`) |
    | Start offset | 8 bytes | Unsigned 64-bit, big-endian |
    | Payload length | 8 bytes | Unsigned 64-bit, big-endian |
    | Total disk size | 8 bytes | Unsigned 64-bit, big-endian |
    | Data | Payload length | Raw virtual-disk bytes |

    Send each block at its correct offset. This is a **TCP protocol**, not a OneBEX HTTP endpoint.

3. **Finish the restore.** After all data has been sent, open one final TCP connection to the same Front-end port and send the single byte **`0x01` (`FINISH`)**, with no payload. The writer stops and OpenNebula can finalize the Image. Send `FINISH` even if the restore is cancelled or fails, to release the writer. Do not send data after it. If the restore fails and the Image remains `LOCKED`, clean up the incomplete Image as described in [Restoring Interactive Backups](#restoring-interactive-backups).
