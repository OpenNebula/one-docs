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

All inputs are `ONEAPP_*` context variables. OneFlow places every one of them in the context of every VM of the service, where root can read it, `ONEAPP_OOD_SSL_KEY` and `ONEAPP_OIDC_CLIENT_SECRET` included.

| Input | Default | Description |
|---|---|---|
| `ONEAPP_POOL_RANGE` | `172.20.0.50-172.20.0.249` | **Required**. Address range the compute Virtual Network assigns to VMs, as `first-last`. |
| `ONEAPP_OOD_SERVERNAME` | empty | Public host name of the portal, resolving to its management address. Empty makes the portal answer on that address. |
| `ONEAPP_OOD_SSL_MODE` | `selfsigned` | `selfsigned`, `letsencrypt` (needs a public name and port 80 reachable) or `custom`. |
| `ONEAPP_OOD_SSL_CERT`, `ONEAPP_OOD_SSL_KEY` | empty | PEM certificate chain and private key for the `custom` mode. |
| `ONEAPP_LDAP_USERS` | `demo1:demo1pass:10001` | Initial users, `user:password:uid` separated by spaces. |
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | How long the oldest worker stays empty before the pool loses a VM. |
| `ONEAPP_WORKER_MAX_SESSIONS` | `4` | Sessions a worker takes. New sessions go elsewhere at that count, and a pool with every worker at it grows. |
| `ONEAPP_SLURM_CONTROLLER` | empty | Compute address of a Slurm controller that shares the users and the home. |
| `ONEAPP_OIDC_ISSUER`, `ONEAPP_OIDC_CLIENT_ID`, `ONEAPP_OIDC_CLIENT_SECRET` | empty | An OpenID Connect provider for the login page. |
| `ONEAPP_OIDC_NAME` | `Institutional login` | Name of that provider on the login page. |
| `ONEAPP_NFS_SERVER`, `ONEAPP_NFS_EXPORT` | empty, `/export/home` | An NFS server of your own for the home directories, and the export path. Empty uses the storage role. |

The mode and name of the certificate, the Slurm controller and the OpenID Connect inputs can also be set on a running portal with `onevm updateconf`; the portal reconfigures itself in under a minute.

## Sizing the Roles

The marketplace template gives every VM 2 vCPU and 4 GB of memory, 8 GB for the portal. A worker holds up to `ONEAPP_WORKER_MAX_SESSIONS` sessions that share its CPU and memory, so size the worker role for the load you expect. Edit the service template before instantiating it and set `CPU`, `VCPU` and `MEMORY` in the `vm_template_contents` of the role.

## Scaling the Worker Pool

The pool scales on its own, see [How the Pool Grows and Shrinks]({{% relref "platform_services/open_ondemand/architecture/#how-the-pool-grows-and-shrinks" %}}). `ONEAPP_WORKER_IDLE_SECONDS` sets how long the oldest worker stays empty before it is removed, and `ONEAPP_WORKER_MAX_SESSIONS` how many sessions a worker takes before the pool grows. Raise `max_vms` of the worker role in the service template for a pool larger than six. To set the size by hand at any time:

```shell
oneflow scale <service_id> worker <cardinality>
```

## Worker Sizes

Every role whose name starts with `worker` is a pool of session VMs. To offer a larger VM, copy the `worker` role in the service template under a new name, `worker_large` for instance, with the CPU and memory you want and the same parents and elasticity policies. The application forms then show a **Worker size** field with the sizes that exist:

{{< image path="/images/open_ondemand/light/jupyter_form_sizes.png"
alt="The Jupyter form offering two worker sizes" align="center" width="90%" mb="20px" >}}

Each size scales on its own and keeps at least one VM, because OneFlow scales a role from the metrics of its VMs. A GPU size is a `worker_gpu` role whose `vm_template_contents` also carries the PCI device of the Host, as the [NVIDIA GPU passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) page describes. The session container then starts with `--nv` when the VM has an NVIDIA device and its driver; the image ships no driver, so the site installs it on that role.

{{< alert title="Warning" type="warning" >}}
The GPU role was prepared without a GPU to test on. Run `nvidia-smi` inside a session before offering the size to users.
{{< /alert >}}

## Batch Jobs with Slurm

The VM pool has no scheduler. For a queue, a walltime and accounting, attach the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service. The portal offers it as a second cluster in the Job Composer and Active Jobs, while the interactive applications keep running on the pool. The Slurm Cluster shares the users and the home directory with the portal.

1. Note the compute addresses of the portal and storage VMs of the running service, the second address of each in `onevm list`.
2. Instantiate `OneSlurm` on the same compute network with its local LDAP disabled:

   ```default
   ONEAPP_LDAP_ENABLE      NO
   ONEAPP_LDAP_DOMAIN      ood.local
   ONEAPP_LDAP_URL         ldap://<portal compute address>
   ONEAPP_SLURM_NFS_HOME   <storage compute address>:/export/home
   ```

3. Once OneSlurm is `RUNNING`, give the portal the compute address of the Slurm controller:

   ```shell
   onevm updateconf <portal vm id> --append <<EOT
   CONTEXT = [ ONEAPP_SLURM_CONTROLLER = "<controller compute address>" ]
   EOT
   ```

{{< image path="/images/open_ondemand/light/job_composer_slurm.png"
alt="A job submitted from the Job Composer and completed on the Slurm cluster" align="center" width="90%" mb="20px" >}}

The portal installs no Slurm client: `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on the controller over SSH as the user. Job history in `sacct` needs `slurmdbd` on the controller, which the default OneSlurm deployment does not run. The `docs/slurmdbd-setup.sh` script of the [appliance repository](https://github.com/OpenNebula/marketplace-community) installs it with MariaDB, enables accounting in `slurm.conf` and registers the cluster.

## External Identity Provider

With `ONEAPP_OIDC_ISSUER`, `ONEAPP_OIDC_CLIENT_ID` and `ONEAPP_OIDC_CLIENT_SECRET` set, the login page offers the provider beside the local directory. Register `https://<ONEAPP_OOD_SERVERNAME>/dex/callback` as the redirect URI at the provider. The account name is the `preferred_username` claim, or the part of the email before the at sign when the provider sends no such claim, and a user who signs in this way needs an entry in the LDAP directory under that name, because the session runs as a Unix user with a home directory.

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
