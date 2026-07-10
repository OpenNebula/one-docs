---
title: "Key Features"
date: "2025-02-17"
description:
categories: [Introduction, Overview]
pageintoc: "5"
tags: [Features]
type: docs
weight: "2"
---

OpenNebula offers a simple but feature-rich and flexible solution to build and manage data center virtualization and enterprise clouds. This page provides a summary of its key features**.

To learn more about the infrastructure platforms and services supported in each version of OpenNebula, please refer to the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes.md#uspng" %}}) for each version.

For high-level overviews and in-depth technical guides, please refer to OpenNebula’s [White Papers](https://opennebula.io/white-papers/).


## Platform Architecture and Management

### Centralized Control Plane

OpenNebula provides a unified and centralized control plane for the complete management, monitoring, and automation of virtual and cloud resources across the infrastructure.

* Graphical User Interface (GUI): Modern Sunstone GUI built on a responsive web framework for complete lifecycle management, monitoring, and accounting of all virtual infrastructure resources.
* Command-Line Interface (CLI): Powerful and scriptable command-line tools that mirror Unix-style commands for fast automation and administration.
* Application Programming Interface (API): REST, gRPC, and XML-RPC APIs offering seamless integration with third-party systems and applications for complete automation and orchestration.

### Federation and Scalability

OpenNebula ensures large-scale deployment and distributed cloud operations with a flexible, federated architecture designed for scalability and isolation.

* Disaggregated Architecture: Efficient management of highly distributed cloud and edge environments with Clusters across multiple sites or data centers.
* Instance Federation: Enables the federation of multiple OpenNebula control planes, allowing unified management across geographically distributed zones.
* Scalability: Proven scalability in production environments with over 2,500 hypervisor nodes managed within a single OpenNebula instance.

### Availability and Business Continuity

Built-in high-availability features ensure continuous service operation and data protection with minimal downtime.

* High Availability of Control Plane: Redundant front-end components with automatic failover for uninterrupted management services.
* High Availability of Hypervisor Nodes: Cluster-based failover mechanisms to automatically restart workloads on surviving hosts.
* Disaster Recovery Across Data Centers: Synchronous and asynchronous VM replication and recovery workflows to protect workloads across multiple sites.

### Hybrid and Edge Cloud

Automates the provisioning and lifecycle management of Clusters across private, public, and edge clouds.

* Dynamic Expansion: Automatically scales Clusters by extending private cloud capacity to public or edge environments.
* Multi-Cloud Federation: Enables seamless access and workload mobility across Clusters deployed in different clouds.
* Unified Management: Provides a single control plane for orchestrating compute, storage, and networking resources across hybrid and distributed infrastructures.

## Infrastructure and Virtualization Layer

### Virtualization

Supports multiple hypervisors and container technologies to match diverse workload needs.

* Processor Architectures: Certified compatibility with Intel and AMD x86 platforms, as well as ARM64-based processors, including Ampere and NVIDIA Grace, ensuring full flexibility across edge, data center, and AI infrastructure environments.
* Supported Operating Systems: Runs on major Linux distributions, including Red Hat Enterprise Linux, Ubuntu, Debian, and AlmaLinux, ensuring flexibility and ease of integration across enterprise environments.
* KVM Virtualization: Robust virtualization using Kernel-based Virtual Machine technology.
* Container Virtualization (LXC): Lightweight container-based virtualization for fast, efficient workloads.

### Enhanced Platform Awareness (EPA)

OpenNebula leverages Intel’s Enhanced Platform Awareness (EPA) framework to provide precise hardware-level optimization and secure, performance-aware orchestration of virtualized workloads.

* NUMA & CPU Pinning: Optimized workload placement through NUMA-aware scheduling, CPU pinning, and core isolation—ensuring deterministic performance and minimal latency for compute-intensive applications.
* PCI Passthrough & SR-IOV: Enables secure, high-performance access to GPUs, network interfaces, and accelerators with direct I/O and SR-IOV virtualization, supporting low-overhead multi-tenant environments.
* Memory and HugePages Management: Advanced memory allocation and hugepage configuration improve throughput and latency for virtual network functions (VNFs), AI inference, and HPC workloads. Native integration with Intel EPA for NFV, AI, and HPC workloads.

### Accelerated Computing

Native integration with NVIDIA technologies to deliver GPU and DPU-accelerated NFV, AI, and HPC workloads.

* GPU Support: Full compatibility with NVIDIA Hopper and Blackwell architectures.
* GPU Scheduling: Efficient sharing and allocation using vGPU and MIG.
* NVLink Integration: Optimized multi-GPU communication for high-performance AI training.
* Enhanced Networking: Support for Infiniband, Spectrum-X, and BlueField DPU fabrics.
* GPU Passthrough: Secure, high-performance GPU access for multi-tenant environments.
* DPU Integration (BF-3): Hardware offload for networking, security, and encryption tasks.
* GPU Telemetry: Real-time GPU monitoring via NVIDIA DCGM and gpu-tools.
* NVIDIA Infrastructure Controller Integration: Multi-tenant, AI Factory-scale bare-metal infrastructure management with NICo.
* Inference Applications: Pre-built apps optimized for fast inference, with native integration of vLLM and Hugging Face frameworks for efficient deployment of AI and LLM workloads.
* NVIDIA Ecosystem Integration: Seamless integration with the NVIDIA AI software stack, including platforms such as Run:ai and Dynamo, enabling unified orchestration, scheduling, and monitoring of AI workloads.

### Network

Comprehensive networking support, including software-defined networking (SDN), virtual, and physical appliances, supporting multiple backends for isolation and performance.

* Linux Bridge Networks: Simple, native networking for basic virtualization scenarios.
* 802.1Q VLANs: Tagged VLAN networks for tenant separation with support for QinQ.
* VXLAN Networks: Overlay networks for large-scale multi-tenant deployments using multicast or BGP EVPN.
* Open vSwitch-DPDK Acceleration: Native integration of Open vSwitch with DPDK enables high-throughput, low-latency packet processing with userspace networking, NUMA-aware PMD thread placement, hugepages optimization, and SR-IOV/vhost-user support for demanding NFV, AI, and HPC workloads.
* IP Leasing for VM Groups: Simplifies network management for multi-tier applications by assigning and managing IP leases consistently across related VM groups.

### Storage

Full support for both software-defined storage (SDS) and appliance-based storage solutions, covering environments ranging from local disks to enterprise-grade storage systems.

* Raw device mapping (RDM): Use the directly attached devices in the hypervisors in your VMS.
* NFS/NAS: Shared network storage with full image management support.
* Local storage with multi-tier caching: Cost-efficient, high-performance storage using local disks with support for image caching across Clusters and hypervisors in multi-cluster or hybrid configurations.
* Disaggregated and HCI Ceph: Scalable distributed storage with block and image replication.
* iSCSI and FC SAN Support: High-performance block storage through iSCSI and Fibre Channel using LVM with thin provisioning, with specific guides for NetApp, Everpure, and generic SAN appliances.
* NetApp: Optimized driver for NetApp All-Flash systems and ONTAP features.
* Everpure: FlashArray Support for native block storage lifecycle management.

### Backup

Integrated and third-party backup solutions ensure data protection and recovery.

* Built-in Backup: Native CBT (change block tracking) and snapshot-based backup with full, incremental, and differential options for all storage solutions (Section B.4).
* Veeam Integration: Seamless integration with Veeam for enterprise-grade incremental and full backup and restore, ensuring data protection, fast recovery, and compliance with corporate retention policies.

## Cloud and Workload Orchestration

### Cloud Provisioning Model

A self-service model enabling users to deploy and manage multi-tier applications easily.

* Self-Service Portal: A simple web portal allowing users to deploy virtual machines and services from a predefined catalog.
* Elastic Multi-VM Services: Auto-scaling of application components based on customizable elasticity rules.
* Application Insight: Real-time application metrics and state monitoring for informed scaling and resource decisions.

### Capacity and Performance Management

Advanced scheduling and resource optimization ensure efficient use of compute and storage resources.

* Live Migration: Seamless movement of running VMs between hosts for maintenance or load balancing.
* Enhanced VM Compatibility (EVC): Enables smooth VM migration across heterogeneous host hardware.
* Storage Live Migration: Seamless VM movement across LVM and file-based datastores.
* Dynamic Resource Scheduling (DRS): Cluster-wide automated & semi-automated load balancing, and generation of migration plans.
* AI-driven Predictive Scheduler: Multi-policy scheduling engine supporting priorities, affinity, and cost-aware placement.
* Affinity/Anti-Affinity Rules: Policy-driven placement of VMs to optimize locality or fault tolerance.
* Host Overcommitment: maximize Resource utilization and efficiency.

### Observability and Monitoring

Integrated telemetry and analytics tools for proactive monitoring and performance visibility.

* Built-in Monitoring: Native monitoring subsystem that provides real-time visibility into virtual machines, hosts, and services directly from the OpenNebula control plane—no external tools required.
* Predictive Monitoring: Built-in health and capacity forecasting to anticipate performance issues.
* External Integration: Export of metrics and events to Prometheus and Grafana for unified observability.

### Secure Multi-Tenancy

Comprehensive isolation, quota management, and access controls ensure secure multi-user environments.

* Application Sharing: Secure sharing of templates and applications across users, groups, and projects.
* Authentication Realms: Integration with LDAP, Active Directory, SAML, and other identity backends, enabling centralized access control with enforced two-factor authentication.
* Fine-Grained ACLs: Per-resource access permissions for complete control of user and group privileges.
* Quota Management: Enforces CPU, GPU, storage, and network usage limits per user or tenant to ensure fair resource allocation and policy compliance, including Cluster-level quotas and custom quota items for granular governance and control.
* Cluster and VDC: Logical partitioning of resources into isolated Clusters and Virtual Data Centers.
* Users & Groups: Logical grouping of users and projects for efficient policy administration.
* Network Isolation: VLANs and overlays ensure tenant traffic separation.

## Extensibility, Automation, and Hybrid Operations

### Kubernetes Platform

Enterprise-grade Kubernetes management and orchestration through built-in add-ons.

* OpenNebula Kubernetes Service (OneKS): Provides elastic Kubernetes-as-a-Service on OpenNebula, enabling users to create, access, operate, upgrade, recover, and deprovision Kubernetes clusters in a simple and repeatable way.
* Cluster API / CAPONE: Native support for Cluster API Provider for OpenNebula to automate Kubernetes infrastructure provisioning and lifecycle management.
* Cloud Provider Interface (CPI): Direct integration between Kubernetes and OpenNebula-managed compute, networking, and infrastructure resources.
* Container Storage Interface (CSI): Persistent volume provisioning from OpenNebula storage backends.
* Rancher Integration: Certified integration with SUSE Rancher Prime and RKE2, providing enterprise-grade multi-cluster lifecycle management and unified governance.


### Confidential Computing

Secure execution environments ensure data privacy and integrity during processing.

* Confidential Computing: Encrypted processing for protecting sensitive workloads in use.
* vTPM: Virtual Trusted Platform Module support for attestation and secure boot.
* Encrypted Storage: Native support for encrypted storage backends to safeguard data at rest and ensure compliance with enterprise security standards.
* Encrypted Memory: Native support for encrypted Virtual Machine memory. The hypervisor is not able to read the VM memory, guaranteeing runtime privacy.

### Automation

Comprehensive automation and orchestration capabilities ensure consistent, repeatable, and policy-driven operations across environments.

* Infrastructure as Code: Full support for automation frameworks such as Terraform for declarative infrastructure provisioning and lifecycle management.
* Configuration Management: Seamless integration with tools like Ansible for configuration control, post-deployment automation, and compliance enforcement.

### App Marketplaces

Distribute and reuse cloud-ready applications within and across organizations.

* Guest Operating Systems: Broad support for Windows and Linux guests, ensuring full compatibility for enterprise, development, and AI workloads across heterogeneous environments.
* Public Marketplace: Access to a broad catalog of pre-built templates for common operating systems, application stacks, and services, enabling rapid deployment and standardization across environments.
* Private Marketplace: Internal catalog for sharing and distributing certified applications.
* Third-Party Integration: Support for external marketplaces such as Linux Containers.

## Usability, Interoperability, and Migration

### Graphical User Interface

Modern, intuitive interface for both administrators and end users.

* Dynamic Tabs: Modular interface views for efficient navigation and operation.
* VM Console: Secure, browser-based remote access to virtual machines through integrated VN, RDP and SSH sessions.
* White Labeling: Customizable branding and visual identity for organizations.
* Self-Service Cloud View: Simplified interface for end users and developers.
* Group Admin View: Delegated administration for project or departmental management.
* Sunstone Labels: Tag-based organization and filtering of resources.

### Interfaces and Integration

Extensible and open architecture designed for seamless interoperability.

* Modular Architecture: Flexible design allowing custom extensions and third-party integrations.
* Hooking System: Event-driven hooks for workflow automation and external triggers.
* Rich API Set: Multi-language APIs for integration with third-party systems and applications for complete automation and orchestration.

### Migration from VMware

Comprehensive tools and workflows to enable a smooth transition from VMware environments to OpenNebula with minimal downtime and configuration effort.

* OneSwap: Streamlines virtual machine migration from VMware into OpenNebula with minimal reconfiguration and downtime.
* OVA Import: Enables direct import of OVA appliances and templates, simplifying workload onboarding and ensuring compatibility across virtualization environments.
* Minimal Disruption: Migration workflows designed to ensure business continuity, avoiding downtime and configuration drift.


{{< alert title="Important" type="info" >}}
\** *Because OpenNebula leverages the functionality exposed by the underlying platform services, its functionality and performance may be affected by the limitations imposed by those services.*

- *The list of features may change on different platform configurations*
- *Not all platform configurations exhibit similar performance and stability*
- *The features may change to offer users more features and integration with other virtualization and cloud components*
- *The features may change due to changes in the functionality provided by underlying virtualization services*
{{< /alert >}}
