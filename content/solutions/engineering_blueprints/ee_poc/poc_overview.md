---
title: "Overview"
linkTitle: "Overview"
description: "Overview of the workplan for the OpenNebula Enterprise Edition Proof of Concept."
weight: 1

---

# Abstract

The OpenNebula Proof of Concept (PoC) service allows potential customers to test the Enterprise Edition of OpenNebula software directly in their own environment. This provides a low-risk opportunity to assess its functionality, performance, and compatibility, ensuring it meets their specific needs and requirements before committing to a full deployment.

By allowing organizations to experience the platform’s capabilities first-hand, the PoC service empowers potential customers to make informed decisions and fully understand the value and benefits of an Enterprise Edition subscription.

This document outlines the hardware and architectural requirements necessary to begin working with OpenNebula. Additionally, it specifies the skills and expertise required from the internal resources responsible for managing the Proof of Concept (PoC) within the potential customer’s environment.

Finally, this document outlines our phased approach to the PoC service, which ensures ongoing bi-directional communication with OpenNebula Solution Architects and other engineering resources, providing expert guidance and support throughout the Proof of Concept process.

The first step is to request a live demo. Contact us by [filling the form](https://opennebula.io/evaluate-opennebula/) or by email at: sales@opennebula.io

# What is OpenNebula?

**OpenNebula is a powerful, but easy-to-use, open source platform to build and manage enterprise clouds and virtualized DCs.** It combines existing virtualization technologies with advanced features for multi-tenancy, automatic provision, and elasticity. The development of OpenNebula follows a bottom-up approach driven by the real needs of sysadmins, DevOps, and users. 

OpenNebula is an open product with an active community, and is commercially supported by OpenNebula Systems. Updated versions of OpenNebula are released regularly, and delivered as a single package with a smooth migration path. More information on the benefits of running an OpenNebula cloud can be checked on the Key Features page.

There are two versions of the solution, namely **Community** Edition and **Enterprise** Edition.  This POC will leverage the **Enterprise Edition**, which is the commercially supported version with access to functionality such as Veeam and NetApp integration among others.

By using the Proof of Concept service, prospects get the following benefits:

- Stable Software Version – It leverages a more fixed and tested software version, since the PoC features OpenNebula Enterprise Edition (EE). This ensures higher stability that prospects might encounter with the Community Edition (CE).

- Pre-Installed & Pre-Configured Environment – It eliminates the installation and configuration burden, allowing prospects to focus on testing features and evaluating performance rather than troubleshooting setup issues.

# Infrastructure Requirements and Deployment

{{< alert title="Warning" type="warning" >}}
The OpenNebula PoC service is designed to be deployed in an isolated environment, fully separated from production systems and without access to external networks or storage systems. Our PoC service includes an automated, low-friction setup process tailored for such isolated environments. It is important to note that OpenNebula cannot be held responsible for any downtime, damages, or other issues that may occur in connected production environments if the PoC is not deployed as intended.
{{< /alert >}}

The PoC program utilizes 2 methods for installing the POC.  The recommended way would be for the OpenNebula team to install in your environment using SSH/VPN.  The second option would be using a  custom-tailored ISO designed to simplify the deployment of a functional OpenNebula environment, enabling users to easily test-drive the platform’s core functionalities. Once the PoC cloud deployment is complete, users will be able to build and manage virtual machines and validate a variety of common cloud use cases.

Infrastructure requirements may vary depending on the final purpose of the infrastructure. As a minimum, prospects should provide the following to deploy the OpenNebula cloud platform using the PoC ISO:

- A single bare-metal server which meets the minimum requirements described in Table 1. We recommend using 3 physical servers for a proper evaluation.  

<center>

| Memory    | 64GB+                                                                  |
| --------- |:---------------------------------------------------------------------- |
| CPU       | Intel or AMD CPU with 16+ cores and SSE2 support                       |
| Disk size | 512GB SSD                                                              |
| Network   | 1 (or more) dedicated NIC(s), with inbound 22 and 2616 ports available |

<sup>Table 1. Front-end hardware recommendations.  </sup>

</center>

- Allocate a NIC port on the servers for the Management Network, and connect it to your infrastructure switch.  <br><br><br>

**Option 1:** for the SSH/VPN installation method by our OpenNebula engineers:

- Ubuntu 24.04 installed in the physical servers

- Network configuration ensuring physical hosts connectivity

- SSH access granted to OpenNebula Systems assigned engineering team members  <br><br><br>

**Option 2:** for the ISO installation method:

- Access to an IPMI (or other out-of-band KVM system) for initial PoC cloud  bootstrapping using the OpenNebula ISO.

- A USB stick or other removable media storage is required to upload the OpenNebula ISO, enabling a quick and straightforward deployment of the OpenNebula environment for the PoC program.  

<br><br>

# Hands-on Skill and Knowledge Requirements

Personnel who execute and operate the OpenNebula PoC are expected to possess the following hands-on skills and knowledge:  

1. Generic Linux administration skills, such as managing users and groups, navigating the Linux filesystem and managing files.

2. A good understanding of virtualization concepts, including virtualized networking and storage.

3. Knowledge of common linux utilities, services and tools; such as, but not limited to:
    - Linux storage subsystem: local disks management, NFS mount management

    - Networking utilities: iptables, tcpdump, iproute2 and Linux bridges

    - Virtualization management: KVM, QEMU, libvirt/virsh

    - Linux services configuration and operation: passwordless SSH configuration

<br><br>

# High-Level Reference Architecture

An OpenNebula PoC cloud is automatically deployed on a single server, as shown by the diagram below.  <br><br>
![image tag](/images/ISO/00-onepoc_architecture.svg)

As shown above, the design for a single-node OpenNebula PoC has the following features:

- The OpenNebula PoC cloud is deployed on a single bare-metal server, which meets the minimum system requirements listed in Table 1. Henceforth, this server will be referred to as the “OpenNebula server.” This can be later on extended to a second server which will act exclusively as a hypervisor host.

- The OpenNebula server should have the following networking connections:
  
  - Connection to an IPMI (or other out-of-band KVM system) for initial server setup and embedded hardware configuration.
  
  - Connection to the Management Network. This connection should be configured on one of the server NIC ports. The Management Network will be used for:
  
  - Accessing the hypervisor host OS for low-level management and troubleshooting

Accessing Front End VMs via the GUI for cloud management operations

- The host OS will be automatically installed and configured from the ISO image. It is based on the AlmaLinux 9 distribution and has all required packages for an isolated cloud deployment.

- The Front-end VM hosts all OpenNebula cloud components, including the GUI, cloud lifecycle management services, CLI tools, etc. Once the cloud is deployed, it should be possible to access the GUI using the IP for the OpenNebula Server on port 2616.

- Once the deployment process has completed, the OpenNebula PoC cloud is ready for testing. It includes pre-configured cloud datastores backed by an NFS server running on the host OS, sample internal virtual networks, and test image and VM templates.
<br><br>
# PoC Phases

## Introduction and Information Gathering Call

This is an introductory call to understand the use case, timescales and criteria required to successfully complete the PoC and transition to an OpenNebula Enterprise Edition annual subscription. Once we complete the initial arrangements, you will be provided with a personalized, one-time link to download the ISO file prepared specifically for your deployment.

## PoC Introductory Call

On the kick-off date for the PoC the installation would proceed with the defined SSH and VPN credentials shared by the potential customer,.
If the ISO installation method is preferred, a one-hour call will be scheduled to go over additional details on the ISO installation and process. You will be provided access to a User Guide and will have the opportunity to install the ISO during the call with the support of OpenNebula Engineers.

## PoC Tutorial

A 90 minute tutorial covering the basics of OpenNebula is included in this PoC program. You will gain  enough knowledge of the OpenNebula platform to kick-start your internal evaluation.

## PoC Support

Throughout the duration of the PoC,  the Sales Engineering team will be the primary point of contact and will manage the testing alongside the OpenNebula engineering team who will be available through an ad-hoc mailing list to ask and solve doubts and issues you may encounter in your evaluation. This testing period will last up to a maximum of four weeks from the date you choose to start the PoC.

## PoC Wrap-up

As you come to the end of the PoC testing period, a wrap-up call will be scheduled with you and the OpenNebula team as an opportunity to discuss any issues, the PoC’s results, and the next steps to transition to an annual Enterprise Edition subscription.
<br><br>
# Is Running an OpenNebula PoC for Me?

Running an OpenNebula PoC in your own environment is an excellent way to explore how OpenNebula operates and evaluate its core functionalities. However, it is important to note that the PoC environment is not designed to precisely replicate your production environment.

The PoC described above provides an opportunity to familiarize yourself with the core functionality of OpenNebula software. However, if you require a setup tailored to your specific environment—such as integrating a software-defined SAN solution, running multiple hypervisors, or implementing custom network configurations—please contact the OpenNebula team to discuss customized solutions designed to meet your unique testing needs.

The table below should help you decide the best medium to test and validate OpenNebula in your own environment. For more details on any of these options, reach out to your account manager or [get in touch](https://opennebula.io/contact/).

<center>

|                               | OpenNebula CE   | OpenNebula PoC       | OpenNebula Custom Pilot                                                           |
| ----------------------------- | --------------- | -------------------- | --------------------------------------------------------------------------------- |
| Price                         | FREE            | FREE                 | [Get in touch](https://opennebula.io/contact/)                                    |
| Maximum # of Hosts            | Unlimited       | 3                    | Unlimited                                                                         |
| Training                      | No              | Included             | via [Professional Service](https://opennebula.io/enterprise/#enterprise_services) |
| OpenNebula Consultant Access  | No              | Up to 5 hours        | via [Professional Service](https://opennebula.io/enterprise/#enterprise_services) |
| OpenNebula Support            | Community Forum | Enterprise - Limited | Enterprise                                                                        |
| Duration                      | Unlimited       | 4 weeks              | [Get in touch](https://opennebula.io/contact/)                                    |
| OpenNebula Enterprise Edition | No              | Yes                  | Yes                                                                               |
| Predefined Architecture       | No              | Yes                  | No                                                                                |

</center>
<br>
An OpenNebula PoC offers a unique opportunity to engage directly with the OpenNebula Services team, ensuring your cloud infrastructure deployment stays on track and progresses toward a successful outcome.

In addition to introductory and wrap-up calls with the OpenNebula commercial and technical teams, the PoC includes an exclusive two-hour training session led by our experts. This session is designed to equip you and your team with the essential knowledge and skills needed to effectively deploy and test OpenNebula within your own environment.
