---
title: Overview
weight: 1
show_card: false
description: "Overview of AI factory deployment and validation."
tags: ['AI']
---

<a id="overview"></a>

The purpose of the AI Factory blueprint collection is to provide a step-by-step process for setting up a simple AI Factory system and getting it up and running quickly, including:

* Identifying the minimum hardware and networking requirements for your AI Factory. These baseline specifications also serve as a reference for more advanced deployments. OpenNebula supports high-performance architectures such as InfiniBand, Spectrum-X, and NVLink, although these setups are not automated and require custom configuration.
<br>

* Follow the step-by-step deployment instructions using OneDeploy to build your AI Factory, with options for both [on-premises installations]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises/" %}}) and [cloud-based deployments]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_cloud/" %}}).
<br>

* Optionally, you can validate the setup using the same methodology we apply during formal infrastructure acceptance. This validation covers direct [vLLM execution for inference]({{% relref "/solutions/ai_factory_blueprints/direct_ai_execution/llm_inference_certification/" %}}), [SLURM integration for fine-tuning]({{% relref "/solutions/ai_factory_blueprints/direct_ai_execution/nvidia_slurm/" %}}), and Kubernetes-based execution using [NVIDIA Dynamo&reg;]({{% relref "/solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo/" %}}) for inference and [NVIDIA KAI Scheduler&reg;]({{% relref "/solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler/" %}}) .

## Hardware Requirements

AI Factories require high performance server hardware, including accelerated infrastructure such as GPUs and high-performance networking. The following details outline a minimal recommended hardware configuration:

* **CPU**: 16 physical or logical CPU cores with hardware virtualization support.
* **Memory**: 64 GB RAM. More memory is recommended when running multiple Kubernetes workers or large AI models.
* **Storage**: At least 250 GB of fast SSD or NVMe storage, with sufficient additional capacity for VM images, container images, model weights, and datasets.
* **GPU**: At least one NVIDIA data-center GPU with PCI passthrough support. Two GPUs are recommended for testing disaggregated inference workloads such as separate prefill and decode workers. See the [Platform Notes]({{% relref "/software/release_information/release_notes/platform_notes/#accelerated-infrastructure" %}}) for supported GPU models.
* **Networking**: At least one physical Ethernet interface suitable for bridged OpenNebula networking. A 10 GbE or faster network is recommended for multi-node deployments.
* **Virtualization**: CPU virtualization extensions and IOMMU enabled in the system firmware to support KVM and PCI passthrough.
* **Operating system**: Ubuntu 24.04 is highly recommended. See the [Platform Notes]({{% relref "/software/release_information/release_notes/platform_notes/#front-end-components" %}}) for a list of alternative operating systems supported by OpenNebula.
* **Bare-metal Cloud Instances**: If you are using resources provided by a 3rd-party cloud provider, bare-metal instances are highly recommended. AI Factory deployments on virtual instances will result in heavily degraded performance and may not function at all.

{{< alert title="Important" type="primary" >}}
The guides in this AI Factory Blueprints documentation have been developed and tested with **Ubuntu 24.04**. We recommend using Ubuntu 24.04 while following these guides if possible. If you must use an alternative operating system, you should adjust the command line instructions accordingly and be aware that troubleshooting may be necessary.
{{< /alert >}}

## Basic Outline

Configuring, deploying and validating a high-performance AI infrastructure using OpenNebula involves these steps:

1. Familiarize yourself with [**Architecture and Specifications**]({{% relref "/getting_started/understand_opennebula/cloud_architecture_and_design/cloud_architecture_design/" %}}). We recommend consulting the [guide on GPU PCI-passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough" %}}) for details relating to your GPU hardware and IOMMU.
<br>

2. Deploy and configure your AI Factory with one of these alternatives:
    * [On-premises AI Factory Deployment]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_on-premises" %}}): Set up an AI Factory using OneDeploy for On-premise environments.
    * [On-cloud AI Factory Deployment]({{% relref "/solutions/ai_factory_blueprints/deployment/cd_cloud" %}}): Set up an AI Factory using OneDeploy with Scaleway for cloud environments.
<br>
<br>

3. Integrate external infrastructure services if required:
    * [NVIDIA InfraControler (NICo)]({{% relref "product/virtual_machines_operation/metal_instances/bare_metal_nico" %}}): Offer multi-tenant bare metal instances from an existing OpenNebula cloud.
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
        * [LLM Inferencing with NVIDIA Dynamo]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_dynamo" %}}): Integrating the GPU-powered Kubernetes Cluster with the NVIDIA Dynamo Cloud Platform to provision and manage AI workloads through the Dynamo framework for your AI workloads on top of the NVIDIA Dynamo framework.
        * [Scheduling with NVIDIA KAI Scheduler]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/nvidia_kai_scheduler" %}}): Use the NVIDIA KAI Scheduler to share GPU resources across different workloads within the AI-ready Kubernetes Cluster.
