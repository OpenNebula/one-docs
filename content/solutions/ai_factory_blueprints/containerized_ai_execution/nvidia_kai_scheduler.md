---
title: Deployment of the NVIDIA KAI Scheduler
linkTitle: Scheduling with NVIDIA KAI
weight: 7
tags: ['AI', 'Kubernetes','NVIDIA']
---

<a id="nvidia_kai_scheduler"></a>

The [NVIDIA&reg; KAI Scheduler](https://github.com/NVIDIA/KAI-Scheduler) is an open source Kubernetes-native scheduler designed to optimize GPU resource allocation for AI and machine learning workloads at scale. It is capable of managing large GPU clusters and handling high-throughput demanding workload environments. KAI Scheduler targets both interactive jobs and large-scale training or inference tasks within the same cluster, orchestrating available resources  across different users and teams. It also operates alongside other schedulers installed in a cluster.

Some of the key features are:
- Share single or multiple GPU resources among multiple workloads for improving resource allocation.
- Batch scheduling of different types of workloads, including gang scheduling (i.e. all pods are scheduled together or none are scheduled until all resources are available).
- Effective workload priority with hierarchical queues.
- Resource distribution with custom quotas, limits, priorities and fairness policies.
- Elastic workloads with dynamic workload escalation.
- Compatibility with other autoscalers like Karpenter.

As the KAI Scheduler operates on top of Kubernetes, users benefit from its robust orchestration, scalability, and resource management capabilities, further enhancing deployment flexibility and reliability. Running both KAI Scheduler and Kubernetes on OpenNebula, this solution extends resource management to hybrid and multi-cloud environments, enabling dynamic and cost-effective scaling of AI workloads while maintaining control over infrastructure. This synergy leverages the strengths of all three technologies to deliver efficient, fair, and portable GPU scheduling from on-premises data centers to the cloud.

In this guide you will learn how to perform a validation using NVIDIA KAI Scheduler in an AI-Ready Kubernetes cluster. You will find details about the installation and efficiently share GPU resources among different workloads.

## Before Starting

Before starting this tutorial, you must complete the AI-factory deployment with either on-premise resources or cloud resources. Please complete one of the following guides relevant to your available resources:

* [AI Factory Deployment with On-premise hardware]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}})
* [AI Factory Deployment on Scaleway Cloud]({{% relref "solutions/ai_factory_blueprints/deployment/cd_cloud"%}})

You must then complete the [AI-ready Kubernetes deployment guide]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}). You also must undeploy any appliances, VMs or services you deployed in previous guides before continuing.

{{< alert title="Important" type="info" >}}

For the following commands to work, you must use the `kubeconfig_workload.yaml` Kubeconfig. Either add `--kubeconfig kubeconfig_workload.yaml` to the commands or export the `KUBECONFIG` environment variable:

```shell
export KUBECONFIG="$PWD/kubeconfig_workload.yaml"
```

{{< /alert >}}

### NVIDIA KAI Scheduler Installation

To install the NVIDIA KAI Scheduler, you need to accomplish the following prerequisites:
- An [AI-Ready Kubernetes Cluster with the NVIDIA GPU Operator]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}) installed.
- Helm CLI. For additional details, check the installation instructions in the [official documentation](https://helm.sh/docs/intro/install/).

1. Create a dedicated namespace for the KAI Scheduler components in the Kubernetes cluster:
    ```shell
    kubectl create namespace kai-scheduler
    ```
    
2. Install the KAI Scheduler through Helm. In case you want to use GPU resource sharing feature, set the `"global.gpuSharing=true"` flag:
    ```shell
    helm install kai-scheduler \
        https://github.com/NVIDIA/KAI-Scheduler/releases/download/v0.9.8/kai-scheduler-v0.9.8.tgz \
        -n kai-scheduler --create-namespace \
        --set "global.gpuSharing=true" \
        --set "global.resourceReservation.runtimeClassName=nvidia"
    ```
    We recommend that you install version 0.9.8 of the KAI Scheduler to continue. If you wish to install a newer version, please consult the [KAI Scheduler repository](https://github.com/NVIDIA/KAI-Scheduler/releases) and install it via Helm. **Note that later versions of the KAI Scheduler may require extensive modification of the example schemas provided below to function correctly**.

3. Verify that the Helm chart is successfully installed, and all the KAI Scheduler components are running:
    ```shell
    kubectl get pods -n kai-scheduler
    ```

    ```
    NAME                                   READY   STATUS    RESTARTS   AGE
    admission-55f6c958b6-sx8q6             1/1     Running   0          31s
    binder-66757b79cf-hnckr                1/1     Running   0          33s
    kai-operator-86579f5b96-nc8tl          1/1     Running   0          33s
    pod-grouper-845d589495-qxmlk           1/1     Running   0          31s
    podgroup-controller-75c6986688-7cfhs   1/1     Running   0          31s
    queue-controller-5bf44f6c4d-gwptq      1/1     Running   0          31s
    scheduler-685b9d6846-69vr4             1/1     Running   0          33s
    ```

4. A workload must belong to a queue in order to be scheduled. To manage workloads, create the corresponding queues which are the essential scheduling primitives. These queues reflect different scheduling guarantees, like resource quota and priority. You can assign the queues to different types of consumers in the cluster, such as users and groups.

    Create two basic scheduling queue hierarchies:
    - A `default` top level queue.
    - A `test` leaf queue that you can use for your workloads.

    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: scheduling.run.ai/v2
    kind: Queue
    metadata:
        name: default
    spec:
        resources:
            cpu:
                quota: -1
                limit: -1
                overQuotaWeight: 1
            gpu:
                quota: -1
                limit: -1
                overQuotaWeight: 1
            memory:
                quota: -1
                limit: -1
                overQuotaWeight: 1
    ---
    apiVersion: scheduling.run.ai/v2
    kind: Queue
    metadata:
        name: test
    spec:
        parentQueue: default
        resources:
            cpu:
                quota: -1
                limit: -1
                overQuotaWeight: 1
            gpu:
                quota: -1
                limit: -1
                overQuotaWeight: 1
            memory:
                quota: -1
                limit: -1
                overQuotaWeight: 1
    EOF
    ```

For scheduling your workloads using those queues you need to:
- Specify the queue name using the `kai.scheduler/queue: test` label.
- Specify the kai workload scheduler using the `spec.schedulerName: kai-scheduler` attribute.

Optionally, you can test the scheduler deploying [this example from the KAI quickstart documentation](https://github.com/NVIDIA/KAI-Scheduler/blob/6ffb4252969df19491ce0902d79c0153cae944b3/docs/quickstart/pods/gpu-pod.yaml).

At this point, the KAI Scheduler is installed and ready to schedule your AI workloads.

### GPU Sharing with KAI Scheduler

One of the features of the KAI Scheduler is the GPU resource sharing, which allows multiple pods or workloads share the same GPU device efficiently, even if they reside in different namespaces.

Allocate a portion of the GPU by:
- requesting a specific GPU amount. Example: `3Gib`.
- requesting a portion of a GPU device memory. Example: `0.5`.

KAI Scheduler does not enforce memory allocation limits or performs memory isolation between processes, so it's important that the running processes allocate the GPU memory up to the requested amount. For instance, vLLM workloads by default consume the 90% of the GPU memory, so you will limit this consumption using the `--gpu-memory-utilization` parameter with the corresponding memory fracton such as `--gpu-memory-utilization=0.5`.

To test the GPU sharing feature of KAI Scheduler, follow these steps:

1. Create a namespace for the scheduled workloads
    ```shell
    kubectl create ns ai-workloads
    ```

2. Deploy a sample workload that uses vLLM for inference serving
    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: vllm-test-07
      namespace: ai-workloads
      labels:
        app: vllm-test-07
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: vllm-test-07
      template:
        metadata:
          labels:
            app: vllm-test-07
            kai.scheduler/queue: test
          annotations:
            gpu-fraction: "0.7"
        spec:
          schedulerName: kai-scheduler
          containers:
          - name: vllm
            image: vllm/vllm-openai:latest
            command: ["/bin/sh", "-c"]
            args: [
    	      "vllm serve Qwen/Qwen2.5-1.5B-Instruct --gpu-memory-utilization=0.7 --host 0.0.0.0"
            ]
            ports:
            - containerPort: 8000
            resources:
              limits:
                cpu: "8"
                memory: 15G
              requests:
                cpu: "6"
                memory: 6G
            startupProbe:
              httpGet:
                path: /health
                port: 8000
              periodSeconds: 10
              failureThreshold: 60
              timeoutSeconds: 5
            livenessProbe:
              httpGet:
                path: /health
                port: 8000
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            readinessProbe:
              httpGet:
                path: /health
                port: 8000
              periodSeconds: 5
              timeoutSeconds: 5
              failureThreshold: 3
    EOF
    ```

3. Verify that the deployment is allocated with the specified resources:

    ```shell
    kubectl -n ai-workloads get pods -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,GPU-FRACTION:.metadata.annotations.gpu-fraction,GPU-GROUP:.metadata.labels.runai-gpu-group"
    ```
    ```
    NAME                            STATUS    NODE                       GPU-FRACTION   GPU-GROUP
    vllm-test-07-5979b99584-llf45   Running   k8s-gpu-md-0-wr9k6-gbtvr   0.7            407623a2-216d-4c06-b5b8-f8345bf28b5a
    ```

    Wait until the STATUS column reaches the `Running` state before continuing, this may take several minutes. 

4. Deploy a Kubernetes service to access the API
    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Service
    metadata:
      name: vllm-test-07
      namespace: ai-workloads
    spec:
      ports:
      - name: http
        port: 80
        protocol: TCP
        targetPort: 8000
      selector:
          app: vllm-test-07
      sessionAffinity: None
      type: ClusterIP
    EOF
    ```

    Check the service:
    ```shell
    kubectl -n ai-workloads get svc
    ```
    ```
    NAME           TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
    vllm-test-07   ClusterIP   10.43.119.6   <none>        80/TCP    39s
    ```

5. Port forward the service through `kubectl`
    ```shell
    kubectl -n ai-workloads port-forward svc/vllm-test-07 9000:80 &
    ```

5. Test the deployment by sending a request to the vLLM service API:
    ```shell
    curl http://localhost:9000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
            "model": "Qwen/Qwen2.5-1.5B-Instruct",
            "prompt": "San Francisco is a",
            "max_tokens": 7,
            "temperature": 0
        }' | jq .
    ```

    You should receive a response similar to the following:
    ```json
    {
        "id": "cmpl-173532a758894deeae63d0a073c53289",
        "object": "text_completion",
        "created": 1763393534,
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "choices": [
            {
            "index": 0,
            "text": " city in the state of California,",
            "logprobs": null,
            "finish_reason": "length",
            "stop_reason": null,
            "token_ids": null,
            "prompt_logprobs": null,
            "prompt_token_ids": null
            }
        ],
        "service_tier": null,
        "system_fingerprint": null,
        "usage": {
            "prompt_tokens": 4,
            "total_tokens": 11,
            "completion_tokens": 7,
            "prompt_tokens_details": null
        },
        "kv_transfer_params": null
    }
    ```

Optionally, you might deploy another workload with a small GPU fraction on that node.

1. Create another workload with a GPU memory fraction of `0.2`:
    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: apps/v1
    kind: Deployment
    metadata:
        name: vllm-test-02
        namespace: ai-workloads
        labels:
            app: vllm-test-02
    spec:
        replicas: 1
        selector:
            matchLabels:
                app: vllm-test-02
        template:
            metadata:
                labels:
                    app: vllm-test-02
                    kai.scheduler/queue: test
                annotations:
                    gpu-fraction: "0.2"
            spec:
                schedulerName: kai-scheduler
                containers:
                  - name: vllm
                    image: vllm/vllm-openai:latest
                    command: ["/bin/sh", "-c"]
                    args: [
                    "vllm serve Qwen/Qwen2.5-1.5B-Instruct --gpu-memory-utilization=0.2"
                    ]
                    ports:
                        - containerPort: 8000
                    resources:
                        limits:
                            cpu: "8"
                            memory: 15G
                        requests:
                            cpu: "6"
                            memory: 6G
                    startupProbe:
                      httpGet:
                        path: /health
                        port: 8000
                      periodSeconds: 10
                      failureThreshold: 60
                      timeoutSeconds: 5
                    livenessProbe:
                      httpGet:
                        path: /health
                        port: 8000
                      periodSeconds: 10
                      timeoutSeconds: 5
                      failureThreshold: 3
                    readinessProbe:
                      httpGet:
                        path: /health
                        port: 8000
                      periodSeconds: 5
                      timeoutSeconds: 5
                      failureThreshold: 3
    EOF
    ```

2. Check that the fraction is successfully assigned and the pod is running:

    ```shell
    kubectl -n ai-workloads get pods -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName,GPU-FRACTION:.metadata.annotations.gpu-fraction,GPU-GROUP:.metadata.labels.runai-gpu-group"
    ```
    ```
    NAME                            STATUS    NODE                       GPU-FRACTION   GPU-GROUP
    vllm-test-02-79b48968bc-dtzxs   Running   k8s-gpu-md-0-wr9k6-gbtvr   0.2            407623a2-216d-4c06-b5b8-f8345bf28b5a
    vllm-test-07-5979b99584-llf45   Running   k8s-gpu-md-0-wr9k6-gbtvr   0.7            407623a2-216d-4c06-b5b8-f8345bf28b5a
    ```

3. Now deploy a second service to access the API of the second workload:

    ```yaml
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Service
    metadata:
      name: vllm-test-02
      namespace: ai-workloads
    spec:
      ports:
      - name: http
        port: 80
        protocol: TCP
        targetPort: 8000
      selector:
          app: vllm-test-02
      sessionAffinity: None
      type: ClusterIP
    EOF
    ```

    And create a port-forward for this second service on a different port:

    ```shell
    kubectl -n ai-workloads port-forward svc/vllm-test-02 9001:80 &
    ```

4. Then, from a separate terminal, try a request to the API:

    ```shell
    curl http://localhost:9001/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
            "model": "Qwen/Qwen2.5-1.5B-Instruct",
            "prompt": "San Francisco is a",
            "max_tokens": 7,
            "temperature": 0
        }' | jq .
    ```

With this validation, you have checked how you can efficiently share fractional GPU resources between workloads in an AI-Ready Kubernetes with the KAI Scheduler.

### Undeployment

Unless you intend to further use the deployed AI models or the KAI scheduler, we recommend undeploying everything prior to commencing with other deployments on your K8s Cluster. 

Undeploy the models:

```shell
kubectl -n ai-workloads delete deployment \
  vllm-test-07 \
  vllm-test-02
```

Undeploy the API services:

```shell
kubectl -n ai-workloads delete service \
  vllm-test-07 \
  vllm-test-02
```

Check the status:

```shell
kubectl -n ai-workloads get deployments,pods,services
```

Wait until the above command returns `No resources found in ai-workloads namespace.`.

Then uninstall the KAI scheduler with Helm:

```shell
helm uninstall kai-scheduler -n kai-scheduler
```

And then delete the namespace:

```shell
kubectl delete namespace kai-scheduler --ignore-not-found
kubectl delete namespace kai-resource-reservation --ignore-not-found
```

## Next Steps

After powering your AI Factory with NVIDIA KAI Scheduler on Kubernetes, you may continue with [NVIDIA Dynamo on Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo" %}}) as an additional validation procedure built on top of K8s.
