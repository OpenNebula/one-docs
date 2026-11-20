---

title: "Overview of the AI Factory Guided Evaluation"
linkTitle: "Overview"
description: ""
weight: 1
---

The AI Factory PoC service allows potential customers to test the AI-ready capabilities of the OpenNebula platform on hosted infrastructure provided by OpenNebula. This provides a low-risk opportunity to assess its functionality, performance, and compatibility, ensuring it meets specific needs and requirements before committing to a full deployment.

This set of AI Factory PoC guides takes the user on a structured tour through OpenNebula's advanced AI capabilities. 

## How it Works

If you are interested in evaluating OpenNebula's AI capabilities through the PoC service, [contact the OpenNebula sales team](https://opennebula.io/contact/) to start the process. Once you have started the PoC process, the OpenNebula team will set up the hosted infrastructure with OpenNebula pre-installed and configured. Your PoC contact will send you instructions and credentials to connect to the hosted infrastructure and access the hosted OpenNebula cloud.

After receiving instructions and credentials from your OpenNebula PoC contact, you should follow the guides in the order given below:

* [Connecting to the Hosted Infrastructure via VPN]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}})
* [Managing Users, Groups and Access Permissions]({{% relref "solutions/engineering_blueprints/ai_poc/access_permissions/" %}})
* [Deploying a GPU-enabled Virtual Machine]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}})
* [Deploying GPU-enabled Kubernetes Clusters]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}})

## User Accounts and Views

The AI PoC demonstrates the functionality of OpenNebula's multitenancy user access model. The multitenancy model allows users to be assigned different levels of privileges, keeps user resources isolated and enables resource quotas to be applied to restrict user resource consumption. 

This guide uses multiple OpenNebula accounts to demonstrate the multitenancy model, you should receive credentials for all of them from your PoC contact:

| **Username** | **Description** |
|----------|-------------|
| **ncp-operator** | Administrative user with high-level privileges. Has the capacity to create and modify users, modify templates and set resource quotas. |
| **vm-tenant-admin** | Tenant user, has access only to the resources needed to launch a GPU-enabled VM. |
| **llm-tenant-admin** | Tenant user, has access only to the resources needed to launch a GPU-enabled Kubernetes Cluster. This users's resources are isolated from those of **vm-tenant-admin**. |

Sunstone offers different [views]({{% relref "product/control_plane_configuration/graphical_user_interface/" %}}) that can be [customized with configuration]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone/#defining-a-new-view" %}}) to restrict visibility of features to the features each user has permissions to use. This helps reduce visual clutter and prevents users attempting prohibited actions. During these guides you will notice different views for each of the users.  

{{< alert title="Tip" type="info" >}}
You need to switch regularly between different accounts in Sunstone during the course of these guides. To avoid repeatedly signing in and out repeatedly it is recommended to use an incognito window or a different browser.
{{< /alert >}}

