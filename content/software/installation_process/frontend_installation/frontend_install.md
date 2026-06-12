---
title: "Manual Single Front-end Installation"
linkTitle: "Manual - Front-end"
date: "2025-02-17"
description:
categories:
pageintoc: "173"
tags:
show_card:
weight: "6"
---

<a id="frontend-install"></a>

This page describes how to install a complete OpenNebula Front-end from binary packages available in the [software repositories]({{% relref "opennebula_repository_configuration" %}}) configured in the previous section. We recommend using a Host with the supported operating system as installation from packages provides the best experience and is referenced in other places of this documentation. If there are no packages for your distribution, you might consider reading the [Building from Source Code]({{% relref "compile#compile" %}}) guide to build OpenNebula for your chosen distribution.

Proceed with the following steps to get the fully-featured OpenNebula Front-end up.

<a id="setup-opennebula-repos"></a>

## Step 1. Install the Database and Configure the OpenNebula Repositories

Before installing the OpenNebula Front-end, you should install the database and configure the repositories. If you haven't already installed the database, complete the [Database Setup Guide]({{% relref "software/installation_process/frontend_installation/database" %}}).

After installing the database, follow one of the following guides to configure the software repositories for the OpenNebula edition you intend to deploy:

* [Configure OpenNebula Community Edition repositories]({{% relref "opennebula_repository_configuration_ce" %}})
* [Configure OpenNebula Enterprise Edition repositories]({{% relref "opennebula_repository_configuration_ee" %}})

## Step 2. Add Third Party Repositories

Not all OpenNebula dependencies are in base distribution repositories. On selected platforms below you need to enable third party repositories by running the following commands under privileged user (`root`):

{{< tabpane text=true right=false >}}
{{% tab header="**OS**:" disabled=true /%}}

{{% tab header="**AlmaLinux 9, 10**"%}}
**AlmaLinux 9, 10**

```shell
yum -y install epel-release
```

{{% /tab %}}
{{% tab header="**RHEL 9**"%}}

**RHEL 9**

```shell
rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
```

{{% /tab %}}
{{< /tabpane >}}

## Step 3. Installing the Software

Available packages for OpenNebula clients, the Front-end and hypervisor nodes:

| Package                                                                                                  | Description                                                                                                                                          |
|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| **opennebula**                                                                                           | OpenNebula Daemon and Scheduler (*EE comes with additional Enterprise Tools*)                                                                        |
| **opennebula-tools**                                                                                     | Command Line Interface                                                                                                                               |
| **opennebula-fireedge**                                                                                  | Next-generation GUI [FireEdge]({{% relref "fireedge#fireedge-setup" %}})                                                                             |
| **opennebula-gate**                                                                                      | [OneGate]({{% relref "onegate_usage#onegate-overview" %}}) server which allows communication between VMs and OpenNebula                              |
| **opennebula-flow**                                                                                      | [OneFlow]({{% relref "/product/virtual_machines_operation/multi-vm_workflows/overview#oneflow-overview" %}}) manages services and elasticity |
| **opennebula-migration**                                                                                 | Database migration tools                                                                                                                             |
| **opennebula-node-kvm**                                                                                  | Base setup for KVM hypervisor Node                                                                                                                   |
| **opennebula-node-lxc**                                                                                  | Base setup for LXC hypervisor Node (*not on RHEL 7*)                                                                                                 |
| **opennebula-prometheus**                                                                                | OpenNebula Prometheus and Grafana integration                                                                                                        |
| **opennebula-prometheus-kvm**                                                                            | OpenNebula KVM exporters                                                                                                                             |
| **opennebula-prometheus-ovs**                                                                            | (optional) Prometheus exporter for Open vSwitch metrics                                                                                              |
| **opennebula-prometheus-mysql**                                                                          | (optional) Prometheus exporter for MySQL/MariaDB server metrics                                                                                      |
| **opennebula-prometheus-smartctl**                                                                       | (optional) Prometheus exporter for S.M.A.R.T. disk metrics                                                                                           |
| **opennebula-prometheus-lvm**                                                                            | (optional) Prometheus exporter for LVM metrics                                                                                                       |
| **opennebula-swap**                                                                                      | OneSwap migration tool from vCenter to OpenNebula KVM                                                                                                |
| **opennebula-guacd**                                                                                     | Proxy daemon for Guacamole                                                                                                                           |
| **opennebula-rubygems**                                                                                  | Bundled Ruby gem dependencies                                                                                                                        |
| **opennebula-libs**                                                                                      | Shared Ruby libraries among various components                                                                                                       |
| **opennebula-common**                                                                                    | Shared content for OpenNebula packages                                                                                                               |
| **opennebula-common-onecfg**                                                                             | Helpers for [Configuration Management]({{% relref "software/upgrade_process/configuration_management_ee/" %}}) tool                                     |
| rpm: **opennebula-java** <br/><br/>deb: **libopennebula-java** <br/><br/>deb: **libopennebula-java-doc** | [Java OCA]({{% relref "/product/integration_references/system_interfaces/java#java" %}}) Bindings                                            |
| **python3-pyone**                                                                                        | [Python 3 OCA]({{% relref "/product/integration_references/system_interfaces/python#python" %}}) Bindings                                    |

There are also packages with debugging symbols for some platforms, e.g., `openenbula-debuginfo` on AlmaLinux/RHEL and `opennebula-dbgsym` on Debian/Ubuntu. Other architecture-specific components might come with similarly named packages, please check your packaging database if necessary.

{{< alert title="Note" type="info" >}}
There are a few differences in package names among distributions. Those with varying package names contain mostly integration libraries and since they are for general use on installation Hosts, their names are left to follow the distribution conventions. Above, you can find the AlmaLinux/RHEL specific packages prefixed with “*rpm:*” and Debian/Ubuntu specific packages prefixed with “*deb:*”.{{< /alert >}}

Install all OpenNebula Front-end components by executing the following commands under a privileged user:

{{< tabpane text=true right=false >}}
{{% tab header="**OS**:" disabled=true /%}}

{{% tab header="**AlmaLinux 9, 10**"%}}
**AlmaLinux / RHEL**

```shell
yum -y install opennebula opennebula-fireedge opennebula-gate opennebula-flow
```

{{% /tab %}}
{{% tab header="**RHEL 9**"%}}

**Debian / Ubuntu**

```shell
apt-get update
```
```shell
apt-get -y install opennebula opennebula-fireedge opennebula-gate opennebula-flow
```
{{% /tab %}}
{{% tab header="**SLES / openSUSE**"%}}

**SLES / openSUSE**

```shell
zypper install opennebula opennebula-fireedge opennebula-gate opennebula-flow
```

{{% /tab %}}
{{< /tabpane >}}

## Step 4. Enabling MySQL/MariaDB (Optional)

You can skip this step if you want to deploy OpenNebula as quickly as possible for evaluation.

If you are deploying Front-end for production/serious use, make sure you read the [Database Setup]({{% relref "database#database-setup" %}}) guide and select the suitable database backend. Although it **is** possible to switch from (default) SQLite to MySQL/MariaDB backend later, it’s not easy and straightforward, so **we suggest to deploy and use MySQL/MariaDB backend from the very beginning**.

## Step 5. Configuring OpenNebula

### OpenNebula Daemon

{{< alert title="Important" type="info" >}}
This is **only for initial** OpenNebula deployment, not applicable to upgrades!{{< /alert >}}

OpenNebula’s initial deployment on first usage creates a user `oneadmin` **inside the OpenNebula** (not to be confused with system user `oneadmin` in the Front-end operating system!) based on a randomly generated password read from `/var/lib/one/.one/one_auth`. To set your own user password from the very beginning, proceed with the following steps before starting the services:

1. Log in as the `oneadmin` system user with this command:

```shell
sudo -u oneadmin /bin/sh
```

2. Create file `/var/lib/one/.one/one_auth` with initial password in the format `oneadmin:<password>`

```shell
echo 'oneadmin:changeme123' > /var/lib/one/.one/one_auth
```

{{< alert title="Warning" type="warning" >}}
This will set the oneadmin’s password only upon starting OpenNebula for the first time. From that point, you must use the `oneuser passwd` command to change oneadmin’s password. More information on how to change the oneadmin password is [here]({{% relref "/product/cloud_system_administration/multitenancy/manage_users#change-credentials" %}}).{{< /alert >}}

Check how to [change oneadmin password]({{% relref "product/cloud_system_administration/multitenancy/manage_users#change-credentials" %}}) for already running services.

{{< alert title="Note" type="info" >}}
For advanced setup, follow the configuration references for the OpenNebula [Daemon]({{% relref "oned#oned-conf" %}}).{{< /alert >}}

### FireEdge

OpenNebula FireEdge is the next-generation web UI server that replaces the legacy Ruby Sunstone. It provides the Sunstone GUI, including additional functionality provided via Guacamole. It is installed and configured by default.

{{< alert title="Note" type="info" >}}
For advanced setup, follow the FireEdge [configuration reference]({{% relref "fireedge#fireedge-configuration" %}}).{{< /alert >}}

### OneGate (Optional)

The OneGate server allows communication between VMs and OpenNebula. It’s optional and not required for basic functionality but is essential for multi-VM services orchestrated by OneFlow server below. The configuration is two-phase: configure the OneGate server to listen for the connections from outside the Front-end and configure the OpenNebula Daemon with OneGate endpoint passed to the Virtual Machines. Neither or both must be done.

1. To configure OneGate, edit `/etc/one/onegate-server.conf` and update the `:bind` parameter under `:server` with the service listening address. For example, use `0.0.0.0` to work on all configured network interfaces on the Front-end:

```yaml
:server:
  :bind: 0.0.0.0
  :port: 5030
```

2. To configure OpenNebula Daemon, edit `/etc/one/oned.conf` and set the `ONEGATE_ENDPOINT` with the URL and port of your OneGate server (domain or IP-based). The endpoint address **must be reachable directly from your future Virtual Machines**. You need to decide which Virtual Networks and addresses will be used in your cloud. For example:

```shell
ONEGATE_ENDPOINT="http://one.example.com:5030"
```

If you are reconfiguring already running services at a later point, don’t forget to restart them to apply the changes.

{{< alert title="Note" type="info" >}}
For advanced setup, follow the OneGate [configuration reference]({{% relref "onegate#onegate-conf" %}}).{{< /alert >}}

### OneFlow (Optional)

The OneFlow server orchestrates the services and multi-VM deployments. While for most cases the default configuration fits well, you might need to reconfigure the service to be able to control the OneFlow **remotely** over API. Edit the `/etc/one/oneflow-server.conf` and update `:host:` parameter with service listening address accordingly. For example, use `0.0.0.0` to work on all configured network interfaces on the Front-end:

```shell
:host: 0.0.0.0
```

If you are reconfiguring already running services at a later point, don’t forget to restart them to apply the changes.

{{< alert title="Note" type="info" >}}
For advanced setup, follow the OneFlow [configuration reference]({{% relref "oneflow#appflow-configure" %}}).{{< /alert >}}

<a id="frontend-services"></a>

## Step 6. Starting and Managing OpenNebula Services

The complete list of operating system services provided by OpenNebula:

| Service                          | Description                                                                                                                 | Auto-Starts With    |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------|---------------------|
| **opennebula**                   | Main OpenNebula Daemon (oned), XML-RPC API endpoint                                                                         |                     |
| **opennebula-hem**               | Hook Execution Service                                                                                                      | opennebula          |
| **opennebula-fireedge**          | Next-generation GUI server [FireEdge]({{% relref "fireedge#fireedge-setup" %}}) 						 |                     |
| **opennebula-gate**              | OneGate Server for communication between VMs and OpenNebula                                                                 |                     |
| **opennebula-flow**              | OneFlow Server for multi-VM services                                                                                        |                     |
| **opennebula-guacd**             | Guacamole Proxy Daemon                                                                                                      | opennebula-fireedge |
| **opennebula-showback**          | Service for periodic recalculation of showback                                                                              | opennebula          |
| **opennebula-ssh-agent**         | Dedicated SSH agent for OpenNebula Daemon                                                                                   | opennebula          |
| **opennebula-ssh-socks-cleaner** | Periodic cleaner of SSH persistent connections                                                                              | opennebula          |
| **opennebula-prometheus**        | OpenNebula Prometheus server                                                                                                |                     |

{{< alert title="Note" type="info" >}}
Since 5.12, the OpenNebula comes with an integrated SSH agent as the `opennebula-ssh-agent` service, which removes the need to copy oneadmin’s SSH private key across your Hosts. For more information, refer to the [passwordless login]({{% relref "software/installation_process/cluster_installation/kvm_node_installation#kvm-local" %}}) section of the manual.{{< /alert >}}

You are ready to **start** all OpenNebula services with the following command (NOTE: you might want to remove the services from the command arguments if you skipped their configuration steps above):

```default
systemctl start opennebula opennebula-fireedge opennebula-gate opennebula-flow
```

{{< alert title="Warning" type="warning" >}}
Make sure all required [network ports]({{% relref "frontend_install#frontend-fw" %}}) are enabled on your firewall (on Front-end or the router).{{< /alert >}}

Other OpenNebula services might be started as a dependency but you don’t need to care about them unless they need to be explicitly restarted or stopped. To start these **services automatically on server boot**, it’s necessary to enable them by the following command:

```default
systemctl enable opennebula opennebula-fireedge opennebula-gate opennebula-flow
```

<a id="verify-frontend-section"></a>

## Step 7. Verifying the Installation

After OpenNebula is started for the first time, you should check that the commands can connect to the OpenNebula Daemon. You can do this in the Linux CLI or the graphical user interface Sunstone.

### Linux CLI

In the Front-end, run the following command as `oneadmin` system user and find a similar output:

```default
$ oneuser show
USER 0 INFORMATION
ID              : 0
NAME            : oneadmin
GROUP           : oneadmin
PASSWORD        : 3bc15c8aae3e4124dd409035f32ea2fd6835efc9
AUTH_DRIVER     : core
ENABLED         : Yes

USER TEMPLATE
TOKEN_PASSWORD="ec21d27e2fe4f9ed08a396cbd47b08b8e0a4ca3c"

RESOURCE USAGE & QUOTAS
```

If you get an error message then the OpenNebula Daemon could not be started properly:

```default
$ oneuser show
Failed to open TCP connection to localhost:2633 (Connection refused - connect(2) for "localhost" port 2633)
```

To check for errors, you can search in the main OpenNebula Daemon log file, `/var/log/one/oned.log`. Check for any error messages marked with `[E]`.

<a id="verify-frontend-section-sunstone"></a>

### FireEdge

{{< alert title="Note" type="info" >}}
Make sure the TCP port 2616 is not blocked on your firewall.{{< /alert >}}

Now you can try to log in through the Sunstone GUI and Provision GUI. To do so, point your browser to `http://<frontend_address>:2616/fireedge/sunstone` to access Sunstone and point your browser to `http://<frontend_address>:2616/fireedge/provision` to access Provision. You should get to the login page in both cases. The access user is `oneadmin` and initial (or customized) password is the one from the file `/var/lib/one/.one/one_auth` on your Front-end.

{{< image
  pathDark="/images/quickstart/dark/sunstone_login_page.png"
  path="/images/quickstart/light/sunstone_login_page.png"
  alt="Sunstone login" align="center" width="50%" mb="20px"
>}}

In case of problems, you can investigate the OpenNebula logs in `/var/log/one` and check file `/var/log/one/fireedge.log`.

### Directory Structure

The following table lists various significant directories on your OpenNebula Front-end:

| Path                              | Description                                                              |
|-----------------------------------|--------------------------------------------------------------------------|
| `/etc/one/`                       | **Configuration files**                                                  |
| `/var/log/one/`                   | Log files, e.g. `oned.log`, `fireedge.log` and `<vmid>.log`              |
| `/var/lib/one/`                   | `oneadmin` home directory                                                |
| `/var/lib/one/datastores/<dsid>/` | Storage for the datastores                                               |
| `/var/lib/one/vms/<vmid>/`        | Action files for VMs (deployment file, transfer manager scripts, etc…)   |
| `/var/lib/one/.one/one_auth`      | `oneadmin` credentials                                                   |
| `/var/lib/one/remotes/`           | Probes and scripts that will be synced to the Hosts                      |
| `/var/lib/one/remotes/etc`        | **Configuration files** for probes and scripts                           |
| `/var/lib/one/remotes/hooks/`     | Hook scripts                                                             |
| `/var/lib/one/remotes/vmm/`       | Virtual Machine Manager Driver scripts                                   |
| `/var/lib/one/remotes/auth/`      | Authentication Driver scripts                                            |
| `/var/lib/one/remotes/im/`        | Information Manager (monitoring) Driver scripts                          |
| `/var/lib/one/remotes/market/`    | Marketplace Driver scripts                                               |
| `/var/lib/one/remotes/datastore/` | Datastore Driver scripts                                                 |
| `/var/lib/one/remotes/vnm/`       | Networking Driver scripts                                                |
| `/var/lib/one/remotes/tm/`        | Transfer Manager Driver scripts                                          |

<a id="frontend-fw"></a>

### Firewall Configuration

The list below shows the ports used by OpenNebula. These ports need to be open for OpenNebula to work properly:

|     Port      | Description                                                  |
|---------------|--------------------------------------------------------------|
| `22`          | Front-end Host SSH server                                    |
| `2474`        | OneFlow server                                               |
| `2616`        | Next-generation GUI server FireEdge                          |
| `2633`        | Main OpenNebula Daemon (oned), XML-RPC API endpoint          |
| `4124`        | Monitoring daemon (both TCP/UDP)                             |
| `5030`        | OneGate server                                               |
| `29876`       | noVNC Proxy Server                                           |
| `5900+`       | VNC Server ports on Hosts for VMs. See VNC_PORTS             |
| `49152-49215` | Host-Host port communication required for KVM live migrations|

{{< alert title="Note" type="info" >}}
These are only the default ports. Each component can be configured to bind to specific ports or use a HTTP Proxy.{{< /alert >}}

OpenNebula connects to the hypervisor nodes over SSH (port 22). Additionally, the main OpenNebula Daemon (oned) may connect to various remote Marketplace servers to get a list of available appliances, e.g.:

- OpenNebula Marketplace (`https://marketplace.opennebula.io/`)
- Linux Containers Marketplace (`https://images.linuxcontainers.org/`)

You should open the outgoing connections to these services.

## Step 8. Stop and Restart Services (Optional)

To stop, start, or restart any of the listed individual [services]({{% relref "#frontend-services" %}}), follow the examples below for a selected service:

```shell
systemctl stop opennebula
```
```shell
systemctl start opennebula
```
```shell
systemctl restart opennebula
```
```shell
systemctl try-restart opennebula
```

Use following command to **stop all** OpenNebula services:

```shell
systemctl stop opennebula opennebula-hem opennebula-fireedge \
    opennebula-gate opennebula-flow opennebula-guacd \
    opennebula-novnc opennebula-showback.timer \
    opennebula-ssh-agent opennebula-ssh-socks-cleaner.timer
```

Use the following command to **restart all** already running OpenNebula services:

```shell
systemctl try-restart opennebula-hem opennebula-fireedge \
    opennebula-gate opennebula-flow opennebula-guacd \
    opennebula-novnc opennebula-ssh-agent
```

Learn more about [Managing Services with Systemd](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/managing-systemd_configuring-basic-system-settings).

In production environments the services should be stopped in a specific order and with extra manual safety checks:

1. Stop **opennebula-fireedge** to disable GUI access to users.
2. Stop **openenbula-flow** to disable unattended multi-VM options.
3. Check and wait until there are no active operations with VMs and images.
4. Stop **opennebula** and rest services.

## Next Steps

Now that you have successfully started your OpenNebula services, you can continue with adding content to your cloud. Add hypervisor nodes, storage, and Virtual Networks. Or you can provision users with groups and permissions, images, define and run Virtual Machines.

Continue with the following guides:

- [Cluster Deployment]({{% relref "software/installation_process/cluster_installation/" %}}) to deploy Clusters automatically or install hypervisor nodes manually.
- [OpenNebula Cloud Management and Operations]({{% relref "product" %}}) for details on configuring and administering your cloud deployment.
