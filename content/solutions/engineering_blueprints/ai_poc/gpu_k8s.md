---
title: "Kubernetes as a Service with OneKS"
linkTitle: "Kubernetes as a Service"
description: ""
weight: 5
---

Use [OneKS]({{% relref "platform_services/oneks/" %}}) to provide a Kubernetes cluster with a GPU worker. The NCP operator prepares access to the appliance, the tenant administrator manages the cluster, and the end user runs GPU workloads with `kubectl`.

| Role | Interface | Work |
| --- | --- | --- |
| NCP operator | Sunstone **Admin** view | Prepare the tenant resources and grant access to the OneKS appliance template and image. |
| Tenant administrator | Sunstone **OneKS view** and `kubectl` | Create the cluster and GPU worker, install GPU Operator, and provide Kubernetes access. |
| End user | `kubectl` | Submit a GPU workload, read its result, and delete the workload. |

## Before Starting

Connect to the PoC VPN as described in the [Connection Guide]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}}). The **ncp-operator** must complete [Multitenancy]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}}) for the OneKS service. This includes the group and administrator, **OneKS view**, public and private networks, VDC resources and quotas.

This guide uses `k8s-tenant` and `k8s-tenant-admin` as example names. Use the names and network settings supplied for your tenant.

The PoC must provide an available GPU, a worker flavour configured for GPU passthrough, and the **NVIDIA GPU Operator** application. The tenant administrator and end user need `kubectl` on their local machines. Follow the [Kubernetes installation instructions](https://kubernetes.io/docs/tasks/tools/) for your operating system. Use a client version compatible with the cluster.

For LLM inference through LiteLLM, follow [Token Factory (OneLLM)]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}). That service uses OneLLM Ready to install its GPU software stack. This page describes the standalone Kubernetes service.

## NCP Operator

Sign into Sunstone as **ncp-operator**. Complete the shared [Kubernetes network preparation]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/#kubernetes-services-oneks-and-onellm" %}}) before granting appliance access.

### Identify the OneKS Appliance

1. Open **Templates -> VM Templates** and find the OneKS appliance template supplied for the PoC.
2. Record its template ID.
3. Open its disk configuration and record the ID of each backing image.
4. Confirm that these images are **READY** and stored in an image datastore available to the tenant through its VDC.

The appliance template and images can remain owned by the NCP operator. Use ACLs to give the tenant access.

### Grant the Tenant Appliance Access

In **System -> ACLs**, create a rule with these settings:

| Field | Value |
| --- | --- |
| Users | **A group**: `k8s-tenant` |
| Resources | **Virtual Machine Template** |
| Resource identifier | **Identifier**: the OneKS appliance template ID |
| Rights | **Use** |
| Zone | The zone that contains the appliance |

Review the summary and click **Finish**. Use the template ID from your installation, for example `88`.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/acl-template-summary.png"
  alt="Grant the Kubernetes tenant USE access to the OneKS appliance template" align="center" width="90%" mb="20px"
>}}

Create a second rule for each backing image. Keep **A group** set to `k8s-tenant`, select **Image**, set **Resource identifier** to **Identifier**, enter the image ID, and grant **Use** in the same zone.

For an operator-owned image, use its specific ID. Selecting the tenant under resource scope **Group** grants access to tenant-owned images and does not share this appliance image.

The image example selects **Identifier** and enters image ID `27`. Use the image ID recorded from your appliance template.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/acl-image-identifier.png"
  alt="Select Identifier scope and enter the operator-owned OneKS appliance image ID" align="center" width="90%" mb="20px"
>}}

Confirm that the summary grants the tenant group **Use** on that image in the selected zone, then click **Finish**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/acl-image-summary.png"
  alt="Grant the Kubernetes tenant group USE on image ID 27 in zone 0" align="center" width="90%" mb="20px"
>}}

Give the tenant administrator the account credentials, public and private network names, and available GPU worker flavour. Tenant creation and infrastructure allocation are covered in Multitenancy.

## Tenant Administrator

Sign into Sunstone as **k8s-tenant-admin**. The account opens with **OneKS view**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/tenant-view.png"
  alt="Tenant administrator in the OneKS service view" align="center" width="90%" mb="20px"
>}}

### Step 1: Create the Kubernetes Cluster

Open **Kubernetes -> K8S Clusters** and click **Create Kubernetes Cluster**.

1. In **General**, enter a name, for example `gpu-cluster`.
2. Select the public network supplied by the NCP operator, for example `k8s-public`.
3. Select the private network, for example `k8s-private`.
4. Select the Kubernetes version. For this example, use `v1.35.0`.
5. Select **Single-Node Control Plane** for this PoC.
6. Review **User inputs**. For this example, use one control-plane VM with **8192 MiB** of memory.
7. Click **Finish**.

If the wizard asks for an OpenNebula cluster, select the physical cluster assigned to the tenant. This is the infrastructure where the Kubernetes VMs will run.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-general.png"
  alt="Name the Kubernetes cluster in the OneKS creation wizard" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-public-network.png"
  alt="Select the public network assigned to the Kubernetes tenant" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-private-network.png"
  alt="Select the private network for communication between cluster nodes" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-flavour.png"
  alt="Select the Single-Node Control Plane flavour" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-resources.png"
  alt="Review the control-plane VM count and resource inputs" align="center" width="90%" mb="20px"
>}}

Follow provisioning in **Logs**. Wait until the cluster is **Running** before adding a worker. At this stage, OneKS has created the cluster router and control plane.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/cluster-running.png"
  alt="Kubernetes cluster Running after control-plane provisioning" align="center" width="90%" mb="20px"
>}}

### Step 2: Add a GPU Worker

Select the cluster and open **Node Groups**. Click **Create Node Group**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/node-groups.png"
  alt="Create a node group in the Kubernetes cluster" align="center" width="90%" mb="20px"
>}}

1. Enter a name, for example `gpu-pool`.
2. Select **OneLLM Workers** as the GPU-enabled family.
3. Select **Large OneLLM Worker Nodes** as the flavour.
4. Set **Count** to `1` and review the CPU, memory and disk inputs.
5. Click **Finish** and follow progress in **Logs**.
6. Wait until the cluster and node group return to **Running**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/worker-family.png"
  alt="Select the GPU-enabled worker family supplied for the PoC" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/worker-flavour.png"
  alt="Select the Large OneLLM Worker Nodes flavour" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/worker-resources.png"
  alt="Create one GPU worker with the assigned CPU, memory and disk resources" align="center" width="90%" mb="20px"
>}}

Open the node group's VM and select **PCI**. Confirm that the assigned GPU appears in the device list. An NVIDIA L40S has vendor `10de`, device `26b9` and class `0302`.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/worker-pci.png"
  alt="GPU device attached to the Kubernetes worker VM" align="center" width="90%" mb="20px"
>}}

### Step 3: Retrieve the Administrative Kubeconfig

Return to the cluster details and open **Kubeconfig**. Copy the configuration and save it on your laptop as `oneks-admin.conf`.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/admin-kubeconfig.png"
  alt="OneKS Kubeconfig tab and copy action for the tenant administrator" align="center" width="90%" mb="20px"
>}}

In the directory that contains the file, run:

```shell
chmod 600 oneks-admin.conf
export KUBECONFIG="$PWD/oneks-admin.conf"
kubectl get nodes
```

Wait until the control plane and worker both show **Ready**. OneKS can report the VM as Running while Kubernetes is still initializing the node.

Keep this administrative kubeconfig for cluster management. Step 5 describes end-user access.

### Step 4: Install NVIDIA GPU Operator

Open **Applications** in the cluster details and click **Install Application**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/applications.png"
  alt="Open the cluster Applications tab to install GPU Operator" align="center" width="90%" mb="20px"
>}}

Select **NVIDIA GPU Operator** and click **Next**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/gpu-operator-select.png"
  alt="Select NVIDIA GPU Operator from the OneKS application catalog" align="center" width="90%" mb="20px"
>}}

Set **Release name** and **Target namespace** to `gpu-operator`. Enable **Create namespace if it does not exist**, then click **Finish**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/gpu-operator-config.png"
  alt="Configure the GPU Operator release name and target namespace" align="center" width="90%" mb="20px"
>}}

Wait until the application is **Ready** and the cluster is **Running**.

{{< image
  path="/images/poc/ai_poc/kubernetes_as_a_service/gpu-operator-ready.png"
  alt="NVIDIA GPU Operator application Ready in the Kubernetes cluster" align="center" width="90%" mb="20px"
>}}

Check the GPU software and resources with the administrative kubeconfig:

```shell
kubectl -n gpu-operator get pods
kubectl get nodes \
  -o 'custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

Wait for the running GPU Operator workloads to become Ready. Validation Pods can finish with **Completed** status. The GPU worker must report a positive value for `nvidia.com/gpu` before the user submits the test.

### Step 5: Provide End-User Access

Use [Multi-tenant Access to OneKS Managed Kubernetes Clusters]({{% relref "platform_services/oneks/management/multi_tenant/" %}}) to prepare the user's Kubernetes identity, namespace, permissions and kubeconfig.

For the VectorAdd procedure, the user needs permission to create, get, list, watch, patch, update and delete Jobs; get, list and watch Pods and Events; and read Pod logs in the assigned namespace. These permissions belong in Kubernetes RBAC. A Sunstone view does not grant Kubernetes API access.

Give the end user:

* Their kubeconfig, with access to the Kubernetes API through the VPN.
* Their assigned namespace.
* Confirmation that GPU capacity is available for a workload requesting `nvidia.com/gpu: 1`.

## End User

Use the kubeconfig and namespace supplied by the tenant administrator. You do not need Sunstone to run this procedure.

### Step 1: Connect to Kubernetes

Save your kubeconfig as `oneks-user.conf`. In the same directory, run:

```shell
chmod 600 oneks-user.conf
export KUBECONFIG="$PWD/oneks-user.conf"
export WORKLOAD_NAMESPACE="gpu-workloads"
kubectl -n "$WORKLOAD_NAMESPACE" get pods
```

Replace `gpu-workloads` with your assigned namespace. An empty Pod list is valid when you have not submitted any workloads.

### Step 2: Submit the VectorAdd Test

Save the following manifest as `vector-add.yaml`. The Job requests one GPU resource and runs a CUDA vector-addition test.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cuda-vectoradd
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: cuda-vectoradd
          image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0-ubuntu22.04
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
          resources:
            limits:
              nvidia.com/gpu: 1
```

Submit the Job and watch its Pod:

```shell
kubectl -n "$WORKLOAD_NAMESPACE" apply -f vector-add.yaml
kubectl -n "$WORKLOAD_NAMESPACE" get pods -l job-name=cuda-vectoradd -w
```

The Pod changes to **Completed**. The PoC test produced this output:

```default
NAME                   READY   STATUS              RESTARTS   AGE
cuda-vectoradd-kkxll    0/1     ContainerCreating   0          5s
cuda-vectoradd-kkxll    0/1     Completed           0          8s
```

Press **Ctrl-C** to stop watching, then read the log:

```shell
kubectl -n "$WORKLOAD_NAMESPACE" logs job/cuda-vectoradd
```

The successful test reports:

```default
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done
```

**Test PASSED** confirms that the workload ran its CUDA computation on the GPU and checked the result.

If the Job does not complete, inspect its Pod and events:

```shell
kubectl -n "$WORKLOAD_NAMESPACE" get pods -l job-name=cuda-vectoradd
kubectl -n "$WORKLOAD_NAMESPACE" describe pods -l job-name=cuda-vectoradd
```

A Pending Pod can indicate that no GPU resource is free. Give the tenant administrator the Pod status and events if you need help.

### Step 3: Delete the Test Workload

```shell
kubectl -n "$WORKLOAD_NAMESPACE" delete -f vector-add.yaml
```

This removes the test Job and its Pod and releases the GPU resource for another workload.

## Next Steps

The tenant administrator can manage node groups and applications in OneKS. End users can submit other workloads within their assigned Kubernetes permissions and available resources.

For LLM model deployment and consumption through LiteLLM, use the separate [Token Factory (OneLLM)]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}).

## PoC Success Criteria

Completing this guide covers these PoC success criteria:

* [AI-SC7]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Deploy a GPU-enabled Kubernetes cluster.
* [AI-SC8]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Schedule a Kubernetes GPU workload.
* [AI-SC9]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Validate NVIDIA GPU Operator integration.
