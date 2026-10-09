---
title: "NVIDIA Run:ai Platform"
linkTitle: "Run:ai"
date: "2026-10-01"
description: "NVIDIA Run:ai control-plane application distributed with OneKS."
categories:
tags:
weight: "4"
type: docs
---

## Description and Purpose

The [**NVIDIA Run:ai Platform**](https://docs.nvidia.com/run-ai/self-hosted/index.html) installs the Run:ai control plane with managed ingress, GPU, monitoring, storage, certificate, and CA-distribution components. Use it to provide centralized Run:ai scheduling and administration services for AI workloads.

| **Attribute** | **Value** |
|-----------|-------|
| Application ID | `905abc6e-7cea-4a0a-bc84-ad215a3fc1fe` |
| Helm repository | `https://helm.ngc.nvidia.com/nvidia/runai` |
| Helm chart | `control-plane` |
| Version | `v2.25` |

As internal dependencies, OneKS also installs and fully manages the following components. They are not exposed as standalone applications, but appear inside the Kubernetes cluster among the resources created by this application:

- **Longhorn**: Persistent storage.
- **trust-manager**: Certificate trust distribution.
- **NVIDIA GPU Operator**: GPU management.
- **Prometheus**: Monitoring and metrics.
- **HAProxy Kubernetes Ingress Controller**: Ingress and service access.

## Parameters

All application-specific parameters are mandatory:

| **Parameter** | **Type** | **Sensitive** | **Description** |
|-----------|------|-----------|-------------|
| `domain` | String | No | Fully qualified domain name used to access the Run:ai control plane. |
| `adminUsername` | String | No | Username for the initial Run:ai administrator account. |
| `registryEmail` | String | No | Email address stored in the NVIDIA registry pull secret. |
| `adminPassword` | String | Yes | Password for the initial Run:ai administrator account. |
| `ngcApiKey` | String | Yes | NVIDIA NGC API key used to pull Run:ai images and charts. |

Sensitive values are used to create Kubernetes Secrets and are not displayed as plain text in normal application output.

## Installation

To install this application, follow the [Managing Applications guide]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) using the catalog ID shown above and provide the application-specific parameters described in the previous section.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the installation wizard, set the release name and target namespace. The following example uses `runai-backend` for both values and enables namespace creation:

{{< image
  path="/images/oneks/light/runai_configuration.png"
  pathDark="/images/oneks/dark/runai_configuration.png"
  alt="NVIDIA Run:ai release configuration" align="center" width="90%" mb="20px"
>}}

Enter the domain, administrator credentials, and NVIDIA registry credentials in the **User Inputs** step:

{{< image
  path="/images/oneks/light/runai_parameters.png"
  pathDark="/images/oneks/dark/runai_parameters.png"
  alt="NVIDIA Run:ai application parameters" align="center" width="90%" mb="20px"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
Create an `install.json` file with the release configuration and application parameters:

```json
{
  "release_name": "runai-backend",
  "target_namespace": "runai-backend",
  "create_namespace": true,
  "user_input_values": {
    "domain": "runai.example.com",
    "adminUsername": "<admin_username>",
    "registryEmail": "<registry_email>",
    "adminPassword": "<admin_password>",
    "ngcApiKey": "<ngc_api_key>"
  }
}
```

The file contains sensitive values. Store it with restricted permissions and remove it when it is no longer required.

Install the application with its catalog ID and the JSON file:

```shell
oneks install app 905abc6e-7cea-4a0a-bc84-ad215a3fc1fe \
  --cluster-id <CLUSTER_ID> \
  --file install.json
```

Inspect the installed release until its state changes to `ready`:

```shell
oneks show cluster <CLUSTER_ID> --app runai-backend
```
{{% /tab %}}

{{% tab header="API"%}}
Install the application through the OneKS API, providing the release configuration and application parameters in the request body:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  -X POST http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "905abc6e-7cea-4a0a-bc84-ad215a3fc1fe",
    "release_name": "runai-backend",
    "target_namespace": "runai-backend",
    "create_namespace": true,
    "user_input_values": {
      "domain": "runai.example.com",
      "adminUsername": "<admin_username>",
      "registryEmail": "<registry_email>",
      "adminPassword": "<admin_password>",
      "ngcApiKey": "<ngc_api_key>"
    }
  }'
```

The request returns `202 Accepted`. Inspect the installed release until its state changes to `ready`:

```shell
curl -u "$(cat /var/lib/one/.one/one_auth)" \
  http://<oneks-server>:10780/api/v1/clusters/<CLUSTER_ID>/applications/runai-backend
```
{{% /tab %}}

{{< /tabpane >}}

## Usage and Configuration

From the OpenNebula Front-end, retrieve the kubeconfig for the target K8s Cluster:

```shell
oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
```

### Connect to the Run:ai User Interface

After the application reaches `ready`, open the release to review its dependencies and connection instructions:

{{< image
  path="/images/oneks/light/runai_installed.png"
  pathDark="/images/oneks/dark/runai_installed.png"
  alt="NVIDIA Run:ai installed application" align="center" width="90%" mb="20px"
>}}

Retrieve the ingress address. The following example assumes that the application was installed with `runai-backend` as both the release name and target namespace:

```shell
KUBECONFIG=./kubeconfig kubectl get ingress -n runai-backend runai-backend-ingress \
  -o json | jq -r '.status.loadBalancer.ingress[0].ip'
```

Map that address to the configured domain on the workstation from which you will access the user interface:

```shell
echo '<ingress_ip> <domain>' | sudo tee -a /etc/hosts
```

Open `https://<domain>` and sign in with `adminUsername` and `adminPassword`. The first login starts the Run:ai configuration wizard:

{{< image
  path="/images/oneks/light/runai_frontend.png"
  alt="NVIDIA Run:ai initial configuration wizard" align="center" width="90%" mb="20px"
>}}

Complete the wizard and connect the K8s Cluster. The Run:ai dashboard displays the GPU nodes and devices detected in the cluster:

{{< image
  path="/images/oneks/light/runai_cluster.png"
  alt="NVIDIA Run:ai cluster dashboard" align="center" width="90%" mb="20px"
>}}

## Verify the Installation

Verify that all Run:ai control-plane workloads are running in the target namespace:

```shell
$ KUBECONFIG=./kubeconfig kubectl get pods -n runai-backend
NAME                                                   READY   STATUS    RESTARTS   AGE
keycloak-0                                             1/1     Running   0          9m9s
runai-backend-assets-service-5b7647d78c-t9cg7          1/1     Running   0          9m9s
runai-backend-audit-service-789d7cb4-mgsdw             1/1     Running   0          3m41s
runai-backend-authorization-77867d556d-b7h8h           1/1     Running   0          3m41s
runai-backend-bff-service-5d6cb8c6f8-87vrn             1/1     Running   0          3m41s
runai-backend-catalog-service-859cb74c4c-mgpj7         1/1     Running   0          3m40s
runai-backend-cli-exposer-74f7758768-t7ch4             1/1     Running   0          9m7s
runai-backend-cluster-service-bcb477bf4-tqrlv          1/1     Running   0          9m8s
runai-backend-datavolumes-658657ddcb-fb45l             1/1     Running   0          9m9s
runai-backend-diagnostics-service-565f85749f-gqznn     1/1     Running   0          9m7s
runai-backend-frontend-7c75f8b788-dxqhd                1/1     Running   0          9m9s
runai-backend-identity-manager-f65b77f5b-dq4mz         1/1     Running   0          3m41s
runai-backend-k8s-objects-tracker-6468bcbbdc-khg4q     1/1     Running   0          3m40s
runai-backend-metrics-service-56c847c8d-qxhc6          1/1     Running   0          3m40s
runai-backend-nats-0                                   1/1     Running   0          9m9s
runai-backend-nats-1                                   1/1     Running   0          7m40s
runai-backend-nats-2                                   1/1     Running   0          7m10s
runai-backend-notifications-proxy-bfdf75897-4mnrj      1/1     Running   0          3m40s
runai-backend-notifications-service-8ffd44bcb-dtppl    1/1     Running   0          9m9s
runai-backend-org-unit-helper-5bc65f695b-jwqvp         1/1     Running   0          3m41s
runai-backend-org-unit-service-c5ff76f98-4mbh6         1/1     Running   0          9m7s
runai-backend-policy-service-665b57f8c4-ssnqz          1/1     Running   0          9m9s
runai-backend-postgresql-0                             1/1     Running   0          9m9s
runai-backend-redoc-86748ddf4d-bl4b6                   1/1     Running   0          9m9s
runai-backend-temp-backend-settings-6bc65ff7b9-fbbr7   1/1     Running   0          3m41s
runai-backend-tenants-manager-5789b475f8-r4h4l         1/1     Running   0          3m40s
runai-backend-thanos-query-5f499bb8b8-jjkvk            1/1     Running   0          9m8s
runai-backend-thanos-receive-0                         1/1     Running   0          2m18s
runai-backend-traefik-685849bc6c-n2gfq                 1/1     Running   0          3m42s
runai-backend-workloads-759c8cd797-bflbj               1/1     Running   0          9m9s
runai-backend-workloads-helper-7bd65d54b7-jt7c8        1/1     Running   0          3m42s
runai-backend-workloads-manager-86c7bc47bb-ght76       1/1     Running   0          3m41s
```
