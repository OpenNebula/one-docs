---
title: "Creating and Configuring Tenants"
linkTitle: "Multitenancy"
description: ""
weight: 3
---

This guide shows how to create tenants for three services in OpenNebula: **GPU as a Service**, **Kubernetes as a Service** and **Token Factory**. Kubernetes as a Service uses OneKS. Token Factory uses OneLLM and LiteLLM.

As **ncp-operator**, create each tenant's group and administrator, assign the service view, associate infrastructure resources through a VDC, and set quotas.

Start with the procedure for **GPU as a Service**, which creates `vm-tenant` from scratch. The [Tenants for OneKS and OneLLM](#tenants-for-oneks-and-onellm) section then gives the settings for the other two services.

The GPU as a Service example creates the following objects:

| **Object** | **Name or setting** | **Purpose** |
| --- | --- | --- |
| Group | `vm-tenant` | Groups the tenant's users and resources. |
| Group administrator | `vm-tenant-admin` | Manages the tenant's users and resources. |
| Sunstone view | **VMs view** | Gives the tenant the interface for VM management. |
| Virtual network | `vm-public` | Connects the tenant's VMs. |
| Virtual Data Center (VDC) | `vm-tenant-vdc` | Gives the tenant access to selected Hosts, datastores and networks. |
| Group quota | **PCI Devices**: `1` | Limits the tenant's VMs to one non-network PCI device, such as a GPU. |

## Before Starting

Connect to the PoC VPN as described in the [Connection Guide]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}}). Sign into Sunstone as **ncp-operator** with **Admin** view.

The account must have permission to create groups, users, Virtual Networks and VDCs, assign resources, set group quotas and create ACL rules. The PoC includes the service views used in this guide.

## Step 1: Create the Tenant Group and Administrator

1. Open **System -> Groups** and click **Create Group**.
2. Set the group name to `vm-tenant`.
3. Enable **Create an administrator user**.
4. Set the administrator username to `vm-tenant-admin`.
5. Select **core** authentication, then enter and confirm a password.
6. Click **Next** to open **Permissions**. Continue with Step 2 in the same wizard.

The wizard creates the user with `vm-tenant` as its primary group and makes it the administrator of that group.

{{< image
  path="/images/poc/ai_poc/multitenancy/group-admin.png"
  alt="Create a tenant group and its administrator" align="center" width="90%" mb="20px"
>}}

## Step 2: Assign Permissions and the Service View

In **Permissions**:

1. Under **Permissions - Create**, select **VMs** and clear the other options.
2. Leave the **Permissions - View** options cleared for this example.
3. Click **Next** to open **Views**.

The creation permission lets the tenant instantiate VMs. **Permissions - View** controls access to resources owned by other members of the group. The group administrator can manage the tenant's resources.

{{< image
  path="/images/poc/ai_poc/multitenancy/vm-permissions.png"
  alt="VM creation permission for the VM service" align="center" width="90%" mb="20px"
>}}

In **Views**, configure both group members and the administrator:

1. Under **Views - Groups**, set **Default view** to **VMs view**. Enable **VMs view** and disable the other views.
2. Under **Views - Admin**, set **Default view** to **VMs view**. Enable **VMs view** and disable the other views.
3. Continue to **System**, keep the default settings, and click **Finish**.

The view selects the Sunstone interface. The permissions determine which operations the user can perform. Set both view sections so that the tenant administrator and group members use the service interface.

{{< image
  path="/images/poc/ai_poc/multitenancy/service-views.png"
  alt="Select VMs view for both group members and group administrators" align="center" width="90%" mb="20px"
>}}

## Step 3: Create the Tenant Virtual Network

1. Open **Networks -> Virtual Networks** and start the creation wizard.
2. Set the network name to `vm-public`.
3. Associate the network with the OpenNebula Cluster that contains the Hosts for the tenant's VMs.
4. Select the network driver and the bridge or VLAN configured on those Hosts.
5. Add an IPv4 address range. Set the first address and size to an available range in your infrastructure.
6. Set the subnet mask, gateway and DNS for that network, then save it.

Use the following network settings for this PoC:

| **Setting** | **Value** |
| --- | --- |
| OpenNebula Cluster | `default` (`0`) |
| Driver | **Bridged** |
| Physical device | `enp33s0f2np2` |
| Custom bridge name | `br0` |
| First IPv4 address / size | `10.16.6.120` / `20` |
| Network mask | `255.255.255.0` |
| Gateway | `10.16.6.1` |
| DNS | `8.8.8.8` |

The address range supplies IP addresses for the tenant's VMs. In Step 4, add this network to the tenant's VDC to grant access to it.

See [Defining and Managing Virtual Networks]({{% relref "product/cluster_configuration/networking_system/manage_vnets/" %}}) for driver and address range settings.

{{< image
  path="/images/poc/ai_poc/multitenancy/network-general.png"
  alt="Create the tenant virtual network on the assigned OpenNebula cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/network-bridge.png"
  alt="Set the virtual network bridge for the infrastructure" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/network-address-range.png"
  alt="Add an IPv4 address range to the tenant network" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/network-context.png"
  alt="Set the tenant network mask, gateway and DNS" align="center" width="90%" mb="20px"
>}}

## Step 4: Assign Infrastructure Through a VDC

A VDC associates the tenant group with the infrastructure that it can use.

1. Open **System -> VDCs** and start the creation wizard.
2. Set the VDC name to `vm-tenant-vdc`.
3. In **Groups**, select `vm-tenant`.
4. In **Resources**, select the zone and the individual resources for this tenant:

   * Hosts with the required CPU, memory and an available GPU for PCI passthrough.
   * Compatible image and system datastores for the VM disks.
   * The `vm-public` Virtual Network created in Step 3.

5. Save the VDC.

For this PoC, select Host `10.16.6.18` and datastores `system`, `default` and `files`.

Select individual Hosts, datastores and networks to control the allocation. Selecting an entire OpenNebula Cluster also gives access to that Cluster's networks and datastores.

{{< image
  path="/images/poc/ai_poc/multitenancy/vdc-group.png"
  alt="Associate the tenant group with its VDC" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/vdc-host-storage.png"
  alt="Select the VDC datastores and hosts" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/vdc-network.png"
  alt="Select the tenant virtual network for the VDC" align="center" width="90%" mb="20px"
>}}

Open the saved VDC and confirm that it contains `vm-tenant` and the selected resources.

{{< image
  path="/images/poc/ai_poc/multitenancy/vdc-saved.png"
  alt="Saved tenant VDC with its allocated resource counts" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/vdc-saved-group.png"
  alt="Tenant group associated with its saved VDC" align="center" width="90%" mb="20px"
>}}

The VDC grants access to infrastructure. It does not reserve a physical GPU. See [VDCs]({{% relref "product/cloud_system_administration/multitenancy/manage_vdcs/" %}}) for more details.

## Step 5: Set the Tenant Quotas

Set a group quota to limit the GPU allocation across the tenant's VMs:

1. Open **System -> Groups** and select `vm-tenant`.
2. Open **Quota** and select **VM Quota**.
3. Under **Cluster ID**, select **@Global**.
4. Select **PCI Devices** as the identifier.
5. Set the value to `1` and click **Apply**.

This sets `PCI_DEV = 1` across the group's VMs. When the only non-network PCI devices requested are GPUs, the tenant can allocate one GPU. The quota counts device entries; it does not select a GPU model or limit GPU memory.

{{< image
  path="/images/poc/ai_poc/multitenancy/pci-quota.png"
  alt="Set the tenant group global PCI Devices quota to one" align="center" width="90%" mb="20px"
>}}

You can also set limits for CPU, memory and the number of VMs in **VM Quota**. See [Usage Quotas]({{% relref "product/cloud_system_administration/capacity_planning/quotas/" %}}).

The `vm-tenant` setup is complete. Continue with [GPU as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}}) to prepare the VM template and grant the tenant access to it.

## Tenants for OneKS and OneLLM

To create a tenant for another service, repeat Steps 1 to 5 with these names and views:

| **Service** | **Tenant group** | **Group administrator** | **Sunstone view** | **VDC** |
| --- | --- | --- | --- | --- |
| Kubernetes as a Service | `k8s-tenant` | `k8s-tenant-admin` | **OneKS view** | `k8s-tenant-vdc` |
| Token Factory | `llm-tenant` | `llm-tenant-admin` | **AI Operator view** | `llm-tenant-vdc` |

### Permissions and Views

In Step 2, under **Permissions - Create**, select **VMs**, **Image**, **Template**, **Virtual router**, **Security group** and **Platform Resources**. Clear the other creation options. Keep the **Permissions - View** options cleared for this example.

OneKS creates images, VM templates, virtual routers and VMs for the Kubernetes infrastructure. **Platform Resources** includes the documents used for Clusters, node groups, models and deployments. VM creation permission is required for both services.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-permissions.png"
  alt="Allow creation of the resources required by OneKS" align="center" width="90%" mb="20px"
>}}

Set the service view as the default and enabled view in both **Views - Groups** and **Views - Admin**. Disable the other views. Use **OneKS view** for Kubernetes management or **AI Operator view** for Kubernetes and OneLLM model deployments.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-views.png"
  alt="Select OneKS view for the Kubernetes tenant and its administrator" align="center" width="90%" mb="20px"
>}}

### Kubernetes Services: OneKS and OneLLM

Prepare two networks before the tenant administrator creates a Kubernetes Cluster:

| **Network** | **Purpose** | **Address ranges** |
| --- | --- | --- |
| Public network | External Cluster access and LoadBalancer service addresses | IPv4 and ETHER |
| Private network | Communication between the Cluster router, control plane and workers | IPv4 |

For OneLLM, use this procedure for the LiteLLM service Cluster and the inference Cluster. LiteLLM must be able to reach the inference gateway. Their service addresses must also be reachable from the PoC VPN.

#### Prepare the Public Network

1. Open **Networks -> Virtual Networks** and create the public network for the tenant: `k8s-public` for OneKS or `llm-public` for OneLLM.
2. Associate it with the physical OpenNebula Cluster that will Host the Kubernetes VMs.
3. Configure the bridge or VLAN, subnet mask, gateway and DNS supplied for the infrastructure.
4. In **Address Ranges**, confirm that the IPv4 range has free addresses for Cluster access and LoadBalancer Services.

Use the public-network driver, bridge, mask, gateway and DNS from the VM network procedure, with these IPv4 ranges:

| **Service** | **Public network** | **First IPv4 address** | **Size** |
| --- | --- | --- | --- |
| Kubernetes as a Service | `k8s-public` | `10.16.6.40` | `20` |
| Token Factory | `llm-public` | `10.16.6.100` | `20` |

Create the IPv4 range first, then add the ETHER range below.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-public-ipv4.png"
  alt="Public Kubernetes network with an IPv4 address range" align="center" width="90%" mb="20px"
>}}

Add the ETHER range used by the OpenNebula cloud controller manager (CCM):

1. Click **Add Address Range**.
2. Set **Address range type** to **Ethernet / DHCP**.
3. Set **Size** to the required MAC address capacity, for example `10`.
4. Leave **Shared** disabled and **First MAC address** empty.
5. Click **Accept** and confirm that both ranges appear in the list.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-ether-create.png"
  alt="Add an Ethernet address range for OpenNebula LoadBalancer routers" align="center" width="90%" mb="20px"
>}}

The PoC CCM uses IPv4 range **ID 0** for service IP addresses and ETHER range **ID 1** for LoadBalancer router MAC addresses. Check these IDs in the saved network. The ETHER range does not supply the service IP addresses.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-public-ranges.png"
  alt="Saved public network with IPv4 range ID 0 and ETHER range ID 1" align="center" width="90%" mb="20px"
>}}

#### Create the Private Network

1. Create the private network: `k8s-private` for OneKS or `llm-private` for OneLLM.
2. Select the infrastructure's private bridge or VLAN and the same physical OpenNebula Cluster as the public network.
3. Use the private subnet and mask assigned to the tenant. The subnet must not overlap the public network or the Kubernetes pod and service networks.
4. Add an IPv4 address range with capacity for the Cluster router, control plane and workers.
5. Leave **Gateway** unset. OneKS configures the Cluster router's private IP as the nodes' gateway.
6. Save the network.

The private network must connect all Hosts where the Cluster VMs can run. A bridge without an uplink connects VMs on one Host only. For multiple Hosts, use the shared Layer 2 network prepared for the infrastructure. See [OneKS network configuration]({{% relref "platform_services/oneks/getting_started/basic_configuration/" %}}).

In this PoC, create each private network on OpenNebula Cluster `0` with the **Bridged** driver and bridge `natbr0`.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-private-general.png"
  alt="Name the private Kubernetes network and select its physical OpenNebula cluster" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-private-bridge.png"
  alt="Select the Bridged driver and the prepared private bridge" align="center" width="90%" mb="20px"
>}}

Use these private IPv4 ranges, with mask `255.255.255.0` and **Gateway** empty:

| **Service** | **Private network** | **First IPv4 address** | **Size** |
| --- | --- | --- | --- |
| Kubernetes as a Service | `k8s-private` | `192.168.160.1` | `254` |
| Token Factory | `llm-private` | `192.168.150.2` | `253` |

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-private-address-range.png"
  alt="Add the private IPv4 address range with its first address and size" align="center" width="90%" mb="20px"
>}}

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-private-context.png"
  alt="Set the private subnet mask and leave Gateway unset for OneKS" align="center" width="90%" mb="20px"
>}}

In Step 4, include both networks in the tenant VDC. Give the tenant administrator the network names and the physical OpenNebula Cluster to use.

{{< image
  path="/images/poc/ai_poc/multitenancy/kubernetes-vdc-networks.png"
  alt="Include the public and private Kubernetes networks in the tenant VDC" align="center" width="90%" mb="20px"
>}}

### Resource Access and Quotas

In Step 4, select Hosts and datastores with capacity for the Kubernetes control planes, workers and router VMs. For OneLLM, include capacity for both the LiteLLM service Cluster and the inference Cluster.

Also grant the tenant group **USE** on the physical OpenNebula Cluster that the tenant administrator will select in the Kubernetes creation wizard:

1. Open **System -> ACLs** and create a rule.
2. Set the subject to the tenant **Group**: `k8s-tenant` or `llm-tenant`.
3. Select resource type **Cluster**.
4. Set **Scope** to **Identifier** and select the specific Cluster ID.
5. Select the **USE** right and save the rule.

This rule lets the wizard read the Cluster. The VDC determines the Host, network and datastore allocation.

In Step 5, size the CPU, memory and VM quotas for all the Kubernetes VMs required by the service. The PCI quota applies to GPUs attached to workers. A worker can use one GPU for several model deployments when GPU sharing is configured.

## Next Steps

Give the tenant administrator the Sunstone address, username and password, and the names of the assigned networks. Then continue with the service guide:

* [GPU as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}}): as **ncp-operator**, import the appliance, configure its GPU VM template, and grant `vm-tenant` access. The tenant administrator then creates the VM.
* [Kubernetes as a Service]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_k8s/" %}}): grant `k8s-tenant` access to the OneKS appliance. The tenant administrator then creates the Kubernetes Cluster.
* [Token Factory]({{% relref "solutions/engineering_blueprints/ai_poc/ai_inference/" %}}): grant `llm-tenant` access to the OneKS appliance. The tenant administrator then creates the service and inference Clusters.

## PoC Success Criteria

This guide covers the configuration steps for these PoC success criteria:

* [SC16]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create additional users.
* [SC17]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create additional groups.
* [SC19]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create a VDC and assign it to a group.
* [SC20]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create and assign quotas to groups.
