---
title: "Upgrading Single Front-end"
date: "2025-02-17"
description:
categories:
pageintoc: "259"
tags:
weight: "3"
---

<a id="upgrade-single"></a>

<!--# Upgrading Single Front-end Deployments -->
{{< alert title="Important" type="info" >}}
If you haven’t done so, please enable the [OpenNebula and needed 3rd party repositories]({{% relref "frontend_install#setup-opennebula-repos" %}}) before attempting the upgrade process.{{< /alert >}}

## Upgrading from 6.x and higher

### Step 1. Check Virtual Machine Status

Before proceeding, make sure you don’t have any VMs in a transient state (prolog, migrate, epilog, save). Wait until these VMs get to a final state (running, suspended, stopped, done). (For more information on the life cycle of Virtual Machines, please see [Virtual Machine Instances]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances" %}}).)

### Step 2. Set All Hosts to Disable Mode

Set all Hosts to disable mode to stop all monitoring processes.

```bash
onehost disable <host_id>
```

### Step 3. Stop OpenNebula

Stop OpenNebula and any other related services you may have running: OneFlow, OneGate and FireEdge. To stop OpenNebula, it's preferable to use the system tools, like `systemctl` or `service` running as user `root`. For example (note that `opennebula-scheduler` is no longer used in 7.0 or newer):
```bash
systemctl stop opennebula opennebula-flow.service opennebula-gate.service opennebula-hem.service opennebula-scheduler.service opennebula-fireedge.service
```

Then make sure every OpenNebula process is stopped. For example:
```bash
systemctl is-active opennebula opennebula-flow.service opennebula-gate.service opennebula-hem.service opennebula-scheduler.service opennebula-fireedge.service
```

{{< alert title="Important" type="info" >}}
If you are running FireEdge service behind Apache/Nginx, please also stop the Apache/Nginx service.{{< /alert >}}

### Step 4. Back up OpenNebula Configuration

Back up the configuration files located in `/etc/one` and `/var/lib/one/remotes/etc`. You don’t need to do a manual backup of your database; the `onedb` command will perform one automatically.

```bash
cp -ra /etc/one /etc/one.$(date +'%Y-%m-%d')
```
```bash
cp -ra /var/lib/one/remotes/etc /var/lib/one/remotes/etc.$(date +'%Y-%m-%d')
```
```bash
onedb backup
```

### Step 5. Upgrade OpenNebula Packages Repository

In order to be able to retrieve the packages for the latest version, you need to update the OpenNebula packages repository. The instructions for doing this are detailed [here]({{% relref "opennebula_repository_configuration#repositories" %}}).

### Step 6. Upgrade to the New Version

{{< alert title="Important" type="info" >}}
When prompted by the package manager, select the option to keep your current (modified) configuration files. The upgrade of these files will be handled in the next step.{{< /alert >}}

Ubuntu/Debian

```bash
apt-get update
apt-get install --only-upgrade opennebula opennebula-gate opennebula-flow opennebula-fireedge opennebula-migration python3-pyone
```

RHEL

```bash
yum upgrade opennebula opennebula-gate opennebula-flow opennebula-fireedge opennebula-migration python3-pyone
```

<!-- TODO: Add SLES/openSUSE upgrade instructions (zypper) once there is a previous SUSE release to upgrade from (SUSE support was introduced in 7.2). -->

### Step 7. Update Configuration Files

In High Availability (HA) setups, you must replace the default value `auto` of the `MONITOR_ADDRESS` parameter in `/etc/one/monitord.conf` with the virtual IP address used in the `RAFT_LEADER_HOOK` and `RAFT_FOLLOWER_HOOK` settings in `/etc/one/oned.conf`.

{{< alert title="Important" type="danger" >}}
**Note**: This step **only applies to installations prior to version 7.0** that have defined custom default label groups in `/etc/one/sunstone-views.yaml` and wish to preserve them.

Before proceeding, back up the `/etc/one/sunstone-views.yaml` file. After completing the `onecfg` upgrade step, restore the file to its original location. Once the upgrade is fully finalized and the custom labels are confirmed to be migrated, the file may be safely removed. {{< /alert >}}

Before upgrading OpenNebula, ensure that the configuration state is clean, with no pending migrations from previous or outdated configurations. To verify this, run `onecfg status`. A clean state should produce output similar to:

```default
onecfg status
--- Versions ------------------------------
OpenNebula:  7.4.0
Config:      6.10.0

--- Backup to Process ---------------------
Snapshot:    /var/lib/one/backups/config/2025-06-27_11:05:47-v6.10.0
(will be used as one-shot source for next update)

--- Available Configuration Updates -------
New config:  7.4.0
- from 6.10.0 to 6.10.2 (YAML, Ruby)
- from 6.10.2 to 7.4.0 (YAML, Ruby)
```

{{< alert title="Note" type="info" >}}
After running `onecfg status`, you might encounter one of the following messages:

* `Unknown Configuration Version Error`: No action is required. The configuration version will be initialized automatically during the OpenNebula upgrade, based on the existing version.

* `Configuration Metadata Outdated Error`: This indicates that a configuration upgrade was skipped during a previous OpenNebula upgrade. To resolve this, reinitialize the configuration state with `onecfg init --force`. This will discard any unprocessed configuration upgrades.{{</alert>}}

After confirming the configuration state, in most cases you can proceed with the following command, which uses OpenNebula's internal version tracking to apply the appropriate configuration updates:

```default
onecfg upgrade
ANY   : Found backed up configuration to process!
ANY   : Snapshot to update from '/var/lib/one/backups/config/2025-06-27_11:05:47-v6.10.0'
ANY   : Backup stored in '/var/lib/one/backups/config/2025-06-27_11:39:36_30392'
ANY   : Configuration updated to 7.4.0
```

If you get conflicts when running the `onecfg` upgrade, refer to the [onecfg upgrade basic usage documentation]({{% relref "../configuration_management_ee/usage#cfg-usage" %}}) on how to upgrade and troubleshoot the configurations, in particular the [onecfg upgrade doc]({{% relref "../configuration_management_ee/usage#cfg-upgrade" %}}) and the [Troubleshooting section]({{% relref "../configuration_management_ee/conflicts#cfg-conflicts" %}}).

Finally, check the configuration state via `onecfg status`. There should be no errors and no new updates available. Your configuration should be up to date for the currently installed OpenNebula version. For example:

```default
--- Versions ------------------------------
OpenNebula:  7.4.0
Config:      7.4.0

--- Available Configuration Updates -------
No updates available.
```

### Step 8. Upgrade the Database Version

{{< alert title="Important" type="danger" >}}
If you have backed up `/etc/one/sunstone-views.yaml` restore the file to `/etc/one` now before executing the following command.{{< /alert >}}

Simply run the `onedb upgrade -v` command. The connection parameters are automatically retrieved from `/etc/one/oned.conf`. Example:

```shell
onedb upgrade -v
Version read:
Shared tables 6.10.0 : OpenNebula 6.10.0 (5d6b8571) daemon bootstrap
Local tables  6.10.0 : OpenNebula 6.10.0 (5d6b8571) daemon bootstrap

Sqlite database backup stored in /var/lib/one/one.db_2025-6-27_11:45:51.bck
Use 'onedb restore' to restore the DB.

>>> Running migrators for shared tables
  > Running migrator /usr/lib/one/ruby/onedb/shared/6.10.0_to_7.4.0.rb
  > Done in 0.00s

Database migrated from 6.10.0 to 7.4.0 (OpenNebula 7.4.0) by onedb command.

>>> Running migrators for local tables
  > Running migrator /usr/lib/one/ruby/onedb/local/6.10.0_to_7.4.0.rb
  > Done in 0.08s

Database migrated from 6.10.0 to 7.4.0 (OpenNebula 7.4.0) by onedb command.

Total time: 0.12s
```

### Step 9. Check DB Consistency

First, move the {{< version >}} backup file created by the upgrade command to a safe place. If you face any issues the `onedb` command can restore this backup, but it won’t downgrade databases to previous versions. Then, execute the `onedb fsck` command:

```default
$ onedb fsck
MySQL dump stored in /var/lib/one/mysql_localhost_opennebula.sql
Use 'onedb restore' or restore the DB using the mysql command:
mysql -u user -h server -P port db_name < backup_file

Total errors found: 0
```

### Step 10. Start OpenNebula

{{< alert title="Important" type="danger" >}}
For versions prior to 7.0, now you can safely delete `/etc/one/sunstone-views.yaml`.{{< /alert >}}

Start OpenNebula and any other related services: OneFlow, OneGate and FireEdge. First reload the new systemd unit files:

```bash
systemctl daemon-reload
```

Then restart the services:

```bash
systemctl start opennebula opennebula-flow.service opennebula-gate.service opennebula-hem.service opennebula-fireedge.service
```

{{< alert title="Important" type="info" >}}
If you are running FireEdge service behind Apache/Nginx, please start also the Apache/Nginx service.{{< /alert >}}

### Step 11. Restore Custom Probes

If you have any custom monitoring probes, follow [these instructions]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-im#devel-im" %}}) to update them to the new monitoring system

### Step 12. Update the Hypervisors

{{< alert title="Warning" type="warning" >}}
The hypervisor node operating system must meet the minimum version required according to the [KVM]({{% relref "../../release_information/release_notes/platform_notes.md#kvm-nodes" %}}) or [LXC]({{% relref "../../release_information/release_notes/platform_notes#lxc-nodes" %}}) platform notes. Running a Front-end node with a newer OpenNebula version controlling hypervisor nodes running in old unsupported platforms, like CentOS 7, can result in a myriad of dependency problems. A very common issue is the old ruby version shipped in CentOS 7 not being able to run the newer driver code.{{< /alert >}}

Log in to your hypervisor Hosts and update the `opennebula-node` packages. **NOTE**: you may need to upgrade the software repository as described [above](#step-5-upgrade-opennebula-packages-repository).

Ubuntu/Debian

```bash
apt-get update
apt-get install --only-upgrade opennebula-node-<hypervisor>
```

RHEL

```bash
yum upgrade opennebula-node-<hypervisor>
```

<!-- TODO: Add SLES/openSUSE node upgrade instructions (zypper) once there is a previous SUSE release to upgrade from (SUSE support was introduced in 7.2). -->

{{< alert title="Note" type="info" >}}
Note that the `<hypervisor>` tag should be replaced by the name of the corresponding hypervisor (i.e., `kvm` or `lxc`).{{< /alert >}}

{{< alert title="Important" type="info" >}}
For KVM hypervisor it’s also necessary to restart the libvirt service{{< /alert >}}

Then update the virtualization, storage, and networking drivers. As the `oneadmin` user, execute:

```bash
onehost sync
```

### Step 13. Enable Hosts

Enable all Hosts, disabled in step 2:

```bash
onehost enable <host_id>
```

If upgrading from a version earlier than 6.0, please see [Upgrading from Previous Versions]({{% relref "upgrade_from_previous_versions" %}}).

### Testing

OpenNebula will continue the monitoring and management of your previous Hosts and VMs.

As a measure of caution, look for any error messages in `oned.log`, and check that all drivers are loaded successfully. You may also try some **show** subcommand for some resources to check everything is working (e.g., `onehost show` or `onevm show`).

### Restoring the Previous Version

If for any reason you need to restore your previous OpenNebula, simply uninstall OpenNebula {{< version >}} and reinstall your previous version. After that, update the drivers if needed, as outlined in Step 12.
