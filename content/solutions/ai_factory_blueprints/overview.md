---
title: Overview
weight: 1
show_card: false
description: "Overview of AI factory deployment and validation."
tags: ['AI']
---

<a id="overview"></a>

The purpose of the AI Factory collection is to provide a step-by-step process for setting up a simple AI Factory system and getting it up and running quickly, including:

* Identifying the minimum hardware and networking requirements for your AI Factory. These baseline specifications also serve as a reference for more advanced deployments. OpenNebula supports high-performance architectures such as InfiniBand, Spectrum-X, and NVLink, although these setups are not automated and require custom configuration.
<br>

* Follow the step-by-step deployment instructions using OneDeploy to build your AI Factory, with options for both on-premises installations and cloud-based deployments.
<br>

* Optionally, you can validate the setup using the same methodology we apply during formal infrastructure acceptance. This validation covers direct vLLM execution for inference, SLURM integration for fine-tuning, and Kubernetes-based execution using NVIDIA Dynamo&reg; for inference and NVIDIA KAI Scheduler&reg;.


## Basic Outline

Configuring, deploying and validating a high-performance AI infrastructure using OpenNebula involves these steps:

1. Familiarize yourself with **Architecture and Specifications**. We recommend consulting the [guide on GPU PCI-passthrough]({{% relref "product/cluster_configuration/hosts_and_clusters/nvidia_gpu_passthrough" %}}) for details relating to your GPU hardware and IOMMU.
<br>

2. Deploy and configure your AI Factory with one of these alternatives:
    * [On-premises AI Factory Deployment]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}}): Set up an AI Factory using OneDeploy for On-premise environments.
    * [On-cloud AI Factory Deployment]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_cloud" %}}): Set up an AI Factory using OneDeploy on Scaleway for cloud environments.
<br>
<br>

3. Integrate external infrastructure services when required:
    * [Bare Metal as a Service with NICo]({{% relref "product/virtual_machines_operation/metal_instances/bare_metal_nico" %}}): Offer multi-tenant bare metal instances from an existing OpenNebula cloud.
<br>
<br>

4. Perform Validation: As a prerequisite, you must have an AI Factory ready to be validated after completing the above installation procedures. These are the options to validate your AI Factory:
    
    * [Direct AI execution]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution" %}}):
        * [LLM Inferencing with vLLM]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/llm_inference_certification" %}}): Using vLLM with two different models and two model sizes, running across both H100 and L40S GPUs.
        * [LLM Fine-Tuning with NVIDIA Slurm]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/nvidia_slurm" %}}): Fine tuning an AI model using the OpenNebula NVIDIA Slurm appliance.
<br>
<br>

    * [Containerized AI Execution]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}): 
        * [Deployment of AI-Ready Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}}): Use H100 and L40S deployment to run Kubernetes.
        * [LLM Inferencing with NVIDIA Dynamo]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo" %}}): Integrating the GPU-powered Kubernetes cluster with the NVIDIA Dynamo Cloud Platform to provision and manage AI workloads through the Dynamo framework for your AI workloads on top of the NVIDIA Dynamo framework. 
        * [Scheduling with NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler" %}}): Use the NVIDIA KAI Scheduler to share GPU resources across different workloads within the AI-ready Kubernetes cluster.
