---
title: "OpenNebula Systems Marketplace"
linkTitle: "Enterprise Marketplace"
date: "2025-02-17"
description:
categories:
pageintoc: "186"
tags:
weight: "2"
---

<a id="market-one"></a>

<!--# OpenNebula Systems Marketplace -->

OpenNebula maintains two appliance marketplaces:

- The [Public OpenNebula Marketplace](http://marketplace.opennebula.io), with appliances maintained by OpenNebula Systems.
- The [Community Marketplace](http://community-marketplace.opennebula.io), with appliances maintained by external contributors.

## Configuration Attributes

| Attribute    | Description                                             |
|--------------|---------------------------------------------------------|
| `NAME`       | The name of the Marketplace. Default: OpenNebula Public |
| `MARKET_MAD` | `one`                                                   |
| `ENDPOINT`   | The Marketplace endpoint URL                            |

For instructions on adding the OpenNebula Community Marketplace to your OpenNebula installation, please see the [OpenNebula Community Marketplace Wiki](https://github.com/OpenNebula/marketplace-community/wiki/marketplace_start).

## Access Through an HTTP Proxy

To use a proxy, set `HTTP_PROXY` in the OpenNebula service environment or add `--proxy http://username:password@proxy.example.com:8080` to the `MARKET_MAD` arguments in [oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#marketplace-driver-configuration" %}}). The `--proxy` option takes precedence over the environment variable.
