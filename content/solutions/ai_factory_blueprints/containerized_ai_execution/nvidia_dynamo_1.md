---
title: Deployment of NVIDIA Dynamo
linkTitle: Inferencing with NVIDIA Dynamo 1
weight: 6
tags: ['AI','Kubernetes','NVIDIA']
---

<a id="nvidia_dynamo"></a>

[NVIDIA&reg; Dynamo](https://docs.nvidia.com/dynamo/latest/index.html) provides an inference framework for serving AI models with backends such as vLLM, TensorRT-LLM, and SGLang. Its Kubernetes Operator manages the frontend and model workers described in a DynamoGraphDeployment (DGD).

This guide continues from [AI-ready Kubernetes 1]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s_1" %}}). You will deploy **Dynamo 1.5.0** on the OneKS Cluster created there, serving **Qwen/Qwen3-0.6B** with one aggregated vLLM worker. The same worker performs both prompt processing (prefill) and token generation (decode), using **one GPU**. A separate CPU-only frontend provides the API.

## Before Starting

Complete the preceding guide, including its successful VectorAdd test and cleanup. Keep the OneKS Cluster, its GPU worker, and the NVIDIA GPU Operator running. Stop any other inference workload that reserves the worker's GPU.

Use the `kubeconfig` file copied from OneKS, as in the preceding guide:

```shell
export KUBECONFIG="$PWD/kubeconfig"
kubectl get nodes
```

Run the commands below from a machine with kubectl, Helm, curl, and jq installed. The Cluster nodes need access to NVIDIA's container registry and Hugging Face to download the runtime and model. This is a small demonstration deployment; the resource settings below are starting points for Qwen3-0.6B, not production sizing.

These instructions assume a fresh Dynamo installation. If the Cluster already runs a Dynamo operator, coordinate with its administrator before proceeding: the operator and its custom resource definitions are Cluster-wide. This guide is not an in-place upgrade procedure for an older Dynamo installation.

## Step 1: Check GPU and Driver Compatibility

Check the GPU capacity advertised by Kubernetes:

```shell
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

Expected output:

```default
NAME                                                 GPU
controlplane-general-standalone-44c7fcc86fd3-kbkb4   <none>
nodegroup-general-large-7fc21d43cda5-hv9j2-xs267     1
```

The GPU worker should advertise `1`. This reports allocatable capacity, not unused capacity; inspect the worker's allocated resources to confirm another pod is not already reserving it:

```shell
kubectl describe node <gpu-worker-node-name>
```

Check the installed driver from the GPU Operator's driver pod on that worker:

```shell
kubectl -n gpu-operator get pods -l app=nvidia-driver-daemonset -o wide
```

Expected output:

```default
NAME                            READY   STATUS    RESTARTS   AGE   IP          NODE                                               NOMINATED NODE   READINESS GATES
nvidia-driver-daemonset-bxbz9   1/1     Running   0          28h   10.42.1.8   nodegroup-general-large-7fc21d43cda5-hv9j2-xs267   <none>           <none>
```


```
kubectl -n gpu-operator exec <driver-pod-name> -c nvidia-driver-ctr -- \
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
```

From the above example, this command would be:

```
kubectl -n gpu-operator exec nvidia-driver-daemonset-bxbz9 -c nvidia-driver-ctr -- \
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
```

Expected output:

```default
name, driver_version, memory.total [MiB]
NVIDIA L40S, 595.91.07, 46068 MiB
```

NVIDIA's [Dynamo compatibility matrix](https://docs.nvidia.com/dynamo/latest/reference/compatibility) lists **CUDA 13.0 and driver branch 580 or newer** for the Dynamo 1.5.0 vLLM runtime. Confirm that the installed driver meets this requirement before continuing. The earlier VectorAdd test uses CUDA 12.5 and alone does not establish compatibility with this runtime. If necessary, update the driver through the existing GPU Operator installation and repeat GPU validation.

The preceding OneKS guide enables CDI through the GPU Operator's NRI plugin. The manifest below requests the GPU through `nvidia.com/gpu`; no explicit runtime class is needed.

## Step 2: Install the Dynamo Platform

### Storage and Platform Services

The [Dynamo 1.5.0 platform chart](https://helm.ngc.nvidia.com/nvidia/ai-dynamo/charts/dynamo-platform-1.5.0.tgz) defaults to Kubernetes service discovery, with bundled etcd and NATS disabled. This example uses those defaults and needs no PersistentVolumeClaims or additional storage provisioner. Leave the Cluster's existing StorageClasses unchanged.

The model is downloaded into the worker's ephemeral storage and may need to be downloaded again when the pod is replaced. Allow disk space for the runtime image, model files, and caches on the worker. For repeated deployments or larger models, configure a persistent model cache using a storage provider appropriate for your Cluster.

Create `dynamo-values.yaml` with the platform settings:

```yaml
global:
  etcd:
    install: false
  nats:
    install: false
dynamo-operator:
  discoveryBackend: kubernetes
```

### Optional Control-plane Placement

For this small lab, prefer placing the Dynamo operator on the control-plane node **only if your OneKS configuration and Cluster policy permit application pods there**, and enough CPU and RAM remain available for Kubernetes itself. The OneKS guide does not establish that permission. Otherwise, keep the values above and let Kubernetes schedule the operator on an eligible worker; it does not request a GPU.

Inspect the control-plane node before choosing placement:

```shell
kubectl get nodes -l node-role.kubernetes.io/control-plane -o wide
kubectl describe node <control-plane-node-name>
```

If application scheduling is permitted, add the following under `dynamo-operator` in `dynamo-values.yaml`. The affinity prefers the control plane but allows fallback to a worker. The toleration below matches the standard control-plane `NoSchedule` taint; use only tolerations for taints your Cluster policy allows. Do not remove node taints to make this example schedule.

```yaml
  controllerManager:
    tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
    affinity:
      nodeAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
                - key: node-role.kubernetes.io/control-plane
                  operator: Exists
```

Only the operator is installed as a platform workload here. The graph's frontend and GPU worker use their own pod specifications and retain normal scheduling.

### Install and Verify

Install the pinned platform chart:

```shell
helm install dynamo-platform \
  https://helm.ngc.nvidia.com/nvidia/ai-dynamo/charts/dynamo-platform-1.5.0.tgz \
  --namespace dynamo-system --create-namespace \
  --values dynamo-values.yaml \
  --wait --timeout 10m
```

The Cluster-wide operator applies its CRDs through its initialization container; there is no separate CRD Helm release to install. See NVIDIA's [installation guide](https://docs.nvidia.com/dynamo/dev/kubernetes/installation/install-dynamo) for this lifecycle.

Verify the operator and DGD API:

```shell
kubectl -n dynamo-system get deploy,pods,svc -o wide
kubectl wait --for=condition=Established \
  crd/dynamographdeployments.nvidia.com --timeout=120s
kubectl explain dynamographdeployment.spec --api-version=nvidia.com/v1beta1
```

The operator should be ready before you apply a graph. This configuration does not create etcd or NATS pods.

## Step 3: Configure Hugging Face Access (Optional)

Qwen3-0.6B is a public model, so the example can download it without a token. If you need authenticated downloads, create a read token on the [Hugging Face tokens page](https://huggingface.co/settings/tokens), then create the Secret in the same namespace as the graph:

```shell
read -rsp 'Hugging Face read token: ' HF_TOKEN
printf '\n'
kubectl -n dynamo-system create secret generic hf-token-secret \
  --from-literal=HF_TOKEN="$HF_TOKEN"
unset HF_TOKEN
```

Use the key **`HF_TOKEN`**, which becomes the environment variable consumed by Hugging Face clients. The graph references this Secret with `envFrom` and `optional: true`, so it also runs when you skip this step. Do not save the token in the guide or a manifest committed to source control.

## Step 4: Deploy the Aggregated Inference Graph

Save the following as `agg_custom.yaml`. It follows NVIDIA's [aggregated vLLM template](https://github.com/ai-dynamo/dynamo/blob/v1.5.0/examples/backends/vllm/deploy/agg.yaml), using the `v1beta1` API's `components` list and standard container resources inside `podTemplate`.

```yaml
apiVersion: nvidia.com/v1beta1
kind: DynamoGraphDeployment
metadata:
  name: vllm-agg
  namespace: dynamo-system
spec:
  components:
    - name: Frontend
      type: frontend
      replicas: 1
      podTemplate:
        spec:
          containers:
            - name: main
              image: nvcr.io/nvidia/ai-dynamo/vllm-runtime:1.5.0
              envFrom:
                - secretRef:
                    name: hf-token-secret
                    optional: true
              resources:
                requests:
                  cpu: "250m"
                  memory: "512Mi"
                limits:
                  cpu: "1"
                  memory: "2Gi"
    - name: worker
      type: worker
      replicas: 1
      podTemplate:
        spec:
          containers:
            - name: main
              image: nvcr.io/nvidia/ai-dynamo/vllm-runtime:1.5.0
              command: ["python3", "-m", "dynamo.vllm"]
              args:
                - --model
                - Qwen/Qwen3-0.6B
                - --max-model-len
                - "4096"
                - --gpu-memory-utilization
                - "0.5"
              envFrom:
                - secretRef:
                    name: hf-token-secret
                    optional: true
              resources:
                requests:
                  cpu: "2"
                  memory: "4Gi"
                  ephemeral-storage: "4Gi"
                  nvidia.com/gpu: 1
                limits:
                  cpu: "4"
                  memory: "8Gi"
                  nvidia.com/gpu: 1
```

The operator configures the frontend command, discovery, and health checks. Only the worker requests a GPU. Its single replica handles both inference phases without an inter-GPU transfer configuration.

The graph requests 2.25 CPUs and 4.5 GiB of RAM in total, in addition to the operator and existing Cluster services. Requests reserve scheduling capacity; allow headroom up to the limits for startup and model loading. The 4,096-token context limit and 50% GPU memory target keep this demonstration modest on the preceding guide's L40S. Smaller GPUs or larger workloads may need different settings. If the worker is killed for exceeding memory, inspect its logs and increase the limit and available node memory as needed.

Validate the manifest against the installed API, then deploy it:

```shell
kubectl apply --dry-run=server -f agg_custom.yaml
kubectl apply -f agg_custom.yaml
kubectl -n dynamo-system get dynamographdeployment vllm-agg
kubectl -n dynamo-system get pods,svc -o wide
```

The first startup can take several minutes while images and model files download. Wait for both graph pods to become ready. Check pod events and logs if progress stops:

```shell
kubectl -n dynamo-system describe pod <worker-pod-name>
kubectl -n dynamo-system logs <worker-pod-name> -c main --tail=100
```

A `Pending` worker may indicate an occupied GPU or insufficient CPU, RAM, or ephemeral storage. Check the pod's scheduling events before changing resource requests. A `Running` pod alone does not prove that the model is ready; test the API next.

## Step 5: Query the API Locally

Forward the frontend Service to your local machine. Leave this command running in its terminal:

```shell
kubectl -n dynamo-system port-forward svc/vllm-agg-frontend 9000:8000
```

In a second terminal, list the available models:

```shell
curl --fail-with-body http://localhost:9000/v1/models | jq .
```

The `data` array should contain a model with the ID `Qwen/Qwen3-0.6B`. If it is empty, wait for the model loading to finish and retry.

When the model is loaded, you should get a response like this:

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen3-0.6B",
      "object": "model",
      "created": 1790190691,
      "owned_by": "nvidia",
      "context_window": 4096
    }
  ]
}
```

Submit an inference request:

```shell
curl --fail-with-body http://localhost:9000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "What is OpenNebula?",
    "stream": false,
    "max_tokens": 300
  }' | jq .
```

A successful response contains generated text in `choices[0].text` and token counts in `usage`. Text varies between requests and may include the model's reasoning output. A successful inference request should appear like the following example:

```json
{
  "id": "cmpl-a9b5fae8-d032-4dc7-8a48-beed1bfc927f",
  "choices": [
    {
      "text": " What are its main features and benefits? What are the key areas where it is used? What are the future prospects of OpenNebula?\n\n**Answer in 100 words or less.**\n\n**Answer:**\n\nOpenNebula is a distributed storage system designed for managing virtualized environments. It offers features like dynamic scaling, resource allocation, and disaster recovery. Key benefits include high availability and scalability. Used in cloud computing, data centers, and virtualization infrastructures. Future prospects involve integration with AI and automation.\n\n**Answer:**\nOpenNebula is a distributed storage system for managing virtualized environments. It provides dynamic resource allocation and disaster recovery. Benefits include high availability and scalability. Used in cloud computing, data centers, and virtualization. Future prospects include integration with AI and automation.\n\n**Answer:**\nOpenNebula is a distributed storage system designed for managing virtualized environments. It provides dynamic resource allocation and disaster recovery. Key benefits include high availability and scalability. Used in cloud computing, data centers, and virtualization infrastructures. Future prospects include integration with AI and automation.\n\n**Answer:**\nOpenNebula is a distributed storage system for managing virtualized environments. It offers dynamic resource allocation and disaster recovery. Key benefits include high availability and scalability. Used in cloud computing, data centers, and virtualization infrastructures. Future prospects include integration with AI and automation. (100 words)**\n**Answer:**\nOpenNebula is a distributed storage",
      "index": 0,
      "finish_reason": "length"
    }
  ],
  "created": 1790190800,
  "model": "Qwen/Qwen3-0.6B",
  "system_fingerprint": null,
  "object": "text_completion",
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 300,
    "total_tokens": 307,
    "prompt_tokens_details": {
      "audio_tokens": null,
      "cached_tokens": 0
    }
  }
}
```

To test streaming, use `stream: true` and curl's `--no-buffer` option:

```shell
curl --fail-with-body --no-buffer http://localhost:9000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "What is OpenNebula?",
    "stream": true,
    "max_tokens": 300
  }'
```

The response arrives as server-sent events with `data:` records, ending with `data: [DONE]`. The port-forward binds to localhost by default; this test does not expose a public inference endpoint. Stop it with **Ctrl-C** when finished.

## Undeployment

Delete the graph while the Dynamo operator is still running so it can clean up the resources it manages:

```shell
kubectl -n dynamo-system delete dynamographdeployment vllm-agg \
  --wait=true --timeout=5m
kubectl -n dynamo-system get pods,deploy,svc
```

Wait until the `vllm-agg` pods and Services have disappeared. If this is the only Dynamo workload and you no longer need the platform, uninstall it and remove this guide's namespace:

```shell
helm uninstall dynamo-platform --namespace dynamo-system --wait --timeout 5m
kubectl delete namespace dynamo-system
```

Deleting the namespace also removes the optional Hugging Face Secret. The model cache is ephemeral, so there are no model PVCs to delete in this example.

Cluster-wide Dynamo CRDs can remain after uninstalling the platform. Leave them in place if other Dynamo installations use them. For a complete removal from a dedicated lab Cluster, inspect them and delete only the Dynamo CRDs after confirming that no Dynamo custom resources are still needed:

```shell
kubectl get crd -o name | grep -E '^customresourcedefinition.apiextensions.k8s.io/dynamo.*\.nvidia\.com$'
# Repeat for each reviewed Dynamo CRD:
kubectl delete crd <dynamo-crd-name>
```

Deleting a CRD also deletes its custom resources across all namespaces. Keep the OneKS Cluster and NVIDIA GPU Operator available for subsequent guides.

## Next Steps

You can continue with the [NVIDIA KAI Scheduler guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler" %}}) to explore scheduling AI workloads on Kubernetes.
