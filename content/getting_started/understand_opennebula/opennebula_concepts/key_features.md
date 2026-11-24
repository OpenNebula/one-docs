---
title: "OpenNebula Key Features"
linkTitle: "Key Features"
date: "2025-02-17"
description:
categories: [Introduction, Overview]
pageintoc: "5"
tags: [Features]
type: docs
weight: "3"
---

OpenNebula offers a simple but feature-rich and flexible solution to build and manage data center virtualization, enterprise clouds, and AI infrastructure. This guide summarizes the capabilities available through OpenNebula {{< version >}} and its documented integrations.

To learn more about the infrastructure platforms and services supported in each version of OpenNebula, please refer to the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes.md" %}}) for each version.

For high-level overviews and in-depth technical guides, please refer to OpenNebula’s [White Papers](https://opennebula.io/white-papers/).


## Platform Architecture and Management

### Centralized Control Plane

OpenNebula provides a unified and centralized control plane for the management, monitoring, and automation of virtual, cloud, and supported bare-metal resources across the infrastructure.

* Graphical User Interface (GUI): Redesigned Sunstone GUI with clearer navigation, resource views, and side-drawer inspection for lifecycle management, monitoring, and accounting of virtual infrastructure resources.
* Command-Line Interface (CLI): Powerful and scriptable command-line tools that mirror Unix-style commands for fast automation and administration.
* Application Programming Interface (API): XML-RPC and gRPC APIs for core management, complemented by REST APIs for platform services such as OneFlow, OneForm, and OneKS, support integration, automation, and orchestration.

### Federation and Scalability

OpenNebula ensures large-scale deployment and distributed cloud operations with a flexible, federated architecture designed for scalability and isolation.

* Disaggregated Architecture: Efficient management of highly distributed cloud and edge environments with Clusters across multiple sites or data centers.
* Instance Federation: Enables the federation of multiple OpenNebula control planes, with shared users, groups, access policies, Virtual Data Centers, and application catalogs across geographically distributed zones.
* Scalability: Published single-zone controller API benchmarks cover 1,250 Hosts and 20,000 VMs. Deployment capacity depends on workload, hardware, API load, and configuration; federation supports expansion across multiple zones.

### Availability and Business Continuity

Built-in high-availability features ensure continuous service operation and data protection with minimal downtime.

* High Availability of Control Plane: Raft-based front-end redundancy with automatic leader election and failover, typically using three or five front-end servers.
* High Availability of Hypervisor Nodes: Cluster-based failover mechanisms to automatically restart workloads on surviving Hosts.
* Disaster Recovery Across Data Centers: Recovery architectures combine OpenNebula with storage replication or backup integrations and defined failover and failback procedures. Replication mode and recovery objectives depend on the selected storage or backup solution.

### Hybrid and Edge Cloud

OneForm automates the provisioning and lifecycle management of Clusters across private, public, and edge clouds.

* Dynamic Expansion: Adds and removes Cluster capacity through repeatable provisioning workflows using on-premises infrastructure or supported cloud and bare-metal providers.
* Multi-Cloud Federation: Enables consistent access policies and application catalogs across federated zones, with workload scheduling and lifecycle management performed locally in each zone.
* Unified Management: Provides a single control plane for orchestrating compute, storage, and networking resources across hybrid and distributed infrastructures.
* Resilient Provisioning: OneForm preserves Terraform and Ansible workflows across service restarts and supports recovery and cancellation of provisioning operations.

## Infrastructure and Virtualization Layer

### Virtualization

Supports multiple hypervisors and container technologies to match diverse workload needs.

* Processor Architectures: Supports Intel and AMD x86_64 platforms and supported ARM64 systems, including Ampere and NVIDIA Grace, with platform-specific hardware and virtualization requirements.
* Supported Operating Systems: Packages for major Linux distributions, including Red Hat Enterprise Linux, Ubuntu, Debian, AlmaLinux, Rocky Linux, SUSE Linux Enterprise, and openSUSE. Supported versions and component combinations are defined in the Platform Notes.
* KVM Virtualization: Robust virtualization using Kernel-based Virtual Machine technology.
* Container Virtualization (LXC): Lightweight container-based virtualization for fast, efficient workloads.

### Enhanced Platform Awareness (EPA)

OpenNebula uses Enhanced Platform Awareness capabilities, including NUMA topology, CPU pinning, HugePages, and direct device access, to optimize performance-sensitive virtualized workloads.

* NUMA & CPU Pinning: Optimized workload placement through NUMA-aware scheduling, CPU pinning, and core isolation — ensuring deterministic performance and minimal latency for compute-intensive applications.
* PCI Passthrough & SR-IOV: Enables secure, high-performance access to GPUs, network interfaces, and accelerators with direct I/O and SR-IOV virtualization, supporting low-overhead multi-tenant environments.
* Memory and HugePages Management: Advanced memory allocation and hugepage configuration improve throughput and latency for virtual network functions (VNFs), AI inference, and HPC workloads.

### Accelerated Computing

Integration with GPU and accelerator technologies for NFV, AI, and HPC workloads, including NVIDIA, AMD, and Axelera.

* GPU and Accelerator Support: NVIDIA Hopper and Blackwell platforms, AMD Instinct GPU passthrough with ROCm in the guest, and Axelera Metis accelerators. Available capabilities depend on the device and software stack.
* GPU Scheduling: Discovery and allocation of NVIDIA vGPU profiles, including MIG-backed vGPU profiles, alongside full GPU passthrough. Available profiles depend on supported hardware, drivers, and NVIDIA licensing.
* NVLink and NVSwitch Integration: Supports multi-GPU communication and NVIDIA Fabric Manager integration for supported AI training configurations.
* Enhanced Networking: Support for InfiniBand, Spectrum-X, and BlueField DPU fabrics in supported infrastructure configurations.
* GPU Passthrough: Secure, high-performance GPU access for multi-tenant environments.
* DPU Integration: Support for NVIDIA BlueField networking and hardware offload in supported infrastructure configurations.
* GPU Telemetry: Monitoring through NVIDIA DCGM and GPU tools, with available GPU utilization, memory-bandwidth utilization, and power metrics displayed in the Sunstone VM PCI tab.
* Bare Metal as a Service: Integrates with NVIDIA Infra Controller (NICo) to provision, monitor, and delete bare-metal instances through OpenNebula templates, users, groups, and quotas.
* Inference Applications: Pre-built apps optimized for fast inference, with native integration of vLLM and Hugging Face frameworks for efficient deployment of AI and LLM workloads.
* NVIDIA Ecosystem Integration: Deployment integrations for Run:ai and AI software such as Dynamo on OpenNebula-managed Kubernetes infrastructure, including Run:ai and NVIDIA GPU Operator applications in the OneKS catalog.

### Network

Comprehensive networking support, including software-defined networking (SDN), virtual, and physical appliances, supporting multiple backends for isolation and performance.

* Linux Bridge Networks: Simple, native networking for basic virtualization scenarios.
* 802.1Q VLANs: Tagged VLAN networks for tenant separation with support for QinQ.
* VXLAN Networks: Overlay networks for large-scale multi-tenant deployments using multicast or BGP EVPN.
* Open vSwitch-DPDK Acceleration: Userspace networking for KVM workloads using DPDK, vhost-user interfaces, HugePages, and NUMA-aware CPU placement for high-throughput, low-latency packet processing.
* SR-IOV Switchdev Networking: Open vSwitch integration for SR-IOV interfaces, including automatic bridge and VF representor management, PF/VF monitoring, and selection of VFs by parent physical function.
* Port Mirroring: RSPAN, GRE, and ERSPAN II/III traffic mirroring for Open vSwitch networks, with traffic-direction and source-VLAN filters, managed through Sunstone, CLI, or API.
* Tenant Network Self-Provisioning: Group-level VLAN rules let administrators delegate VLAN ranges and enable controlled tenant creation of Virtual Networks.
* IP Address Management: Allocates IP and MAC leases from Virtual Network address ranges, with reservations, round-robin lease assignment, and an optional global MAC address space.

### Storage

Full support for both software-defined storage (SDS) and appliance-based storage solutions, covering environments ranging from local disks to enterprise-grade storage systems.

* Raw Device Mapping (RDM): Makes directly attached Host devices available to Virtual Machines.
* NFS/NAS: Shared network storage with full image management support.
* Local storage with multi-tier caching: Cost-efficient, high-performance storage using local disks with support for image caching across Clusters and hypervisors in multi-cluster or hybrid configurations.
* Disaggregated and HCI Ceph: Scalable distributed storage with block and image replication.
* iSCSI and FC SAN Support: High-performance block storage through iSCSI and Fibre Channel using LVM with thin provisioning, with specific guides for NetApp, Everpure, and generic SAN appliances.
* NetApp: Optimized driver for NetApp All-Flash systems and ONTAP features.
* Everpure: FlashArray support for native block storage lifecycle management.
* Filesystem as a Service: VirtioFS-based shared filesystems can be created and attached to compatible VMs, with filesystem-image management available in Sunstone.

### Backup

Integrated and third-party backup solutions ensure data protection and recovery.

* Built-in Backup: Full and incremental VM backups using supported CBT (Changed Block Tracking) or snapshot modes, with scheduled Backup Jobs and selected-disk protection. Available backup modes depend on the source datastore.
* Backup Repositories: Restic and Rsync backup datastores, including S3 and S3-compatible object storage with Restic. Backup Jobs provide scheduling and retention controls.
* OpenNebula Backup Exporter (OneBEX): Exposes full and CBT incremental disk data to interactive third-party backup integrations. Version {{< version >}} adds Ceph RBD support and improves transfer handling.
* Veeam Integration: Agentless image-level backup and restore through an oVirt-compatible API and OneBEX. In {{< version >}}, full and CBT incremental backup support covers qcow2, LVM, and Ceph RBD disks; Veeam stores the backups in its repositories.

## Cloud and Workload Orchestration

### Cloud Provisioning Model

A self-service model enabling users to deploy and manage multi-tier applications easily.

* Self-Service Portal: A simple web portal allowing users to deploy Virtual Machines and services from a predefined catalog.
* Elastic Multi-VM Services: Auto-scaling of application components based on customizable elasticity rules.
* Application Insight: Real-time application metrics and state monitoring for informed scaling and resource decisions.

### Capacity and Performance Management

Advanced scheduling and resource optimization ensure efficient use of compute and storage resources.

* Live Migration: Moves running VMs between compatible Hosts for maintenance or load balancing, subject to the VM, CPU, device, and storage configuration.
* Enhanced VM Compatibility (EVC): Uses compatible CPU models to support migration across Hosts with compatible processor features; it does not remove cross-architecture or device restrictions.
* Storage Live Migration: Moves VM storage between supported LVM and file-based datastores. In {{< version >}}, LVM and thin-LVM migration pauses the guest during memory transfer and storage handover.
* Distributed Resource Scheduler (OneDRS): Generates and executes Cluster-level optimization plans with manual, partially automated, or fully automated migration workflows, including Host and datastore balancing.
* Predictive Optimization: Combines monitored and forecast resource usage to optimize Cluster workload distribution and generate proactive migration recommendations.
* Storage Balancing: OneDRS considers datastore space utilization alongside other resource objectives. Storage migrations are enabled explicitly and remain subject to datastore and VM compatibility.
* Affinity/Anti-Affinity Rules: Policy-driven placement of VMs to optimize locality or fault tolerance.
* Host Overcommitment: Configurable CPU and memory overcommitment to improve resource utilization and efficiency.

### Observability and Monitoring

Integrated telemetry and analytics tools for proactive monitoring and performance visibility.

* Built-in Monitoring: Native monitoring subsystem that provides real-time visibility into Virtual Machines, Hosts, and services directly from the OpenNebula control plane—no external tools required.
* Resource Usage Forecasts: Predicts resource consumption to support capacity planning and predictive OneDRS optimization.
* External Integration: Export of metrics and events to Prometheus and Grafana for unified observability.

### Secure Multi-Tenancy

Comprehensive isolation, quota management, and access controls ensure secure multi-user environments.

* Application Sharing: Secure sharing of templates and applications across users, groups, and projects.
* Authentication Realms: Integration with LDAP, Active Directory, SAML, and other identity backends, enabling centralized access control with configurable enforcement of two-factor authentication in Sunstone.
* Fine-Grained ACLs: Per-resource access permissions for complete control of user and group privileges.
* Quota Management: Enforces CPU, GPU, storage, and network usage limits per user or tenant to ensure fair resource allocation and policy compliance, including Cluster-level quotas and custom quota items for granular governance and control.
* Cluster and VDC: Logical partitioning of resources into isolated Clusters and Virtual Data Centers.
* Users & Groups: Logical grouping of users and projects for efficient policy administration.
* Network Isolation: VLANs and overlays ensure tenant traffic separation.

## Extensibility, Automation, and Hybrid Operations

### Kubernetes Platform

Integrated Kubernetes management and orchestration through OneKS and the OpenNebula Kubernetes ecosystem.

* OpenNebula Kubernetes Service (OneKS): Provides elastic Kubernetes-as-a-Service on OpenNebula, enabling users to create, access, scale, upgrade, recover, and deprovision Kubernetes clusters and node groups through Sunstone, CLI, and API.
* Cluster API / CAPONE: Native support for Cluster API Provider for OpenNebula to automate Kubernetes infrastructure provisioning and lifecycle management.
* Cloud Provider Interface (CPI): Direct integration between Kubernetes and OpenNebula-managed compute, networking, and infrastructure resources.
* Container Storage Interface (CSI): Persistent volume provisioning from OpenNebula storage backends.
* Rancher Integration: Integration with SUSE Rancher Prime and RKE2 for multi-cluster lifecycle management and governance, with support coverage defined by the selected integration or embedded subscription.
* OneKS Deployment Options: Select the target OpenNebula Cluster and networks, run pre-deployment diagnostics, and use supported ARM64 or air-gapped deployment configurations.
* OneKS Application Catalog: Deploy and manage validated Helm-based applications through Sunstone or the CLI, with lifecycle monitoring. Catalog entries include KServe, NVIDIA GPU Operator, Prometheus, and NVIDIA Run:ai.

### Slurm and HPC Services

* OneSlurm: Deploy Slurm clusters as OneFlow services, with scalable worker VMs, NVIDIA GPU access, LDAP identity integration, NFS shared storage, and InfiniBand connectivity.
* Open OnDemand: A dedicated appliance provides a web portal for accessing OneSlurm environments.

### Confidential Computing

Hardware-assisted security and encryption capabilities help protect sensitive workloads and data.

* Confidential Computing: Supports hardware-assisted memory protection for compatible KVM workloads, subject to the selected CPU, firmware, and virtualization configuration.
* vTPM: Virtual Trusted Platform Module support for KVM VMs, with TPM state preserved through supported migration and backup workflows.
* Encrypted Storage: Supports encrypted VM disks and storage backends where available in the selected datastore and key-management configuration.
* Encrypted Memory: AMD SEV and SEV-ES support on compatible KVM Hosts protects VM memory in use, with Host selection based on the requested encryption mode.


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

Redesigned interface for administrators and end users, with clearer navigation, updated forms, richer resource views, and side-drawer inspection.

* Dynamic Tabs: Modular interface views for efficient navigation and operation.
* VM Console: Secure, browser-based remote access through VNC, RDP, and SSH, with SPICE console support for KVM VMs added in {{< version >}}.
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

* OneSwap: Streamlines migration from VMware with batch conversion, Windows OS profiles, and delta synchronization to reduce cutover downtime. Version {{< version >}} adds VDDK transport for delta migrations, excluding vSAN-backed VMs, plus machine-type and CPU-feature options.
* OVA Import: Enables import of supported OVA appliances and templates to simplify workload onboarding, subject to guest and virtual hardware compatibility.
* Controlled Cutover: Migration workflows reduce disruption through preparation, automated conversion, and delta synchronization, followed by planned cutover and validation of migrated workloads.


{{< alert title="Platform and Support Scope" type="info" >}}
*Because OpenNebula uses capabilities exposed by the underlying platform services, functionality and performance depend on those services and the selected configuration. Supported combinations are defined in the [Platform Notes]({{% relref "software/release_information/release_notes/platform_notes/" %}}); enterprise maintenance and specialized integration support follow the applicable subscription.*

- *The list of features may change on different platform configurations*
- *Not all platform configurations exhibit similar performance and stability*
- *The features may change to offer users more features and integration with other virtualization and cloud components*
- *The features may change due to changes in the functionality provided by underlying virtualization services*
{{< /alert >}}
