---
title: "Requirements"
linkTitle: "Requirements"
date: "2026-10-14"
description: "Check the Clusters, services, network and ports that the portal needs."
categories:
tags:
type: docs
weight: "2"
---

Before you deploy the portal, check that you have the elements in the following table.

| **Requirement** | **What the portal needs** |
|-------------|-----------------------|
| OneSlurm Clusters | One or more Clusters in `RUNNING` state, and the IP address of each controller. |
| LDAP server | The LDAP server of the Clusters, with a `ldap://` URL. |
| NFS export | The export with the home directories of the users, for example `10.0.0.10:/export/home`. |
| User homes | One home directory for each user on that export, owned by the user, with mode `700`. |
| Virtual Network | A Virtual Network that reaches the controllers, the LDAP server and the NFS server. |
| [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate" %}}) | Reachable from that network. The portal publishes its URL and its errors there. |

## LDAP Details

* Use the same domain as `ONEAPP_LDAP_DOMAIN` in OneSlurm. The default is `slurm.local`.
* You can also use a base DN, such as `dc=example,dc=org`.
* Users must be `posixAccount` entries under `ou=People`.
* The portal has no bind user, so **the LDAP server must allow anonymous search under `ou=People`**.

The LDAP server of OneSlurm meets all of these points.

## NFS Details

* Use the same export as `ONEAPP_SLURM_NFS_HOME` in OneSlurm.
* **The NFS server must allow the IP address of the portal.**
* The portal uses NFS version 4. The export can use `root_squash`.

## Size of the VM

The default VM has 2 vCPU, 4 GB of memory and a 10 GB disk. Each active user needs about 200 MB of memory (measured with six users). Add memory if more users work at the same time.

## Network Ports

Limit the traffic of the portal, for example with a [security group]({{% relref "product/virtual_machines_operation/virtual_machines_networking/security_groups" %}}).

| **Direction** | **Port** | **Use** |
|-----------|------|-----|
| Inbound | TCP 443 | Users open the portal. |
| Inbound | TCP 80 | Redirects to 443. |
| Inbound | TCP 22 | Administrators only. |
| Outbound | TCP 22 | SSH to the controllers. |
| Outbound | TCP 389 | LDAP server. |
| Outbound | TCP 2049 | NFS server. |
| Outbound | OneGate port | OneGate. |

**Do not open port 5558.** The login service of the portal (Dex) shows metrics there without authentication, and Open OnDemand does not allow changing it.

## Next Steps

To deploy the portal, refer to [Quick Start]({{% relref "platform_services/slurm/integrations/open_ondemand/quick_start" %}}).
