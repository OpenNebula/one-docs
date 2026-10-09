---
title: "Prometheus"
linkTitle: "Prometheus"
date: "2026-10-01"
description: "Prometheus monitoring and time-series database application distributed with OneKS."
categories:
tags:
weight: "3"
type: docs
---

## Description and Purpose

The [**Prometheus**](https://prometheus.io/docs/introduction/overview/) application installs the `kube-prometheus-stack` chart to collect Kubernetes metrics and store them as time-series data. Use it to monitor K8s Cluster components and workloads and to provide a metrics source for observability integrations.

| **Attribute** | **Value** |
|-----------|-------|
| Application ID | `d511b694-d868-4e40-8224-fdf6a0ca3383` |
| Helm repository | `https://prometheus-community.github.io/helm-charts` |
| Helm chart | `kube-prometheus-stack` |
| Version | `v87.12.2` |

## Parameters

This application has no application-specific user inputs. During installation, provide the standard release name, target namespace, and namespace-creation option.

Grafana is disabled in the built-in Helm values:

```yaml
grafana:
  enabled: false
```

## Installation

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the installation wizard, set the release name and target namespace. The following example uses `prometheus` for both values and enables namespace creation:

{{< image
  path="/images/oneks/light/prometheus_configuration.png"
  pathDark="/images/oneks/dark/prometheus_configuration.png"
  alt="Prometheus release configuration" align="center" width="90%" mb="20px"
>}}

After finishing the wizard, the release appears in the K8s Cluster **Applications** tab. Open the release to inspect its state and chart version:

{{< image
  path="/images/oneks/light/prometheus_installed.png"
  pathDark="/images/oneks/dark/prometheus_installed.png"
  alt="Prometheus installed application" align="center" width="90%" mb="20px"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
Install the application with its catalog ID:

```shell
oneks install app d511b694-d868-4e40-8224-fdf6a0ca3383 \
  --cluster-id <CLUSTER_ID> \
  --release-name prometheus \
  --target-namespace prometheus \
  --create-namespace
```

Inspect the installed release until its state changes to `ready`:

```shell
oneks show cluster <CLUSTER_ID> --app prometheus
```
{{% /tab %}}

{{% tab header="API"%}}
Install the application through the OneKS API:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "d511b694-d868-4e40-8224-fdf6a0ca3383",
    "release_name": "prometheus",
    "target_namespace": "prometheus",
    "create_namespace": true,
    "user_input_values": {}
  }'
```

The request returns `202 Accepted`. Inspect the installed release until its state changes to `ready`:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications/prometheus
```
{{% /tab %}}

{{< /tabpane >}}

## Usage and Configuration

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

Use this kubeconfig when running the verification commands below.

## Verify the Installation

After the release reaches `ready`, verify that all Prometheus workloads are running. The following output assumes that the application was installed with `prometheus` as both the release name and target namespace:

```shell
$ KUBECONFIG=./kubeconfig kubectl get pods -n prometheus
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          2m
prometheus-kube-prometheus-operator-869fb87b59-xb5c9     1/1     Running   0          2m9s
prometheus-kube-state-metrics-79ff744748-bwgnl           1/1     Running   0          2m9s
prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          2m
prometheus-prometheus-node-exporter-22zl4                1/1     Running   0          2m9s
prometheus-prometheus-node-exporter-2l4nv                1/1     Running   0          2m9s
prometheus-prometheus-node-exporter-wg76q                1/1     Running   0          2m9s
```

Query the Prometheus readiness endpoint through the Kubernetes API proxy:

```shell
$ KUBECONFIG=./kubeconfig kubectl get --raw \
  "/api/v1/namespaces/prometheus/services/http:prometheus-kube-prometheus-prometheus:9090/proxy/-/ready"
Prometheus Server is Ready.
```
