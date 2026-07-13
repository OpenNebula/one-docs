---
title: "Defining and Managing Virtual Networks"
linkTitle: "Virtual Networks"
date: "2025-02-17"
description:
categories:
pageintoc: "60"
tags:
weight: "2"
---

<a id="manage-vnets"></a>

<!--# Virtual Networks -->

Commonly a Host is connected to one or more networks that are available to the VMs through bridges. OpenNebula allows the creation of Virtual Networks by mapping them on top of the physical ones.

## Virtual Network Definition

A Virtual Network definition consists of three different parts:

- The **underlying physical network infrastructure** that will support it, including the network driver.
- The **logical address space** available. Addresses associated to a Virtual Network can be IPv4, IPv6, dual stack IPv4-IPv6, or Ethernet.
- The **guest configuration attributes** to set up the Virtual Machine network, that may include for example network masks, DNS servers, or gateways.

### Physical Network Attributes

To define a Virtual Network include:

* Its name (`NAME`) to refer to this Virtual Network.
* The driver (`VN_MAD`) to implement this Virtual Network. Depending on the driver you may need to set additional attributes, check the following to get more details:
  * [Linux bridge networks]({{% relref "bridged#bridged-net" %}})
  * [802.1Q networks]({{% relref "vlan#hm-vlan-net" %}})
  * [VXLAN networks]({{% relref "vxlan#vxlan-net" %}})
  * [OpenvSwitch networks]({{% relref "openvswitch#ovswitch-net" %}})
* QoS parameters (optional) for each NIC attached to the network, to limit the inbound/outbound average and peak bandwidths as well as the burst data size that can be transmitted at peak speed ([see more details here]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-qos" %}})).

For example, to define a 802.1Q Virtual Network you would add:

```default
NAME    = "Private Network"
VN_MAD  = "802.1Q"
PHYDEV  = "eth0"

OUTBOUND_AVG_BW = "1000"
OUTBOUND_PEAK_BW = "1500"
OUTBOUND_PEAK_KB = "2048"
```

<a id="manage-vnet-ar"></a>

### Address Space

The addresses available in a Virtual Network are defined by one or more Address Ranges (AR). Each AR defines a continuous address range and, optionally, configuration attributes that will override those defined in the Virtual Network. There are four types of ARs:

- **IPv4**, to define a contiguous IPv4 address set (classless), [see more details here]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-ar4" %}})
- **IPv6**, to define global and ULA IPv6 networks, [see full details here]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-ar6" %}})
- **IPv6 no-SLAAC**, to define fixed 128 bits IPv6 address, [see here]({{% relref "../../operation_references/configuration_references/vnet_template#vn-template-ar6-nslaac" %}})
- **Dual stack**, each NIC in the network will get both an IPv4 and an IPv6 address (SLAAC or no-SLAAC), [see more here]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-ar46" %}})
- **Ethernet**,  just MAC addresses are generated for the VMs. You should use this AR when an external service is providing the IP addresses, such as a DHCP server, [see more details here]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-eth" %}})

For example, to define the IPv4 address range 10.0.0.150 - 10.0.0.200

```default
AR=[
    TYPE = "IP4",
    IP   = "10.0.0.150",
    SIZE = "51",
]
```

### Shared Address Ranges (Shared AR) for Virtual IPs

Marking an Address Range as `SHARED` converts its IPs into **Virtual IPs**. This allows **multiple VMs** to use the same IP address.

To mark an Address Range as `SHARED`, add the `SHARED` attribute in the AR definition:

```default
AR=[
    TYPE   = "IP4",
    IP     = "10.0.0.211",
    SIZE   = "3",
    SHARED = "YES"
]
```

The option to create a Shared AR is also available through a checkbox in the Sunstone UI in the **Add Address Range** dialog.

Shared Address Ranges behave slightly differently from regular Address Ranges:

- Same IP, multiple VMs: The same IP address from a Shared AR can be used by more than one VM.
- Explicit request required: Shared IPs are not assigned automatically. They must be explicitly requested in a NIC or NIC Alias ([more details](#using-virtual-ips)).
- Attribute `USED_LEASES` shows how many different shared IPs are in use, not how many VMs are using them.

{{< alert title="Important" type="info" >}}
The `SHARED` attribute of an Address Range can't be changed after creation. The default value is `NO`. {{< /alert >}}

### Guest Configuration Attributes (Context)

To set up the guest network, the Virtual Network may include additional information to be injected into the VM at boot time. These contextualization attributes may include, for example, network masks, DNS servers, or gateways. For example, to define a gateway and DNS server for the Virtual Machines in the Virtual Network, simply add:

```default
DNS = "10.0.0.23"
GATEWAY = "10.0.0.1"
```

These attributes are automatically added to the VM and processed by the context packages. Virtual Machines just need to add:

```default
CONTEXT = [
  NETWORK="yes"
]
```

[See here for a full list of supported attributes]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-context" %}})

### Virtual Network Definition Example

Putting all the three pieces together we get:

```default
NAME    = "Private"
VN_MAD  = "802.1Q"
PHYDEV  = "eth0"

AR=[
    TYPE = "IP4",
    IP   = "10.0.0.150",
    SIZE = "51"
]

DNS     = "10.0.0.23"
GATEWAY = "10.0.0.1"

DESCRIPTION = "A private network for VM inter-communication"
```

This file will create an IPv4 network using VLAN tagging, the VLAN ID in this case is assigned by OpenNebula. The network will lease IPs in the range 10.0.0.150 - 10.0.0.200. Virtual Machines in this network will get a lease in the range and configure DNS servers to 10.0.0.23 and 10.0.0.1 as default gateway.

[See here for more examples]({{% relref "../../operation_references/configuration_references/vnet_template#vnet-template-example" %}})

<a id="vnet-state"></a>

## States and Life-cycle

The Virtual Network will be moving through different states to represent the actions you perform and their status. The following table summarizes the Virtual Network states and their meaning:

| State         | Short state   | OpenNebula State Names   | Meaning                                                                                                         |
|---------------|---------------|--------------------------|-----------------------------------------------------------------------------------------------------------------|
| Ready         | `rdy`         | `READY`                  | Virtual Network is ready to be used                                                                             |
| Locked        | `lock`        | `LOCK_CREATE`            | Virtual Network is being created/deleted. Driver operation is in progress.                                      |
| `LOCK_DELETE` |               |                          |                                                                                                                 |
| Error         | `err`         | `ERROR`                  | Error state, an operation failed. See the Virtual Network information with `onevnet show` for an error message. |
| Failure       | `fail`        | `UPDATE_FAILURE`         | Virtual Network update fails to update some Virtual Machine NICs. `ERROR_VMS` contains list of failed VMs       |

<a id="add-and-delete-vnet"></a>

## Adding and Deleting Virtual Networks

{{< alert title="Tip" type="tip" >}}
This guide uses the CLI command `onevnet`, but you can also manage your Virtual Networks using the [Sunstone GUI]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}). Select the **Virtual Networks** tab to create, enable and operate your Virtual Networks in a user-friendly way.{{< /alert >}}

There are three different ways for creating a network:

- **Creating** the network from scratch.
- **Making a reservation** from an existing network.
- **Instantiating** a Virtual Network Template.

End users typically use the last two ways, instantiation and reservation. The administrator can define a network template to be instantiated later by the end user or create a Virtual Network from which the end user can make a reservation.

To create a new network from scratch, put its configuration in a file and then execute:

```shell
onevnet create priv.net
ID: 4
```

You can delete a Virtual Network using its ID or name:

```shell
onevnet delete 0
onevnet delete "Private"
```

To list the Virtual Networks in the system use `onevnet list`:

```shell
onevnet list
ID USER      GROUP       NAME        CLUSTER    BRIDGE    STATE  LEASES
 0 admin     oneadmin    Private     0,100      onebr.10  rdy         0
 1 admin     oneadmin    Public      0,101      vbr0      rdy         0
```

In the output above, `USER` is the owner of the network and `LEASES` the number of addresses assigned to a Virtual Machine or reserved.

You can check the details of a Virtual Network with the `onevnet show` command:

```shell
onevnet show 1
  VIRTUAL NETWORK 4 INFORMATION
  ID             : 4
  NAME           : Private
  USER           : ruben
  GROUP          : oneadmin
  CLUSTERS       : 0
  BRIDGE         : onebr4
  STATE          : READY
  VN_MAD         : 802.1Q
  PHYSICAL DEVICE: eth0
  VLAN ID        : 6
  USED LEASES    : 0

  PERMISSIONS
  OWNER          : um-
  GROUP          : ---
  OTHER          : ---

  VIRTUAL NETWORK TEMPLATE
  BRIDGE="onebr4"
  DESCRIPTION="A private network for VM inter-communication"
  DNS="10.0.0.23"
  GATEWAY="10.0.0.1"
  PHYDEV="eth0"
  SECURITY_GROUPS="0"
  VN_MAD="802.1Q"

  ADDRESS RANGE POOL
  AR 0
  SIZE           : 51
  LEASES         : 0

  RANGE                                   FIRST                               LAST
  MAC                         02:00:0a:00:00:96                  02:00:0a:00:00:c8
  IP                                 10.0.0.150                         10.0.0.200
```

Check the `onevnet` command help or the [reference guide]({{% relref "../../operation_references/command_line_interface/cli#cli" %}}) for more options to list the Virtual Networks.

## Group VLAN Rules

Group VLAN rules allow cloud administrators to delegate Virtual Network self-provisioning while restricting tenant VLAN usage within explicit ranges. Rules are defined [**per user group**]({{% relref "product/cloud_system_administration/multitenancy/manage_groups/" %}}) and are evaluated when a non-administrator:

- Instantiates a Virtual Network template.
- Updates a Virtual Network, including VLAN attributes in Address Ranges.

A group VLAN rule is defined with `ID`, `SCOPE`, and optionally `VNTEMPLATE`:

```default
RULE = [
  ID         = "100-199",
  SCOPE      = "VLAN_ID",
  VNTEMPLATE = "10"
]
```

- `ID`: Allowed VLAN values. Use a single value, a comma-separated list, or ranges, for example `100`, `100,105`, or `100-199`.
- `SCOPE`: VLAN attribute controlled by the rule. Supported values are `VLAN_ID`, `OUTER_VLAN_ID`, `CVLAN`, `VLAN_TAGGED_ID`, and `ANY`.
- `VNTEMPLATE`: Virtual Network template IDs where the rule applies. Use a single ID, a comma-separated list, ranges, or `-1` to apply the rule to any Virtual Network template. If omitted, OpenNebula sets it by default as `-1`.

For example, the following rule allows VLAN IDs 300, and 400 through 450, for any supported VLAN attribute and any Virtual Network template:

```default
RULE = [
  ID         = "300,400-450",
  SCOPE      = "ANY",
  VNTEMPLATE = "-1"
]
```

To set the rules for a user group, create a file such as `vlans.txt` with the intended group VLAN rules as detailed above then run:

```shell
onegroup vlan <user_group_name> vlans.txt
```

If the file argument is omitted, `onegroup vlan` opens an editor with the current rules. Adjust this file to your preferences then save and close the editor, the `onegroup vlan` command will then execute upon closing the editor.

When users belong to more than one group, a requested VLAN value is accepted if any of their groups has a matching rule. A rule only authorizes values within its own scope, except for `ANY`, which matches all supported VLAN scopes. `VLAN_ID` and `OUTER_VLAN_ID` must be single values; `CVLAN` and `VLAN_TAGGED_ID` can use the same range syntax as rule IDs.

{{< alert title="Important" type="info" >}}
If a group has VLAN rules that apply to the target Virtual Network template, users in that group must request explicit VLAN values. Automatic selection with `AUTOMATIC_VLAN_ID` or `AUTOMATIC_OUTER_VLAN_ID` is rejected for that template since it would bypass the group VLAN policy.{{< /alert >}}

### Virtual Network Tips

* You may have some used IPs in a VNET so you do not want them to be assigned. You can add as many ARs as you need to implement these address gaps. Alternatively you can put address on hold to prevent them from being assigned.
* ARs can be of SIZE = 1 to define single addresses lease scheme.
* ARs does not need to be of the same type or belong to the same IP network. To accommodate this use case you can overwrite context attributes in the AR, for example by adding attributes like NETWORK_MASK or DNS in the AR definition.
* *Super-netting*, you can even combine ARs overwriting the physical attributes, e.g., `BRIDGE` or `VLAN_ID`. This way a Virtual Network can be a logical super-net, e.g., DMZ, that can be implemented through multiple VLANs each using a different hypervisor bridge.
* There is no need to design all your IP assignment plan beforehand, as ARs can be added and modified after the Virtual Network is created, see below.
* Orphan Virtual Networks (i.e., Virtual Networks not referenced by any template) can be shown with `onevnet orphans` command.

<a id="vnet-update"></a>

## Updating a Virtual Network

After creating a Virtual Network, you can use the `onevnet update` command to update its attributes. The name of the Virtual Network can be changed with `onevnet rename` command.

The update operation will trigger driver action to live update the network configuration for all Virtual Machines with leases in the Virtual Network. The attributes that can be live-updated depends on the driver configured for the Virtual Network, see the following table:

| Network Driver                    | Live-update Attributes                                                                                                                                                                           |
|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OpenvSwitch<br/>OpenvSwitch VXLAN | - VLAN_ID<br/>- PHYDEV<br/>- MTU<br/>- VLAN_TAGGED_ID<br/>- CVLANS<br/>- QINQ_TYPE<br/>- INBOUND_AVG_BW<br/>- INBOUND_PEAK_BW<br/>- INBOUND_PEAK_KB<br/>- OUTBOUND_AVG_BW<br/>- OUTBOUND_PEAK_BW |
| bridge                            | - PHYDEV<br/>- VLAN_TAGGED_ID                                                                                                                                                                    |
| fw                                | - PHYDEV<br/>- INBOUND_AVG_BW<br/>- INBOUND_PEAK_BW<br/>- INBOUND_PEAK_KB<br/>- OUTBOUND_AVG_BW<br/>- OUTBOUND_PEAK_BW                                                                           |
| 802.1Q<br/>vxlan                  | - PHYDEV<br/>- VLAN_ID<br/>- MTU<br/>- INBOUND_AVG_BW<br/>- INBOUND_PEAK_BW<br/>- INBOUND_PEAK_KB<br/>- OUTBOUND_AVG_BW<br/>- OUTBOUND_PEAK_BW                                                   |
> {{< alert title="Important" type="info" >}}
> QoS attributes (INBOUND and OUTBOUND) can be updated for single VMs with [onevm nic-update]({{% relref "../../virtual_machines_operation/virtual_machines/vm_instances#nic-update" %}}).{{< /alert >}}

> {{< alert title="Important" type="info" >}}
> For SR-IOV-based NICs you can update all the attributes that can be set for this type of interfaces.{{< /alert >}}

As the network is updated for each VM and Host, you can check the progress of the update in Virtual Network details:

> - `UPDATED_VMS`, list of VM IDs already updated.
> - `UPDATING_VMS`, list of VM IDs that are being updated (driver action in execution).
> - `OUTDATED_VMS`, list of VM IDs with outdated Virtual Network configuration.
> - `ERROR_VMS` lists of VM IDs where the update operation failed.

In case of driver action failure, the Virtual Network will switch to `UPDATE_FAILURE` state. In that case you can use `onevnet recover --retry` to re-launch the driver actions for failed VMs. Or manually fix the network and call `onevnet recover --success`.

{{< alert title="Note" type="info" >}}
Please consider that for Virtual Networks with lot of leases it may take some time to propagate changes to all Hosts and VMs.{{< /alert >}}

<a id="manage-address-ranges"></a>

## Managing Address Ranges

Addresses are structured in Address Ranges (AR). Address Ranges can be dynamically added or removed from a Virtual Network. In this way, you can easily add new addresses to an existing Virtual Network if the current addresses are exhausted.

### Adding and Removing Address Ranges

A new AR can be added using exactly the same definition parameters as described above. For example, the following command will add a new AR of 20 IP addresses:

```default
onevnet addar Private --ip 10.0.0.200 --size 20
```

In the same way you can remove an AR:

```default
onevnet rmar Private 2
```

### Updating Address Ranges

You can update the following attributes of an AR:

- `SIZE`, assigned addresses cannot fall outside of the range.
- IPv6 prefix: `GLOBAL_PREFIX` and `ULA_PREFIX`
- Any custom attribute that may override the Virtual Network defaults.

The following command shows how to update an AR using the CLI, an interactive editor session will be stated:

```default
onevnet updatear Private 0
```

### Hold and Release Leases

Addresses can be temporarily be marked as `hold`. They are still part of the network but they will not be assigned to any Virtual Machine.

To do so, use the `onevnet hold` and `onevnet release` commands. By default, the address will be put on hold in all ARs containing it; if you need to hold the IP of a specific AR you can specify it with the ‘-a <AR_ID>’ option:

```shell
#Hold IP 10.0.0.120 in all ARs
onevnet hold "Private Network" 10.0.0.120

#Hold IP 10.0.0.123 in AR 0
onevnet hold 0 10.0.0.123 -a 0
```

You see the list of leases on hold with the `onevnet show` command; they’ll show up as used by Virtual Machine -1, ‘V: -1’

<a id="vgg-vm-vnets"></a>

## Using Virtual Networks

Once the Virtual Networks are set up, they can be made available to users based on access rights and ownership. The preferred way to do so is through [Virtual Data Center abstraction]({{% relref "../../cloud_system_administration/multitenancy/manage_vdcs#manage-vdcs" %}}). By default, all Virtual Networks are automatically available to the group `users`.

Virtual Networks can be used by VMs in two different ways:

- Manual selection: NICs in the VMs are attached to a specific Virtual Network.
- Automatic selection: Virtual Networks are scheduled like other resources needed by the VM (like Hosts or datastores).

### Manually Attach a Virtual Machine to a Virtual Network

To attach a Virtual Machine to a Virtual Network simply specify its name or ID in the `NIC` attribute.  For example, to define VM with a network interface connected to the `Private` Virtual Network, just include in the template:

```default
NIC = [ NETWORK = "Private" ]
```

Equivalently you can use the network ID as:

```default
NIC = [ NETWORK_ID = 0 ]
```

The Virtual Machine will also get a free address from any of the address ranges of the network.  You can also request a specific address just by adding the `IP` or `MAC` to `NIC`. For example, to put a Virtual Machine in the network `Private` and request 10.0.0.153, use:

```default
NIC = [ NETWORK = "Network", IP = 10.0.0.153 ]
```

{{< alert title="Warning" type="warning" >}}
Note that if OpenNebula is not able to obtain a lease from a network the submission will fail.{{< /alert >}}

{{< alert title="Warning" type="warning" >}}
Users can only attach VMs or make reservations from Virtual Networks with **USE** rights on them. See the [Managing Permissions documentation]({{% relref "../../cloud_system_administration/multitenancy/chmod#chmod" %}}) for more information.{{< /alert >}}

<a id="vgg-vn-automatic"></a>

### Automatic Attach a Virtual Machine to a Virtual Network

You can delay the network selection for each NIC in the VM to the deployment phase. In this case the Scheduler will pick the Virtual Network among the available networks in the Host selected to deploy the VM.

This strategy is useful to prepare generic VM templates that can be deployed in multiple OpenNebula clusters.

To set the automatic selection mode, simply add the attribute `NETWORK_MODE = "auto"` into the `NIC` attribute.

```default
NIC = [ NETWORK_MODE = "auto" ]
```

Also you can add SCHED_REQUIREMENTS and SCHED_RANK when this mode is activated. This will let you specify which networks can be used for a specific NIC (`SCHED_REQUIREMENTS`) and what your preferences are (`SCHED_RANK`) to select a network among the suitable ones.

```default
NIC = [ NETWORK_MODE = "auto",
        SCHED_REQUIREMENTS = "TRAFFIC_TYPE = \"public\" & INBOUND_AVG_BW<1500",
        SCHED_RANK = "-USED_LEASES" ]
```

In this case the scheduler will look for any Virtual Network in the selected cluster with a custom tag `TRAFFIC_TYPE` to be equal to `public` and `INBOUND_AVG_BW` less than 1500. Among all the networks that satisfy these requirements the scheduler will select the one with the most free leases.

<a id="vgg-vn-alias"></a>

### Attach an NIC Alias to a Virtual Machine

To attach an NIC alias to a VM you need to refer to the parent NIC by its `NAME` attribute:

```default
NIC = [ NETWORK = "public", NAME = "test" ]
```

{{< alert title="Important" type="info" >}}
Names in the form `NIC<number>` are reserved. OpenNebula will rename them to `_NIC<number>`.{{< /alert >}}

Then you can attach an alias using an `NIC_ALIAS` attribute:

```default
NIC_ALIAS = [ NETWORK = "private", PARENT = "test" ]
```

If the nic `NAME` is empty, it will be generated automatically in the form `NIC${NIC_ID}`. This name can be also used to create an alias, e.g., `NIC_ALIAS = [ NETWORK = "private", PARENT = "NIC0" ]`

{{< alert title="Note" type="info" >}}
You can also use the `onevm` command using the option `--alias alias` so that NIC will be attached as an alias, instead of as an NIC.{{< /alert >}}

{{< alert title="Important" type="info" >}}
Any attribute supported by an NIC attribute can be also used in an alias except for `NETWORK_MODE`. A `NIC_ALIAS` network cannot be automatically selected.{{< /alert >}}

{{< alert title="Important" type="info" >}}
The [Security Groups]({{% relref "../../virtual_machines_operation/virtual_machines_networking/security_groups#security-groups" %}}) and IP/MAC spoofing filters from the NIC network will be applied to the NIC_ALIAS. Those ones belonging to the NIC_ALIAS network won’t apply.{{< /alert >}}

### Using Virtual IPs

To request a Virtual IP (VIP) from a [Shared Address Range](#shared-address-ranges-shared-ar-for-virtual-ips) you must explicity request the IP in a `NIC` or `NIC_ALIAS` attribute. The most natural way of using Shared Address Ranges for VIPs is to define a primary NIC in the network with a regular IP and a NIC Alias with the VIP, this way you get a single network interface with two different IPs. The procedure is described below:

1. Define the primary NIC and give it a `NAME` so aliases can refer to it:

```default
NIC = [ NETWORK = "private", NAME = "main" ]
```

2. Add a `NIC_ALIAS` that **explicitly requests the shared IP** from the Shared AR (you must include the `IP` attribute):

```default
NIC_ALIAS = [ NETWORK = "private", PARENT = "main", IP = "10.0.0.211" ]
```

This will result in the VM having a **single network interface** (the parent NIC) with **two IPs** configured:

- The IP assigned to the main NIC
- The explicitly requested shared IP from the `NIC_ALIAS`

{{< alert title="Important" type="info" >}}
Requesting a Shared IP from a Shared AR **without** using `NIC_ALIAS` will create a **new interface** in the VM, with a random MAC assigned by OpenNebula.{{< /alert >}}

### Configuring the Virtual Machine Network

Hypervisors will set the MAC address for the NIC of the Virtual Machines, but not the IP address. The IP configuration inside the guest is performed by the contextualization process, check the [contextualization guide]({{% relref "../../virtual_machines_operation/virtual_machines/vm_templates#context-overview" %}}) to learn how to prepare your Virtual Machines to automatically configure the network

{{< alert title="Note" type="info" >}}
Alternatively, a custom external service can configure the Virtual Machine network (e.g., your own DHCP server in a separate Virtual Machine){{< /alert >}}

### Recovering the Virtual Network

In case the Virtual Network is not in `READY` state, use `onevnet recover` to fix the Virtual Network. The command accepts the following flags:
: * `--failure` Driver action wasn’t completed successfully, move the Virtual Network to `ERROR` state.
  * `--success` User manually fixed the issue, move the Virtual Network to `READY` state.
  * `--delete` The Virtual Network can’t be fixed, delete it.
  * `--retry` Retry the last driver action. Allowed only in `UPDATE_FAILURE` state.

## Using Sunstone to Manage Virtual Networks

You can also manage your Virtual Networks using the [Sunstone GUI]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}). Select the **Virtual Networks** tab to create, enable, and operate your Virtual Networks in a user-friendly way.

![image0](/images/sunstone_vnets.png)

- Create new Virtual Networks

![image1](/images/sunstone_vnet_create_general.png)

![image2](/images/sunstone_vnet_create_advanced.png)
