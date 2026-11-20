---
title: "Deploying a GPU-enabled Virtual Machine"
linkTitle: "GPU Virtual Machines"
description: ""
weight: 4
---

Having explored OpenNebula's multitenancy model in the [previous guide]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions" %}}), you can now move on to exploring OpenNebula's AI capabilities by deploying a GPU-enabled Virtual Machine. 

This guide uses the OpenNebula [vLLM Appliance](https://github.com/OpenNebula/one-apps/wiki/vllm_intro), which enables the deployment of a low-latency, high-throughput LLM inferencing engine capable of hosting many different LLM models. 

## Before Starting

You will be using the following OpenNebula user account for this guide, ensure you have the credentials at hand:

* **vm-tenant-admin**

This user has been preconfigured with the necessary permissions to complete this guide. A VM template has also been prepared to launch a GPU-enabled VM capable of deploying an LLM model for inference. This user also sees the **VM Tenant** view, which allows access to the VM template and VM management functionality needed to launch and manage the GPU-enabled VM. 

Log in with your **vm-tenant-admin** account using the credentials you received before starting step 1. 

## Step 1: Find the vLLM Template

Go to **Template -> VM Templates** and find the **vllm** template:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_template.png"
  path="/images/poc/ai_poc/light/poc_vllm_template.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

## Step 2: Instantiate the vLLM Template

In **Templates -> VM Templates** select the **vllm** template and press the play icon to instantiate it:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_instantiate_vllm.png"
  path="/images/poc/ai_poc/light/poc_instantiate_vllm.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Give the VM instance a name, e.g. **vLLM** and press **Next** to the **User inputs** step. 

In this example, we want to use a non-default LLM model for inference. In the **MODEL** section of the **User inputs** page replace the default **Qwen/Qwen2.5-1.5B-Instruct** model with **HuggingFaceTB/SmolLM2-1.7B-Instruct**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_llm_model.png"
  path="/images/poc/ai_poc/light/poc_llm_model.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Press **Next** and then **Finish** to deploy the VM. You will see the **Instances -> VMs** view, where you will see your VM go through the various provisioning stages. Once it is RUNNING, click on the vLLM machine item in the list to open its details panel. Click on the PCI tab and you will see the attached GPU (in this case the hexadecimal PCI device codes):

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_pci_device.png"
  path="/images/poc/ai_poc/light/poc_pci_device.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

## Step 3: Query the vLLM API and Try the Chat

In **Instances -> VMs**, wait until the VM has reached the RUNNING state:

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

You may receive *Connection refused* warnings on the command line, this does not necessarily indicate a problem, it most likely means that the vLLM API is still initializing. If you continue to have connection problems after 10 mins, please message your OpenNebula PoC contact.

Eventually you will receive a response similar to the following:

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

If the response `data` attribute is an empty list, it most likely means that the model has not loaded. A large model may take time to download. Keep querying the API until you see a similar response.

Once you have confirmed that the model is loaded through the API, you can then access the web chat. Visit `http://<VLLM_VM_IP>:5000` in a separate browser tab and enter a prompt:

{{< image
  path="/images/poc/ai_poc/vllm_chat.png"
  alt="POC operator view" align="center" width="80%" mb="20px"
>}}

## Step 4: Try Cycling the vLLM Appliance

Go back to **Instances -> VMs** and find the vLLM Appliance instance in the list. Click on the list item to open its information panel. Open the **VM state** drop-down menu and select **Poweroff**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_reboot.png"
  path="/images/poc/ai_poc/light/poc_vllm_reboot.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Once the VM has reached the POWEROFF state, try querying the API or the web chat as you did in step 3, you will find that the API won't respond, since the vLLM appliance is now powered down.

Now from the **VM state** dropdown select **Resume**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_resume.png"
  path="/images/poc/ai_poc/light/poc_vllm_resume.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

The VM will power up and reboot, after a few minutes, you should be able to query the API and access the web chat again as you did in step 3.

## Next Steps

Congratulations! You have deployed a GPU-enabled Virtual Machine on OpenNebula and deployed an LLM GPU workload through the vLLM framework. 

Before moving onto the next guide, you should terminate the vLLM instance to ensure that the GPU is free for the Kubernetes Cluster you will deploy. In **Instances -> VMs**, select the vLLM VM instance and select the **Delete** option with the red dustbin icon:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_delete.png"
  path="/images/poc/ai_poc/light/poc_delete.png"
  alt="POC operator view" align="center" width="50%" mb="20px"
>}}

From the drop-down menu select **Terminate**, then confirm termination in the modal dialog. Wait until the VM is fully terminated before moving to the next step. Note that **Poweroff** and **Suspend** actions do not necessarily free up a VM's resources, it is necessary to use the termination action to ensure the resources are free.


You can now move on to [Deploying a OneKS Kubernetes Cluster]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}}).

## PoC Success Criteria

Completing this guide fulfills the following PoC success criteria:

* [AI-SC2]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#gpu-instances" %}}): Deploy a VM with GPU resources
* [SC14]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#virtual-machine-administration" %}}): Use of power options on a VM (Start / Stop / Reboot / etc.)