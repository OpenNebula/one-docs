---
title: "Kubernetes Cluster Configuration"
linkTitle: "Configuration"
date: "2026-05-12"
description:
categories:
tags:
weight: "3"
type: docs
---

This page summarizes the main runtime configuration used by the OneKS service. It covers the settings that define the service behavior and the server configuration options.

## Configuration File

By default, the main OneKS server configuration file is:

```default
/etc/one/oneks-server.conf
```

When OpenNebula is installed with `ONE_LOCATION` set, the same configuration file is resolved relative to that installation path:

```default
$ONE_LOCATION/etc/oneks-server.conf
```

The file follows the same YAML syntax used by other OpenNebula services.

{{< alert title="Note" type="info" >}}
After modifying this file, restart the OneKS service for the changes to take effect:
```shell
systemctl restart opennebula-ks.service
```
{{< /alert >}}

## Server Configuration

These options define how OneKS reaches OpenNebula and how the OneKS API listens for client requests.

| Attribute                     | Default                              | Description |
|-------------------------------|--------------------------------------|-------------|
| `:one_xmlrpc`                 | `http://localhost:2633/RPC2`         | OpenNebula XML-RPC endpoint used by the OneKS server to talk to the OpenNebula daemon. Change it when OneKS runs outside the Front-end Host or when OpenNebula uses a non-default endpoint. |
| `:one_xmlrpc_tproxy`          | `http://169.254.16.9:2633/RPC2`      | XML-RPC endpoint exposed through the transparent proxy network. Workloads that need to reach OpenNebula through the K8s Cluster router use this address. The matching TPROXY rule must exist in `VAR_LOCATION/remotes/etc/vnm/OpenNebulaNetwork.conf`. |
| `:server`                     | See nested values                    | API listener configuration for the OneKS server. |
| `:server` / `:environment`    | `production`                         | Runtime environment used by the service. Production deployments should keep `production`. |
| `:server` / `:bind`           | `127.0.0.1`                          | IP address where the OneKS API listens. Keep it local when only local CLI or Sunstone access is required. Use a reachable address only when the API must be exposed remotely. |
| `:server` / `:port`           | `10780`                              | TCP port where the OneKS API listens. The default local API endpoint is `http://127.0.0.1:10780/api/v1`. |
| `:subscriber_endpoint`        | `tcp://localhost:2101`               | OpenNebula event subscription endpoint. It must match the event publisher endpoint configured in `oned.conf`. |
| `:subscriber_timeout`         | `10`                                 | Receive timeout, in seconds, for OpenNebula event subscribers. Increase it only if event processing is timing out in a slow or overloaded environment. |

## Kubernetes Configuration

These options are used when OneKS runs Kubernetes commands from the Front-end Host.

| Attribute            | Default                                  | Description |
|----------------------|------------------------------------------|-------------|
| `:kubectl_path`      | `/var/lib/rancher/rke2/bin/kubectl`      | Path to the `kubectl` binary used by OneKS. Change it if `kubectl` is installed in a different location. |
| `:kubeconfig_path`   | `/etc/rancher/rke2/rke2.yaml`            | Kubeconfig file used by `kubectl` operations executed by the service. The file must be readable by the service user. |
| `:k8s_timeout`       | `15`                                     | Timeout, in seconds, while waiting for Kubernetes command execution results. Increase it for slow API servers or busy management clusters. |

## Readiness Check Configuration

The optional `:readiness` section enables the OneKS readiness check service. When it is enabled, users can validate the full deployment placement that will be used by a K8s Cluster before starting a deployment.

The readiness check uses the OneKS appliance dependency defined by the selected control-plane family. It deploys a temporary probe VM from the same appliance and image datastore resolution path used by the real K8s Cluster provisioning flow.

Comment out the full `:readiness` section to disable the readiness check service.

| Attribute                         | Default                                 | Description |
|-----------------------------------|-----------------------------------------|-------------|
| `:readiness` / `:external_url`    | `https://get.rke2.io`                   | Public URL used by the probe VM to validate DNS resolution and outbound internet access. |
| `:readiness` / `:timeout`         | `60`                                    | Maximum time, in seconds, to wait for the probe VM and each readiness check step. |

## Operational Defaults

These values control retry behavior, concurrency, cooldowns, and generated resource names.

| Attribute             | Default | Description |
|-----------------------|---------|-------------|
| `:retries`            | `5`     | Number of retries for operations that can be retried after an aborted call. |
| `:default_cooldown`   | `300`   | Cooldown period, in seconds, after a scale operation. This prevents immediate repeated scale actions. |
| `:concurrency`        | `10`    | Number of worker threads used for K8s Cluster actions. Increase it only when the Front-end, OpenNebula, and the infrastructure can handle more concurrent lifecycle operations. |
| `:base_name`          | `oneks` | Prefix used when OneKS generates names for created resources. Change it to separate resources created by different OneKS environments. |

## Authentication

These options define how the OneKS API authenticates requests and how it authenticates against OpenNebula core.

| Attribute         | Default      | Description |
|-------------------|--------------|-------------|
| `:auth`           | `opennebula` | Authentication driver for incoming OneKS API requests. With `opennebula`, credentials are validated against OpenNebula. |
| `:core_auth`      | `cipher`     | Authentication driver used to communicate with OpenNebula core. Supported values are `cipher` for symmetric token encryption and `x509` for X.509 certificate based token encryption. |
| `:expire_delta`   | `3600`       | Token lifetime window, in seconds. Tune it according to the token expiration policy used by the deployment. |

## Logging

These values configure the OneKS service logging behavior and are defined under the `:log` section of the configuration file.

| Attribute            | Default | Description |
|----------------------|---------|-------------|
| `:log` / `:level`    | `3`     | Log verbosity. Values are `0` for ERROR, `1` for WARNING, `2` for INFO, and `3` for DEBUG. Use `3` for troubleshooting and reduce it in normal production operation if logs are too verbose. |
| `:log` / `:system`   | `file`  | Log destination. Supported values are `file` and `syslog`. |

Service logs are written to the standard OneKS log files. These files are useful to inspect general service activity, runtime errors, and unexpected failures. Service logs files can be found in the following paths:

```default
/var/log/one/oneks.log
/var/log/one/oneks.error
```

Each cluster also has its own lifecycle log file. These per-cluster logs are useful to follow provisioning and monitoring operations for a specific cluster:

```default
/var/log/one/oneks/<cluster_id>.log
```

With `ONE_LOCATION` set, these log files can be found in the below paths:

```default
$ONE_LOCATION/var/oneks.log
$ONE_LOCATION/var/oneks.error
$ONE_LOCATION/var/oneks/<cluster_id>.log
```

## Service Management

OneKS is managed through the packaged systemd unit `opennebula-ks.service`.

Use the following command to start the OneKS service:

```shell
systemctl start opennebula-ks.service
```

Use this command to check the current status of the service:

```shell
systemctl status opennebula-ks.service
```

Use this command to stop the OneKS service:

```shell
systemctl stop opennebula-ks.service
```

Use this command to restart the service after configuration changes or when troubleshooting:

```shell
systemctl restart opennebula-ks.service
```

When debugging service errors, always check the systemd journal for the OneKS unit:

```shell
journalctl -u opennebula-ks.service
```

## Related Configuration

OneKS relies on several OpenNebula services and network endpoints:

| Area                 | What to Check |
|----------------------|---------------|
| OneGate              | OneGate must be reachable by the Seed VM during provisioning. |
| OpenNebula XML-RPC   | `:one_xmlrpc` must point to the OpenNebula daemon endpoint used by the OneKS server. |
| TPROXY               | `:one_xmlrpc_tproxy` must match the XML-RPC endpoint exposed through the transparent proxy network. |
| OpenNebula events    | `:subscriber_endpoint` must match the event endpoint configured in `oned.conf`. |
| Service logs         | Use service logs for daemon issues and per-cluster logs for provisioning, scaling, upgrade, and deletion workflows. |

## Example Configuration

```yaml
################################################################################
# Server Configuration
################################################################################

:one_xmlrpc: http://localhost:2633/RPC2
:one_xmlrpc_tproxy: http://169.254.16.9:2633/RPC2

:server:
  :environment: production
  :bind: 127.0.0.1
  :port: 10780

:subscriber_endpoint: 'tcp://localhost:2101'
:subscriber_timeout: 10

################################################################################
# Kubernetes Configuration
################################################################################

:kubectl_path: '/var/lib/rancher/rke2/bin/kubectl'
:kubeconfig_path: '/etc/rancher/rke2/rke2.yaml'
:k8s_timeout: 15

################################################################################
# Cluster Readiness Check
################################################################################

:readiness:
  :external_url: 'https://get.rke2.io'
  :timeout: 60

################################################################################
# Defaults
################################################################################

:retries: 5
:default_cooldown: 300
:concurrency: 10
:base_name: 'oneks'

################################################################################
# Auth
################################################################################

:auth: opennebula
:core_auth: cipher
:expire_delta: 3600

################################################################################
# Log
################################################################################

:log:
  :level: 3
  :system: file
```
