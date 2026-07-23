---
title: "Security Groups"
date: "2025-02-17"
description:
categories:
pageintoc: "88"
tags:
weight: "3"
---

<a id="security-groups"></a>

<a id="firewall"></a>

<!--# Security Groups -->

Security Groups define firewall rules to be applied to Virtual Machines.

{{< alert title="Warning" type="warning" >}}
Security groups are not supported for OpenvSwitch.{{< /alert >}} 

<a id="security-groups-requirements"></a>

## Defining a Security Group

A Security Group is composed of several Rules. Each Rule is defined with the following attributes:

| Attribute      | Type      | Meaning                                                                                                                                                                                                       | Values                                                                                                                                                                      |
|----------------|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PROTOCOL**   | Mandatory | Defines the protocol of the rule                                                                                                                                                                              | ALL, TCP, UDP, ICMP, IPSEC                                                                                                                                                  |
| **RULE_TYPE**  | Mandatory | Defines the traffic direction                                                                                                                                                                                 | INBOUND, OUTBOUND                                                                                                                                                           |
| **IP**         | Optional  | If the rule only applies to a specific net. This is the first<br/>**IP** of the consecutive set of **IPs**. Must be used with<br/>**SIZE**.                                                                   | A valid IP                                                                                                                                                                  |
| **SIZE**       | Optional  | If the rule only applies to a net. The number of total<br/>consecutive IPs of the network. Use always with **IP**.                                                                                            | An integer >= 1                                                                                                                                                             |
| **RANGE**      | Optional  | A Port Range to filter specific ports. Only works with<br/>**TCP** and **UDP**.                                                                                                                               | (iptables syntax) multiple ports or port<br/>ranges are separated using a comma, and a<br/>port range is specified using a colon.<br/>Example: `22,53,80:90,110,1024:65535` |
| **ICMP_TYPE**  | Optional  | Specific ICMP type of the rule. If a type has multiple codes,<br/>it includes all the codes within. This can only be used with<br/>**ICMP**. If omitted the rule will affect the whole **ICMP**<br/>protocol. | 0,3,4,5,8,9,10,11,12,13,14,17,18                                                                                                                                            |
| **NETWORK_ID** | Optional  | Specify a network ID to which this Security Group will apply                                                                                                                                                  | A valid networkd ID                                                                                                                                                         |

{{< alert title="Note" type="info" >}}
When using `IPSEC` value for `PROTOCOL`, rules for the Encapsulating Security Payload (ESP) protocol of IPSec are set.{{< /alert >}} 

To create a Security Group, use the [Sunstone UI Interface]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}) or create a template file following this example:

```default
NAME = test

RULE = [
    PROTOCOL = TCP,
    RULE_TYPE = inbound,
    RANGE = 1000:2000
]

RULE = [
    PROTOCOL= TCP,
    RULE_TYPE = outbound,
    RANGE = 1000:2000
]

RULE = [
    PROTOCOL = ICMP,
    RULE_TYPE = inbound,
    NETWORK_ID = 0
]

$ onesecgroup create ./sg.txt
ID: 102
```

{{< alert title="Tip" type="tip" >}}
This guide focuses on the CLI command `onesecgroup` but you can also manage Security Groups using the [Sunstone GUI interface]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}). Select the **Security Group** tab to create and manage groups in a user-friendly way.{{< /alert >}} 

{{< image
  pathDark="/images/virtual_networks/security_groups/dark/create_security_group_dark.png"
  path="/images/virtual_networks/security_groups/light/create_security_group_light.png"
  alt="Sunstone create security group" align="center" width="90%" mb="20px"
>}}

## Using a Security Group

To apply a Security Group to your Virtual Machines, you can assign them to the Virtual Networks. Either use the Sunstone wizard, or set the SECURITY_GROUPS attribute:

```default
$ onevnet update 0

SECURITY_GROUPS = "100, 102, 110"
```

When a Virtual Machine is instantiated, the rules are copied to the VM resource and can be seen in the CLI and Sunstone.

{{< image
  pathDark="/images/virtual_networks/security_groups/dark/use_security_group_dark.png"
  path="/images/virtual_networks/security_groups/light/use_security_group_light.png"
  alt="Sunstone security group" align="center" width="90%" mb="20px"
>}}

### Advanced Usage

To accommodate more complex scenarios, you can also set Security Groups to each Address Range of a Virtual Network:

```default
$ onevnet updatear 0 1

SECURITY_GROUPS = "100, 102, 110"
```

Moreover, each Virtual Machine Template NIC can define a list of Security Groups:

```default
NIC = [
  NETWORK = "private-net",
  NETWORK_UNAME = "oneadmin",
  SECURITY_GROUPS = "103, 125"
]
```

If the Address Range or the Template NIC defines SECURITY_GROUPS, the IDs will be added to the ones defined in the Virtual Network. All the Security Group IDs are combined and applied to the Virtual Machine instance.

## The Default Security Group

There is a special Security Group: `default` (ID 0). This security
group allows all OUTBOUND traffic and all INBOUND traffic.

Whenever a network is created, the `default` Security Group is added to the
network.

This means that you **must** edit every newly created network and remove the
`default` Security Group from it. Otherwise, even if you add other Security
Groups, the `default` one will allow all traffic and therefore override the rest
of the Security Groups.

{{< alert title="Note" type="info" >}}
You may want to remove the rules included in the `default` security groups. This way, users are forced to create security groups (otherwise they will not have connectivity to and from the VMs) which avoid some security problems.{{< /alert >}} 

<a id="security-groups-update"></a>

## Security Group Update

Security Groups can be updated to edit or add new rules. These changes are propagated to all VMs in the security group, so it may take some time till the changes are applied. The particular status of a VM can be checked in the Security Group properties, where outdated and up-to-date VMs are listed.

If the update process needs to be reset, i.e., reapply the rules, you can use the `onesecgroup commit` command.
