---
title: "GPU as a Service"
linkTitle: "GPU as a Service"
description: ""
weight: 4
---

Use this guide to provide a GPU-enabled virtual machine with the vLLM appliance. The NCP operator prepares the service, the tenant administrator deploys and manages the VM, and the end user sends requests through the API or web chat.

| **Role** | **Interface** | **Work** |
| --- | --- | --- |
| NCP operator | Sunstone **Admin** view | Import the appliance, configure its GPU template, and grant tenant access. |
| Tenant administrator | Sunstone **VMs view** | Create and manage the GPU VM, select a model, and provide the service addresses. |
| End user | vLLM API or web chat | Send inference requests to the deployed model. |

## Before Starting

Connect to the PoC VPN as described in the [Connection Guide]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}}). The **ncp-operator** must complete [Multitenancy]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}}) for the VM service. This creates the group, administrator, network, VDC and quotas.

This guide uses `vm-tenant` and `vm-tenant-admin` as example names. Use the names configured for your tenant.

The assigned Host must have a GPU available for PCI passthrough. Have the compatible image/system datastores and tenant network ready. Use the GPU type and VM capacity supplied for your PoC.

## NCP Operator

Sign into Sunstone as **ncp-operator**. This account needs permission to import Marketplace appliances, edit VM templates, and create ACL rules.

### Import the vLLM Appliance

1. Open **Storage -> Apps**.
2. Enter `vllm` in the search bar.
3. Select the appliance that matches the assigned Host's hypervisor and CPU architecture, for example **KVM** and **x86_64**. Open its details.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/marketplace-search.png"
  alt="Search for vLLM in Sunstone Marketplace Apps and select the matching architecture" align="center" width="90%" mb="20px"
>}}

Click **Import** to open **Download App to OpenNebula**.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/marketplace-import-action.png"
  alt="Open the vLLM Marketplace appliance details and click Import" align="center" width="90%" mb="20px"
>}}

In the import wizard:

1. Set the image name and VM template name, for example `vllm`.
2. Enable **Export associated VM templates/images**.
3. Select the image datastore available to the tenant through its VDC.
4. Complete the import and wait for the image to become **READY**.
5. Open **Templates -> VM Templates** and find the imported template.
6. Record its ID and the image IDs referenced by its disks. You will use them when granting tenant access.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/appliance-import.png"
  alt="Import vLLM and its associated VM template" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/appliance-datastore.png"
  alt="Select the tenant-compatible image datastore for the appliance" align="center" width="90%" mb="20px"
>}}

### Configure the GPU VM Template

1. Open **Infrastructure -> Hosts**, select the assigned GPU Host and open **PCI**. Record the available GPU's vendor, device and class identifiers.
2. Return to **Templates -> VM Templates**, select `vllm` and open its update form.
3. Set the CPU, memory and disk capacity required by the model that the tenant will run.
4. Under **Advanced options -> PCI Devices**, click **Attach PCI device**.
5. Select the GPU's vendor, device and class identifiers. The scheduler can then select an available matching GPU on an assigned Host.
6. Under **Network**, attach a NIC and select the tenant virtual network.
7. Keep the appliance's contextualization inputs and save the template.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/template-gpu.png"
  alt="Select the GPU vendor, device and class for the VM template" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/template-network.png"
  alt="Select the tenant network for the template NIC" align="center" width="90%" mb="20px"
>}}

See [Generic PCI Devices]({{% relref "product/cluster_configuration/pci_passthrough_sriov/generic_devices/#selecting-a-pci-device-in-sunstone" %}}) for the template controls and [NVIDIA GPU Passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) for Host requirements. Host passthrough configuration must already be complete.

### Grant the Tenant Access

Grant access to the **tenant group**, so that its users can use the prepared template and its disk images.

1. Open **System -> ACLs** and click **Create ACL**.
2. Choose **From Form**.
3. Set **Apply this rule to** to **A group** and select `vm-tenant`.
4. Select **Virtual Machine Template** as the resource type.
5. Set **Scope** to **Identifier** and enter the imported template ID.
6. Select **USE** as the right and the zone that contains the template.
7. Review the rule and save it.
8. Create a rule for each required disk image. Use the same tenant group, resource type **Image**, that image's individual ID, right **USE**, and the same zone.

| **Subject** | **Resource** | **Right** |
| --- | --- | --- |
| Tenant group | Specific vLLM VM template (`TEMPLATE`) | `USE` |
| Tenant group | Each disk image used by the template (`IMAGE`) | `USE` |

Keep the operator as the owner of these resources. For tenant-exclusive access, check existing group/other permissions and ACLs. Remove unintended grants and preserve intentional sharing. Permissions and ACL rules grant access cumulatively.

Template access and image access are both required to create a VM. The tenant also needs VM creation permission and the infrastructure access assigned through its VDC.

See [Managing ACL Rules]({{% relref "product/cloud_system_administration/multitenancy/chmod/#manage-acl" %}}) for resource scope and rule syntax.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/acl-tenant-group.png"
  alt="Select the tenant group as the ACL subject" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/acl-template-summary.png"
  alt="Review the tenant group USE rule for the specific vLLM template" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/acl-image-summary.png"
  alt="Review the tenant group USE rule for the vLLM disk image" align="center" width="90%" mb="20px"
>}}

Give the tenant administrator the Sunstone address and account credentials.

## Tenant Administrator

Sign into Sunstone as **vm-tenant-admin**. The **VMs view** provides access to VM templates and VM management.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/tenant-view.png"
  alt="Tenant administrator signed into the VMs view" align="center" width="90%" mb="20px"
>}}

### Add Your SSH Public Key

Add your SSH public key to the tenant administrator's profile **before you instantiate the VM**. The appliance uses this key to give you SSH access for administration and troubleshooting.

1. Open the user menu at the bottom left and select **Profile Settings**.
2. Select **Security** and find the **SSH key** section.
3. Click the edit icon beside **SSH public key**.
4. Paste your public key from the laptop, for example the contents of `~/.ssh/id_ed25519.pub`.
5. Press **Enter** to save it and confirm that the public key is displayed.

Keep the matching private key on your laptop. Use it to connect to the VM over SSH after deployment.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/tenant-ssh-key.png"
  alt="Add the tenant administrator SSH public key under Profile Settings and Security before VM creation" align="center" width="90%" mb="20px"
>}}

### Create the GPU VM

1. Open **Templates -> VM Templates** and select the shared `vllm` template.
2. Click **Instantiate**.
3. Enter a VM name, for example `vllm_engine`.
4. Check the selected capacity against the model requirements and the tenant quota.
5. Continue to **User inputs**.
6. Set the API port, for example `8000`, and enable **Deploy a web application to interact with the model** if you need the browser chat.
7. Set the Hugging Face model ID. The example uses the appliance's default `Qwen/Qwen2.5-1.5B-Instruct`.
8. Supply a Hugging Face authentication token only if the selected model requires one.
9. Complete the wizard and wait for the VM to reach **RUNNING**.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/tenant-template.png"
  alt="Shared vLLM template available to the tenant administrator" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/vm-create.png"
  alt="Set the GPU VM name and capacity" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/model-inputs.png"
  alt="Set the vLLM model, API port and web application inputs" align="center" width="90%" mb="20px"
>}}

The model must fit the GPU memory, VM memory and disk capacity assigned to the service. Model download and initialization can continue after the VM reaches **RUNNING**.

### Check the VM and Provide the Service Addresses

1. Open **Instances -> VMs** and select the new VM.
2. Confirm that it is **RUNNING** and record its IP address.
3. Open **PCI** and confirm that the assigned GPU is attached.
4. Give the end user the API address, model ID and web chat address.

For the example ports, the addresses are:

* API base URL: `http://<VLLM_VM_IP>:8000/v1`.
* Web chat: `http://<VLLM_VM_IP>:5000`.

Use the ports configured for the appliance. Complete the end-user checks below before handing over a ready service.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/vm-running.png"
  alt="Running GPU VM owned by the tenant administrator" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/vm-pci.png"
  alt="Running tenant VM with its attached GPU in the PCI tab" align="center" width="90%" mb="20px"
>}}

### Manage the VM

To stop and start the VM, use **Poweroff** and **Resume** in the VM actions. The inference service is unavailable while the VM is off. After resuming, allow time for the model to initialize.

When the service is no longer required, select the VM's **Delete** action and choose **Terminate**. Wait for termination to complete. If your PoC has one GPU, terminate this VM before assigning that GPU to another VM or a Kubernetes worker.

## End User

Get the API base URL, model ID and web chat address from the tenant administrator. Connect to the PoC VPN. Use a browser for the chat and `curl` for API requests.

### Check the Available Model

Replace `<VLLM_VM_IP>` with the supplied VM address:

```bash
export VLLM_API_URL="http://<VLLM_VM_IP>:8000/v1"
curl -fsS "$VLLM_API_URL/models"
```

Wait until the service responds and the `data` list contains the model. A connection error can occur while the appliance is starting. Ask the tenant administrator to check the service if initialization does not complete.

A model entry contains its ID, for example:

```json
{
  "object": "list",
  "data": [
    {"id": "Qwen/Qwen2.5-1.5B-Instruct", "object": "model"}
  ]
}
```

### Send an Inference Request

Use the model ID returned by `/v1/models`. This example uses `Qwen/Qwen2.5-1.5B-Instruct`:

```bash
curl -fsS "$VLLM_API_URL/chat/completions" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "What is OpenNebula?"}],
    "max_tokens": 128
  }'
```

The response contains the model's answer under `choices[0].message.content`.

### Use the Web Chat

Open the supplied chat URL, for example `http://<VLLM_VM_IP>:5000`. Enter a prompt and wait for the answer.

{{< image
  path="/images/poc/ai_poc/gpu_as_a_service/end-user-chat.png"
  alt="An end user receives an answer from the vLLM web chat" align="center" width="90%" mb="20px"
>}}

## Next Steps

Continue to the [OneKS Guide]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}}) for GPU workloads on Kubernetes, or the [OneLLM Guide]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}) for model deployments with LiteLLM.

## PoC Success Criteria

* [AI-SC2]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#gpu-instances" %}}): Deploy a VM with GPU resources.
* [SC14]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#virtual-machine-administration" %}}): Use VM power actions.
