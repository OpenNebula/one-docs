---
title: "Installation Overview"
linkTitle: "Overview"
date: "2026-04-29"
description: 
categories:
pageintoc: "168"
tags:
show_card: false
weight: "1"
---

<a id="package-installation-references"></a>

This section contains details for deploying an OpenNebula-managed cloud manually. There are two principal components of an OpenNebula cloud deployment:

* **OpenNebula Front-end**: This is the control plane of an OpenNebula cloud deployment. The Front-end enables the deployment of Cluster nodes for handling cloud workloads along with the deployment and management of Virtual Machines, Virtual Networks, Kubernetes Clusters, cloud monitoring, user and security management.

* [**OpenNebula Clusters**]({{% relref "product/cluster_configuration/hosts_and_clusters/cluster_guide/" %}}): Logical groupings of Hosts, datastores and Virtual Networks that provide compute capacity. The OpenNebula Front-end deploys and manages Clusters using either on-premises hardware or resources from 3rd-party IaaS providers. Through the Edge Provisioning model, the Front-end can dynamically deploy and undeploy Edge Clusters on remote providers to scale cloud compute capacity on demand.

## How Should I Read This Chapter

Installation starts with the deployment of an OpenNebula Front-end. You should start with the [Front-end Deployment Documentation](#front-end-deployment), choosing the appropriate installation method for your use case. After installing the OpenNebula Front-end, you can proceed with the [Cluster Deployment Documentation](#cluster-deployment). After successful deployment of an OpenNebula cloud, you can customize it through [configuration](#configuration). 

The documentation in this section details how to install OpenNebula manually, there are also automated installation options available with miniONE for Front-end installation and OneForm for Cluster installation. If you would prefer to install via the automated methods refer to the [Automated Installation Guides]({{% relref "getting_started/install_opennebula/production/" %}}) in the Getting Started section.

## Front-end Deployment

The first step in deploying an OpenNebula cloud is deploying the OpenNebula Front-end. There are three options:

* [**Automatic Deployment with miniONE**]({{% relref "getting_started/install_opennebula/production/minione_frontend_install/" %}}): miniONE is a tool for rapid deployment of an OpenNebula Front-end, suitable for evaluation, testing, learning and rapid installation of a production deployment. 
* **Manual Deployment with System Packages**: This option is appropriate for a production environment, for users needing fine-grained control over an OpenNebula cloud deployment. The process consists of three steps to be followed in order:
    1. [Database Setup]({{% relref "software/installation_process/frontend_installation/database" %}})
    2. Repository Configuration:
        * [Repository Configuration for OpenNebula Community Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ce/" %}})
        * [Repository Configuration for OpenNebula Enterprise Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ee/" %}})
    3. [Single Front-end Installation]({{% relref "software/installation_process/frontend_installation/frontend_install/" %}})
* [**Advanced Deployment with OneDeploy**]({{% relref "getting_started/install_opennebula/one_deploy/one_deploy_overview" %}}): OneDeploy automates the deployment of cloud infrastructure with advanced configuration options.

After deploying an OpenNebula Front-end, you can move on to deploying and managing Clusters through OpenNebula's Sunstone user interface, the CLI or the REST API.

## Cluster Deployment

After successfully deploying an OpenNebula Front-end, you can proceed to manually install or automatically create (provision) Clusters to handle cloud workloads. There are three options:

* [Automated Cluster Provisioning with OneForm]({{% relref "getting_started/install_opennebula/production/cluster_oneform/" %}})
* [Manual Cluster Installation with KVM]({{% relref "software/installation_process/cluster_installation/kvm_node_installation/" %}})
* [Manual Cluster Installation with LXC]({{% relref "software/installation_process/cluster_installation/lxc_node_installation/" %}})

OneDeploy can also be used to deploy Cluster nodes (independently or simultaneously with Front-end deployment). Please refer to the [Advanced Installation with OneDeploy]({{% relref "getting_started/install_opennebula/one_deploy/one_deploy_overview" %}}) documentation.

## Configuration

After deploying an OpenNebula cloud, you can customize the deployment through configuration. The complete references for configuring OpenNebula services, templates, and hypervisor nodes may be found in [Operation References]({{% relref "product/operation_references/" %}}).
