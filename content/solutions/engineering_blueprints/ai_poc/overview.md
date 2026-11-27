---

title: "Overview of the AI Factory Guided Evaluation"
linkTitle: "Overview"
description: ""
weight: 1
---

Use the AI Factory Guided Evaluation to prepare tenants and provide three OpenNebula services: **GPU as a Service**, **Kubernetes as a Service** and **Token Factory**. The guides cover infrastructure preparation, service installation and end-user access on hosted [Proof of Concept (PoC) infrastructure]({{% relref "solutions/engineering_blueprints/ee_poc/poc_overview/" %}}).

## How it Works

If you are interested in evaluating OpenNebula's AI capabilities through the PoC service, [contact the OpenNebula sales team](https://opennebula.io/contact/) to start the process. Once you have started the PoC process, the OpenNebula team will set up the hosted infrastructure with OpenNebula pre-installed and configured. Your PoC contact will send you instructions and credentials to connect to the hosted infrastructure and access the pre-deployed OpenNebula cloud.

Start with the connection and tenant setup guides. Then use the guide for the service that you want to provide:

* [Connecting to the PoC Infrastructure via VPN]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}})
* [Creating and Configuring Tenants]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}})
* [GPU as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}}): GPU-enabled virtual machines with vLLM.
* [Kubernetes as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}}): use OneKS to create Kubernetes clusters and run GPU workloads.
* [Token Factory]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}): use OneLLM to deploy models, LiteLLM to manage consumer access, and Grafana to inspect request metrics.

## User Accounts and Views

Each OpenNebula tenant has a group, an administrator, a service view, allocated infrastructure and quotas. The NCP operator prepares these objects. The tenant administrator then installs and manages the selected service.

Start with the **ncp-operator** credentials supplied by your PoC contact. In the [Multitenancy Guide]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}}), create `vm-tenant` and its administrator for GPU as a Service. Assign the service view, network, VDC resources and quotas. The guide also gives the settings to create tenants for OneKS and OneLLM.

| **Username** | **Sunstone view** | **Work** |
| --- | --- | --- |
| **ncp-operator** | **Admin view** | Create tenants, assign infrastructure, set quotas, and grant access to service appliances. |
| **vm-tenant-admin** | **VMs view** | Provide GPU as a Service: create and manage GPU VMs from the shared vLLM template. |
| **k8s-tenant-admin** | **OneKS view** | Provide Kubernetes as a Service: create clusters and GPU workers, then give users Kubernetes access. |
| **llm-tenant-admin** | **AI Operator view** | Provide Token Factory: create service and inference clusters, register models, and deploy inference services with OneLLM. |

The Token Factory guide also uses LiteLLM administrator, LiteLLM consumer and Grafana administrator accounts. These accounts are managed by their respective applications. An end user consumes the service through the vLLM API or chat, a Kubernetes kubeconfig, or the LiteLLM UI and API, as described in the service guide.

The Sunstone web interface offers different [views]({{% relref "product/control_plane_configuration/graphical_user_interface/" %}}) that can be [customized with configuration]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone/#defining-a-new-view" %}}) to restrict visibility to the features each user has permissions to use. This helps reduce visual clutter and prevents users attempting prohibited actions. During these guides you will notice different views for each of the user accounts you control.  

{{< alert title="Tip" type="info" >}}
You need to switch between different OpenNebula user accounts in Sunstone during the course of these guides. To avoid repeatedly signing in and out it is recommended to use an incognito window or a different browser.
{{< /alert >}}

