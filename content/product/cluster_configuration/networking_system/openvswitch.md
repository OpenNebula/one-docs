---
title: "Open vSwitch Networks"
linkTitle: "Open vSwitch"
date: "2025-02-17"
description:
categories:
pageintoc: "65"
tags:
weight: "6"
---

<a id="openvswitch"></a>

<!--# Open vSwitch Networks -->

This guide describes how to use the [Open vSwitch](http://openvswitch.org/) network drivers. They provide network isolation using VLANs by tagging ports and basic network filtering using OpenFlow. Other traffic attributes that may be configured through Open vSwitch are not modified.

The VLAN ID will be the same for every interface in a given network, calculated automatically by OpenNebula. It may also be forced by specifying an `VLAN_ID` parameter in the [Virtual Network template]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template" %}}).

{{< alert title="Warning" type="warning" >}}
This driver doesn’t support Security Groups.{{< /alert >}}


<a id="openvswitch-node"></a>

## Node Setup

### Requirements

* The OpenNebula node packages are installed. See the [KVM node]({{% relref "kvm_node_installation#kvm-node" %}}) and [LXC node]({{% relref "lxc_node_installation#lxc-node" %}}) installation sections for more details.
* You need to install Open vSwitch on each node. Please refer to the Open vSwitch documentation to do so.

### Configuration

* No additional configuration is needed. If `BRIDGE` configured in the virtual network does not exist, a Linux bridge and a Open vSwitch bridge will be created when the VM is instantiated. For example:

```default
# ovs-vsctl show
61a35859-c8a3-4fd0-a30e-185aa568956f
    Bridge "ovsbr0"
        Port "enp0s8"
            Interface "enp0s8"
        Port "one-19-0"
            tag: 4
            Interface "one-19-0"
        Port "ovsbr0"
            Interface "ovsbr0"
                type: internal
```


## OpenNebula Configuration

The VLAN ID is calculated according to this configuration option [/etc/one/oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf" %}}):

```default
#  VLAN_IDS: VLAN ID pool for the automatic VLAN_ID assigment. This pool
#  is for 802.1Q networks (Open vSwitch and 802.1Q drivers). The driver
#  will try first to allocate VLAN_IDS[START] + VNET_ID
#     start: First VLAN_ID to use
#     reserved: Comma separated list of VLAN_IDs or ranges. Two numbers
#     separated by a colon indicate a range.

VLAN_IDS = [
    START    = "2",
    RESERVED = "0, 1, 4095"
]
```

By modifying this section, you can reserve some VLANs so they aren’t assigned to a Virtual Network. You can also define the first VLAN ID. When a new isolated network is created, OpenNebula will find a free VLAN ID from the VLAN pool. This pool is global and it’s also shared with the [802.1Q Networks]({{% relref "vlan#hm-vlan" %}}).

The following configuration parameters can be adjusted in `/var/lib/one/remotes/etc/vnm/OpenNebulaNetwork.conf`:

| Parameter              | Description                                                                                                                                |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `:arp_cache_poisoning` | Set to `true` to enable ARP Cache Poisoning Prevention Rules<br/>(effective only with IP/MAC spoofing filters enabled on Virtual Network). |
| `:keep_empty_bridge`   | Set to `true` to preserve bridges with no virtual interfaces left.                                                                         |
| `:ovs_bridge_conf`     | *(Hash)* Options for Open vSwitch bridge creation                                                                                          |

{{< alert title="Note" type="info" >}}
Remember to run `onehost sync -f` to synchronize the changes to all the nodes.{{< /alert >}}

<a id="ovswitch-net"></a>

## Defining Open vSwitch Network

To create an Open vSwitch network, include the following information:

| Attribute           | Value                                                                        | Mandatory               |
|---------------------|------------------------------------------------------------------------------|-------------------------|
| `VN_MAD`            | Set `ovswitch`                                                               | **YES**                 |
| `PHYDEV`            | Name of the physical network device that will be attached to the bridge      | NO (unless using VLANs) |
| `BRIDGE`            | Name of the Open vSwitch bridge to use                                       | NO                      |
| `VLAN_ID`           | The VLAN ID, will be generated if not defined and `AUTOMATIC_VLAN_ID=YES`    | NO                      |
| `AUTOMATIC_VLAN_ID` | Ignored if `VLAN_ID` defined. Set to `YES` to automatically assign `VLAN_ID` | NO                      |
| `MTU`               | The MTU for the Open vSwitch port                                            | NO                      |

For example, you can define an *Open vSwitch Network* with the following template:

```default
NAME    = "private4"
VN_MAD  = "ovswitch"
BRIDGE  = vbr1
VLAN_ID = 50          # Optional
...
```

{{< alert title="Warning" type="warning" >}}
Currently, if IP Spoofing is enabled, only one NIC per VM for the same Open vSwith network can be attached.{{< /alert >}}

## Multiple VLANs (VLAN trunking)

OpenNebula supports VLAN trunking with the `ovswitch` driver through the `VLAN_TAGGED_ID` attribute. This allows a VM interface to carry traffic for multiple VLANs simultaneously.

By default, when only `VLAN_TAGGED_ID` is defined, the Open vSwitch port is configured in `trunk` mode. In this mode, all traffic exchanged with the VM must be VLAN tagged.

For example:

```bash
NAME = "ovs-trunk"
VN_MAD = "ovswitch"
PHYDEV = "br0"

VLAN_TAGGED_ID = "10,20,30"
```

With this configuration:

* Traffic for VLANs `10`, `20`, and `30` is allowed through the interface.
* The VM must send and receive traffic tagged with the corresponding VLAN IDs.
* Untagged traffic generated by the VM is dropped by Open vSwitch.

Inside the guest, VLAN-aware interfaces must be configured, for example:

```bash
ip link add link eth0 name eth0.10 type vlan id 10
ip link add link eth0 name eth0.20 type vlan id 20
```

### Native VLAN with Trunking

It is also possible to define a native (untagged) VLAN together with additional tagged VLANs by combining `VLAN_ID` and `VLAN_TAGGED_ID`.

```bash
NAME = "ovs-native-trunk"
VN_MAD = "ovswitch"
PHYDEV = "br0"

VLAN_ID        = "10"
VLAN_TAGGED_ID = "20,30"
```

In this configuration:

* Untagged traffic from the VM is associated with VLAN `10`.
* Traffic for VLANs `20` and `30` must be tagged by the guest.
* Traffic received from VLAN `10` is delivered to the VM untagged.

This configuration is useful when the VM requires a default network together with access to additional VLANs through tagged subinterfaces.

> [!NOTE]
> If `VLAN_ID` is included in `VLAN_TAGGED_ID`, Open vSwitch still delivers traffic for the native VLAN untagged to the guest. Guest operating systems expecting tagged traffic for that VLAN may not receive packets as expected.

<a id="openvswitch-vxlan"></a>

## Using Open vSwitch on VXLAN Networks

This section describes how to use [Open vSwitch](http://openvswitch.org/) on VXLAN networks. To use VXLAN you need to use a specialized version of the Open vSwitch driver that incorporates the features of the [VXLAN]({{% relref "vxlan#vxlan" %}}) driver. It’s necessary to be familiar with these two drivers, their configuration options, benefits, and drawbacks.

The VXLAN overlay network is used as a base with the Open vSwitch (instead of regular Linux bridge) on top. Traffic on the lowest level is isolated by the VXLAN encapsulation protocol and Open vSwitch still allows second level isolation by 802.1Q VLAN tags **inside the encapsulated traffic**. The main isolation is always provided by VXLAN, not 802.1Q VLANs. If 802.1Q is required to isolate the VXLAN, the driver needs to be configured with a user-created 802.1Q-tagged physical interface.

This hierarchy is important.

### OpenNebula Configuration

There is no configuration specific to this driver except the options specified above and in the [VXLAN Networks]({{% relref "vxlan#vxlan" %}}) guide.

### Defining an Open vSwitch - VXLAN Network

To create a network, include the following information:

| Attribute                 | Value                                                                                                                                | Mandatory                                  |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `VN_MAD`                  | Set `ovswitch_vxlan`                                                                                                                 | **YES**                                    |
| `PHYDEV`                  | Name of the physical network device that will be attached to the bridge.                                                             | **YES**                                    |
| `BRIDGE`                  | Name of the Open vSwitch bridge to use                                                                                               | NO                                         |
| `OUTER_VLAN_ID`           | The outer VXLAN network ID.                                                                                                          | **YES** (unless `AUTOMATIC_OUTER_VLAN_ID`) |
| `AUTOMATIC_OUTER_VLAN_ID` | If `OUTER_VLAN_ID` has been defined, this attribute is ignored.<br/>Set to `YES` if you want OpenNebula to generate an automatic ID. | **YES** (unless `OUTER_VLAN_ID`)           |
| `VLAN_ID`                 | The inner 802.1Q VLAN ID. If this attribute is not defined a VLAN ID<br/>will be generated if AUTOMATIC_VLAN_ID is set to YES.       | NO                                         |
| `AUTOMATIC_VLAN_ID`       | Ignored if `VLAN_ID` defined. Set to `YES` to automatically<br/>assign `VLAN_ID`                                                     | NO                                         |
| `MTU`                     | The MTU for the VXLAN interface and bridge                                                                                           | NO                                         |

For example, you can define an *Open vSwitch - VXLAN Network* with the following template:

```default
NAME          = "private5"
VN_MAD        = "ovswitch_vxlan"
PHYDEV        = eth0
BRIDGE        = ovsvxbr0.10000
OUTER_VLAN_ID = 10000               # VXLAN VNI
VLAN_ID        = 50                 # Optional VLAN ID
...
```

In this example, the driver will check for the existence of bridge `ovsvxbr0.10000`.  If it doesn’t exist, it will be created. Also, the VXLAN interface `eth0.10000` will be created and attached to the Open vSwitch bridge `ovsvxbr0.10000`. When a Virtual Machine is instantiated, its bridge ports will be tagged with 802.1Q VLAN ID `50`.

<a id="openvswitch-dpdk"></a>

## Open vSwitch with DPDK

Open vSwitch can use DPDK to provide an accelerated userspace data path for KVM Virtual Machines. This mode requires additional Host resource planning, physical NIC configuration, Huge Pages and vhost-user VM settings.

See [Open vSwitch DPDK]({{% relref "openvswitch_dpdk#openvswitch-dpdk" %}}) for the complete Host, Virtual Network and VM configuration.

<a id="openvswitch-qinq"></a>

## Using Open vSwitch with Q-in-Q

Q-in-Q is an amendment to the IEEE 802.1Q specification that provides the capability for multiple VLAN tags to be inserted into a single Ethernet frame. Using Q-in-Q (aka C-VLAN, customer VLAN) tunneling allows us to create Layer 2 Ethernet connection between customers' cloud infrastructure and OpenNebula VMs, or use a single service VLAN to bundle different customer VLANs.

### OpenNebula Configuration

There is no configuration specific for this use case, just consider the general options specified above.

### Defining a Q-in-Q Open vSwitch Network

To create a network you need to include the following information:

| Attribute           | Value                                                                                                                  | Mandatory   |
|---------------------|------------------------------------------------------------------------------------------------------------------------|-------------|
| `VN_MAD`            | Set `ovswitch`                                                                                                         | **YES**     |
| `PHYDEV`            | Name of the physical network device that will be attached to the bridge.                                               | **YES**     |
| `BRIDGE`            | Name of the Open vSwitch bridge to use                                                                                 | NO          |
| `VLAN_ID`           | The service 802.1Q VLAN ID. If not defined the VLAN ID tag<br/>will be generated if AUTOMATIC_VLAN_ID is set to YES.   | NO          |
| `AUTOMATIC_VLAN_ID` | Ignored if `VLAN_ID` defined. Set to `YES` to automatically<br/>assign `VLAN_ID`                                       | NO          |
| `CVLANS`            | Customer VLAN IDs, as a comma separated list (ranges supported)                                                        | **YES**     |
| `QINQ_TYPE`         | Tag Protocol Identifier (TPID) for the service VLAN tag. Use `802.1ad`<br/>for TPID 0x88a8 or `802.1q` for TPID 0x8100 | NO          |
| `MTU`               | The MTU for the Open vSwitch port                                                                                      | NO          |

For example, you can define an *Open vSwitch - QinQ Network* with the following template:

```default
NAME     = "qinq_net"
VN_MAD   = "ovswitch"
PHYDEV   = eth0
VLAN_ID  = 50                 # Service VLAN ID
CVLANS   = "101,103,110-113"  # Customer VLAN ID list
```

In this example, the driver will assign and create an Open vSwitch bridge and will attach the interface `eth0` it. When a Virtual Machine is instantiated, its bridge ports will be tagged with 802.1Q VLAN ID `50` and service VLAN IDs `101,103,110,111,112,113`. The configuration of the port should be similar to the that of following example that shows the second (`NIC_ID=1`) interface port `one-1-5` for VM 5:

```default
# ovs-vsctl list Port one-5-1

_uuid               : 791b84a9-2705-4cf9-94b4-43b39b98fe62
bond_active_slave   : []
bond_downdelay      : 0
bond_fake_iface     : false
bond_mode           : []
bond_updelay        : 0
cvlans              : [101, 103, 110, 111, 112, 113]
external_ids        : {}
fake_bridge         : false
interfaces          : [6da7ff07-51ec-40e9-97cd-c74a36e2c267]
lacp                : []
mac                 : []
name                : one-5-1
other_config        : {qinq-ethtype="802.1q"}
protected           : false
qos                 : []
rstp_statistics     : {}
rstp_status         : {}
statistics          : {}
status              : {}
tag                 : 100
trunks              : []
vlan_mode           : dot1q-tunnel
```
