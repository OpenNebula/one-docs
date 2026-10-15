---
title: "Port Mirroring"
linkTitle: "Port Mirroring"
date: "2026-10-05"
description: "Capture Virtual Machine network traffic with Open vSwitch mirrors."
categories:
tags:
weight: "12"
---

<a id="port-mirroring"></a>

Port mirroring copies selected Virtual Machine traffic to a monitoring destination without changing the original traffic flow. Use it for packet capture, troubleshooting, or traffic analysis.

Mirrors belong to a Virtual Network and are supported only by the `ovswitch` and `ovswitch_vxlan` network drivers. Open vSwitch must be installed on every participating Host. Create the Virtual Network first, then configure mirrors with the dedicated `onevnet mirror-*` commands.

## Mirror Types and Requirements

| Type    | Destination                                                     | Requirements |
|---------|-----------------------------------------------------------------|--------------|
| `SPAN`  | A collector VM NIC on the same Open vSwitch bridge.             | Source and destination NICs must belong to the same Virtual Network. Deployed source and collector VMs must be on the same Host and bridge. The collector NIC cannot also be a source port. |
| `RSPAN` | A dedicated output VLAN.                                        | Provision the VLAN transport and collector on the physical network. OpenNebula does not configure external switches. |
| `GRE`   | A remote IPv4 collector, using a GRE tunnel.                    | Provide IP connectivity from each source Host to the collector and allow GRE traffic through intervening firewalls. |
| `ERSPAN`| A remote IPv4 collector, using an ERSPAN type II or III tunnel. | The installed Open vSwitch and collector must support the selected ERSPAN type. Provide IP connectivity and allow GRE traffic. |

For `SPAN`, use a dedicated collector NIC in promiscuous mode. Open vSwitch reserves the mirror output port for mirrored traffic; use a separate NIC for collector management. Keep the collector and sources on the same Host when scheduling or migrating VMs.

### Permissions

Mirror operations require `ADMIN` permission on the Virtual Network. Configuring sources and a `SPAN` destination also requires `ADMIN` permission on the referenced VMs. A VLAN-only mirror can only be configured by a cloud administrator because its capture is bridge-wide, rather than limited to explicitly authorized VM ports.

## Mirror Template

Creation and update templates contain exactly one `MIRROR` vector. Names are mandatory, and unknown attributes are rejected. `MIRROR_ID` is assigned by OpenNebula and identifies the mirror within its Virtual Network.

### Common Attributes

| Attribute     | Description                                    |
|---------------|------------------------------------------------|
| `NAME`        | Required, nonempty mirror name.                |
| `TYPE`        | Required: `SPAN`, `RSPAN`, `GRE`, or `ERSPAN`. |
| `DIRECTION`   | `IN`, `OUT`, or `BOTH`; default `BOTH`. Direction is relative to the source VM, `OUT` copies packets sent by the VM|
| `PORTS`       | Optional comma-separated `VM_ID:NIC_ID` pairs. Duplicates are removed. After creation, change membership with `mirror-addport` and `mirror-delport`. |
| `VLANS`       | Optional comma-separated VLAN IDs from `0` to `4094`. Ranges are not accepted. Duplicates are removed. |
| `DESCRIPTION` | Optional description.                          |

### Destination Attributes

Only include attributes applicable to the selected type.

| Type               | Attribute            | Mandatory | Description       |
|--------------------|----------------------|-----------|-------------------|
| `SPAN`             | `DESTINATION_VM_ID`  | Yes       | Collector VM ID.  |
| `SPAN`             | `DESTINATION_NIC_ID` | Yes       | Collector NIC ID. |
| `RSPAN`            | `OUTPUT_VLAN`        | Yes       | Output VLAN, from `1` to `4094`. Use a dedicated VLAN for mirrored traffic. |
| `GRE`, `ERSPAN`    | `REMOTE_IP`          | Yes       | Collector IPv4 address; hostnames and IPv6 addresses are not accepted. |
| `GRE`, `ERSPAN`    | `LOCAL_IP`           | Optional  | Source IPv4 address on the hypervisor, or an interface reference such as `interface:ovsbr0`. If omitted, routing determines the source address. |
| `ERSPAN`           | `ERSPAN_TYPE`        | Yes       | `II` or `III`.    |
| `ERSPAN`           | `ERSPAN_KEY`         | Yes       | Session identifier, from `0` to `1023`. |
| `ERSPAN` type `II` | `ERSPAN_INDEX`       | Optional  | Index, from `0` to `1048575`; default `0`. Not valid for type `III`. |
| `ERSPAN` type `III`| `ERSPAN_HWID`        | Optional  | Hardware identifier, from `0` to `63`; default `0`. Not valid for type `II`. |

An interface referenced by `LOCAL_IP` must exist on each participating Host and have exactly one usable IPv4 address. Resolution occurs on the hypervisor when the driver applies the mirror.

For example, a local collector mirror:

```default
MIRROR = [
    NAME = "local-capture",
    TYPE = "SPAN",
    DIRECTION = "BOTH",
    PORTS = "210:1",
    DESTINATION_VM_ID = "211",
    DESTINATION_NIC_ID = "1"
]
```

For a remote collector using ERSPAN type II:

```default
MIRROR = [
    NAME = "remote-capture",
    TYPE = "ERSPAN",
    PORTS = "210:1",
    REMOTE_IP = "198.51.100.20",
    ERSPAN_TYPE = "II",
    ERSPAN_KEY = "10",
    ERSPAN_INDEX = "0"
]
```

## Selecting Traffic

A source port is identified by `VM_ID:NIC_ID`, for example `210:1`. Obtain NIC IDs with `onevm show`. Source NICs must belong to the mirror's Virtual Network.

| `PORTS`  | `VLANS`  | Captured traffic |
|----------|----------|------------------|
| Nonempty | Empty    | Traffic on the selected VM NICs, without a VLAN filter. |
| Nonempty | Nonempty | Traffic on the selected VM NICs that also matches the VLAN filter. |
| Empty    | Nonempty | Traffic matching the VLAN filter across the participating Open vSwitch bridges. This uses bridge-wide selection, including other networks sharing a bridge. |
| Empty    | Empty    | No traffic; the mirror is inactive. |

{{< alert title="Warning" type="warning" >}}
Removing the last source port stops capture only if `VLANS` is also empty. With a nonempty VLAN filter, the mirror becomes VLAN-only instead. Delete the mirror to stop all capture, or clear its VLAN filter before removing the last port.
{{< /alert >}}

## Managing Mirrors

The examples below use Virtual Network `5` and mirror `0`; replace these IDs with your own.

```bash
# Create from a file, or supply the template on standard input.
onevnet mirror-create 5 mirror.txt
onevnet show 5

# Open the editor with the current mirror configuration.
onevnet mirror-update 5 0

# Replace the configuration from a file, or merge supplied attributes.
onevnet mirror-update 5 0 mirror.txt
onevnet mirror-update 5 0 changes.txt --append

# Add or remove one or more source NICs.
onevnet mirror-addport 5 0 210:1,212:0
onevnet mirror-delport 5 0 212:0

# Remove the mirror and its capture configuration.
onevnet mirror-delete 5 0
```

Mirrors cannot be introduced through `onevnet create`, `onevntemplate create`, or `onevntemplate instantiate`. General `onevnet update` cannot modify mirror definitions; use the dedicated commands. OpenNebula manages the `MIRROR_IDS` and `MIRROR_*` NIC attributes, which are not editable through `onevm nic-update`.

### Applying Changes to Running VMs

Mirror changes propagate asynchronously through the existing Virtual Network update action. Inspect `onevnet show` for the network state and its updated, outdated, and failed VM lists. Wait for the affected VMs to be updated before checking packet capture. A successful API response alone does not mean the hypervisor has finished applying the change.

If an update fails, inspect the VM and driver logs, correct connectivity or Host configuration, then retry:

```bash
onevnet recover 5 --retry
```
