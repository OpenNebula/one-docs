---
title: "Workplan"
linkTitle: "Workplan"
description: "Workplan for the OpenNebula Enterprise Edition Proof of Concept."
weight: 1

---
{{< image path="/images/ISO/poc.drawio.png" align="center" width="90%" mb="20px">}}

The first step is to request a live demo. Contact us by [filling the form](https://opennebula.io/evaluate-opennebula/) or by email at: sales@opennebula.io

By using the Proof of Concept service, prospects get the following benefits:

- Stable Software Version – It leverages a more fixed and tested software version, since the PoC features OpenNebula Enterprise Edition (EE). This ensures higher stability that prospects might encounter with the Community Edition (CE).

- Pre-Installed & Pre-Configured Environment – It eliminates the installation and configuration burden, allowing prospects to focus on testing features and evaluating performance rather than troubleshooting setup issues.


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

## Infrastructure Requirements and Deployment

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

## Hands-on Skill and Knowledge Requirements

Personnel who execute and operate the OpenNebula PoC are expected to possess the following hands-on skills and knowledge:  

1. Generic Linux administration skills, such as managing users and groups, navigating the Linux filesystem and managing files.

2. A good understanding of virtualization concepts, including virtualized networking and storage.

3. Knowledge of common linux utilities, services and tools; such as, but not limited to:
   
   - Linux storage subsystem: local disks management, NFS mount management
   
   - Networking utilities: iptables, tcpdump, iproute2 and Linux bridges
   
   - Virtualization management: KVM, QEMU, libvirt/virsh
   
   - Linux services configuration and operation: passwordless SSH configuration

<br><br>

## High-Level Reference Architecture

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
