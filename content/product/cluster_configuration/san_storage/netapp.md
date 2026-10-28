---
title: "NetApp SAN Datastore (EE)"
linkTitle: "NetApp - Native (EE)"
weight: "6"
---

OpenNebula’s **NetApp SAN Datastore** provides production-grade, native control of NetApp ONTAP block storage, from provisioning to cleanup, directly from OpenNebula. This integration enables the full lifecycle of Volumes, LUNs, and Snapshots — including FlexClone-based cloning and SAN-snapshot incremental backups — with secure HTTPS control and robust iSCSI/multipath host orchestration. This datastore driver is part of OpenNebula Enterprise Edition (EE).

### Key Benefits

Using the native NetApp driver, mixed 4k/8k (70/30) workloads delivered up to ~3x higher IOPS with ~4 to 10x lower write latency than LVM-thin, especially as snapshots accumulate. In pgbench, the NetApp path sustained ~2x higher, steadier transactions per second (TPS). On 4k fsync micro-writes it showed ~10 to 25% lower write latency. In short, the NetApp array keeps latency flat under snapshot pressure while host-side LVM-thin degrades sooner due to copy on write.

| Area | Benefit | Description |
|------|----------|--------------|
| **Automation** | Full lifecycle control | End-to-end creation, cloning, resizing, renaming, and cleanup of Volumes and LUNs directly from OpenNebula. |
| **Efficiency** | Space-efficient FlexClone and snapshot management | Uses NetApp’s native FlexClone for instant, zero-copy clones of non-persistent images. |
| **Performance** | Optimized host I/O path | Native multipath and iSCSI management per host for high throughput and availability. |
| **Reliability** | Job-aware REST orchestration | Each ONTAP operation is tracked via ONTAP’s job system with retries and error mapping. |
| **Data Protection** | Incremental SAN-snapshot backups (7.0.1+) | Enables block-level incremental backups based on array snapshots—no guest agents required. |
| **Security** | HTTPS control path | All ONTAP communication is performed securely via authenticated HTTPS REST calls. |
| **Scalability** | Parallel host operations | Safe concurrent attach/detach with per-path coordination and multipath support. |

### Supported NetApp Native Functionality

| NetApp Feature | Supported | Notes |
|----------------|------------|-------|
| **FlexClone** | Yes | Used for instant cloning of non-persistent images; optional split for persistent ones. |
| **Snapshot (manual)** | Yes | Created, listed, and deleted directly from OpenNebula; job-aware. |
| **Snapshot restore** | Yes | Volume restoration from snapshot UUID or name. |
| **Snapshot autogrow** | Yes | Tunable via `NETAPP_GROW_THRESHOLD` and `NETAPP_GROW_RATIO`. |
| **Incremental backups (SAN snapshot diff)** | Yes | New in 7.0.1; generates block-level sparse deltas without guest agents. |
| **Volume autosize** | Yes | Automatic growth and shrink; configurable thresholds. |
| **LUN mapping / igroup management** | Yes | Handled automatically per host; safe detach and cleanup. |
| **Multipath I/O** | Yes | Fully orchestrated; automatic detection, resize, and removal of maps. |
| **Snapshot policy management** | Yes | Driver enforces “no automatic snapshots”; OpenNebula controls all snapshots. |
| **Data encryption (at-rest)** | Yes | Supported transparently if enabled in ONTAP; not managed by OpenNebula. |
| **SnapMirror replication** | No (planned) | Not yet supported; may be added in future roadmap. |
| **QoS policy groups** | No | Not currently exposed through the datastore driver. |
| **SVM DR / MetroCluster** | No | Supported by ONTAP, but not orchestrated by OpenNebula. |


## Limitations and Unsupported Features

While the NetApp integration covers the full VM disk lifecycle and most SAN-level operations, it focuses strictly on **primary datastore management** using **iSCSI block devices**.
Some advanced ONTAP-specific or VMware-exclusive capabilities are intentionally not part of this driver.

{{< alert title="Important" type="warning" >}}
This integration targets block-level provisioning for OpenNebula environments.
It does not expose advanced replication or NAS-protocol features available in other ecosystems (e.g. VMware vVols or SnapMirror).
{{< /alert >}}

| Category | Unsupported Feature | Rationale / Alternative |
|-----------|--------------------|--------------------------|
| **Replication & DR** | SnapMirror, SnapVault | Planned for future releases; can be managed externally through ONTAP. |
| **Storage QoS / Performance tiers** | Policy group integration | Manual setup possible in ONTAP, not exposed in driver. |
| **Storage efficiency analytics** | Deduplication & compression metrics | Handled internally by ONTAP, not shown in OpenNebula UI. |
| **Encryption management** | Per-volume encryption toggling | Configure at SVM level outside OpenNebula. |
| **SVM HA features** | MetroCluster, SyncMirror | Can be used under the SVM, but not managed by OpenNebula. |


## NetApp ONTAP Setup

OpenNebula runs the set of datastore and transfer manager driver to register an existing NetApp SAN appliance. This set utilizes the NetApp ONTAP API to create volumes with a single LUN, which will be treated as Virtual Machine disks using the iSCSI interface. Both the Image and System datastores should use the same NetApp SAN appliance with identical Storage VM configurations (aggregates, etc.), as volumes (disks) are either cloned or renamed depending on the image type. Persistent images are renamed to the System datastore, while non‐persistent images are cloned using FlexClone and then split.

The [NetApp ONTAP documentation](https://docs.netapp.com/us-en/ontap/) may be useful during this setup.

{{< alert title="Note" type="info" >}}
Sharing datastores between multiple OpenNebula instances is not supported and may cause issues if they share datastore IDs.
{{< /alert >}}


The NetApp system requires specific configurations. This driver operates using a Storage VM that provides iSCSI connections, with volumes/LUNs mapped directly to each Host after creation. Configure and enable the iSCSI protocol according to your infrastructure requirements.

1. **Define Aggregates/Local Tiers for your Storage VM:**
   - In ONTAP System Manager: **Storage > Storage VMs > Select your SVM > Edit > Limit volume creation to preferred local tiers**
   - Assign at least one aggregate/tier and note their UUID(s) from the URL for later use

{{< alert title="Note" type="info" >}}
The UUID of an object is often found in the URL if using the web interface, otherwise you can use the ONTAP CLI to gather them: `vserver show -fields uuid`, `igroup show -fields uuid`, etc.
{{< /alert >}}

2. **To enable capacity monitoring:**
   - Enable *Enable maximum capacity limit* on the same Edit Storage VM screen
   - If not configured, set `DATASTORE_CAPACITY_CHECK=no` in both of the OpenNebula datastores’ attributes

3. This driver will manage the snapshots, so do not enable any automated snapshots for this SVM; they will not be picked up by OpenNebula unless created through OpenNebula.

4. If you do not plan to use the administrator account, create a new user with all API permissions and assign it to the SVM.

## Front-end Only Setup

The Front-end requires network access to the NetApp ONTAP API endpoint:

1. **API Access:**
   - Ensure network connectivity to the NetApp ONTAP API interface. The datastore will be in an ERROR state if the API is not accessible or the SVM cannot be monitored properly.

## Front-end & Node Setup

Configure both the Front-end and nodes with persistent iSCSI connections and multipath configuration as described by the [NetApp ONTAP Documentation - SAN Host Utilities Overview](https://docs.netapp.com/us-en/ontap-sanhost/hu_fcp_scsi_index.html):

1. **iSCSI Initiators:**
   - Configure initiator security in NetApp Storage VM:
     - **Storage VM > Settings > iSCSI Protocol > Initiator Security**
     - Add initiators from `/etc/iscsi/initiatorname.conf` (all nodes and Front-end)
   - Discover and login to the iSCSI targets:
     ~~~bash
     iscsiadm -m discovery -t sendtargets -p <target_ip>   # for each iSCSI target IP from NetApp
     iscsiadm -m node -l                                 # login to all discovered targets
     ~~~

2. **Persistent iSCSI Configuration:**
   - Set `node.startup = automatic` in `/etc/iscsi/iscsid.conf`
   - Ensure iscsid is started with `systemctl status iscsid`
   - Enable iscsid with `systemctl enable iscsid`

3. **Multipath Configuration:**
   Update `/etc/multipath.conf` to something like:
   ~~~text
    defaults {
      user_friendly_names no
      find_multipaths yes
    }

    devices {
      device {
        vendor "NETAPP"
        product "LUN"
        path_grouping_policy "group_by_prio"
        features "2 pg_init_retries 50"
        prio "ontap"
        failback "immediate"
        no_path_retry "queue"
        flush_on_last_del "always"
        dev_loss_tmo "infinity"
        user_friendly_names "no"
      }
    }

    blacklist {
      devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
      devnode "^hd[a-z][0-9]*"
      devnode "^cciss!c[0-9]d[0-9]*[p[0-9]*]"
    }
   ~~~

## OpenNebula Configuration

Create both datastores as NetApp (instant cloning/moving capabilities):

- **System Datastore**
- **Image Datastore**

### Create System Datastore

**Template required parameters:**

| Attribute             | Description                                     |
| --------------------- | ----------------------------------------------- |
| `NAME`                | Datastore name                                  |
| `TYPE`                | `SYSTEM_DS`                                     |
| `TM_MAD`              | `netapp`                                        |
| `DISK_TYPE`           | `BLOCK`                                         |
| `NETAPP_HOST`         | NetApp ONTAP API IP address                     |
| `NETAPP_USER`         | API username                                    |
| `NETAPP_PASS`         | API password                                    |
| `NETAPP_SVM`          | Storage VM UUID                                 |
| `NETAPP_AGGREGATES`   | Aggregate UUID(s)                               |
| `NETAPP_IGROUP`       | Initiator group UUID                            |
| `NETAPP_TARGET`       | iSCSI Target name                               |

**Example template:**

~~~shell
$ cat netapp_system.ds
NAME              = "netapp_system"
TYPE              = "SYSTEM_DS"
DISK_TYPE         = "BLOCK"
TM_MAD            = "netapp"
NETAPP_HOST       = "10.1.234.56"
NETAPP_USER       = "admin"
NETAPP_PASS       = "password"
NETAPP_SVM        = "c9dd74bc-8e3e-47f0-b274-61be0b2ccfe3"
NETAPP_AGGREGATES = "280f5971-3427-4cc6-9237-76c3264543d5"
NETAPP_IGROUP     = "27702521-68fb-4d9a-9676-efa3018501fc"
NETAPP_TARGET     = "iqn.1993-08.org.debian:01:1234"


$ onedatastore create netapp_system.ds
ID: 101
~~~

### Create Image Datastore

**Template required parameters:**

| Attribute           | Description                                     |
| ------------------- | ----------------------------------------------- |
| `NAME`              | Datastore name                                  |
| `TYPE`              | `IMAGE_DS`                                      |
| `DS_MAD`            | `netapp`                                        |
| `TM_MAD`            | `netapp`                                        |
| `DISK_TYPE`         | `BLOCK`                                         |
| `NETAPP_HOST`       | NetApp ONTAP API IP address                     |
| `NETAPP_USER`       | API username                                    |
| `NETAPP_PASS`       | API password                                    |
| `NETAPP_SVM`        | Storage VM UUID                                 |
| `NETAPP_AGGREGATES` | Aggregate UUID(s)                               |
| `NETAPP_IGROUP`     | Initiator group UUID                            |
| `NETAPP_TARGET`     | iSCSI Target name                               |

**Example template:**
~~~shell
$ cat netapp_image.ds
NAME              = "netapp_image"
TYPE              = "IMAGE_DS"
DISK_TYPE         = "BLOCK"
DS_MAD            = "netapp"
TM_MAD            = "netapp"
NETAPP_HOST       = "10.1.234.56"
NETAPP_USER       = "admin"
NETAPP_PASS       = "password"
NETAPP_SVM        = "c9dd74bc-8e3e-47f0-b274-61be0b2ccfe3"
NETAPP_AGGREGATES = "280f5971-3427-4cc6-9237-76c3264543d5"
NETAPP_IGROUP     = "27702521-68fb-4d9a-9676-efa3018501fc"
NETAPP_TARGET     = "iqn.1993-08.org.debian:01:1234"

$ onedatastore create netapp_image.ds
ID: 102
~~~

### Datastore Optional Attributes

Since Volumes contain the LUNs and snapshots, they are by default configured to contain 10% extra space and reserve this for snapshots. You can override these settings with the following datastore attributes, which should be same for both datastores:

**Template optional parameters:**

| Attribute                 | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `NETAPP_SUFFIX`           | Volume/LUN name suffix.                               |
| `NETAPP_GROW_THRESHOLD`   | Volume autogrow threshold in percent. Default: 90     |
| `NETAPP_GROW_RATIO`       | Volume maximum autogrow ratio. Default: 2             |
| `NETAPP_SNAPSHOT_RESERVE` | Volume snapshot reserve in percent. Default: 10       |
| `NETAPP_STANDALONE`       | Volume FlexClones always split. Default: NO           |

{{< alert title="Note" type="info" >}}
Volumes will be created with the extra reservation space in mind, which will be `size * ( 1 + NETAPP_SNAPSHOT_RESERVE / 100 )`.
{{< /alert >}}

## Datastore Internals

**Storage architecture details:**

- **Images:** Stored as a volume with a single LUN in NetApp
- **Naming Convention:**
  - Image datastore: `one_<datastore_id>_<image_id>` (volume), `one_<datastore_id>_<image_id>_lun` (LUN)
  - System datastore: `one_<vm_id>_disk_<disk_id>` (volume), `one_<datastore_id>_<vm_id>_disk_<disk_id>_lun` (LUN)
- **Operations:**
  - Non‐persistent: FlexClone, optionally split when `NETAPP_STANDALONE="YES"`
  - Persistent: Rename

Symbolic links from the System datastore will be created for each Virtual Machine on its Host once the LUNs have been mapped.

{{< alert title="Note" type="info" >}}
The minimum size for a NetApp volume is 20 MB, so any disk smaller than that will result in a 20 MB volume; however, the LUN inside will be the correct size.
{{< /alert >}}

{{< alert title="Warning" type="warning" >}}
NetApp ONTAP systems have Volume limitations found [in the NetApp Hardware Universe page](https://hwu.netapp.com), which can be anywhere from 1000 to 2500 Volumes. Be aware that each Image is a Volume and each Virtual Machine Disk is a Volume with a single LUN inside. This is to retain the atomic disk functionalities provided by OpenNebula.
{{< /alert >}}

**Backups process details:**

Both Full and Incremental backups are supported by NetApp. For Full Backups, a snapshot of the Volume containing the VM disk LUN is taken and attached to the host, where it is converted into a qcow2 image and uploaded to the backup datastore. 

Incremental backups are created by first creating the base full backup from the snapshot however this snapshot is then retained on the NetApp Volume rather than deleted after the backup is taken. When another incremental backup is taken, a new snapshot is taken and both the previous and current snapshots are cloned to new Volumes where they are attached to the host and compared for differences at the block level. These block changes are stored in a sparse QCOW2 file backed by the previous snapshot, which is then uploaded to the backup datastore.  The old snapshot is then removed while the new one is retained. When incremental backups are restored, the backing chain is rebuilt before restoring the backup to the VM disk.

{{< alert title="Note" type="info" >}}
You can configure the block size ( Defualt 2097152 B / 2 MB ) for incremental backups by modifing the file at `/var/lib/one-remotes/etc/tm/san/backup.conf`
{{< /alert >}}

{{< alert title="Warning" type="warning" >}}
The incremental backup feature of NetApp requires the `nbd` kernel module to be loaded and the `nbdfuse` package to be installed on all OpenNebula nodes.
{{< /alert >}}

## System Considerations

Occasionally, under network interruptions or if a volume is deleted directly from NetApp, the iSCSI connection may drop or fail. This can cause the system to hang on a `sync` command, which in turn may lead to OpenNebula operation failures on the affected Host. Although the driver is designed to manage these issues automatically, it’s important to be aware of these potential iSCSI connection challenges.

You may wish to contact the OpenNebula Support team to assist in this cleanup; however, here are a few advanced tips to clean these up if you are comfortable doing so:

- If you have extra devices from failures leftover, run:
  ~~~bash
  rescan_scsi_bus.sh -r -m
  ~~~
- If an entire multipath setup remains, run:
  ~~~bash
  multipath -f <multipath_device>
  ~~~
  *Be very careful to target the correct multipath device.*

{{< alert title="Note" type="info" >}}
This behavior stems from the inherent complexities of iSCSI connections and is not exclusive to OpenNebula or NetApp.
{{< /alert >}}

If devices persist, follow these steps:

1. Run `dmsetup ls --tree` or `lsblk` to see which mapped devices remain. You may see devices not attached to a mapper entry in `lsblk`.
2. For each such device (not your root device), run:
   ~~~bash
   echo 1 > /sys/bus/scsi/devices/sdX/device/delete
   ~~~
   where `sdX` is the device name.
3. Once those devices are gone, remove leftover mapper entries:
   ~~~bash
   dmsetup remove /dev/mapper/<device_name>
   ~~~
4. If removal fails:
   - Check usage:
     ~~~bash
     fuser -v $(realpath /dev/mapper/<device_name>)
     ~~~
   - If it’s being used as swap:
     ~~~bash
     swapoff /dev/mapper/<device_name>
     dmsetup remove /dev/mapper/<device_name>
     ~~~
   - If another process holds it, kill the process and retry:
     ~~~bash
     dmsetup remove /dev/mapper/<device_name>
     ~~~
   - If you can’t kill the process or nothing shows up:
     ~~~bash
     dmsetup suspend /dev/mapper/<device_name>
     dmsetup wipe_table /dev/mapper/<device_name>
     dmsetup resume /dev/mapper/<device_name>
     dmsetup remove /dev/mapper/<device_name>
     ~~~

This should resolve most I/O lockups caused by failed iSCSI operations. Please contact the OpenNebula Support team if you need assistance.
