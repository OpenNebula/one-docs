---
title: "Configuration"
linkTitle: "Configuration"
date: "2026-09-15"
description:
categories:
tags:
weight: "4"
type: docs
---

This section describes the inputs of the Open OnDemand Service and how to size the roles, tune the worker pool, add worker sizes, use the Slurm cluster of the service, attach an external one, use an external identity provider and manage users.

## Service Inputs

All inputs are `ONEAPP_*` context variables. OneFlow places every one of them in the context of every VM of the service, where root can read it, `ONEAPP_PORTAL_CERTIFICATE_KEY` and `ONEAPP_AUTH_OIDC_CLIENT_SECRET` included. Every input is optional, and the Sunstone wizard groups them in three tabs, **Portal**, **Users and login** and **Home directories**. A feature with an `_ENABLED` switch shows its other inputs only while the switch is `YES`, and ignores them while it is `NO`. A switch turned on with a required field empty stops the role at boot, and the message names the field, see [A Role Does Not Reach RUNNING]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}).

| Tab | Input | Default | Description |
|---|---|---|---|
| Portal | `ONEAPP_PORTAL_HOST_NAME` | empty | Public host name of the portal, resolving to its management address. Empty makes the portal answer on that address. |
| Portal | `ONEAPP_PORTAL_LETSENCRYPT_ENABLED` | `NO` | Request a Let's Encrypt certificate for the host name. The name has to resolve to the portal, and ports 80 and 443 have to be reachable from the Internet when the portal boots. On failure the portal keeps its self-signed certificate. |
| Portal | `ONEAPP_PORTAL_CERTIFICATE_ENABLED` | `NO` | Use a certificate of your own instead of the self-signed one. |
| Portal | `ONEAPP_PORTAL_CERTIFICATE_CHAIN`, `ONEAPP_PORTAL_CERTIFICATE_KEY` | empty | PEM certificate chain and private key, both required when the switch is on. |
| Users and login | `ONEAPP_AUTH_LOCAL_USERS` | `demo1:demo1pass` | Initial users, `user:password` separated by spaces, created in the directory of the portal at first boot. A uid may follow, `user:password:uid`, to match accounts that exist elsewhere; the others get the next free number from 10001. |
| Users and login | `ONEAPP_AUTH_OIDC_ENABLED` | `NO` | Sign in through an OpenID Connect provider as well, see [External Identity Provider](#external-identity-provider). |
| Users and login | `ONEAPP_AUTH_OIDC_ISSUER`, `ONEAPP_AUTH_OIDC_CLIENT_ID`, `ONEAPP_AUTH_OIDC_CLIENT_SECRET` | empty | Issuer URL, client id and client secret registered at the provider. The issuer and the client id are required when the switch is on, and the secret may stay empty for a provider that allows public clients. |
| Users and login | `ONEAPP_AUTH_OIDC_NAME` | `Institutional login` | Name of the provider on the login page. |
| Home directories | `ONEAPP_HOME_NFS_ENABLED` | `NO` | Use an NFS server of your own for the home directories instead of the storage role, which then only keeps the software cache. |
| Home directories | `ONEAPP_HOME_NFS_SERVER` | empty | Address of that NFS server, required when the switch is on. |
| Home directories | `ONEAPP_HOME_NFS_EXPORT` | `/export/home` | Path of the home export. With the switch off, it is also the path the storage role exports. |
{.w-100}

The host name, the OpenID Connect inputs and the external Slurm attributes can also be set on a running portal with `onevm updateconf`, and the portal reconfigures itself in under a minute. The portal keeps the certificate it already has for its host name, so a certificate switch changed later takes effect only together with a new host name. To apply it under the same host name, remove `/etc/ood/ssl/<host name>.crt` and `.key` on the portal (named after the address when there is no host name), and the next reconfigure issues the certificate again.

## Advanced Attributes

These attributes never appear in the wizard, so set them in the `template_contents` of a role in the service template, or in the `CONTEXT` of a standalone portal VM. A value set in a role reaches that role only, and the table names the role that reads each attribute:

| Attribute | Default | Description |
|---|---|---|
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | Seconds the oldest worker stays without a job before it drains its Slurm node and the pool loses it. The worker role reads it. |
| `ONEAPP_WORKER_DRAIN_SECONDS` | `600` | Seconds a drained worker waits for OneFlow to remove it before it returns its node to service. The worker role reads it. |
| `ONEAPP_POOL_RANGE` | derived | Address range the portal accepts workers from, as `first-last`, which also bounds the number of Slurm nodes. Inside a service the portal derives it from its compute interface, the whole /24 around its address, so set it only for a compute network larger than a /24 or for a portal outside a OneFlow service. The range has to stay inside one /24, because a session publishes the address of the worker that starts with the first three octets of the range, so on a larger compute network reserve a /24 slice of it for the workers and give that slice here. The portal role reads it. |
| `ONEAPP_SLURM_STATE_EXPORT` | `/export/slurm` | Export of the storage role that keeps the state of the Slurm controller, the munge key and the accounting dumps. The portal role mounts it. |
| `ONEAPP_SLURM_DEF_MEM_PER_CPU` | `1024` | Memory in MB a job gets per core when it asks for none. The portal role reads it. |
| `ONEAPP_SLURM_CONTROLLER_ENABLED` | `NO` | Add a second Slurm cluster of the site for batch jobs, see [An External Slurm Cluster](#an-external-slurm-cluster). The portal role reads it. |
| `ONEAPP_SLURM_CONTROLLER_HOST` | empty | Address or host name of that controller, required when the switch is on. The portal role reads it. |
| `ONEAPP_SLURM_TITLE` | `External Slurm` | Name of that cluster in the Job Composer and Active Jobs. The portal role reads it. |
{.w-100}

## Sizing the Roles

The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal. Every session is a Slurm job that reserves the cores and the memory its form asks for, and a worker takes sessions until its cores or its memory are reserved, so size the worker role for the sessions one VM should hold. The portal runs the Slurm controller, its accounting daemon and MariaDB beside Open OnDemand, 710 MB of memory in use on an idle service. Edit the service template before instantiating it and set `CPU`, `VCPU` and `MEMORY` in the `template_contents` of the role.

## Scaling the Worker Pool

The pool scales on its own, see [How the Pool Grows and Shrinks]({{% relref "platform_services/open_ondemand/architecture/#how-the-pool-grows-and-shrinks" %}}). The workers publish `SLURM_PENDING`, the jobs waiting for a worker of their role, and OneFlow adds one VM when it stays above 0 for two periods of 30 seconds. The oldest worker drains its Slurm node once it has been without a job for `ONEAPP_WORKER_IDLE_SECONDS` with nothing pending, publishes `OLDEST_IDLE=1` while the node is drained and empty, and OneFlow removes it after two periods of 60 seconds. `ONEAPP_WORKER_DRAIN_SECONDS` undoes a drain OneFlow has not acted on, and the last worker of a role never drains. Both are [Advanced Attributes](#advanced-attributes) of the worker role. Raise `max_vms` of the worker role in the service template for a pool larger than six. To set the size by hand while the service is `RUNNING` (OneFlow refuses the command during the cooldown that follows every scale operation, 300 seconds after a policy acts and 120 seconds after a scale by hand):

```shell
oneflow scale <service_id> worker <cardinality>
```

## Worker Sizes

Every role whose name starts with `worker` is a pool of session VMs. To offer a larger VM, copy the `worker` role in the service template under a new name, `worker_large` for instance, with the CPU and memory you want and the same parents and elasticity policies. Each worker registers its Slurm node with the name of its role as a feature, so a session that chooses a size is submitted with `--constraint=<role>` and runs on a worker of that role only, while a job with no constraint takes any worker. The application forms show a **Worker size** field only when several worker roles exist:

{{< image path="/images/open_ondemand/light/jupyter_form_sizes.png"
alt="The Jupyter form offering two worker sizes" align="center" width="90%" mb="20px" >}}

Each size scales on its own and keeps at least one VM, because OneFlow scales a role from the metrics of its VMs, and the workers count only the pending jobs that their role can serve. A GPU size is a `worker_gpu` role whose `template_contents` also carries the PCI device of the Host, as the [NVIDIA GPU passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) page describes. A worker that boots with `/dev/nvidia0` registers its node with the GPU as a Slurm resource, the forms then show a **GPUs** field, and a session that asks for one is submitted with `--gres=gpu:<n>`. The image ships no driver, so the site installs it on that role.

{{< alert title="Warning" type="warning" >}}
The GPU role was prepared without a GPU to test on. Run `nvidia-smi` inside a session before offering the size to users.
{{< /alert >}}

## Batch Jobs with Slurm

The service runs its own Slurm cluster, always on. The portal role runs `slurmctld`, `slurmdbd` and MariaDB beside Open OnDemand, keeps the controller state on the `/export/slurm` export of the storage role, and every worker joins the partition `main` as a dynamic node with the name of its role as a feature. Every interactive session is a Slurm job, so batch jobs and sessions share one queue and no two of them share a core. The portal offers the cluster as `Slurm` in the Job Composer and Active Jobs, and `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on the portal itself, so the Shell app submits a job as the user:

```shell
sbatch -c 1 --mem=512M -t 5 --wrap hostname
squeue
sacct -j <job id>
```

The job runs on a worker with the cores and the memory it asked for, and a job without `--mem` gets `ONEAPP_SLURM_DEF_MEM_PER_CPU` MB per core. The partition gives a job one hour when it sets no time and allows twelve. A job that waits for a worker grows the pool, see [Scaling the Worker Pool](#scaling-the-worker-pool), while a job no worker of the pool could ever run never does, because a GPU on a pool without one is refused at submit with `Requested node configuration is not available` and more cores than the largest worker has waits with reason `PartitionConfig`. Accounting runs through `slurmdbd` on the portal, so `sacct` keeps the history of every job and session, the portal dumps the database to the storage export every 30 minutes and restores the newest dump when a new portal boots.

{{< image path="/images/open_ondemand/light/job_composer_slurm.png"
alt="A job submitted from the Job Composer and completed on the Slurm cluster" align="center" width="90%" mb="20px" >}}

### An External Slurm Cluster

A second Slurm cluster of the site can be attached for batch jobs when it shares the users and the home with the portal, the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service for instance. The portal offers it in the Job Composer and Active Jobs under the name in `ONEAPP_SLURM_TITLE`, while the interactive applications keep running on the cluster of the service. `ONEAPP_SLURM_CONTROLLER_ENABLED` and `ONEAPP_SLURM_CONTROLLER_HOST` are [Advanced Attributes](#advanced-attributes) of the portal role, and a running portal takes them with `onevm updateconf`.

1. Note the compute addresses of the portal and storage VMs of the running service, the second address of each in `onevm list --list ID,NAME,IP`.
2. Instantiate `OneSlurm` on the same compute network with its local LDAP disabled:

   ```default
   ONEAPP_LDAP_ENABLE      NO
   ONEAPP_LDAP_DOMAIN      ood.local
   ONEAPP_LDAP_URL         ldap://<portal compute address>
   ONEAPP_SLURM_NFS_HOME   <storage compute address>:/export/home
   ```

   From the command line, the instantiation file has to list every input of the template, the others at their defaults.

3. Once OneSlurm is `RUNNING`, declare the cluster on the portal with the compute address of the controller:

   ```shell
   onevm updateconf <portal vm id> --append <<EOT
   CONTEXT = [ ONEAPP_SLURM_CONTROLLER_ENABLED = "YES", ONEAPP_SLURM_CONTROLLER_HOST = "<controller compute address>" ]
   EOT
   ```

For that cluster `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on its controller over SSH as the user, so the controller has to answer on port 22 from the compute address of the portal. Job history in `sacct` needs `slurmdbd` on that controller, which the default OneSlurm deployment does not run. The `appliances/one-ondemand/docs/slurmdbd-setup.sh` script of the [appliance repository](https://github.com/OpenNebula/marketplace-community) installs it with MariaDB, enables accounting in `slurm.conf` and registers the cluster.

## External Identity Provider

When `ONEAPP_AUTH_OIDC_ENABLED` is `YES`, the login page offers the provider in `ONEAPP_AUTH_OIDC_ISSUER`, `ONEAPP_AUTH_OIDC_CLIENT_ID` and `ONEAPP_AUTH_OIDC_CLIENT_SECRET` beside the local directory, under the name in `ONEAPP_AUTH_OIDC_NAME`. Register `https://<ONEAPP_PORTAL_HOST_NAME>/dex/callback` as the redirect URI at the provider. The account name is the `preferred_username` claim, or the part of the email before the at sign when the provider sends no such claim, and a user who signs in this way needs an entry in the LDAP directory under that name, because the session runs as a Unix user with a home directory.

## Managing Users

Users live in the LDAP directory of the portal role. The administrator password is generated at first boot and kept in `/etc/one-ondemand/ldap-admin.pass` on the portal, readable by root only. To add a user, on the portal VM:

```shell
ldapadd -x -D cn=admin,dc=ood,dc=local -y /etc/one-ondemand/ldap-admin.pass <<EOT
dn: cn=alice,ou=Groups,dc=ood,dc=local
objectClass: posixGroup
cn: alice
gidNumber: 10003

dn: uid=alice,ou=People,dc=ood,dc=local
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: alice
cn: alice
sn: alice
uidNumber: 10003
gidNumber: 10003
homeDirectory: /home/alice
loginShell: /bin/bash
userPassword: {SSHA}...
EOT
```

Generate the hash with `slappasswd -h '{SSHA}' -s <password>`. The user can sign in right away, and the workers resolve users against the same directory.
