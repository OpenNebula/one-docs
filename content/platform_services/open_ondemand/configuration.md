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

This section describes how to configure the Open OnDemand Service: the inputs asked at instantiation, the size of the roles, the elasticity of the worker pool, additional worker sizes, an optional Slurm Cluster for batch jobs, an external identity provider and the management of users.

## Service Inputs

The service template asks for the following inputs. All of them are `ONEAPP_*` context variables, and OneFlow places every one of them in the context of every VM of the service.

| Input | Default | Description |
|---|---|---|
| `ONEAPP_POOL_RANGE` | `172.20.0.50-172.20.0.249` | **Required**. The address range the compute Virtual Network assigns to VMs, as `first-last`. |
| `ONEAPP_OOD_SERVERNAME` | empty | Public host name of the portal. It has to resolve to the management address of the portal VM. Empty makes the portal answer on that address. |
| `ONEAPP_OOD_SSL_MODE` | `selfsigned` | `selfsigned`, `letsencrypt` or `custom`. See [TLS Certificates](#tls-certificates). |
| `ONEAPP_OOD_SSL_CERT` | empty | PEM certificate chain for the `custom` mode. Paste the file, the form encodes it. |
| `ONEAPP_OOD_SSL_KEY` | empty | PEM private key for the `custom` mode. |
| `ONEAPP_LDAP_USERS` | `demo1:demo1pass:10001` | Initial users, as `user:password:uid` separated by spaces. |
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | How long the oldest worker stays empty before the pool loses a VM. |
| `ONEAPP_WORKER_MAX_SESSIONS` | `4` | Sessions a worker takes. The portal sends new sessions elsewhere at that count, and a pool whose workers are all at it grows. |
| `ONEAPP_SLURM_CONTROLLER` | empty | Compute address of a Slurm controller that shares the users and the home. See [Batch Jobs with Slurm](#batch-jobs-with-slurm). |
| `ONEAPP_OIDC_ISSUER` | empty | Issuer URL of an OpenID Connect provider. See [External Identity Provider](#external-identity-provider). |
| `ONEAPP_OIDC_CLIENT_ID` | empty | Client id registered at that provider. |
| `ONEAPP_OIDC_CLIENT_SECRET` | empty | Client secret registered at that provider. |
| `ONEAPP_OIDC_NAME` | `Institutional login` | Name of the provider on the login page. |
| `ONEAPP_NFS_SERVER` | empty | Address of an NFS server of your own for the home directories. Empty uses the storage role. See [Operations]({{% relref "platform_services/open_ondemand/operations/#keeping-the-home-directories" %}}). |
| `ONEAPP_NFS_EXPORT` | `/export/home` | Path of the home export, on the storage role or on that server. |

{{< alert title="Note" type="primary" >}}
OneFlow copies every service input into the context of every VM of the service, where root can read it. This includes `ONEAPP_OOD_SSL_KEY` and `ONEAPP_OIDC_CLIENT_SECRET`. Keep the service networks and the VM consoles restricted accordingly.
{{< /alert >}}

## Sizing the Roles

The marketplace template gives every VM 2 vCPU and 4 GB of memory, and 8 GB to the portal. A worker runs every session that lands on it inside one VM, so the worker role is the one to size for the load you expect: `ONEAPP_WORKER_MAX_SESSIONS` sessions share its CPU and memory. To change the size of a role, edit the service template before instantiating it, from **Templates -> Service Templates** in Sunstone or with `oneflow-template update`, and set `CPU`, `VCPU` and `MEMORY` in the `vm_template_contents` of the role:

```default
MEMORY = "16384"
VCPU = "8"
```

## Scaling the Worker Pool

The pool grows and shrinks on its own, as described in [How the Pool Grows and Shrinks]({{% relref "platform_services/open_ondemand/architecture/#how-the-pool-grows-and-shrinks" %}}). Two inputs tune it:

* `ONEAPP_WORKER_IDLE_SECONDS`: how long the oldest worker has to stay empty before OneFlow removes it. Ten minutes by default. A lower value returns capacity sooner, a higher one keeps a warm VM for the next user.
* `ONEAPP_WORKER_MAX_SESSIONS`: how many sessions a worker takes. When every worker is at that count the pool grows, and a new session waits for the new VM instead of overloading an existing one.

The role goes from 1 to 6 workers. Raise `max_vms` of the worker role in the service template for a larger pool. The pool shrinks one VM at a time, so a single long session keeps one worker, not six.

To change the pool by hand, see [Operations]({{% relref "platform_services/open_ondemand/operations/#scaling-the-pool-by-hand" %}}).

## Worker Sizes

Every role whose name starts with `worker` is a pool of session VMs. When the service has more than one, the application forms offer a **Worker size** field with the sizes that exist, `worker` shown as `Standard`:

{{< image path="/images/open_ondemand/light/jupyter_form_sizes.png"
alt="The Jupyter form offering two worker sizes" align="center" width="90%" mb="20px" >}}

To add a size, copy the `worker` role in the service template under a new name, `worker_large` for instance, with the CPU and memory you want and the same parents and elasticity policies. OneFlow accepts letters, digits and underscores in a role name. Each size grows and shrinks on its own and starts with at least one VM, because OneFlow scales a role from the metrics of its VMs and a role with no VM has none. A session asked for a size with no live worker falls back to the whole pool.

## GPU Workers

A worker role with a GPU is a `worker_gpu` role in the service template, as any other size, whose `vm_template_contents` also carries the PCI device of the Host, as the [NVIDIA GPU passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/" %}}) page describes:

```default
PCI = [ VENDOR = "10de", DEVICE = "<device id>", CLASS = "0302" ]
```

The session containers start through `/usr/local/bin/apptainer-gpu`, a wrapper that adds `--nv` to Apptainer when the VM has an NVIDIA device and its driver, so a session on such a worker sees the GPU. The image ships no NVIDIA driver, so the site installs it on the GPU role, with a customised image or at boot.

{{< alert title="Warning" type="warning" >}}
The GPU role was prepared without a GPU to test on. A site with one should run `nvidia-smi` inside a session before offering the size to users.
{{< /alert >}}

## Batch Jobs with Slurm

The VM pool has no scheduler. For a queue, a walltime and node accounting, attach the [Elastic Slurm]({{% relref "platform_services/slurm/" %}}) service from the marketplace. The portal then offers it as a second cluster in the Job Composer and in Active Jobs, while the interactive applications keep running on the pool. The Slurm Cluster shares the users and the home directory with the portal, so a job writes its output into the same home the notebooks use.

1. With the Open OnDemand Service running, note the compute addresses of its portal and storage VMs, the second address of each:

   ```shell
   onevm list -l ID,NAME,IP --filter NAME~service_<service_id>
   ```

2. Instantiate `OneSlurm` on the same compute network, with its local LDAP disabled and these inputs, where `<portal>` and `<storage>` are those addresses:

   ```default
   ONEAPP_LDAP_ENABLE      NO
   ONEAPP_LDAP_DOMAIN      ood.local
   ONEAPP_LDAP_URL         ldap://<portal>
   ONEAPP_SLURM_NFS_HOME   <storage>:/export/home
   ```

3. Once OneSlurm is `RUNNING`, give the portal the compute address of the Slurm controller. The portal reconfigures itself in under a minute and the cluster appears in the portal:

   ```shell
   onevm updateconf <portal vm id> --append <<EOT
   CONTEXT = [ ONEAPP_SLURM_CONTROLLER = "<controller compute address>" ]
   EOT
   ```

{{< image path="/images/open_ondemand/light/job_options_slurm.png"
alt="The Job Composer offering the Slurm cluster beside the OpenNebula VMs" align="center" width="90%" mb="20px" >}}

{{< image path="/images/open_ondemand/light/job_composer_slurm.png"
alt="A job submitted from the Job Composer and completed on the Slurm cluster" align="center" width="90%" mb="20px" >}}

`ONEAPP_SLURM_CONTROLLER` is also a service input, for a controller that exists before the service does. The portal installs no Slurm client. `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on the controller over SSH as the user, with the key the portal keeps in each user's home. Accounting history in `sacct` depends on OneSlurm running `slurmdbd`, which its default deployment does not.

## External Identity Provider

With `ONEAPP_OIDC_ISSUER`, `ONEAPP_OIDC_CLIENT_ID` and `ONEAPP_OIDC_CLIENT_SECRET` set, the login page offers the provider beside the local directory, through the OpenID Connect connector of Dex. Register `https://<ONEAPP_OOD_SERVERNAME>/dex/callback` as the redirect URI at the provider. A user who signs in that way still needs an account in the LDAP directory under the same name, the `preferred_username` claim or the part of the email before the at sign, because a session runs as a Unix user with a home directory.

{{< alert title="Warning" type="warning" >}}
The connector was written without a provider to test against. A site enabling it should check one login before announcing it.
{{< /alert >}}

## TLS Certificates

`ONEAPP_OOD_SSL_MODE` selects how the portal gets its certificate:

* `selfsigned`: The portal generates its own certificate at first boot. Browsers ask to accept it. This is the default and needs nothing else.
* `letsencrypt`: The portal requests a certificate from Let's Encrypt for `ONEAPP_OOD_SERVERNAME`. The name has to be public, resolve to the management address of the portal, and port 80 has to be reachable from the Internet for the validation.
* `custom`: The portal installs the certificate chain and key given in `ONEAPP_OOD_SSL_CERT` and `ONEAPP_OOD_SSL_KEY`.

The mode and the name can be changed on a running portal with `onevm updateconf`, as in the Slurm example above. The portal reconfigures itself when its context changes.

## Managing Users

Users live in the LDAP directory of the portal role, and adding one is one entry in it. The portal generates the administrator password of the directory when it first configures itself and keeps it in `/etc/one-ondemand/ldap-admin.pass`, readable by root only. On the portal VM:

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

Generate the password hash with `slappasswd -h '{SSHA}' -s <password>`. The new user can sign in right away, and their home directory is created on first login. The workers resolve users against the same directory, so nothing has to be done on them.
