---
title: Deployment of the NVIDIA KAI Scheduler
linkTitle: Scheduling with NVIDIA KAI
weight: 3
tags: ['AI', 'Kubernetes', 'NVIDIA']
---


<a id="nvidia_kai_scheduler"></a>

[NVIDIA&reg; KAI Scheduler](https://github.com/kai-scheduler/KAI-Scheduler) schedules AI workloads using queues, resource quotas, priorities, and GPU sharing. It runs alongside Kubernetes' default scheduler; workloads select KAI explicitly.

This guide continues from [AI-ready Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}). You will install **KAI v0.17.0** on the OneKS Cluster and run two small vLLM inference services on its **single NVIDIA L40S**. Both services use **Qwen/Qwen3-0.6B**, allowing you to validate fractional GPU scheduling and query each service independently.

## Before Starting

To follow this guide, you must have a working deployment of OpenNebula {{< version >}} and a hypervisor node on a Host with at least one [compatible NVIDIA GPU]({{% relref "software/release_information/release_notes/platform_notes/#nvidia" %}}). [PCI passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) must be properly configured to allow OpenNebula-managed VMs to directly access the GPU. 

To meet these prerequisites we recommend completing the relevant OneDeploy AI Factory Deployment before starting this guide:

* [OneDeploy AI Factory Deployment with On-premises Resources]({{% relref "solutions/ai_factory_blueprints/deployment/cd_on-premises/" %}})
* [OneDeploy AI Factory Deployment with Cloud Resources]({{% relref "solutions/ai_factory_blueprints/deployment/cd_cloud/" %}})

You must also complete the OneKS K8s Cluster provisioning and NVIDIA GPU Operator deployment in the [AI-ready Kubernetes Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}), including the VectorAdd validation and cleanup. Keep the OneKS Cluster, its GPU worker, and the NVIDIA GPU Operator running. Terminate any other inference workload that reserves the worker's GPU.

These examples target the [AI-ready Kubernetes Guide's]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}) Large Worker Nodes flavour (8 vCPUs, 16 GB RAM) with one L40S attached through PCI passthrough. Run commands from a machine with kubectl, Helm, curl, and jq. The nodes need access to GitHub Container Registry, Docker Hub, and Hugging Face. Allow worker disk space for the container image, two model caches, and temporary files; model storage is ephemeral in this example.

This is a fresh installation procedure. Check for an existing KAI release with `helm list -A` before proceeding. If KAI is already installed, reuse it only after checking its version and configuration with the Cluster administrator. Older releases require the upstream [migration instructions](https://github.com/kai-scheduler/KAI-Scheduler/tree/v0.17.0/docs/migrationguides).

This guide was tested on the same validation environment detailed in the [AI-ready K8s Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s/#validated-environment" %}}). The following procedures may need to be adjusted for different hardware configurations.

## Step 1: Check the GPU Worker

First, set up the `kubeconfig` file copied from OneKS in the [AI-ready K8s Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s/#step-5-copy-the-kubeconfig" %}}):

```shell
export KUBECONFIG="$PWD/kubeconfig"
kubectl get nodes
```

Inspect the GPU capacity and memory reported by GPU Feature Discovery:

```shell
kubectl get nodes -l nvidia.com/gpu.present=true \
  -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu,MODEL:.metadata.labels.nvidia\.com/gpu.product,MEMORY-MiB:.metadata.labels.nvidia\.com/gpu.memory'
```

Replace `<gpu_worker_node_name>` with the node name given by the previous command:

```shell
kubectl describe node <gpu_worker_node_name>
```

Expect one GPU with the `NVIDIA-L40S` product label. Allocatable capacity does not mean unused capacity: check the node's allocated resources and stop workloads holding the GPU before continuing. Keep the GPU Operator's normal device configuration; do not enable device-plugin time-slicing or MPS for this example.

The workloads below use the pinned [vLLM v0.28.0 image](https://github.com/vllm-project/vllm/releases/tag/v0.28.0), which ships CUDA 13.0. Check the installed driver:

```shell
kubectl -n gpu-operator get pods -l app=nvidia-driver-daemonset -o wide
```

Replace `<driver_pod_name>` with the driver pod name given by the previous command:

```shell
kubectl -n gpu-operator exec <driver_pod_name> -c nvidia-driver-ctr -- \
  nvidia-smi --query-gpu=uuid,name,driver_version,memory.total --format=csv
```

Use driver branch **580 or newer**, as required by NVIDIA's [CUDA 13 compatibility table](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html). If necessary, update the driver through the existing GPU Operator installation before proceeding. The preceding guide's CUDA 12.5 VectorAdd test alone does not verify compatibility with CUDA 13.

## Step 2: Install KAI Scheduler

[KAI v0.17.0](https://github.com/kai-scheduler/KAI-Scheduler/releases/tag/v0.17.0) is a published non-prerelease version. Pin the chart to this release so that its settings and schemas match the examples below.

The OneKS guide installs GPU Operator v26.7.0 with CDI and the NRI plugin enabled. Standard whole-GPU workloads use this configuration without an explicit `nvidia` runtime class. Fractional workloads need an additional integration step: KAI v0.17.0's binder passes its assigned CDI device through `NVIDIA_VISIBLE_DEVICES`, whereas NVIDIA's NRI plugin expects a `nvidia.cdi.k8s.io/container.<container-name>` pod annotation. The Helm settings below alone do not connect those mechanisms. This single-GPU lab therefore adds an explicit NRI device annotation and pins both servers to the matching worker in Step 4. This workaround is specific to a node with exactly one GPU; it must not be used as a general multi-GPU scheduling recipe.

Save the following as `kai-values.yaml`:

```yaml
global:
  gpuSharing: true
binder:
  cdiEnabled: true
  runtimeClassName: ""
admission:
  gpuFractionRuntimeClassName: ""
```

These are the settings used by the [v0.17.0 chart templates](https://github.com/kai-scheduler/KAI-Scheduler/blob/v0.17.0/deployments/kai-scheduler/templates/_helpers.tpl): `binder.cdiEnabled` selects CDI device names, `binder.runtimeClassName` leaves reservation pods on the default runtime, and `admission.gpuFractionRuntimeClassName` disables runtime-class injection into sharing workloads. The workload manifests use the default runtime and explicitly annotate the single testbed GPU for NRI injection.

Install the released chart:

```shell
helm install kai-scheduler \
  https://github.com/kai-scheduler/KAI-Scheduler/releases/download/v0.17.0/kai-scheduler-v0.17.0.tgz \
  --namespace kai-scheduler --create-namespace \
  --values kai-values.yaml \
  --wait --timeout 10m
```

Successful output:

```default
NAME: kai-scheduler
LAST DEPLOYED: Wed Sep 23 20:16:36 2026
NAMESPACE: kai-scheduler
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

Inspect the operator-managed components as well as the Helm release (you may find it easier to run these commands one by one):

```shell
kubectl -n kai-scheduler get deployments,pods
kubectl get configs.kai.scheduler kai-config -o yaml
kubectl get schedulingshards.kai.scheduler
kubectl wait --for=condition=Established crd/queues.scheduling.run.ai --timeout=120s
kubectl explain queue.spec --api-version=scheduling.run.ai/v2
```

Wait until the operator, admission controller, binder, pod grouper, queue controller, podgroup controller, and scheduler are ready. Helm finishing does not necessarily mean all operator-created components have finished starting. In `kai-config`, confirm that `spec.binder.cdiEnabled` is `true` and `spec.admission.gpuFractionRuntimeClassName` is an empty string.

Leave normal node placement in place. The GPU worker needs capacity for KAI, the GPU Operator, and the two model servers as well as Kubernetes services. Control-plane scheduling is not a prerequisite for this guide.

## Step 3: Create a Lab Queue

Queues remain **`scheduling.run.ai/v2`** in KAI v0.17.0. They are Cluster-wide objects, unlike the namespaced Deployments used below. A fresh chart installation creates a default queue hierarchy; this guide creates a separate `oneks-lab` parent and `oneks-inference` leaf to make its resource budget explicit.

Save this as `kai-queues.yaml`:

```yaml
apiVersion: scheduling.run.ai/v2
kind: Queue
metadata:
  name: oneks-lab
spec:
  resources:
    cpu:
      quota: 2000
      limit: -1
      overQuotaWeight: 1
    memory:
      quota: 7000
      limit: -1
      overQuotaWeight: 1
    gpu:
      quota: 1
      limit: 1
      overQuotaWeight: 1
---
apiVersion: scheduling.run.ai/v2
kind: Queue
metadata:
  name: oneks-inference
spec:
  parentQueue: oneks-lab
  resources:
    cpu:
      quota: 2000
      limit: -1
      overQuotaWeight: 1
    memory:
      quota: 7000
      limit: -1
      overQuotaWeight: 1
    gpu:
      quota: 1
      limit: 1
      overQuotaWeight: 1
```

Both levels of the hierarchy provide a quota of **2 CPUs, 7,000 MB of RAM, and one GPU**. KAI expresses CPU quotas in millicores and memory quotas in decimal MB: the two servers request 2 CPUs and 6 GiB (approximately 6,442 MB) in total. These quotas cover their scheduling requests; the container limits still allow temporary higher CPU and RAM use. Kubernetes also checks that the node has sufficient available resources. See the release's [queue reference](https://github.com/kai-scheduler/KAI-Scheduler/blob/v0.17.0/docs/queues/README.md) for quota units and semantics.

KAI assigns Deployments the non-preemptible `inference` priority by default. Such workloads must fit within the queue hierarchy's quotas; `limit: -1` does not let them exceed a zero quota. Setting CPU or memory quota to zero prevents these servers from scheduling even on an otherwise idle worker. See KAI's [workload priority rules](https://github.com/kai-scheduler/KAI-Scheduler/blob/v0.17.0/docs/priority/README.md).

Validate and apply the queues, then create a dedicated workload namespace:

```shell
kubectl apply --dry-run=server -f kai-queues.yaml
kubectl apply -f kai-queues.yaml
kubectl get queues.scheduling.run.ai oneks-lab oneks-inference
kubectl create namespace ai-workloads
```

Workloads select the leaf queue with the pod label `kai.scheduler/queue: oneks-inference` and KAI with `spec.schedulerName: kai-scheduler`.

## Step 4: Deploy the First Model Server

KAI's [GPU sharing](https://github.com/kai-scheduler/KAI-Scheduler/blob/v0.17.0/docs/gpu-sharing/README.md) uses a `gpu-fraction` annotation to account for part of a GPU. A reservation pod holds the physical GPU while KAI places fractional workloads on it. Do not add a whole-device `nvidia.com/gpu: 1` request to these fractional workloads.

The two servers in this example use the following budget:

| **Setting** | **Each server** | **Both servers** |
| --- | --- | --- |
| KAI GPU fraction | 0.4 | 0.8 of one L40S |
| vLLM GPU memory target | 0.3 of the device | Approximately 0.6 of the device |
| CPU request / limit | 1 / 2 CPUs | 2 / 4 CPUs |
| RAM request / limit | 3 GiB / 5 GiB | 6 GiB / 10 GiB |
| Ephemeral storage request | 4 GiB | 8 GiB |

On an L40S reporting roughly 46,000 MiB, each vLLM instance targets about 13.5 GiB of device memory. Qwen3-0.6B, a 2,048-token context, and at most two concurrent sequences keep this example small. Eager execution avoids CUDA graph capture overhead. The vLLM options are documented in the [v0.28.0 CLI reference](https://docs.vllm.ai/en/v0.28.0/cli/serve/).

KAI's default sharing configuration does **not** enforce GPU memory isolation or guarantee a fraction of GPU compute time. The annotation is scheduling accounting; the application must control its memory use. The vLLM memory target is below KAI's reservation to leave headroom. These are lab starting values, to be checked against actual startup and inference memory use on the testbed.

We will save the new Deployment and Service as `qwen-a.yaml`. Before applying it, you must retrieve the two values needed for its placeholders.

To find the value for the `GPU_UUID_FROM_NVIDIA_SMI` placeholder in `qwen-a.yaml` below, list the driver pods and identify the one on your GPU worker using the `NODE` column:

```shell
kubectl -n gpu-operator get pods -l app=nvidia-driver-daemonset -o wide
```

Example output: 

```default
NAME                            READY   STATUS   ...  NODE                             
nvidia-driver-daemonset-bxbz9   1/1     Running  ...  nodegroup-general-large-7fc...
```

Replace `<driver_pod_name>` below with that pod's name (`nvidia-driver-daemonset-bxbz9` in the above example). This command prints only the GPU UUID, without a table header:

```shell
kubectl -n gpu-operator exec <driver_pod_name> -c nvidia-driver-ctr -- \
  nvidia-smi --query-gpu=uuid --format=csv,noheader
```

Example output:

```default
GPU-1cb3a919-51a9-0d16-965b-4fed91e74679
```

Take a note of this value and replace the entire `GPU_UUID_FROM_NVIDIA_SMI` placeholder in the `qwen-a.yaml` below with your output, including the `GPU-` prefix. For the example above, the annotation becomes:

```yaml
nvidia.cdi.k8s.io/container.vllm: "k8s.device-plugin.nvidia.com/gpu=GPU-1cb3a919-51a9-0d16-965b-4fed91e74679"
```

To find `GPU_WORKER_HOSTNAME`, display the GPU workers and their hostname labels together:

```shell
kubectl get nodes -l nvidia.com/gpu.present=true \
  -o custom-columns='NAME:.metadata.name,HOSTNAME:.metadata.labels.kubernetes\.io/hostname,GPU:.status.allocatable.nvidia\.com/gpu,MODEL:.metadata.labels.nvidia\.com/gpu.product,MEMORY-MiB:.metadata.labels.nvidia\.com/gpu.memory'
```

Example output:

```default
NAME                                               HOSTNAME                                          
nodegroup-general-large-7fc21d43cda5-hv9j2-xs267   nodegroup-general-large-7fc21d43cda5-hv9j2-xs267
```

Find the row whose `NAME` matches the worker hosting the driver pod used above. Take a note of the value and replace `GPU_WORKER_HOSTNAME` in `quen-a.yaml` below with that row's **HOSTNAME** value. The two columns may be identical, but the pod's node selector matches the hostname label.

Verify that this worker advertises exactly one GPU. The annotation supplies NVIDIA NRI with that device, while the hostname selector ensures KAI can only place the pod on its matching node. KAI still manages the reservation and `gpu-fraction` accounting. Recheck both values if the worker or its passthrough GPU changes. This workaround is awaiting end-to-end testbed confirmation.

After replacing `GPU_UUID_FROM_NVIDIA_SMI` and `GPU_WORKER_HOSTNAME` with the values recovered in above and save the following manifest as `qwen-a.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-a
  namespace: ai-workloads
spec:
  replicas: 1
  progressDeadlineSeconds: 1800
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: qwen-a
  template:
    metadata:
      labels:
        app: qwen-a
        kai.scheduler/queue: oneks-inference
      annotations:
        gpu-fraction: "0.4"
        nvidia.cdi.k8s.io/container.vllm: "k8s.device-plugin.nvidia.com/gpu=GPU_UUID_FROM_NVIDIA_SMI"
    spec:
      schedulerName: kai-scheduler
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-L40S
        kubernetes.io/hostname: GPU_WORKER_HOSTNAME
      containers:
        - name: vllm
          image: vllm/vllm-openai:v0.28.0
          command: ["vllm", "serve"]
          args:
            - Qwen/Qwen3-0.6B
            - --host
            - "0.0.0.0"
            - --port
            - "8000"
            - --gpu-memory-utilization
            - "0.3"
            - --max-model-len
            - "2048"
            - --max-num-seqs
            - "2"
            - --max-num-batched-tokens
            - "2048"
            - --enforce-eager
          env:
            - name: OMP_NUM_THREADS
              value: "1"
          ports:
            - name: http
              containerPort: 8000
          resources:
            requests:
              cpu: "1"
              memory: "3Gi"
              ephemeral-storage: "4Gi"
            limits:
              cpu: "2"
              memory: "5Gi"
          volumeMounts:
            - name: shm
              mountPath: /dev/shm
          startupProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 120
          readinessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 5
      volumes:
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: qwen-a
  namespace: ai-workloads
spec:
  type: ClusterIP
  selector:
    app: qwen-a
  ports:
    - name: http
      port: 8000
      targetPort: http
```

`Recreate` avoids a rolling update attempting to reserve a third 0.4-GPU pod before an old pod stops. Shared memory counts against the container's RAM limit. The public model requires no Hugging Face token; if your environment needs authenticated downloads, provide `HF_TOKEN` through a Secret in `ai-workloads` and reference it in the container environment.

Validate and deploy the first server:

```shell
kubectl apply --dry-run=server -f qwen-a.yaml
kubectl apply -f qwen-a.yaml
kubectl -n ai-workloads rollout status deployment/qwen-a --timeout=35m
kubectl -n ai-workloads logs deployment/qwen-a -c vllm --tail=100
```

Image download and model initialization may take several minutes. Wait for readiness before starting the second server so that the two instances do not profile GPU memory simultaneously.

The Deployment allows 30 minutes without progress before reporting a failed rollout. This is separate from the startup probe, which allows approximately 20 minutes after the container starts, and the 35-minute client wait in `kubectl rollout status`. Without `progressDeadlineSeconds`, Kubernetes uses a [10-minute Deployment deadline](https://kubernetes.io/docs/reference/kubernetes-api/apps/deployment-v1/), even if the client waits longer. If rollout monitoring fails, inspect the pod events and logs in [Troubleshooting](#troubleshooting) before retrying or deploying the second server.

## Step 5: Add a Second Server on the Same GPU

Create `qwen-b.yaml` from the first manifest, changing its Deployment name, pod labels, and Service selector together. Keep the same resolved NRI annotation and worker hostname:

```shell
sed 's/qwen-a/qwen-b/g' qwen-a.yaml > qwen-b.yaml
kubectl apply --dry-run=server -f qwen-b.yaml
kubectl apply -f qwen-b.yaml
kubectl -n ai-workloads rollout status deployment/qwen-b --timeout=35m
```

Both servers run the same small model independently. Inspect their scheduler, GPU fractions, node placement, and GPU group:

```shell
kubectl -n ai-workloads get pods \
  -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[*].ready,SCHEDULER:.spec.schedulerName,NODE:.spec.nodeName,FRACTION:.metadata.annotations.gpu-fraction,GPU-GROUP:.metadata.labels.runai-gpu-group'
kubectl -n kai-resource-reservation get pods -o wide
```

Both workload pods should be ready, use `kai-scheduler`, show fraction `0.4`, and have the same worker node and GPU-group value. Confirm that each container sees the same GPU UUID:

```shell
kubectl -n ai-workloads exec deployment/qwen-a -c vllm -- \
  nvidia-smi --query-gpu=uuid,name,memory.used,memory.total --format=csv
kubectl -n ai-workloads exec deployment/qwen-b -c vllm -- \
  nvidia-smi --query-gpu=uuid,name,memory.used,memory.total --format=csv
```

These memory figures describe the whole shared device, not a per-pod allocation. The reservation pod's whole-GPU request is expected; the two vLLM pods account for fractions through KAI instead of separate Kubernetes GPU requests.

## Step 6: Test Both Inference APIs

In separate terminals with the OneKS kubeconfig exported, start a port-forward for each Service:

```shell
export KUBECONFIG="$PWD/kubeconfig"
kubectl -n ai-workloads port-forward svc/qwen-a 9000:8000
```

In a second terminal:

```shell
export KUBECONFIG="$PWD/kubeconfig"
kubectl -n ai-workloads port-forward svc/qwen-b 9001:8000
```

Leave both commands running. In another terminal, verify that both services advertise the model:

```shell
curl --fail-with-body http://localhost:9000/v1/models | jq .
curl --fail-with-body http://localhost:9001/v1/models | jq .
```

Each response should list `Qwen/Qwen3-0.6B`. Send a short chat request to each endpoint:

```shell
for port in 9000 9001; do
  curl --fail-with-body "http://localhost:${port}/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d '{
      "model": "Qwen/Qwen3-0.6B",
      "messages": [{"role": "user", "content": "What is OpenNebula? Answer in one sentence."}],
      "chat_template_kwargs": {"enable_thinking": false},
      "max_tokens": 128,
      "temperature": 0,
      "stream": false
    }' | jq .
done
```

The response should look similar to the following for each model deployment: 

```json
{
  "id": "chatcmpl-a98f8a4def3e55ad",
  "object": "chat.completion",
  "created": 1790329799,
  "model": "Qwen/Qwen3-0.6B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "OpenNebula is a distributed storage system designed for managing and scaling virtualized cloud environments.",
        "refusal": null,
        "annotations": null,
        "audio": null,
        "function_call": null,
        "reasoning": null
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null,
      "token_ids": null,
      "routed_experts": null
    }
  ],
  "service_tier": null,
  "system_fingerprint": "vllm-0.28.0-61dfa98f",
  "usage": {
    "prompt_tokens": 24,
    "total_tokens": 44,
    "completion_tokens": 20,
    "prompt_tokens_details": null,
    "completion_tokens_details": null
  },
  "prompt_logprobs": null,
  "prompt_token_ids": null,
  "prompt_text": null,
  "kv_transfer_params": null,
  "ec_transfer_params": null,
  "metrics": null
}
```

Successful responses contain text in `choices[0].message.content` and token counts in `usage`. Exact text can vary. These requests, together with the matching GPU UUIDs, validate two running inference services sharing the testbed's single L40S. The port-forwards bind to localhost by default; stop both with **Ctrl-C** when finished.

## Troubleshooting

Use pod events to distinguish scheduling problems from container startup or model-loading failures:

```shell
kubectl -n ai-workloads get pods -o wide
kubectl -n ai-workloads describe deployment qwen-a
kubectl -n ai-workloads get events --sort-by=.lastTimestamp | tail -40
kubectl -n ai-workloads describe pod <workload-pod-name>
kubectl -n ai-workloads logs <workload-pod-name> -c vllm --tail=100
kubectl -n ai-workloads get podgroups.scheduling.run.ai
kubectl -n kai-resource-reservation get pods
```

If the container has restarted, also inspect its previous logs:

```shell
kubectl -n ai-workloads logs <workload-pod-name> -c vllm --previous --tail=100
```

* **Deployment exceeded its progress deadline**: This reports a lack of progress, not its cause, and does not stop the pod. A successful server dry run validates the Deployment and Service but does not create or schedule their pods, download the image, or start vLLM. Inspect events and logs to find which stage is blocked. If you used an earlier copy of this manifest without `progressDeadlineSeconds`, add `progressDeadlineSeconds: 1800` under the Deployment's `spec` in your local YAML and reapply it. Increasing the deadline only gives a slow startup more time; it does not resolve scheduling or application errors. An already-recorded failure condition can persist until the Deployment makes progress, so also watch the pod directly with `kubectl -n ai-workloads get pods -w`.
* **NonPreemptibleOverQuota**: Check CPU and memory quotas on both `oneks-inference` and its parent `oneks-lab`. Earlier copies of this guide incorrectly set them to zero. Update both queues in `kai-queues.yaml` to the values in Step 3 and reapply that file. KAI will reconsider the existing Pending pod; deleting it or reinstalling KAI is unnecessary. After correcting CPU, memory must also cover the requested RAM. Watch the pod's readiness and recent events, since a previous Deployment deadline failure can remain visible until progress resumes.
* **Pending workload**: Check the queue label, scheduler name, L40S node label, CPU/RAM requests, and whether another workload holds the physical GPU. The two fractions total 0.8; a third 0.4 allocation cannot fit on this GPU.
* **Missing runtime class or GPU access**: Check `kai-config` against the CDI settings in Step 2, the reservation pod's events, and the GPU Operator toolkit/device-plugin pods. Confirm that the preceding guide's NRI plugin remains enabled. Correct the Helm values and recreate affected workload pods so admission runs again.
* **CUDA out of memory**: Start the servers sequentially, confirm the vLLM memory option is still `0.3`, and check for other GPU processes. The KAI fraction alone does not cap actual memory use.
* **OOMKilled or disk pressure**: Inspect host RAM and ephemeral storage on the worker. Keep enough capacity for Cluster services when increasing a model server's limits.

### Fractional GPU Access with NRI

A pod can be successfully scheduled and assigned a `runai-gpu-group` but still lack GPU devices and driver libraries inside its container. On the OneKS NRI configuration, this has produced `0 active driver(s) found`, `No CUDA runtime is found`, and `Failed to infer device type` in vLLM, followed by exit code 1. The failed health probe is a consequence of the application exiting, not the cause.

The [KAI v0.17.0 binder](https://github.com/kai-scheduler/KAI-Scheduler/blob/v0.17.0/pkg/binder/plugins/gpusharing/gpu_sharing.go) writes the assigned CDI device into an environment variable. The [NVIDIA NRI plugin](https://github.com/NVIDIA/nvidia-container-toolkit/blob/v1.20.0/cmd/nvidia-ctk-installer/container/runtime/nri/plugin.go) reads CDI requests from pod annotations. Setting `binder.cdiEnabled: true` selects CDI device names but does not add that NRI annotation.

Inspect the assigned device and installed toolkit version before choosing a compatibility adjustment:

```shell
kubectl -n ai-workloads get pod <workload-pod-name> -o json | \
  jq '.spec.containers[] | select(.name == "vllm") | .env'
kubectl -n ai-workloads get configmap <configmap-referenced-by-NVIDIA_VISIBLE_DEVICES> -o yaml
kubectl -n gpu-operator get daemonset nvidia-container-toolkit-daemonset \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{": "}{.image}{"\n"}{end}'
```

Do not address this error by increasing model memory limits, reinstalling Triton, or adding a whole-GPU request to each fractional pod. For this single-GPU lab, add the NRI annotation and matching worker hostname to `spec.template` as shown in Step 4, then reapply the Deployment. Changing the pod template creates a new pod so that NRI runs during container creation. Editing only the existing pod annotation is insufficient to ensure a new pod sandbox. This explicit device selection is not a general substitute for KAI's dynamic assignment on multi-GPU nodes.

## Undeployment

Remove both model servers and their Services while KAI is still running:

```shell
kubectl delete -f qwen-b.yaml -f qwen-a.yaml
kubectl -n ai-workloads wait --for=delete pod --all --timeout=5m
kubectl -n kai-resource-reservation get pods
```

Wait for KAI to release the GPU reservation after the last fractional workload terminates. Then remove this guide's leaf queue before its parent, and delete the workload namespace:

```shell
kubectl delete queues.scheduling.run.ai oneks-inference
kubectl delete queues.scheduling.run.ai oneks-lab
kubectl delete namespace ai-workloads
```

If no other workloads use this KAI installation, uninstall it:

```shell
helm uninstall kai-scheduler --namespace kai-scheduler --wait --timeout 10m
kubectl delete namespace kai-scheduler
kubectl delete namespace kai-resource-reservation --ignore-not-found
```

The chart intentionally retains some Cluster-wide resources, including its default queues, default SchedulingShard, and CRDs. On this dedicated lab Cluster, inspect and remove the default queues and shard only if they are no longer used:

```shell
kubectl get queues.scheduling.run.ai
kubectl get schedulingshards.kai.scheduler
kubectl delete queues.scheduling.run.ai default-queue
kubectl delete queues.scheduling.run.ai default-parent-queue
kubectl delete schedulingshards.kai.scheduler default
```

CRDs may remain for reuse. Deleting a CRD also deletes all its custom resources, so do not remove shared CRDs as routine cleanup. Keep the OneKS Cluster and GPU Operator running for subsequent guides.

## Next Steps

If you did not previously follow the [NVIDIA Dynamo Deployment Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo" %}}), you could follow that next to deploy a managed inference graph on the same OneKS Cluster after releasing the GPU used by this example.
