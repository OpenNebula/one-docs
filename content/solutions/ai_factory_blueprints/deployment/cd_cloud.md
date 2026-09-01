---
title: "On-cloud AI Factory Deployment with Scaleway"
linkTitle: "Cloud Deployment"
date: "2025-10-21"
weight: 3
tags: ['AI']
---

<a id="cd_cloud"></a>

This document describes the procedure to deploy an AI-ready OpenNebula cloud using OneDeploy on a single [Scaleway Elastic Metal](https://www.scaleway.com/en/elastic-metal/) bare-metal server equipped with GPUs.

The architecture is a converged OpenNebula installation, where the frontend services and KVM hypervisor run on the same physical host. This approach is ideal for demonstrations, proofs-of-concept (PoCs), or for quickly trying out the solution without the need for a complex physical infrastructure.

The outlined procedure is based on an instance with NVIDIA L40S GPUs as an example.

## Prerequisites

Before you begin, ensure your environment meets the following prerequisites.

### Instance Launch and Initial Checks

1. Log in to your Scaleway console.
2. Navigate to **Bare Metal > Elastic Metal**
3. Click **Create Elastic Metal Server**.
4. Configure your server in the portal:

    *  **Availability Zone:** Choose your preferred zone, such as `PARIS 2`. Alternatively, select `Auto allocate`.
    *  **Billing Method:** Select either hourly or monthly. Note that hourly billing is often more cost-effective for short-term projects or testing.
    *  **Server Type:** Select an instance. For GPU acceleration, you must choose an `Elastic Metal Titanium` server.
    *  **Image:** Choose `Ubuntu 24.04 LTS` as the operating system.
    *  **Cloud-init:** You can skip this step, as it is not used in this setup.
    *  **Disk Partitions:** Configure the disk partition table so that the `/` path has the full disk space available.
    *  **Name and Tags:** Enter a name for your server and add any optional tags for organization.
    *  **SSH Keys:** add your public SSH key. This is essential for securely accessing your server.
    *  **Public Bandwidth:** the default bandwidth is usually sufficient. You can increase it here if your use case requires higher public throughput.
    * **Private Networks:** enabling 25Gbps Private Networks is not needed for a single-node setup.
    * **Environmental Summary:** review the Environmental Footprint Summary.
    * **Cost Summary:** review the *Estimated Cost Summary* to ensure it matches your expectations.
    * **Create Server:** once you have verified all settings, click **"Create Elastic Metal Server"** to provision and launch your instance.

5. After some minutes and once the instance is running, connect to it via SSH using its public IP address:
```bash
ssh ubuntu@<your_instance_public_ip>
```

6. Verify that the GPUs are detected as PCI devices:
```bash
lspci -Dnnk | grep NVIDIA
```
You should see an output similar to this, listing your NVIDIA GPUs:
```bash
0000:01:00.0 3D controller [0302]: NVIDIA Corporation AD102GL [L40S] [10de:26b9] (rev a1)
    Subsystem: NVIDIA Corporation AD102GL [L40S] [10de:1851]
0000:82:00.0 3D controller [0302]: NVIDIA Corporation AD102GL [L40S] [10de:26b9] (rev a1)
    Subsystem: NVIDIA Corporation AD102GL [L40S] [10de:1851]
```

Make sure you note down the full PCI addresses for both GPUs.

7. Confirm that IOMMU is enabled on the server. The `ls` command below should list several numbered subdirectories:
```bash
ls -la /sys/kernel/iommu_groups/
```
If the directory is not empty it means that IOMMU is active, which is a prerequisite for PCI passthrough.

### Server Pre-configuration

The following steps prepare the server to run OneDeploy, which operates with `root` privileges.

1.  Obtain Root Privileges:
    OneDeploy installs software and modifies system-level configuration files. To perform these actions, open a `root` shell.
    ```shell
    sudo -i
    ```

2.  Configure Local Root SSH Access:
    Generate an SSH key pair for `root` and authorize it for local connections. This allows Ansible to connect to `127.0.0.1` as `root`.
    ```shell
    ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" -q
    cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
    ```

3.  Create a Virtual Network Bridge:
    To provide network connectivity to the VMs, create a virtual bridge with NAT. This allows VMs to access the internet through the server's public network interface.

    3.1 Create the Netplan configuration file for the bridge:
    ```shell
    tee /etc/netplan/60-bridge.yaml > /dev/null << 'EOF'
    network:
      version: 2
      bridges:
        br0:
          dhcp4: no
          addresses: [192.168.100.1/24]
          interfaces: []
          parameters:
            stp: false
            forward-delay: 0
          nameservers:
            addresses: [1.1.1.1,8.8.8.8]
    EOF
    ```

    3.2  Apply the network configuration and enable IP forwarding. Replace `enp129s0f0np0` with your server's main network interface if it is different.
    ```shell
    netplan apply
    sysctl -w net.ipv4.ip_forward=1
    iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o enp129s0f0np0 -j MASQUERADE
    iptables-save | uniq | iptables-restore
    ```

### OneDeploy Dependencies

As a `root` user, clone the `one-deploy` repository and install its dependencies.

```shell
cd /root
git clone https://github.com/OpenNebula/one-deploy.git
cd one-deploy/
apt update && apt install -y pipx make
pipx install hatch
pipx ensurepath
source ~/.bashrc
make requirements
hatch shell
```

At this point, you should be using the hatch environment shell:
```shell
(one-deploy) #
```
For more details, refer to the [OneDeploy System Requirements](https://github.com/OpenNebula/one-deploy/wiki/sys_reqs).

## AI Factory Deployment

Create an inventory file named `inventory/scaleway.yaml`. This file defines a complete OpenNebula deployment on the local machine (`127.0.0.1`).

{{< alert title="Important" type="info" >}}
*   Replace `YOUR_SECURE_PASSWORD` with a strong and unique password for the `oneadmin` user.
*   The PCI device addresses (`0000:01:00.0`, `0000:82:00.0`) must match the ones you found earlier with `lspci`.
{{< /alert >}}

```yaml
---
all:
  vars:
    ansible_user: root
    one_version: '7.0'
    one_pass: YOUR_SECURE_PASSWORD # Replace with a strong password
    gate_endpoint: "http://192.168.100.1:5030"
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
            IP: 192.168.100.50
            SIZE: 200
          NETWORK_ADDRESS: 192.168.100.0
          NETWORK_MASK: 255.255.255.0
          GATEWAY: 192.168.100.1
          DNS: 1.1.1.1

frontend:
  hosts:
    f1: { ansible_host: 127.0.0.1 }

node:
  hosts:
    h1:
      ansible_host: 127.0.0.1
      pci_passthrough_enabled: true
      pci_devices:
        - address: "0000:01:00.0" # First L40S GPU
        - address: "0000:82:00.0" # Second L40S GPU
```

Run the deployment on the `one-deploy` hatch shell environment previously created:
```bash
make I=inventory/scaleway.yaml
```

{{< alert title="Tip" type="tip" >}}
Improve the security of your public-facing OpenNebula instances with SSL termination and rate limiting by performing the configuration of a reverse proxy such as Nginx or Apache, forwarding requests to localhost:2616. Then, set the host variable in /etc/one/fireedge-server.conf so that it listens only on localhost.
{{< /alert >}}

## Post-Deployment Verification

Once the deployment is complete:
1. Access the OpenNebula Sunstone web interface at `http://<your_instance_public_ip>:2616`.
2. Log in with the username `oneadmin` and the password you set in the inventory file.
3. Verify the GPU passthrough configuration:
    1. In Sunstone, navigate to **Infrastructure -> Hosts**.
    2. Select the `127.0.0.1` host.
    3. Go to the **PCI** tab. You should see both L40S GPUs listed and ready for passthrough.

---

## Next steps

After completing the above steps to launch your AI-ready OpenNebula cloud with OneDeploy, validate your deployment one of the one of the following options:

* [Validation with LLM Inferencing]({{% relref "solutions/ai_factory_blueprints/direct_ai_execution/llm_inference_certification" %}})
* [Validation with AI-Ready Kubernetes]({{% relref "solutions/ai_factory_blueprints/containerized_ai_execution/ai_ready_k8s" %}})
