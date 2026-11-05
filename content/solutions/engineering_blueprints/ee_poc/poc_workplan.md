---
title: "Workplan"
linkTitle: "Workplan"
description: "Workplan for the OpenNebula Enterprise Edition Proof of Concept."
weight: 1

---

## Infrastructure Requirements and Deployment

Once the PoC cloud deployment is complete, users will be able to build and manage Virtual Machines and validate a variety of common cloud use cases.

Infrastructure requirements may vary depending on the final purpose of the infrastructure. As a minimum, customers should provide the following to deploy the OpenNebula cloud platform:

- A single bare-metal server which meets the minimum requirements described in Table 1 below. We recommend using 3 physical servers for a proper evaluation.  

<center>

| **Resource** | **Recommended minimum**                                                |
| ------------ |:---------------------------------------------------------------------- |
| Memory       | 64GB+                                                                  |
| CPU          | Intel or AMD CPU with 16+ cores and SSE2 support                       |
| Disk size    | 512GB SSD                                                              |
| Network      | 1 (or more) dedicated NIC(s), with inbound 22 and 2616 ports available |

<sup>Table 1. Front-end hardware recommendations.</sup>

</center>

- Allocate a NIC port on the servers for the Management Network, and connect it to your infrastructure switch.

The PoC program offers two deployment methods: [Remote Deployment](#remote-deployment), in which an OpenNebula engineer installs the cloud in your target infrastructure using SSH/VPN, and [ISO Installation](#iso-installation), in which you deploy the cloud using a custom-tailored ISO. The appropriate method will be agreed during the preparation phase.

### Remote Deployment {#remote-deployment}

For the SSH/VPN installation method, our OpenNebula engineers will create a design document to guide the deployment. An assigned OpenNebula engineer will use this document to perform the deployment in your target infrastructure. This method requires:

- Ubuntu 24.04 installed in the physical servers
- Network configuration ensuring physical Hosts connectivity
- SSH access granted to OpenNebula Systems assigned engineering team members

### ISO Installation {#iso-installation}

For the ISO installation method:

- Access to an IPMI (or other out-of-band KVM system) for initial PoC cloud bootstrapping using the OpenNebula ISO.
- A USB stick or other removable media storage is required to upload the OpenNebula ISO image, enabling a quick and straightforward deployment of the OpenNebula environment for the PoC program.  

## Hands-on Skills and Knowledge Requirements

Personnel who execute and operate the OpenNebula PoC are expected to possess the following hands-on skills and knowledge:  

1. Generic Linux administration skills, such as managing users and groups, navigating the Linux filesystem and managing files.
2. A good understanding of virtualization concepts, including virtualized networking and storage.
3. Knowledge of common Linux utilities, services and tools; such as, but not limited to: 
   - **Linux storage subsystem**: Local disks management, NFS mount management
   - **Networking utilities**: iptables, tcpdump, iproute2 and Linux bridges
   - **Virtualization management**: KVM, QEMU, libvirt/virsh
   - **Linux services configuration and operation**: Passwordless SSH configuration

## How Can I Take Part in a PoC?

Before starting a PoC, we hold discovery and demonstration sessions to understand your needs. Contact us by [filling in the demonstration request form](https://opennebula.io/evaluate-opennebula/#request-demo) or by email at sales@opennebula.io.

## Proof of Concept Phases

{{< image path="/images/ISO/poc_diagram.png" align="center" width="90%" mb="20px">}}

### 1. Success Criteria and Preparation Phase {#information-gathering-call}

During this phase, you communicate with OpenNebula's solution architects to discuss the details of your use case and establish the timescales and criteria required to successfully complete the PoC and transition to an OpenNebula Enterprise Edition annual subscription.

We will prepare a spreadsheet describing the success criteria to be used during the PoC. It will be based on the criteria in the [Success Criteria guide]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/" %}}) and will include any custom success criteria that are within the [scope of the PoC]({{% relref "solutions/engineering_blueprints/ee_poc/poc_overview/#is-running-an-opennebula-poc-for-me" %}}).

We will also agree on a schedule of weekly meetings to align on the PoC and review its progress against the agreed success criteria throughout the evaluation.

Once we complete the initial arrangements, an engineer will contact you to agree on the design and start the [Remote Deployment](#remote-deployment), if that method is suitable, or provide you with a personalized, one-time link to download the ISO file prepared specifically for your [ISO Installation](#iso-installation).

### 2. Infrastructure Readiness Phase

For a [Remote Deployment](#remote-deployment), you prepare the infrastructure according to the agreed design. For an [ISO Installation](#iso-installation), you prepare the infrastructure according to the [hardware and personnel requirements]({{% relref "solutions/engineering_blueprints/ee_poc/ee_poc_iso/#hardware-and-personnel-requirements" %}}).

Before the deployment begins, you must confirm that all required infrastructure, network configuration, access and credentials are ready.

### 3. Deployment Phase

On the PoC kick-off date, the installation will proceed using the SSH and VPN credentials you provided for a Remote Deployment. For an ISO Installation, a one-hour call will be scheduled to discuss the installation process. During the call, you will be able to complete the installation with the support of OpenNebula engineers by following the [ISO-based deployment guide]({{% relref "solutions/engineering_blueprints/ee_poc/ee_poc_iso/#Introduction" %}}).

### 4. Knowledge Transfer Phase

After the deployment, OpenNebula engineers will hand over the access credentials and provide a 90-minute tutorial covering the basics of OpenNebula in your environment. During this session, we will walk through the default success criteria and show you how to validate them, giving you the knowledge needed to begin your internal evaluation.

### 5. Validation Phase

You will validate the agreed default and custom success criteria with our assistance. Throughout the PoC, the Sales Engineering team will be your primary point of contact and will manage the testing alongside the OpenNebula engineering team. The engineering team will be available through an ad-hoc mailing list to answer questions and resolve issues encountered during your evaluation. This testing period will last up to four weeks from the date you choose to start the PoC.

### 6. Acceptance and Wrap-up Phase

As you come to the end of the PoC testing period, a wrap-up call will be scheduled with you and the OpenNebula team as an opportunity to discuss any issues, the PoC’s results, and the next steps to transition to an annual Enterprise Edition subscription. During this call, we will review the success criteria spreadsheet with you to ascertain whether the different success criteria items were correctly validated.
<br><br>
