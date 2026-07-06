---
title: "NICo Driver (AE)"
date: "2026-06-03"
description: "Configure OpenNebula Hosts and VM templates for NVIDIA NICo instances."
categories:
pageintoc: "177"
tags:
weight: "4"
---

<a id="nicomg"></a>

## Overview

The NICo [VMM]({{% relref "product/integration_references/infrastructure_drivers_development/devel-vmm/" %}}) and [IM]({{% relref "product/integration_references/infrastructure_drivers_development/devel-im/" %}}) drivers enable OpenNebula to deploy and monitor NVIDIA NICo instances through the NICo REST API. A NICo Host in OpenNebula does not represent a KVM or LXC hypervisor node. Instead, it represents a NICo allocation and the API connection settings used to create, inspect, and delete NICo instances.

The NICo VMM driver stores the NICo instance UUID as the VM `DEPLOY_ID`. Later operations, such as shutdown and monitoring, use this value when making calls to the NICo REST API.

OpenNebula maintains a NICo VM in the `RUNNING` state during a NICo reboot request. The monitor data includes `NICO_STATUS`, so that transient NICo states such as `Rebooting` can be inspected without changing the OpenNebula lifecycle state.

## Creating a NICo Host

Create a dedicated Host using the NICo IM and VMM drivers:

```shell
onehost create nico --im nico --vm nico
```

After creating the Host, add the NICo connection and allocation attributes:

```shell
onehost update nico
```

Example Host template:

```default
NICO_CARBIDE_PROXY     = "https://ncp-isv-carbide-proxy.nvidia.com/v1/carbide/proxy"
NICO_SSA_ISSUER        = "https://issuer.example/token-provider"
NICO_NGC_ORG           = "example-org"
NICO_ISV_CLIENT_ID     = "client-id"
NICO_ISV_CLIENT_SECRET = "client-secret"
NICO_TARGET_SCOPES     = "scope1 scope2"
NICO_ALLOCATION        = "allocation-id"
NICO_API_TIMEOUT       = "60"
NICO_FORCE_DESTROY     = "NO"
```

Required Host attributes:

- `NICO_CARBIDE_PROXY`: Base URL for the CARBIDE proxy.
- `NICO_SSA_ISSUER`: Issuer URL used to obtain the JWT token.
- `NICO_NGC_ORG`: NGC organization used in NICo API paths.
- `NICO_ISV_CLIENT_ID`: Client ID for the `client_credentials` flow.
- `NICO_ISV_CLIENT_SECRET`: Client secret for the `client_credentials` flow.
- `NICO_TARGET_SCOPES`: Scopes requested when acquiring the JWT token.
- `NICO_ALLOCATION`: NICo allocation ID represented by this OpenNebula Host.

Optional Host attributes:

- `NICO_API_TIMEOUT`: API timeout in seconds. The default is `60`.
- `NICO_FORCE_DESTROY`: Set to `YES` to request forced deletion on cancel operations. The default is `NO`.

The IM driver uses `NICO_ALLOCATION` to query `GET /allocation/<id>` and report Host capacity from `allocationConstraints[0].constraintValue`.

## Creating a NICo VM Template

Create a VM template with the NICo instance attributes required by the allocation and operating system you intend to deploy.

Example VM template:

```default
NAME   = "nico-instance"
CPU    = "1"
MEMORY = "1"

NICO_INSTANCE_TYPE_ID = "instance-type-id"
NICO_OS_ID            = "operating-system-id"
NICO_VPC_ID           = "vpc-id"

NICO_NETWORK_SECURITY_GROUP_ID = "security-group-id"
NICO_SSH_KEY_GROUP_IDS         = "ssh-key-group-1,ssh-key-group-2"
NICO_USER_DATA                 = "cloud-init-or-user-data"
NICO_LABELS                    = "{\"environment\":\"test\"}"

NIC = [
  NETWORK            = "nico-network",
  NICO_VPC_PREFIX_ID = "vpc-prefix-id"
]

SCHED_REQUIREMENTS = "ID = 123"
```

Required VM attributes:

- `CPU`: Must be `1`, as it represents a single instance to the OpenNebula scheduler.
- `MEMORY`: Must be `1`, same as with CPU.
- `NICO_INSTANCE_TYPE_ID`: NICo instance type to deploy.
- `NICO_OS_ID`: Operating system ID.
- `NICO_VPC_ID`: VPC used by the instance. This attribute must be defined in the VM template.
- `NIC`: Network interface used by the instance.
- `NIC/NICO_VPC_PREFIX_ID`: VPC prefix used by the instance interface. This attribute must be defined in the NIC section.
- `SCHED_REQUIREMENTS`: Scheduling expression used to place the VM on the NICo Host.

`NICO_VPC_ID` is read only from the VM template. `NICO_VPC_PREFIX_ID` is read only from the first NIC section.

Common optional VM attributes:

- `NICO_NETWORK_SECURITY_GROUP_ID`: Network security group ID.
- `NICO_SSH_KEY_GROUP_IDS`: Comma-separated list of SSH key group IDs.
- `NICO_USER_DATA`: User data passed to the NICo instance.
- `NICO_LABELS`: JSON object with labels to attach to the NICo instance.

## Scheduling to the NICo Host

NICo instances must be scheduled to the OpenNebula Host configured with the NICo drivers and the corresponding NICo allocation attributes. Use `SCHED_REQUIREMENTS` in the VM template to force placement on that Host.

Pin by Host ID:

```default
SCHED_REQUIREMENTS = "ID = 123"
```

Alternatively, place the VM on any Host using the NICo VMM driver:

```default
SCHED_REQUIREMENTS = "VM_MAD = \"nico\""
```

Using explicit scheduling prevents the NICo template from being placed on regular KVM or LXC Hosts.
