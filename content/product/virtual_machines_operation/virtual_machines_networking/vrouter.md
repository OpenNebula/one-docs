---
title: "Virtual Routers"
date: "2025-02-17"
description:
categories:
pageintoc: "90"
tags:
weight: "5"
---

Virtual Routers provide routing across Virtual Networks. The administrators can easily connect Virtual Networks from Sunstone and the CLI. The routing itself is implemented with a Virtual Machine appliance available though the Marketplace. This Virtual Machine can be seamlessly deployed in high availability mode.

## Download the Virtual Router Appliance

OpenNebula provides an appliance which implements various Virtual Network Functions (VNFs), including the Virtual Router. The Virtual Router image is prepared to run in an HA mode and process the context information from OpenNebula. In this way, its base capabilities can be easily extended. Continue to the [VNF appliance documentation](https://github.com/OpenNebula/one-apps/wiki/vr_intro) for more details about the advanced usage and other implemented functions.

- Download the appliance from the OpenNebula Marketplace. For example, to put the Virtual Router image in the default datastore and create a Virtual Router template named `Service Virtual Router`, use:

  ```shell
  onemarketapp export 'Service Virtual Router' vr --datastore default --vmname vr
  IMAGE
      ID: 9
  VMTEMPLATE
      ID: 8
  ```

- Check that the resources are properly created and update them to your OpenNebula installation if needed:

  ```shell
  oneimage show 9 # 9 is the IMAGE ID from the previous onemarketapp command
  onetemplate show 8 # 8 is for the VMTEMPLATE ID
  ```

## Creating a New Virtual Router

New Virtual Routers are created from a special type of VM Template, like the one created automatically when downloading the market app.

Select the interface to find the corresponding instructions:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
<a id="force-ipv4-sunstone"></a>

To create a new Virtual Router from [Sunstone UI Interface]({{% relref "product/control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}), follow the wizard to select the Virtual Networks that will get logically linked to it. This connection takes effect when the Virtual Machine containing the VR Appliance is automatically deployed, with a network interface attached to each Virtual Network.

For each Virtual Network, define the relevant options:

* **Floating IP**: Only used in High Availability. This option is controlled with `FLOATING_IP` and `FLOATING_ONLY` parameters.
* **Force IPv4**: You can force the IP assigned to the network interface. When the VR is not configured in High Availability, this will be the IP requested for the Virtual Machine appliance.
* **Management Interface**: If checked, this network interface will be a Virtual Router management interface. Traffic will not be forwarded to it.

Once ready, click the **Create** button to finish. OpenNebula automatically creates the Virtual Router and the corresponding Virtual Machines.

{{< image
  pathDark="/images/virtual_networks/virtual_router/dark/create_vr_template.png"
  path="/images/virtual_networks/virtual_router/light/create_vr_template.png"
  alt="Sunstone create security group" align="center" width="90%" mb="20px"
>}}

{{% /tab %}}

{{% tab header="CLI"%}}

Manage Virtual Routers with the `onevrouter` command.

To create a new Virtual Router from the CLI, first specify a VR Template file with the attributes below. Then run the `onevrouter create` command:

```shell
cat myvr.txt
NAME = my-vr
NIC = [
  NETWORK="blue-net",
  IP="192.168.30.5",
  FLOATING_IP = "yes" ]
NIC = [
  NETWORK="red-net" ]

onevrouter create myvr.txt
ID: 1
```

The Virtual Router resource is created but it does not have any Virtual Machines. Create one or more VMS, depending if High Availability is used:

```shell
onevrouter instantiate <vrouterid> <templateid>
```

{{% /tab %}}

{{< /tabpane >}}


## Managing Virtual Routers

Using the Virtual Routers tab in Sunstone, or the `onevrouter show` command, you can retrieve the generic resource information such as owner and group, the list of Virtual Networks interconnected by this router, and the Virtual Machines that are actually providing the routing.

The Virtual Networks connected to the VR machines can be modified with the attach/detach actions.

In the [Sunstone GUI]({{% relref "../../control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}) the actions can be found in the Virtual Router’s main information panel, in the networks table. The options to add a new Virtual Network are the same as for the creation wizard, see previous section.

{{< image
  pathDark="/images/virtual_networks/virtual_router/dark/virtual_router_dark.png"
  path="/images/virtual_networks/virtual_router/light/virtual_router_light.png"
  alt="Sunstone virtual routers" align="center" width="90%" mb="20px"
>}}

The `onevrouter nic-attach` command takes a file containing a single NIC attribute. Alternatively, you can provide the new Virtual Network settings with command options, see `onevrouter nic-attach -h` for more information.

After a NIC is attached or detached, the Virtual Machine appliances are automatically reconfigured to start routing to the new interface. No other action, like a reboot, is required.

### Managing Virtual Router VMs

The Virtual Machines that are associated to a Virtual Router have all actions allowed except nic-attach/detach. They can be terminated and new Virtual Machines can be added to an existing Virtual Router.

All the Virtual Machines associated with a Virtual Router are terminated automatically when the Virtual Router is deleted. Each VM can however be terminated individually at any time.

To create new VMs use the `onevrouter instantiate` command, or the “Instantiate VMs” dialog in Sunstone.

## High Availability

More than one Virtual Machine can be associated to a Virtual Router in order to implement a high-availability scenario. In this case, OpenNebula will also assign a floating IP to the group of Virtual Machines that will coordinate to manage the traffic directed to that IP.

To enable a high-availability scenario, you need to choose two or more instances when the Virtual Router is created in Sunstone. In the CLI, the number of VM instances is given with the `-m` option

```shell
onevrouter instantiate -h
[...]
-m, --multiple x          Instance multiple VMs
```

In this scenario, the following Virtual Router options become relevant:

* **Keepalived ID**: Optional. Sets keepalived configuration parameter `virtual_router_id`. If not set, OpenNebula will pick one for you.
* **Keepalived password**: Optional. Sets keepalived configuration parameter `authentication/auth_pass`.

And for each Virtual Network Interface:

* **Floating IP**. Select this to enable the floating IP. This adds the attribute `FLOATING_IP = yes` in the NIC.
* **Force IPv4**. Optional. With the floating IP option selected, this field requests a fixed IP for that floating IP, not the individual VM IPs.

The floating IP assignment is managed in a similar way to normal VM IPs. If you open the information of the Virtual Network, it will contain a lease assigned to the Virtual Router (not a VM). Besides the floating IP, you can choose to assign each VM their own individual IP in the network or not (set `FLOATING_ONLY = yes` in the NIC). In this case VRRP will run on one of the other VM NICs.

Other Virtual Machines in the network will use the floating IP to contact the Virtual Router VMs. At any given time, only one VM is using that floating IP address. If the active VM crashes, the other VMs will coordinate to assign the floating IP to a new Virtual Router VM.

## Customization

You can provide two optional parameters in the context to configure the keepalived service started in the Virtual Router VM:

* `VROUTER_KEEPALIVED_PASSWORD`: Password used for the service to protect the service from packages of rogue machines. By default the service is configured without a password.
* `VROUTER_KEEPALIVED_ID`: Number identifier of the service (1-255). This is useful when you have several Virtual Routers or other keepalived services in the same network. By default it is generated from the Virtual Router ID (`$vrouter_id & 255`) but you can specify it manually if needed.
* `FLOATING_IP` and `FLOATING_ONLY` controls the IP assignment  on the NIC interface. When the `FLOATING_IP` is set to `yes` an IP (`VROUTER_IP`) is assigned and shared across all VMs of the VR. When `FLOATING_ONLY` is set to `yes` no additional IP is allocated for that NIC.

These parameters can also be provided in the Virtual Router creation wizard of Sunstone.