---
title: "Configuration Parameters"
linkTitle: "Configuration Parameters"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "2"
---

## Service Network

| **Name** | **Mandatory** | **Description** |
|---|---|---|
| `Service` | Yes | Virtual Network for the controller and the workers |

## Service Inputs

All the inputs are optional. You set them when you create the service.

### LDAP

Used by the controller. The workers get the LDAP settings from the controller through OneGate. See [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}).

| **Parameter** | **Default** | **Description** |
|---|---|---|
| `ONEAPP_LDAP_ENABLE` | `NO` | `YES` installs a local LDAP server on the controller |
| `ONEAPP_LDAP_DOMAIN` | `slurm.local` | LDAP domain or base DN |
| `ONEAPP_LDAP_ADMIN_USER` | `admin` | Admin of the local LDAP, as a name or a DN |
| `ONEAPP_LDAP_ADMIN_PASSWORD` | empty | Password of the local LDAP admin |
| `ONEAPP_LDAP_URL` | empty | URL of an external LDAP server. Ignored with local LDAP |
| `ONEAPP_LDAP_BIND_USER` | empty | User to read the external LDAP, as a name or a DN |
| `ONEAPP_LDAP_BIND_PASSWORD` | empty | Password of the bind user |

The admin user input is empty in the service. When it stays empty, the appliance uses `admin`.

### NFS

Used by the controller and the workers. See [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}).

| **Parameter** | **Default** | **Description** |
|---|---|---|
| `ONEAPP_SLURM_NFS_HOME` | empty | NFS export mounted at `/home` |
| `ONEAPP_SLURM_NFS_SCRATCH` | empty | NFS export mounted at `/scratch` |

Both use the format `host:/export`.

### InfiniBand

See [InfiniBand and High-Performance Networking]({{% relref "platform_services/slurm/management/infiniband" %}}).

| **Parameter** | **Default** | **Used by** | **Description** |
|---|---|---|---|
| `ONEAPP_SLURM_INFINIBAND_ENABLE` | `NO` | Controller, workers | `YES` configures IPoIB and the MPI settings |
| `ONEAPP_SLURM_IPOIB_SUBNET` | empty | Workers | IPoIB subnet. Required when InfiniBand is enabled |

The IPoIB subnet must use a `/8`, `/16` or `/24` prefix.

## Image Build Variables

These variables apply when you build the appliance images yourself from [one-apps](https://github.com/OpenNebula/one-apps). The Marketplace images use the defaults.

| **Variable** | **Default** | **Image** | **Description** |
|---|---|---|---|
| `INSTALL_INFINIBAND` | `true` | Controller, worker | Installs the InfiniBand, UCX and Open MPI packages |
| `INSTALL_DRIVERS` | `true` | Worker | Installs the NVIDIA driver |
| `NVIDIA_DRIVER_BRANCH` | `595` | Worker | NVIDIA driver branch, for `nvidia-driver-<branch>-server-open` |
