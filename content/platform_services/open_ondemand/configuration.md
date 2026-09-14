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
| `ONEAPP_OOD_SSL_MODE` | `selfsigned` | `selfsigned` or `letsencrypt`. Let's Encrypt needs the host name to be public and port 80 reachable. |
| `ONEAPP_LDAP_USERS` | `demo1:demo1pass:10001` | Initial users, as `user:password:uid` separated by spaces. |
| `ONEAPP_PORTAL_IP` | `172.20.0.60` | Fixed address of the portal on the compute network. |
| `ONEAPP_COMPUTE_NET` | `172.20.0.0/24` | The compute network in CIDR notation. |
| `ONEAPP_POOL_RANGE` | `172.20.0.230-172.20.0.249` | Address range reserved for the workers, `first-last`, inside the compute network. |

## Scaling the worker pool

The pool grows and shrinks on its own. Every worker reports its open session count to OneGate, OneFlow adds a VM when the average passes one session per worker, and removes one after three minutes with every worker empty. To change the pool by hand:

```shell
$ oneflow scale <service_id> worker <cardinality>
```

The role accepts from 1 to 6 workers. Raise `max_vms` in the service template for a larger pool.

## Users

Users live in the LDAP directory of the portal role, and adding one is one entry in it. On the portal VM, with the administrator password that `/etc/sssd/sssd.conf` holds as `ldap_default_authtok`:

```shell
$ ldapadd -x -D cn=admin,dc=ood,dc=local -W <<EOF
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
