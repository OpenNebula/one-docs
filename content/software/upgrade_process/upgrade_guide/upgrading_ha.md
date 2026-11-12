---
title: "Upgrading High Availability Clusters"
date: "2025-02-17"
description:
categories:
pageintoc: "260"
tags:
weight: "4"
---

<a id="upgrade-ha"></a>

<!--# Upgrading High Availability Clusters -->

## Step 1. Check Virtual Machine Status

Before proceeding, make sure you don’t have any VMs in a transient state (prolog, migrate, epilog, save). Wait until these VMs get to a final state (running, suspended, stopped, done). For more information on the life cycle of Virtual Machines, see [Virtual Machine Instances]({{% relref "../../../product/virtual_machines_operation/virtual_machines/vm_instances" %}}).

## Step 2. Set All Hosts to Disable Mode

Set all Hosts to disable mode to stop all monitoring processes.

```default
$ onehost disable <host_id>
```

If you are upgrading from version 6.2+ use `onezone disable <zone_id>` to make sure that no operations changing OpenNebula's state are executed.

## Step 3. Stop the HA Cluster

You need to stop all the nodes in the cluster to upgrade them at the same time. Start with the followers and leave the leader until the end.

Stop OpenNebula and any other related services you may have running: OneFlow, OneGate, FireEdge, OneForm, and OneKS. It’s preferable to use the system tools, like `systemctl` or `service` as `root` in order to stop the services.

{{< alert title="Important" type="info" >}}
If you are running FireEdge service behind Apache/Nginx, please also stop the Apache/Nginx service.{{< /alert >}} 

{{< alert title="Warning" type="warning" >}}
Make sure that every OpenNebula process is stopped. The output of `systemctl list-units | grep opennebula` should be empty.{{< /alert >}} 

## Step 4. Upgrade the Leader

When upgrading from 7.4.0 or 7.4.1 to 7.4.2, back up the configuration and database, then apply the [Front-end package and configuration updates]({{% relref "upgrading_single#maintenance-package-configuration" %}}). No database schema upgrade is needed. Keep the services stopped until Step 7 below.

For upgrades from earlier versions, follow steps 4 to 9 of [Upgrading Single Front-end]({{% relref "upgrading_single#upgrade-from-older-releases" %}}).

Then, create a database backup to replicate the upgraded state to the followers:

```default
$ onedb backup
MySQL dump stored in /var/lib/one/mysql_localhost_opennebula_2019-9-27_11:52:47.sql
Use 'onedb restore' or restore the DB using the mysql command:
mysql -u user -h server -P port db_name < backup_file
```

## Step 5. Upgrade OpenNebula in the Followers

On every follower, back up the configuration and database, then apply the same updates as on the leader. For upgrades from 7.4.0 or 7.4.1 to 7.4.2, use the [Front-end package and configuration updates]({{% relref "upgrading_single#maintenance-package-configuration" %}}); for earlier versions, follow steps 4 to 9 of [Upgrading Single Front-end]({{% relref "upgrading_single#upgrade-from-older-releases" %}}). Keep the services stopped until Step 7 below.

## Step 6. Replicate Database and Configuration

Copy the database backup of the leader to each follower and restore it:

```default
$ scp /var/lib/one/mysql_localhost_opennebula_2019-9-27_11:52:47.sql <follower_ip>:/tmp
$ onedb restore -f /tmp/mysql_localhost_opennebula_2019-9-27_11:52:47.sql
MySQL DB opennebula at localhost restored.
```

Synchronize the configuration files to the followers:

{{< alert title="Note" type="info" >}}
Before copying, gather the `SERVER_ID` from your `/etc/one/oned.conf files` on each follower, then replace those values afterwards.{{< /alert >}} 

```default
$ rsync -r /etc/one root@<follower_ip>:/etc
$ rsync -r /var/lib/one/remotes/etc root@<follower_ip>:/var/lib/one/remotes
```

On each of the followers, ensure these folders are owned by the `oneadmin` user:

```default
$ chown -R oneadmin:oneadmin /etc/one
$ chown -R oneadmin:oneadmin /var/lib/one/remotes/etc
```

## Step 7. Start OpenNebula in the Leader and Followers

Start OpenNebula and any other related services: OneFlow, OneGate, FireEdge, OneForm, and OneKS. It’s preferable to use the system tools, like `systemctl` or `service` as `root` in order to start the services.

{{< alert title="Important" type="info" >}}
If you are running FireEdge service behind Apache/Nginx, please also start the Apache/Nginx service.{{< /alert >}} 

## Step 8. Check Cluster Health

At this point the `onezone show` command should display all the followers active and in sync with the leader.

If you disabled the zone in Step 2, re-enable it through that zone’s endpoint before enabling the Hosts:

```bash
onezone enable <zone_id>
```

After upgrading to 7.4.2 and re-enabling the zone, complete the [feature configuration updates]({{% relref "upgrading_single#feature-updates-742" %}}). Apply service configuration changes on each Front-end where the corresponding services are installed.

## Step 9. Update the Hypervisors

For upgrades from 7.4.0 or 7.4.1 to 7.4.2, [update the hypervisor packages and synchronize the drivers]({{% relref "upgrading_single#step-12-update-the-hypervisors" %}}), then enable the Hosts disabled in Step 2.

For upgrades from earlier versions, upgrade the hypervisors and enable them as described in Steps 11-13 in the [Upgrading Single Front-end Deployments]({{% relref "upgrading_single#step-11-restore-custom-probes" %}}) guide.
