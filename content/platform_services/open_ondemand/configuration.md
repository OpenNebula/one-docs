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

This section describes the inputs of the Open OnDemand Service and how to size the roles, tune the worker pool, add worker sizes, attach a Slurm Cluster, use an external identity provider and manage users.

## Service Inputs

All inputs are `ONEAPP_*` context variables. OneFlow places every one of them in the context of every VM of the service, where root can read it, `ONEAPP_PORTAL_CERTIFICATE_KEY` and `ONEAPP_AUTH_OIDC_CLIENT_SECRET` included. Every input is optional, and the Sunstone wizard groups them in four tabs, **Portal**, **Users and login**, **Home directories** and **Slurm**. A feature with an `_ENABLED` switch shows its other inputs only while the switch is `YES`, and ignores them while it is `NO`. A switch turned on with a required field empty stops the role at boot, and the message names the field, see [A Role Does Not Reach RUNNING]({{% relref "platform_services/open_ondemand/monitoring_and_troubleshooting/#a-role-does-not-reach-running" %}}).

| Tab | Input | Default | Description |
|---|---|---|---|
| Portal | `ONEAPP_PORTAL_HOST_NAME` | empty | Public host name of the portal, resolving to its management address. Empty makes the portal answer on that address. |
| Portal | `ONEAPP_PORTAL_LETSENCRYPT_ENABLED` | `NO` | Request a Let's Encrypt certificate for the host name. The name has to resolve to the portal, and ports 80 and 443 have to be reachable from the Internet when the portal boots. On failure the portal keeps its self-signed certificate. |
| Portal | `ONEAPP_PORTAL_CERTIFICATE_ENABLED` | `NO` | Use a certificate of your own instead of the self-signed one. |
| Portal | `ONEAPP_PORTAL_CERTIFICATE_CHAIN`, `ONEAPP_PORTAL_CERTIFICATE_KEY` | empty | PEM certificate chain and private key, both required when the switch is on. |
| Users and login | `ONEAPP_AUTH_LOCAL_USERS` | `demo1:demo1pass:10001` | Initial users, `user:password:uid` separated by spaces, created in the directory of the portal at first boot. |
| Users and login | `ONEAPP_AUTH_OIDC_ENABLED` | `NO` | Sign in through an OpenID Connect provider as well, see [External Identity Provider](#external-identity-provider). |
| Users and login | `ONEAPP_AUTH_OIDC_ISSUER`, `ONEAPP_AUTH_OIDC_CLIENT_ID`, `ONEAPP_AUTH_OIDC_CLIENT_SECRET` | empty | Issuer URL, client id and client secret registered at the provider. The issuer and the client id are required when the switch is on, and the secret may stay empty for a provider that allows public clients. |
| Users and login | `ONEAPP_AUTH_OIDC_NAME` | `Institutional login` | Name of the provider on the login page. |
| Home directories | `ONEAPP_HOME_NFS_ENABLED` | `NO` | Use an NFS server of your own for the home directories instead of the storage role, which then only keeps the software cache. |
| Home directories | `ONEAPP_HOME_NFS_SERVER` | empty | Address of that NFS server, required when the switch is on. |
| Home directories | `ONEAPP_HOME_NFS_EXPORT` | `/export/home` | Path of the home export. With the switch off, it is also the path the storage role exports. |
| Slurm | `ONEAPP_SLURM_CONTROLLER_ENABLED` | `NO` | Submit batch jobs to a Slurm cluster that shares the users and the home, see [Batch Jobs with Slurm](#batch-jobs-with-slurm). |
| Slurm | `ONEAPP_SLURM_CONTROLLER_HOST` | empty | Compute address of the Slurm controller, required when the switch is on. |
{.w-100}

The host name, the Slurm controller and the OpenID Connect inputs can also be set on a running portal with `onevm updateconf`, and the portal reconfigures itself in under a minute. The portal keeps the certificate it already has for its host name, so a certificate switch changed later takes effect only together with a new host name. To apply it under the same host name, remove `/etc/ood/ssl/<host name>.crt` and `.key` on the portal (named after the address when there is no host name), and the next reconfigure issues the certificate again.

## Advanced Attributes

Three attributes never appear in the wizard, so set them in the `template_contents` of a role in the service template, or in the `CONTEXT` of a standalone portal VM. A value set in a role reaches that role only, and the table names the role that reads each attribute:

| Attribute | Default | Description |
|---|---|---|
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | Seconds the oldest worker stays empty before the pool loses a VM. The worker role reads it. |
| `ONEAPP_WORKER_MAX_SESSIONS` | `4` | Sessions a worker takes. New sessions go elsewhere at that count, and a pool with every worker at it grows. The worker role and the portal role both read it, so set it in both. |
| `ONEAPP_POOL_RANGE` | derived | Address range the portal accepts workers from, as `first-last`. Inside a service the portal derives it from its compute interface, the whole /24 around its address, so set it only for a compute network larger than a /24 or for a portal outside a OneFlow service. The range has to stay inside one /24, so on a larger compute network reserve a /24 slice of it for the workers and give that slice here. The portal role reads it. |
{.w-100}

## Sizing the Roles

The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal. A worker holds up to `ONEAPP_WORKER_MAX_SESSIONS` sessions that share its CPU and memory, so size the worker role for the load you expect. Edit the service template before instantiating it and set `CPU`, `VCPU` and `MEMORY` in the `template_contents` of the role.

## Scaling the Worker Pool

The pool scales on its own, see [How the Pool Grows and Shrinks]({{% relref "platform_services/open_ondemand/architecture/#how-the-pool-grows-and-shrinks" %}}). `ONEAPP_WORKER_IDLE_SECONDS` sets how long the oldest worker stays empty before it is removed, and `ONEAPP_WORKER_MAX_SESSIONS` how many sessions a worker takes before the pool grows. Both are [Advanced Attributes](#advanced-attributes), the first in the worker role and the second in both the worker and the portal roles, because the workers publish `AT_CAPACITY` from it and the portal caps the dispatcher with it. Raise `max_vms` of the worker role in the service template for a pool larger than six. To set the size by hand while the service is `RUNNING` (OneFlow refuses the command during the cooldown that follows every scale operation, 120 seconds after growing and 300 seconds after the policy shrinks):

```shell
oneflow scale <service_id> worker <cardinality>
```

## Worker Sizes

Every role whose name starts with `worker` is a pool of session VMs. To offer a larger VM, copy the `worker` role in the service template under a new name, `worker_large` for instance, with the CPU and memory you want and the same parents and elasticity policies. The application forms then show a **Worker size** field with the sizes that exist:

{{< image path="/images/open_ondemand/light/jupyter_form_sizes.png"
alt="The Jupyter form offering two worker sizes" align="center" width="90%" mb="20px" >}}

Each size scales on its own and keeps at least one VM, because OneFlow scales a role from the metrics of its VMs. A GPU size is a `worker_gpu` role whose `template_contents` also carries the PCI device of the Host, as the [NVIDIA GPU passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) page describes. The session container then starts with `--nv` when the VM has an NVIDIA device and its driver; the image ships no driver, so the site installs it on that role.

{{< alert title="Warning" type="warning" >}}
The GPU role was prepared without a GPU to test on. Run `nvidia-smi` inside a session before offering the size to users.
{{< /alert >}}

## Batch Jobs with Slurm

The VM pool has no scheduler, so for a queue, a walltime and accounting attach the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service. The portal offers it as a second cluster in the Job Composer and Active Jobs, while the interactive applications keep running on the pool. The Slurm Cluster shares the users and the home directory with the portal.

1. Note the compute addresses of the portal and storage VMs of the running service, the second address of each in `onevm list --list ID,NAME,IP`.
2. Instantiate `OneSlurm` on the same compute network with its local LDAP disabled:

   ```default
   ONEAPP_LDAP_ENABLE      NO
   ONEAPP_LDAP_DOMAIN      ood.local
   ONEAPP_LDAP_URL         ldap://<portal compute address>
   ONEAPP_SLURM_NFS_HOME   <storage compute address>:/export/home
   ```

   From the command line, the instantiation file has to list every input of the template, the others at their defaults.

3. Once OneSlurm is `RUNNING`, enable the Slurm integration on the portal with the compute address of the controller:

   ```shell
   onevm updateconf <portal vm id> --append <<EOT
   CONTEXT = [ ONEAPP_SLURM_CONTROLLER_ENABLED = "YES", ONEAPP_SLURM_CONTROLLER_HOST = "<controller compute address>" ]
   EOT
   ```

{{< image path="/images/open_ondemand/light/job_composer_slurm.png"
alt="A job submitted from the Job Composer and completed on the Slurm cluster" align="center" width="90%" mb="20px" >}}

The portal installs no Slurm client, so `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on the controller over SSH as the user. Job history in `sacct` needs `slurmdbd` on the controller, which the default OneSlurm deployment does not run. The `appliances/one-ondemand/docs/slurmdbd-setup.sh` script of the [appliance repository](https://github.com/OpenNebula/marketplace-community) installs it with MariaDB, enables accounting in `slurm.conf` and registers the cluster.

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
