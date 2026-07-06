---
title: "What's New"
date: "2025-10-06"
description:
categories:
pageintoc: "244"
tags:
weight: "1"
---

<a id="whats-new"></a>

The OpenNebula team is excited to announce the availability of OpenNebula 7.4. This release introduces a broad set of usability, automation, and operational improvements across the platform, led by a redesigned Sunstone interface that makes day-to-day cloud management more modern and intuitive.

OpenNebula 7.4 also delivers important enhancements for operating virtualized infrastructure at scale, including OneSwap batch VMware migrations, improved OneDRS datastore selection, dynamic VM group management through the CLI, bulk operations for service VMs, Ubuntu 26.04 support, expanded backup capabilities with OneBEX, new VLAN group-level authorization policies, support for SR-IOV-capable PCI network interfaces in Switchdev mode with Open vSwitch, an enhanced Slurm appliance with out-of-the-box NVIDIA GPU support and LDAP identity integration, and a wide range of fixes and improvements across HA, networking, storage, monitoring, and vCenter compatibility.

Together with this release, OpenNebula also introduces new extension capabilities for advanced infrastructure use cases, including automated AI Factory-scale Bare Metal as a Service with NVIDIA NICo and enhanced Kubernetes provisioning and pre-deployment diagnostics with OneKS. These extensions further expand OpenNebula’s role as a flexible, production-ready platform for private cloud, edge, HPC, and sovereign AI infrastructure.

Key highlights of this release include:

* Redesigned Sunstone interface, delivering a modern, highly intuitive user experience for cloud administrators.
* Optimized enterprise workload management with OneSwap batch VMware migrations, dynamic VM group management via the CLI, and bulk deletion of scheduled actions from all service VMs.
* Removed Veeam integration storage requirements using expanded backup capabilities via the OpenNebula Backup Exporter (OneBEX), allowing third-party tools to interactively pull full incremental changes on virtual disks — qcow2 and LVM based disks are supported in this first release.
* Enhanced Slurm appliance simplifies the creation of Slurm Clusters for AI and HPC workloads with out-of-the-box NVIDIA GPU support and LDAP identity integration.
* Improved OneDRS datastore selection during VM migrations, helping identify optimal datastores based on space and usage requirements.
* New VLAN group-level authorization policies, allowing cloud administrators to delegate VLAN management to tenants and enable Virtual Network self-provisioning in multi-tenant environments. 
* Support for SR-IOV-capable PCI network interfaces in Switchdev mode with Open vSwitch.
* Updated OS compatibility with production-ready packages fully supporting Ubuntu 26.04 (Resolute Raccoon).
* Multiple fixes and stability improvements across the platform, and much more!...

The Enterprise Subscription also includes advanced extensions designed for enterprise cloud and AI Factory deployments, including:

* Enhanced Kubernetes management with multi-cluster deployment configuration options and pre-deployment diagnostics to validate cluster readiness and avoid time-consuming provisioning failures.
* Native integration with the NVIDIA Infrastructure Controller (NICo) to deliver automated Bare Metal as a Service (BMaaS) and AI Factory-scale provisioning and orchestration of accelerated infrastructure.

Thank you to our incredible community and partners for your continued support in building the future of open-source cloud orchestration!

## OpenNebula Core

* Added the capacity to [batch delete scheduled actions from all service VMs]({{% relref "product/virtual_machines_operation/multi-vm_workflows/appflow_use_cli/#deleting-scheduled-actions-from-service-vms" %}}), negating the need to delete actions from each individual VM.

## Storage & Backups

* Added [interactive backup integration support]({{% relref "../../../product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}), enabling third-party backup integrations to pull full and CBT incremental `qcow2` VM backups directly from KVM hypervisors through the OpenNebula Backup Exporter (OneBEX).
* Added [selected disk backups]({{% relref "../../../product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks" %}}), allowing VM backup configurations and Backup Jobs to back up only a defined subset of eligible VM disks. Selected-disk backups can be restored as [individual disks]({{% relref "../../../product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks-restore" %}}).

## AI Factories

* Integration of the NVIDIA Infra Controller (NICo) delivers automated AI Factory-scale provisioning of accelerated bare-metal hardware, with full lifecycle management including hardware discovery, firmware validation, DPU provisioning, and multi-tenant operation.

## Sunstone

* Complete redesign of interface, improving useability.
* Added FSaaS (VirtioFS) support in Sunstone, allowing users to manage shared storage file systems, create filesystem images, and attach disks directly from the GUI.

## API and CLI

* New CLI commands `onevm vmgroup-add` and `onevm vmgroup-del` enable dynamic VM Group management, with the capacity to add or remove VMs from a [VM Group]({{% relref "affinity.md#dynamic-vmg" %}}) dynamically.
* OneGate now exposes the Sinatra server configuration through the `:server` section in `onegate-server.conf`, allowing administrators to customize supported Sinatra settings such as Host authorization.

## KVM

* Enable filtering by OS ID/type/version/architecture in [QEMU Guest Agent Monitoring](/product/operation_references/hypervisor_configuration/kvm_driver/#qemu-guest-agent-monitoring).
* Added support for [dummy interfaces]({{% relref "vm_templates#network-interfaces--alias" %}}), allowing KVM VMs to use guest NICs that are not attached to any OpenNebula Virtual Network.
* Gather network information using qemu-guest-agent when [QEMU Guest Agent Monitoring](/product/operation_references/hypervisor_configuration/kvm_driver/#qemu-guest-agent-monitoring) is enabled.

## OpenNebula Elastic Kubernetes Service

* Added multi-cluster deployment support in OneKS, allowing users to select the target OpenNebula Cluster and deployment networks when creating Kubernetes Clusters.
* Added [pre-deployment diagnostics for OneKS provisioning]({{% relref "platform_services/oneks/management/configuration/#readiness-check-configuration" %}}), enabling users to validate the readiness a deployment placement option prior to deployment to avoid time-consuming provisioning failures. 

## Networking

* VLAN Groups enable cloud administrators fo delegate VLAN management to tenants in multi-tenant clouds, allowing tenant self-provisioning of Virtual Networks.
* Support for [SR-IOV capable PCI network interfaces in Switchdev mode]({{% relref "product/cluster_configuration/hosts_and_clusters/pci_passthrough/#usage-as-network-interfaces" %}}) with Open vSwitch.  

## Packaging

* Added OpenNebula packages for for Ubuntu 26.04 (Resolute Raccoon).

## OneSwap

* Added Windows OS Profile/Best practices VM template options to oneswap Windows conversion.
* OneSwap batch VM conversion enables the migration of multiple VMs in a single execution 
## AI Factories

Integration of the [NVIDIA Infra Controller (NICo)]({{% relref "product/virtual_machines_operation/metal_instances/bare_metal_nico/" %}}) introduces Bare Metal as a Service to OpenNebula, streamlining the lifecycle management of bare-metal instances within multi-tenant, AI Factory-scale infrastructures.
## OpenNebula Distributed Resource Scheduler

* [OneDRS]({{% relref "product/cloud_system_administration/scheduler/drs#scheduler-drs" %}}) can now skip automatic migration for VMs whose user template sets `ONEDRS_BLOCKED` to `YES`.

## Features Backported to 7.2.x

Additionally, the following functionalities are present that were not in OpenNebula 7.2.0, although they debuted in subsequent maintenance releases of the 7.2.x series:

* [Allow the customization of the favicon in FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#branding-fireedge" %}}).
* Added the capacity to [batch delete scheduled actions from all service VMs]({{% relref "product/virtual_machines_operation/multi-vm_workflows/appflow_use_cli/#deleting-scheduled-actions-from-service-vms" %}}), negating the need to delete actions from each individual VM.

## Other Issues Solved

* Fix marketplace broken redirect link [#7291](https://github.com/OpenNebula/one/issues/7291).
* Fix improve live migration options for busy guests [#5774](https://github.com/OpenNebula/one/issues/5774).
* Fix missing units in "Size on instantiate" VM Template instantiation [#7672](https://github.com/OpenNebula/one/issues/7672).
* Fix VM log is not showing up in the FireEdge if `USE_VMS_LOCATION=YES` [#7680](https://github.com/OpenNebula/one/issues/7680).
* Fix VM CDROM hot-attach without target or dev-prefix [#7736](https://github.com/OpenNebula/one/issues/7736).
* Fix API commands executed on HA follower, for full list of commands the GitHub issue [#7725](https://github.com/OpenNebula/one/issues/7725).
* Fix onehost failing on CLI-only installs due to an unconditional require of HostSyncManager [#7768](https://github.com/OpenNebula/one/issues/7768).
* Fix AutoNFS bug where `NFX_AUTO_*` attributes are not correctly read, preventing the automatic mount [#7763](https://github.com/OpenNebula/one/issues/7763)
* Fix OneDRS placement failure for LVM SAN EE datastore with `KeyError` on Image DS ID [#7752](https://github.com/OpenNebula/one/issues/7752)
* Fix incorrect reporting of sizes for VirtioFS images [#7751](https://github.com/OpenNebula/one/issues/7751)
* Fix OneKS Clusters stuck in DEPROVISIONING state if a OneKS group becomes empty during the deprovisioning process [#7749](https://github.com/OpenNebula/one/issues/7749)
* Fix unrecoverable WARNING state of OneKS groups after recovery of OneKS Cluster [#7748](https://github.com/OpenNebula/one/issues/7748)
* Fix OneKS lifecycle operations after renaming a cluster by using stable Kubernetes identifiers [#7724](https://github.com/OpenNebula/one/issues/7724).
* Fix oneswap compatibility issue with vCenter 8.0.3 [#7698](https://github.com/OpenNebula/one/issues/7698).
* Fix `opennebula-exporter` crash when monitoring diskless VMs [#7703](https://github.com/OpenNebula/one/issues/7703).
* Fix PCI attach to prevent bus address collisions [#7695](https://github.com/OpenNebula/one/issues/7695).
* Fix lack of VLAN tags clearance in OVS when removing them from virtual network [#7707](https://github.com/OpenNebula/one/issues/7707)
* Fix LVM (EE) post-reboot activation silently skipping VM disks [#7720](https://github.com/OpenNebula/one/issues/7720).
* Fix OVS port QinQ vlan mode being overwritten with changes introduced in[#7657](https://github.com/OpenNebula/one/issues/7657).
* Fix MAC address range parsing for invalid MAD address ranges [#7233](https://github.com/OpenNebula/one/issues/7233).
* Fix file-based image cloning between two datastores with BRIDGE_LIST [#7762](https://github.com/OpenNebula/one/issues/7762).
* Fix AutoNFS not working correctly when used on System Datastores of type `shared` [#7763](https://github.com/OpenNebula/one/issues/7763).
* Fix LVM concurrency issue with parallel deployments from different hosts using the same VG [#7719](https://github.com/OpenNebula/one/issues/7719).
* Fix various logrotate issues [#7646](https://github.com/OpenNebula/one/issues/7646).
