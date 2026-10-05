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

| Attribute | Value |
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

## Usage and Configuration

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above.

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

After installation, use the K8s Cluster kubeconfig to inspect the monitoring workloads. The following example assumes that the application was installed with `prometheus` as the release name and `monitoring` as the target namespace:

```shell
KUBECONFIG=./kubeconfig kubectl get pods -n monitoring
```
