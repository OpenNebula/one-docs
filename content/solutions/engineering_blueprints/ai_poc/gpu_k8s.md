---

title: "Deploying GPU-enabled Kubernetes Clusters"
linkTitle: "GPU Kubernetes Clusters"
description: ""
weight: 5

---

[OneKS]({{% relref "/platform_services/oneks/" %}})  is OpenNebula's powerful Kubernetes Cluster provisioning and management tool. It enables simple, streamlined deployment of GPU-enabled Kubernetes Clusters on OpenNebula clouds to handle AI and HPC workloads. 

In this guide, you will deploy a GPU-enabled Kubernetes Cluster with OneKS and deploy a GPU workload on the Kubernetes Cluster using the [kubectl](https://kubernetes.io/docs/reference/kubectl/) command line tool.

## Before Starting

You will be using the following OpenNebula user account for this guide, ensure you have the credentials at hand:

* **llm-tenant-admin**

This user has been preconfigured with the necessary permissions to complete this guide. The necessary templates to launch a GPU-enabled OneKS Kubernetes Cluster have been prepared  for the user. This user also sees the **LLM Tenant** view, which allows access to the Kubernetes Cluster and OneLLM management functionality needed to launch and manage the GPU-enabled Kubernetes Cluster and deploy LLM models for inferencing. 

Log in with your **llm-tenant-admin** account using the credentials you received before starting step 1.

## Prerequisites: Install kubectl and Helm

On your local machine, download the latest patch release for Kubernetes 1.35:

{{< tabpane text=true right=false >}}
{{% tab header="**Architecture**:" disabled=true /%}}

{{% tab header="x86-64"%}}
```shell
curl -fLO "https://dl.k8s.io/release/$(curl -fsSL \
https://dl.k8s.io/release/stable-1.35.txt)/bin/linux/amd64/kubectl"
```
{{% /tab %}}

{{% tab header="ARM64"%}}
```shell
curl -fLO "https://dl.k8s.io/release/$(curl -fsSL \
https://dl.k8s.io/release/stable-1.35.txt)/bin/linux/arm64/kubectl"
```
{{% /tab %}}
{{< /tabpane >}}

Then install kubectl:

```shell
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

Install Helm version 4:


```shell
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 | bash
```

## Step 1: Create the Cluster

Go to **Kubernetes -> K8S Clusters** and select **+ Create Kubernetes Cluster**:

{{< image path="/images/poc/ai_poc/light/poc_create_k8s.png" 
          pathDark="/images/poc/ai_poc/dark/poc_create_k8s.png" 
alt="OneKS Create Cluster" align="center" width="90%" mb="20px" >}}

Then follow the steps of the Create Kubernetes Cluster wizard:

{{< image path="/images/poc/ai_poc/light/poc_name_cluster.png" 
          pathDark="/images/poc/ai_poc/dark/poc_name_cluster.png" 
alt="OneKS Create Cluster" align="center" width="90%" mb="20px" >}}

* **General**: Name the Cluster, e.g. `gpu-cluster` or `inference-cluster`
* **Select Cluster**: Select the OpenNebula Cluster to Host your K8s Cluster - **0 default** 
* **Select a public Virtual Network**: Select the Virtual Network named **llm-tenant-public**
* **Select a private Virtual Network**: Select the Virtual Network named **llm-tenant-private**
* **K8s version**: Select version *1.35.0*
* **Flavours**: Select *Single-Node Control Plane*
* **User inputs**: No changes required

Click **Finish** in the final step to start the provisioning process. You can monitor the provisioning progress int the **Kubernetes Logs** view. The K8s Cluster will take several minutes to complete provisioning. Proceed with the next step once the K8s Cluster reaches the RUNNING state:

{{< image path="/images/poc/ai_poc/light/poc_k8s_running.png" 
          pathDark="/images/poc/ai_poc/dark/poc_k8s_running.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

## Step 2: Scale the K8s Cluster

Once the K8s Cluster has entered the RUNNING state, go to **Kubernetes -> K8S Clusters**, select the K8s Cluster in the list to open its details panel then select the **Node Groups** tab, click **+ Create Node Group**:

{{< image path="/images/poc/ai_poc/light/poc_scale_k8s.png"
          pathDark="/images/poc/ai_poc/dark/poc_scale_k8s.png" 
alt="OneKS scale Cluster" align="center" width="90%" mb="20px" >}}

* In the **General** step enter a name, e.g. `gpu-worker` or `inference-worker`
* In the **Family** step choose the **OneLLM Workers** family 
* In the **Flavours** step choose the **Medium OneLLM Worker Nodes** flavour 
* In the **User inputs** step set the **Count** as 1

Click **Finish** and you will see the scaling progress in the **Logs** view. Once the node has changed from the SCALING state to RUNNING, proceed with the next step:

{{< image path="/images/poc/ai_poc/light/poc_k8s_node_running.png" 
          pathDark="/images/poc/ai_poc/dark/poc_k8s_node_running.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

### Ensure the GPU is Attached

Once the new node group enters the RUNNING state, in **Kubernetes -> K8S Clusters** select the K8s Cluster that you just launched. In the **Node Groups** tab, select the new node group in the node group list and click on the node itself in the node list:

{{< image path="/images/poc/ai_poc/light/poc_inspect_node.png" 
          pathDark="/images/poc/ai_poc/dark/poc_inspect_node.png"
alt="OneKS inspect node" align="center" width="90%" mb="20px" >}}

This will open the node's details view. In the **PCI** tab, you should see the GPU listed in the PCI devices:

{{< image path="/images/poc/ai_poc/light/poc_node_gpu.png" 
          pathDark="/images/poc/ai_poc/dark/poc_node_gpu.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

In this case we see the hexadecimal PCI device codes for an NVIDIA L40S:

* **Class**: 0302
* **Device**: 26b9
* **Vendor**: 10de

If you see your GPU in this list, your K8s worker node has successfully attached to the GPU.

## Step 3: Copy the kubeconfig

The kubeconfig contains the details and credentials of the K8s Cluster you have just created, it is necessary to interact with the Cluster through kubectl.

Close the details panel of the node group and go to the **Kubeconfig** tab. Copy and save the kubeconfig details into a file named *kubeconfig* in your local machine with a text editor:

{{< image path="/images/poc/ai_poc/light/poc_kubeconfig.png" 
          pathDark="/images/poc/ai_poc/dark/poc_kubeconfig.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

Open a terminal on your local machine and execute the following commands:

*  Export the KUBECONFIG environment variable in the terminal at the beginning of any kubectl session to direct kubectl to the Kubenetes Cluster details and credentials:

    ```shell
    export KUBECONFIG="$PWD/kubeconfig"
    ```

* Check that kubectl can access the Cluster:

    ```shell
    kubectl get nodes
    ```

* The output should look similar to the following:

    ```default
    NAME                                                 STATUS   ROLES                AGE   VERSION
    controlplane-general-standalone-44c7fcc86fd3-kbkb4   Ready    control-plane,etcd   22m   v1.35.0+rke2r1
    nodegroup-general-large-7fc21d43cda5-hv9j2-xs267     Ready    <none>               15m   v1.35.0+rke2r1
    ```

Wait until both the control-plane node and the worker node report `Ready` before continuing. A OneKS node group can be `RUNNING` while the worker is still initializing Kubernetes. If a node is missing or shows `NotReady`, wait and repeat the command.

This confirms that the K8s Cluster is operating properly and kubectl can access it.

## Step 4: Install the NVIDIA GPU Operator (Optional)

{{< alert title="This section is optional" type="primary" >}}If you are moving on to the **OneLLM** deployment in the following guide, it is not necessary to install the NVIDIA GPU Operator. You can advance to step 6.{{< /alert >}} 

Add the NVIDIA Helm repo:

```shell
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia \
&& helm repo update
```

Install the NVIDIA GPU Operator, this command may require a few minutes:

```shell
# create gpu-operator namespace
kubectl create ns gpu-operator

# allow the privileged workloads required by GPU Operator
kubectl label --overwrite ns gpu-operator \
    pod-security.kubernetes.io/enforce=privileged

# install NVIDIA GPU Operator
helm install --wait --generate-name \
    -n gpu-operator \
    nvidia/gpu-operator \
    --version=v26.7.0 \
    --set cdi.nriPluginEnabled=true
```

After a few minutes you should receive output like this:

```default
NAME: gpu-operator-1790086490
LAST DEPLOYED: Tue Sep 22 14:14:51 2026
NAMESPACE: gpu-operator
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

The previous output confirms that the NVIDIA GPU Operator installed correctly. Now check **gpu-operator** pods:

```shell
kubectl get pods -n gpu-operator
```

Expected output:

```default
NAME                                                              READY   STATUS      RESTARTS   AGE
gpu-feature-discovery-9jfmt                                       1/1     Running     0          7m33s
gpu-operator-1790086490-node-feature-discovery-gc-5575668f29f7n   1/1     Running     0          7m47s
gpu-operator-1790086490-node-feature-discovery-master-d45bq87r7   1/1     Running     0          7m47s
gpu-operator-1790086490-node-feature-discovery-worker-m94bc       1/1     Running     0          7m47s
gpu-operator-1790086490-node-feature-discovery-worker-zv5lc       1/1     Running     0          7m47s
gpu-operator-558cc5d94f-hjvp2                                     1/1     Running     0          7m47s
nvidia-container-toolkit-daemonset-s7jb9                          1/1     Running     0          7m35s
nvidia-cuda-validator-6895r                                       0/1     Completed   0          4m37s
nvidia-dcgm-exporter-n6bsg                                        1/1     Running     0          7m33s
nvidia-device-plugin-daemonset-r4lkl                              1/1     Running     0          7m34s
nvidia-driver-daemonset-bxbz9                                     1/1     Running     0          7m35s
nvidia-operator-validator-hzsrc                                   1/1     Running     0          7m34s
```

Check the worker node, first identify the node name with `kubectl get nodes` as above then describe the node:

```shell
kubectl describe node <kubernetes_workload_node_name>
```

In this example the node is named `nodegroup-general-large-7fc21d43cda5-hv9j2-xs267` so the command would look like this: 

```shell
kubectl describe node nodegroup-general-large-7fc21d43cda5-hv9j2-xs267
```

The output of `kubectl describe node` will be verbose. Scroll through the output and you should see lines similar to the below example with details matching the model and specs of your GPU:

```default
...
nvidia.com/gpu.machine=Ubuntu-24.04-PC-Q35-ICH9-2009
nvidia.com/gpu.memory=46068
nvidia.com/gpu.mode=compute
nvidia.com/gpu.present=true
nvidia.com/gpu.product=NVIDIA-L40S
nvidia.com/gpu.replicas=1
nvidia.com/gpu.sharing-strategy=none
nvidia.com/mig.capable=false
nvidia.com/mig.strategy=single
nvidia.com/mps.capable=false
nvidia.com/vgpu.present=false
...
```

## Step 5: Validate with VectorAdd (Optional)

{{< alert title="This section is optional" type="primary" >}}If you are moving on to the **OneLLM** deployment in the following guide, it is not necessary to install or validate the NVIDIA GPU Operator. You can advance to step 6.{{< /alert >}} 

Deploy a simple CUDA vector-addition workload to verify that Kubernetes can schedule a workload onto the GPU worker and execute CUDA kernels on the attached GPU. The workload copies vectors to GPU memory, performs the addition using a CUDA kernel, copies the result back to the container, and verifies the result.

Create a YAML file named `vector-add.yaml` with the following manifest:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cuda-vectoradd
spec:
  template:
    spec:
      containers:
        - name: cuda-vectoradd
          image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0-ubuntu22.04
          resources:
            limits:
              nvidia.com/gpu: 1
      restartPolicy: Never
  backoffLimit: 0
```

Then apply and watch:

```shell
kubectl apply -f vector-add.yaml && kubectl get pods -l job-name=cuda-vectoradd -w
```

```default
cuda-vectoradd-m4bnc   0/1     Pending   0          0s
cuda-vectoradd-m4bnc   0/1     ContainerCreating   0          0s
cuda-vectoradd-m4bnc   1/1     Running             0          1s
cuda-vectoradd-m4bnc   0/1     Completed           0          2s
```

Once you see **Completed**, exit with **Ctrl-C** then check the logs:

```shell
kubectl logs job/cuda-vectoradd
```

Expected output:

```default
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done
```

The **Test PASSED** response shows that your K8s Cluster is properly configured and ready to deploy workloads on the GPU. 

Clean up by deleting the VectorAdd validation job:


```shell
kubectl delete -f vector-add.yaml
```

If you are continuing with the OneLLM deployment guides, you need to [uninstall the NVIDIA GPU Operator]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s/#optional-undeploy-the-nvidia-gpu-operator" %}}) before proceeding to the next step.


## Step 6: Check the Operator View

Go to the **Instances VMs** view. You will see their the various VMs that have been provisioned for the K8s Cluster, each serving a different role. They should be named similarly to the following:

* **Virtual Router**: `vr-controlplane-general-*`
* **Control Plane**: `controlplane-general-*`
* **K8s Worker**: `nodegroup-onellm-*`

{{< image path="/images/poc/ai_poc/light/poc_k8s_vms.png" 
          pathDark="/images/poc/ai_poc/dark/poc_k8s_vms.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

Note that you do not see the vLLM VM that you launched in the previous guide since the resources of the **vm-tenant-admin** and **llm-tenant-admin** are isolated.

Now sign out of the **llm-tenant-admin** account (or open a separate browser session) and sign into the **ncp-operator** account. Go to **Instances -> VMs**:

{{< image path="/images/poc/ai_poc/light/poc_operator_vms.png" 
          pathDark="/images/poc/ai_poc/dark/poc_operator_vms.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

Since the **ncp-operator** has administrative privileges, they have visibility over the resources (including VMs, Clusters, Virtual Networks, Templates, etc.) of other users and, depending upon configuration, create, delete or modify resources of other users. Administrative users can also set quotas for users to limit their access to resources, including restricting the number of VMs, CPU limits, and even GPU allocation.  

## Next Steps

Contratulations! You have deployed a GPU-enabled Kubernetes Cluster using OneKS, installed the GPU Operator and validated it with a simple GPU workload. 

This concludes the AI Factory PoC guided tour. You may now want to continue with advanced AI Kubernetes deployments such as [NVIDIA Dynamo]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo/" %}}) or the [NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler/" %}}).

## PoC Success Criteria

Completing this guide fulfills the following PoC success criteria:

* [AI-SC7]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Deploy a GPU-enabled Kubernetes Cluster
* [AI-SC8]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Schedule a Kubernetes GPU Workload
* [AI-SC9]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Validate NVIDIA GPU Operator Integration
