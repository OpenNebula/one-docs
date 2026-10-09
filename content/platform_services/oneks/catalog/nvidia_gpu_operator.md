---
title: "NVIDIA GPU Operator"
linkTitle: "GPU Operator"
date: "2026-10-01"
description: "NVIDIA GPU Operator application distributed with OneKS."
categories:
tags:
weight: "2"
type: docs
---

## Description and Purpose

The [**NVIDIA GPU Operator**](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/) deploys the NVIDIA GPU software stack required to expose and manage NVIDIA GPUs in Kubernetes. Use it on K8s Clusters with NVIDIA GPU worker nodes so workloads can request GPU resources through Kubernetes.

| **Attribute** | **Value** |
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

## Installation

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the installation wizard, set the release name and target namespace. The following example uses `gpu` for both values and enables namespace creation:

{{< image
  path="/images/oneks/light/nvidia_gpu_operator_configuration.png"
  pathDark="/images/oneks/dark/nvidia_gpu_operator_configuration.png"
  alt="NVIDIA GPU Operator release configuration" align="center" width="90%" mb="20px"
>}}

After finishing the wizard, the release appears in the K8s Cluster **Applications** tab. Wait until its state changes to `ready`:

{{< image
  path="/images/oneks/light/nvidia_gpu_operator_installed.png"
  pathDark="/images/oneks/dark/nvidia_gpu_operator_installed.png"
  alt="NVIDIA GPU Operator installed application" align="center" width="90%" mb="20px"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
Install the application with its catalog ID:

```shell
oneks install app 8cb0d29e-4521-4bcb-a977-786df097d162 \
  --cluster-id <CLUSTER_ID> \
  --release-name gpu \
  --target-namespace gpu \
  --create-namespace
```

Inspect the installed release until its state changes to `ready`:

```shell
oneks show cluster <CLUSTER_ID> --app gpu
```
{{% /tab %}}

{{% tab header="API"%}}
Install the application through the OneKS API:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "8cb0d29e-4521-4bcb-a977-786df097d162",
    "release_name": "gpu",
    "target_namespace": "gpu",
    "create_namespace": true,
    "user_input_values": {}
  }'
```

The request returns `202 Accepted`. Inspect the installed release until its state changes to `ready`:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications/gpu
```
{{% /tab %}}

{{< /tabpane >}}

## Usage and Configuration

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

Use this kubeconfig when running the verification commands below. For additional GPU Operator configuration and validation procedures, follow the upstream documentation linked above.

## Verify the Installation

After the release reaches `ready`, verify that all operator workloads are running. The following output assumes that the application was installed with `gpu` as both the release name and target namespace:

```shell
$ KUBECONFIG=./kubeconfig kubectl get pods -n gpu
NAME                                                 READY   STATUS    RESTARTS   AGE
gpu-node-feature-discovery-gc-9c447fb86-tsq7l        1/1     Running   0          2m1s
gpu-node-feature-discovery-master-7468976f6b-pjlxt   1/1     Running   0          2m1s
gpu-node-feature-discovery-worker-786zk              1/1     Running   0          2m1s
gpu-node-feature-discovery-worker-9rltp              1/1     Running   0          2m1s
gpu-node-feature-discovery-worker-xqhwz              1/1     Running   0          2m1s
gpu-operator-7946976c5c-s8dmf                        1/1     Running   0          2m1s
```

Verify that GPU resources are advertised by the intended worker nodes:

```shell
KUBECONFIG=./kubeconfig kubectl get nodes \
  -o custom-columns=NAME:.metadata.name,GPUS:.status.capacity.nvidia\.com/gpu
```
