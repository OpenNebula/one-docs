---
title: Deployment of NVIDIA Dynamo
linkTitle: Inferencing with NVIDIA Dynamo
weight: 6
tags: ['AI','Kubernetes','NVIDIA']
---

<a id="nvidia_dynamo"></a>

[NVIDIA&reg; Dynamo](https://docs.nvidia.com/dynamo/latest/index.html) is a high-performant inference framework for serving AI models in an agnostic way, across any framework, architecture or deployment scale, as well as in multi-node distributed environments. Being an agnostic inference engine, it supports different backends such as TRT-LLM, vLLM, SGLang, etc. Dynamo also allows you to declare inference graphs which deploy different containerized components in a disaggregated way - like an API frontend, a prefill worker, a decode worker, a K/V cache, and others - and to let them interact to efficiently respond to the user queries.

Encapsulating the different inference engines, AI models and dependencies into a single container improves the workload portability and isolation. With this approach, each container is deployed consistently across different environments, including all its dependencies, avoiding conflicts and reproducibility issues.

In this guide you will learn how to combine the GPU powered Kubernetes Cluster with the NVIDIA Dynamo Cloud Platform for provisioning a secure, robust and scalable solution for our AI workloads on top of the NVIDIA Dynamo framework powered by the OpenNebula cloud platform.

## Before Starting

Before starting this tutorial, you must complete the AI Factory deployment with either on-premises resources or cloud resources. Please complete one of the following guides relevant to your available resources:

* [AI Factory Deployment with On-premises Hardware]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}})
* [AI Factory Deployment on Scaleway Cloud]({{% relref "solutions/ai_factory_blueprints/deployment/cd_cloud"%}})

You must then complete the [AI-ready Kubernetes Deployment Guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}). You also must undeploy any appliances, VMs or services you deployed in previous guides before continuing.

{{< alert title="Important" type="info" >}}

For the following commands to work, you must use the `kubeconfig_workload.yaml` Kubeconfig. Either add `--kubeconfig kubeconfig_workload.yaml` to the commands or export the `KUBECONFIG` environment variable:

```shell
export KUBECONFIG="$PWD/kubeconfig_workload.yaml"
```

{{< /alert >}}

### NVIDIA Dynamo Cloud Platform Installation

As a prerequisite, you need a storage provider installed to supply PersistentVolumes to the platform. For testing purposes, use the [rancher local-path-provisioner](https://github.com/rancher/local-path-provisioner) that references to a local path from the pod host as storage, and creates a default storage class using it.

1. To install the provisioner, deploy the manifest from the GitHub repository:

```shell
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.32/deploy/local-path-storage.yaml
```

2. Check that the storage provisioner is up and running:

```shell
kubectl -n local-path-storage get deploy,pods
```
You should see an output like this:
```
NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/local-path-provisioner   1/1     1            1           7d2h

NAME                                          READY   STATUS    RESTARTS   AGE
pod/local-path-provisioner-7f57b55d56-7qb42   1/1     Running   0          7d2h
```

3. Create the following storageClass and set it as default.

If you want to modify the `nodePath` parameter, ensure that it is available in the `nodePathMap` field of the provider config as indicated in the [Customize the configmap](https://github.com/rancher/local-path-provisioner?tab=readme-ov-file#customize-the-configmap) guide.

```shell
cat <<EOF > storageClass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: rancher.io/local-path
parameters:
  nodePath: /opt/local-path-provisioner
  pathPattern: "{{ .PVC.Namespace }}/{{ .PVC.Name }}"
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
EOF

kubectl replace --force -f storageClass.yaml

```

4. Make this storage class is the default:
```shell
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

```shell
kubectl get storageClass
```

The `local-path` storage class should have the `(default)` suffix:

```
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false
```

At this point, the Dynamo Cloud platform is ready for installation. Configure your cluster in a declarative way, by using the containers and helm charts in the [NVIDIA NGC catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-dynamo/collections/ai-dynamo), and follow these steps:

1. Install the CRDs:

```shell
helm install dynamo-crds https://helm.ngc.nvidia.com/nvidia/ai-dynamo/charts/dynamo-crds-0.7.0.tgz \
  --namespace dynamo-cloud --create-namespace \
  --wait --atomic
```

2. Install the operator, using the 0.7.0 version (using another version may cause problems while following this guide):

```shell
helm install dynamo-platform https://helm.ngc.nvidia.com/nvidia/ai-dynamo/charts/dynamo-platform-0.7.0.tgz \
  --namespace dynamo-cloud \
  --create-namespace \
  --set "dynamo-operator.controllerManager.manager.image.repository=nvcr.io/nvidia/ai-dynamo/kubernetes-operator" \
  --set "dynamo-operator.controllerManager.manager.image.tag=0.7.0"
```

3. Check if the operator is up and running:

```shell
kubectl -n dynamo-cloud get deploy,pod,svc
```

All the pods should be in `Running` or `Completed` state:

```default
NAME                                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dynamo-platform-dynamo-operator-controller-manager   1/1     1            1           27h
deployment.apps/dynamo-platform-nats-box                             1/1     1            1           27h

NAME                                                                  READY   STATUS      RESTARTS   AGE
pod/dynamo-platform-dynamo-operator-controller-manager-75fd6b7cdvlt   2/2     Running     0          26h
pod/dynamo-platform-etcd-0                                            1/1     Running     0          27h
pod/dynamo-platform-etcd-pre-upgrade-g5cjm                            0/1     Completed   0          27h
pod/dynamo-platform-nats-0                                            2/2     Running     0          27h
pod/dynamo-platform-nats-box-57c9cf4c7b-vbgpg                         1/1     Running     0          27h

NAME                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
service/dynamo-platform-etcd            ClusterIP   10.43.157.193   <none>        2379/TCP,2380/TCP   27h
service/dynamo-platform-etcd-headless   ClusterIP   None            <none>        2379/TCP,2380/TCP   27h
service/dynamo-platform-nats            ClusterIP   10.43.175.109   <none>        4222/TCP            27h
service/dynamo-platform-nats-headless   ClusterIP   None            <none>        4222/TCP,8222/TCP   27h
```

{{< alert title="Tip" type="info" >}}
If the `dynamo-platform-dynamo-operator-controller-manager` pod is stuck in the `ImagePullBackOff` state, see the [Known Issues]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo/#known-issues" %}}) section for a solution.
{{< /alert >}}

4. To use some LLM models in the platform, you need a HuggingFace token for authenticating against the API. Go to the [tokens page of the HuggingFace website](https://huggingface.co/settings/tokens) to create a new token if you don't already have one. Create a YAML file with your HF token (replace `<token>`):

```shell
cat<<EOF > hf-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: hf-token-secret
  namespace: dynamo-cloud
type: Opaque
stringData:
  token: "<token>"
EOF
```
Then apply YAML file so that Dynamo can access the token:

```shell
kubectl apply -f hf-secret.yaml
```

## Deployment of Dynamo Inference Graphs

NVIDIA Dynamo orchestrates the deployment of inference graphs [through the Dynamo CLI](https://docs.nvidia.com/dynamo/cli/getting-started/quickstart) or by deploying manifests following the specific [Dynamo CRDs](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-dynamo/helm-charts/dynamo-crds?version=0.9.1) directly in the cluster, which are recognized and managed by the Dynamo Kubernetes Operator.

The instructions of this guide do not expose the Dynamo API externally. You benefit from the Dynamo Kubernetes Operator by deploying the manifests of the inference graphs directly on the cluster.

To run your workloads as Dynamo Inference Graphs, check the following requirements:

- If the HuggingFace model that you are using needs authorization, configure an updated HF token set as Kubernetes secret with the `hf-token-secret` name.
- Assign a GPU to the worker pod, by setting the `spec.VllmDecodeWorker.extraPodSpec` field with `runtimeClassName: nvidia`

Once you access the Kubernetes API, proceed to deploy the inference graphs you defined in the corresponding manifest.

The latest vllm-runtime image is located in [`nvcr.io/nvidia/ai-dynamo/vllm-runtime:0.4.1`](https://github.com/ai-dynamo/dynamo/tree/main/docs/backends/vllm), but you can build your own runtime image following the [instructions](https://github.com/ai-dynamo/dynamo/tree/main/docs/backends/vllm) in the Dynamo repository.

An example of a disaggregated deployment graph (for a multi-GPU setup) is available in the [NVIDIA Dynamo GitHub Repository](https://github.com/ai-dynamo/dynamo/tree/v0.4.1/components/backends/vllm/deploy). For this guide, the example was adapted to work for a validated container runtime:

{{< alert title="Important" type="primary" >}}
This disaggregated example is intended for a topology with **2 GPUs** exposed through PCI passthrough, either within the same Host or on separate Hosts. Resource conflicts will prevent proper function with only a single GPU available. For a single GPU setup, we recommend that you find an aggregated example graph.
{{< /alert >}} 

```yaml
cat << EOF > disagg_custom.yaml
apiVersion: nvidia.com/v1alpha1
kind: DynamoGraphDeployment
metadata:
  name: vllm-v1-disagg-router
spec:
  services:
    Frontend:
      dynamoNamespace: vllm-v1-disagg-router
      componentType: frontend
      replicas: 1
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 20
        periodSeconds: 5
        timeoutSeconds: 5
        failureThreshold: 3
      readinessProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - 'curl -s http://localhost:8000/health | jq -e ".status == \"healthy\""'
        initialDelaySeconds: 60
        periodSeconds: 60
        timeoutSeconds: 30
        failureThreshold: 10
      resources:
        requests:
          cpu: "1"
          memory: "2Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
      extraPodSpec:
        mainContainer:
          image: nvcr.io/nvidia/ai-dynamo/vllm-runtime:0.7.0
          workingDir: /workspace/components/backends/vllm
          command:
            - /bin/sh
            - -c
          args:
            - "python3 -m dynamo.frontend --http-port 8000 --router-mode kv"
    VllmDecodeWorker:
      dynamoNamespace: vllm-v1-disagg-router
      envFromSecret: hf-token-secret
      componentType: worker
      replicas: 1
      livenessProbe:
        httpGet:
          path: /live
          port: 9090
        periodSeconds: 5
        timeoutSeconds: 30
        failureThreshold: 1
      readinessProbe:
        httpGet:
          path: /health
          port: 9090
        periodSeconds: 10
        timeoutSeconds: 30
        failureThreshold: 60
      resources:
        requests:
          cpu: "4"
          memory: "8Gi"
          gpu: "1"
        limits:
          cpu: "8"
          memory: "16Gi"
          gpu: "1"

      envs:
        - name: DYN_SYSTEM_ENABLED
          value: "true"
        - name: DYN_SYSTEM_USE_ENDPOINT_HEALTH_STATUS
          value: "[\"generate\"]"
      extraPodSpec:
        runtimeClassName: nvidia
        mainContainer:
          startupProbe:
            httpGet:
              path: /health
              port: 9090
            periodSeconds: 10
            failureThreshold: 60
          image: nvcr.io/nvidia/ai-dynamo/vllm-runtime:0.7.0
          workingDir: /workspace/components/backends/vllm
          command:
            - /bin/sh
            - -c
          args:
            - python3 -m dynamo.vllm --model Qwen/Qwen3-0.6B
    VllmPrefillWorker:
      dynamoNamespace: vllm-v1-disagg-router
      envFromSecret: hf-token-secret
      componentType: worker
      replicas: 1
      livenessProbe:
        httpGet:
          path: /live
          port: 9090
        periodSeconds: 5
        timeoutSeconds: 30
        failureThreshold: 1
      readinessProbe:
        httpGet:
          path: /health
          port: 9090
        periodSeconds: 10
        timeoutSeconds: 30
        failureThreshold: 60
      resources:
        requests:
          cpu: "4"
          memory: "8Gi"
          gpu: "1"
        limits:
          cpu: "8"
          memory: "16Gi"
          gpu: "1"
      envs:
        - name: DYN_SYSTEM_ENABLED
          value: "true"
        - name: DYN_SYSTEM_USE_ENDPOINT_HEALTH_STATUS
          value: "[\"generate\"]"
        - name: DYN_SYSTEM_PORT
          value: "9090"
      extraPodSpec:
        runtimeClassName: nvidia
        mainContainer:
          startupProbe:
            httpGet:
              path: /health
              port: 9090
            periodSeconds: 10
            failureThreshold: 60
          image: nvcr.io/nvidia/ai-dynamo/vllm-runtime:0.7.0
          workingDir: /workspace/components/backends/vllm
          command:
            - /bin/sh
            - -c
          args:
            - python3 -m dynamo.vllm --model Qwen/Qwen3-0.6B  --is-prefill-worker
EOF
```

Deploy the disaggregated deployment graph with kubectl:

```shell
kubectl -n dynamo-cloud apply -f disagg_custom.yaml
```

After some minutes (pulling the vLLM runtime image takes some time), check that the pods are up and running. If pods are in the `ContainerCreating` status, continue waiting until they convert to `Running`:

```shell
kubectl -n dynamo-cloud get pods,svc
```
```
---
NAME                                                                  READY   STATUS      RESTARTS   AGE
pod/disagg-frontend-65646b6f7b-dwfr2                                  1/1     Running     0          27m
pod/disagg-prefillworker-5b784c677c-42pts                             1/1     Running     0          27m
pod/disagg-vllmworker-d494976f6-78hr7                                 1/1     Running     0          33m
[...]

NAME                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
service/disagg-frontend                 ClusterIP   10.43.92.113    <none>        8000/TCP            33m
[...]
```

## Querying the API Locally (Optional)

In case you want to query the API client locally, forward the vllm frontend service through Kubernetes with this command:

```shell
kubectl -n dynamo-cloud port-forward svc/<frontend_service> <local_port>:8000 &
```

For example:

```shell
kubectl -n dynamo-cloud port-forward svc/vllm-v1-disagg-router-frontend 9000:8000 &
```

 To test the loaded models, run requests to the frontend via curl:

```shell
curl localhost:9000/v1/models | jq .
```

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen3-0.6B",
      "object": "object",
      "created": 1756908946,
      "owned_by": "nvidia"
    }
  ]
}
```

If the `data` attribute is empty, the model may still be loading, try again in a minute or so. 

Once the model is loaded, try submitting an inference request:

```shell
curl localhost:9000/v1/completions   -H "Content-Type: application/json"   -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "What is opennebula?",
    "stream": false,
    "max_tokens": 300
  }' | jq
```

You will receive a response like this:

```json
{
  "id": "cmpl-2c749514-9a81-4864-a119-d195d39a235b",
  "choices": [
    {
      "text": "<think>\nOkay, the user is asking about OpenNebula. First, I need to make sure I understand what OpenNebula is. From what I remember, OpenNebula is an open-source orchestration system used for managing virtual machines (VMs) in cloud environments. It's often used in Linux-based cloud infrastructures like AWS or Azure. \n\nI should start by defining OpenNebula. It's a tool that helps manage and orchestrate virtual machines on a cloud platform. The key features include providing a way to manage VMs, resources, and services in a centralized manner. OpenNebula is designed to be flexible and scalable, allowing for easy integration with various cloud providers.\n\nWait, are there any specific use cases or industries where OpenNebula is commonly used? I think it's often used in enterprise environments for managing VMs, especially in environments where automation and resource management are critical. It's also used in hybrid cloud setups where VMs can be managed between on-premises and cloud environments.\n\nI should mention that OpenNebula is open-source, which is important to highlight. It's developed by a community and is licensed under a specific open-source license. Maybe include something about how it simplifies VM orchestration and management.\n\nAre there any common misconceptions about OpenNebula? Perhaps users might confuse it with other cloud management tools. I should clarify that it's specifically for orchestration rather than just managing VMs.",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "created": 1755169608,
  "model": "Qwen/Qwen3-0.6B",
  "system_fingerprint": null,
  "object": "text_completion",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 299,
    "total_tokens": 314,
    "prompt_tokens_details": null,
    "completion_tokens_details": null
  }
}
```

If you want to test the response in stream mode, set the parameter `stream: true` and delete the `jq` tool piping to that call:

```shell
curl localhost:9000/v1/completions   -H "Content-Type: application/json"   -d '{
    "model": "Qwen/Qwen3-0.6B",
    "prompt": "What is opennebula?",
    "stream": true,
    "max_tokens": 300
  }'
```

You will see this streamed output:

```
data: {"id":"cmpl-84041acf-79d1-4ec4-b913-c492fa4f3379","choices":[{"text":"<think>","index":0,"logprobs":null,"finish_reason":null}],"created":1756908478,"model":"Qwen/Qwen3-0.6B","system_fingerprint":null,"object":"text_completion","usage":{"prompt_tokens":15,"completion_tokens":1,"total_tokens":16,"prompt_tokens_details":null,"completion_tokens_details":null}}

data: {"id":"cmpl-84041acf-79d1-4ec4-b913-c492fa4f3379","choices":[{"text":"\n","index":0,"logprobs":null,"finish_reason":null}],"created":1756908478,"model":"Qwen/Qwen3-0.6B","system_fingerprint":null,"object":"text_completion","usage":{"prompt_tokens":15,"completion_tokens":2,"total_tokens":17,"prompt_tokens_details":null,"completion_tokens_details":null}}

data: {"id":"cmpl-84041acf-79d1-4ec4-b913-c492fa4f3379","choices":[{"text":"Okay","index":0,"logprobs":null,"finish_reason":null}],"created":1756908478,"model":"Qwen/Qwen3-0.6B","system_fingerprint":null,"object":"text_completion","usage":{"prompt_tokens":15,"completion_tokens":3,"total_tokens":18,"prompt_tokens_details":null,"completion_tokens_details":null}}

[...]
```

In the streamed output, you will receive multiple JSON responses with the response tokens in the `text` field, with some metadata included.

## Undeployment

Before moving on to other AI Factory guides or deployments, it is recommended to undeploy NVIDIA Dynamo and the Disaggregated Deployment Graph if you do not intend to further use NVIDIA Dynamo. 

Run the following command to undeploy the graph:

```shell
kubectl delete dynamographdeployment vllm-v1-disagg-router -n dynamo-cloud
```

Run the following command until you see the disagg-router resources disappear:

```shell
kubectl -n dynamo-cloud get pods,deploy,svc
```

Then uninstall NVIDIA Dynamo with Helm:

```shell
helm uninstall dynamo-crds -n dynamo-cloud
helm uninstall dynamo-platform -n dynamo-cloud
```

Run the following command, until you receive the response `No resources found in dynamo-cloud namespace.`:

```shell
kubectl get all -n dynamo-cloud
```

Finally, delete the `dynamo-cloud` namespace:

```shell
kubectl delete namespace dynamo-cloud
```

## Next Steps

After powering your AI Factory with NVIDIA Dynamo on Kubernetes, you may continue with the [NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler" %}}) as an additional validation procedure built on top of K8s.

## Known Issues

### Dynamo Operator Controller Manager stuck in ImagePullBackoff

If the `dynamo-platform-dynamo-operator-controller-manager` pod is stuck in the ImagePullBackOff state, this may be due to a missing image path:

```shell
kubectl -n dynamo-cloud get deploy,pod,svc
```
```default
NAME                                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dynamo-platform-dynamo-operator-controller-manager   1/1     1            1           42m

NAME                                                                  READY   STATUS             RESTARTS   AGE
pod/dynamo-platform-dynamo-operator-controller-manager-75847c7qj2kx   2/2     ImagePullBackOff   0          19m
pod/dynamo-platform-etcd-0                                            1/1     Running            0          42m
pod/dynamo-platform-nats-0                                            2/2     Running            0          42m
...
```

Google is migrating images away from the *gcr.io* domain to *pkg.dev*. Fix the problem by updating the image path in the deployment:

Open the deployment for editing:

```shell
kubectl -n dynamo-cloud edit deployment dynamo-platform-dynamo-operator-controller-manager
```

Look for the line:

```yaml
image: gcr.io/kubebuilder/kube-rbac-proxy:v0.15.0
```

Replace it with:

```yaml
image: quay.io/brancz/kube-rbac-proxy:v0.15.0
```

Save and exit the editor. The pod should automatically restart. Run the following command again until the pod reaches the `Running` status:

```shell
kubectl -n dynamo-cloud get deploy,pod,svc
```
