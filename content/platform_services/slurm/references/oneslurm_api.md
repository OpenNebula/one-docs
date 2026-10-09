---
title: "OneSlurm API"
linkTitle: "API"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "4"
---

OneSlurm has no API of its own. A OneSlurm cluster is a OneFlow service, so you create, scale and delete it with the [OneFlow Server API]({{% relref "product/integration_references/system_interfaces/appflow_api" %}}). This page shows the calls relevant to OneSlurm.

| **Item** | **Value** |
|---|---|
| Endpoint | `http://<FRONT_END_IP>:2474` |
| Authentication | HTTP Basic, with an OpenNebula user and password |
| Format | JSON |

The examples use these variables.

```shell
FLOW=http://localhost:2474
AUTH='oneadmin:<password>'
```

## Find the Service Template

```shell
curl -s -u "$AUTH" $FLOW/service_template
```

The response lists the service templates in `DOCUMENT_POOL.DOCUMENT`. Take the `ID` of the one named `Service OneSlurm`.

## Create a Cluster

```shell
curl -s -u "$AUTH" -X POST -H 'Content-Type: application/json' \
    $FLOW/service_template/<template_id>/action -d '{
  "action": {
    "perform": "instantiate",
    "params": {
      "merge_template": {
        "name": "oneslurm-api",
        "networks_values": [ { "Service": { "id": "2" } } ],
        "user_inputs_values": {
          "ONEAPP_LDAP_ENABLE": "YES",
          "ONEAPP_LDAP_DOMAIN": "slurm.local",
          "ONEAPP_LDAP_ADMIN_USER": "",
          "ONEAPP_LDAP_ADMIN_PASSWORD": "",
          "ONEAPP_LDAP_URL": "",
          "ONEAPP_LDAP_BIND_USER": "",
          "ONEAPP_LDAP_BIND_PASSWORD": "",
          "ONEAPP_SLURM_INFINIBAND_ENABLE": "NO",
          "ONEAPP_SLURM_IPOIB_SUBNET": "",
          "ONEAPP_SLURM_NFS_HOME": "",
          "ONEAPP_SLURM_NFS_SCRATCH": ""
        }
      }
    }
  }
}'
```

* `networks_values` sets the `Service` network. Replace `2` with the ID of your Virtual Network.
* `user_inputs_values` must contain **all** the service inputs, also the empty ones. Otherwise the API answers `Verify that every User Input have its corresponding value defined`.
* The response is the new service. Its ID is in `DOCUMENT.ID`.

Refer to [Configuration Parameters]({{% relref "platform_services/slurm/references/configuration_parameters" %}}) for a description of each input.

## Check the Cluster

```shell
curl -s -u "$AUTH" $FLOW/service/<service_id>
```

The state of the service is in `DOCUMENT.TEMPLATE.BODY.state`, and the roles with their VMs in `DOCUMENT.TEMPLATE.BODY.roles`.

| `state` | **Meaning** |
|---|---|
| `1` | Deploying |
| `2` | Running |
| `8` | Scaling |
| `10` | Cooldown |

## Change the Number of Workers

```shell
$ curl -s -u "$AUTH" -X POST -H 'Content-Type: application/json' \
    $FLOW/service/<SERVICE_ID>/scale \
    -d '{ "role_name": "worker", "cardinality": 2, "force": false }'
```

* The API answers `204` when it accepts the request.
* Always send `force`. Without it, the API answers `500`.
* The service goes through `Scaling` and `Cooldown` and returns to `Running`. The new workers join Slurm on their own.

## Delete the Cluster

```shell
curl -s -u "$AUTH" -X DELETE $FLOW/service/<SERVICE_ID>
```

The API answers `204`. You cannot delete the service during the cooldown after a scale operation.
