---
title: "Developing OneBEX Exporters"
linkTitle: "OneBEX Exporters"
date: "2026-10-16"
description: "Implementing, installing, and testing a custom OneBEX disk exporter."
categories:
pageintoc: "300"
tags:
weight: "10"
---

<a id="onebex-exporter-development"></a>

<!--# Developing OneBEX Exporters -->

A **OneBEX exporter** is a Ruby class that lets OneBEX read a VM disk from a particular storage backend. The disk is prepared by the Transfer Manager (TM) driver and described in `interactive_exports.json`. OneBEX selects the exporter named in that file, manages the HTTP requests and transfer lifecycle, and delegates storage-specific operations to the exporter.

Create an exporter when adding a storage backend that is not handled by the OneBEx built-in [exporters]({{% relref "interactive_backup#exporters" %}}). The exporter must be able to report the virtual disk size, describe the relevant extents, read arbitrary byte ranges, and release any resources it opens. **It does not implement HTTP endpoints, create the backup image, or store the backup payload.**

For the three-phase backup workflow, the meaning of `interactive_exports.json`, supported configurations, and the complete HTTP API, see [Interactive Backup Integrations]({{% relref "interactive_backup#interactive-backup-integration" %}}).

{{< alert title="Important" type="info" >}}
A new exporter by itself is not sufficient for a storage integration. The matching TM driver must prepare a stable disk source, describe it in `interactive_exports.json`, and clean up backend snapshots or temporary devices after the backup. The exporter is responsible only for the resources that it opens or starts.
{{< /alert >}}

## OneBEX exporter interface

An exporter is a Ruby class under `OneBEX::Exporters`. OneBEX creates an instance for each disk transfer and calls its methods to open the prepared source, describe it, read data from it, and release resources when the transfer ends.

Each exporter must provide these six methods:

| Method | Responsibility | Expected result |
| --- | --- | --- |
| `initialize(config:, logger:)` | Receive the OneBEX configuration and logger. | Initializes the Ruby object. |
| `start(transfer)` | Validate the disk source, open or start its export, and retain any state needed later. | `true` when ready; raise on failure. |
| `info(transfer)` | Describe the exposed virtual disk. | A Hash with `:SIZE` in MiB and `:FORMAT`. |
| `blocks(transfer)` | Return the extents relevant to the backup. | An Array of extent Hashes, using byte offsets and lengths. |
| `data(transfer, range)` | Read bytes from the exposed disk at the requested offset. | A binary String containing exactly the requested number of bytes. |
| `finish(transfer, force: false)` | Close the export and release exporter-owned resources. | Conventionally `true`; raise on a cleanup failure. |

### Exporter Lifecycle and HTTP Requests

For each disk, OneBEX starts the transfer and calls the exporter as the external backup application requests data. The relevant routes are:

| Request | What OneBEX does |
| --- | --- |
| `POST /export` | Creates the selected disk transfers and starts their exporters. |
| `GET /transfers/:transfer_id/info` | Calls `info(transfer)`. |
| `GET /images/:transfer_id/extents` | Calls `blocks(transfer)`. |
| `GET /images/:transfer_id` | Parses the `Range` header and calls `data(transfer, range)`; returns the bytes with HTTP `206`. |
| `POST /transfer/:transfer_id/finalize` | Finalizes an individual transfer through the transfer manager. |
| `POST /vms/:vm_id/finish` | Completes the VM export after its transfers have finished. |
| `POST /vms/:vm_id/cancel` | Cancels the VM export and requests cleanup. |

The exporter must also be ready for repeated calls to `info`, `blocks`, and `data`, which are driven by HTTP requests rather than a single fixed call sequence.

The API shown here is for reading disk data. In the current OneBEX routes, `PUT /images/:transfer_id` returns `501` (not implemented), and the supported `PATCH` flush operation returns success without invoking an exporter method. A read-only exporter therefore does not need to implement write or flush methods.

### The Transfer Hash

OneBEX passes a `transfer` Hash to each exporter method. The `/export` route constructs it from `interactive_exports.json` and the export request:

| Key | Description |
| --- | --- |
| `transfer[:transfer_id]` | Unique identifier for this disk transfer, such as `one-123-0-a1b2c3d4`. |
| `transfer[:disk_id]` | VM disk ID. |
| `transfer[:exporter_name]` | Name used to select the exporter (`nbd`, `lvm`, etc.). |
| `transfer[:export_dir]` | The `BACKUP_DIR` provided to `POST /export`. |
| `transfer[:source]` | The disk entry's `source` field. |
| `transfer[:format]` | The disk entry's `format` field. |
| `transfer[:map]` | Optional block-map field, used by exporters that support it. |
| `transfer[:disk]` | Complete disk entry from `interactive_exports.json`, with **String** keys. |
| `transfer[:exporter]` | The exporter instance assigned by OneBEX. Do not overwrite it. |

For example, a custom entry with some additional attributes:

```json
{
  "0": {
    "exporter": "my_exporter",
    "source": "/path/to/prepared/snapshot.raw",
    "format": "raw",
    "snapshot_id": "snapshot-42",
    "mode": "full"
  }
}
```

An exporter may also save runtime state in the Hash, for use by later methods:

```ruby
transfer[:my_exporter_handle] = handle
transfer[:my_exporter_size]   = size_bytes
```

### Implementing the Operations

#### `start(transfer)`

`start` makes the already prepared disk available for random reads. Depending on the backend, it may open a file or block device, connect to a storage service, or launch a helper process. Validate required input and return `true` only after the source is usable. Save any handles, process IDs, or socket paths that later calls and cleanup will need.

The built-in NBD exporter illustrates two cases: if `source` is already an NBD URI, it reuses that export. Otherwise, it launches `qemu-nbd` in read-only mode for the source image and records its process ID, socket, and NBD URI in the transfer. It waits for the socket to become ready before returning.

If startup fails after allocating resources, clean up those resources before re-raising the error.

#### `info(transfer)`

Return the **virtual disk size in MiB** and the disk format:

```ruby
{
  :SIZE   => 10240,
  :FORMAT => 'raw'
}
```

`SIZE` is not a byte count. When converting from bytes, round up so the reported size covers the disk:

```ruby
mib = 1024 * 1024
size_mib = (size_bytes + mib - 1) / mib
```

#### `blocks(transfer)`

Return the disk extent map as an Array. Every extent uses byte offsets and lengths:

```ruby
[
  {
    :start  => 0,
    :length => 1048576,
    :dirty  => true,
    :zero   => false,
    :hole   => false
  }
]
```

- `start` is the byte offset from the beginning of the virtual disk.
- `length` is the number of bytes covered by the extent.
- `dirty` indicates that the extent has data to include in this backup.
- `zero` marks a region known to contain zeroes.
- `hole` marks an unallocated or sparse region.

For a basic **full backup**, a safe starting point is one dirty extent covering the entire virtual disk. For **incremental backups**, the exporter needs a backend-specific way to report the regions changed since the relevant snapshot or base backup.

Extents should use valid byte ranges, be sorted and non-overlapping, and stay within the virtual disk size. 

#### `data(transfer, range)`

The HTTP request includes a header such as:

```default
Range: bytes=1048576-2097151
```

OneBEX validates the header format and passes the exporter:

```ruby
{
  :start  => 1048576,
  :finish => 2097151,
  :length => 1048576
}
```

The endpoints are **inclusive**: `length = finish - start + 1`. Return a binary Ruby String of exactly `range[:length]` bytes, beginning at `range[:start]`. A short read is a failure, not a successful partial response. The exporter should also reject reads beyond the virtual disk's actual size.

#### `finish(transfer, force: false)`

Release whatever `start` allocated: open handles, child processes, sockets, or exporter-created temporary files. Implement cleanup so it is safe even if a handle or process is already gone. If `force` is `true`, avoid long graceful waits where the backend permits immediate termination.

## Example: A Minimal Exporter

The following implementation is a complete **full-backup example for an already prepared raw, regular file**. It demonstrates the six exporter methods without introducing backend-specific libraries or processes. It does **not** read `qcow2` directly, implement changed-block tracking, or create a consistent VM snapshot. Those responsibilities require an appropriate storage integration and TM driver.

```ruby
module OneBEX
    module Exporters
        class MyExporter
            MIB = 1024 * 1024

            def initialize(config:, logger:)
                @config = config
                @logger = logger
            end

            def start(transfer)
                source = transfer[:source].to_s
                format = transfer[:format].to_s

                raise 'Missing MyExporter source' if source.empty?
                raise "MyExporter supports only raw format: #{format}" unless format == 'raw'
                raise "Not a regular file: #{source}" unless File.file?(source)

                io = File.open(source, 'rb')
                size = io.stat.size
                raise "Invalid disk size: #{size}" unless size.positive?

                transfer[:my_exporter_io]   = io
                transfer[:my_exporter_size] = size
                true
            rescue StandardError
                io&.close
                raise
            end

            def info(transfer)
                size = transfer.fetch(:my_exporter_size)
                {
                    :SIZE   => (size + MIB - 1) / MIB,
                    :FORMAT => 'raw'
                }
            end

            def blocks(transfer)
                [
                    {
                        :start  => 0,
                        :length => transfer.fetch(:my_exporter_size),
                        :dirty  => true,
                        :zero   => false,
                        :hole   => false
                    }
                ]
            end

            def data(transfer, range)
                offset = Integer(range[:start])
                length = Integer(range[:length])
                size   = transfer.fetch(:my_exporter_size)

                raise "Invalid range: #{range}" if offset.negative? || length <= 0
                raise "Read exceeds disk size: #{range}" if offset + length > size

                bytes = transfer.fetch(:my_exporter_io).pread(length, offset)
                raise "Short read: expected #{length} bytes" unless bytes.bytesize == length

                bytes.b
            end

            def finish(transfer, force: false)
                io = transfer[:my_exporter_io]
                io.close if io && !io.closed?
                transfer[:my_exporter_io] = nil
                true
            end
        end
    end
end
```

This example uses a full-disk extent because it has no incremental block map. For a real integration, replace file access and extent discovery with operations appropriate for the backend.

## Installing and Registering an Exporter

Perform these changes on the **OpenNebula Front-end**, then synchronize the remotes so the exporter is available on the hypervisors.

1. **Install the Ruby class** under the OneBEX exporters directory, for example:

   ```text
   /var/lib/one/remotes/onebex/exporters/my_exporter.rb
   ```

2. **Load the class** from `/var/lib/one/remotes/onebex/config/environment.rb`:

   ```ruby
   require_relative '../exporters/my_exporter'
   ```

3. **Register its name** in the `exporter_registry` helper in `/var/lib/one/remotes/onebex/app/helpers.rb`:

   ```ruby
   registry.register('my_exporter', OneBEX::Exporters::MyExporter)
   ```

   This name must match the value of `"exporter"` in the disk's `interactive_exports.json` entry.

4. **Synchronize the remotes** to the hypervisors:

   ```bash
   onehost sync --force
   ```

5. **Verify the installation** on the hypervisor. Make sure the exporter can be loaded, any external dependencies are installed, and the OneBEX process has the required access to its disk sources. `GET /exporters` should include `my_exporter` after OneBEX starts.

If your OpenNebula deployment has multiple Front-ends with separate remotes trees, apply the changes to each relevant Front-end. Keep these modifications under configuration management, since package or remote updates may replace locally modified files.

## Testing an Exporter

Before connecting a backup application, test the exporter with a prepared disk source:

1. Confirm that the Ruby class loads and `GET /exporters` lists its registered name.
2. Check that `POST /export` selects the exporter and initializes each requested disk transfer.
3. Verify that `info` returns the correct virtual size in MiB and format.
4. Check that the full extent map covers the intended disk.
5. Read ranges at the beginning, middle, and end of the disk, including an unaligned range. Confirm that the returned bytes and byte count are exact, and that out-of-bounds reads fail.
6. Finalize and cancel transfers. Verify that exporter-owned handles, sockets, and processes are cleaned up without deleting TM-owned snapshots.
