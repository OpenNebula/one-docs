---
title: "Overview"
linkTitle: "Overview"
date: "2026-10-14"
categories:
tags:
type: docs
weight: "1"
aliases:
  - /solutions/integration_blueprints/open_ondemand/overview/
  - /solutions/integration_blueprints/open_ondemand/architecture/
---

[Open OnDemand](https://openondemand.org/) is a web portal for HPC users. The Open OnDemand appliance runs this portal in one VM, connected to your OneSlurm Clusters. Users sign in with their LDAP account and, from a web browser, they can:

* Manage the files in their home
* Submit jobs and follow them
* Open a terminal on a Cluster

The appliance is available in the [OpenNebula Public Marketplace](https://marketplace.opennebula.io/appliance/d3c8ea14-f6f0-455c-8a41-6129affa9a0e). It uses Ubuntu 26.04 LTS and Open OnDemand 4.2.

## How It Works

**The portal does not run Slurm.** It sends the Slurm commands of each user to the controller of the Cluster over SSH.

The portal and the Clusters share two services:

* The same LDAP directory, so users have the same account everywhere
* The same NFS export for `/home`, so users see the same files everywhere

One portal can serve several OneSlurm Clusters.

## What Happens at Boot

1. The appliance checks the values of the wizard.
2. It mounts the NFS export on `/home`.
3. It reads the users from LDAP.
4. It creates a self-signed certificate for the IP address of the VM.
5. It adds each Slurm Cluster to the portal and saves the SSH host key of each controller.
6. It starts the portal and publishes its URL in OneGate.

## What Happens at the First Login of a User

* The portal creates an SSH key for the user in `~/.ssh/id_ed25519_portal`.
* It adds the key to `~/.ssh/authorized_keys`, accepted only from the IP addresses of the portal.
* The controllers read the same home directory over NFS, so the portal can run `sbatch`, `squeue` and `scancel` as that user. The terminal uses the same key.

Each user works with their own Unix account, with the same UID as on the Clusters. **Users cannot read the files or cancel the jobs of other users.**

## Next Steps

Before you deploy the portal, refer to [Requirements]({{% relref "platform_services/slurm/integrations/open_ondemand/requirements" %}}).
