---
title: "Open OnDemand Overview"
linkTitle: "Overview"
weight: 1
type: docs
---

The Open OnDemand appliance deploys a complete Open OnDemand portal on OpenNebula. A user signs in, presses a button and gets a JupyterLab notebook, RStudio, Octave, a C++ notebook or VS Code running on a compute VM, with the scientific software served from the [EESSI](https://www.eessi.io/) catalogue and a home directory that follows them from session to session.

The service has three roles, all running from the same image. `ONEAPP_ROLE` decides at boot which one a VM plays, and the OneFlow template sets it per role.

| Role | What it runs | Cardinality |
|---|---|---|
| `storage` | NFS server for the shared home, site cache for the software catalogue | 1 |
| `portal` | Open OnDemand, its own LDAP directory and Dex authentication | 1 |
| `worker` | User sessions, inside Apptainer containers | 1 to 6, elastic |

{{< image path="/images/open_ondemand/light/architecture.svg" pathDark="/images/open_ondemand/dark/architecture.svg"
alt="The three roles of the service on the management and compute networks" align="center" width="90%" mb="20px" >}}

Instantiating the service creates one VM per role plus the elastic workers, on two Virtual Networks you select. The image, the VM template and the service template come from the marketplace download and stay in your OpenNebula after the service is deleted.

## How a session runs

The portal reaches the worker VMs over SSH with the Open OnDemand `linux_host` adapter, and each session runs inside an Apptainer container with the VM filesystem mounted inside. There is no batch scheduler. Scientific software comes from EESSI over CernVM-FS, cached by the storage role, so a notebook opened here loads the same modules a user would find at a EuroHPC centre and the image does not age with the software it serves.

## How the pool grows

Every worker reports its open session count to OneGate. OneFlow adds a VM when the average passes one session per worker and removes one when the oldest worker has been empty for ten minutes, one VM at a time. The portal sends each new session to the least loaded worker and, among equals, to the youngest, so a VM added by the autoscaler receives work as soon as it is ready and the oldest one drains as its sessions end. A worker is serving about 40 seconds after instantiation.

## Requirements

* OpenNebula 6.10 or later, with [OneFlow](https://docs.opennebula.io/7.4/product/operation_references/opennebula_services_configuration/oneflow/) and [OneGate](https://docs.opennebula.io/7.4/product/virtual_machines_operation/multi-vm_workflows/onegate_usage/) enabled, and OneGate reachable from the service networks.
* Two Virtual Networks. A management network with internet access, where the portal publishes its web interface, and a compute network reserved for the service, where the three roles talk to each other. The portal treats every live address in the range that network assigns as a worker, apart from its own and the storage role's, so nothing else may live there.
* Outbound access to the EESSI CernVM-FS servers from the storage role.

If a firewall sits between the networks, these are the flows the service needs:

| From | To | Port | What for |
|---|---|---|---|
| users | portal, management network | 443, and 80 with `letsencrypt` | the web interface |
| portal | workers | 22 | starting and stopping sessions |
| workers | portal | 389 | resolving users against the directory |
| portal and workers | storage | 2049 | the shared home over NFSv4 |
| portal and workers | storage | 3128 | the software catalogue through the site cache |
| every role | OneGate endpoint | 5030 by default | reporting readiness and session counts |
| Prometheus | portal, management network | 9101 | the service metrics, only if you scrape them |
| storage | internet | 80 and 8000 | the EESSI CernVM-FS servers, plain HTTP |

The compute network carries the directory lookups in the clear, so it has to stay reserved for the service.

Marketplace defaults per VM are 2 vCPU and 4 GB of memory, 8 GB for the portal role. A worker runs every session that lands on it inside one VM, so size the worker role for the sessions you expect.

## Versions and licence

Open OnDemand 4.2 on Ubuntu 24.04, EESSI 2025.06, Apptainer 1.5. Open OnDemand is MIT licensed and the appliance code is Apache 2.0. There is no fee for the appliance; it runs on your own OpenNebula.
