---
title: "Overview"
linkTitle: "Overview"
date: "2026-04-15"
description: "OpenNebula Front-end installation overview."
categories:
pageintoc: "168"
tags:
weight: "1"
---

<a id="frontend-installation"></a>

The **OpenNebula Front-end** serves as the control plane for your entire cloud infrastructure. It is the central orchestrator responsible for deploying and managing the lifecycle of Cluster nodes, Virtual Machines (VMs), Virtual Networks, and storage datastores. The Front-end Hosts the core OpenNebula services and provides the interfaces — a REST API, a CLI and the Sunstone user interface — through which administrators and users interact with the cloud. 

The Front-end can be deployed using an on-premises server, a Virtual Machine, or bare-metal instance from an IaaS cloud provider such as AWS or Scaleway. This decision is governed by the intended cloud architecture and available resources. Ensure that the virtual or physical machine on which you intend to deploy the Front-end meets the minimum [requirements given below](#requirements). 

Once you have deployed an OpenNebula Front-end, you can deploy and manage Cluster nodes for handling cloud workloads including Kubernetes Clusters and Virtual Machines. The server on which you deploy the Front-end can also be used as a workload Cluster node simultaneously, if the hardware specification is adequate.

## Installation Methods

Depending on your environment (evaluation, testing, or production) and your preference for automation, there are three options to deploy your OpenNebula Front-end.

### 1. Automated Installation via miniONE

The miniONE tool is the fastest method to get an OpenNebula cloud up and running. It is a lightweight installation script designed for deploying an OpenNebula cloud configuration specialized for quick startup. miniONE is ideal for evaluation, testing and learning, but can also be used to quickly bootstrap a production deployment, with later reconfiguration for production hardening.  

* **Best for**: Rapid prototyping, sandboxes, testing, learning and quickly bootstrapping a production deployment.  

* **Workflow**: A single command installs the Front-end and, optionally, a local KVM or LXC hypervisor on the same Host.

* **Environment**: Typically used on a fresh Linux installation (Ubuntu or AlmaLinux).

Refer to the [Automatic Installation with miniONE Documentation]({{% relref "getting_started/install_opennebula/production/minione_frontend_install/" %}}) for more details. 

{{< alert title="Note" type="info" >}}
The miniONE installation is not appropriate for production environments, if you intend to deploy a production cloud, we recommend that you use the [Manual Installation Process](#2-manual-installation-with-system-packages) or [OneDeploy](#3-advanced-deployment-with-onedeploy).
{{< /alert >}}

### 2. Manual Installation with System Packages

For users who require granular control over an OpenNebula cloud deployment, the manual method involves installing OpenNebula directly from official system repositories. The guides in this section outline the manual installation process.

* **Best for**: Custom production architectures, specific security hardening, or integration with existing databases.

* **Workflow**: Complete the following steps in order: 
    1. [Install and configure the database]({{% relref "software/installation_process/frontend_installation/database/" %}}) (SQLite by default, or MySQL/MariaDB for production)
    2. Configure the official OpenNebula repositories for your Linux distribution and OpenNebula edition:
        * [Configure the OpenNebula repositories for the Community Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ce/" %}})
        * [Configure the OpenNebula repositories for the Enterprise Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ee/" %}})
    3. [Install the Front-end packages]({{% relref "software/installation_process/frontend_installation/frontend_install/" %}})

* **Environment**: Recommended with a fresh Linux installation (Ubuntu or AlmaLinux), this can also work on existing infrastructure with appropriate configuration.

### 3. Advanced Deployment with OneDeploy

OneDeploy is an Ansible-based automation toolset intended for complex, production-ready, or High Availability (HA) deployments. If you are looking to automate the deployment of OpenNebula with high flexibility (such as a multi-node production environment distributed across various infrastructure providers), please refer to the [Advanced Installation with OneDeploy]({{% relref "getting_started/install_opennebula/one_deploy/one_deploy_overview/" %}}) section of the documentation.  

## Cluster Installation 

After completing the installation of an OpenNebula Front-end, you can then proceed to manually install or automatically provision Clusters to handle cloud workloads. Refer to the [Cluster Installation Documentation]({{% relref "software/installation_process/cluster_installation/" %}}). Clusters can also be deployed using OneDeploy, 

## Requirements

Regardless of the method chosen, you must ensure that your Host meets the minimum hardware requirements and has a clean operating system installation to avoid dependency conflicts. 

**Supported operating systems:**
* RHEL/AlmaLinux 9 or 10
* Debian 12 or 13
* Ubuntu 24.04 or 26.04
* openSUSE 16.0, SLES 15.7
* See the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes.md" %}}) for further details on compatible operating systems

**Minimum hardware:**

Hardware requirements for the Front-end machine differ if you intend the target machine to be used solely for the Front-end control plane or for the machine to be used for both the Front-end and Cluster workloads.

**Front-end only**:
* Virtual Machine or bare-metal instance
* 16 GiB RAM
* 80 GiB free disk space

**Kubernetes**:
* Bare-metal instance recommended
* 64 GiB RAM
* 120 GiB free disk space
<br> 

**AI Factory**:
* Bare-metal instance recommended
* 128 GiB RAM
* 512 GiB free disk space
* NVIDIA L40S or H100 GPU
