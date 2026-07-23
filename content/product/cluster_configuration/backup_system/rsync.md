---
title: "Backup Datastore: Rsync"
linkTitle: "Rsync"
date: "2025-02-17"
description:
categories:
pageintoc: "79"
tags:
weight: "3"
---

<a id="vm-backups-rsync"></a>

<!--# Backup Datastore: Rsync -->

RSync is an open source file transfer utility that is included with most distributions of Linux. This backup utility is provided with the Community Edition (CE) of OpenNebula and supports both full and incremental backup methods.

## Configuring the backup server

First, a server should be configured to receive and store these backup files.  The rsync backup server can be any server which is accessible from the oneadmin user on the Hosts.  This user on the nodes should have their key placed on the rsync server under the user specified in the rsync Backup Datastore configuration ( `~/.ssh/authorized_keys` by default ).

Perform the following steps:

* Create a user on the rsync server with permissions to access the datastore directory (default: /var/lib/one/datastores/<ds_id>)
* Copy the public SSH keys from each node to the RSYNC_USER’s ~/.ssh/authorized_keys file on the RSYNC_HOST.
* Verify that the Front-end and ALL Hosts can SSH to the RSYNC_HOST as the RSYNC_USER without a password.
* Create the folder /var/lib/one/datastores on the rsync server and change ownership to the RSYNC_USER.
* (Optional) Mount a storage volume to /var/lib/one/datastores or to the Datastore ID directory under that.
* Finally make sure **rsync** and **qemu-img** commands are installed in the backup server.

## Creating the OpenNebula Datastore

Once the rsync server is prepared to receive backup files from all of the nodes, we just need to create a datastore detailing the user and Host:

```shell
cat ds_rsync.txt
 NAME   = "rsync Backups"
 TYPE   = "BACKUP_DS"
 
 DS_MAD = "rsync"
 TM_MAD = "-"
 
 RSYNC_USER = "oneadmin"
 RSYNC_HOST = "192.168.100.1"
```

*Note*: Transferring the backups over a separate network can improve performance and availability of the rest of the cloud.

With that file in place we just need to create the datastore from that:

```shell
onedatastore create ds_rsync.txt
 ID: 100
```

After applying this configuration and verifying that all of the Hosts can access RSYNC_HOST using the RSYNC_USER, you should be able to start utilizing the rsync backup system.  You can also create the DS through Sunstone like any other datastore:

{{< image
  pathDark="/images/storage/dark/backup_rsync_create.png"
  path="/images/storage/light/backup_rsync_create.png"
  alt="Create Rsync Backup" align="center" width="90%" mb="20px"
>}}

## Other Configurations

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
- Must be able to establish **passwordless SSH connections** to:
  - The **OpenNebula Frontend**
  - The **Backup Server**

During the backup process:

- OpenNebula automatically selects one of the hosts from the `BRIDGE_LIST`.
- This host is used to:
  - Retrieve the snapshot created by the hypervisor.
  - Export it to the Backup Datastore.
- The name of the selected Host is recorded in the VM's backup configuration, under the `LAST_BRIDGE` field.


## Reference: rsync Datastore Attributes

| Attribute         | Description                                                                                          |
|-------------------|------------------------------------------------------------------------------------------------------|
| `RSYNC_USER`      | User to connect to the rsync server (Required)                                                       |
| `RSYNC_HOST`      | IP address of the backup server (Required)                                                           |
| `RSYNC_ARGS`      | Command line arguments for rsync command (Default: -az)                                              |
| `RSYNC_TMP_DIR`   | Temporary Directory used for rebasing incremental images (Default: /var/tmp)                         |
| `RSYNC_IONICE`    | Run backups under a given ionice priority (best-effort, class 2). Value: 0 (high) - 7 (low)          |
| `RSYNC_NICE`      | Run backups under a given nice. Value: -19 (high) to 19 (low)                                        |
| `RSYNC_MAX_RIOPS` | Run backups in a systemd slice, limiting the max number of read iops                                 |
| `RSYNC_MAX_WIOPS` | Run backups in a systemd slice, limiting the max number of write iops                                |
| `RSYNC_CPU_QUOTA` | Run backups in a systemd slice with a given cpu quota (percentage). Use > 100 for using several CPUs |
| `RSYNC_SPARSIFY`  | Runs `virt-sparsify` on flatten backups to reduce backup size. It requires `libguestfs` package.     |
| `BRIDGE_LIST`     | List of hosts responsible for transferring VM backups from the hypervisor to the Backup Datastore    |
