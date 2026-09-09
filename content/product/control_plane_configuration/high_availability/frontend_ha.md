---
title: "Front-end HA"
linkTitle: "Front-end"
date: "2025-02-17"
description:
categories:
pageintoc: "33"
tags:
weight: "2"
---

<a id="frontend-ha-setup"></a>

<a id="oneha"></a>

<!--# OpenNebula Front-end HA -->

OpenNebula provides a built-in mechanism to ensure high availability (HA) of the core Front-end daemon, `oned`. Services need to be deployed and configured across several hosts, and a distributed consensus protocol enforced to provide fault-tolerance and state consistency across them. Such deployment is resilient to the failure of at least a single host, depending on the total number of hosts.

In this section, you learn the basics of how to bootstrap a distributed highly available OpenNebula Front-end.

{{< alert title="Warning" type="warning" >}}
If you are interested in fail-over protection against hardware and operating system outages within your virtualized IT environment, check the [Virtual Machines High Availability Guide]({{% relref "vm_ha#ftguide" %}}).{{< /alert >}} 

## Raft Overview

This section covers some internals on how OpenNebula implements Raft. You do not need to know these details to effectively operate OpenNebula on HA. These details are provided for those who wish to learn about them to fine-tune their deployments.

A consensus algorithm is built around two concepts:

- **System State** - OpenNebula data stored in the database tables (users, ACLs, or the VMs in the system).
- **Log** - sequence of SQL statements that are *consistently* applied to the OpenNebula DB in all servers to evolve the system state.

To preserve a consistent view of the system across servers, modifications to the system state are performed through a special node, the *leader*. The servers in the OpenNebula cluster elect a single node to be the *leader*. The *leader* periodically sends heartbeats to the other servers, the *followers*, to keep its leadership. If a *leader* fails to send the heartbeat, *followers* are promoted to *candidates* and start a new election.

Whenever the system is modified (e.g. a new VM is added to the system), the *leader* updates the log and replicates the entry in a majority of *followers* before actually writing it to the database. The latency of DB operations is thus increased, but the system state is safely replicated and the cluster can continue its operation in case of node failure.

In OpenNebula, read-only operations can be performed through any oned server in the cluster and write operations issued to the follower nodes are forwarded to the leader node. This means that reads can be arbitrarily stale but generally within the round-trip time of the network.

## Requirements and Architecture

The recommended deployment size is either three or five servers, which provides a fault-tolerance for one or two server failures, respectively. You can add, replace or remove servers once the cluster is up and running.

Every HA cluster requires:

* An odd number of servers (three is recommended).
* (Recommended) identical server capacities.
* The same software configuration of the servers. (The sole difference would be the `SERVER_ID` field in `/etc/one/oned.conf`.)
* A working database connection of the same type. MySQL is recommended.
* All the servers must share the credentials.
* Floating IP which will be assigned to the *leader*.
* A shared filesystem.

The servers should be configured in the following way:

* Shared datastores must be mounted on all the nodes.

## Bootstrapping the HA cluster

This section shows examples of all the steps required to deploy the HA Cluster.

{{< alert title="Warning" type="warning" >}}
To maintain a healthy cluster during the procedure of adding servers to the clusters, make sure you add **only** one server at a time.{{< /alert >}} 

{{< alert title="Important" type="info" >}}
In the following, each configuration step starts with (initial) **Leader** or (future) **Follower** to indicate the server where the step must be performed.{{< /alert >}} 

### Configuration of the initial leader

We start with the first server, to perform the initial system bootstrapping.

* **Leader**: Start OpenNebula
* **Leader**: Add the server itself to the zone:

```default
$ onezone list
C    ID NAME                      ENDPOINT
*     0 OpenNebula                http://localhost:2633/RPC2

# We are working on Zone 0

$ onezone server-add 0 --name server-0 --rpc http://192.168.150.1:2633/RPC2

# It's now available in the zone:

$ onezone show 0
ZONE 0 INFORMATION
ID                : 0
NAME              : OpenNebula
STATE             : ENABLED


ZONE SERVERS
ID NAME            ENDPOINT
 0 server-0        http://192.168.150.1:2633/RPC2

HA & FEDERATION SYNC STATUS
ID NAME            STATE      TERM       INDEX      COMMIT     VOTE  FED_INDEX
 0 server-0        solo       0          -1         0          -1    -1

ZONE TEMPLATE
ENDPOINT="http://localhost:2633/RPC2"
```

{{< alert title="Important" type="info" >}}
Floating IP should be used for **zone endpoints** and cluster private addresses for the zone **server endpoints**.{{< /alert >}}

* **Leader**: Stop OpenNebula service and update `SERVER_ID` in `/etc/one/oned.conf`

```default
FEDERATION = [
    MODE          = "STANDALONE",
    ZONE_ID       = 0,
    SERVER_ID     = 0, # changed from -1 to 0 (as 0 is the server id)
    MASTER_ONED   = ""
]
```

* **Leader**: [Optional] Enable the RAFT Hooks in `/etc/one/oned.conf`. This will add a floating IP to the system.

{{< alert title="Note" type="info" >}}
Floating IP should be used for monitoring daemon parameter `MONITOR_ADDRESS` in `/etc/one/monitord.conf`{{< /alert >}} 

```default
# Executed when a server transits from follower->leader
RAFT_LEADER_HOOK = [
     COMMAND = "raft/vip.sh",
     ARGUMENTS = "leader eth0 10.3.3.2/24"
]

# Executed when a server transits from leader->follower
RAFT_FOLLOWER_HOOK = [
    COMMAND = "raft/vip.sh",
    ARGUMENTS = "follower eth0 10.3.3.2/24"
]
```

* **Leader**: Start OpenNebula.
* **Leader**: Check the zone. The server is now the *leader* and has the floating IP:

```default
$ onezone show 0
ZONE 0 INFORMATION
ID                : 0
NAME              : OpenNebula
STATE             : ENABLED


ZONE SERVERS
ID NAME            ENDPOINT
 0 server-0        http://192.168.150.1:2633/RPC2

HA & FEDERATION SYNC STATUS
ID NAME            STATE      TERM       INDEX      COMMIT     VOTE  FED_INDEX
 0 server-0        leader     1          3          3          -1    -1

ZONE TEMPLATE
ENDPOINT="http://localhost:2633/RPC2"
$ ip -o a sh eth0|grep 10.3.3.2/24
2: eth0    inet 10.3.3.2/24 scope global secondary eth0\       valid_lft forever preferred_lft forever
```

<a id="frontend-ha-setup-add-remove-servers"></a>

### Adding more servers

{{< alert title="Warning" type="warning" >}}
This procedure will discard the OpenNebula database in the server you are adding and substitute it with the database of the initial *leader*.{{< /alert >}} 

{{< alert title="Warning" type="warning" >}}
Add only one host at a time. Repeat this process for every server you want to add.{{< /alert >}} 

* **Leader**: Create a DB backup in the initial *leader* and distribute it to the new server, along with the files in `/var/lib/one/.one/`:

```default
$ onedb backup -u oneadmin -p oneadmin -d opennebula
MySQL dump stored in /var/lib/one/mysql_localhost_opennebula_2017-6-1_11:52:47.sql
Use 'onedb restore' or restore the DB using the mysql command:
mysql -u user -h server -P port db_name < backup_file

# Copy it to the other servers
$ scp /var/lib/one/mysql_localhost_opennebula_2017-6-1_11:52:47.sql <ip>:/tmp

# Copy the .one directory (make sure you preseve the owner: oneadmin)
$ ssh <ip> rm -rf /var/lib/one/.one
$ scp -r /var/lib/one/.one/ <ip>:/var/lib/one/
```

* **Follower**: Stop OpenNebula on the new server if it is running.
* **Follower**: Restore the database backup on the new server.

```default
$ onedb restore -f -u oneadmin -p oneadmin -d opennebula /tmp/mysql_localhost_opennebula_2017-6-1_11:52:47.sql
MySQL DB opennebula at localhost restored.
```

* **Leader**: Add the new server to OpenNebula (in the initial *leader*) and note the server id.

```default
$ onezone server-add 0 --name server-1 --rpc http://192.168.150.2:2633/RPC2
```

* **Leader**: Check the zone. The new server is in the error state, since OpenNebula on the new server is still not running. Make a note of the server id, in this case 1.

```default
$ onezone show 0
ZONE 0 INFORMATION
ID                : 0
NAME              : OpenNebula
STATE             : ENABLED


ZONE SERVERS
ID NAME            ENDPOINT
 0 server-0        http://192.168.150.1:2633/RPC2
 1 server-1        http://192.168.150.2:2633/RPC2

HA & FEDERATION SYNC STATUS
ID NAME            STATE      TERM       INDEX      COMMIT     VOTE  FED_INDEX
 0 server-0        leader     1          19         19         -1    -1
 1 server-1        error      -          -          -          -

ZONE TEMPLATE
ENDPOINT="http://localhost:2633/RPC2"
```

* **Follower**: Edit `/etc/one/oned.conf` on the new server to set the `SERVER_ID` for the new server. Make sure to enable the hooks as in the initial *leader’s* configuration.
* **Follower**: Start the OpenNebula service.
* **Leader**: Run `onezone show 0` to make sure that the new server is in *follower* state.

```default
$ onezone show 0
ZONE 0 INFORMATION
ID                : 0
NAME              : OpenNebula
STATE             : ENABLED


ZONE SERVERS
ID NAME            ENDPOINT
 0 server-0        http://192.168.150.1:2633/RPC2
 1 server-1        http://192.168.150.2:2633/RPC2

HA & FEDERATION SYNC STATUS
ID NAME            STATE      TERM       INDEX      COMMIT     VOTE  FED_INDEX
 0 server-0        leader     1          21         19         -1    -1
 1 server-1        follower   1          16         16         -1    -1

ZONE TEMPLATE
ENDPOINT="http://localhost:2633/RPC2"
```

{{< alert title="Note" type="info" >}}
It may be that the **TERM**/**INDEX**/**COMMIT** does not match (as above). This is not important right now; it will sync automatically when the database is changed.{{< /alert >}} 

* **Follower**: Ensure the new node has the exact same configuration as the **Leader** node. In order to do this [onezone serversync](#server-sync-ha) can be used to fetch the configuration from the Leader node.

{{< alert title="Note" type="info" >}}
If you are using FireEdge you need to restart this service in the **Follower** `systemctl restart opennebula-fireedge`.{{< /alert >}} 

Repeat this section to add new servers. Make sure that you only add servers when the cluster is in a healthy state. That means there is 1 *leader* and the rest are in *follower* state. If there is one server in error state, fix it before proceeding.

## Checking Cluster Health

Execute `onezone show <id>` to see if any of the servers are in error state. If they are in error state, check `/var/log/one/oned.log` in both the current *leader* (if any) and in the host that is in error state. All Raft messages will be logged in that file.

If there is no *leader* in the cluster please review `/var/log/one/oned.log` to make sure there are no errors taking place.

## Adding and Removing Servers

In order to add servers you need to use this command:

```default
$ onezone server-add
Command server-add requires one parameter to run
## USAGE
server-add <zoneid>
        Add an OpenNebula server to this zone.
        valid options: server_name, server_rpc

## OPTIONS
     -n, --name                Zone server name
     -r, --rpc                 Zone server RPC endpoint
     -v, --verbose             Verbose mode
     -h, --help                Show this message
     -V, --version             Show version and copyright information
     --user name               User name used to connect to OpenNebula
     --password password       Password to authenticate with OpenNebula
     --endpoint endpoint       URL of OpenNebula xmlrpc frontend
```

Make sure that there is one *leader* (by running `onezone show <id>`), otherwise it will not work.

To remove a server, use the command:

```default
$ onezone server-del
Command server-del requires 2 parameters to run.
## USAGE
server-del <zoneid> <serverid>
        Delete an OpenNebula server from this zone.

## OPTIONS
     -v, --verbose             Verbose mode
     -h, --help                Show this message
     -V, --version             Show version and copyright information
     --user name               User name used to connect to OpenNebula
     --password password       Password to authenticate with OpenNebula
     --endpoint endpoint       URL of OpenNebula xmlrpc frontend
```

The whole procedure is documented [above]({{% relref "#frontend-ha-setup-add-remove-servers" %}}).

<a id="frontend-ha-recover-servers"></a>

## Recovering Servers

When a *follower* is down for some time it may fall out of the recovery window, i.e. the log may not include all the records needed to bring it up to date. In order to recover this server you need to:

* **Leader**: Create a DB backup and copy it to the failed *follower*. Note that you cannot reuse a previous backup.
* **Follower**: Stop OpenNebula if it is running.
* **Follower**: Restore the DB backup from the *leader*.
* **Follower**: Start OpenNebula.
* **Leader**: Reset the failing *follower* with:

```default
$ onezone server-reset <zone_id> <server_id_of_failed_follower>
```

<a id="frontend-ha-zone"></a>

## Enable/Disable a Zone

During maintenance you may use `onezone disable zone_id`. Disabled zone can still execute read only commands, but can’t do any modifications to VMs, Hosts, Templates, etc. Right after `onezone disable zone_id`, there still can be VMs in transient states, it may take some time to finish all pending operations. To enable to zone again execute `onezone enable zone_id`.

<a id="frontend-ha-shared"></a>

## Shared Data Between HA Nodes

HA deployment requires the filesystem view of most datastores (by default in `/var/lib/one/datastores/`) to be the same on all frontends. It is necessary to set up a shared filesystem over the datastore directories. This document doesn’t cover configuration and deployment of the shared filesystem; it is left completely up to the cloud administrator.

OpenNebula stores virtual machine logs inside `/var/log/one/` as files named `${VMID}.log`. It is not recommended to share the whole log directory between the Front-ends as there are also other OpenNebula logs which would be randomly overwritten. It is up to the cloud administrator to periodically back-up the virtual machine logs on the cluster *leader*, and in case of fail-over to restore from the backup of a new *leader* (e.g. as part of the raft hook). You can use the `USE_VMS_LOCATION` option in `oned.conf` to generate the log files in `/var/lib/one/vms/${VMID}/vm.log`, this could simplify the synchronization process across servers.

## FireEdge

There are several types of FireEdge deployments in an HA environment. The basic one is FireEdge running on **each OpenNebula Front-end node** configured with the local OpenNebula. Only one server, the *leader* with floating IP, is used by the clients.

It is possible to configure a load balancer (e.g. HAProxy, Pound, Apache, or Nginx) over the Front-ends to spread the load (read operations) among the nodes.

To easily scale out beyond the total number of core OpenNebula daemons, FireEdge can be running on separate machines. They should talk to the cluster floating IP (see `:one_xmlprc:` in `fireedge-server.conf`) and shared `/var/tmp/` between Fireedge and Front-end nodes. Please check [Configuring FireEdge for Large Deployments]({{% relref "../large-scale_deployment/fireedge_for_large_deployments#fireedge-advance" %}}).

FireEdge need to share the same `/var/lib/one/.one/fireedge_key`. This is covered by the above procedure. Additionally, to have all provision logs available in all HA nodes (hence, available on leader change), all nodes need to share the same `/var/lib/one/fireedge` folder.

## Raft Configuration Attributes

The Raft algorithm can be tuned by several parameters in the configuration file `/etc/one/oned.conf`. The following options are available:

|                        | Raft: Algorithm Attributes                                                                                             |
|------------------------|------------------------------------------------------------------------------------------------------------------------|
| `LIMIT_PURGE`          | Number of DB log records that will be deleted on each purge.                                                           |
| `LOG_RETENTION`        | Number of DB log records kept, it determines the synchronization window across servers and extra storage space needed. |
| `LOG_PURGE_TIMEOUT`    | How often applied records are purged according the log retention value. (in seconds).                                  |
| `ELECTION_TIMEOUT_MS`  | Timeout to start an election process if no heartbeat or log is received from the *leader*. Can be used to prioritize servers, server with lower value has higher chance to be selected as leader. |
| `BROADCAST_TIMEOUT_MS` | How often heartbeats are sent to  *followers*.                                                                         |
| `XMLRPC_TIMEOUT_MS`    | To timeout raft-related API calls. To set an infinite timeout set this value to 0.                                     |

{{< alert title="Warning" type="warning" >}}
Any change in these parameters can lead to unexpected behavior during the fail-over and result in whole-cluster malfunction. After any configuration change, always check the crash scenarios for the correct behavior.{{< /alert >}} 

<a id="server-sync-ha"></a>

## Synchronize Configuration Files Across Servers

To synchronize files, you can use the command `onezone serversync`. This command is designed to help administrators to sync OpenNebula’s configurations across HA nodes and fix lagging nodes in HA environments. The command first checks for inconsistencies between local and remote configuration files inside the `/etc/one/` directory. If inconsistencies are found, the local version of a file will be replaced by the remote version, and only the affected service will be restarted. Whole configuration files will be replaced, with the sole exception of `/etc/one/oned.conf`. For this file, the local `FEDERATION` configuration and optionally the `RAFT` configuration will be maintained, but the rest of the content will be overwritten. Before replacing any file, a backup will be made inside `/etc/one/`.

{{< alert title="Warning" type="warning" >}}
Only use this option between HA nodes, never across federated nodes.{{< /alert >}} 

This is the list of files that will be checked and replaced:

Individual files:

- `/etc/one/monitord.conf`
- `/etc/one/oneflow-server.conf`
- `/etc/one/onegate-server.conf`

Folders:

- `/etc/one/fireedge`
- `/etc/one/auth`
- `/etc/one/hm`
- `/etc/one/schedulers`
- `/etc/one/vmm_exec`

{{< alert title="Note" type="info" >}}
Any file inside the above folders that does not exist on the remote server (such as backups) will *not* be removed.{{< /alert >}}

### Usage

{{< alert title="Important" type="info" >}}
The command has to be executed under a privileged user `root` (as it modifies the configuration files) and requires passwordless SSH access to the remote OpenNebula Front-end and to remote users `root` or `oneadmin`.{{< /alert >}} 

```default
# onezone serversync <remote_opennebula_server> [--db] [--keep-ha]
```

where `<remote_opennebula_server>` needs to be replaced by a hostname/IP of the OpenNebula server that will be used to fetch configuration files from. If `--db` option is used, the local database will be synced with the one located on remote server. If `--keep-ha` is used, the server will keep its own RAFT configuration

You also have to adjust the configuration file of each FireEdge `/etc/one/fireedge-server.conf`, to know which FireEdge corresponds to which zone.

```default
default_zone:
  id: 0
  name: 'OpenNebula'
  endpoint: 'http://localhost:2633/RPC2'
```

<a id="replace-failing-front-end"></a>

## Replace failing front-end

Follow this guide as the `oneadmin` user. To switch the user run:

```shell
sudo -i -u oneadmin
```

### Back up files

This command has to be executed in the failing Host.

Create the backup directory:

```shell
BAK_DIR=~/one_backup
mkdir -p $BAK_DIR
```

Copy configuration directory `/etc/one` to backup directory:

```shell
cp -rp --parents /etc/one $BAK_DIR
```

Copy remotes directory `/var/lib/one/remotes` to backup directory:

```shell
cp -rp --parents /var/lib/one/remotes $BAK_DIR
```

Copy keys directory `/var/lib/one/.one` to backup directory:

```shell
cp -rp --parents /var/lib/one/.one $BAK_DIR
```

Back up the database:

```shell
onedb backup -S <database_host> -u <user> -p <password> -d <database_name> -P <port>
```

Copy the database backup file to the backup directory:

```shell
cp -rp <onedb_backup> $BAK_DIR
```

### Remove failing Front-end from HA

Stop all the OpenNebula services `systemctl stop opennebula*`. This command has to be executed in the failing Host.

```shell
systemctl stop opennebula*
```

Remove it from HA using the CLI command onezone `onezone server-del <zone_id> <server_id>`. This command has to be executed in the leader.

```shell
onezone server-del <zone_id> <server_id>
```

### Add the server back to the HA

To add the a replacement server into the HA cluster, please follow this
[guide](http://docs.opennebula.org/5.8/advanced_components/ha/frontend_ha_setup.html#adding-more-servers).

