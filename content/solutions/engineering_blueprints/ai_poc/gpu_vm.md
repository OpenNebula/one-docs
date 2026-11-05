---

title: "Deploying a GPU-enabled Virtual Machine"
linkTitle: "GPU-enabled VM"
description: ""
weight: 3

---

Having explored OpenNebula's multi-tenancy model in the [previous guide]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions" %}}), you can now move on to exploring OpenNebula's AI capabilities by deploying a GPU-enabled Virtual Machine. 

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

Congratulations! You have now learned how to deploy a GPU-enabled Virtual Machine on OpenNebula and deploy a GPU workload through the vLLM framework. Now you can move on to [Deploying a OneKS Kubernetes Cluster]({{% relref "solutions/engineering_blueprints/ai_poc/oneks/" %}}).