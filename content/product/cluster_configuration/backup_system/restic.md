---
title: "Backup Datastore: Restic"
linkTitle: "Restic"
date: "2025-02-17"
description:
categories:
pageintoc: "78"
tags:
weight: "2"
---

<a id="vm-backups-restic"></a>

<!--# Backup Datastore: Restic -->

[Restic](https://restic.net/) is an open source (BSD 2-Clause License) backup tool designed for speed, security, and efficiency. The current implementation of the driver supports SFTP and S3 storage types. Restic offers interesting features to store backups, like deduplication (only transferring image blobs not already present in the repository) or compression (enabled by default).

In both the Enterprise and Community editions of OpenNebula, the correct version of restic is included as a dependency. In this guide we will use the following terminology (introduced by restic):

- *Repository*: This is the storage location where VM disk backups will be stored. Depending on the selected backend, it can be a directory on an SFTP backup server or a path inside an S3 bucket. Restic creates a specific internal structure to store the backups efficiently. OpenNebula will create a separate restic repository for each VM or backup job.
- *Snapshot*: It represents a backup and it is referenced by a unique hash (e.g., `eda52f34`). Each snapshot stores a VM backup and includes the backed up disks and the metadata description of the VM at the time you make the backup.
- *Backup Server*: A Host that stores VM backups and restic repositories when using the SFTP backend.
- *S3 Bucket*: An AWS S3 or S3-compatible bucket that stores the restic repositories when using the S3 backend.

## Step 1. Backend Configuration

The first thing you need to do is prepare the storage backend that will hold the restic repositories. The required setup depends on the backend selected for the datastore.

The restic repository itself does not need to be created manually. OpenNebula initializes the repository automatically during the first backup, using the datastore configuration.

### SFTP Backend

For the SFTP backend, set up a backup server to hold the restic repositories. Typically the server will have a dedicated storage medium to store the backups (e.g., iSCSI volume). Also, the Hosts and Front-end need to reach the server IP.

To set up the backup server perform the following steps:

- Create a user account with username `oneadmin`. This account will be used to connect to the server.
- Copy the SSH public key of existing `oneadmin` from the OpenNebula Front-end to this new `oneadmin` account.
- Check that `oneadmin` can SSH access the server **without being prompted for a password** from the Front-end and Hosts.
- Create the following folder in the backup server `/var/lib/one/datastores`, change the ownership to `oneadmin`.
- Mount the storage volume in `/var/lib/one/datastores`.
- Finally make sure **rsync** and **qemu-img** commands are installed in the backup server.

The following example showcases this setup using a dedicated 1.5T volume for backups:

```shell
id oneadmin
 uid=9869(oneadmin) gid=9869(oneadmin) groups=9869(oneadmin)
```

```shell
lsblk
 sdb                         8:16   0  1.5T  0 disk
 └─sdb1                      8:17   0  1.5T  0 part
   └─vgBackup-lvBackup     253:0    0  1.5T  0 lvm  /var/lib/one/datastores
```

```shell
ls -ld /var/lib/one/datastores/
  drwxrwxr-x 2 oneadmin oneadmin 4096 Sep  3 12:04 /var/lib/one/datastores/
```

### S3 Backend

For the S3 backend, prepare an AWS S3 bucket or an S3-compatible bucket before creating the OpenNebula Backup Datastore. The bucket must be reachable from the Front-end and Hosts.

The S3 credentials configured in the datastore must allow OpenNebula to list the bucket and to create, read, and delete objects in it.

For AWS S3, use an access key and secret access key with permissions for the target bucket. For S3-compatible backends, use the equivalent credentials and enable path-style access if required by the service.

If the S3 endpoint uses a private CA certificate, make the CA certificate file available on the KVM Hosts where restic commands run. For lab or debugging environments, TLS verification can also be disabled in the datastore configuration.

## Step 2. [Front-end] Create a Restic Datastore

Create an OpenNebula Backup Datastore with the attributes required by the selected backend. The `RESTIC_PASSWORD` attribute is used by restic to encrypt and access the repository.

### SFTP Backend

For SFTP, create a datastore template with the backup server address. `RESTIC_BACKEND` can be omitted because SFTP is the default backend.

```shell
cat ds_restic.txt
 NAME   = "RBackups"
 TYPE   = "BACKUP_DS"
 
 DS_MAD = "restic"
 TM_MAD = "-"
 
 RESTIC_BACKEND     = "SFTP"
 RESTIC_PASSWORD    = "opennebula"
 RESTIC_SFTP_SERVER = "192.168.1.8"
```

*Note*: The `RESTIC_SFTP_SERVER` is the IP address of the backup server. It needs to be reachable from the Front-end and Hosts.

```shell
onedatastore create ds_restic.txt
 ID: 100
```

You can also create the DS through Sunstone like any other datastore, go to **Storage -> Datastores** and select **Backup**, in the **Storage backend** menu select **Backup - Restic**:

{{< image
  pathDark="/images/storage/dark/backup_restic_create.png"
  path="/images/storage/light/backup_restic_create.png"
  alt="Create Restic Backup" align="center" width="90%" mb="20px"
>}}

After some time, the datastore should be monitored:

```shell
onedatastore list
 ID  NAME                                         SIZE AVA CLUSTERS IMAGES TYPE DS      TM      STAT
 100 RBackups                                     1.5T 91% 0             0 bck  restic  -       on
   2 files                                       19.8G 84% 0             0 fil  fs      local   on
   1 default                                     19.8G 84% 0             1 img  fs      local   on
   0 system                                          - -   0             0 sys  -       local   on
```

### AWS S3 Backend

For AWS S3, use `RESTIC_BACKEND="S3"`. The endpoint can be omitted, in which case it defaults to `s3.amazonaws.com`, and path-style access is normally not required.

```shell
cat ds_restic_aws_s3.txt
 NAME   = "RBackups-AWS-S3"
 TYPE   = "BACKUP_DS"
 
 DS_MAD = "restic"
 TM_MAD = "-"
 
 RESTIC_BACKEND              = "S3"
 RESTIC_PASSWORD             = "opennebula"
 RESTIC_S3_BUCKET            = "opennebula-backups"
 RESTIC_S3_REGION            = "us-west-1"
 RESTIC_S3_ACCESS_KEY_ID     = "S3ACCESSKEYID"
 RESTIC_S3_SECRET_ACCESS_KEY = "S3SECRETACCESSKEY"
 TOTAL_MB                    = "512000"
```

```shell
onedatastore create ds_restic_aws_s3.txt
 ID: 101
```

### S3-Compatible Backend

For non-AWS S3-compatible backends, create a datastore template with `RESTIC_BACKEND="S3"` and set the S3 endpoint explicitly. The endpoint can include the scheme; for plain HTTP endpoints, specify it explicitly, for example `http://s3-storage:8080`. Many S3-compatible backends require path-style access. In that case set `RESTIC_S3_FORCE_PATH_STYLE="YES"`.

```shell
cat ds_restic_s3.txt
 NAME   = "RBackups-S3"
 TYPE   = "BACKUP_DS"
 
 DS_MAD = "restic"
 TM_MAD = "-"
 
 RESTIC_BACKEND              = "S3"
 RESTIC_PASSWORD             = "opennebula"
 RESTIC_S3_ENDPOINT          = "http://s3-storage:8080"
 RESTIC_S3_BUCKET            = "opennebula-backups"
 RESTIC_S3_ACCESS_KEY_ID     = "S3ACCESSKEYID"
 RESTIC_S3_SECRET_ACCESS_KEY = "S3SECRETACCESSKEY"
 RESTIC_S3_FORCE_PATH_STYLE  = "YES"
 TOTAL_MB                    = "512000"
```

```shell
onedatastore create ds_restic_s3.txt
 ID: 102
```

For S3 datastores, OpenNebula does not discover the bucket quota automatically. The total capacity is taken from the `TOTAL_MB` datastore attribute. The examples above set `TOTAL_MB="512000"` to configure a custom `500G` capacity. If `TOTAL_MB` is omitted, the driver uses `1048576` MB (`1024G`) as the default capacity. Used capacity is computed from backup images registered in OpenNebula.

OpenNebula creates a separate restic repository inside the SFTP path or S3 bucket for each VM or backup job.

{{< alert title="Note" type="info" >}}
At this time, S3 Restic datastore creation is expected to be performed through the CLI, or through the standard XML-RPC datastore allocation API by passing the datastore template attributes shown above. No new XML-RPC method is required for the driver itself: once the Backup Datastore exists, backup and restore operations use the regular OpenNebula backup APIs. FireEdge configuration support for S3-specific attributes will be added in future releases.{{< /alert >}}

## Repository Maintenance and Troubleshooting

### Repository Pruning

Data not referenced by any snapshot needs to be deleted by running the `prune` command in the repository. This operation is executed by OpenNebula whenever an image backup is deleted, either because of an explicit removal or to conform the retention policy set.

### Repository is locked

During the operation of the VM backups you may rarely find that the repository is left in a locked state. You should see an error similar to:

```default
unable to create lock in backend: repository is already locked exclusively by PID 111971 on ubuntu2204-kvm-qcow2-6-5-yci34-0 by oneadmin (UID 9869, GID 9869)
lock was created at 2022-11-28 17:33:51 (55.876852076s ago)
storage ID 1448874c
```

To recover from this error, check there are no ongoing operations and execute `restic unlock --remove-all` for the repository.

### Limiting I/O and CPU usage

Backup operations may incur in high I/O or CPU demands. This will add noise to the VMs running in the hypervisor. You can control resource usage of the backup operations by:

* Lowering the priority of the associated processes. Backup commands are run under a given ionice priority (best-effort, class 2 scheduler); and a given nice.
* Confining the associated processes in a cgroup. OpenNebula will create a systemd slice for each Backup Datastore so the backup commands run with a limited number or read/write IOPS and CPU Quota.

Note that for the latter, you need to delegate the `cpu` and `io` cgroup controllers to the `oneadmin` user. This way OpenNebula can set `CPUQuota`, `IOReadIOPSMax` and `IOWriteIOPSMax`.

To delegate the controllers you need to add the following file for `oneadmin` account (id 9869) in **all the Hosts** (note that you’d probably need to create the user service folder):

```shell
cat /etc/systemd/system/user@9869.service.d/delegate.conf
 [Service]
 Delegate=cpu cpuset io
```

After that, reboot the hypervisor and double check that the setting is correct (you need to login as `oneadmin`):

```shell
cat /sys/fs/cgroup/user.slice/user-9869.slice/cgroup.controllers
 cpuset cpu io memory pids
```

### Temporary Backup Path

Disk images backups are generated within a local folder in the Host where the VM is running. These images are later uploaded to the selected Backup Datastore. By default, this temporary path is set to the VM folder, in `/var/lib/one/datastores/<DATASTORE_ID>/<VM_ID>/backup`.

However, it’s possible to modify this path to utilize alternative locations, such as different local volumes, or to opt out of using the shared VM folder entirely.

To change the base folder to store disk backups for **all** Hosts, edit `/var/lib/one/remotes/etc/datastore.conf` and set the `BACKUP_BASE_PATH` variable. Please note this file uses shell syntax.

### Bridge List

The `BRIDGE_LIST` parameter in a Backup Datastore defines which Hosts are responsible for transferring VM backups from the hypervisor to the Backup Datastore.

{{< alert title="Note" type="info" >}}
This feature is only supported for **shared system datastores** (currently only with **Ceph**).{{< /alert >}}

All Hosts listed in `BRIDGE_LIST` must meet the following requirements:

- Must have **network access** to the Backup Datastore.
- Must be able to establish **passwordless SSH connections** to the **OpenNebula Front-end**.
- For the SFTP backend, must be able to establish **passwordless SSH connections** to the **Backup Server**.

During the backup process:

- OpenNebula automatically selects one of the hosts from the `BRIDGE_LIST`.
- This host is used to:
  - Retrieve the snapshot created by the hypervisor.
  - Export it to the Backup Datastore.
- The name of the selected Host is recorded in the VM's backup configuration, under the `LAST_BRIDGE` field.

## Reference: Restic Datastore Attributes

### Common Attributes

| Attribute            | Description                                                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------|
| `RESTIC_BACKEND`     | Restic backend to use. Allowed values: `SFTP`, `S3`. Defaults to `SFTP` when omitted.                       |
| `RESTIC_PASSWORD`    | Password to access the restic repository.                                                                   |
| `RESTIC_IONICE`      | Run backups under a given ionice priority (best-effort, class 2). Value: 0 (high) - 7 (low).                |
| `RESTIC_NICE`        | Run backups under a given nice. Value: -19 (high) to 19 (low).                                              |
| `RESTIC_MAX_RIOPS`   | Run backups in a systemd slice, limiting the max number of read IOPS.                                       |
| `RESTIC_MAX_WIOPS`   | Run backups in a systemd slice, limiting the max number of write IOPS.                                      |
| `RESTIC_CPU_QUOTA`   | Run backups in a systemd slice with a given CPU quota (percentage). Use > 100 for using several CPUs.       |
| `RESTIC_BWLIMIT`     | Limit restic upload/download bandwidth.                                                                     |
| `RESTIC_COMPRESSION` | Compression (three modes: off, auto, max), default is `auto` (average compression without too much CPU use). |
| `RESTIC_CONNECTIONS` | Number of concurrent connections (default 5). For high-latency backends this number can be increased.       |
| `RESTIC_MAXPROC`     | Sets `GOMAXPROCS` for restic to limit the OS threads that execute user-level Go code simultaneously.        |
| `RESTIC_SPARSIFY`    | Runs `virt-sparsify` on flatten backups to reduce backup size. It requires the `libguestfs` package.        |
| `BRIDGE_LIST`        | List of hosts responsible for transferring VM backups from the hypervisor to the Backup Datastore.          |

### SFTP Backend Attributes

| Attribute            | Description                                                     |
|----------------------|-----------------------------------------------------------------|
| `RESTIC_SFTP_USER`   | User to connect to the backup server (default `oneadmin`).      |
| `RESTIC_SFTP_SERVER` | IP address of the backup server. Mandatory for the SFTP backend. |

### S3 Backend Attributes

| Attribute                     | Description                                                                                                 |
|-------------------------------|-------------------------------------------------------------------------------------------------------------|
| `RESTIC_S3_ACCESS_KEY_ID`     | S3 access key ID. Mandatory for the S3 backend.                                                              |
| `RESTIC_S3_SECRET_ACCESS_KEY` | S3 secret access key. Mandatory for the S3 backend. Stored encrypted in OpenNebula.                          |
| `RESTIC_S3_BUCKET`            | S3 bucket name only, without endpoint URL. Mandatory for the S3 backend.                                     |
| `RESTIC_S3_REGION`            | S3 region. Optional, defaults to `us-east-1` when omitted.                                                  |
| `RESTIC_S3_ENDPOINT`          | S3 endpoint. Defaults to `s3.amazonaws.com` for AWS S3. Mandatory for non-AWS S3-compatible backends. Can include a scheme, e.g. `http://s3-storage:8080`. |
| `RESTIC_S3_FORCE_PATH_STYLE`  | Use `YES` to force path-style S3 access. Needed for many non-AWS S3-compatible backends.                    |
| `RESTIC_S3_CACERT`            | Path to a custom CA certificate file available on the KVM Hosts where restic commands run.                                           |
| `RESTIC_S3_INSECURE_TLS`      | Use `YES` to disable TLS certificate verification. Intended for lab or debug environments only.             |
| `TOTAL_MB`                    | Datastore capacity in MB for S3 monitoring. Defaults to `1048576` MB (`1024G`).                             |
