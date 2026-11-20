---
title: "BlueCat IPAM Integration"
linkTitle: "BlueCat IPAM"
date: "2026-11-20"
description: "Integration of OpenNebula with BlueCat Address Manager through the IPAM driver."
categories:
tags:
weight: "3"
aliases:
---

## Overview

The BlueCat IPAM integration allows OpenNebula to manage IP address allocations through BlueCat Address Manager (BAM) using its REST API v2.

The integration uses OpenNebula's external IPAM driver interface to coordinate IP address reservations between OpenNebula Virtual Networks and BlueCat.

The driver supports:

- Registering OpenNebula Address Ranges (ARs) using existing BlueCat networks.
- Dynamic allocation of available IP addresses.
- Reservation of specific IP addresses.
- Releasing IP address reservations when they are no longer needed.
- Preserving existing BlueCat networks when OpenNebula Address Ranges are removed.

For more information about the external IPAM interface, see the [IPAM Driver]({{% relref "product/integration_references/infrastructure_drivers_development/devel-ipam" %}}) documentation.

## Prerequisites

Before configuring the integration, ensure that:

- A BlueCat Address Manager instance with REST API v2 is available.
- The OpenNebula Front-end can communicate with the BlueCat API endpoint.
- A BlueCat API account with permissions to manage IP address reservations is available.
- The `curl` and `jq` packages are installed on the OpenNebula Front-end.
- An existing BlueCat network is available for integration.

The recommended configuration uses an existing BlueCat network identified by `BLUECAT_NETWORK_ID`.

## Installation

The driver source code is available in the [OpenNebula repository](https://github.com/OpenNebula/one/tree/d36e93c/src/ipamm_mad/remotes/bluecat). Ensure that the driver is available in your OpenNebula installation before proceeding with the configuration.

The driver files must be installed in the following directory on the OpenNebula Front-end:

```text
/var/lib/one/remotes/ipam/bluecat/
```

The driver requires the following files:

```text
common.sh
register_address_range
unregister_address_range
get_address
allocate_address
free_address
```

Ensure that the driver files are accessible to the `oneadmin` user and that the action scripts are executable.

For example, from the driver directory:

```bash
chown oneadmin:oneadmin \
  register_address_range unregister_address_range \
  get_address allocate_address free_address common.sh

chmod 770 \
  register_address_range unregister_address_range \
  get_address allocate_address free_address

chmod 660 common.sh
```

For HA deployments, install the same driver version and configuration on every Front-end node that can become the active leader.

## Configuration

### BlueCat Connection

Create the configuration file:

```text
/etc/one/bluecat_ipam.conf
```

Example configuration:

```bash
BLUECAT_MOCK=no
BLUECAT_URL=https://bluecat.example.com
BLUECAT_USER=api-user
BLUECAT_PASS=api-password
BLUECAT_VERIFY_TLS=yes
BLUECAT_UNREGISTER_ACTION=keep
BLUECAT_NETWORK_ID=12345
```

The main configuration parameters are:

| Parameter | Description |
|---|---|
| `BLUECAT_URL` | BlueCat BAM REST API endpoint. |
| `BLUECAT_USER` | Username used for API authentication. |
| `BLUECAT_PASS` | Password used for API authentication. |
| `BLUECAT_VERIFY_TLS` | Enables TLS certificate verification. Defaults to `yes`. |
| `BLUECAT_NETWORK_ID` | Identifier of an existing BlueCat network. |
| `BLUECAT_UNREGISTER_ACTION` | Controls network removal behavior. The recommended value is `keep`. |
| `BLUECAT_MOCK` | Enables testing without connecting to BlueCat when set to `yes`. |

Additional configuration options include `BLUECAT_PARENT_BLOCK_ID`, `BLUECAT_BLOCK_ID`, and `BLUECAT_NETWORK_NAME` for network creation.

Network creation and deletion require validation against the BlueCat environment and its network management policies.

Protect the configuration file because it contains API credentials:

```bash
chown root:oneadmin /etc/one/bluecat_ipam.conf
chmod 640 /etc/one/bluecat_ipam.conf
```

### Enable the IPAM Driver

Edit `/etc/one/oned.conf` and add `bluecat` to the list of enabled IPAM drivers.

For example:

```text
IPAM_MAD = [
    EXECUTABLE = "one_ipam",
    ARGUMENTS  = "-t 1 -i dummy,bluecat"
]
```

Preserve any existing IPAM drivers in the configuration.

Restart the OpenNebula service to apply the changes:

```bash
systemctl restart opennebula
```

Verify that the IPAM driver is running with BlueCat enabled:

```bash
ps -ef | grep '[o]ne_ipam'
```

The driver arguments should include `bluecat`.

In an HA deployment, maintain consistent IPAM configuration across Front-end nodes while preserving node-specific HA settings.

### Virtual Network Configuration

To use BlueCat for IP address allocation, configure an OpenNebula Virtual Network with an Address Range using the `bluecat` IPAM driver.

For example:

```text
NAME = "BlueCat Network"

BRIDGE  = "br0"
VN_MAD  = "dummy"

AR = [
    TYPE               = "IP4",
    IP                 = "192.168.100.10",
    SIZE               = "100",
    IPAM_MAD           = "bluecat",
    BLUECAT_NETWORK_ID = "12345"
]
```

Replace the network settings, address range, and BlueCat network identifier with values appropriate for your environment. BlueCat manages IP address reservations but does not configure the underlying virtual networking.

The `BLUECAT_NETWORK_ID` can be specified in the Address Range or configured as a default in `/etc/one/bluecat_ipam.conf`.

When a VM requests an IP address from this network, OpenNebula delegates the allocation to the BlueCat IPAM driver.

## Verification

After configuring the integration, verify the following operations:

1. Create an OpenNebula Address Range associated with an existing BlueCat network.
2. Instantiate a VM using the configured Virtual Network and verify that its IP address is reserved in BlueCat.
3. Reserve a specific address using `onevnet hold` and verify the reservation in BlueCat.
4. Release the address using `onevnet release` and verify that it becomes available again.
5. Terminate the VM and verify that its IP reservation is released.
6. Remove the Address Range and confirm that the BlueCat network is preserved when `BLUECAT_UNREGISTER_ACTION=keep` is configured.

The driver logs operations to `/tmp/bluecat-ipam.log` by default. The log path can be overridden using the `BLUECAT_LOG` environment variable.

## Limitations

The current integration has the following limitations:

- IP address allocation is designed primarily for individual addresses. Multi-address reservations are not fully supported.
- Creating or deleting BlueCat networks requires additional validation against the target environment.
- The recommended `BLUECAT_UNREGISTER_ACTION=keep` configuration preserves existing BlueCat networks.
- The driver does not provide background reconciliation between existing OpenNebula leases and BlueCat reservations.
- Available addresses must be reported as `UNASSIGNED` by BlueCat.
- Each driver action establishes a new API session; persistent session caching and automatic reauthentication are not implemented.

The integration has been validated against a BlueCat BAM REST API v2 environment. Compatibility with other BlueCat versions and site-specific configurations should be verified before production deployment.
