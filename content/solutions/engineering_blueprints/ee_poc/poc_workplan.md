---

title: "Workplan"
linkTitle: "Workplan"
description: "Workplan for the OpenNebula Enterprise Edition Proof of Concept."
weight: 1

---

## Infrastructure Requirements and Deployment

{{< alert title="Warning" type="warning" >}}
The OpenNebula PoC service is designed to be deployed in an isolated environment, fully separated from production systems and without access to external networks or storage systems. Our PoC service includes an automated, low-friction setup process tailored for such isolated environments. It is important to note that OpenNebula cannot be held responsible for any downtime, damages, or other issues that may occur in connected production environments if the PoC is not deployed as intended.
{{< /alert >}}

The PoC program utilizes two methods for installing the PoC OpenNebula cloud. The recommended method is for the OpenNebula team to install in your environment using SSH/VPN.  The second option is using a custom-tailored ISO designed to simplify the deployment of a functional OpenNebula environment, enabling users to easily test-drive the platform’s core functionalities. Once the PoC cloud deployment is complete, users will be able to build and manage Virtual Machines and validate a variety of common cloud use cases.

Infrastructure requirements may vary depending on the final purpose of the infrastructure. As a minimum, customers should provide the following to deploy the OpenNebula cloud platform using the PoC ISO:

- A single bare-metal server which meets the minimum requirements described in Table 1 below. We recommend using 3 physical servers for a proper evaluation.  

<center>

| **Resource**  | **Recommended minimum**                                            |
| --------- |:---------------------------------------------------------------------- |
| Memory    | 64GB+                                                                  |
| CPU       | Intel or AMD CPU with 16+ cores and SSE2 support                       |
| Disk size | 512GB SSD                                                              |
| Network   | 1 (or more) dedicated NIC(s), with inbound 22 and 2616 ports available |

<sup>Table 1. Front-end hardware recommendations.</sup>

</center>

- Allocate a NIC port on the servers for the Management Network, and connect it to your infrastructure switch.

### Option 1

For the SSH/VPN installation method by our OpenNebula engineers:

- Ubuntu 24.04 installed in the physical servers
- Network configuration ensuring physical Hosts connectivity
- SSH access granted to OpenNebula Systems assigned engineering team members

### Option 2

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

## High-Level Reference Architecture

An OpenNebula PoC cloud is automatically deployed on a single server, as shown by the diagram below.

{{< image path="/images/ISO/00-onepoc_architecture.svg" align="center" width="90%" mb="20px">}}

As shown above, the design for a single-node OpenNebula PoC has the following features:

- The OpenNebula PoC cloud is deployed on a single bare-metal server, which meets the minimum system requirements listed in Table 1. Henceforth, this server will be referred to as the “OpenNebula server.” This can be later on extended to a second server which acts exclusively as a hypervisor Host.

- The OpenNebula server should have the following networking connections:
  - Connection to an IPMI (or other out-of-band KVM system) for initial server setup and embedded hardware configuration.
  - Connection to the Management Network. This connection should be configured on one of the server NIC ports. The Management Network will be used for:
    - Accessing the hypervisor Host OS for low-level management and troubleshooting.
    - Accessing Front-end VMs via the GUI for cloud management operations.
<br><br>

- The Host OS will be automatically installed and configured from the ISO image. It is based on the AlmaLinux 9 distribution and has all required packages for an isolated cloud deployment.

- The Front-end VM Hosts all OpenNebula cloud components, including the GUI, cloud lifecycle management services, CLI tools, etc. Once the cloud is deployed, it should be possible to access the GUI using the IP for the OpenNebula Server on port 2616.

- Once the deployment process has completed, the OpenNebula PoC cloud is ready for testing. It includes pre-configured cloud datastores backed by an NFS server running on the Host OS, sample internal Virtual Networks, test images, and VM templates.
<br><br>
  
  
## PoC Phases

{{< image path="/images/ISO/poc_diagram.png" align="center" width="90%" mb="20px">}}

### Request a Demo
The first step is to request a live demo. Contact us by [filling the demonstration request form](https://opennebula.io/evaluate-opennebula/#request-demo) or by email at: sales@opennebula.io.

### Introduction and Information Gathering Call

During this introductory call you communicate with OpenNebula's solution architects to discuss the details of your use case and then establish timescales and criteria required to successfully complete the PoC and transition to an OpenNebula Enterprise Edition annual subscription. Once we complete the initial arrangements, you will be provided with a personalized, one-time link to download the ISO file prepared specifically for your deployment.

### Introductory Call

On the PoC kick-off date the installation will proceed with the SSH and VPN credentials shared by the potential customer. If the ISO installation method is preferred, a one-hour call will be scheduled to discuss additional details on the ISO installation process. You will be provided access to a User Guide and you will complete the ISO installation during the call with the support of OpenNebula Engineers.

### Tutorial

A 90 minute tutorial covering the basics of OpenNebula is included in this PoC program. You will gain  enough knowledge of the OpenNebula platform to kick-start your internal evaluation.

### Support

Throughout the duration of the PoC, the Sales Engineering team will be the primary point of contact and will manage the testing alongside the OpenNebula engineering team who will be available through an ad-hoc mailing list to ask and solve doubts and issues you may encounter in your evaluation. This testing period will last up to a maximum of four weeks from the date you choose to start the PoC.

### Wrap-up

As you come to the end of the PoC testing period, a wrap-up call will be scheduled with you and the OpenNebula team as an opportunity to discuss any issues, the PoC’s results, and the next steps to transition to an annual Enterprise Edition subscription.
<br><br>
