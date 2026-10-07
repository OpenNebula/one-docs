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

| Name | Mandatory | Description |
|---|---|---|
| `Service` | Yes | Virtual Network for the controller and the workers |

## Service Inputs

All the inputs are optional. They are set when you create the service, and OneFlow passes them to the roles shown in the table.

| Parameter | Default | Roles | Description | Guide |
|---|---|---|---|---|
| `ONEAPP_LDAP_ENABLE` | `NO` | Controller | `YES` installs a local LDAP server on the controller | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_DOMAIN` | `slurm.local` | Controller | LDAP domain or base DN | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_ADMIN_USER` | empty, the appliance uses `admin` | Controller | Admin of the local LDAP, as a name or a DN | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_ADMIN_PASSWORD` | empty | Controller | Password of the local LDAP admin | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_URL` | empty | Controller | URL of an external LDAP server. Ignored when `ONEAPP_LDAP_ENABLE=YES` | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_BIND_USER` | empty | Controller | User to read the external LDAP, as a name or a DN | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_LDAP_BIND_PASSWORD` | empty | Controller | Password of the bind user | [Identity]({{% relref "platform_services/slurm/management/identity_management" %}}) |
| `ONEAPP_SLURM_NFS_HOME` | empty | Controller, workers | NFS export mounted at `/home`, as `host:/export` | [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}) |
| `ONEAPP_SLURM_NFS_SCRATCH` | empty | Controller, workers | NFS export mounted at `/scratch`, as `host:/export` | [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}) |
| `ONEAPP_SLURM_INFINIBAND_ENABLE` | `NO` | Controller, workers | `YES` configures IPoIB and MPI settings | [InfiniBand]({{% relref "platform_services/slurm/management/infiniband" %}}) |
| `ONEAPP_SLURM_IPOIB_SUBNET` | empty | Workers | IPoIB subnet, `/8`, `/16` or `/24`. Required with InfiniBand | [InfiniBand]({{% relref "platform_services/slurm/management/infiniband" %}}) |

The workers get the LDAP settings from the controller through OneGate, not from these inputs.

## Image Build Variables

These variables apply when you build the appliance images yourself from [one-apps](https://github.com/OpenNebula/one-apps). The Marketplace images use the defaults.

| Variable | Default | Image | Description |
|---|---|---|---|
| `INSTALL_INFINIBAND` | `true` | Controller, worker | Installs the InfiniBand, UCX and Open MPI packages |
| `INSTALL_DRIVERS` | `true` | Worker | Installs the NVIDIA driver |
| `NVIDIA_DRIVER_BRANCH` | `595` | Worker | NVIDIA driver branch, for `nvidia-driver-<branch>-server-open` |
