---
title: Deployment of AI-ready Kubernetes
linkTitle: AI-ready Kubernetes
weight: 5
tags: ['AI', 'Kubernetes']
---

<a id="ai_ready_k8s"></a>

Tools like Kubernetes provide robust orchestration for deploying AI workloads at scale, capable of managing isolation between Cluster workloads and GPU resources for AI inference tasks. With the use of the NVIDIA GPU Operator, you  can perform the provision of the necessary NVIDIA drivers and libraries for making GPU resources available to containers.

Kubernetes embraces multi-tenancy, supporting different isolated namespaces where the access from different teams or users are managed with Role Based Access Control (RBAC) and network policies. As an administrator, you can also enforce limits on the GPU usage or other resources consumed per namespace, ensuring fair resource allocation.

Additionally, running Kubernetes Clusters on top of OpenNebula-provisioned Virtual Machines (VMs) provides several advantages, such as hardware-level isolation, physically secure multi-tenancy. This also provides an additional layer of resource isolation for performance-sensitive workloads, multi-cloud architectures, flexibility as well as lifecycle management, and resource efficiency. Using CAPONE, the OpenNebula Cluster API provisioner for Kubernetes, to run K8s Clusters over OpenNebula-provisioned infrastructure allows the provisioning of Kubernetes workload Clusters in a declarative manner.

In this guide you will learn how to combine all of these components for provisioning a secure, robust and scalable solution for our AI workloads on top of the NVIDIA Dynamo framework powered by the OpenNebula cloud platform.

{{< alert title="Important" type="info" >}}
In this guide, we assume that you are using a single node OpenNebula deployment (i.e. a single node that works as both the OpenNebula Front-end and hypervisor Host at the same time).
{{< /alert >}}

## Before Starting

Before starting this tutorial, you must complete the AI-factory deployment with either on-premises resources or cloud resources. Please complete one of the following guides relevant to your available resources:

* [AI Factory Deployment with On-premises hardware]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}})
* [AI Factory Deployment on Scaleway Cloud]({{% relref "solutions/ai_factory_blueprints/deployment/cd_cloud"%}})

## Architecture

The diagram below depicts the top-level architecture of the NVIDIA Dynamo framework setup in an OpenNebula deployment. The OpenNebula Front-end Host contains two NVIDIA L40S GPU PCI cards which operate as the Host server for the K8s Cluster VMs. For this reference setup, the VMs share a simple bridged network.

{{< image path="/images/solutions/deployment_blueprints/ai-ready_opennebula/k8s_architecture_opennebula.svg" alt="Architecture of NVIDIA Dynamo in OpenNebula over two servers" align="center" width="90%" mb="20px" border="false" >}}

To deploy the GPU-enabled Kubernetes workload Cluster, first deploy a VM with the OpenNebula “CAPI Service” marketplace appliance which contains a light Kubernetes management Cluster which includes a Rancher/CAPONE controller deployment. This instance is used to provision the GPU-enabled Kubernetes workload Cluster nodes in a declarative way.

The GPU-enabled Kubernetes workload Cluster consists of three VMs that operate as a control plane node and two worker nodes. Each worker node uses one of the two NVIDIA L40S GPU PCI cards. Deploy the NVIDIA GPU Operator in this Cluster for automatic configuration of the nodes that make the GPU available to its workloads, and the NVIDIA Dynamo framework operator to deploy inference graphs in a declarative manner.

## Infrastructure Deployment and Configuration

Here is a brief glossary of the components described in this section:

- **Management Cluster**: A lightweight Kubernetes Cluster that contains Cluster API provider components for creating workload Kubernetes declaratively, based on CRDs and yaml manifests/Helm charts.
- **Workload Cluster**: The Kubernetes Clusters created through the Cluster API that manage the actual workloads.
- **CAPI service Appliance**: An OpenNebula Cluster API VM appliance that contains a lightweight-Kubernetes-based (k3s) management Cluster prebuilt with the OpenNebula Cluster API Provider (CAPONE) and other Cluster API providers, as well as a Rancher instance. This appliance is ready for deploying and managing workload Clusters without any previous setup.
- **CAPONE**: The OpenNebula Cluster API Provider which is a Kubernetes  Cluster API infrastructure provider that contacts with the OpenNebula Front-end API for provisioning the necessary infrastructure for running workload Clusters over OpenNebula VMs.

### Infrastructure Provisioning

This setup requires OpenNebula running on a GPU-ready environment, such as an OpenNebula Host configured with PCI-Passthrough for exposing the GPU cards to the node workloads.

### Kubernetes GPU Workload Cluster Provisioning with CAPONE

#### Deploying the Management Cluster

First we need to deploy the Kubernetes management Cluster. This Cluster uses the CAPONE controller for automatically provisioning the required VMs for hosting the Kubernetes GPU workload Cluster.

Deploy your Kubernetes management Cluster through the CAPI Service in OpenNebula.

##### Step 1: Deploying the CAPI Appliance

1. Login as `oneadmin` user on the Front-end instance and download the CAPI Service from the marketplace:

    ```shell
    onemarketapp export "Service Capi" service_Capi -d <datastore_id>
    ```

    Where `datastore_id` is your image datastore identifier. In this example, use the default one, with ID:`1`.

    ```shell
    onemarketapp export "Service Capi" service_Capi -d 1
    ```

2. Update the `service_Capi` template by adding the necessary scheduling requirements for deploying in to the desired Host. In this case, we're enabling the `host-passthrough` feature and adding a NIC card attached to the default `admin_net` network, but you can change it to another network if necessary. The chosen network must be the same that we are going to use for the workload Cluster vRouter ingress traffic.

    ```shell
    onetemplate update service_Capi
    ---
    NIC=[ NETWORK="admin_net" ]
    CPU_MODEL=[MODEL="host-passthrough" ]
    ```

3. Instantiate the `service_Capi` appliance:

    ```shell
    onetemplate instantiate service_Capi --name capi
    ```

    The CLI will ask you to input some values. Just press "Enter" for each input in order to keep the default values.

The CAPI appliance takes some minutes to be in “Ready” status. Once the appliance is available, proceed to deploy the workload to the Kubernetes Cluster with the following steps.

##### Step 2: Deploy the Workload Cluster

1. Login as `root` user in the Front-end and install [`helm 3`](https://helm.sh/docs/intro/install/) and [`kubectl`](https://kubernetes.io/docs/tasks/tools/#kubectl) tools on the Front-end instance:

    Helm:
    ```shell
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    ```

    kubectl:
    ```shell
    curl -fsSL "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" | \
         install -o root -g root -m 0755 -D /dev/fd/0 /usr/local/bin/kubectl
    ```

2. Switch to the `oneadmin` user again in the Front-end and gather the following information from your setup and export the following environment variables:

    In this example, `ONE_FRONETEND_IP` is set as the IP of the machine running the OpenNebula Front-end in the example AI Factory inventory file given in the [on-premises deployment guide]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises#ai-factory-deployment" %}}). In some cases, the gateway of the Virtual Network may be more appropriate, uncomment the following line if this is the case.

    ```shell
    export ONE_VNET=admin_net
    export ONE_FRONTEND_IP=192.168.122.2
    #export ONE_FRONTEND_IP=$(onevnet show $ONE_VNET -j | jq .VNET.TEMPLATE.GATEWAY | tr -d '"')
    export CAPI_VM_IP=$(onevm show capi -j | jq '.VM.TEMPLATE.NIC[0].IP' | tr -d '"')
    export ONEADMIN_PASSWORD=$(cat /var/lib/one/.one/one_auth | awk -F: '{print $2}')
    ```
    The `ONE_VNET` variable contains the name of the vnet where the CAPI instance has been deployed and where the workload Cluster is going to be deployed (in our case, `admin_net`),
    `ONE_FRONTEND_IP` is the IP used for accessing the OpenNebula Front-end XMLRPC API (in our case we are using the `admin_vnet` Virtual Network gateway IP, that is bridged with the OpenNebula Front-end Host),
    
    The `CAPI_VM_IP` is the CAPI appliance IP address, and the `ONEADMIN_PASSWORD` variable is the defined password for the `oneadmin` user.

    Check that the environment variables have been properly set:
    ```shell
    echo $ONE_VNET
    echo $ONE_FRONTEND_IP
    echo $CAPI_VM_IP
    echo $ONEADMIN_PASSWORD
    ```

    You should see an output like this (note that the IP addresses and the password could change depending on the environment):

    ```
    admin_net
    192.168.100.1
    192.168.100.50
    p455w0rd
    ```

3. Retrieve the management Cluster kubeconfig connecting to the CAPI appliance through the Front-end oneadmin user SSH key:

    ```shell
    ssh root@$CAPI_VM_IP cat /etc/rancher/k3s/k3s.yaml | \
    sed "s|server: https://127.0.0.1:6443|server: https://$CAPI_VM_IP:6443|"> \
    kubeconfig_management.yaml
    ```

    Check that you can access the management Cluster with the following command:
    ```shell
    kubectl --kubeconfig ./kubeconfig_management.yaml get nodes
    ```
    You should see an output similar to this:
    ```
    NAME   STATUS   ROLES                  AGE     VERSION
    capi   Ready    control-plane,master   9m20s   v1.31.4+k3s1
    ```

4. Create a `values.yaml` file for parameterizing the workload Cluster helm chart. You will see that the `values.yaml` file contains some default value overrides, like the images and templates applied for the workload nodes:

    ```shell
    cat > values.yaml << EOF
    ONE_XMLRPC: "http://$ONE_FRONTEND_IP:2633/RPC2"
    ONE_AUTH: "oneadmin:$ONEADMIN_PASSWORD"

    ROUTER_TEMPLATE_NAME: "{{ .Release.Name }}-router"
    MASTER_TEMPLATE_NAME: "{{ .Release.Name }}-master"
    WORKER_TEMPLATE_NAME: "{{ .Release.Name }}-worker"

    CLUSTER_IMAGES:
    - imageName: "{{ .Release.Name }}-router"
      imageContent: |
        PATH = "https://d24fmfybwxpuhu.cloudfront.net/service_VRouter-7.0.0-0-20250528.qcow2"
        DEV_PREFIX = "vd"
    - imageName: "{{ .Release.Name }}-node"
      imageContent: |
        PATH = "https://d24fmfybwxpuhu.cloudfront.net/ubuntu2404-7.0.0-0-20250528.qcow2"
        DEV_PREFIX = "vd"

    CLUSTER_TEMPLATES:
    - templateName: "{{ .Release.Name }}-router"
      templateContent: |
        CONTEXT = [
            NETWORK = "YES",
            ONEAPP_VNF_DNS_ENABLED = "YES",
            ONEAPP_VNF_DNS_NAMESERVERS = "1.1.1.1,8.8.8.8",
            ONEAPP_VNF_DNS_USE_ROOTSERVERS = "NO",
            ONEAPP_VNF_NAT4_ENABLED = "YES",
            ONEAPP_VNF_NAT4_INTERFACES_OUT = "eth0",
            ONEAPP_VNF_ROUTER4_ENABLED = "YES",
            SSH_PUBLIC_KEY = "\$USER[SSH_PUBLIC_KEY]",
            TOKEN = "YES" ]
        CPU = "1"
        CPU_MODEL=[
            MODEL="host-passthrough" ]
        DISK = [
            IMAGE = "{{ .Release.Name }}-router" ]
        GRAPHICS = [
            LISTEN = "0.0.0.0",
            TYPE = "vnc" ]
        LXD_SECURITY_PRIVILEGED = "true"
        MEMORY = "4096"
        NIC_DEFAULT = [
            MODEL = "virtio" ]
        SCHED_REQUIREMENTS="HYPERVISOR=kvm"
        OS = [
            ARCH = "x86_64",
            FIRMWARE_SECURE = "YES" ]
        VCPU = "2"
        VROUTER = "YES"
    - templateName: "{{ .Release.Name }}-master"
      templateContent: |
        CONTEXT = [
            BACKEND = "YES",
            NETWORK = "YES",
            GROW_FS = "/",
            SET_HOSTNAME = "\$NAME",
            SSH_PUBLIC_KEY = "\$USER[SSH_PUBLIC_KEY]",
            TOKEN = "YES" ]
        CPU = "12"
        CPU_MODEL=[
            MODEL="host-passthrough" ]
        DISK = [
            IMAGE = "{{ .Release.Name }}-node",
            SIZE = "41920" ]
        FEATURES=[
            ACPI="yes",
            APIC="yes",
            PAE="yes" ]
        GRAPHICS = [
            LISTEN = "0.0.0.0",
            TYPE = "vnc" ]
        HYPERVISOR = "kvm"
        LXD_SECURITY_PRIVILEGED = "true"
        MEMORY = "32768"
        NIC=[
            NETWORK="$ONE_VNET" ]
        OS = [
            ARCH = "x86_64",
            FIRMWARE="UEFI",
            MACHINE="pc-q35-noble" ]
        SCHED_REQUIREMENTS = "HYPERVISOR=kvm"
        VCPU = "16"
    - templateName: "{{ .Release.Name }}-worker"
      templateContent: |
        CONTEXT = [
            BACKEND = "YES",
            NETWORK = "YES",
            GROW_FS = "/",
            SET_HOSTNAME = "\$NAME",
            SSH_PUBLIC_KEY = "\$USER[SSH_PUBLIC_KEY]",
            TOKEN = "YES" ]
        CPU = "12"
        CPU_MODEL=[
            MODEL="host-passthrough" ]
        DISK = [
            IMAGE = "{{ .Release.Name }}-node",
            SIZE = "204800" ]
        FEATURES=[
            ACPI="yes",
            APIC="yes",
            PAE="yes" ]
        GRAPHICS = [
            LISTEN = "0.0.0.0",
            TYPE = "vnc" ]
        HYPERVISOR = "kvm"
        LXD_SECURITY_PRIVILEGED = "true"
        MEMORY = "32768"
        NIC=[
            NETWORK="$ONE_VNET" ]
        OS=[
            ARCH="x86_64",
            FIRMWARE="UEFI",
            MACHINE="pc-q35-noble" ]
        PCI=[
            CLASS="0302",
            DEVICE="26b9",
            VENDOR="10de" ]
        SCHED_REQUIREMENTS="HYPERVISOR=kvm"
        VCPU = "16"

    CONTROL_PLANE_MACHINE_COUNT: 1
    WORKER_MACHINE_COUNT: 2
    PUBLIC_NETWORK_NAME: $ONE_VNET
    PRIVATE_NETWORK_NAME: $ONE_VNET
    EOF
    ```

    The number of GPU devices mounted in each worker node depends on the definition of the `PCI` attribute in the worker nodes template (note that the attributes of this map could change depending on the GPU model). In our case, we are deploying 2 worker nodes, with 1 GPU attached to each one. In case you only have available a single GPU card, change the number or `WORKER_MACHINE_COUNT` to 1. More information is available in the [NVIDIA GPU Passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) guide. In this example, we will attach a single NVIDIA GPU card to each worker nodes.

5. Once the `values.yaml` file is available, you can proceed to deploy the workload Cluster with Helm. First, add the helm chart repo for CAPONE and apply the helm chart referencing the values file:

    ```shell
    helm repo add capone https://opennebula.github.io/cluster-api-provider-opennebula/charts/ \
        && helm repo update
    ```

    Verify the available charts in that repo:
    ```shell
    helm search repo capone
    ```
    The result should output the `capone-kadm` and `capone-rke2` charts:
    ```
    NAME                    CHART VERSION   APP VERSION     DESCRIPTION
    capone/capone-kadm      0.1.7           v0.1.7          OpenNebula/Kubeadm CAPI Templates
    capone/capone-rke2      0.1.7           v0.1.7          OpenNebula/RKE2 CAPI Templates
    ```

6. Finally, proceed to install the workload Cluster template in the CAPI appliance from the capone-rke2 chart:
    ```shell
    helm install --kubeconfig ./kubeconfig_management.yaml \
        k8s-gpu-test capone/capone-rke2 --values ./values.yaml
    ```

The CAPONE and rke2 Cluster API controllers in the management Cluster will deploy the workload Cluster on the scheduled Host. Check the logs of those controllers to review the progress:

```
kubectl get pods -A --kubeconfig kubeconfig_management.yaml -l control-plane=controller-manager
```

You should be able to see the following pods:

```
NAMESPACE                           NAME                                                             READY   STATUS    RESTARTS   AGE
capi-kubeadm-bootstrap-system       capi-kubeadm-bootstrap-controller-manager-548b88955-5qktn        1/1     Running   0          9m39s
capi-kubeadm-control-plane-system   capi-kubeadm-control-plane-controller-manager-79ddf6c498-lckn9   1/1     Running   0          9m37s
capi-system                         capi-controller-manager-698c5749d4-prxw5                         1/1     Running   0          9m46s
capone-system                       capone-controller-manager-5cfc7d5f85-8r7tw                       1/1     Running   0          9m36s
rancher-turtles-system              caapf-controller-manager-6b9b6ccdc-27vz7                         2/2     Running   0          9m35s
rancher-turtles-system              rancher-turtles-controller-manager-546957d6dc-d4t2z              1/1     Running   0          10m
rke2-bootstrap-system               rke2-bootstrap-controller-manager-8567757df9-cnzvr               1/1     Running   0          9m31s
rke2-control-plane-system           rke2-control-plane-controller-manager-6cdf48586d-dzqfm           1/1     Running   0          9m29s
```

Check the Virtual Machines in order to see if the Cluster has been finally deployed:

```shell
onevm list
```
When the deployment finishes you will see the following list of VMs: 1 vRouter instance with control plane Kubernetes API as backend (with the `vr-` suffix), 1 control plane node, and 2 worker nodes (with the `md-0` affix in the name).
```
ID USER     GROUP    NAME                                  STAT  CPU     MEM HOST
448 oneadmin oneadmin k8s-gpu-test-md-0-m5tzv-drg4k         runn   16     32G vgpu2
447 oneadmin oneadmin k8s-gpu-test-md-0-m5tzv-btvn4         runn   16     32G vgpu2
446 oneadmin oneadmin k8s-gpu-test-qb8dl                    runn   16     32G vgpu2
445 oneadmin oneadmin vr-k8s-gpu-test-cp-0                  runn    2    512M vgpu2
```

#### Connecting to the Workload Cluster Kubernetes API Locally

To establish a local connection to the Workload Cluster Kubernetes API, you will need to export the following environment variables. The `$VROUTER_IP` will contain the public IP address of the vRouter instance, and the `$CONTROL_PLANE_IP` will contain the IP address of the workload Cluster control plane instance. Here, we will connect directly to the Kubernetes Cluster from the OpenNebula Front-end, to make things simpler.
Note that the Virtual Machines change on each deploy, so change the name of the vRouter and control plane instance appropriately in the following code block:

```shell
export VROUTER_VM_NAME=<changeme>
export CONTROL_PLANE_VM_NAME=<changeme>
export VROUTER_IP=$(onevm show $VROUTER_VM_NAME -j | jq '.VM.TEMPLATE.NIC[0].VROUTER_IP' | tr -d '"')
export CONTROL_PLANE_IP=$(onevm show $CONTROL_PLANE_VM_NAME -j | jq '.VM.TEMPLATE.NIC[0].IP' | tr -d '"')
```
for instance, corresponding to our previous example:
```shell
export VROUTER_VM_NAME=vr-k8s-gpu-test-cp-0
export CONTROL_PLANE_VM_NAME=k8s-gpu-test-qb8dl
export VROUTER_IP=$(onevm show $VROUTER_VM_NAME -j | jq '.VM.TEMPLATE.NIC[0].VROUTER_IP' | tr -d '"')
export CONTROL_PLANE_IP=$(onevm show $CONTROL_PLANE_VM_NAME -j | jq '.VM.TEMPLATE.NIC[0].IP' | tr -d '"')
```
echo the declared variables for checking they have been properly filled:
```shell
echo $VROUTER_IP
echo $CONTROL_PLANE_IP
```
you should see an output like this (the IP addresses could change depending on the environment):
```
192.168.100.51
192.168.100.54
```

To access the Kubernetes API from your localhost, use the kubeconfig file that is located in the `/etc/rancher/rke2/rke2.yaml` file of the workload Cluster control plane node.

```shell
ssh -J root@$VROUTER_IP root@$CONTROL_PLANE_IP cat /etc/rancher/rke2/rke2.yaml | \
    sed "s|server: https://127.0.0.1:6443|server: https://$VROUTER_IP:6443|">  kubeconfig_workload.yaml
```

{{< alert title="Tip" type="info" >}}
If you encounter the following error when running this command:
```default
Connection closed by UNKNOWN port 65535
```
Follow the [procedure detailed in the Known Issues section](#known-errors).
{{< /alert >}}

Connect to the workload Cluster through kubectl, checking for instance the workload Cluster nodes:
```shell
kubectl --kubeconfig=kubeconfig_workload.yaml get nodes
```

This command should output the workload Cluster nodes:
```
NAME                            STATUS   ROLES                       AGE   VERSION
k8s-gpu-test-md-0-m5tzv-btvn4   Ready    <none>                      8d    v1.31.4+rke2r1
k8s-gpu-test-md-0-m5tzv-drg4k   Ready    <none>                      8d    v1.31.4+rke2r1
k8s-gpu-test-qb8dl              Ready    control-plane,etcd,master   8d    v1.31.4+rke2r1
```

If you want to avoid setting the `--kubeconfig` flag each time you use kubectl, export an env variable referencing the kubeconfig file. This will make kubectl refer to that kubeconfig by default on the shell that you are using:

```shell
export KUBECONFIG="$PWD/kubeconfig_workload.yaml"
```

### NVIDIA GPU Operator Installation

The NVIDIA GPU Operator executes the necessary steps for allowing NVIDIA GPU workloads in Kubernetes using the device plugin framework. The managed components includes:

* NVIDIA CUDA drivers
* Kubernetes device plugin for GPUs
* [NVIDIA Container runtime](https://developer.nvidia.com/container-runtime)
* [DCGM](https://developer.nvidia.com/dcgm) based monitoring
* Others

The procedure to install the NVIDIA GPU Operator is as follows:

1. Add the NVIDIA helm repo:

    ```shell
    helm repo add nvidia https://helm.ngc.nvidia.com/nvidia \
    && helm repo update
    ```

2. Export the `KUBECONFIG` variable.
    ```shell
    export KUBECONFIG="$PWD/kubeconfig_workload.yaml"
    ```

3. Deploy the gpu-operator on the workload Cluster:

    ```shell
    # create gpu-operator namespace
    kubectl create ns gpu-operator

    # enforce privileged pods on that namespace
    kubectl label --overwrite ns gpu-operator pod-security.kubernetes.io/enforce=privileged

    # install the helm chart
    helm install --wait --generate-name \
        -n gpu-operator --create-namespace \
        nvidia/gpu-operator \
        --version=v25.3.2 \
        --set "toolkit.env[0].name=CONTAINERD_CONFIG" \
        --set "toolkit.env[0].value=/var/lib/rancher/rke2/agent/etc/containerd/config.toml" \
        --set "toolkit.env[1].name=CONTAINERD_SOCKET" \
        --set "toolkit.env[1].value=/run/k3s/containerd/containerd.sock" \
        --set "toolkit.env[2].name=CONTAINERD_RUNTIME_CLASS" \
        --set "toolkit.env[2].value=nvidia" \
        --set "toolkit.env[3].name=CONTAINERD_SET_AS_DEFAULT" \
        --set-string "toolkit.env[3].value=true"
    ```

    Note that you have specified the `CONTAINERD_CONFIG` and `CONTAINERD_SOCKET` paths for the rke2 Kubernetes distribution, as it’s using a different one than the default.

    After a successful Helm installation, you will see this output:

    ```shell
    NAME: gpu-operator-1753949578
    LAST DEPLOYED: Thu Jul 31 10:13:01 2025
    NAMESPACE: gpu-operator
    STATUS: deployed
    REVISION: 1
    TEST SUITE: None
    ```

4. Check that the deployed pods for the gpu-operator are up and running:

    ```shell
    kubectl get pods -n gpu-operator
    ```

    Run this command over the next several minutes until all pods are in the `Running` or `Completed` status. Eventually, you should see the following pods running on the `gpu-operator` namespace (there may be less pods if you are running a single worker node or more if you are running more than two):

    ```
    NAME                                                              READY   STATUS      RESTARTS   AGE
    gpu-feature-discovery-f9fs6                                       1/1     Running     0          8d
    gpu-feature-discovery-q7h26                                       1/1     Running     0          8d
    gpu-operator-1753950388-node-feature-discovery-gc-854b7fb8jr989   1/1     Running     0          8d
    gpu-operator-1753950388-node-feature-discovery-master-955d78rh4   1/1     Running     0          8d
    gpu-operator-1753950388-node-feature-discovery-worker-4tvlv       1/1     Running     0          8d
    gpu-operator-1753950388-node-feature-discovery-worker-d7sxz       1/1     Running     0          8d
    gpu-operator-1753950388-node-feature-discovery-worker-zb5gj       1/1     Running     0          8d
    gpu-operator-84f4699cc4-kdcjn                                     1/1     Running     0          8d
    nvidia-container-toolkit-daemonset-d5fwk                          1/1     Running     0          8d
    nvidia-container-toolkit-daemonset-k54w7                          1/1     Running     0          8d
    nvidia-cuda-validator-gmnrq                                       0/1     Completed   0          8d
    nvidia-cuda-validator-vl94m                                       0/1     Completed   0          8d
    nvidia-dcgm-exporter-g5j2n                                        1/1     Running     0          8d
    nvidia-dcgm-exporter-g6x99                                        1/1     Running     0          8d
    nvidia-device-plugin-daemonset-rhj8z                              1/1     Running     0          8d
    nvidia-device-plugin-daemonset-v5bcq                              1/1     Running     0          8d
    nvidia-operator-validator-ctg6s                                   1/1     Running     0          8d
    nvidia-operator-validator-z52q7                                   1/1     Running     0          8d
    ```

    If you find tha the `nvidia-driver-daemonset-*****` pods are stuck in an Error/CrashLoopBackoff cycle, this may be caused by a problem with the availability of the drivers for the Linux kernel version of the worker VMs. Refer to the [Known Issues]({{% relref "/solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s/#nvidia-driver-daemonset-pods-stuck-in-crashloopbackoff" %}}) section for a solution.

5. Check if the Kubernetes nodes GPU autodiscovery operates as expected, by checking the workload nodes, for instance the `nvidia.com/*` labels and the allocatable gpu capacity:

    ```shell
    kubectl describe node <kubernetes_workload_node_name>
    ```

    for instance, in the example above:

    ```shell
    kubectl describe node k8s-gpu-test-md-0-m5tzv-drg4k
    ```

    Those are the labels you should see
    ```
    [...]
                        nvidia.com/gpu.memory=46068
                        nvidia.com/gpu.mode=compute
                        nvidia.com/gpu.present=true
                        nvidia.com/gpu.product=NVIDIA-L40S
                        nvidia.com/gpu.replicas=1

    [...]
    Capacity:
    cpu:                16
    ephemeral-storage:  202051056Ki
    hugepages-1Gi:      0
    hugepages-2Mi:      0
    memory:             32855784Ki
    nvidia.com/gpu:     1
    pods:               110
    Allocatable:
    cpu:                16
    ephemeral-storage:  196555267123
    hugepages-1Gi:      0
    hugepages-2Mi:      0
    memory:             32855784Ki
    nvidia.com/gpu:     1
    pods:               110
    ```

6. Finally, to use the PCI GPUs on the specific pod, add the `spec.runtimeClassName:nvidia` parameter in the pod/deploy manifest and set `nvidia.com/gpu: 1` as a requested resource. See the Verification section below for an example.

## Verification

To use the PCI GPU in a pod deployment add the `spec.runtimeClassName:nvidia` parameter in the pod/deploy manifest and set [`nvidia.com/gpu`](http://nvidia.com/gpu)`:1` as a requested resource.

For example, we can deploy a job targeting the NVIDIA GPU. Create a manifest with the following schema as `l40s-verify.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: l40s-verify-gpu
spec:
  template:
    spec:
      # Maps the pod to the NVIDIA Container Toolkit
      runtimeClassName: nvidia 
      
      containers:
      - name: cuda-test
        image: nvidia/cuda:12.4.1-base-ubuntu22.04
        command: ["nvidia-smi"]
        resources:
          limits:
            # Requests exactly 1 physical GPU
            nvidia.com/gpu: 1 
          requests:
            nvidia.com/gpu: 1
      
      # Ensures the pod doesn't loop if it fails
      restartPolicy: Never
  backoffLimit: 0
```

Then apply the job:

```bash
kubectl apply -f l40s-verify.yaml & kubectl get pods -l job-name=l40s-verify-gpu -w
```

Then check the logs:

```bash
kubectl logs -l job-name=l40s-verify-gpu
```

Then delete for cleanup:

```bash
kubectl delete -f l40s-verify.yaml
```

## Next Steps

Now that you have provisioned an AI-ready Kubernetes Cluster, you can move onto the following guides:

* [Deployment of NVIDIA Dynamo]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo" %}})
* [Deployment of the NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler" %}})

## Undeployment

Once you have completed the AI Factory guides that you are interested in, we recommend to undeploy the CAPI Cluster to free up compute resources (unless you intend to make further K8s deployments). The following instructions show how to cleanly shut down the CAPI Cluster:

Run the following command on your OpenNebula Front-end's command line:

```shell
kubectl --kubeconfig ./kubeconfig_management.yaml delete cluster k8s-gpu-test -n default
```

Watch the virtual router, the control plane and the worker VMs terminate with `onevm list`. Once the router, control plane and worker VMs are all successfully terminated, terminate the CAPI VM itself:

```shell
onevm terminate <CAPI_VM_ID>
```

## Known Issues

### NVIDIA Driver Daemonset Pods Stuck in CrashLoopBackoff

The `nvidia-driver-daemonset-*****` may get stuck in an Error/CrashLoopBackoff cycle. This may be a problem with the availability of the drivers for the Linux kernel version of the worker VMs. 

Using `onevm list` identify the worker VM ID(s), they are normally the VMs with the longest names. Use `onevm ssh <VM_ID>` to access the command line on each worker VM, then run the following commands:

```shell
apt update
apt full-upgrade -y
reboot
```

Choose `Keep the local version currently installed` in the prompt asking `What do you want to do about modified configuration file sshd_config?`. After running these commands on the worker nodes and rebooting, within a few minutes the situation should resolve and all pods should reach the `Running` status. 

### Connection closed by UNKNOWN port 65535

This error sometimes occurs when one or more VMs in the SSH command are not included in the `known_hosts` file. You can solve this by connecting to each individual VM through SSH and following the command line instructions.

For example, if you run the following command:

```shell
ssh -J root@$VROUTER_IP root@$CONTROL_PLANE_IP cat /etc/rancher/rke2/rke2.yaml
```

If you receive the error: `Connection closed by UNKNOWN port 65535`

Attempt the `ssh` command into each individual machine in the SSH jumphost command:

```shell
ssh root@$VROUTER_IP
```

And then:

```shell
ssh root@$CONTROL_PLANE_IP
```

You may receive a warning similar to the following in one or both cases:

```default
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ED25519 key sent by the remote host is
SHA256:mmp8kq8Cb1Xtb7zv/aFuD6dK5YXMhoQ6K4THNDTc00c.
Please contact your system administrator.
Add correct host key in /var/lib/one/.ssh/known_hosts to get rid of this message.
Offending ED25519 key in /var/lib/one/.ssh/known_hosts:4
  remove with:
  ssh-keygen -f "/var/lib/one/.ssh/known_hosts" -R "172.20.0.9"
Host key for 172.20.0.9 has changed and you have requested strict checking.
Host key verification failed.
```

Follow the instructions given by the command line warning with the respective IP:

```shell
ssh-keygen -f "/var/lib/one/.ssh/known_hosts" -R "172.20.0.9"
```

After completing this procedure, the SSH jumphost command should work correctly.

