---
title: "Basic Configuration"
linkTitle: "Basic Configuration"
date: "2026-05-12"
description:
categories:
tags:
weight: "2"
type: docs
---

Before creating a K8s Cluster, ensure that the minimum required components are configured and available.

## Install and Configure the OneKS Service

Install the OneKS package on the OpenNebula Front-end if it is not already installed:
```shell
sudo apt install -y opennebula-ks
```

OneKS uses an appliance from the OpenNebula Marketplace to bootstrap K8s Clusters. By default, it imports this appliance into the default OpenNebula image datastore when the service starts. Ensure that this datastore is accessible to the OpenNebula Cluster where K8s Clusters will be deployed. To make the appliance available to additional Clusters or configure it for air-gapped environments, see [Appliance Configuration]({{% relref "platform_services/oneks/management/configuration/#appliance-configuration" %}}).

## Confirm the Status of the OneGate Service

Verify that OneGate is properly configured and reachable. OneGate is required during K8s Cluster provisioning because the bootstrap process uses it to communicate with other OpenNebula services.

Check the OneGate service status on the Front-end command line:

```shell
sudo systemctl status opennebula-gate.service
```

Validate the OneGate configuration using the OpenNebula [OneGate Documentation]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}).

## Transparent Proxy Configuration

Verify that the [transparent proxy]({{% relref "product/virtual_machines_operation/virtual_machines_networking/tproxy/" %}}) is configured to expose OneGate, the OpenNebula API, and the OneKS API through the network interconnecting the Front-end and Hosts. Access to the OneKS API through TProxy is required by the in-cluster monitor.

The configuration is typically defined in the following location on the OpenNebula Front-end:

```default
/var/lib/one/remotes/etc/vnm/OpenNebulaNetwork.conf
```

{{< alert title="Warning" type="warning" >}}
If the transparent proxy configuration file cannot be found or loaded correctly, the OneKS service will not start. See [Service Management]({{% relref "platform_services/oneks/management/configuration/#service-management" %}}) to restart the service or inspect its journal.

You can also check the OneKS service logs at `/var/log/one/oneks.log`.
{{< /alert >}}

Example configuration:

```yaml
:tproxy:
  - :remote_addr: 192.168.150.1 # Front-end IP
    :remote_port: 5030
    :service_port: 5030
  - :remote_addr: 192.168.150.1 # Front-end IP
    :remote_port: 2633
    :service_port: 2633
  - :remote_addr: 192.168.150.1 # Front-end IP
    :remote_port: 10780
    :service_port: 10780
```

The entries expose OneGate on port `5030`, OpenNebula XML-RPC on port `2633`, and the OneKS API on port `10780`. Replace `192.168.150.1` with the Front-end IP address used to connect to the Hosts and save the file. When the monitor is enabled, configure `:server` / `:bind` in `oneks-server.conf` with this Front-end address, or with `0.0.0.0`, so OneKS accepts the forwarded connections. On the Front-end command line, as the `oneadmin` system user, sync the `OpenNebulaNetwork.conf` file with the hypervisor Hosts by running `onehost sync -f`.

Before provisioning K8s Clusters, set `ONEGATE_ENDPOINT` in `/etc/one/oned.conf` to the TProxy address:

```default
ONEGATE_ENDPOINT = "http://169.254.16.9:5030"
```

Restart OpenNebula to apply the change:

```shell
sudo systemctl restart opennebula.service
```

The link-local endpoint makes guest contextualization configure the route to `169.254.16.9`. This route is also needed to reach the OpenNebula and OneKS APIs through TProxy. Leaving the endpoint set to the Front-end IP can cause the OneKS readiness check to time out on the private network.

For installations managed with OneDeploy, set both values in the inventory variables for the Front-end so that subsequent OneDeploy runs preserve the configuration:

```yaml
gate_endpoint: http://169.254.16.9:5030
gate_tproxy:
  - { ":service_port": 5030, ":remote_addr": 192.168.150.1, ":remote_port": 5030 }
  - { ":service_port": 2633, ":remote_addr": 192.168.150.1, ":remote_port": 2633 }
  - { ":service_port": 10780, ":remote_addr": 192.168.150.1, ":remote_port": 10780 }
```

Replace `192.168.150.1` with the same Front-end address used above. Without these inventory settings, re-running OneDeploy can reset the endpoint and proxy list.

## Start the OneKS Service

Once the above configuration steps are complete, enable and start the OneKS service on the command line of your OpenNebula Front-end. Enabling the service also starts it automatically after a Front-end reboot:

```shell
sudo systemctl enable --now opennebula-ks.service
```

Verify that the OneKS service is running:
```shell
sudo systemctl status opennebula-ks.service
```

The service should be in the active (`running`) state. If you changed `oneks-server.conf` while OneKS was running, or the service is in a failed state, restart it:
```shell
sudo systemctl restart opennebula-ks.service
```

## Public and Private Virtual Networks

Identify the OpenNebula Virtual Network IDs that will be used by the K8s Cluster. On the Front-end command line, run the following command to inspect the available networks:

```shell
onevnet list
```

You need:

* A **public Virtual Network**, used as the gateway to the Internet and for external K8s Cluster connectivity.
* A **private Virtual Network**, used for internal communication between K8s Cluster nodes.

Both networks must be available in the OpenNebula Cluster selected for the K8s Cluster. The private network connects the Cluster router, control plane, and workers, so it must span every Host where these VMs can run. A bridge without an uplink only connects VMs on the same Host. For deployments across multiple Hosts, use a shared Layer 2 network, such as [802.1Q]({{% relref "product/cluster_configuration/networking_system/vlan" %}}) or [VXLAN]({{% relref "product/cluster_configuration/networking_system/vxlan" %}}).

For example, if you have already configured a bridge named `br-private` connected to the same private Layer 2 network on every Host, save the following template as `oneks-private.net`:

```default
NAME = "oneks-private"
VN_MAD = "bridge"
BRIDGE = "br-private"
NETWORK_ADDRESS = "10.20.0.0"
NETWORK_MASK = "255.255.255.0"

AR = [
  TYPE = "IP4",
  IP = "10.20.0.10",
  SIZE = "100"
]
```

Replace the bridge name, subnet, and address range with values for your deployment. Choose a subnet that does not overlap the public network. Leave `GATEWAY` unset: OneKS supplies the Cluster router's private IP as the gateway for the nodes. See [Bridged Networking]({{% relref "product/cluster_configuration/networking_system/bridged" %}}) for Host bridge configuration.

Create the network as `oneadmin`, replacing `<CLUSTER_ID>` with the target OpenNebula Cluster ID:

```shell
onevnet create oneks-private.net --cluster <CLUSTER_ID>
```

Use the returned Virtual Network ID as the private network when checking readiness and creating the K8s Cluster.

### Network MTU

{{< alert title="Warning" type="warning" >}}
Provisioning can fail on VM networks with an MTU below 1500 because the TProxy veth devices retain MTU 1500. This can cause repeated control-plane VM creation and a `PROVISIONING_FAILURE` state. VXLAN over a standard 1500-byte underlay is one affected configuration.

Use VM networks with MTU 1500 on an underlay that supports the additional encapsulation overhead. If you use a lower VM network MTU, a temporary workaround is to set both TProxy veth devices to the bridge MTU on every Host where the network is used:

```shell
sudo ip link set <bridge>b mtu <MTU>
sudo ip netns exec one_tproxy_<bridge> ip link set <bridge>a mtu <MTU>
```

Replace `<bridge>` with each public or private network bridge name and `<MTU>` with that bridge's MTU. For example, for a `br-private` bridge with MTU 1450, set `br-privateb` on the Host and `br-privatea` inside namespace `one_tproxy_br-private`.

The commands require existing TProxy devices, which are created when a VM activates the network; creating the Virtual Network alone does not create them. Apply the workaround before retrying provisioning, and repeat it after Host reboots or whenever the devices are recreated.
{{< /alert >}}

## User Permissions

Verify that the user has permission to create and manage OneKS K8s Clusters and the related OpenNebula resources, including Virtual Machines, Virtual Networks, images, and templates.

OneKS stores its K8s Cluster and node-group definitions as OpenNebula documents. The user must therefore also have the required permissions to manage OpenNebula document resources. Without document permissions, OneKS may be able to reach the infrastructure resources but fail when creating, updating, or deleting the OneKS records that represent the K8s Cluster lifecycle.

Use OpenNebula ACL rules to grant the required permissions for the target users or groups. For more information, see the [Managing ACL Rules]({{% relref "product/cloud_system_administration/multitenancy/chmod#manage-acl" %}}) documentation.

## kubectl Client

[kubectl](https://kubernetes.io/docs/reference/kubectl/) is the official command-line interface for Kubernetes. kubectl communicates with K8s Clusters launched by OneKS remotely from the Front-end Host, removing the need to interact directly with the K8s Cluster VMs themselves. kubectl handles the following key functions:

* **K8s Cluster Management**: View nodes, health status, and resource usage.
* **Workload Deployment**: Create, update, and delete pods, services and containerized application deployments.
* **Troubleshooting**: Retrieving logs, describing pod and node statuses or errors.
* **Configuration**: Manage secrets, environment variables and storage.

kubectl must be installed on the Front-end Host machine. On a Linux machine, run the following command to install kubectl:

1. Download kubectl for the Kubernetes minor version you plan to deploy. The following example downloads the latest patch release for Kubernetes 1.35; replace `1.35` if you select a different Cluster version. Kubernetes supports kubectl within one minor version of the API server; using the same minor version avoids version-skew warnings. See the [Kubernetes version-skew policy](https://kubernetes.io/releases/version-skew-policy/#kubectl).

{{< tabpane text=true right=false >}}
{{% tab header="**Architecture**:" disabled=true /%}}

{{% tab header="x86-64"%}}
```shell
curl -fLO "https://dl.k8s.io/release/$(curl -fsSL \
https://dl.k8s.io/release/stable-1.35.txt)/bin/linux/amd64/kubectl"
```
{{% /tab %}}

{{% tab header="ARM64"%}}
```shell
curl -fLO "https://dl.k8s.io/release/$(curl -fsSL \
https://dl.k8s.io/release/stable-1.35.txt)/bin/linux/arm64/kubectl"
```
{{% /tab %}}
{{< /tabpane >}}

To download a specific patch release, replace `$(curl -fsSL https://dl.k8s.io/release/stable-1.35.txt)` in the commands above with its version number, including the `v` prefix, such as `v1.35.0`.

2. Install kubectl:

```shell
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

{{< alert title="Note" type="primary" >}}
If you do not have root access on the target system, you can still install kubectl to the `~/.local/bin` directory:
```shell
chmod +x kubectl
mkdir -p ~/.local/bin
mv ./kubectl ~/.local/bin/kubectl
# and then append (or prepend) ~/.local/bin to $PATH
```
{{< /alert >}}

3. Verify that the installed client has the expected version:

```shell
kubectl version --client
```

If the above command is not suitable for your Front-end Host configuration, consult the [kubectl installation documentation](https://kubernetes.io/docs/tasks/tools/) for [MacOS](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/) or [Windows](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/).

## Automatically Generated Resources

When OneKS starts, it automatically downloads the OneKS appliance from the OpenNebula Marketplace. During this process, OneKS creates the corresponding OpenNebula image in the default OpenNebula image datastore with its VM Template, making them ready to deploy K8s Clusters that use that datastore.

{{< alert title="Warning" type="warning" >}}
If the OneKS appliance cannot be downloaded correctly, the OneKS service will
not start. Check the OneKS service logs at `/var/log/one/oneks.log` and refer
to the [Service Management Documentation]({{% relref "platform_services/oneks/management/configuration/#service-management" %}})
for details on restarting the service or inspecting its journal.

To use a manually imported appliance instead of creating it automatically, see
the [Appliance Configuration]({{% relref "platform_services/oneks/management/configuration/#appliance-configuration" %}})
section.
{{< /alert >}}

The generated image is used by the Seed VM to start the K8s Cluster deployment process. For more information about the Seed VM role during provisioning, see the [Seed VM section]({{% relref "platform_services/oneks/getting_started/core_concepts/#seed-vm" %}}) in Core Concepts.

The appliance ID is configured in the control-plane specification file:
```default
/var/lib/one/oneks/controlplanes/general/controlplane.conf
```

Example configuration:

```yaml
dependencies:
  - object: seed_vm
    options:
      creation_timeout: 2000
      destroy_on_running: true
      appliance_name: OneKS Appliance
      appliance_id: c3ecb387-e726-49fe-975d-fa39c6d40d05
```

## Next Steps

After completing the basic configuration steps described here, you are ready to start provisioning K8s Clusters with OneKS. Move on to the [OneKS Quick-start Guide]({{% relref "platform_services/oneks/getting_started/quick_start/" %}}) to learn how to deploy a basic K8s Cluster.
