---
title: "Service Architecture"
linkTitle: "Service Architecture"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "1"
---

## Components

| **Component** | **Where** | **Role** |
|---|---|---|
| OneFlow service `OneSlurm` | OpenNebula Front-end | Creates the roles in order and scales the workers |
| `controller` role | 1 VM | `slurmctld`, Munge, optional OpenLDAP, reconciler |
| `worker` role | 1 or more VMs, child of `controller` | `slurmd`, Munge, self-drain hook |
| OneGate | OpenNebula Front-end | Shares data between the VMs of the service |
| Service network | Virtual Network | Connects all the VMs. Chosen when the service is created |

The service uses `deployment: straight` and `ready_status_gate: true`. OneFlow creates the controller first and the workers only after the controller reports `READY=YES`.

## Data in OneGate

| **Attribute** | **Published by** | **Read by** | **Content** |
|---|---|---|---|
| `READY` | Controller | OneFlow, workers | `YES` when the controller is configured |
| `SLURM_MUNGE_KEY` | Controller | Workers | Munge key in base64 |
| `LDAP_URL` | Controller | Workers | LDAP URL. Empty when LDAP is disabled |
| `LDAP_DOMAIN` | Controller | Workers | LDAP domain or base DN |
| `LDAP_ADMIN_USER` | Controller | | LDAP admin user, when set |
| `LDAP_BIND_USER` | Controller | Workers | LDAP bind user, when set |
| `LDAP_BIND_PASSWORD` | Controller | Workers | LDAP bind password, when set |
| `SLURM_NODENAME` | Each worker | Controller reconciler | Name of the Slurm node of this VM |

With local LDAP, `LDAP_URL` is `ldap://<CONTROLLER_IP>`.

## Network Ports

The following table shows the default ports of each service.

| **Port** | **Service** | **From** | **To** |
|---|---|---|---|
| 6817/TCP | `slurmctld` and configless configuration | Workers | Controller |
| 389/TCP | LDAP | All VMs | Local LDAP on the controller, or the external LDAP |
| 2049/TCP | NFSv4 | All VMs | NFS server, when NFS is used |
| 22/TCP | SSH | Users | Controller |

## Files and Units

| **Item** | **VM** | **Purpose** |
|---|---|---|
| `/etc/slurm/slurm.conf`, `gres.conf`, `cgroup.conf` | Controller | Slurm configuration, written at each boot |
| `/etc/munge/munge.key` | All | Munge key |
| `/etc/sssd/sssd.conf` | All, with LDAP | SSSD client for LDAP |
| `oneslurm-reconcile.timer` | Controller | Runs the reconciler 2 minutes after boot, then every 60 seconds |
| `/usr/local/sbin/oneslurm-reconcile-nodes` | Controller | Reconciler script |
| `oneslurm-self-drain.service` | Workers | Removes the node from Slurm at shutdown |
| `/etc/systemd/system/slurmd.service` | Workers | `slurmd` in configless mode with dynamic registration |
| `/etc/netplan/90-oneslurm-ipoib.yaml` | Workers, with InfiniBand | IPoIB address |

## Boot Sequence

In every VM, the NFS exports are mounted first, while the network is configured. Then the appliance configures the role.

### Controller

1. Sets the hostname `slurm-one-controller`.
2. Writes `slurm.conf`, `gres.conf` and `cgroup.conf`.
3. Creates the Munge key at the first boot and starts `slurmctld`.
4. Configures LDAP, local or external, and publishes the LDAP data in OneGate.
5. Publishes `SLURM_MUNGE_KEY` and `READY=YES` in OneGate.
6. Starts the reconciler timer.

### Worker

1. Waits until the controller publishes `READY=YES`, then reads its IP, the Munge key and the LDAP data.
2. Sets its hostname. The Marketplace template uses the VM name. Without `SET_HOSTNAME`, the hostname is `slurm-one-worker-<VM_ID>`.
3. Checks that port 6817 of the controller answers.
4. Maps `slurm-one-controller` to the controller IP in `/etc/hosts`.
5. Configures IPoIB, when InfiniBand is enabled.
6. Installs the Munge key and starts `slurmd`.
7. Publishes `SLURM_NODENAME` in OneGate.
8. Installs the self-drain hook.
9. Configures the SSSD client, when the controller published LDAP data.
