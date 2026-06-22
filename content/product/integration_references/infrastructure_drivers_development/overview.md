---
title: "Overview"
date: "2025-02-17"
description:
categories:
pageintoc: "291"
tags:
weight: "1"
---

<a id="intro-integration"></a>

<!--# Overview -->

The interactions between OpenNebula and the Cloud infrastructure are performed by specific drivers. Each one addresses a particular area:

- **Storage**. The OpenNebula core issue abstracts storage operations (e.g., clone or delete) that are implemented by specific programs that can be replaced or modified to interface special storage backends and file-systems.
- **Virtualization**. The interaction with the hypervisors are also implemented with custom programs to boot, stop, or migrate a Virtual Machine. This allows you to specialize each VM operation so as to perform custom operations.
- **Monitoring**. Monitoring information is also gathered by external probes. You can add additional probes to include custom monitoring metrics that can later be used to allocate Virtual Machines or for accounting purposes.
- **Authentication**. OpenNebula can be also configured to use an external program to authorize and authenticate user requests. In this way, you can implement any access policy to Cloud resources.
- **Networking**. The hypervisor is also prepared with the network configuration for each Virtual Machine.

Use the driver interfaces if you need OpenNebula to interface any specific storage, virtualization, monitoring, or authorization system already deployed in your data center, or to tune the behavior of the standard OpenNebula drivers.

## How Should I Read This Chapter

You should be reading this Chapter if you are trying to extend OpenNebula functionality.

You can proceed to any of the following sections depending on which component you want to understand and extend the [virtualization system]({{% relref "devel-vmm#devel-vmm" %}}), the [storage system]({{% relref "sd#sd" %}}), the [interactive backup integrations]({{% relref "interactive_backup#interactive-backup-integration" %}}), the [information system]({{% relref "devel-im#devel-im" %}}), the [authentication system]({{% relref "devel-auth" %}}), the [network system]({{% relref "devel-nm#devel-nm" %}}) or the [marketplace drivers]({{% relref "devel-market#devel-market" %}}). Also you might be interested in the [Hook mechanism]({{% relref "../system_interfaces/hook_driver#hooks" %}}), a powerful way of integrating OpenNebula within your data center processes.
