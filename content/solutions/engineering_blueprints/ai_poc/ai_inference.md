---
title: "Token Factory (OneLLM)"
linkTitle: "Token Factory (OneLLM)"
description: ""
weight: 6
aliases:
  - /solutions/engineering_blueprints/ai_poc/ai_inference/tenant_admin/
  - /solutions/engineering_blueprints/ai_poc/ai_inference/end_user/
---

Use **OneLLM** to deploy models on Kubernetes, **LiteLLM** to manage consumer access, and **Grafana** to inspect request performance. The NCP operator prepares the tenant resources, the tenant administrator provides the inference service, and the end user consumes assigned models.

| Role | Interface | Work |
| --- | --- | --- |
| NCP operator | Sunstone **Admin** view | Prepare the tenant, networks and resource access, and make the PoC platform available. |
| Tenant administrator | Sunstone **AI Operator view**, LiteLLM administrator UI and Grafana | Create both Kubernetes clusters, deploy models, assign consumer access, configure policies and inspect metrics. |
| End user | LiteLLM UI and API | Create personal virtual API keys, use the Playground or API, and review usage. |

This procedure uses two OneKS Kubernetes clusters:

| Cluster | Applications | Workers |
| --- | --- | --- |
| Service cluster | LiteLLM, PostgreSQL, Prometheus and Grafana | General-purpose CPU workers |
| Inference cluster | OneLLM Ready, KServe, vLLM and the inference gateway | OneLLM workers with a GPU |

Requests follow this path: **End user -> LiteLLM -> inference gateway -> model deployment**. The OneKS monitor publishes ready deployments to LiteLLM. Prometheus collects LiteLLM request metrics, and Grafana displays them.

Connect to the PoC VPN as described in the [Connection Guide]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}}). Use the section for your role.

## NCP Operator

Sign into Sunstone as **ncp-operator**. Prepare the shared infrastructure before the tenant administrator starts the service installation.

### Step 1: Prepare the Tenant

Follow [Multitenancy]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}}) for the **OneLLM** service profile:

1. Create the tenant group and its administrator, for example `llm-tenant` and `llm-tenant-admin`.
2. Assign **AI Operator view** to the group members and group administrator, with the resource-creation permissions required by OneLLM.
3. Complete the shared [OneKS and OneLLM network preparation]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/#kubernetes-services-oneks-and-onellm" %}}). Prepare the public IPv4 and ETHER ranges and the private network.
4. Assign the intended hosts, datastores and networks through the tenant VDC. Remove the tenant from the default VDC and grant access to the selected physical OpenNebula cluster as described in that guide.
5. Set quotas for both Kubernetes clusters, their control planes, workers and router VMs. Include the required GPU allocation.

The LiteLLM service address must be reachable from the inference cluster. LiteLLM must be able to reach the inference gateway. Browser-facing service addresses must be reachable through the PoC VPN.

{{< image
  path="/images/poc/ai_poc/token_factory/ai-operator-view-assignment.png"
  alt="Assign AI Operator view to both the tenant group and its administrator" align="center" width="90%" mb="20px"
>}}

### Step 2: Grant Access to the OneKS Appliance

Use the [OneKS appliance access procedure]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/#grant-the-tenant-appliance-access" %}}), with `llm-tenant` as the subject group:

* Grant **USE** on the specific OneKS appliance VM template, with resource scope **Identifier** and its template ID.
* Grant **USE** on the OneKS image.

## Tenant Administrator

Sign into Sunstone as **llm-tenant-admin**. The account opens with **AI Operator view**. Create the infrastructure in Sunstone, then manage consumers in the **LiteLLM administrator UI**.

The procedure uses a CPU Kubernetes cluster for services and a separate GPU Kubernetes cluster for inference.

### Before Starting

Install `kubectl` locally as described in the [OneKS guide]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/#before-starting" %}}). The shell examples use Bash.

### Step 1: Create the LiteLLM Service Cluster

Sign into Sunstone with the tenant administrator account.

Open **Kubernetes -> K8S Clusters** and click **Create Kubernetes Cluster**. Use the following settings:

| Setting | Value |
| --- | --- |
| Name | `litellm` |
| Public virtual network | `llm-public` |
| Private virtual network | `llm-private` |
| Kubernetes version | `v1.34.2` |
| Control-plane flavour | **Single-Node Control Plane** |
| Count | `1` |
| CPU / Virtual CPU | `2` / `2` |
| Memory | `16384` MiB (16 GiB) |
| Disk size | `16384` MiB (16 GiB) |

Complete the wizard and wait for **RUNNING**.

Open **Node Groups** and create the CPU worker:

| Setting | Value |
| --- | --- |
| Node group name | `cpu-pool` |
| Family | **General Purpose** |
| Flavour | **Medium Worker Nodes** |
| Count | `1` |
| CPU / Virtual CPU | `8` / `8` |
| Memory | `16384` MiB (16 GiB) |
| Disk size | `65536` MiB (64 GiB) |

Finish the node-group wizard and wait for **RUNNING**.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-cluster-name.png"
  alt="Name the LiteLLM Kubernetes cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-public-network.png"
  alt="Select llm-public for the service cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-private-network.png"
  alt="Select llm-private for the service cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-kubernetes-version.png"
  alt="Select Kubernetes v1.34.2 for the LiteLLM cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-control-plane-resources.png"
  alt="Set one control plane with CPU 2, Virtual CPU 2, memory 16384 MiB and disk 16384 MiB" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-worker-family.png"
  alt="Select the General Purpose worker family" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-worker-flavour.png"
  alt="Select Medium Worker Nodes for the LiteLLM CPU worker" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-worker-resources.png"
  alt="Set one CPU worker with CPU 8, Virtual CPU 8, memory 16384 MiB and disk 65536 MiB" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-worker-running.png"
  alt="LiteLLM cluster and cpu-pool worker Running" align="center" width="90%" mb="20px"
>}}

Open the cluster's **Kubeconfig** tab. Save its contents as `litellm-kubeconfig`, then run:

```bash
export LITELLM_KUBECONFIG="$PWD/litellm-kubeconfig"
chmod 600 "$LITELLM_KUBECONFIG"
kubectl --kubeconfig "$LITELLM_KUBECONFIG" get nodes
```

Confirm that the control-plane node and worker are **Ready**.

### Step 2: Install the LiteLLM Application

Open the cluster's **Applications** tab. Start the installation wizard and select **LiteLLM v1.108.4**.

| Setting | Value for this procedure |
| --- | --- |
| Release name | `litellm` |
| Target namespace | `litellm` |
| Create namespace | Enabled |
| Storage size (`storageSize`) | `10` with **GB** selected (`10Gi`) |

Complete the wizard and wait for the application and its dependencies to become **Ready**.

The current application uses a LoadBalancer Service on port `4000`.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-application-select.png"
  alt="Select the LiteLLM catalog application" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-application-namespace.png"
  alt="Set release and target namespace to litellm and enable namespace creation" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-storage-size.png"
  alt="Set the LiteLLM storage size to 10 with GB selected" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-application-ready.png"
  alt="LiteLLM application Ready in the service cluster" align="center" width="90%" mb="20px"
>}}

Find the LiteLLM address:

```bash
kubectl --kubeconfig "$LITELLM_KUBECONFIG" -n litellm get service litellm
```

Wait until **EXTERNAL-IP** contains an IP address or hostname. Record these URLs:

| URL | Purpose |
| --- | --- |
| `http://<LITELLM_ADDRESS>:4000` | Management and inference API base URL |
| `http://<LITELLM_ADDRESS>:4000/ui/` | Administrator and end-user UI |

Use the reachable service address in the following variable:

```bash
export LITELLM_BASE_URL='http://<LITELLM_ADDRESS>:4000'
```

#### Obtain the Administrator Credential

The native chart creates `litellm-masterkey`, with a `masterkey` entry. Read the value in a private terminal:

```bash
set +x
kubectl --kubeconfig "$LITELLM_KUBECONFIG" -n litellm \
  get secret litellm-masterkey \
  -o 'go-template={{index .data "masterkey" | base64decode}}{{"\n"}}'
```

Sign in as `admin` with the master key.

### Step 3: Create the OneLLM Inference Cluster

Create a second Kubernetes cluster with these settings:

| Setting | Value |
| --- | --- |
| Name | `inference` |
| Public / private networks | `llm-public` / `llm-private` |
| Kubernetes version | `v1.34.2` |
| Control-plane flavour | **Single-Node Control Plane** |
| Count | `1` |
| CPU / Virtual CPU | `2` / `2` |
| Memory | `16384` MiB (16 GiB) |
| Disk size | `16384` MiB (16 GiB) |

Wait for **RUNNING**, then create the GPU node group:

| Setting | Value |
| --- | --- |
| Node group name | `gpu-pool` |
| Family | **OneLLM Workers** |
| Flavour | **Extra Large OneLLM Worker Nodes** |
| Count | `1` |
| CPU / Virtual CPU | `32` / `32` |
| Memory | `65536` MiB (64 GiB) |
| Disk size | `262144` MiB (256 GiB) |

Wait for the node group and cluster to return to **RUNNING**. The selected worker profile includes the GPU passthrough.

Save the cluster kubeconfig as `onellm-kubeconfig`:

```bash
export ONELLM_KUBECONFIG="$PWD/onellm-kubeconfig"
chmod 600 "$ONELLM_KUBECONFIG"
kubectl --kubeconfig "$ONELLM_KUBECONFIG" get nodes
```

{{< image
  path="/images/poc/ai_poc/token_factory/inference-cluster-name.png"
  alt="Name the second Kubernetes cluster inference" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-kubernetes-version.png"
  alt="Select Kubernetes v1.34.2 for the inference cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-control-plane-resources.png"
  alt="Set the inference control plane to CPU 2, Virtual CPU 2, memory 16384 MiB and disk 16384 MiB" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-worker-family.png"
  alt="Select OneLLM Workers for the GPU node group" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-worker-flavour.png"
  alt="Select Extra Large OneLLM Worker Nodes" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-worker-resources.png"
  alt="Set one GPU worker with CPU 32, Virtual CPU 32, memory 65536 MiB and disk 262144 MiB" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/inference-worker-running.png"
  alt="Inference cluster and gpu-pool worker Running" align="center" width="90%" mb="20px"
>}}

### Step 4: Install OneLLM Ready and Connect LiteLLM

Open the inference cluster's **Applications** tab. Select **OneLLM Ready v0.1.0** and enter:

| Setting | Value for this procedure |
| --- | --- |
| Release name | `onellm` |
| Target namespace | `onellm-system` |
| Create namespace | Enabled |
| Local model cache size (`localModelCacheSize`) | `100` with **GB** selected (`100Gi`) |
| LiteLLM API URL (`litellmApiUrl`) | Reachable LiteLLM base URL from Step 2 |
| LiteLLM master key (`litellmMasterKey`) | Master key retrieved in Step 2 |

Use the LiteLLM API URL obtained in Step 2, without `/ui/` or `/v1`. For example, `http://10.16.6.117:4000`. Enter the master key retrieved in Step 2 in the masked field.

{{< image
  path="/images/poc/ai_poc/token_factory/onellm-application-select.png"
  alt="Select OneLLM Ready for the inference cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/onellm-application-namespace.png"
  alt="Set release onellm and target namespace onellm-system" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/onellm-application-inputs.png"
  alt="Set the model cache to 100 with GB selected, enter the LiteLLM URL and provide the masked master key" align="center" width="90%" mb="20px"
>}}

Complete the wizard and wait for **Ready**.

{{< image
  path="/images/poc/ai_poc/token_factory/onellm-application-ready.png"
  alt="OneLLM Ready application Ready in the inference cluster" align="center" width="90%" mb="20px"
>}}

### Step 5: Register and Deploy a Model

#### Register the Model Artifact

In Sunstone, open **OneLLM -> Models** and start the creation wizard.

| Field | Value |
| --- | --- |
| Name | `gemma4` |
| Publisher | `Google` |
| Description | `Quantized instruction model for the inference evaluation` |
| Source | `huggingface` |
| `reference` | `google/gemma-4-E2B-it-qat-w4a16-ct` |
| `revision` | `main` |
| `token` | Enter a token if repository access requires it; otherwise leave empty |

Complete the wizard and confirm that the model appears in the catalog. OneLLM resolves the repository revision. Registration describes the model artifact; it does not start a model server or allocate a GPU.

A private or gated model requires a Hugging Face token with the necessary repository access.

{{< image
  path="/images/poc/ai_poc/token_factory/model-register-general.png"
  alt="Register gemma4 with publisher Google and Hugging Face as source" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/model-register-reference.png"
  alt="Set the Gemma Hugging Face repository and main revision" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/model-catalog.png"
  alt="Gemma model artifact registered in the OneLLM catalog" align="center" width="90%" mb="20px"
>}}

#### Create the Deployment

Open **OneLLM -> Deployments** and start the creation wizard.

| Field | Value |
| --- | --- |
| Name | `gemma4` |
| Model | `gemma4` |
| Cluster | The `inference` Kubernetes cluster |
| Engine | `vllm` |
| Orchestrator | `kserve` |
| CPU | `4` |
| Memory | `8 GiB` |
| GPU | `1` |

Use one serving replica for this evaluation. Complete the wizard and follow the deployment logs and conditions. The first deployment downloads the model, pulls the runtime image and starts vLLM. Wait for **RUNNING**.

{{< image
  path="/images/poc/ai_poc/token_factory/deployment-general.png"
  alt="Create gemma4 on the inference cluster with vllm and kserve" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/deployment-resources.png"
  alt="Set model deployment CPU 4, memory 8 GB and GPU 1" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/deployment-progress.png"
  alt="Follow the model deployment logs" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/deployment-running.png"
  alt="The gemma4 model deployment Running" align="center" width="90%" mb="20px"
>}}

#### Confirm Publication in LiteLLM

Open **Models + Endpoints -> Deployed Models** in the LiteLLM administrator UI. Select **Team: Personal** and **View Current Team Models**. Wait for `gemma4` to appear.

The public model name is the name entered in Sunstone. The backend can retain a name such as `onellm-<ID>`. LiteLLM's provider value can therefore be `openai/onellm-<ID>` while consumers request `gemma4`.

The `openai/` prefix selects the provider adapter. Do not add that prefix to the consumer's public model name.

Do not manually add a second LiteLLM entry for the managed deployment. Publication creates and updates that entry; user permissions are configured separately.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-model-published.png"
  alt="The gemma4 model automatically published in LiteLLM" align="center" width="90%" mb="20px"
>}}

### Step 6: Invite a User and Assign Model Access

In the LiteLLM administrator UI, open **Internal Users** and click **Invite User**.

1. Enter the consumer's email address.
2. Select **Internal User (Create/Delete/View)** (`internal_user`) as the global proxy role. The view-only role does not permit key creation.
3. Leave **Team** unselected for this personal-key procedure.
4. Leave **Send invitation email** disabled.
5. Click **Invite User** and copy the invitation link.
6. Use the invitation link to let the end user create the account.

You can also assign models during invitation through **Personal Key Creation**.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-internal-users.png"
  alt="Open Internal Users in the LiteLLM administrator UI" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-invite-user.png"
  alt="Invite an internal user and leave email delivery disabled" align="center" width="90%" mb="20px"
>}}

After the user completes onboarding, open that user in **Internal Users** and select **Details -> Edit Settings**. Add `gemma4` under **Personal Models** and save the settings before the user creates a key or tests the model. Use specific models for restricted access. **All Proxy Models** grants broader access. Repeat this procedure when you need to change access later.

An existing virtual API key can have a narrower model list. After you grant another model to the user, check the key's **Models** list too.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-details.png"
  alt="Open the invited user details and Edit Settings" align="center" width="90%" mb="20px"
>}}

The OpenNebula tenant account and the LiteLLM consumer account are independent.

With the new account, the user follows the [End User section](#end-user) to create a personal virtual API key and test `gemma4`.

### Step 7: Configure Request and Token Limits

**RPM** means requests per minute. **TPM** means tokens per minute.

#### Set User Limits

1. Open **Internal Users** in the LiteLLM administrator UI and select the user.
2. Open **Details -> Edit Settings**.
3. For this example, set **RPM Limit** to `2` and **TPM Limit** to `10000`.
4. Leave a limit empty to keep it unlimited.
5. Save the settings.

These limits apply across the user's personal keys.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-model-limits.png"
  alt="Assign gemma4 as Personal Model and set TPM 10000 and RPM 2" align="center" width="90%" mb="20px"
>}}

#### Set Key Limits

1. Open **Virtual Keys** and create a key or select an existing key to edit.
2. Open its optional settings.
3. Enter the required key RPM and TPM limits.
4. Save the key.

Key limits apply alongside any user or team limits. See [LiteLLM rate-limit documentation](https://docs.litellm.ai/docs/proxy/users) for the available scopes.

### Step 8: Configure a Fallback

A fallback directs requests to another model when the primary backend fails.

#### Prepare the Fallback Model

Use another ready OneLLM deployment as the fallback. To create one, repeat Step 5 with the deployment name `gemma4-backup`. You can reuse the same model artifact. Wait for **RUNNING** and automatic publication in LiteLLM.

Both deployments must fit the available GPU and RAM capacity. If only one GPU is available, your PoC contact must first configure GPU sharing and suitable model memory budgets.

Add `gemma4-backup` to the user's **Personal Models** and the key's **Models** list.

#### Set the Global Fallback

Open **Settings -> Router Settings -> Fallbacks** in the LiteLLM administrator UI.

1. Click **Add Fallbacks**.
2. Select `gemma4` as **Primary Model**.
3. Add `gemma4-backup` to the **Fallback Chain**.
4. Click **Save All Configurations**.

> **Screenshot reference ADMIN-12:** the primary model, ordered fallback chain and saved global mapping.

#### Set a Key-Specific Fallback

1. Open **Virtual Keys** and create a key for the user.
2. Open **Optional Settings -> Router Settings -> Fallbacks**.
3. Select the primary model and its fallback chain.
4. Save the key.

Key router settings take precedence over team settings, which take precedence over global defaults. Team router settings provide another scope when you use teams.

See the [key and team router-settings guide](https://docs.litellm.ai/docs/proxy/keys_teams_router_settings) for additional options.

> **Screenshot reference ADMIN-13:** a key's Router Settings with its fallback chain.

### Step 9: Inspect Performance in Grafana

The LiteLLM application installs Prometheus and Grafana in the **service cluster**. Prometheus collects the authenticated LiteLLM metrics endpoint every 15 seconds. No separate dashboard installation is required for this procedure.

#### Find Grafana and Sign In

Find its service address:

```bash
kubectl --kubeconfig "$LITELLM_KUBECONFIG" -n monitoring \
  get service litellm-monitoring-grafana
```

Connect to the VPN and open `http://<GRAFANA_ADDRESS>` using the displayed external address.

Read the administrator password in a private terminal:

```bash
set +x
kubectl --kubeconfig "$LITELLM_KUBECONFIG" -n monitoring \
  get secret litellm-monitoring-grafana \
  -o 'go-template={{index .data "admin-password" | base64decode}}{{"\n"}}'
```

Sign in as `admin` and open **Dashboards -> LiteLLM Gateway**.

{{< image
  path="/images/poc/ai_poc/token_factory/grafana-dashboard-overview.png"
  alt="Grafana model and user filters with throughput and token-counter panels" align="center" width="90%" mb="20px"
>}}

#### Read the Dashboard

Select a time range that includes the requests, such as **Last 30 minutes**, then refresh.

Use the **model** filter for the requested public model name. Use the **user** filter for the LiteLLM user identity. Select **All** to compare models or users. An identity can appear as a user ID rather than the account email.

| Panel | Interpretation |
| --- | --- |
| Request throughput by model | Request rate observed by LiteLLM, in requests per second |
| Output token throughput | Aggregate output tokens per second for the selected traffic |
| Input and output token counters | Tokens observed since the exporter started; counters can reset after restart |
| Request latency p50 | Median request duration for the selected interval |
| Request latency p95 | Duration at the 95th percentile for the selected interval |
| Streaming TTFT p95 | Time to first token at the 95th percentile, from streaming samples |
| Failed requests per second | Request failures recorded by LiteLLM |
| Output tokens by user and model | Token totals grouped by the exported consumer and requested-model labels |

### Model Deployment Deletion

Delete model deployments from **OneLLM -> Deployments** in Sunstone. Their corresponding LiteLLM entries are removed automatically through background synchronization.

### Troubleshooting

| Symptom | What to check |
| --- | --- |
| A network, datastore or image is absent in Sunstone | Ask the platform operator to check tenant sharing and permissions. |
| A LoadBalancer address remains pending | Ask the platform operator to check cloud-controller configuration and the network's available address range. |
| LiteLLM waits for storage | Check general-worker readiness, available disk, generic Longhorn and PVC status. Do not add OneLLM storage labels to solve a service-cluster catalog mismatch. |
| OneLLM waits for GPU readiness | Check passthrough, the OneLLM worker profile and GPU Operator workloads. |
| Deployment remains pending or fails to load | Check GPU/RAM/disk capacity, model access, download logs and serving conditions. |
| Deployment runs but is absent in LiteLLM | Check the LiteLLM API URL and master key in the OneLLM Ready settings, and connectivity between the clusters. |
| LiteLLM cannot call the backend | Check that LiteLLM can reach the inference gateway address. |
| User cannot see or call the model | Check Personal Models and the key's Models list. Sunstone permissions do not configure these lists. |
| User cannot create a personal key | Check the internal_user role and personal-key permissions. Team keys require separate team permissions. |
| Fallback does not occur | Check the saved policy scope, key overrides, backup readiness/access and whether the primary failure actually occurred. |
| Grafana has no data | Check the time range and filters. TTFT needs streaming samples. If data remains absent, contact your PoC contact. |
| Invitation link is unreachable | Use the consumer-reachable UI origin while preserving the onboarding path and query parameters. |

## End User

Use this section when the administrator invites you to LiteLLM. Complete onboarding first. The administrator then assigns your model before you create a key or send requests. You do not need a Sunstone account, Kubernetes access or an administrator credential.

The examples request the public model `gemma4`. Use the public model name supplied by your administrator if it differs.

### Prepare Your LiteLLM Account

Obtain the following items from your administrator:

* A reachable LiteLLM UI URL and API base URL.
* An invitation link for your LiteLLM account.
* The names of the models that you can use.
* Permission to create personal virtual API keys.
* VPN access if the service uses the private PoC network.

A **virtual API key** is a secret token for API requests. It belongs to your LiteLLM account and has its own model restrictions.

### Step 1: Accept the Invitation

Open the invitation link and follow the onboarding form to set your password. Sign into LiteLLM with the invited email address and that password.

Use a separate browser profile if an administrator is already signed into the same service. Your OpenNebula password is not used for this LiteLLM account.

If the link is unreachable or expired, ask the administrator for a corrected invitation. Keep the invitation private.

After onboarding, ask the administrator to confirm that `gemma4` is assigned before you continue to Step 2.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-onboarding.png"
  alt="Complete the LiteLLM account onboarding form with a masked password" align="center" width="90%" mb="20px"
>}}

### Step 2: Check Your Models

Open **Models + Endpoints**. Select the **Personal** scope and confirm that `gemma4` is listed.

If a model is absent, ask the administrator to check your **Personal Models**. Creating a virtual API key does not grant access to an unassigned model.

### Step 3: Create a Personal Virtual API Key

Open **Virtual Keys** and click **Create New Key**.

1. Keep **Owned By** set to **You** and leave **Team** unselected.
2. Enter a key name, such as `api_key`.
3. Select **AI APIs** as the key type.
4. In **Models**, select `gemma4` or the assigned models needed by your application.
5. Create the key.
6. Copy the revealed value and store it privately.

The full secret is shown at creation time. The key list displays a masked value afterwards. Use a separate key for each application when you need independent revocation.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-keys.png"
  alt="Open Virtual Keys as the LiteLLM consumer" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-key-settings.png"
  alt="Create a personal key named api_key for gemma4" align="center" width="90%" mb="20px"
>}}

The key's model list can be narrower than your account's permissions. If the administrator later grants another model, check whether your existing key also allows it.

A personal key is not a team key. Team keys have separate team membership and key-creation requirements. Ask your administrator before changing scope.

### Step 4: Test the Key in Playground

Open **Playground** and use the chat interface.

1. Open **Configurations**.
2. Set **Virtual Key Source** to **Virtual Key**.
3. Paste your key into the masked **Enter custom Virtual Key** field.
4. Keep **Custom Proxy Base URL** on the LiteLLM installation supplied by your administrator.
5. Select `gemma4`.
6. Send: `Reply with just the number: what is 1 + 1?`

The answer should contain `2`; wording can vary. This request uses your virtual API key rather than relying only on the UI session.

To test with your signed-in account, select **Current UI Session**. To test a particular API key, select **Virtual Key** as described above.

{{< image
  path="/images/poc/ai_poc/token_factory/litellm-user-playground.png"
  alt="Successful gemma4 response using Current UI Session in the LiteLLM Playground" align="center" width="90%" mb="20px"
>}}

If the model list is empty, confirm that the key was entered and that both your account and key permit the model. Refresh after the administrator changes access.

The [LiteLLM Playground guide](https://docs.litellm.ai/docs/proxy/model_compare_ui) describes additional test options.

### Step 5: Use the Key from the Command Line

The LiteLLM API supports OpenAI-compatible chat requests. Use the supplied API base URL without `/ui/`. The example below requires Bash and curl with `--fail-with-body` support.

```bash
export LITELLM_BASE_URL='http://<LITELLM_ADDRESS>:4000'
set +x
read -r -s -p 'Your virtual API key: ' LITELLM_API_KEY
printf '\n'

curl --fail-with-body "$LITELLM_BASE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gemma4",
    "messages": [
      {"role": "user", "content": "Reply with just the number: what is 1 + 1?"}
    ],
    "max_tokens": 32,
    "temperature": 0
  }'

unset LITELLM_API_KEY
```

A successful response includes the assistant's text in `choices[0].message.content`. Do not put the key into a shared script, screenshot or support message.

Use the LiteLLM address, not the inference cluster's gateway address. Your virtual API key does not authenticate directly to that backend gateway.

### Step 6: Review Your Usage

Open **Usage** and select **Your Usage**. Choose a time range that includes your requests.

In **Overview**, select **Tokens** or **Requests** for the daily-usage chart. Use **Model Activity** to inspect a particular model. Records can take a short time to appear after completion.

> **Screenshot reference USER-05:** token/request usage charts for the consumer and a selected model.

This guide uses consumption counts rather than costs. For request-performance analysis across models, ask your administrator to use the Grafana dashboard. LiteLLM's usage view and the Grafana performance view serve different purposes.

### Troubleshooting

| Symptom | Action |
| --- | --- |
| Invitation does not open | Ask for a valid link with a reachable service origin. Connect to the VPN if required. |
| Personal key creation is unavailable | Ask the administrator to check your role and personal-key permissions. |
| Model is absent from Your Models | Ask the administrator to assign the model to your Personal Models. |
| Model is listed but absent in Playground | Enter the virtual key, check its allowed models and refresh. |
| HTTP `401` | Check that the key is correct, active and not expired or revoked. |
| HTTP `403` | Check the public model name and ask the administrator to verify account/key model permissions. |
| HTTP `429` | Wait for the rate-limit window and reduce traffic. Ask which user, key or team limit applies. Do not create keys to bypass a user-wide limit. |
| Backend or timeout error | Report the public model name, time and request identifier to the administrator, without the key. |
| Usage is not visible yet | Check the time range and Your Usage selection, then allow processing time and refresh. |

The administrator's [model access, limits and fallback procedures](#tenant-administrator) explain the service controls.
