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

The OpenNebula team is excited to announce the availability of the **OpenNebula 7.4**!


## OpenNebula Core

## Storage & Backups

* Added [interactive backup integration support]({{% relref "../../../product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}), enabling third-party backup integrations to pull full and CBT incremental `qcow2` VM backups directly from KVM hypervisors through the OpenNebula Backup Exporter (OneBEX).
* Added [selected disk backups]({{% relref "../../../product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks" %}}), allowing VM backup configurations and Backup Jobs to back up only a defined subset of eligible VM disks. Selected-disk backups can be restored as [individual disks]({{% relref "../../../product/virtual_machines_operation/virtual_machine_backups/operations#vm-backups-selected-disks-restore" %}}).

## Networking

## Sunstone

* Added FSaaS (virtiofs) support in Sunstone, allowing users to manage shared storage file systems, create filesystem images, and attach disks directly from the GUI.

## API and CLI

* **Dynamic VM Group Management**: New CLI commands `onevm vmgroup-add` and `onevm vmgroup-del` allow adding or removing VMs from a [VM Group]({{% relref "affinity.md#dynamic-vmg" %}}) dynamically.
* **OneGate Sinatra Configuration**: OneGate now exposes the Sinatra server configuration through the `:server` section in `onegate-server.conf`, allowing administrators to customize supported Sinatra settings such as Host authorization.

## KVM

* Enable filtering by OS ID/type/version/architecture in [QEMU Guest Agent Monitoring](/product/operation_references/hypervisor_configuration/kvm_driver/#qemu-guest-agent-monitoring).
* Added support for [dummy interfaces]({{% relref "vm_templates#network-interfaces--alias" %}}), allowing KVM VMs to use guest NICs that are not attached to any OpenNebula Virtual Network.
* Gather network information using qemu-guest-agent when [QEMU Guest Agent Monitoring](/product/operation_references/hypervisor_configuration/kvm_driver/#qemu-guest-agent-monitoring) is enabled

## LXC

## OpenNebula Form

## OpenNebula Elastic Kubernetes Service

* Added multi-cluster deployment support in OneKS, allowing users to select the target OpenNebula cluster and deployment networks when creating Kubernetes Clusters.

## Packaging

## OpenNebula Distributed Resource Scheduler

* [OneDRS]({{% relref "product/cloud_system_administration/scheduler/drs#scheduler-drs" %}}) can now skip automatic migration for VMs whose user template sets `ONEDRS_BLOCKED` to `YES`.

## Features Backported to 7.2.x

Additionally, the following functionalities are present that were not in OpenNebula 7.2.0, although they debuted in subsequent maintenance releases of the 7.2.x series:

* [Allow the customization of the favicon in FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#branding-fireedge" %}}).

## Other Issues Solved

* [Fix marketplace broken redirect link](https://github.com/OpenNebula/one/issues/7291).
* [Fix Improve live migration options for busy guests](https://github.com/OpenNebula/one/issues/5774).
* [Fix Units in "Size on instantiate" VM Template instantiation](https://github.com/OpenNebula/one/issues/7672).
* [Fix VM log is not showing up in the FireEdge if USE_VMS_LOCATION=YES](https://github.com/OpenNebula/one/issues/7680).
* [Fix VM CDROM hot-attach without target or dev-prefix](https://github.com/OpenNebula/one/issues/7736).
* [Fix API commands executed on HA follower, for full list of commands the GitHub issue](https://github.com/OpenNebula/one/issues/7725).
* [Fix VirtioFS filesystem image size reporting always `0`](https://github.com/OpenNebula/one/issues/7751).
* [Fix onehost failing on CLI-only installs due to an unconditional require of HostSyncManager](https://github.com/OpenNebula/one/issues/7768).
