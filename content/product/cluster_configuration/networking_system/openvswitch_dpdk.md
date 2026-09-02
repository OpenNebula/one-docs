---
title: "Open vSwitch DPDK"
linkTitle: "Open vSwitch DPDK"
date: "2026-08-10"
description:
categories:
pageintoc: "58"
tags: ['AI','NVIDIA']
weight: "7"
---

<a id="openvswitch-dpdk"></a>

Open vSwitch (OVS) can use the Data Plane Development Kit (DPDK) to move packet processing from the kernel to dedicated userspace polling threads. This provides an accelerated, shareable network path when assigning a physical NIC directly to each Virtual Machine is not appropriate.

{{< alert title="Warning" type="warning" >}}
Open vSwitch DPDK is supported only for KVM Hosts.
{{< /alert >}}

The physical NIC is owned by `ovs-vswitchd`, normally through `vfio-pci`; it is not passed through to the VM. OpenNebula connects each VM to the userspace bridge with a `dpdkvhostuserclient` port. QEMU creates the corresponding vhost-user socket under `/var/run/one/vhost-socks/`.

Although OpenNebula can create a missing OVS bridge with `datapath_type=netdev`, the recommended workflow is to create the bridge during Host provisioning, either manually or with OneDeploy. The physical NIC must be bound and its DPDK port or bond must be added by the administrator, so configuring the bridge at the same time makes it possible to verify the complete physical data path before deploying VMs. OpenNebula then manages the VM-side ports.

## Requirements

Before starting, verify only that:

* The Host is an OpenNebula KVM node.
* The physical NIC is supported by a DPDK Poll Mode Driver (PMD).
* Administrative and, when changing a management uplink, out-of-band access to the Host is available.

This guide walks you through configuring the remaining requirements; they do not need to be prepared before starting:

* An OVS build with DPDK support and a compatible DPDK version. The guide uses distribution packages and references the [OVS and DPDK compatibility table](https://docs.openvswitch.org/en/latest/faq/releases/).
* Huge Pages for OVS and for every VM connected through vhost-user.
* Dedicated CPU threads for the OVS PMDs and their reservation in OpenNebula.
* IOMMU and VFIO when the selected PMD requires the NIC to be bound to `vfio-pci`. Bifurcated PMDs are an exception and retain their kernel driver.
* The OVS userspace bridge and its physical DPDK port or bond.
* A virtio NIC, shared memory and NUMA-aware placement in the VM Template.

## Automated Configuration

The [OneDeploy Open vSwitch role](https://github.com/OpenNebula/one-deploy/tree/master/roles/openvswitch) can install OVS-DPDK, configure kernel parameters and modules, bind PCI devices, and create OVS ports, bonds and bridges. Use it when Host networking is managed with OneDeploy.

{{< alert title="Warning" type="warning" >}}
The role replaces the operating system network configuration. Keep out-of-band access to the Host and validate the interface names, PCI addresses, IP configuration and routes before applying it.
{{< /alert >}}

The following sections describe the equivalent manual configuration and the OpenNebula objects required to consume it.

## Step 1. Install OVS with DPDK Support

Use the packages provided for the Host operating system:

* **Ubuntu and Debian**: install `openvswitch-switch-dpdk`. Select `/usr/lib/openvswitch-switch-dpdk/ovs-vswitchd-dpdk` with `update-alternatives` if the distribution does not select it automatically. The service is `openvswitch-switch.service`.
* **Red Hat Enterprise Linux**: enable the Fast Datapath repository for the installed RHEL major version, then install one of its versioned Open vSwitch packages and `dpdk-tools`. The service is `openvswitch.service`.
* **AlmaLinux**: enable the NFV Open vSwitch repository with `centos-release-nfv-openvswitch`, then install a versioned Open vSwitch package and `dpdk-tools`. The service is `openvswitch.service`.

Start and enable the service. Use the command for the Host distribution:

```shell
# Ubuntu and Debian
systemctl enable --now openvswitch-switch.service

# Red Hat Enterprise Linux and AlmaLinux
systemctl enable --now openvswitch.service
```

Verify that `ovs-vswitchd` reports both OVS and DPDK versions:

```shell
ovs-vswitchd --version
```

Do not continue if the output does not contain a DPDK version.

## Step 2. Plan the Host Resources

Use one consistent topology throughout the configuration. The examples in this guide use the following values; replace them with the values from each Host:

| Resource | Example value |
|----------|---------------|
| Host NUMA nodes | `0` and `1` |
| Physical uplink | `enp1s0f0` |
| PCI address | `0000:01:00.0` |
| NIC NUMA node | `0` |
| MTU | `1500` |
| PMD CPU | `2`, on NUMA node 0 |
| OVS memory | 1024 MB on NUMA node 0 |
| Test VM memory | 4096 MB on NUMA node 0 |
| Huge Page size | 1 GB |
| OVS bridge | `ovsbr0` |

### Identify the NIC and its NUMA Node

Determine the PCI address used by the uplink and verify its current driver:

```shell
ethtool -i enp1s0f0
lspci -Dnnk -s 0000:01:00.0
```

Display the NUMA node associated with the device:

```shell
cat /sys/bus/pci/devices/0000:01:00.0/numa_node
```

A value of `-1` means that the platform did not report a NUMA association for the device.

When using VFIO, also inspect the complete IOMMU group:

```shell
readlink -f /sys/bus/pci/devices/0000:01:00.0/iommu_group
ls -1 /sys/bus/pci/devices/0000:01:00.0/iommu_group/devices/
```

The IOMMU group is the minimum device-ownership unit. For the group to be usable through VFIO, every member must be detached from its native host driver and bound to a VFIO-compatible driver, or otherwise left unbound. Inspect the group before changing any driver and do not detach a member that the Host still requires.

{{< alert title="Warning" type="warning" >}}
Do not bind an active management interface to `vfio-pci` from a remote session. Binding removes its kernel network interface and immediately interrupts connectivity. Use a separate management interface or out-of-band console and prepare any required IP and route migration first.
{{< /alert >}}

### Allocate Huge Pages

OVS uses a shared memory model by default. Ports on the same NUMA node with the same MTU share a mempool; memory is not allocated independently for every NIC. Enabling `other_config:per-port-memory=true` changes this behavior and requires a separate calculation for each port.

The following values from the [OVS DPDK memory model](https://docs.openvswitch.org/en/latest/topics/dpdk/memory/) are useful starting points for the default shared model:

| MTU | Approximate shared mempool | Practical 1 GB page allocation |
|-----|-----------------------------|--------------------------------|
| 1500 | 788 MB | 1 GB per active NUMA node |
| 9000 | 2667 MB | 3 GB per active NUMA node |

An additional pool may be created for every distinct MTU on the same NUMA node. Size the final allocation from the configured MTUs, queue counts and OVS memory model rather than multiplying these values by the number of NICs.

Allocate OVS memory only on NUMA nodes that will run DPDK physical or vhost-user ports. For example, the reference Host uses 1024 MB on node 0 and none on node 1:

```default
dpdk-socket-mem=1024,0
```

VM memory is separate from `dpdk-socket-mem`. The reference Host needs at least five 1 GB Huge Pages on node 0 to start OVS and one 4 GB VM: one page for the OVS mempool and four pages for the guest. Add capacity for concurrent VMs and operational headroom.

Configure the required pages as described in [Host Configuration for PCI Passthrough and SR-IOV]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration#step-3-configure-huge-pages-optional" %}}). Huge Pages are allocated per NUMA node, so verify their placement:

```shell
grep -i '\<Huge' /sys/devices/system/node/node*/meminfo
mount | grep hugetlbfs
```

The directory passed to `dpdk-hugepage-dir` must be a mounted `hugetlbfs` with the intended page size. This guide uses `/dev/hugepages` with 1 GB pages. Do not assume that libvirt created or mounted it.

### Reserve PMD CPUs

PMD threads continuously poll the Rx queues assigned to them. Start with at least one PMD CPU on every NUMA node that runs DPDK ports, then scale the number of PMDs and queues from measured traffic and packet-loss requirements. OVS assigns Rx queues to PMDs automatically unless an explicit affinity is configured; see the [OVS PMD documentation](https://docs.openvswitch.org/en/latest/topics/dpdk/pmd/).

Inspect the CPU topology:

```shell
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE
```

Prefer dedicated physical cores. Using both SMT siblings of one core can reduce the number of reserved cores, but usually provides less predictable maximum throughput. Keep PMDs, physical ports, VM vCPUs and VM memory on the same NUMA node whenever possible.

`other_config:pmd-cpu-mask` is a hexadecimal bit mask of logical CPU IDs. For the reference CPU ID `2`, calculate the mask with:

```shell
python3 -c 'cpus=(2,); print(hex(sum(1 << cpu for cpu in cpus)))'
0x4
```

Reserve the same CPUs in the OpenNebula Host template so that the scheduler does not pin VM vCPUs to them. Update the Host through Sunstone or run:

```shell
onehost update <host-id> -a
```

Add the following attribute in the editor:

```default
ISOLCPUS = "2"
```

The OpenNebula `ISOLCPUS` attribute is required for scheduler accounting. The kernel `isolcpus` parameter is optional CPU scheduling and performance tuning; it is not a security control.

## Step 3. Prepare the Physical NIC

The required binding procedure depends on the DPDK PMD used by the NIC.

### Conventional VFIO PMDs

Enable the IOMMU and configure persistent `vfio-pci` binding as described in [Host Configuration for PCI Passthrough and SR-IOV]({{% relref "product/cluster_configuration/pci_passthrough_sriov/host_configuration#step-2-configure-vfio-device-binding" %}}). For the reference NIC:

```shell
driverctl set-override 0000:01:00.0 vfio-pci
dpdk-devbind.py --status-dev net
```

Repeat the binding operation for every other IOMMU-group member that must use `vfio-pci`. The status command should show `drv=vfio-pci` for `0000:01:00.0`.

VFIO ownership must match the process consuming the group. On distributions where `ovs-vswitchd` runs as a non-root user, the `root:kvm` and `0660` rule from the generic passthrough guide is sufficient only when that service user belongs to the `kvm` group. Otherwise, use a suitable supplementary group or distribution-provided policy. Check both the service identity and the VFIO group device:

```shell
ps -o user,group,comm -C ovs-vswitchd
ls -l /dev/vfio/
```

### Bifurcated PMDs

Some NICs, including devices using the `mlx5` PMD, use a bifurcated driver. The device remains bound to its native kernel driver, such as `mlx5_core`, while DPDK accesses the data path. Do not bind such a device to `vfio-pci`. Check the NIC-specific section of the [DPDK driver documentation](https://doc.dpdk.org/guides/nics/index.html) before changing its driver.

## Step 4. Configure OVS-DPDK

Set the initialization parameters together so that only one restart is required. The following values implement the reference topology:

```shell
ovs-vsctl --no-wait set Open_vSwitch . \
    other_config:dpdk-init=true \
    other_config:dpdk-hugepage-dir=/dev/hugepages \
    other_config:dpdk-socket-mem=1024,0 \
    other_config:pmd-cpu-mask=0x4
```

Restart the service for the initialization parameters to take effect:

```shell
# Ubuntu and Debian
systemctl restart openvswitch-switch.service

# Red Hat Enterprise Linux and AlmaLinux
systemctl restart openvswitch.service
```

Verify initialization before creating ports:

```shell
ovs-vsctl get Open_vSwitch . dpdk_initialized
ovs-vsctl get Open_vSwitch . dpdk_version
ovs-vsctl get Open_vSwitch . other_config:dpdk-socket-mem
ovs-vsctl get Open_vSwitch . other_config:pmd-cpu-mask
ovs-vsctl get Open_vSwitch . other_config:dpdk-hugepage-dir
```

`dpdk_initialized` must return `true`. If it does not, inspect the service log:

```shell
# Ubuntu and Debian
journalctl -u openvswitch-switch.service --since "10 minutes ago"

# Red Hat Enterprise Linux and AlmaLinux
journalctl -u openvswitch.service --since "10 minutes ago"
```

## Step 5. Configure the Physical Uplink

Create the DPDK bridge as part of Host provisioning, either manually as shown below or with OneDeploy. OpenNebula can create a missing bridge when the first VM NIC is attached, but it cannot bind or add the physical DPDK uplink. Creating the bridge explicitly keeps the bridge and uplink configuration together and allows the physical data path to be verified before it is exposed to VMs:

```shell
ovs-vsctl --may-exist add-br ovsbr0 \
    -- set Bridge ovsbr0 datapath_type=netdev
```

Add the reference NIC as a DPDK port:

```shell
ovs-vsctl --may-exist add-port ovsbr0 dpdk0 \
    -- set Interface dpdk0 type=dpdk \
       options:dpdk-devargs=0000:01:00.0
```

The OVS interface name `dpdk0` is local to OVS. A VFIO-bound device has no kernel interface name; `options:dpdk-devargs` identifies the device by PCI address.

Verify the bridge and physical port:

```shell
ovs-vsctl show
ovs-vsctl get Interface dpdk0 error
ovs-vsctl get Interface dpdk0 link_state
```

An empty `error` value and `link_state` of `up` indicate that OVS attached the port successfully.

If the Host needs an IP address on this network, configure it on the bridge internal interface, `ovsbr0`, rather than on the physical NIC. Make this change persistently with the distribution network renderer. Migrating a management address requires out-of-band access and a coordinated change to addresses, routes and DNS.

### DPDK Bonds and Jumbo Frames

For redundancy, create a DPDK bond instead of the single physical port. This corrected example uses the same interface names in `add-bond` and `set Interface`:

```shell
ovs-vsctl --may-exist add-bond ovsbr0 bond0 dpdk0 dpdk1 \
    -- set Port bond0 bond_mode=balance-slb \
    -- set Interface dpdk0 type=dpdk \
       options:dpdk-devargs=0000:01:00.0 mtu_request=9000 \
    -- set Interface dpdk1 type=dpdk \
       options:dpdk-devargs=0000:81:00.0 mtu_request=9000
```

Do not run both the single-port and bond examples without first removing `dpdk0` from its existing OVS port. If the second NIC is on another NUMA node, allocate Huge Pages and a PMD CPU on that node and update `dpdk-socket-mem`, `pmd-cpu-mask` and OpenNebula `ISOLCPUS` accordingly.

For jumbo frames, use the same MTU on the physical DPDK interfaces, the OVS internal interface when used, the OpenNebula Virtual Network, and the guest. Recalculate the OVS mempool before changing the MTU.

## Step 6. Configure OpenNebula

### Create the Virtual Network

Use the `ovswitch` driver and set `BRIDGE_TYPE` to `openvswitch_dpdk`. Do not define `PHYDEV`; the physical DPDK port is already attached to the bridge outside OpenNebula.

```default
NAME        = "dpdk-net"
VN_MAD      = "ovswitch"
BRIDGE      = "ovsbr0"
BRIDGE_TYPE = "openvswitch_dpdk"
VLAN_ID     = "1402"
MTU         = "1500"
```

Normal [Open vSwitch network configuration]({{% relref "openvswitch#ovswitch-net" %}}) rules apply, including the Open vSwitch Security Group limitations.

### Configure the VM

The VM NIC must use the virtio model. [Vhost-user](https://docs.openvswitch.org/en/latest/topics/dpdk/vhost-user/) also requires shared guest memory; in OpenNebula, configure Huge Pages and set `MEMORY_ACCESS` to `shared`. Add the following resources to a normal VM Template:

```default
CPU    = "2"
VCPU   = "2"
MEMORY = "4096"

NIC = [
  NETWORK = "dpdk-net",
  MODEL   = "virtio"
]

TOPOLOGY = [
  SOCKETS       = "1",
  CORES         = "2",
  THREADS       = "1",
  PIN_POLICY    = "THREAD",
  NODE_AFFINITY = "0",
  HUGEPAGE_SIZE = "1024",
  MEMORY_ACCESS = "shared"
]
```

`NODE_AFFINITY="0"` matches the NIC, PMD and Huge Pages in the reference topology. Change it when the physical path is on another NUMA node. See [CPU and NUMA Pinning]({{% relref "product/cluster_configuration/hosts_and_clusters/numa#cpu-and-numa-pinning" %}}) for more complex topologies.

For each NIC, QEMU creates a server socket in `/var/run/one/vhost-socks/` and OpenNebula adds an OVS `dpdkvhostuserclient` interface that connects to it. The socket name matches the VM NIC target, normally `one-<vm-id>-<nic-id>`.

## Step 7. Verify the Data Path

Verify the Host configuration:

```shell
ovs-vsctl get Open_vSwitch . dpdk_initialized
ovs-vsctl show
ovs-appctl dpif-netdev/pmd-rxq-show
ovs-appctl dpif-netdev/pmd-perf-show
```

`pmd-rxq-show` displays the physical and vhost-user Rx queues assigned to every PMD. Use it after adding ports and starting a VM; the number of PMDs is not derived from the number of interfaces.

Verify the VM-side socket and libvirt interface:

```shell
find /var/run/one/vhost-socks/ -maxdepth 1 -type s -ls
virsh dumpxml one-<vm-id>
```

The domain XML must contain an interface similar to:

```xml
<interface type='vhostuser'>
  <source type='unix' path='/var/run/one/vhost-socks/one-42-0' mode='server'/>
  <model type='virtio'/>
</interface>
```

The corresponding OVS interface must use client mode:

```default
Interface "one-42-0"
    type: dpdkvhostuserclient
    options: {vhost-server-path="/var/run/one/vhost-socks/one-42-0"}
```

## Troubleshooting

### DPDK Does Not Initialize

Check:

* `ovs-vswitchd --version` reports DPDK support and the OVS/DPDK versions are compatible.
* The Huge Page mount exists and has sufficient free pages on the requested NUMA nodes.
* `dpdk-socket-mem` matches the Host NUMA topology; use `0` for unused nodes.
* The OVS service user can open the required VFIO group.
* The PCI device is using the driver required by its PMD.

Review the distribution-specific Open vSwitch service log for DPDK EAL errors after every initialization change.

### Unexpected PMD CPU Usage

Polling PMDs with assigned Rx queues normally consume a complete logical CPU even when traffic is low. This is expected. Confirm the queue assignment with `ovs-appctl dpif-netdev/pmd-rxq-show` before adding PMDs.

Recent OVS versions support `other_config:pmd-sleep-max` to reduce idle polling. Sleeping trades CPU consumption for wake-up latency and possible packet loss during bursts; validate it with the target workload before using it in production.

### Vhost-user Socket Permission Errors

QEMU is the socket server and OVS is the client. Check directory traversal, socket permissions and the service identities:

```shell
namei -l /var/run/one/vhost-socks/
ps -o user,group,comm -C ovs-vswitchd
ps -eo user,group,comm,args | grep '[q]emu-system'
```

On SELinux or AppArmor systems, inspect the audit or kernel log for a mandatory-access-control denial before changing policy. The required policy depends on the distribution packages and their service domains. Prefer an updated distribution policy or a reviewed local policy.

Do not use `chcon` as a permanent fix because its label can be lost during filesystem relabeling. If a custom SELinux file context is required and has been validated for the distribution, make it persistent with `semanage fcontext` and apply it with `restorecon`. Apply equivalent profile changes when AppArmor is in use.
