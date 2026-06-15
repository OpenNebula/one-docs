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

## Networking

## Sunstone

* Added FSaaS (virtiofs) support in Sunstone, allowing users to manage shared storage file systems, create filesystem images, and attach disks directly from the GUI.

## API and CLI

* **Dynamic VM Group Management**: New CLI commands `onevm vmgroup-add` and `onevm vmgroup-del` allow adding or removing VMs from a [VM Group]({{% relref "affinity.md#dynamic-vmg" %}}) dynamically.

## KVM

* Enable filtering by OS ID/type/version/architecture in [QEMU Guest Agent Monitoring](/product/operation_references/hypervisor_configuration/kvm_driver/#qemu-guest-agent-monitoring).
* Added support for [dummy interfaces]({{% relref "vm_templates#network-interfaces--alias" %}}), allowing KVM VMs to use guest NICs that are not attached to any OpenNebula Virtual Network.

## LXC

## OpenNebula Form

## Packaging

## Features Backported to 7.2.x

Additionally, the following functionalities are present that were not in OpenNebula 7.2.0, although they debuted in subsequent maintenance releases of the 7.2.x series:

* [Allow the customization of the favicon in FireEdge]({{% relref "product/operation_references/opennebula_services_configuration/fireedge.md#branding-fireedge" %}}).

## Other Issues Solved

* [Fix marketplace broken redirect link](https://github.com/OpenNebula/one/issues/7291).
* [Fix Improve live migration options for busy guests](https://github.com/OpenNebula/one/issues/5774).
* [Fix Units in "Size on instantiate" VM Template instantiation](https://github.com/OpenNebula/one/issues/7672).
* [Fix VM log is not showing up in the FireEdge if USE_VMS_LOCATION=YES](https://github.com/OpenNebula/one/issues/7680).
* [Fix API commands executed on HA follower, for full list of commands the GitHub issue](https://github.com/OpenNebula/one/issues/7725).
