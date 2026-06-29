---
title: "Kubernetes Cluster Lifecycle Management"
linkTitle: "Kubernetes Cluster Lifecycle Management"
date: "2026-05-12"
description:
categories:
tags:
weight: "1"
type: docs
---

This section describes the main lifecycle operations for OneKS K8s Clusters. It covers how to create, access, scale, upgrade, recover, and delete K8s Clusters.

A OneKS K8s Cluster lifecycle normally follows this sequence:

* **Create a K8s Cluster**: Provision the control plane and required infrastructure.
* **Access the K8s Cluster**: Retrieve the kubeconfig and validate Kubernetes API access.
* **Add or Scale Worker Capacity**: Create or resize node groups.
* **Upgrade the K8s Cluster**: Move the K8s Cluster to a supported Kubernetes version.
* **Recover Failed Operations**: Retry selected failed lifecycle actions.
* **Delete the K8s Cluster**: Deprovision the K8s Cluster and associated resources.

OneKS exposes these operations through Sunstone, the CLI, and the REST API, depending on the deployment and user permissions.

## Creating a K8s Cluster

Creating a K8s Cluster provisions the Kubernetes control plane and the supporting OpenNebula infrastructure required by the selected K8s Cluster profile.

Before creating a K8s Cluster, verify that:

* **OneKS Service**: The OneKS service is configured and running.
* **OneGate Service**: OneGate is configured and reachable.
* **Transparent Proxy**: `tproxy` is configured for the required OneGate and OpenNebula XML-RPC ports.
* **OpenNebula Cluster**: The target OpenNebula Cluster ID is known.
* **Networks**: The OpenNebula public and private Virtual Network IDs are known.
* **Profiles**: The required family and flavour are available.
* **Kubernetes Version**: The target Kubernetes version is supported by the selected family.
* **Images and Templates**: Required VM images, VM templates, and runtime dependencies are available.
* **Permissions**: The user has permission to create and manage the required OneKS and OpenNebula resources.

{{< alert title="Note" type="primary" >}}
For more detailed information about the basic configuration and requirements needed to create K8s Clusters, refer to the [Basic Configuration Guide]({{% relref "platform_services/oneks/getting_started/basic_configuration" %}}).
{{< /alert >}}

Deployment options let you choose where each K8s Cluster is placed and which OpenNebula resources it uses. This makes it possible to provision independent K8s Clusters in different OpenNebula Clusters from the same OneKS service. For each deployment, you can select the target OpenNebula Cluster and the public and private Virtual Networks that will be used by the K8s Cluster. The selected networks must be available in the target OpenNebula Cluster. The OneKS appliance required by the selected control-plane family must also be available in an image datastore that can be used from that placement.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
From the left-hand navigation menu in Sunstone, go to **Kubernetes -> K8S Clusters** and click **Create** to start the K8s Cluster creation wizard.

{{< image path="/images/oneks/light/create_k8s_cluster_1.png"
          pathDark="/images/oneks/dark/create_k8s_cluster_1.png"
alt="OneKS create Cluster step 1" align="center" width="90%" mb="20px" >}}

The wizard guides you through the required configuration steps:

* **General**: K8s Cluster name and optional description.
* **Select a OpenNebula Cluster ID**: The OpenNebula Cluster used for K8s Cluster placement.
* **Select a Public Virtual Network**: Public network used for external connectivity and bootstrap paths.
* **Select a Private Virtual Network**: Private network used for internal K8s Cluster communication.
* **Kubernetes Version**: Kubernetes version to deploy.
* **Flavours**: Control-plane flavour to use.
* **User Inputs**: Remaining values required by the selected profile and flavour.

After completing the required fields, finish the wizard to start K8s Cluster creation. You will be redirected to the **Kubernetes Logs** view, where you can monitor the provisioning process.

{{< image path="/images/oneks/light/create_k8s_logs_running.png"
          pathDark="/images/oneks/dark/create_k8s_logs_running.png"
alt="OneKS K8s Cluster running logs" align="center" width="90%" mb="20px" >}}

For a complete Sunstone walkthrough, see the [OneKS Quick Start]({{% relref "platform_services/oneks/getting_started/quick_start/" %}}).
{{% /tab %}}

{{% tab header="CLI"%}}
Before creating a K8s Cluster with the CLI, identify the IDs of the OpenNebula public and private Virtual Networks:

```shell
$ onevnet list
ID USER     GROUP    NAME         CLUSTERS   BRIDGE   STATE
 1 oneadmin oneadmin private      0          br1      rdy
 0 oneadmin oneadmin public       0          br1      rdy
```

Also identify the OpenNebula Cluster where the K8s Cluster must be deployed:

```shell
$ onecluster list
ID NAME          HOSTS   VNETS  DATASTORES
 0 default           2       2           3
```

Launch the interactive K8s Cluster creation command. You can add `--wait` to subscribe to the deployment logs and keep the command attached until the operation completes or reaches a terminal state:

```shell
oneks create cluster --wait
```

The interactive CLI flow asks for:

* **K8s Cluster Name**: The name used to identify the OneKS K8s Cluster.
* **OpenNebula Cluster ID**: The OpenNebula Cluster used for K8s Cluster placement.
* **Public Network ID**: The OpenNebula public Virtual Network used by the K8s Cluster.
* **Private Network ID**: The OpenNebula private Virtual Network used by the K8s Cluster.
* **Kubernetes Version**: The Kubernetes version to deploy.
* **K8s Cluster Flavour**: The control-plane flavour, such as `standalone` or `ha`.

```shell
$ oneks create cluster
> Cluster name: example-oneks-cluster

DEPLOYMENT PLACEMENT
> OpenNebula cluster ID: 0
> Public network ID: 0
> Private network ID: 1

ONEKS SPEC
> Select a Kubernetes version for the Cluster:
    0: v1.33.7
    1: v1.34.2

    Select an option by number: 1

> Select a flavour for the Cluster:
    0: Single-Node Control Plane
       Single Control Plane node deployment.
       Suitable for development, evaluation, and non-critical workloads.
       1 node | 2 CPU | 2 vCPU | 4 GB RAM | 16 GB Storage

    1: Highly Available Control Plane
       Three-node Control Plane deployment with built-in redundancy.
       Suitable for production and other environments that require higher availability.
       3 nodes | 2 CPU | 2 vCPU | 4 GB RAM | 16 GB Storage

    Select an option by number: 1

ID: 10
```

You can also create a K8s Cluster from a JSON specification:

```shell
oneks create cluster --file spec.json --wait
```

Example `spec.json`:

```json
{
  "name": "prod-cluster",
  "description": "Production Kubernetes cluster",
  "kubernetes_version": "v1.34.2",
  "deployment": {
    "cluster": {
      "id": 0
    },
    "networks": {
      "public": {
        "id": 12
      },
      "private": {
        "id": 34
      }
    }
  },
  "spec": {
    "flavour": "ha"
  }
}
```

After the K8s Cluster is created, wait until its status changes from `PROVISIONING` to `RUNNING`.
{{% /tab %}}

{{% tab header="API"%}}
Use the following request to create a K8s Cluster:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://127.0.0.1:10780/api/v1/clusters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-cluster",
    "description": "Production Kubernetes cluster",
    "kubernetes_version": "v1.34.2",
    "deployment": {
      "cluster": {
        "id": 0
      },
      "networks": {
        "public": {
          "id": 0
        },
        "private": {
          "id": 1
        }
      }
    },
    "spec": {
      "flavour": "ha"
    }
  }'
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}

{{< /tabpane >}}

## Accessing a K8s Cluster

After the K8s Cluster reaches the `RUNNING` state, retrieve its kubeconfig. The kubeconfig contains the Kubernetes API endpoint and credentials required to access the K8s Cluster.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
From **Kubernetes -> K8S Clusters**, open the target K8s Cluster. In the K8s Cluster detail view, select the **Kubeconfig** tab.

{{< image path="/images/oneks/light/k8s_kubeconfig.png"
          pathDark="/images/oneks/dark/k8s_kubeconfig.png"
alt="OneKS K8s Cluster kubeconfig" align="center" width="90%" mb="20px" >}}

Copy the kubeconfig content and save it locally as a kubeconfig file.
{{% /tab %}}

{{% tab header="CLI"%}}
Retrieve the kubeconfig with the CLI:

```shell
oneks show cluster <cluster_id> --kubeconfig > kubeconfig
```

Use the kubeconfig with standard Kubernetes commands:

```shell
$ KUBECONFIG=./kubeconfig kubectl get nodes
NAME                         STATUS   ROLES           AGE   VERSION
test-cluster-control-plane   Ready    control-plane   3m    v1.31.4
```
{{% /tab %}}
{{% tab header="API"%}}
Retrieve the kubeconfig through the API and save it locally:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/kubeconfig \
  | jq -r '.kubeconfig' > kubeconfig
```

Use the saved kubeconfig with `kubectl`:

```shell
KUBECONFIG=./kubeconfig kubectl get nodes
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}

{{< /tabpane >}}

## Scaling Worker Capacity

Scaling worker capacity is done by creating or resizing node groups.

Node groups are the main operational unit for managing worker capacity in OneKS. Scaling should be performed against node groups, not directly against the K8s Cluster control plane.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
From **Kubernetes -> K8S Clusters**, open the target K8s Cluster. Select the **NodeGroup** tab, then click **Add Node Group**.

{{< image path="/images/oneks/light/k8s_add_node_group.png"
          pathDark="/images/oneks/dark/k8s_add_node_group.png"
alt="OneKS add node group" align="center" width="90%" mb="20px" >}}

The node-group creation wizard guides you through:

* **General**: Node group name and optional description.
* **Flavours**: Worker node flavour.
* **User Inputs**: Node count and remaining values required by the selected flavour.

{{< image path="/images/oneks/light/k8s_user_inputs.png"
          pathDark="/images/oneks/dark/k8s_user_inputs.png"
alt="OneKS node group user inputs" align="center" width="90%" mb="20px" >}}

After finishing the wizard, monitor the K8s Cluster logs until the node group reaches `RUNNING`.
{{% /tab %}}
{{% tab header="CLI"%}}
Create a node group:

```shell
oneks create nodegroup --cluster-id <cluster_id>
```

The command starts an interactive creation flow. You will be asked to provide:

* **Nodegroup Name**: The name used to identify the worker node group.
* **Flavour**: The worker node size profile to use.
* **Count**: The number of worker nodes to create.

```shell
$ oneks create group --cluster-id 10
> Nodegroup name: example-oneks-group
> Select a flavour for the Nodegroup:
    0: Small Worker Nodes
       Small worker node profile for lightweight workloads.
       2 CPU | 2 vCPU | 4 GB RAM | 16 GB Storage

    1: Medium Worker Nodes
       Medium worker node profile for balanced workloads.
       4 CPU | 4 vCPU | 8 GB RAM | 32 GB Storage

    2: Large Worker Nodes
       Large worker node profile for demanding workloads.
       8 CPU | 8 vCPU | 16 GB RAM | 64 GB Storage

    Select an option by number: 2
There are some parameters that require user input.
  * (count) Number of Worker nodes [type: number]
    Enter a number: 1

ID: 11
```

Scale a node group by specifying its ID and the desired number of worker nodes:

```shell
oneks scale nodegroup <nodegroup_id> --target <worker_count>
```

Example:

```shell
oneks scale nodegroup 11 --target 3
```

Validate the Kubernetes node list:

```shell
$ KUBECONFIG=./kubeconfig kubectl get nodes
NAME                         STATUS   ROLES           AGE   VERSION
test-cluster-control-plane   Ready    control-plane   9m    v1.34.2
test-cluster-worker-1        Ready    <none>          2m    v1.34.2
test-cluster-worker-2        Ready    <none>          2m    v1.34.2
test-cluster-worker-3        Ready    <none>          2m    v1.34.2
```

{{% /tab %}}

{{% tab header="API"%}}
Create a node group:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/nodegroups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "workers",
    "family": "general",
    "flavour": "small",
    "user_inputs_values": {
      "count": 2
    }
  }'
```

Scale an existing node group:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/nodegroups/<nodegroup_id>/scale \
  -H "Content-Type: application/json" \
  -d '{
    "target": 3
  }'
```

Validate the Kubernetes node list:

```shell
$ KUBECONFIG=./kubeconfig kubectl get nodes
NAME                         STATUS   ROLES           AGE   VERSION
test-cluster-control-plane   Ready    control-plane   9m    v1.34.2
test-cluster-worker-1        Ready    <none>          2m    v1.34.2
test-cluster-worker-2        Ready    <none>          2m    v1.34.2
test-cluster-worker-3        Ready    <none>          2m    v1.34.2
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}

{{< /tabpane >}}



## Upgrading a K8s Cluster

OneKS supports Kubernetes version upgrades for versions supported by the selected profile family.

Before upgrading, verify that:

* **Target Version**: The target Kubernetes version is supported by the selected family.
* **K8s Cluster State**: The K8s Cluster is in a suitable operational state.
* **Profiles**: The selected profiles support the target version.
* **Workloads**: Running workloads have been reviewed according to the user’s upgrade policy.
* **Backups**: Any required backups or recovery procedures have been completed.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the **K8S Clusters** view, select the K8s Cluster you want to upgrade. Open the **Info** tab and scroll to the **Kubernetes Version** field.

Use the dropdown menu to select the target Kubernetes version, then confirm the upgrade.

{{< image path="/images/oneks/light/k8s_upgrade_cluster_sunstone.png"
          pathDark="/images/oneks/dark/k8s_upgrade_cluster_sunstone.png"
alt="OneKS upgrade cluster Sunstone" align="center" width="90%" mb="20px" >}}

The selected version must be supported by the K8s Cluster profile. After starting the upgrade, monitor the K8s Cluster state and logs until the K8s Cluster returns to `RUNNING`.
{{% /tab %}}

{{% tab header="CLI"%}}
Upgrade a K8s Cluster:

```shell
oneks upgrade cluster <cluster_id> --k8s-version <version>
```

Example:

```shell
oneks upgrade cluster 42 --k8s-version v1.34.2
```

After the upgrade starts, inspect the K8s Cluster state:

```shell
oneks show cluster 42
```

Validate the Kubernetes nodes:

```shell
KUBECONFIG=./kubeconfig kubectl get nodes -o wide
```
{{% /tab %}}

{{% tab header="API"%}}
Upgrade a K8s Cluster:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/upgrade \
  -H "Content-Type: application/json" \
  -d '{
    "kubernetes_version": "v1.34.2"
  }'
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}
{{< /tabpane >}}

## Recovering a K8s Cluster or Node Group

OneKS includes recovery actions for selected failure and warning states. Recovery retries the failed lifecycle operation where possible. It may also retry failed dependency actions.

Recovery is not a general rollback mechanism. It should not be assumed to fix every infrastructure, dependency, or Kubernetes-level failure.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the **K8S Clusters** view, select the K8s Cluster that contains the affected node group. Open the **NodeGroup** tab and locate the node group you want to recover. Click the **Recover Node Group** action button on the node group row.

{{< image path="/images/oneks/light/k8s_recover_nodegroup_sunstone.png"
          pathDark="/images/oneks/dark/k8s_recover_nodegroup_sunstone.png"
alt="OneKS recover nodegroup Sunstone" align="center" width="90%" mb="20px" >}}

The recovery action retries the last failed lifecycle operation where possible. It is intended for node groups in a warning or failure state, such as `PROVISIONING_FAILURE`, `SCALING_FAILURE`, or `WARNING`.
{{% /tab %}}
{{% tab header="CLI"%}}
Recover a K8s Cluster:

```shell
oneks recover cluster <cluster_id>
```

Recover a node group:

```shell
oneks recover nodegroup <nodegroup_id>
```

Then verify the recovery result:

```shell
oneks show cluster <cluster_id>
oneks show nodegroup <nodegroup_id>
oneks logs cluster <cluster_id>
```
{{% /tab %}}

{{% tab header="API"%}}
Recover a K8s Cluster:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/recover
```

Recover a node group:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<cluster_id>/nodegroups/<nodegroup_id>/recover
```

Then verify the recovery result:

```shell
oneks logs cluster <cluster_id>
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}

{{< /tabpane >}}

## Deleting a K8s Cluster

Deleting a K8s Cluster deprovisions the OneKS K8s Cluster and its managed resources.

{{< alert title="Warning" type="warning" >}}
Use force option during deletion cautiously. It may skip parts of the normal deprovisioning workflow and can leave infrastructure that requires manual cleanup.
{{< /alert >}}

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the **K8S Clusters** view, select the K8s Cluster you want to delete. Click the red **Delete** button next to the **Create** button.

{{< image path="/images/oneks/light/delete_k8s_cluster.png"
          pathDark="/images/oneks/dark/delete_k8s_cluster.png"
alt="OneKS recover nodegroup Sunstone" align="center" width="90%" mb="20px" >}}

The deletion operation deprovisions the OneKS K8s Cluster and its managed resources, including the control plane and managed node groups. Referenced infrastructure, such as the public and private Virtual Networks selected during K8s Cluster creation, is not normally deleted by OneKS.
{{% /tab %}}

{{% tab header="CLI"%}}
Delete a K8s Cluster:

```shell
oneks delete cluster <cluster_id>
```

Force deletion, if required:

```shell
oneks delete cluster <cluster_id> --force
```

After deletion, verify that the K8s Cluster no longer appears in OneKS:

```shell
oneks list clusters
```
{{% /tab %}}

{{% tab header="API"%}}
Delete a K8s Cluster:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X DELETE "http://<oneks-server>:10780/api/v1/clusters/<cluster_id>"
```

Force deletion, if required:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X DELETE "http://<oneks-server>:10780/api/v1/clusters/<cluster_id>?force"
```

For further details about the API, see the [OneKS REST API Reference]({{% relref "platform_services/oneks/references/oneks_api/" %}}).
{{% /tab %}}
{{< /tabpane >}}
