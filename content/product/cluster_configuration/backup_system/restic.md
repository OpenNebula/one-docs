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

[Restic](https://restic.net/) is an open source (BSD 2-Clause License) backup tool designed for speed, security, and efficiency. The current implementation of the driver uses the SFTP storage type. Restic offers interesting features to store backups, like deduplication (only transferring image blobs not already present in the repository) or compression (enabled by default).

In both the Enterprise and Community editions of OpenNebula, the correct version of restic is included as a dependency. In this guide we will use the following terminology (introduced by restic):

- *Repository*: This is the storage volume where the disk images backups will be stored. Restic creates a specific interval structure to store the backups efficiently. The restic driver accesses the repository through the sftp. protocol. OpenNebula will create a separate restic repository for each VM or backup job.
- *Snapshot*: It represents a backup and it is referenced by a unique hash (e.g., `eda52f34`). Each snapshot stores a VM backup and includes the backed up disks and the metadata description of the VM at the time you make the backup.
- *Backup Server*: A Host that will store the VM backups and the restic repositories.

## Step 1. [Backup Server] Set up the backup server

The first thing you need to do is set up a server to hold the restic repository. Typically the server will have a dedicated storage medium dedicated to store the backups (e.g., iSCSI volume). Also, the Hosts and Front-end need to reach the server IP.

To set up the server perform the following steps:

- Create a user account with username `oneadmin`. This account will be used to connect to the server.
- Copy the SSH public key of existing `oneadmin` from the OpenNebula Front-end to this new `oneadmin` account.
- Check that `oneadmin` can SSH access the server **without being prompt for a password** from the Front-end and Hosts.
- Create the following folder in the backup server `/var/lib/one/datastores`, change the ownership to `oneadmin`.
- Mount the storage volume in `/var/lib/one/datastores`.
- Finally make sure **rsync** and **qemu-img** commands are installed in the backup server.

The following example showcases this setup using a dedicated 1.5T volume for backups:

```default
$ id oneadmin
uid=9869(oneadmin) gid=9869(oneadmin) groups=9869(oneadmin)
```

```default
$ lsblk
sdb                         8:16   0  1.5T  0 disk
└─sdb1                      8:17   0  1.5T  0 part
  └─vgBackup-lvBackup     253:0    0  1.5T  0 lvm  /var/lib/one/datastores
```

```default
$ ls -ld /var/lib/one/datastores/
drwxrwxr-x 2 oneadmin oneadmin 4096 Sep  3 12:04 /var/lib/one/datastores/
```

## Step 2. [Front-end] Create a Restic Datastore

Now that we have the backup server prepared, let’s create an OpenNebula Backup Datastore. We just need to pick a password to access our repository and create a datastore template:

```default
$ cat ds_restic.txt
NAME   = "RBackups"
TYPE   = "BACKUP_DS"

DS_MAD = "restic"
TM_MAD = "-"

RESTIC_PASSWORD    = "opennebula"
RESTIC_SFTP_SERVER = "192.168.1.8"
```

*Note*: The `RESTIC_SFTP_SERVER` is the IP address of the backup server, it needs to be reachable from the Front-end and Hosts.

```default
$ onedatastore create ds_restic.txt
ID: 100
```

You can also create the DS through Sunstone like any other datastore:

![restic_create](/images/backup_restic_create.png)

After some time, the datastore should be monitored:

```default
$ onedatastore list
ID  NAME                                         SIZE AVA CLUSTERS IMAGES TYPE DS      TM      STAT
100 RBackups                                     1.5T 91% 0             0 bck  restic  -       on
  2 files                                       19.8G 84% 0             0 fil  fs      local   on
  1 default                                     19.8G 84% 0             1 img  fs      local   on
  0 system                                          - -   0             0 sys  -       local   on
```

That’s it, we are all set to make VM backups!

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

> * Lowering the priority of the associated processes. Backup commands are run under a given ionice priority (best-effort, class 2 scheduler); and a given nice.
> * Confining the associated processes in a cgroup. OpenNebula will create a systemd slice for each Backup Datastore so the backup commands run with a limited number or read/write IOPS and CPU Quota.

Note that for the latter, you need to delegate the `cpu` and `io` cgroup controllers to the `oneadmin` user. This way OpenNebula can set `CPUQuota`, `IOReadIOPSMax` and `IOWriteIOPSMax`.

To delegate the controllers you need to add the following file for `oneadmin` account (id 9869) in **all the Hosts** (note that you’d probably need to create the user service folder):

```default
$ cat /etc/systemd/system/user@9869.service.d/delegate.conf
[Service]
Delegate=cpu cpuset io
```

After that, reboot the hypervisor and double check that the setting is correct (you need to login as `oneadmin`):

```default
$ cat /sys/fs/cgroup/user.slice/user-9869.slice/cgroup.controllers
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
- Must be able to establish **passwordless SSH connections** to:
  - The **OpenNebula Frontend**
  - The **Backup Server**

During the backup process:

- OpenNebula automatically selects one of the hosts from the `BRIDGE_LIST`.
- This host is used to:
  - Retrieve the snapshot created by the hypervisor.
  - Export it to the Backup Datastore.
- The name of the selected Host is recorded in the VM's backup configuration, under the `LAST_BRIDGE` field.

## Reference: Restic Datastore Attributes

| Attribute            | Description                                                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------|
| `RESTIC_SFTP_USER`   | User to connect to the backup server (default `oneadmin`)                                                   |
| `RESTIC_SFTP_SERVER` | IP address of the backup server                                                                             |
| `RESTIC_PASSWORD`    | Password to access the restic repository                                                                    |
| `RESTIC_IONICE`      | Run backups under a given ionice priority (best-effort, class 2). Value: 0 (high) - 7 (low)                 |
| `RESTIC_NICE`        | Run backups under a given nice. Value: -19 (high) to 19 (low)                                               |
| `RESTIC_MAX_RIOPS`   | Run backups in a systemd slice, limiting the max number of read iops                                        |
| `RESTIC_MAX_WIOPS`   | Run backups in a systemd slice, limiting the max number of write iops                                       |
| `RESTIC_CPU_QUOTA`   | Run backups in a systemd slice with a given cpu quota (percentage). Use > 100 for using several CPUs        |
| `RESTIC_BWLIMIT`     | Limit restic upload/download bandwidth                                                                      |
| `RESTIC_COMPRESSION` | Compression (three modes:off, auto, max), default is `auto` (average compression without to much CPU usage) |
| `RESTIC_CONNECTIONS` | Number of concurrent connections (default 5). For high-latency backends this number can be increased.       |
| `RESTIC_MAXPROC`     | Sets `GOMAXPROCS` for restic to limit the OS threads that execute user-level Go code simultaneously.        |
| `RESTIC_SPARSIFY`    | Runs `virt-sparsify` on flatten backups to reduce backup size. It requires `libguestfs` package.            |
| `BRIDGE_LIST`        | List of hosts responsible for transferring VM backups from the hypervisor to the Backup Datastore           |
