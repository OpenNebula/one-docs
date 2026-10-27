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

- [Port Mirroring]({{% relref "port_mirroring" %}}) on Open vSwitch networks supports SPAN, RSPAN, GRE, and ERSPAN destinations, source NIC selection, VLAN filtering, and live updates through dedicated API and CLI operations.
- Restricted-attribute configuration can now [protect a complete vector attribute]({{% relref "oned#oned-conf-restricted-attributes-configuration" %}}), such as `DISK`, `NIC`, or `PCI`, without listing each attribute within the vector separately.

## Sunstone
- Redesigned multi-step creation forms with a responsive layout, adaptive step navigation, and a dedicated creation header with progress and cancellation controls [#8038](https://github.com/OpenNebula/one/issues/8038).

## API and CLI
- New parameter `--keep-ha` for CLI command `onezone serversync`, which keeps local [RAFT configuration]({{% relref "frontend_ha.md#server-sync-ha" %}}). Usefull for asymmetric HA deployments.

## OpenNebula Form

* Improved control of Provision lifecycle actions. OneForm now tracks Terraform and Ansible executions across service restarts, enables recovery of interrupted operations, and allows users to [cancel an active Provision operation]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations.md#cancelling-an-active-operation" %}}).

## Features Backported to 7.4.x

Additionally, the following functionalities are present that were not in OpenNebula 7.4.0, although they debuted in subsequent maintenance releases of the 7.4.x series:

- Log HA hearbeat and replication messages at log level 5
- Option to configure network lease policy for internal Address Ranges. The policy can be set globally in [oned.conf]({{% relref "oned#virtual-networks" %}}) or [overridden for each Virtual Network]({{% relref "manage_vnets#lease-allocation-policy" %}}).
- Added a dedicated [FINISH frame to gracefully finalize interactive restore transfers]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}), eliminating the need to manually terminate the OneBEX writer process
- OpenNebula packages for [SUSE Linux Enterprise Server 16]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ce/#suse" %}}), which replaces SUSE Linux Enterprise Server 15 as a supported platform (see [Platform Notes]({{% relref "platform_notes" %}})).
- Add a dedicated [FINISH frame to gracefully finalize interactive restore transfers]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}), eliminating the need to manually terminate the OneBEX writer process.

- Add the OneSwap [`--machine` and `--cpu-features`]({{% relref "software/migration_from_vmware/oneswap.md#customizing-the-created-vm-template" %}}) options to set the KVM machine type and CPU model features per migration profile, allowing migration projects to use their own target hardware settings. This feature was backported to 7.4.2; `--cpu-features` requires `--cpu-model` [#8112](https://github.com/OpenNebula/one/issues/8112).

* Add [SR-IOV PF/VF relationship monitoring]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts.md#host-pci-devices" %}}) and [VF selection by parent PF]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#selecting-virtual-functions-by-physical-function" %}}) through `PF_IFNAME` or `PF_ADDRESS`. Select the same PF to keep VFs together (affinity), or different PFs to spread them (anti-affinity). This feature was backported to 7.4.2. Monitoring also reports passthrough eligibility and the network PF e-switch mode when available [#7671](https://github.com/OpenNebula/one/issues/7671), [#7619](https://github.com/OpenNebula/one/issues/7619).

## Other Issues Solved

List of new issues solved in OpenNebula 7.6.
* Fix groupadmin vm configuration file [#7766](https://github.com/OpenNebula/one/issues/7766).
* Fix Host monitoring and driver failures caused by inconsistent remote script paths and cleanup of `/var/tmp/one` [#7899](https://github.com/OpenNebula/one/issues/7899).
