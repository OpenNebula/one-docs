---
title: "Deploying a GPU-enabled Virtual Machine"
linkTitle: "GPU Virtual Machines"
description: ""
weight: 4
---

Having explored OpenNebula's multi-tenancy model in the [previous guide]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions" %}}), you can now move on to exploring OpenNebula's AI capabilities by deploying a GPU-enabled Virtual Machine. 

This guide uses the OpenNebula [vLLM Appliance](https://github.com/OpenNebula/one-apps/wiki/vllm_intro), which enables the deployment of a low-latency, high-throughput LLM inferencing engine capable of hosting many different LLM models. 

{{< alert title="Sign In as poc-tenant" type="primary" >}}To start this guide sign into Sunstone as the **poc-tenant** user with the credentials given to you by your OpenNebula PoC contact.{{< /alert >}} 

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

Click **Next** in the wizard to progress to the **Advanced options** step. Select the **PCI Devices** tab and select **+ Attach PCI Device**, choose the GPU device available in your PoC environment from the drop-down menu:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_attach_pci.png"
  path="/images/poc/ai_poc/light/poc_attach_pci.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Press **Continue** in the **Attach PCI device** dialog then press **Next** and then **Finish** to complete the update template wizard. 

## Step 3: Instantiate the vLLM Template

In **Templates -> VM Templates** select the **service_Vllm** template and press the play icon to instantiate it. Give the VM instance a name and press **Next** to the **User inputs** step. 

In this example, we want to use a non-default LLM model for inference. In the **MODEL** section of the **User inputs** page replace the default **Qwen/Qwen2.5-1.5B-Instruct** model with **HuggingFaceTB/SmolLM2-1.7B-Instruct**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_llm_model.png"
  path="/images/poc/ai_poc/light/poc_llm_model.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

Press **Next** to progress to the **Advanced options** step, in the **Network** tab, select **Attach NIC**. Press **Next** in the first step of the **Attach NIC** wizard, then select the **public** network so that the vLLM VM has a publicly available IP.

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_attach_nic.png"
  path="/images/poc/ai_poc/light/poc_attach_nic.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

In the **Network values** and **Select QoS** steps, do not alter the default settings, press **Next** and then **Finish** to complete the network settings. Then press **Finish** to deploy the VM. You will see the **Instances -> VMs** view, where you will see your VM boot.

## Step 4: Query the vLLM API and Try the Chat

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

## Step 5: Try Cycling the vLLM Appliance

Go back to **Instances -> VMs** and find the vLLM Appliance instance in the list. Click on the list item to open its information panel. Open the **VM state** drop-down menu and select **Reboot**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vllm_reboot.png"
  path="/images/poc/ai_poc/light/poc_vllm_reboot.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

The status will remain RUNNING, however, the VM itself is rebooting the OS. Try querying the API as you did in step 4 shortly after ordering the reboot (within 1-2 minutes). You will find that for a few minutes after rebooting, the API and web chat will not work as expected. After a few minutes, it should return to normal behavior, confirming that the vLLM appliance has successfully rebooted, re-attached to the GPU and the vLLM framework has loaded the model again.

You can also try a similar experiment by cycling the VM with the **Poweroff** operation followed by **Resume**.

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