---
title: "What's New"
date: "2026-07-24"
description:
categories:
pageintoc: "244"
tags:
weight: "1"
---

<a id="whats-new"></a>

This page will contain the list of new features in OpenNebula 7.6.0.

## OpenNebula Core

- Restricted-attribute configuration can now [protect a complete vector attribute]({{% relref "oned#oned-conf-restricted-attributes-configuration" %}}), such as `DISK`, `NIC`, or `PCI`, without listing each attribute within the vector separately.

## API and CLI

- New parameter `--keep-ha` for CLI command `onezone serversync`, which keeps local [RAFT configuration]({{% relref "frontend_ha.md#server-sync-ha" %}}). Usefull for asymmetric HA deployments.

## OpenNebula Form

* Improved control of Provision lifecycle actions. OneForm now tracks Terraform and Ansible executions across service restarts, enables recovery of interrupted operations, and allows users to [cancel an active Provision operation]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations.md#cancelling-an-active-operation" %}}).

## Features Backported to 7.4.x

Additionally, the following functionalities are present that were not in OpenNebula 7.4.0, although they debuted in subsequent maintenance releases of the 7.4.x series:

- Log HA hearbeat and replication messages at log level 5
- Option to configure network lease policy for internal Address Ranges. The policy can be set globally in [oned.conf]({{% relref "oned#virtual-networks" %}}) or [overridden for each Virtual Network]({{% relref "manage_vnets#lease-allocation-policy" %}}).

## Other Issues Solved

* Fix `oneprovision logs` not showing existing log entries by default before streaming new output [#7558](https://github.com/OpenNebula/one/issues/7558).
* Fix `oneform sync` leaving stale resources and symbolic links when a driver is removed [#7591](https://github.com/OpenNebula/one/issues/7591).
* Fix OneForm provisioning with the Community Edition repository instead of the Enterprise Edition repository [#7728](https://github.com/OpenNebula/one/issues/7728).
* Migrate OneForm to the OpenNebula Document Server (ODS) framework to standardize its internal models, client, error handling, and API patterns [#7579](https://github.com/OpenNebula/one/issues/7579).
