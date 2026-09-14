---
title: "Configuration"
linkTitle: "Configuration"
weight: 3
type: docs
---

## Service inputs

| Parameter | Default | Description |
|---|---|---|
| `ONEAPP_OOD_SERVERNAME` | empty | Public host name of the portal. It has to resolve to the management address of the portal VM. Empty makes the portal answer on that address. |
| `ONEAPP_OOD_SSL_MODE` | `selfsigned` | `selfsigned`, `letsencrypt` or `custom`. Let's Encrypt needs the host name to be public and port 80 reachable. `custom` installs the certificate given in the next two inputs. |
| `ONEAPP_OOD_SSL_CERT` | empty | PEM certificate chain for the `custom` mode. Paste the file, the form encodes it. |
| `ONEAPP_OOD_SSL_KEY` | empty | PEM private key for the `custom` mode. OneFlow puts every service input in the context of every VM of the service, where root can read it. |
| `ONEAPP_LDAP_USERS` | `demo1:demo1pass:10001` | Initial users, as `user:password:uid` separated by spaces. |
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | How long the oldest worker stays empty before the pool loses a VM. |
| `ONEAPP_WORKER_MAX_SESSIONS` | `4` | Sessions a worker takes. The portal sends new sessions elsewhere at that count, and a pool whose workers are all at it grows. |
| `ONEAPP_SLURM_CONTROLLER` | empty | Compute address of a Slurm controller that shares the users and the home. |
| `ONEAPP_OIDC_ISSUER`, `ONEAPP_OIDC_CLIENT_ID`, `ONEAPP_OIDC_CLIENT_SECRET`, `ONEAPP_OIDC_NAME` | empty | An OpenID Connect provider on the login page, see below. |
| `ONEAPP_POOL_RANGE` | `172.20.0.50-172.20.0.249` | The address range the compute network assigns to VMs, `first-last`. |
| `ONEAPP_NFS_SERVER` | empty | Address of an NFS server of your own for the home. Empty uses the storage role. |
| `ONEAPP_NFS_EXPORT` | `/export/home` | Path of the home export, on the storage role or on that server. |

## Scaling the worker pool

The pool grows and shrinks on its own. Every worker reports its open session count to OneGate, OneFlow adds a VM when the average passes one session per worker or when every worker holds `ONEAPP_WORKER_MAX_SESSIONS` sessions, and removes one when the oldest worker has been empty for `ONEAPP_WORKER_IDLE_SECONDS`, ten minutes by default. It shrinks one VM at a time, so a single long session keeps one worker, not six. OneFlow always removes the oldest VM of the role, so a long session on the oldest worker holds the pool at its size until it ends. To change the pool by hand:

```shell
$ oneflow scale <service_id> worker <cardinality>
```

The role accepts from 1 to 6 workers. Raise `max_vms` in the service template for a larger pool.

## Worker sizes

Every role whose name starts with `worker` is a pool of session VMs, and the portal offers the sizes that exist as a "Worker size" field in each application form, with `worker` as `Standard`. To add a larger size, copy the `worker` role in the service template under a new name, `worker_large` for instance, with the CPU and memory you want and the same parents and elasticity policies. Each size grows and shrinks on its own and starts with at least one VM, because OneFlow scales a role from its metrics and a role with no VM has none. A session asked for a size with no live worker falls back to the whole pool.

## GPU workers, prepared

A worker role with a GPU is a `worker_gpu` role in the service template, as any other size, whose `vm_template_contents` also carries the PCI device of the host,
as the [NVIDIA GPU passthrough](https://docs.opennebula.io/7.4/product/cluster_configuration/pci_passthrough_sriov/nvidia_gpu_passthrough/)
page describes:

```text
PCI = [ VENDOR = "10de", DEVICE = "<device id>", CLASS = "0302" ]
```

The session containers run through `/usr/local/bin/apptainer-gpu`, which adds `--nv` when the VM has an NVIDIA device and its driver, so a session on such a worker sees the GPU. The
image ships no NVIDIA driver, so the site installs it on the GPU role, with a customised
image or at boot. This was prepared without a GPU to test on, and a site with one should
run `nvidia-smi` inside a session before offering the size to users.

## Batch jobs with Slurm

The VM pool has no scheduler. For a queue, a walltime and node accounting, attach the official OneSlurm service from the marketplace and the portal offers it as a second cluster in the Job Composer and in Active Jobs, while the interactive applications keep running on the pool. The Slurm cluster shares the users and the home with the portal, so nothing is copied and a job writes its output into the same home the notebooks use.

1. With the Open OnDemand service running, note the compute addresses of its portal and storage VMs:

   ```shell
   $ onevm list -f NAME~service_<service_id> -l ID,NAME,IP
   ```

2. Instantiate `OneSlurm` on the same compute network, with the local LDAP disabled and these inputs, where `<portal>` and `<storage>` are those addresses:

   ```text
   ONEAPP_LDAP_ENABLE      NO
   ONEAPP_LDAP_DOMAIN      ood.local
   ONEAPP_LDAP_URL         ldap://<portal>
   ONEAPP_SLURM_NFS_HOME   <storage>:/export/home
   ```

3. Once OneSlurm is `RUNNING`, give the portal the address of the controller. The portal reconfigures itself in under a minute and the cluster appears:

   ```shell
   $ onevm updateconf <portal vm id> --append <<EOF
   CONTEXT = [ ONEAPP_SLURM_CONTROLLER = "<controller compute address>" ]
   EOF
   ```

{{< image path="/images/open_ondemand/light/job_options_slurm.png"
alt="The Job Composer offering the Slurm cluster beside the OpenNebula VMs" align="center" width="90%" mb="20px" >}}

{{< image path="/images/open_ondemand/light/job_composer_slurm.png"
alt="A job submitted from the Job Composer and completed on the Slurm cluster" align="center" width="90%" mb="20px" >}}

`ONEAPP_SLURM_CONTROLLER` is also a service input, for a controller that exists before the service does. The portal installs no Slurm client: `sbatch`, `squeue`, `scancel`, `sinfo`, `sacct` and `scontrol` run on the controller over SSH as the user, with the key the portal keeps in each user's home. Accounting history in `sacct` depends on OneSlurm running `slurmdbd`, which its default deployment does not.

## An external identity provider

With `ONEAPP_OIDC_ISSUER`, `ONEAPP_OIDC_CLIENT_ID` and `ONEAPP_OIDC_CLIENT_SECRET` set, the login page offers the provider beside the local directory, through the OpenID Connect connector of Dex, with `https://<ONEAPP_OOD_SERVERNAME>/dex/callback` as the redirect URI to register at the provider. A user who signs in that way still needs an account in the directory under the same name, the `preferred_username` claim or the part of the email before the at sign, because a session runs as a Unix user with a home. This was written without a provider to test against, so a site enabling it checks one login first.

## Users

Users live in the LDAP directory of the portal role, and adding one is one entry in it. The portal generates the administrator password of the directory when it first configures itself and keeps it in `/etc/one-ondemand/ldap-admin.pass`, readable by root only. On the portal VM:

```shell
$ ldapadd -x -D cn=admin,dc=ood,dc=local -y /etc/one-ondemand/ldap-admin.pass <<EOF
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
EOF
```

Generate the password hash with `slappasswd -h '{SSHA}' -s <password>`. The new user can sign in right away, and their home is created on first login.
