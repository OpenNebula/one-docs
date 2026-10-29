---
title: "On-premises AI Factory Deployment"
linkTitle: "On-premises Deployment"
date: "2025-10-21"
weight: 2
tags: ['AI']
---

<a id="cd_on-premises"></a>

Machine Learning (ML) training and inference are resource-intensive tasks that often require the full power of a dedicated GPU. PCI passthrough allows a Virtual Machine (VM) to have exclusive access to a physical GPU, delivering bare-metal performance for the most demanding AI workloads.

In this guide you will find the details to deploy and configure an AI-ready OpenNebula cloud using the [OneDeploy](https://github.com/OpenNebula/one-deploy) tool. It covers the general process of preparing an environment for demanding AI workloads by leveraging PCI passthrough for GPUs such as the NVIDIA H100 and L40S.

## Prerequisites

Before you begin, ensure your environment meets the following prerequisites.

### Hardware Requirements

The virtualization Hosts (hypervisors) must support I/O MMU virtualization:
*   **Intel CPUs**: Must support **VT-d**.
*   **AMD CPUs**: Must support **AMD-Vi**.

You must enable this feature in your server's BIOS/UEFI. Refer to your hardware vendor's documentation for instructions.

### Kernel Configuration (Manual Step)

OneDeploy checks that IOMMU support is active on each hypervisor node, but does not configure the kernel boot parameters. If necessary, update them manually before deployment.

Before modifying the kernel parameters, check if IOMMU is already active by inspecting the `/sys/kernel/iommu_groups/` directory on the hypervisor.

```shell
ls /sys/kernel/iommu_groups/
```

If this directory exists and contains subdirectories (e.g., `0/`, `1/`, etc.), IOMMU is likely active. An empty directory or a non-existent directory indicates that IOMMU is not correctly enabled in your kernel or BIOS/UEFI.

Kernel requirements depend on the CPU and kernel configuration:

* For Intel CPUs: add `intel_iommu=on` if IOMMU is not already enabled by default.
* For AMD CPUs: the kernel normally enables IOMMU once AMD-Vi is enabled in the BIOS/UEFI. No additional enable parameter is usually required.

Optionally, add `iommu=pt` to use identity mappings for devices used by the Host. This option is not required for PCI passthrough.

For details, refer to the [Host Configuration Guide]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration.md#enable-the-iommu-in-the-kernel" %}}).

### Hypervisor Preparation

For a correct performance of the PCI passthrough with NVIDIA GPUs, start with a clean state on the hypervisor nodes regarding NVIDIA drivers.

Avoid pre-installing NVIDIA drivers on the hypervisor nodes before running the OneDeploy playbook. An active proprietary NVIDIA driver will claim the GPU and prevent other drivers, like `vfio-pci`, from binding to the device. This will block the PCI passthrough configuration from succeeding.

### Hostname Resolution

Every Front-end and hypervisor Host must resolve the system hostname of every Front-end through DNS or `/etc/hosts`.

For a static inventory without DNS, use the servers' existing hostnames as inventory names and set `ensure_hosts: true` under `all.vars`. OneDeploy then adds missing `/etc/hosts` entries using each server's `ansible_host` address and inventory name. Existing entries are preserved.

Both `ensure_hosts` and `ensure_hostname` default to `false`. Setting `ensure_hostname: true` changes each server's system hostname to its inventory name. Enable it only if you intend to rename the servers.

### Setting Up OneDeploy

The OneDeploy tool is a collection of Ansible playbooks that streamline the installation of OpenNebula. Before running this collection, prepare your control node which is the machine where you will execute the Ansible commands.

1.  **Clone the repository**:

    Switch to the root user:

    ```shell
    sudo -i
    ```

    Clone the OneDeploy repository:

    ```shell
    git clone https://github.com/OpenNebula/one-deploy.git
    cd one-deploy
    ```

2.  **Install dependencies**:
    OneDeploy requires Ansible and a few other Python libraries. For detailed system requirements and setup instructions, consult the [Platform Notes](https://github.com/OpenNebula/one-deploy/wiki/sys_reqs) in the official wiki. Run the following commands as the root user:

    Install PIPx:

    ```bash
    apt update
    apt install pipx
    ```

    Install [Hatch](https://hatch.pypa.io/latest/):

    ```bash
    pipx install hatch==1.16.5
    pipx ensurepath
    source ~/.bashrc
    ```
    From within the one-deploy directory install the requirements:

    ```bash
    apt install make
    make requirements
    ```

    `make requirements` creates the Hatch environment and installs OneDeploy's dependencies, including Ansible. The deployment commands use this environment automatically. You can optionally run `hatch shell` to use the environment interactively.

    For guidance on how to execute the playbooks in different cloud architectures, consult the [Playbook Usage Guide](https://github.com/OpenNebula/one-deploy/wiki/sys_use).

3.  **Configure SSH access**:

    The inventories below use `ansible_user: root`. Configure passwordless root SSH from the control node to every Host in the inventory, including the Front-end and hypervisors.

    Reuse an existing root SSH key if available. If root does not have an SSH key, create one:

    ```shell
    ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" -q
    ```

    Copy the public key to each remote Host, using its `ansible_host` address in place of `<HOST_IP>`. If you use an existing key, adjust the public key path:

    ```shell
    ssh-copy-id -i /root/.ssh/id_ed25519.pub root@<HOST_IP>
    ```

    If the control node is also a Host in the inventory, authorize the key locally as well. Root must be able to connect through that Host's `ansible_host` address:

    ```shell
    cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
    ```

## AI Factory Deployment

Once the prerequisites including configurations and dependencies are met, proceed to deploy your AI Factory with OneDeploy.

### Configure a Network Bridge for the VMs

The following AI Factory deployment examples assume the configuration of a bridge for the VMs to attach to. You will normally find the network configuration of your server in `/etc/netplan/` named something like `50-cloud-init.yaml`. You may need to update this file.

The following example configures a Linux bridge named `br0` on the OpenNebula Host. The physical interface `enp33s0f0np0` is enslaved to the bridge, and the Host IP address is assigned to `br0` rather than directly to the physical NIC. OpenNebula bridged Virtual Networks attach VM NICs to this Host bridge, allowing VMs to communicate through the underlying physical network.

```yaml
network:
  version: 2
  ethernets:
    enp33s0f0np0:
      dhcp4: false
    enp33s0f1np1:
      dhcp4: true
      dhcp4-overrides:
        use-routes: false
    enp33s0f2np2:
      dhcp4: true
      dhcp4-overrides:
        use-routes: false

  bridges:
    br0:
      interfaces:
        - enp33s0f0np0
      addresses:
        - 10.0.1.18/24
      nameservers:
        addresses:
          - 10.0.1.1
          - 1.1.1.1
      routes:
        - to: default
          via: 10.0.1.1
      parameters:
        stp: false
        forward-delay: 0
```

Update the following parameters with values corresponding to your setup:

* `enp33s0f0np0`: Physical NIC connected to the network to be used by OpenNebula VMs.
* `br0`: Linux bridge name. This must match the BRIDGE value used in the following OneDeploy inventories.
* `10.0.1.18/24`: Static IP address of the OpenNebula Host.
* `10.0.1.1`: Default gateway for that subnet.
* `10.0.1.1` and `1.1.1.1`: Example DNS resolvers.
* `enp33s0f1np1` / `enp33s0f2np2`: These are additional network interfaces of the Host used in this example that are not utilized by OpenNebula.

After adjusting the Netplan configuration run the following command to update the network:

```shell
sudo netplan apply
```

{{< alert title="Warning!" type="warning" >}}
When you update the Netplan configuration with `netplan apply`, improper configuration could break your network connectivity and render the server inaccessible through SSH. Revise the updated configuration carefully before applying it and ensure you have alternative access to the server (e.g. through IPMI or physical access to the server) in case of errors.
{{< /alert >}}

The necessity of a bridge depends upon your network topology. Consult the [OpenNebula Networking System Documentation]({{% relref "product/cluster_configuration/networking_system/" %}}) for details or ask your system administrator for advice.

### Configure the Inventory for PCI Passthrough

Use a dedicated inventory file to define the general cloud architecture, where you specify PCI devices for passthrough. The following example corresponds to a topology with the OpenNebula Front-end and GPU nodes on separate physical Hosts. If you wish to deploy the OpenNebula Front-end and GPU nodes on the same Host, see [Single Host Deployment]({{% relref "solutions/ai_factory_blueprints/deployment/cd_on-premises.md#single-host-deployment" %}}) below.

Below is an example inventory file, which you can adapt for your environment. For the available PCI device settings, see the [OneDeploy PCI role variables](https://github.com/OpenNebula/one-deploy/blob/master/roles/helper/pci/README.md#role-variables).

The inventory file shown below is a basic example, and you should adjust it to match your specific cloud architecture, including your frontend and node IP addresses, network configuration (`vn`), and datastore setup (`ds`). For more detailed information on configuring OneDeploy for different architectures like shared or Ceph-based storage, refer to the official [OneDeploy Wiki](https://github.com/OpenNebula/one-deploy/wiki).


```yaml
---
all:
  vars:
    ansible_user: root
    one_version: '{{<version>}}'
    one_pass: opennebulapass
    ds:
      mode: ssh
    vn:
      admin_net:
        managed: true
        template:
          VN_MAD: bridge
          BRIDGE: br0
          AR:
            TYPE: IP4
            IP: 192.168.122.100
            SIZE: 48
          NETWORK_ADDRESS: 192.168.122.0
          NETWORK_MASK: 255.255.255.0
          GATEWAY: 192.168.122.1
          DNS: 1.1.1.1

frontend:
  hosts:
    f1: { ansible_host: 192.168.122.2 }

node:
  hosts:
    h100-node:
      ansible_host: 192.168.122.3
      pci_devices:
        - address: "0000:09:00.0" # NVIDIA H100 GPU
          set_driver: vfio-pci
          unlisted: false
    l40s-node:
      ansible_host: 192.168.122.4
      pci_devices:
        - address: "0000:0a:00.0" # NVIDIA L40S GPU
          set_driver: vfio-pci
          unlisted: false
    standard-node:
      ansible_host: 192.168.122.5
```

Key configuration parameters to setup:

* `ansible_host`: The IP address of each server used for either the Front-end or GPU nodes.
* `pci_devices`: The list of PCI devices to configure on that node.
  * `address`: The full PCI address, including the domain, in the format `domain:bus:slot.function` (e.g., `"0000:09:00.0"`). Short addresses are not supported.
  * `set_driver`: The driver that `driverctl` binds the device to. Set it to `vfio-pci` for passthrough. The default, `omit`, leaves the driver unchanged.
  * `unlisted`: Controls inclusion in the Host's `PCI_SHORT_ADDRESS` filter. Set it to `false` to include the GPU. The default is `true`.

In this example, OneDeploy does not configure a per-Host PCI filter for `standard-node`. With the default global filter (`*:*`), this Host may list PCI devices other than GPUs.

To find the address of the GPU on each node you can use the following command:

```bash
lspci -Dnn | grep -i nvidia
```

This command should output something similar to the following:

```
0000:c1:00.0 3D controller [0302]: NVIDIA Corporation AD102GL [L40S] [10de:26b9] (rev a1)
```

Use the full address `"0000:c1:00.0"` from this output in the inventory. The domain and bus are separated by a colon.

### Single Host Deployment

The above inventory example outlines a topology with 2 separate GPU nodes deployed on different physical Hosts to the OpenNebula Front-end. If you have a single bare-metal server and wish to deploy the OpenNebula Front-end and a KVM hypervisor node with GPU-passthrough on the same Host, the following inventory example can be used as reference:

```yaml
---
all:
  vars:
    ansible_user: root
    one_version: '{{<version>}}'
    one_pass: opennebulapass
    ds:
      mode: ssh
    vn:
      admin_net:
        managed: true
        template:
          VN_MAD: bridge
          BRIDGE: br0
          AR:
            TYPE: IP4
            IP: 10.0.1.100
            SIZE: 48
          NETWORK_ADDRESS: 10.0.1.0
          NETWORK_MASK: 255.255.255.0
          GATEWAY: 10.0.1.1
          DNS: 1.1.1.1

frontend:
  hosts:
    ai-server: { ansible_host: 10.0.1.18 }

node:
  hosts:
    ai-server:
      ansible_host: 10.0.1.18
      pci_devices:
        - address: "0000:c1:00.0" # NVIDIA L40S GPU
          set_driver: vfio-pci
          unlisted: false
        - address: "0000:01:00.0" # NVIDIA L40S GPU
          set_driver: vfio-pci
          unlisted: false
```

This inventory outlines a topology with the OpenNebula Front-end and a KVM hypervisor node deployed on the same physical Host with PCI passthrough to 2 separate GPU devices. Adjust the inventory according to your topology.

### Run the Deployment

Once your inventory file is ready (e.g. saved as `inventory/ai_factory.yml`), run OneDeploy from its repository directory to provision your OpenNebula cloud:

```shell
make I=inventory/ai_factory.yml
```

For each GPU configured with `set_driver: vfio-pci`, OneDeploy uses `driverctl` to bind the device to the passthrough driver.

For GPUs configured with `unlisted: false`, OneDeploy adds their addresses to the Host's `PCI_SHORT_ADDRESS` filter so OpenNebula can discover them for VM assignment.

## Post-Deployment Verification

After the deployment is complete, verify that the GPUs are correctly configured and available to OpenNebula by checking the Host information in Sunstone:

1. Log in to your OpenNebula Sunstone GUI (normally accessible at <FRONTEND_IP>:2616), with the password you set in the above inventory
2. Navigate to **Infrastructure -> Hosts**
3. Select one of the hypervisors you configured for passthrough (e.g. `h100-node` or `10.0.1.18`)
4. Go to the **PCI** tab
5. You will see your GPU(s) listed as an available PCI device (you may need to wait 2-3 minutes for them to appear):

{{< image
  pathDark="/images/ai_factories/dark/pci_sunstone.png"
  path="/images/ai_factories/light/pci_sunstone.png"
  alt="Sunstone login" align="center" width="90%" mb="20px"
>}}

If the device is visible here, your AI-ready OpenNebula cloud is correctly configured. The H100 and/or L40S GPUs are now ready to be passed through to Virtual Machines for high-performance AI and ML tasks.

---

## Next Steps

After completing the above steps to launch your AI-ready OpenNebula cloud with OneDeploy, validate your deployment one of the one of the following options:

* [Inferencing with vLLM]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/llm_inference_certification" %}})
* [AI-ready Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}})

