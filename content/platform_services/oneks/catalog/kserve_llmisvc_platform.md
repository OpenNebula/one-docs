---
title: "KServe LLMInferenceService Platform"
linkTitle: "KServe LLMInferenceService"
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

## Usage and Configuration

To install this application, follow the [Managing Applications Guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalogue ID shown above.

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

After installation, use the K8s Cluster kubeconfig to inspect the platform resources and deploy your KServe runtime and `LLMInferenceService` objects. The following example assumes that the application was installed with `kserve` as both the release name and target namespace:

```shell
KUBECONFIG=./kubeconfig kubectl get pods -n kserve
KUBECONFIG=./kubeconfig kubectl api-resources | grep -i llminference
```
