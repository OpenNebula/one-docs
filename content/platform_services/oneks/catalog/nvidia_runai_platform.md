---
title: "NVIDIA Run:ai Platform"
linkTitle: "NVIDIA Run:ai Platform"
date: "2026-10-01"
description: "NVIDIA Run:ai control-plane application distributed with OneKS."
categories:
tags:
weight: "4"
type: docs
---

## Description and Purpose

The [**NVIDIA Run:ai Platform**](https://docs.nvidia.com/run-ai/self-hosted/index.html) installs the Run:ai control plane with managed ingress, GPU, monitoring, storage, certificate, and CA-distribution components. Use it to provide centralized Run:ai scheduling and administration services for AI workloads.

| **Attribute** | **Value** |
|-----------|-------|
| Application ID | `905abc6e-7cea-4a0a-bc84-ad215a3fc1fe` |
| Helm repository | `https://helm.ngc.nvidia.com/nvidia/runai` |
| Helm chart | `control-plane` |
| Version | `v2.25` |

OneKS installs Longhorn, trust-manager, NVIDIA GPU Operator, Prometheus, and the HAProxy Kubernetes Ingress Controller as managed component dependencies.

## Parameters

All application-specific parameters are mandatory:

| **Parameter** | **Type** | **Sensitive** | **Description** |
|-----------|------|-----------|-------------|
| `domain` | String | No | Fully qualified domain name used to access the Run:ai control plane. |
| `adminUsername` | String | No | Username for the initial Run:ai administrator account. |
| `registryEmail` | String | No | Email address stored in the NVIDIA registry pull secret. |
| `adminPassword` | String | Yes | Password for the initial Run:ai administrator account. |
| `ngcApiKey` | String | Yes | NVIDIA NGC API key used to pull Run:ai images and charts. |

Sensitive values are used to create Kubernetes Secrets and are not displayed as plain text in normal application output.

## Usage and Configuration

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above and provide the application-specific parameters described in the previous section.

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

### Connect to the Run:ai User Interface

After the application reaches `ready`, retrieve the ingress address. The following example assumes that the application was installed with `runai` as both the release name and target namespace:

```shell
KUBECONFIG=./kubeconfig kubectl get ingress -n runai runai-ingress \
  -o json | jq -r '.status.loadBalancer.ingress[0].ip'
```

Map that address to the configured domain on the workstation from which you will access the user interface:

```shell
echo '<ingress_ip> <domain>' | sudo tee -a /etc/hosts
```

Open `https://<domain>` and sign in with `adminUsername` and `adminPassword`.
