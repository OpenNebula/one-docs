---
title: "Identity Management"
linkTitle: "Identity"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "4"
---

A user needs the same account, with the same UID and GID, on the controller and on every worker. OneSlurm gets these accounts from an LDAP directory, through SSSD on each VM.

## Identity Modes

Choose one mode when you create the service.

| **Mode** | **Inputs** | **What the appliance does** |
|---|---|---|
| Disabled (default) | Leave the LDAP inputs empty | No LDAP. SSSD is stopped. Only local Linux users exist |
| Local LDAP | `ONEAPP_LDAP_ENABLE=YES` | Installs OpenLDAP on the controller and connects the controller and the workers to it |
| External LDAP | `ONEAPP_LDAP_URL` and `ONEAPP_LDAP_DOMAIN` | Connects the controller and the workers to your LDAP server |

With `ONEAPP_LDAP_ENABLE=YES`, the appliance ignores `ONEAPP_LDAP_URL`.

The controller decides the mode. It publishes the LDAP settings in OneGate, and the workers use them. The workers ignore their own LDAP inputs.

## LDAP Inputs

| **Parameter** | **Default** | **Description** |
|---|---|---|
| `ONEAPP_LDAP_ENABLE` | `NO` | `YES` installs a local LDAP server on the controller |
| `ONEAPP_LDAP_DOMAIN` | `slurm.local` | LDAP domain or base DN |
| `ONEAPP_LDAP_ADMIN_USER` | empty, the appliance uses `admin` | Admin of the local LDAP, as a name or a DN |
| `ONEAPP_LDAP_ADMIN_PASSWORD` | empty | Password of the local LDAP admin. Empty means the admin can only work as root on the controller |
| `ONEAPP_LDAP_URL` | empty | URL of an external LDAP server, for example `ldap://10.0.0.5` |
| `ONEAPP_LDAP_BIND_USER` | empty | User to read the external LDAP, as a name or a DN. Empty means anonymous read |
| `ONEAPP_LDAP_BIND_PASSWORD` | empty | Password of the bind user |

### Domain and Base DN

The base DN is the top entry of the directory. OneSlurm builds it from `ONEAPP_LDAP_DOMAIN`.

| **Domain input** | **s** |
|---|---|
| `slurm.local` | `dc=slurm,dc=local` |
| `dc=example,dc=org` | `dc=example,dc=org` |

* A domain such as `slurm.local` becomes one `dc=` part for each word.
* A value with `=` is already a base DN and is used without changes.
* Users must be in `ou=People,<base DN>` and groups in `ou=Groups,<base DN>`.
* A user name without `=`, such as `admin`, becomes `cn=admin,<base DN>`.

## Local LDAP

With `ONEAPP_LDAP_ENABLE=YES`, the controller creates the base DN, `ou=People` and `ou=Groups`. The directory is empty. Add users and groups as root on the controller.

This example adds the user `alice` with UID and GID `10001`.

```shell
$ ldapadd -Y EXTERNAL -H ldapi:/// -Q <<EOF
dn: cn=alice,ou=Groups,dc=slurm,dc=local
objectClass: posixGroup
cn: alice
gidNumber: 10001

dn: uid=alice,ou=People,dc=slurm,dc=local
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: alice
cn: Alice
sn: Example
uidNumber: 10001
gidNumber: 10001
homeDirectory: /home/alice
loginShell: /bin/bash
userPassword: $(slappasswd -s '<password>')
EOF
```

Check the user on the controller and on a worker:

```shell
getent passwd alice
srun -N1 -n1 getent passwd alice
```

If `/home` is an NFS export, create the home directory once, on the NFS server, owned by the user. With the default `root_squash` export option, root on the controller cannot create it.

```shell
install -d -m 700 -o 10001 -g 10001 /srv/nfs/slurm/home/alice    # on the NFS server
```

{{< alert title="Important" type="warning" >}}
The local LDAP lives inside the controller VM. Deleting the service deletes all its users. For production, it is recommended to use an external LDAP.
{{< /alert >}}

## External LDAP

Set `ONEAPP_LDAP_URL` and `ONEAPP_LDAP_DOMAIN`. Your directory must have users in `ou=People,<base DN>` and groups in `ou=Groups,<base DN>`, with POSIX attributes (`uidNumber`, `gidNumber`, `homeDirectory`).

If the directory does not allow anonymous reads, also set `ONEAPP_LDAP_BIND_USER` and `ONEAPP_LDAP_BIND_PASSWORD`.

## Security

| **Topic** | **Behavior** |
|---|---|
| Encryption | SSSD connects with plain `ldap://`, without StartTLS, and does not check certificates. Keep the LDAP traffic on a private network |
| Bind password | The controller publishes `LDAP_BIND_PASSWORD` in OneGate, so the workers can read it. Any VM of the service can read it too |
| Loopback URL | Workers refuse an LDAP URL that points to `127.0.0.1` or `localhost` |
