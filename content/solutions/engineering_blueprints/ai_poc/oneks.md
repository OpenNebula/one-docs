---
title: "Deploying a GPU-enabled Kubernetes Cluster on OpenNebula"
linkTitle: "GPU OneKS"
description: ""
weight: 4
---

In this guide, you will deploy a OneKS Kubernetes Cluster and deploy a GPU workload on the K8s Cluster using kubectl.

Sign in using the **gpu-operator** account credentials you were provided by your OpenNebula PoC contact.

## Prerequisites: Install kubectl and Helm

If you haven't already installed kubectl during the OneKS setup, download the latest patch release for Kubernetes 1.35, matching the Cluster version used in Step 3:

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

{{< image path="/images/ai_factories/light/create_k8s_cluster.png" 
          pathDark="/images/ai_factories/dark/create_k8s_cluster.png"
alt="OneKS Create Cluster" align="center" width="90%" mb="20px" >}}

Then follow the steps of the Create Kubernetes Cluster wizard:

{{< image path="/images/ai_factories/light/name_cluster.png" 
          pathDark="/images/ai_factories/dark/name_cluster.png"
alt="OneKS name Cluster" align="center" width="90%" mb="20px" >}}

* **General**: Name the Cluster, e.g. `gpu-cluster`
* **Select Cluster**: Select the OpenNebula Cluster to Host your K8s Cluster (`0 default` if you have followed the standard installation)
* **Select a public virtual network**: Select the public Virtual Network you previously created (must have internet access)
* **Select a private virtual network**: Select the private Virtual Network you previously created
* **K8s version**: Select version 1.35.0
* **Flavours**: Select *Single-Node Control Plane*
* **User inputs**: Review, no changes required

## Step 2: Scale the K8s Cluster

Once the K8s Cluster has entered the RUNNING state, select the K8s Cluster in the list to open its details panel and select the **Node Groups** tab, click **+ Create Node Group**:

{{< image path="/images/ai_factories/light/create_node_group.png" 
          pathDark="/images/ai_factories/dark/create_node_group.png"
alt="OneKS scale Cluster" align="center" width="90%" mb="20px" >}}

* In the **General** step enter a name, e.g. `gpu-worker`
* In the **Flavours** step choose the **Large Worker Nodes** flavour 
* In the **User inputs** step set the **Count** as 1

Click **Finish** and you will see the progress in the **Logs** view.

### Ensure the GPU is Attached

Once the new node group enters the RUNNING state, select the K8s Cluster, in the **Node Groups** tab, select the new node group in the node group list and click on the node itself in the node list:

{{< image path="/images/ai_factories/light/inspect_node.png" 
          pathDark="/images/ai_factories/dark/inspect_node.png"
alt="OneKS inspect node" align="center" width="90%" mb="20px" >}}

This will open the node details view. In the **PCI** tab, you should see the GPU listed in the PCI devices:

{{< image path="/images/ai_factories/light/node_gpu.png" 
          pathDark="/images/ai_factories/dark/node_gpu.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

If you see your GPU in this list, your K8s worker node has successfully attached to the GPU.

## Step 3: Copy the kubeconfig

Close the details panel of the node group and go to the **Kubeconfig** tab. Copy and save the kubeconfig details into a file locally (on the Front-end command line) with a text editor. The kubeconfig contains the details and credentials of the K8s Cluster you have just created, it is necessary to interact with the Cluster through kubectl.

{{< image path="/images/ai_factories/light/kubeconfig.png" 
          pathDark="/images/ai_factories/dark/kubeconfig.png"
alt="OneKS inspect node GPU" align="center" width="90%" mb="20px" >}}

Export the KUBECONFIG environment variable in the terminal at the beginning of any kubectl session:

```shell
export KUBECONFIG="$PWD/kubeconfig"
```

Check that kubectl can access the Cluster:

```shell
kubectl get nodes
```

Wait until both the control-plane node and the worker node report `Ready` before continuing. A OneKS node group can be `RUNNING` while the worker is still initializing Kubernetes. If a node is missing or shows `NotReady`, wait and repeat the command.

The output should look similar to the following:

```default
NAME                                                 STATUS   ROLES                AGE   VERSION
controlplane-general-standalone-44c7fcc86fd3-kbkb4   Ready    control-plane,etcd   22m   v1.35.0+rke2r1
nodegroup-general-large-7fc21d43cda5-hv9j2-xs267     Ready    <none>               15m   v1.35.0+rke2r1
```

This confirms that the K8s Cluster is operating properly and kubectl can access it.

