---
title: "Advanced Deployment with OneDeploy"
date: "2025-02-17"
description:
categories:
pageintoc: "26"
tags: [OneDeploy, deployment, 'automatic deployment', installation]
weight: "1"
resources:
- src: "assets/images/one_deploy_basic_arch.png"
  params:
    byline: "Example"
---

<a id="one-deploy-overview"></a>

<!--# Overview of Automatic Deployment -->

OpenNebula provides [OneDeploy](https://github.com/OpenNebula/one-deploy), a set of Ansible playbooks that allows you to automatically deploy an OpenNebula cloud in a simple and convenient way.

[Ansible](https://www.ansible.com) is a Python application for IT automation. It can deploy software, configure systems, and orchestrate complex deployments and workflows.

The Ansible playbooks in OneDeploy install a complete OpenNebula cloud, including the Front-end with the OneFlow and OneGate services, and the Sunstone UI. Before running the playbooks, you can modify variables to configure the OpenNebula cloud that will be created. For example, you can select the OpenNebula version to install, and define the network, storage configuration, and other options.

To perform automated deployments, the Ansible architecture is based on the concept of a control node and managed nodes. You designate a machine as a control node, where you will run the playbooks to deploy on the managed nodes. Nodes may be physical or virtual and you can deploy to any nodes that you have network access to.

The basic procedure is as follows:

1. Download the playbooks on the machine that you designate as control node, where you will run the playbooks.
2. Modify the inventory according to your needs.
3. Run the playbooks on the control node, to deploy on the managed nodes.

Ansible is an agentless platform and uses SSH as the default transport for deployment. The control node must be able to communicate with the managed nodes via SSH.

{{< image path="/images/one_deploy_basic_arch.svg" alt="OpenNebula Basic Architecture" align="center" width="50%" mb="20px" border="false" >}}

<!-- ![image](/images/one_deploy_basic_arch.png)
<br/> -->

It is worth noting that you can use the control node itself as a managed node. In the tutorials included in this documentation, the OpenNebula Front-end is installed on the Ansible control node and the Hypervisors on the managed nodes.

In the sections below you will find a brief overview of reference architectures and requirements for installing an OpenNebula cloud with the most basic configuration. The documentation also includes two short tutorials for performing a simple installation on two of the reference architectures: using local storage for datastores, and using shared storage.

{{< alert title="Important" type="info" >}}
The recommended OS for running the playbooks is Ubuntu 24.04 or 22.04. The tutorials contain configuration and commands tested on these versions. It is possible to use other OSs to perform the installation; for reference please see the [OneDeploy Wiki](https://github.com/OpenNebula/one-deploy/wiki).{{< /alert >}} 

## OneDeploy Wiki

The OneDeploy Wiki is the primary documentation resource for deploying a multitude of cloud architectures with OneDeploy. You will find documentation for deploying several reference architectures, advanced configurations and developer information. Please visit the [OneDeploy Wiki Homepage](https://github.com/OpenNebula/one-deploy/wiki) to get started deploying an OpenNebula cloud with OneDeploy.