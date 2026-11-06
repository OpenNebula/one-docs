---

title: "GPU-enabled Virtual Machines and Kubernetes Clusters"
linkTitle: "GPU VMs and Kubernetes"
description: ""
weight: 8

---

## Deploying an LLM using the vLLM Appliance

Having explored OpenNebula's multi-tenancy model in the [previous guide]({{% relref "solutions/engineering_blueprints/ee_poc/access_permissions" %}}), you can now move on to exploring OpenNebula's AI capabilities by deploying a GPU-enabled Virtual Machine. 

Sign into Sunstone as the **poc-tenant** user with the credentials given to you by your OpenNebula PoC contact.

## Step 1: Find and Import the vLLM Appliance

Go to **Storage -> Apps**, search for the **service_Vllm** appliance and import it. Leave the name as it is and select the **default** datastore during the import wizard:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_template.png"
  path="/images/poc/ai_poc/light/poc_vllm_template.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

## Step 2: Update the Template to Attach the GPU

Go to **Templates -> VM Templates** and select the **service_Vllm** template, then press update (the pencil icon):

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_update_template.png"
  path="/images/poc/ai_poc/light/poc_update_template.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Click next in the wizard to progress to the **Advanced options** step. Select the **PCI Devices** tab and select **+ Attach PCI Device**, choose the GPU device available in your PoC environment:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_attach_pci.png"
  path="/images/poc/ai_poc/light/poc_attach_pci.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Press **Continue** in the **Attach PCI device** dialog then press **Next** and then **Finish** to complete the update template wizard. 

## Step 3: Instantiate the vLLM Template

In **Templates -> VM Templates** select the **service_Vllm** template and press the play icon to instantiate it. Give the VM instance a name and press **Next** to the **User inputs** step. 

In this example, we want to use a non-default LLM model for inference. In the **MODEL** section of the **User inputs** page replace the default **Qwen/Qwen2.5-1.5B-Instruct model** with **HuggingFaceTB/SmolLM2-1.7B-Instruct**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_llm_model.png"
  path="/images/poc/ai_poc/light/poc_llm_model.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Press **Next** to progress to the **Advanced options** step, in the **Network** tab, select **Attach NIC**. Press Next in the first step, then select the **public** network so that the vLLM VM has a publicly available IP.

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_attach_nic.png"
  path="/images/poc/ai_poc/light/poc_attach_nic.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

In the **Network values** and **Select QoS** steps, do not alter the default settings, press **Next** and then **Finish** to complete the network settings. Then press **Finish** to deploy the VM.

## Step 4: Query the vLLM API and Try the Chat

You should be able to see the VM instance details in **Instances -> VMs**, wait until the VM has reached the RUNNING state:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_running.png"
  path="/images/poc/ai_poc/light/poc_vllm_running.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Take a note of the **IP Address** of the machine and use it to execute the following commands (replace <VLLM_VM_IP> with the IP you noted):

Query the model:

```shell
curl http://<VLLM_VM_IP>:8000/v1/models | jq .
```

You will receive a response similar to the following:

```json
{
  "object": "list",
  "data": [
    {
      "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
      "object": "model",
      "created": 1793869992,
      "owned_by": "vllm",
      "root": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
      "parent": null,
      "max_model_len": 1024,
      "permission": [
        {
          "id": "modelperm-8b3c55714a9139cc",
          "object": "model_permission",
          "created": 1793869992,
          "allow_create_engine": false,
          "allow_sampling": true,
          "allow_logprobs": true,
          "allow_search_indices": false,
          "allow_view": true,
          "allow_fine_tuning": false,
          "organization": "*",
          "group": null,
          "is_blocking": false
        }
      ]
    }
  ]
}
```

If the response `data` attribute is an empty list, it most likely means that the model has not loaded. A large model may take time to download. Keep querying the API until you see the above response.

Once you have confirmed that the model is loaded through the API, you can then access the web chat. Visit `http://<VLLM_VM_IP>:5000` in a separate browser tab and enter a prompt:

{{< image
  path="/images/poc/ai_poc/vllm_chat.png"
  alt="POC operator view" align="center" width="80%" mb="20px"
>}}

## Next Steps

Congratulations! You have now learned how to deploy a GPU-enabled Virtual Machine on OpenNebula and deploy a GPU workload through the vLLM framework. Now you can move on to [Deploying a OneKS Kubernetes Cluster](#deploying-a-gpu-enabled-kubernetes-cluster-with-oneks).

## Success Criteria

Completing this guide fulfills the following success criteria:

* [AI-SC2]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#gpu-instances" %}}): Deploy a VM with GPU resources

---

## Deploying a GPU-enabled Kubernetes Cluster with OneKS

In this guide, you will deploy a OneKS Kubernetes Cluster and deploy a GPU workload on the K8s Cluster using kubectl.

Sign in using the **poc-operator** account credentials you were provided by your OpenNebula PoC contact.

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

In the top left hand corner, switch to the **User** view to reveal the Kubernetes view. Go to **Kubernetes -> K8S Clusters** and select **+ Create Kubernetes Cluster**:

{{< image path="/images/poc/ai_poc/light/poc_create_k8s.png" 
          pathDark="/images/poc/ai_poc/dark/poc_create_k8s.png" 
alt="OneKS Create Cluster" align="center" width="90%" mb="20px" >}}

Then follow the steps of the Create Kubernetes Cluster wizard:

{{< image path="/images/poc/ai_poc/light/poc_name_cluster.png" 
          pathDark="/images/poc/ai_poc/dark/poc_name_cluster.png" 
alt="OneKS Create Cluster" align="center" width="90%" mb="20px" >}}

* **General**: Name the Cluster, e.g. `gpu-cluster`
* **Select Cluster**: Select the OpenNebula Cluster to Host your K8s Cluster: `0 default` 
* **Select a public Virtual Network**: Select the public Virtual Network (`public`)
* **Select a private Virtual Network**: Select the private Virtual Network (`private-k8s`)
* **K8s version**: Select version *1.35.0*
* **Flavours**: Select *Single-Node Control Plane*
* **User inputs**: No changes required

You can monitor the provisioning progress int the **Kubernetes Logs** view. Proceed with the next step once the K8s Cluster has reached the RUNNING state.

## Step 2: Scale the K8s Cluster

Once the K8s Cluster has entered the RUNNING state, go to **Kubernetes -> K8S Clusters**, select the K8s Cluster in the list to open its details panel then select the **Node Groups** tab, click **+ Create Node Group**:

{{< image path="/images/poc/ai_poc/light/poc_scale_k8s.png"
          pathDark="/images/poc/ai_poc/dark/poc_scale_k8s.png" 
alt="OneKS scale Cluster" align="center" width="90%" mb="20px" >}}

* In the **General** step enter a name, e.g. `gpu-worker`
* In the **Flavours** step choose the **Large Worker Nodes** flavour 
* In the **User inputs** step set the **Count** as 1

Click **Finish** and you will see the progress in the **Logs** view. Once the node has changed from the SCALING state to RUNNING, proceed with the next step.

### Ensure the GPU is Attached

Once the new node group enters the RUNNING state, select the K8s Cluster, in the **Node Groups** tab, select the new node group in the node group list and click on the node itself in the node list:

{{< image path="/images/poc/ai_poc/light/poc_inspect_node.png" 
          pathDark="/images/poc/ai_poc/dark/poc_inspect_node.png"
alt="OneKS inspect node" align="center" width="90%" mb="20px" >}}

This will open the node's details view. In the **PCI** tab, you should see the GPU listed in the PCI devices:

{{< image path="/images/poc/ai_poc/light/poc_node_gpu.png" 
          pathDark="/images/poc/ai_poc/dark/poc_node_gpu.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

If you see your GPU in this list, your K8s worker node has successfully attached to the GPU.

## Step 3: Copy the kubeconfig

Close the details panel of the node group and go to the **Kubeconfig** tab. Copy and save the kubeconfig details into a file locally with a text editor. The kubeconfig contains the details and credentials of the K8s Cluster you have just created, it is necessary to interact with the Cluster through kubectl:

{{< image path="/images/poc/ai_poc/light/poc_kubeconfig.png" 
          pathDark="/images/poc/ai_poc/dark/poc_kubeconfig.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

Open a terminal on your local machine and execute the following commands:

*  Export the KUBECONFIG environment variable in the terminal at the beginning of any kubectl session:

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

## Step 4: Install the NVIDIA GPU Operator

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

The previous output confirms that the NVIDIA GPU Operator installed correctly. Now check gpu-operator pods:

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

## Step 5: Validate with VectorAdd

Deploy a simple CUDA vector-addition workload to verify that Kubernetes can schedule a workload onto the GPU worker and execute CUDA kernels on the attached GPU. The workload copies vectors to GPU memory, performs the addition using a CUDA kernel, copies the result back to the container, and verifies the result.

Create `vector-add.yaml`

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

Exit with **Ctrl-C** then check the logs:

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

## Sharing the Kubernetes Cluster

Using OpenNebula's multi-tenancy features, a K8s Cluster launched by OneKS can be easily shared with teammates. In the **Kubernetes -> K8S Clusters** view, click on the **gpu-cluster** you created to open its information panel. In the **Permissions** section, select the **Group** option in the **Use** column:

{{< image path="/images/poc/ai_poc/light/poc_share_k8s.png" 
          pathDark="/images/poc/ai_poc/dark/poc_share_k8s.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

If you now sign into the **poc-tenant** account, since it is in the same group as **poc-operator**, you will be able to see the **gpu-cluster** K8s Cluster in **Kubernetes -> K8S Clusters** and retrieve the kubeconfig to deploy GPU workloads.  

## Next Steps

Contratulations! You have now deployed a GPU-enabled Kubernetes Cluster using OneKS, installed the GPU Operator and validated it with a simple GPU workload. You can now move on to deploy more complex AI Kubernetes frameworks such as [NVIDIA Dynamo]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo/" %}}) or the [NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler/" %}}).

## Success Criteria

Completing this guide fulfills the following success criteria:

* [AI-SC7]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Deploy a GPU-enabled Kubernetes Cluster
* [AI-SC8]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Schedule a Kubernetes GPU Workload
* [AI-SC9]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#managed-kubernetes" %}}): Validate NVIDIA GPU Operator Integration
