---

title: "Overview of the AI Factory Guided Evaluation"
linkTitle: "Overview"
description: ""
weight: 1
---

The AI Factory Guided Evaluation allows potential customers to test the AI-ready capabilities of the OpenNebula platform on hosted infrastructure provided by OpenNebula as part of the [Proof of Concept (PoC) Service]({{% relref "solutions/engineering_blueprints/ee_poc/poc_overview/" %}}). The PoC process provides a low-risk opportunity to assess OpenNebula's functionality, performance, and compatibility, ensuring it meets specific needs and requirements before committing to a full deployment.

The guides in this section take the user on a structured tour through OpenNebula's advanced AI capabilities. 

## How it Works

If you are interested in evaluating OpenNebula's AI capabilities through the PoC service, [contact the OpenNebula sales team](https://opennebula.io/contact/) to start the process. Once you have started the PoC process, the OpenNebula team will set up the hosted infrastructure with OpenNebula pre-installed and configured. Your PoC contact will send you instructions and credentials to connect to the hosted infrastructure and access the pre-deployed OpenNebula cloud.

Start with the connection and tenant setup guides. Then use the guide for the service that you want to provide:

* [Connecting to the PoC Infrastructure via VPN]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}})
* [Creating and Configuring Tenants]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}})
* [GPU as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}}): GPU-enabled virtual machines with vLLM.
* [Kubernetes as a Service with OneKS]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}}): create Kubernetes clusters and run GPU workloads.
* [Token Factory (OneLLM)]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}): LLM model deployments with LiteLLM.

## User Accounts and Views

The AI PoC demonstrates the functionality of OpenNebula's multitenancy user access model. The multitenancy model allows for users to be assigned different levels of privileges, maintains user resources isolated and enables the application of resource quotas to restrict user resource consumption. 

Start with the **ncp-operator** credentials supplied by your PoC contact. In the [Multitenancy Guide]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}}), create `vm-tenant` and its administrator for GPU as a Service. Assign the service view, network, VDC resources and quotas. The guide also gives the settings to create tenants for OneKS and OneLLM.

| **Username** | **Description** |
|----------|-------------|
| **ncp-operator** | Administrative user with high-level privileges. Has the capacity to create and modify users, modify templates, create or destroy resources and set resource quotas. |
| **vm-tenant-admin** | Tenant administrator for GPU virtual machines. Uses the VMs view and the prepared GPU VM template. |
| **k8s-tenant-admin** | Tenant administrator for Kubernetes clusters. Uses the OneKS view. |
| **llm-tenant-admin** | Tenant administrator for Kubernetes and OneLLM. Creates service and inference clusters, registers models and deploys inference services. These resources are separate from those of **vm-tenant-admin**. |

The AI Inference guide also uses separate LiteLLM administrator, LiteLLM consumer and Grafana administrator accounts. These accounts are managed by their respective applications.

The Sunstone web interface offers different [views]({{% relref "product/control_plane_configuration/graphical_user_interface/" %}}) that can be [customized with configuration]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone/#defining-a-new-view" %}}) to restrict visibility to the features each user has permissions to use. This helps reduce visual clutter and prevents users attempting prohibited actions. During these guides you will notice different views for each of the user accounts you control.  

{{< alert title="Tip" type="info" >}}
You need to switch between different OpenNebula user accounts in Sunstone during the course of these guides. To avoid repeatedly signing in and out it is recommended to use an incognito window or a different browser.
{{< /alert >}}

