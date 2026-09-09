---
title: "Known Issues"
date: "2025-10-06"
description:
categories:
pageintoc: "248"
tags:
weight: "6"
---

<a id="known-issues"></a>

<!--# Known Issues -->

A complete list of [known issues for OpenNebula is maintained here](https://github.com/OpenNebula/one/issues?q=is%3Aopen%20is%3Aissue%20type%3ABug%20label%3A%22Status%3A%20Accepted%22%20milestone%3A%22Release%207.4%22).

This page will be updated with relevant information about bugs affecting OpenNebula, as well as possible workarounds until a patch is officially published.

## Upgrade Overwrites the Host Fencing Script

Upgrading the OpenNebula packages [overwrites a customized](https://github.com/OpenNebula/one/issues/7996) `/var/lib/one/remotes/hooks/ft/fence_host.sh` with the stock template. If the Host error hook is configured with fencing enabled, fencing (and thus the hook) will fail after the upgrade until the file is restored.

The pre-upgrade file is preserved in the configuration backup taken automatically during the package upgrade, and can be restored from there:

```default
cp /var/lib/one/backups/config/<timestamp>-v<previous version>/var/lib/one/remotes/hooks/ft/fence_host.sh \
   /var/lib/one/remotes/hooks/ft/fence_host.sh
```

## Live Storage Migration with NVRAM VMs Failure

During Live Storage Migration the virtual machine goes through a series of commands in virsh: dumpxml, define, undefine. If the virtual machine has NVRAM there is a [silent uncaught failure](https://github.com/OpenNebula/one/issues/7770):

```default
error: Requested operation is not valid: cannot undefine domain with nvram
```

The migrate pattern should be aware of NVRAM existence and properly use --keep-nvram during the undefine operation. Fix will be made availabe in OpenNebula 7.4.1.

## Frontend HA

- [ARP tables are not updated automatically](https://github.com/OpenNebula/one/issues/7920) when a leader is elected in Red Hat Enterprise Linux OS variants.

## Veeam Backups

Worker creation and restores [will fail](https://github.com/OpenNebula/one/issues/7949) if the VM with ID 0 doesn't exist in the database.

It can be fixed by changing the line ~145 in the `/usr/lib/one/ovirtapi-server/controllers/disk_controller.rb` file (located in the oVirtAPI backup server). Then restart the apache2/httpd service.

```
vm_id = disk_hash['IMAGE']['VM_ID'].to_i
if backup_mode == 'incremental' && vm_id > 0    # <-- Add this vm_id check
    vm = VmController.get_one_vms(client, :vm_id => vm_id)
    vm_hash = vm.to_hash
    backup_ids = vm_hash.dig('VM', 'BACKUPS', 'BACKUP_IDS', 'ID')
```

### Missing `interactive` Datastore Configuration

The required `interactive` [datastore driver configuration](https://github.com/OpenNebula/one/issues/8074) in `/etc/one/oned.conf`. In this case, Veeam worker deployment can fail with:

```default
Datastore driver 'interactive' not available
```

Ensure that the `interactive` driver is included in the `DATASTORE_MAD` driver list under the `-d` option:

```default
DATASTORE_MAD = [
    EXECUTABLE = "one_datastore",
    ARGUMENTS  = "-t 15 -d dummy,fs,lvm,ceph,dev,iscsi_libvirt,restic,rsync,netapp,purefa,virtiofs,interactive -s dummy,lvm,shared,ssh,local,ceph,fs_lvm,fs_lvm_ssh,qcow2,netapp,purefa"
]
```

The corresponding `DS_MAD_CONF` entry must also be present:

```default
DS_MAD_CONF = [
    NAME = "interactive",
    REQUIRED_ATTRS = "",
    PERSISTENT_ONLY = "NO",
    DATASTORE_CAPACITY_CHECK = "NO"
]
```

After modifying `/etc/one/oned.conf`, restart OpenNebula:

```shell
systemctl restart opennebula
```
