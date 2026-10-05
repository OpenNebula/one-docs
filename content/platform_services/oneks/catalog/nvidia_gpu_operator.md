---
title: "NVIDIA GPU Operator"
linkTitle: "NVIDIA GPU Operator"
date: "2026-10-01"
description: "NVIDIA GPU Operator application distributed with OneKS."
categories:
tags:
weight: "2"
type: docs
---

## Description and Purpose

The [**NVIDIA GPU Operator**](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/) deploys the NVIDIA GPU software stack required to expose and manage NVIDIA GPUs in Kubernetes. Use it on K8s Clusters with NVIDIA GPU worker nodes so workloads can request GPU resources through Kubernetes.

| Attribute | Value |
|-----------|-------|
| Application ID | `8cb0d29e-4521-4bcb-a977-786df097d162` |
| Helm repository | `https://helm.ngc.nvidia.com/nvidia` |
| Helm chart | `gpu-operator` |
| Version | `v26.3.1` |

## Parameters

This application has no application-specific user inputs. During installation, provide the standard release name, target namespace, and namespace-creation option.

The built-in Helm values enable the NVIDIA Container Device Interface integration for the NRI plugin:

```yaml
cdi:
  nriPluginEnabled: true
```

## Usage and Configuration

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalogue ID shown above.

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

After installation, use the K8s Cluster kubeconfig to verify the operator workloads. The following example assumes that the application was installed with `gpu-operator` as both the release name and target namespace:

```shell
KUBECONFIG=./kubeconfig kubectl get pods -n gpu-operator
```

After the release reaches `ready`, verify that GPU resources are advertised by the intended worker nodes:

```shell
KUBECONFIG=./kubeconfig kubectl get nodes \
  -o custom-columns=NAME:.metadata.name,GPUS:.status.capacity.nvidia\.com/gpu
```

For GPU Operator configuration and validation procedures, follow the upstream documentation linked above.
