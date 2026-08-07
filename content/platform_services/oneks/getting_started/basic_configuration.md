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

## OneKS Service

Install the OneKS package on the OpenNebula Front-end if it is not already installed:
```shell
sudo apt install -y opennebula-ks
```

Before starting the OneKS service for the first time, configure the datastore where the OneKS appliance image will be stored. OneKS creates the appliance image and VM template when the service starts, so the target datastore must be configured beforehand.

Edit the control-plane specification file:
```shell
/var/lib/one/oneks/controlplanes/general/controlplane.conf
```

Set `appliance_ds` under the `seed_vm` dependency to the ID of the image datastore where the OneKS appliance should be stored:
```shell
dependencies:
- object: seed_vm
  options:
    creation_timeout: 2000
    destroy_on_running: true
    appliance_id: c3ecb387-e726-49fe-975d-fa39c6d40d05
    appliance_ds: 1
```

Replace `1` with the ID of the target OpenNebula image datastore. The selected datastore must be accessible by the OpenNebula Hosts where the K8s Cluster VMs will be deployed.

Once the datastore configuration is correct, start the OneKS service on the command line of your OpenNebula Front-end:

```shell
sudo systemctl start opennebula-ks.service
```
Verify that the OneKS service is running:
```shell
sudo systemctl status opennebula-ks.service
```

The service should be in the active (`running`) state. If the service is in a failed state, try restarting it:
```shell
sudo systemctl restart opennebula-ks.service
```

{{< alert title="Warning" type="warning" >}}
Configure `appliance_ds` before starting `opennebula-ks.service` for the first time. If the service is started with the wrong datastore, OneKS may create the appliance image and VM template there. Changing `appliance_ds` afterwards does not automatically move or recreate these resources and may result in errors indicating that the IMAGE or TEMPLATE name is already in use. In that case, remove the previously generated OneKS image and VM template from OpenNebula, then restart `opennebula-ks.service` so OneKS can create them again using the configured datastore.
{{< /alert >}}

## OneGate Service

Verify that OneGate is configured and reachable. OneGate is required during K8s Cluster provisioning because the bootstrap process uses it to communicate with OpenNebula services.

Check the OneGate service status on the Front-end command line:

```shell
sudo systemctl status opennebula-gate.service
```

Validate the OneGate configuration using the OpenNebula OneGate [documentation]({{% relref "product/operation_references/opennebula_services_configuration/onegate/" %}}).

## Transparent Proxy Configuration

Verify that the [transparent proxy]({{% relref "product/virtual_machines_operation/virtual_machines_networking/tproxy/" %}}) is configured to expose OneGate and the OpenNebula API through the network interconnecting the Front-end and Hosts.

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
```

Replace `192.168.150.1` with the Front-end IP address used to connect to the Hosts and save the file. On the Front-end command line, as the `oneadmin` system user, sync the `OpenNebulaNetwork.conf` file with the hypervisor Hosts by running `onehost sync -f`. Power-cycle any guests that are already running so they use the updated transparent proxy configuration.

## Public and Private Virtual Networks

Identify the OpenNebula Virtual Network IDs that will be used by the K8s Cluster. On the Front-end command line, run the following command to inspect the available networks:

```shell
onevnet list
```

You need:

* A **public Virtual Network**, used as the gateway to the Internet and for external K8s Cluster connectivity.
* A **private Virtual Network**, used for internal communication between K8s Cluster nodes.

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

1. Download the latest release with the following command:

{{< tabpane text=true right=false >}}
{{% tab header="**Architecture**:" disabled=true /%}}

{{% tab header="x86-64"%}}
```shell
curl -fsSL "https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```
{{% /tab %}}

{{% tab header="ARM64"%}}
```shell
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
```
{{% /tab %}}
{{< /tabpane >}}

To download a specific version of kubectl, replace `$(curl -L -s https://dl.k8s.io/release/stable.txt)` in the above commands with the version number. E.g. for version 1.36.0:

{{< tabpane text=true right=false >}}
{{% tab header="**Architecture**:" disabled=true /%}}

{{% tab header="x86-64"%}}
```shell
curl -fsSL "https://dl.k8s.io/release/v1.36.0/bin/linux/amd64/kubectl"
```
{{% /tab %}}

{{% tab header="ARM64"%}}
```shell
curl -LO "https://dl.k8s.io/release/v1.36.0/bin/linux/arm64/kubectl"
```
{{% /tab %}}
{{< /tabpane >}}

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

3. Ensure the version you have installed is up-to-date or the expected version:

```shell
kubectl version --client
```

If the above command is not suitable for your Front-end Host configuration, consult the [kubectl installation documentation](https://kubernetes.io/docs/tasks/tools/) for [MacOS](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/) or [Windows](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/).

## Automatically Generated Resources

When OneKS starts, it automatically downloads the OneKS appliance from the OpenNebula Marketplace. During this process, OneKS creates the corresponding OpenNebula image and VM template in the OpenNebula database, making them ready to deploy K8s Clusters.

The datastore used for the appliance image must be configured before the first time that the OneKS service is started. See the OneKS Service section above.

{{< alert title="Warning" type="warning" >}}
If the OneKS appliance cannot be downloaded correctly, the OneKS service will not start. Refer to the [Service Management Documentation]({{% relref "platform_services/oneks/management/configuration/#service-management" %}}) for details on how to restart the service or inspect its journal.

You can also check the OneKS service logs at `/var/log/one/oneks.log`.
{{< /alert >}}

The generated image is used by the Seed VM to start the K8s Cluster deployment process. For more information about the Seed VM role during provisioning, see the [Seed VM section]({{% relref "platform_services/oneks/getting_started/core_concepts/#seed-vm" %}}) in Core Concepts.

The appliance ID and target image datastore can be configured from the control-plane specification file:
```default
/var/lib/one/oneks/controlplanes/general/controlplane.conf
```

You can also configure the datastore where the appliance image will be stored. This datastore must be accessible by the OpenNebula Hosts where the K8s Cluster VMs will be deployed.

Example configuration:

```yaml
dependencies:
  - object: seed_vm
    options:
      creation_timeout: 2000
      destroy_on_running: true
      appliance_name: OneKS Appliance
      appliance_id: c3ecb387-e726-49fe-975d-fa39c6d40d05
      appliance_ds: 1
```

`appliance_ds` specifies the OpenNebula image datastore where the downloaded appliance image will be created. The datastore must be accessible by the OpenNebula Hosts where the K8s Cluster VMs will be deployed.

Do not change `appliance_ds` after OneKS has already generated the appliance resources unless you also remove the existing OneKS image and VM template. Otherwise, OneKS may fail to recreate them because resources with the same names already exist.

## Next Steps

After completing the basic configuration steps described here, you are ready to start provisioning K8s Clusters with OneKS. Move on to the [OneKS Quick-start Guide]({{% relref "platform_services/oneks/getting_started/quick_start/" %}}) to learn how to deploy a basic K8s Cluster.
