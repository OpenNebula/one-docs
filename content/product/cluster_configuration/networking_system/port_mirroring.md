---
title: "Port Mirroring"
linkTitle: "Port Mirroring"
date: "2026-10-05"
categories:
tags:
weight: "12"
---

<a id="port-mirroring"></a>

Port mirroring copies selected Virtual Machine traffic to a monitoring destination without changing the original traffic flow. It can be used for packet capture, troubleshooting, or traffic analysis.

Mirrors belong to a Virtual Network and are supported only by the `ovswitch` and `ovswitch_vxlan` network drivers. Open vSwitch must be installed on every participating Host. Create the Virtual Network first, then configure mirrors with the dedicated `onevnet mirror-*` commands.

## Mirror Types and Requirements

| Type    | Destination                                                     | Requirements |
|---------|-----------------------------------------------------------------|--------------|
| `RSPAN` | A dedicated output VLAN.                                        | Provision the VLAN transport and collector on the physical network. OpenNebula does not configure external switches. |
| `GRE`   | A remote IPv4 collector, using a GRE tunnel.                    | Provide IP connectivity from each source Host to the collector and allow GRE traffic through intervening firewalls. |
| `ERSPAN`| A remote IPv4 collector, using an ERSPAN type II or III tunnel. | The installed Open vSwitch and collector must support the selected ERSPAN type. Provide IP connectivity and allow GRE traffic. |

{{< alert title="Open vSwitch mirror capacity" type="info" >}}
Open vSwitch supports up to **32 active mirrors per bridge**. This limit is shared by all Virtual Networks using that bridge and includes mirrors configured outside OpenNebula. A mirror selecting multiple source NICs consumes one mirror slot on each participating Host bridge. OpenNebula does not enforce this OVS-specific limit. If it is exceeded, the mirror definition may still appear in OVSDB and the OpenNebula operation may succeed, but OVS cannot activate the excess mirror. Check the affected Host's `ovs-vswitchd` log for `maximum of 32 port mirrors reached` and `mirror ... configuration is invalid` errors.
{{< /alert >}}

### Permissions

Mirror operations require `ADMIN` permission on the Virtual Network. Adding or removing source ports requires `ADMIN` permission on the referenced VMs. Source ports must be regular VM NICs belonging to the mirror's Virtual Network; NIC aliases, PCI NICs, and NICs of terminated VMs are not supported.

## Mirror Template

Creation and update templates contain exactly one `MIRROR` vector. Names are mandatory, and unknown attributes are rejected. `MIRROR_ID` is assigned by OpenNebula and identifies the mirror within its Virtual Network.

### Common Attributes

| **Attribute** | **Description**                                |
|---------------|------------------------------------------------|
| `NAME`        | Required, nonempty mirror name.                |
| `TYPE`        | Required: `RSPAN`, `GRE`, or `ERSPAN`. |
| `DIRECTION`   | `IN`, `OUT`, or `BOTH`; default `BOTH`. Direction is relative to the source VM, `OUT` copies packets sent by the VM|
| `PORTS`       | Optional comma-separated `VM_ID:NIC_ID` pairs. Duplicates are removed. After creation, change membership with `mirror-addport` and `mirror-delport`. |
| `VLANS`       | Optional comma-separated VLAN IDs from `0` to `4094`. Ranges are not accepted. Duplicates are removed. |
| `DESCRIPTION` | Optional description.                          |

### Destination Attributes

Only include attributes applicable to the selected type.

| Type               | Attribute            | Mandatory | Description       |
|--------------------|----------------------|-----------|-------------------|
| `RSPAN`            | `OUTPUT_VLAN`        | Yes       | Output VLAN, from `1` to `4094`. Use a dedicated VLAN for mirrored traffic. |
| `GRE`, `ERSPAN`    | `REMOTE_IP`          | Yes       | Collector IPv4 address; hostnames and IPv6 addresses are not accepted. |
| `GRE`, `ERSPAN`    | `LOCAL_IP`           | Optional  | Source IPv4 address on the hypervisor, or an interface reference such as `interface:ovsbr0`. If omitted, routing determines the source address. |
| `ERSPAN`           | `ERSPAN_TYPE`        | Yes       | `II` or `III`.    |
| `ERSPAN`           | `ERSPAN_KEY`         | Yes       | Session identifier, entered in decimal, from `0` to `1023`. |
| `ERSPAN` type `II` | `ERSPAN_INDEX`       | Optional  | Index, entered in decimal, from `0` to `1048575`; default `0`. Not valid for type `III`. |
| `ERSPAN` type `III`| `ERSPAN_HWID`        | Optional  | Hardware identifier, entered in decimal, from `0` to `63`; default `0`. Not valid for type `II`. |

An interface referenced by `LOCAL_IP` must exist on each participating Host and have exactly one usable IPv4 address. Resolution occurs on the hypervisor when the driver applies the mirror.

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

| `PORTS`  | `VLANS`  | **Captured traffic** |
|----------|----------|------------------|
| Nonempty | Empty    | Traffic on the selected VM NICs, without a VLAN filter. |
| Nonempty | Nonempty | Traffic on the selected VM NICs that also matches the VLAN filter. |
| Empty    | Nonempty | No traffic; the mirror is inactive. VLAN-only capture is not supported. |
| Empty    | Empty    | No traffic; the mirror is inactive. |

A VLAN filter restricts traffic on explicitly selected source NICs. It never selects other ports on the bridge. Removing the last source port deactivates the mirror configuration even when `VLANS` remains nonempty; see the [RSPAN cache limitation](#known-limitations) below for traffic that may continue after removal. SPAN destinations and bridge-wide VLAN-only capture are not supported.

## Managing Mirrors

The examples below use Virtual Network `5` and mirror `0`; replace these IDs with your own in the following commands:

```shell
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

# Remove the mirror and propagate cleanup through the affected VM NICs.
onevnet mirror-delete 5 0
```

Mirrors cannot be introduced through `onevnet create`, `onevntemplate create`, or `onevntemplate instantiate`. General `onevnet update` cannot modify mirror definitions; use the dedicated commands. OpenNebula stores each selected mirror definition once in `VM/TEMPLATE/MIRROR`, including its `NETWORK_ID` and VNet-scoped `MIRROR_ID`. Participating NICs contain only `MIRROR_IDS` references. These values are managed by OpenNebula; `onevm nic-update` updates QoS attributes only and cannot change mirror configuration.

A mirror cannot be deleted while its `PORTS` list is nonempty. Remove all sources with `mirror-delport` first and wait for their updates to finish. `mirror-update` preserves source membership in both replacement and append mode; any supplied `PORTS` attribute is ignored. Use `mirror-addport` and `mirror-delport` to change membership.

Detaching a NIC or terminating its VM automatically removes that NIC from mirror source lists. Migration and temporary VM power-state changes preserve membership so that the driver can reconstruct capture when the source becomes active again. Sources on the same Host and bridge share one OVS mirror per VNet mirror definition.

### Applying Changes to Running VMs

Mirror changes propagate asynchronously through the existing Virtual Network update action. Port membership changes update only VMs whose membership changed; adding an already selected port does not trigger another update. Inspect `onevnet show` for the network state and its updated, outdated, and failed VM lists. Wait for the affected VMs to be updated before checking packet capture. A successful API response alone does not mean the hypervisor has finished applying the change.

If an update fails, inspect the VM and driver logs, correct connectivity or Host configuration, then retry:

```shell
onevnet recover 5 --retry
```


## Known Limitations

{{< alert title="RSPAN traffic can persist after mirror removal" type="warning" >}}
An Open vSwitch datapath cache issue can cause RSPAN traffic to continue reaching the collector after the last source port is removed, even though the OVSDB mirror has been removed successfully. This behavior has been reproduced on several OVS versions, including 3.3.9 and 3.6.1, and can persist for more than 30 seconds while traffic continues. No fixed minimum OVS version has been established.

A successful OpenNebula operation or an empty OVSDB `Mirror` table does not guarantee that mirrored traffic has stopped. Verify capture at the collector after removing sources or deleting a mirror. If traffic continues, inspect the affected Host's OVS datapath and consult the OVS vendor for a fix. OpenNebula does not automatically purge cached datapath flows: a daemon-wide purge also affects unrelated networks. Manual cache cleanup is not a required step in the normal mirror deletion procedure.
{{< /alert >}}

## Configuring a Linux Collector

A collector needs a capture interface and a packet capture tool such as `tcpdump`. GRE and ERSPAN collectors also need to decapsulate the mirrored Ethernet frames. A Linux collector can use kernel tunnel interfaces; Open vSwitch does not need to be installed on the collector.

For GRE and ERSPAN, the collector can be a host reachable from every participating hypervisor. RSPAN requires a Layer 2 path carrying the output VLAN to the collector.

### Prerequisites and Addresses

Install `iproute2` and `tcpdump` on the collector. Its kernel must support `gretap` for GRE or `erspan` for ERSPAN, including the selected ERSPAN version. Run the interface configuration commands with root privileges.

The examples use these addresses; replace them with addresses from your deployment:

| Endpoint          | Example IPv4 address |
| ----------------- | -------------------- |
| Collector         | `192.0.2.10`         |
| First hypervisor  | `192.0.2.11`         |
| Second hypervisor | `192.0.2.12`         |

The collector address must already be assigned to its transport interface. Set `REMOTE_IP = "192.0.2.10"` in the mirror definition. Each receive interface's `remote` address must match the outer source address used by that hypervisor: its `LOCAL_IP` if explicitly configured, otherwise the source selected by routing. On a hypervisor, `ip -4 route get 192.0.2.10` shows the route-selected `src` address.

Allow GRE (IP protocol **47**, not a TCP or UDP port) from the hypervisors to the collector through host and intervening firewalls. The underlay must accommodate the encapsulation overhead; use small test packets initially when checking connectivity. No address or bridge membership is needed on the capture interfaces.

### GRE

OVS mirrors Ethernet frames over GRE, so use Linux **`gretap`**, rather than a Layer 3 `gre` interface. Create a receive interface for each source hypervisor:

```bash
sudo ip link add name pm-gre1 type gretap local 192.0.2.10 remote 192.0.2.11
sudo ip link add name pm-gre2 type gretap local 192.0.2.10 remote 192.0.2.12
sudo ip link set dev pm-gre1 addrgenmode none
sudo ip link set dev pm-gre2 addrgenmode none
sudo ip link set dev pm-gre1 up promisc on
sudo ip link set dev pm-gre2 up promisc on
sudo tcpdump -ni pm-gre1 -e
```

Capture on `pm-gre2` to observe traffic from the second hypervisor. Disabling IPv6 address generation keeps these capture interfaces unnumbered when brought up.

### ERSPAN Type II

Configure the mirror with `TYPE = "ERSPAN"`, `ERSPAN_TYPE = "II"`, `ERSPAN_KEY = "10"`, and, for this example, `ERSPAN_INDEX = "7"`. Linux uses `erspan_ver 1` for type II and `key` for the session identifier:

```bash
sudo ip link add name pm-er21 type erspan local 192.0.2.10 remote 192.0.2.11 oseq key 10 erspan_ver 1 erspan 7
sudo ip link add name pm-er22 type erspan local 192.0.2.10 remote 192.0.2.12 oseq key 10 erspan_ver 1 erspan 7
sudo ip link set dev pm-er21 addrgenmode none
sudo ip link set dev pm-er22 addrgenmode none
sudo ip link set dev pm-er21 up promisc on
sudo ip link set dev pm-er22 up promisc on
sudo tcpdump -ni pm-er21 -e
```

### ERSPAN Type III

For type III, configure `ERSPAN_TYPE = "III"`, `ERSPAN_KEY = "20"`, and `ERSPAN_HWID = "3"`. Linux uses `erspan_ver 2`:

```bash
sudo ip link add name pm-er31 type erspan local 192.0.2.10 remote 192.0.2.11 oseq key 20 erspan_ver 2 erspan_dir egress erspan_hwid 3
sudo ip link add name pm-er32 type erspan local 192.0.2.10 remote 192.0.2.12 oseq key 20 erspan_ver 2 erspan_dir egress erspan_hwid 3
sudo ip link set dev pm-er31 addrgenmode none
sudo ip link set dev pm-er32 addrgenmode none
sudo ip link set dev pm-er31 up promisc on
sudo ip link set dev pm-er32 up promisc on
sudo tcpdump -ni pm-er31 -e
```

`oseq` enables transmit sequencing without enforcing receive sequencing, so the collector also accepts traffic after a mirror is recreated and its sequence counter restarts.

The receiving tunnel is identified by the outer endpoint addresses and session ID. The index, hardware ID and direction are ERSPAN metadata, rather than additional receive-side filters. The Linux `erspan`/`erspan_hwid`/`erspan_dir` options describe metadata for packets transmitted through that interface; these examples keep the settings consistent with the sender. The collector is only used for capture. The mirror's `DIRECTION` independently controls which VM traffic is copied.

See the [iproute2 ERSPAN interface reference](https://git.kernel.org/pub/scm/network/iproute2/iproute2.git/tree/man/man8/ip-link.8.in) for the Linux interface options. The [Linux ERSPAN receive implementation](https://github.com/torvalds/linux/blob/master/net/ipv4/ip_gre.c) shows endpoint and session matching.

### Capturing Payloads and Tunnel Headers

Capturing on a receive tunnel interface shows the **decapsulated Ethernet frames**. To save a capture, use `sudo tcpdump -ni pm-er21 -s 0 -U -w mirror.pcap` and generate recognizable traffic between the source VM and a peer. Use a separate terminal to start traffic after `tcpdump` reports that it is listening.

To inspect the **outer GRE/ERSPAN headers**, capture on the collector's transport interface instead. Replace `eth1` with the actual interface:

```bash
sudo tcpdump -ni eth1 -s 0 -vv 'ip proto 47 and dst host 192.0.2.10'
```

Use the outer capture to verify ERSPAN type, session ID, index or hardware ID. If outer packets arrive but the tunnel interface stays silent, check the configured endpoint addresses, session ID, kernel support, and collector firewall. Delete and recreate the receive interfaces when changing their endpoints or session ID.

### RSPAN

For RSPAN, arrange for the output VLAN to reach the collector on a tagged trunk. For example, if VLAN `999` arrives on `eth1`:

```bash
sudo ip link add link eth1 name pm-rspan type vlan id 999
sudo ip link set dev pm-rspan addrgenmode none
sudo ip link set dev pm-rspan up promisc on
sudo tcpdump -ni pm-rspan -e
```

This capture shows frames after removal of the transport VLAN tag. Capture on `eth1` to inspect the tag itself. If an external switch delivers the RSPAN VLAN untagged on an access port, capture directly on that dedicated interface instead. Creating a VLAN interface alone does not provision the VLAN transport.


### Cleanup

Stop capture processes, then remove only the interfaces created for the collector. For example, after the ERSPAN type II setup:

```bash
sudo ip link delete dev pm-er21
sudo ip link delete dev pm-er22
```

Use the corresponding names for GRE, ERSPAN type III, or RSPAN. These commands remove the collector interfaces; remove the OpenNebula mirror separately with `onevnet mirror-delete` when capture is no longer needed.
