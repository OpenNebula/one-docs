---
title: "Installation and Configuration"

description:
categories:
pageintoc: ""
tags:
weight: "2"
---

<a id="monitor-alert-installation"></a>

<!--# Installation and Configuration -->

This page describes how to install the OpenNebula Prometheus integration packages available in the [OpenNebula software repositories]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration" %}}).

## Step 1. OpenNebula Repositories [Front-end, Hosts]

At this point OpenNebula software repositories should already be configured in your Front-end and Hosts. Double check this is the case before proceeding, more information can be found in the [OpenNebula Repositories]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration" %}}) guide.

## Step 2. Install Front-end Packages [Front-end]

In your OpenNebula Front-end, install the Prometheus package. This package includes:

> - The [Prometheus monitoring system binary](https://github.com/prometheus/prometheus).
> - The [Prometheus Alertmanager binary](https://github.com/prometheus/alertmanager).

You should also install the Prometheus-KVM package that includes metric exporters. This package includes:

> - The OpenNebula exporter.
> - The OpenNebula Libvirt exporter (unused in Front-ends).
> - The [Prometheus Node exporter binary](https://github.com/prometheus/node_exporter/blob/master/LICENSE).

Prometheus, Alertmanager Node Exporter are free software and they are re-distributed for your convenience under the terms of the Apache License 2.0, as described in the [Prometheus](https://github.com/prometheus/prometheus/blob/main/LICENSE), [Alertmanager](https://github.com/prometheus/alertmanager/blob/main/LICENSE) and [Node exporter](https://github.com/prometheus/node_exporter/blob/master/LICENSE) licenses respectively.

Note that you will be able to use any existing installation of both systems after the installation.

**RPM-based distributions (Alma, RHEL)**

```default
# yum -y install opennebula-prometheus opennebula-prometheus-kvm
```

**Deb-based distributions (Ubuntu, Debian)**

```default
# apt -y install opennebula-prometheus opennebula-prometheus-kvm
```

**SLES/openSUSE**

```default
# zypper install opennebula-prometheus opennebula-prometheus-kvm
```

## Step 3. Install Hosts Packages [Hosts]

In your Hosts you need to install the Prometheus-KVM, this package includes:

> - The OpenNebula exporter (unused in Hosts).
> - The OpenNebula Libvirt exporter.
> - The [Prometheus Node exporter binary](https://github.com/prometheus/node_exporter/blob/master/LICENSE).

Prometheus Node exporter is free software and re-distributed in this package for your convenience under the terms of the Apache License 2.0, as described in the [Node exporter license](https://github.com/prometheus/node_exporter/blob/master/LICENSE).

Note that you will be able to use any existing installation of the node exporter after the installation.

**RPM-based distributions (Alma, RHEL)**

```default
# yum -y install opennebula-prometheus-kvm
```

**Deb-based distributions (Ubuntu, Debian)**

```default
# apt -y install opennebula-prometheus-kvm
```

**SLES/openSUSE**

```default
# zypper install opennebula-prometheus-kvm
```

## Step 4. Configure Prometheus [Front-end]

The OpenNebula Prometheus package comes with a simple script that automatically configures the scrape endpoints for your cloud. First, make sure all your Hosts are properly listed with the onehost command, for example:

```default
$ onehost list
ID NAME                          CLUSTER    TVM      ALLOCATED_CPU      ALLOCATED_MEM STAT
 1 kvm-local-uimw3-2.test        default      0       0 / 100 (0%)     0K / 1.2G (0%) on
 0 kvm-local-uimw3-1.test        default      0       0 / 100 (0%)     0K / 1.2G (0%) on
```

Now, we will generate the Prometheus configuration in `/etc/one/prometheus/prometheus.yml`, as `root` (or `oneadmin`) execute:

```default
# /usr/share/one/prometheus/patch_datasources.rb
```

This command connects to your cloud as oneadmin to gather the relevant information. Now you can verify the configuration, for the example above:

```default
# cat /etc/one/prometheus/prometheus.yml

---
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 127.0.0.1:9093

rule_files:
- rules.yml

scrape_configs:
- job_name: prometheus
  static_configs:
  - targets:
    - 127.0.0.1:9090
- job_name: opennebula_exporter
  static_configs:
  - targets:
    - 127.0.0.1:9925
- job_name: node_exporter
  static_configs:
  - targets:
    - 127.0.0.1:9100
  - targets:
    - kvm-local-uimw3-2.test:9100
    labels:
      one_host_id: '1'
  - targets:
    - kvm-local-uimw3-1.test:9100
    labels:
      one_host_id: '0'
- job_name: libvirt_exporter
  static_configs:
  - targets:
    - kvm-local-uimw3-2.test:9926
    labels:
      one_host_id: '1'
  - targets:
    - kvm-local-uimw3-1.test:9926
    labels:
      one_host_id: '0'
```

You can adjust scrape intervals or other configuration attributes in this file.

{{< alert title="Note" type="info" >}}
You can easily add or remove Hosts by copying or deleting the corresponding targets, or simply re-run the script. In that case you’ll have a backup in `/etc/one/prometheus/` to recover any additional configurations.{{< /alert >}}

## Step 5. Start the Prometheus Service [Front-end]

Prometheus service is controlled with a Systemd unit file (`/usr/lib/systemd/system/opennebula-prometheus.service`). We recommend that you take a look at the default options set in that file and add any flags of interest for your setup (e.g., run `prometheus -h` to get a complete list).

Once you are happy with the options, start and enable Prometheus:

```default
# systemctl enable --now opennebula-prometheus.service
```

Finally, we need to start and enable both exporters:

```default
# systemctl enable --now opennebula-exporter.service opennebula-node-exporter.service
```

If everything went ok, you should be able to check that Prometheus and both exporters are running:

```default
# ss -tapn | grep 'LISTEN.*\(9925\|9100\|9090\)'
LISTEN    0      100          0.0.0.0:9925       0.0.0.0:*     users:(("ruby",pid=32402,fd=7))
LISTEN    0      4096               *:9090             *:*     users:(("prometheus",pid=35494,fd=7))
LISTEN    0      4096               *:9100             *:*     users:(("node_exporter",pid=32507,fd=3))
```

and the opennebula-exporter is providing the monitor metrics:

```default
$ curl http://localhost:9925/metrics
# TYPE opennebula_host_total gauge
# HELP opennebula_host_total Total number of hosts defined in OpenNebula
opennebula_host_total 2.0
# TYPE opennebula_host_state gauge
# HELP opennebula_host_state Host state 0:init 2:monitored 3:error 4:disabled 8:offline
opennebula_host_state{one_host_id="1"} 2.0
opennebula_host_state{one_host_id="0"} 2.0
```

## Step 6. Start Node and Libvirt Exporters [Host]

Now we need to enable and start the node and libvirt exporters. Simply, using the provided Systemd unit files:

```default
# systemctl enable --now opennebula-libvirt-exporter.service opennebula-node-exporter.service
```

As we did previously, let’s verify exporters are listening in the targets ports:

```default
# ss -tapn | grep 'LISTEN.*\(9926\|9100\)'
LISTEN    0      100          0.0.0.0:9926       0.0.0.0:*     users:(("ruby",pid=38851,fd=7))
LISTEN    0      4096               *:9100             *:*     users:(("node_exporter",pid=38884,fd=3))
```

You should also be able to retrieve some metrics:

```default
$ curl localhost:9926/metrics
# TYPE opennebula_libvirt_requests_total counter
# HELP opennebula_libvirt_requests_total The total number of HTTP requests handled by the Rack application.
opennebula_libvirt_requests_total{code="200",method="get",path="/metrics"} 18.0
...
# TYPE opennebula_libvirt_daemon_up gauge
# HELP opennebula_libvirt_daemon_up State of the libvirt daemon 0:down 1:up
opennebula_libvirt_daemon_up 1.0
```

<a id="monitor-alert-extra-exporters"></a>

## Optional Exporters

OpenNebula ships four optional Prometheus exporter sub-packages. Each one is independently installable and only needed where the matching subsystem is in use:

| Sub-package                          | Where to install   | Default port | Requirements | Upstream                                                                       |
|--------------------------------------|--------------------|--------------|--------------|--------------------------------------------------------------------------------|
| opennebula-prometheus-ovs          | KVM Hosts with OVS | 9475         | Open vSwitch daemon running (v3.6) | [Liquescent-Development/ovs_exporter](https://github.com/Liquescent-Development/ovs_exporter) |
| opennebula-prometheus-mysql        | Front-end with MySQL/MariaDB | 9104         | -            | [prometheus/mysqld_exporter](https://github.com/prometheus/mysqld_exporter)    |
| opennebula-prometheus-smartctl     | Hosts with physical disks | 9633         | `smartmontools` (>= 7.0) installed; elevated/disk group permissions | [prometheus-community/smartctl_exporter](https://github.com/prometheus-community/smartctl_exporter) |
| opennebula-prometheus-lvm          | Hosts using LVM    | 9845         | -            | [hansmi/prometheus-lvm-exporter](https://github.com/hansmi/prometheus-lvm-exporter) |

These exporter binaries are pre-built upstream releases re-distributed for your convenience under their respective licenses.

Install on the relevant Hosts (or Front-ends, for `mysql`):

**RPM-based distributions (Alma, RHEL)**

```default
# yum -y install opennebula-prometheus-{ovs|mysql|smartctl|lvm}
```

**Deb-based distributions (Ubuntu, Debian)**

```default
# apt -y install opennebula-prometheus-{ovs|mysql|smartctl|lvm}
```

**SLES/openSUSE**

```default
# zypper install opennebula-prometheus-{ovs|mysql|smartctl|lvm}
```

Each package installs the exporter binary, a systemd unit, and runtime hardening (e.g. file capabilities for `ovs_exporter`, `disk` group membership for `smartctl_exporter`). Enable and start the corresponding service after install:

```default
# systemctl enable --now opennebula-{ovs|mysql|smartctl|lvm}-exporter.service
```

For the `mysql` exporter, the service reads database credentials from `/var/lib/one/.my.cnf` (owned by `oneadmin`, mode `0600`):

```ini
[client]
user=<db_user>
password=<db_password>
```

### Adding the Exporters to Prometheus

Re-run `patch_datasources.rb` on the Front-end after installing a new exporter:

```default
# /usr/share/one/prometheus/patch_datasources.rb
# systemctl restart opennebula-prometheus
```

The script TCP-probes every Host (`onehost list`) and Zone server (`onezone show`) on each known exporter port and adds a scrape job only for the ones that respond and generates a configuration file: `/etc/one/prometheus/prometheus.yml`.

No manual configuration is required — install the sub-package, start the service, re-run the script, and the new exporter appears in Prometheus under a job named after the exporter (`ovs_exporter`, `mysql_exporter`, `smartctl_exporter`, `lvm_exporter`).

<a id="monitor-alert-existing"></a>

## Using an Existing Prometheus Installation

If you already have an existing Prometheus installation, you just need to adapt Steps 4, 5, and 6 as follows:

> - You can use `/usr/share/one/prometheus/patch_datasources.rb` as described in Step 4 to copy the scrape configurations into your current Prometheus configuration file.
> - You just need to enable and start the `opennebula-exporter` as described in Step 5, but not the Prometheus service.
> - You will be already running the official node exporter, so in Step 6 only enable the `opennebula-libvirt-exporter`

<a id="monitor-alert-ha"></a>

## Using Prometheus with OpenNebula in HA

You can refer to [OpenNebula Front-end HA]({{% relref "../../../product/control_plane_configuration/high_availability/frontend_ha#frontend-ha-setup" %}}) to learn more about HA mode in OpenNebula.

Let’s assume your existing OpenNebula instance consists of three Front-ends and two KVM Hosts:

```default
# onezone show 0
ZONE 0 INFORMATION
ID                : 0
NAME              : OpenNebula
STATE             : ENABLED

ZONE SERVERS
ID NAME            ENDPOINT
 0 Node-1          http://192.168.150.1:2633/RPC2
 1 Node-2          http://192.168.150.2:2633/RPC2
 2 Node-3          http://192.168.150.3:2633/RPC2

HA & FEDERATION SYNC STATUS
ID NAME            STATE      TERM       INDEX      COMMIT     VOTE  FED_INDEX
 0 Node-1          follower   26         13719      13719      2     -1
 1 Node-2          follower   26         13719      13719      -1    -1
 2 Node-3          leader     26         13719      13719      2     -1

ZONE TEMPLATE
ENDPOINT="http://localhost:2633/RPC2"
```

```default
# onehost list
ID NAME                CLUSTER  TVM   ALLOCATED_CPU      ALLOCATED_MEM  STAT
1 kvm-ha-xqhnt-5.test  default    2  20 / 100 (20%)  192M / 1.4G (13%)  on
0 kvm-ha-xqhnt-4.test  default    1  10 / 100 (10%)   96M / 1.4G (6%)   on
```

Executing the `/usr/share/one/prometheus/patch_datasources.rb` script on the “first” (192.168.150.1) Front-end should produce the following Prometheus configuration:

```yaml
---
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 192.168.150.2:9093
      - 192.168.150.3:9093
      - 192.168.150.1:9093

rule_files:
- rules.yml

scrape_configs:
- job_name: prometheus
  static_configs:
  - targets:
    - localhost:9090
- job_name: opennebula_exporter
  static_configs:
  - targets:
    - 192.168.150.1:9925
- job_name: node_exporter
  static_configs:
  - targets:
    - 192.168.150.2:9100
    - 192.168.150.3:9100
    - 192.168.150.1:9100
  - targets:
    - kvm-ha-xqhnt-5.test:9100
    labels:
      one_host_id: '1'
  - targets:
    - kvm-ha-xqhnt-4.test:9100
    labels:
      one_host_id: '0'
- job_name: libvirt_exporter
  static_configs:
  - targets:
    - kvm-ha-xqhnt-5.test:9926
    labels:
      one_host_id: '1'
  - targets:
    - kvm-ha-xqhnt-4.test:9926
    labels:
      one_host_id: '0'
```

You can spot that all Front-ends and all Hosts are included in various scrape jobs. You can also see configuration for alerting:

```yaml
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 192.168.150.2:9093
      - 192.168.150.3:9093
      - 192.168.150.1:9093
```

which points to *all* alertmanager instances that are supposed to be configured in [HA mode](https://prometheus.io/docs/alerting/latest/alertmanager/#high-availability) as well (to deduplicate alert notifications).

{{< alert title="Important" type="info" >}}
Services `opennebula-prometheus`, `opennebula-alertmanager`, `opennebula-node-exporter` and `opennebula-exporter` should be configured, enabled and started on *all* Front-end machines.{{< /alert >}}

To configure each alertmanager as a cluster peer, you need to override (or modify) the `opennebula-alertmanager` systemd service.
For example on the “second” Front-end:

```default
# mkdir -p /etc/systemd/system/opennebula-alertmanager.service.d/
# cat >/etc/systemd/system/opennebula-alertmanager.service.d/override.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/alertmanager \
          --config.file=/etc/one/alertmanager/alertmanager.yml \
          --storage.path=/var/lib/alertmanager/data/ \
          --cluster.peer=192.168.150.1:9094 \
          --cluster.peer=192.168.150.3:9094
EOF
# systemctl restart opennebula-alertmanager.service
```

{{< alert title="Note" type="info" >}}
You can create the `opennebula-alertmanager.service.d/override.conf` file yourself or automatically with `systemctl edit opennebula-alertmanager.service`.{{< /alert >}}
