---
title: "KServe LLMInferenceService Platform"
linkTitle: "KServe"
date: "2026-10-01"
description: "KServe platform for deploying LLMInferenceService workloads with managed routing and model caching."
categories:
tags:
weight: "1"
type: docs
---

## Description and Purpose

The [**KServe LLMInferenceService Platform**](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview) installs the KServe runtime configuration for generative-inference workloads. It provides Gateway API routing through Envoy AI Gateway, the LeaderWorkerSet operator for multi-node inference workloads, and node-local model caching.

| **Attribute** | **Value** |
|-----------|-------|
| Application ID | `8323494d-06ad-48e1-8ebe-779a2a91f17d` |
| Helm chart | `oci://ghcr.io/kserve/charts/kserve-runtime-configs` |
| Version | `v0.20.0` |

The application requires the `cert-manager` installation provided by Cluster API. OneKS also installs the following managed components before the root chart:

* KServe LLMInferenceService CRDs
* Envoy Gateway and Envoy AI Gateway
* LeaderWorkerSet Operator
* KServe LLMInferenceService resources
* KServe LocalModel resources

## Parameters

This application has no application-specific user inputs. During installation, provide the standard release name, target namespace, and namespace-creation option.

The built-in Helm values enable `llmisvcConfigs` and disable the chart's default `servingruntime`. Define the serving runtime required by your inference workload after installation.

## Installation

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the installation wizard, set the release name and target namespace. The following example uses `kserve` for both values and enables namespace creation:

{{< image
  path="/images/oneks/light/kserve_configuration.png"
  pathDark="/images/oneks/dark/kserve_configuration.png"
  alt="KServe release configuration" align="center" width="90%" mb="20px"
>}}

After finishing the wizard, the release appears in the K8s Cluster **Applications** tab. Open the release to inspect its state and chart version:

{{< image
  path="/images/oneks/light/kserve_installed.png"
  pathDark="/images/oneks/dark/kserve_installed.png"
  alt="KServe installed application" align="center" width="90%" mb="20px"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
Install the application with its catalog ID:

```shell
oneks install app 8323494d-06ad-48e1-8ebe-779a2a91f17d \
  --cluster-id <CLUSTER_ID> \
  --release-name kserve \
  --target-namespace kserve \
  --create-namespace
```

Inspect the installed release until its state changes to `ready`:

```shell
oneks show cluster <CLUSTER_ID> --app kserve
```
{{% /tab %}}

{{% tab header="API"%}}
Install the application through the OneKS API:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "8323494d-06ad-48e1-8ebe-779a2a91f17d",
    "release_name": "kserve",
    "target_namespace": "kserve",
    "create_namespace": true,
    "user_input_values": {}
  }'
```

The request returns `202 Accepted`. Inspect the installed release until its state changes to `ready`:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications/kserve
```
{{% /tab %}}

{{< /tabpane >}}

## Usage and Configuration

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

Use the K8s Cluster kubeconfig to deploy the serving runtime and `LLMInferenceService` objects required by your inference workload.

## Verify the Installation

After the release reaches `ready`, verify that the KServe controllers are running. The following output assumes that the application was installed with `kserve` as both the release name and target namespace:

```shell
$ KUBECONFIG=./kubeconfig kubectl get pods -n kserve
NAME                                                  READY   STATUS    RESTARTS   AGE
kserve-localmodel-controller-manager-795f666c-bpq2f   1/1     Running   0          4m39s
llmisvc-controller-manager-856bfcccd6-tjtqd           1/1     Running   0          5m5s
```

Verify that all installed `LLMInferenceServiceConfig` resources report `True` in the `READY` column:

```shell
$ KUBECONFIG=./kubeconfig kubectl get llminferenceserviceconfig -n kserve
NAME                                             READY   REASON   AGE
kserve-config-llm-decode-template                True             4m9s
kserve-config-llm-decode-worker-data-parallel    True             4m9s
kserve-config-llm-prefill-template               True             4m9s
kserve-config-llm-prefill-worker-data-parallel   True             4m9s
kserve-config-llm-router-route                   True             4m9s
kserve-config-llm-scheduler                      True             4m9s
kserve-config-llm-scheduler-latency-predictor    True             4m9s
kserve-config-llm-template                       True             4m9s
kserve-config-llm-tracing                        True             4m9s
kserve-config-llm-worker-data-parallel           True             4m9s
```
