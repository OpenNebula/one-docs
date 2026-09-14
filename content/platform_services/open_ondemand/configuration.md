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
| `ONEAPP_OOD_SSL_KEY` | empty | PEM private key for the `custom` mode. The service template passes it to the portal VM only. |
| `ONEAPP_LDAP_USERS` | `demo1:demo1pass:10001` | Initial users, as `user:password:uid` separated by spaces. |
| `ONEAPP_WORKER_IDLE_SECONDS` | `600` | How long the oldest worker stays empty before the pool loses a VM. |
| `ONEAPP_SLURM_CONTROLLER` | empty | Compute address of a Slurm controller that shares the users and the home. |
| `ONEAPP_POOL_RANGE` | `172.20.0.50-172.20.0.249` | The address range the compute network assigns to VMs, `first-last`. |
| `ONEAPP_NFS_SERVER` | empty | Address of an NFS server of your own for the home. Empty uses the storage role. |
| `ONEAPP_NFS_EXPORT` | `/export/home` | Path of the home export, on the storage role or on that server. |

## Scaling the worker pool

The pool grows and shrinks on its own. Every worker reports its open session count to OneGate, OneFlow adds a VM when the average passes one session per worker, and removes one when the oldest worker has been empty for `ONEAPP_WORKER_IDLE_SECONDS`, ten minutes by default. It shrinks one VM at a time, so a single long session keeps one worker, not six. OneFlow always removes the oldest VM of the role, so a long session on the oldest worker holds the pool at its size until it ends. To change the pool by hand:

```shell
$ oneflow scale <service_id> worker <cardinality>
```

The role accepts from 1 to 6 workers. Raise `max_vms` in the service template for a larger pool.

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
