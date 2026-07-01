---
title: "KVM Driver"
date: "2025-02-17"
description:
categories:
pageintoc: "177"
tags:
weight: "3"
---

<a id="kvmg"></a>

<!--# KVM Driver -->

## Requirements

To support virtualization, the Hosts will need a CPU with Intel VT or AMD’s AMD-V features. KVM's [Preparing to use KVM](http://www.linux-kvm.org/page/FAQ#Preparing_to_use_KVM) guide will clarify any doubts you may have regarding whether your hardware supports KVM.

KVM will be installed and configured after following the [KVM Host Installation]({{% relref "kvm_node_installation#kvm-node" %}}) section.

## Considerations & Limitations

Try to use [virtio]({{% relref "#kvmg-virtio" %}}) whenever possible for both networks and disks. Using emulated hardware for networks and disks, will have an impact on performance and will not expose all the available functionality. For instance, if you don’t use `virtio` for the disk drivers, you will not be able to exceed a small number of devices connected to the controller, meaning that you have a limit when attaching disks and it will not work while the VM is running (live disk-attach).

When **updating the VM configuration live** by using `one.vm.updateconf`, although all of the VM configuration will be updated on the VM instance template, only the CONTEXT and BACKUP_CONFIG will take effect immediately. The rest of the configuration will not take effect until the next VM reboot because it changes the VM virtual hardware.

The full list of configuration attributes are:

```default
OS        = ["ARCH", "MACHINE", "KERNEL", "INITRD", "BOOTLOADER", "BOOT", "KERNEL_CMD", "ROOT", "SD_DISK_BUS", "UUID", "FIRMWARE", "FIRMWARE_FORMAT"]
FEATURES  = ["ACPI", "PAE", "APIC", "LOCALTIME", "HYPERV", "GUEST_AGENT", "VIRTIO_SCSI_QUEUES", "VIRTIO_BLK_QUEUES", "IOTHREADS"]
INPUT     = ["TYPE", "BUS"]
GRAPHICS  = ["TYPE", "LISTEN", "PASSWD", "KEYMAP", "COMMAND" ]
VIDEO     = ["TYPE", "IOMMU", "ATS", "VRAM", "RESOLUTION"]
RAW       = ["DATA", "DATA_VMX", "TYPE", "VALIDATE"]
CPU_MODEL = ["MODEL", "FEATURES"]
BACKUP_CONFIG = ["FS_FREEZE", "KEEP_LAST", "BACKUP_VOLATILE", "MODE", "INCREMENT_MODE", "DISK_IDS"]
CONTEXT (any value, except ETH*, **variable substitution will be made**)
```

## Configuration

### KVM Configuration

The OpenNebula packages will configure KVM automatically, therefore you don’t need to take any extra steps.

### OpenNebula

The KVM driver is enabled by default in OpenNebula `/etc/one/oned.conf` on your Front-end Host with reasonable defaults. Read the [oned Configuration]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-virtualization-drivers" %}}) to understand these configuration parameters and [Virtual Machine Drivers Reference]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-vmm#devel-vmm" %}}) to know how to customize and extend the drivers.

<a id="kvmg-default-attributes"></a>

### Driver Defaults

There are some attributes required for KVM to boot a VM. You can set a suitable default for them so all the VMs get the required values. These attributes are set in `/etc/one/vmm_exec/vmm_exec_kvm.conf`. Default values from the configuration file can be overriden in the Cluster, Host, or VM template. The following attributes can be set for KVM:

- `EMULATOR`: path to the KVM executable.
- `OS`: attributes `KERNEL`, `INITRD`, `ROOT`, `KERNEL_CMD`, `MACHINE`, `ARCH`, `SD_DISK_BUS`, `FIRMWARE`, `FIRMWARE_FORMAT`, `FIMRWARE_SECURE` and `BOOTLOADER`.
- `VCPU`
- `VCPU_MAX`
- `MEMORY_SLOTS`
- `FEATURES`: attributes `ACPI`, `PAE`, `APIC`, `HEPRV`, `LOCALTIME`, `GUEST_AGENT`, `VIRTIO_SCSI_QUEUES`, `VIRTIO_BLK_QUEUES`, `IOTHREADS`.
- `CPU_MODEL`: attribute `MODEL`, `FEATURES`.
- `DISK`: attributes `DRIVER`, `CACHE`, `IO`, `DISCARD`, `TOTAL_BYTES_SEC`, `TOTAL_BYTES_SEC_MAX`, `TOTAL_BYTES_SEC_MAX_LENGTH`, `TOTAL_IOPS_SEC`, `TOTAL_IOPS_SEC_MAX`, `TOTAL_IOPS_SEC_MAX_LENGTH`, `READ_BYTES_SEC`, `READ_BYTES_SEC_MAX`, `READ_BYTES_SEC_MAX_LENGTH`, `WRITE_BYTES_SEC`, `WRITE_BYTES_SEC_MAX`, `WRITE_BYTES_SEC_MAX_LENGTH`, `READ_IOPS_SEC`, `READ_IOPS_SEC_MAX`, `READ_IOPS_SEC_MAX_LENGTH`, `WRITE_IOPS_SEC`, `WRITE_IOPS_SEC_MAX`, `WRITE_IOPS_SEC_MAX_LENGTH`, `SIZE_IOPS_SEC`.
- `NIC`: attribute `FILTER`, `MODEL`.
- `GRAPHICS`: attributes `TYPE`, `LISTEN`, `PASSWD`, `KEYMAP`, `RANDOM_PASSWD`. The VM instance must have at least empty `GRAPHICS = []` section to read these default attributes from the config file and to generate cluster unique `PORT` attribute.
- `VIDEO`: attributes: `TYPE`, `IOMMU`, `ATS`, `VRAM`, `RESOLUTION`.
- `RAW`: to add libvirt attributes to the domain XML file.
- `HYPERV_OPTIONS`: to enable hyperv extensions.
- `HYPERV_TIMERS`: timers added when HYPERV is set to yes in FEATURES.
- `SPICE_OPTIONS`: to add default devices for SPICE.

The following attributes can be overridden at Cluster and Host level, but not within individual VM configuration:

- `OVMF_UEFIS`: to specify allowed file paths for Open Virtual Machine Firmware
- `Q35_ROOT_PORTS`: to modify the number of PCI devices that can be attached in q35 VMs (defaults to 16)
- `Q35_NUMA_PCIE`: to generate a NUMA-aware PCIe topology for pinned VMs
- `CGROUPS_VERSION`: Use ‘2’ to use Cgroup V2, all other values or undefined: use Cgroup V1
- `EMULATOR_CPUS`: specifies which of the host physical CPUs runs the main QEMU emulator threadValue used for KVM option <cputune><emulatorpin cpuset=…>

{{< alert title="Warning" type="warning" >}}
These values are only used during VM creation; for other actions like nic or disk attach/detach the default values must be set in `/var/lib/one/remotes/etc/vmm/kvm/kvmrc`. For more info check [Files and Parameters]({{% relref "kvm_driver#kvmg-files-and-parameters" %}}) section.{{< /alert >}}

For example (check the actual state in the configuration file on your Front-end):

```default
OS       = [ ARCH = "x86_64" ]
FEATURES = [ PAE = "no", ACPI = "yes", APIC = "no", HYPERV = "no", GUEST_AGENT = "no", VIRTIO_SCSI_QUEUES="auto" ]
DISK     = [ DRIVER = "raw" , CACHE = "none"]
HYPERV_OPTIONS="<relaxed state='on'/><vapic state='on'/><spinlocks state='on' retries='4096'/>"
SPICE_OPTIONS="
    <video>
        <model type='vga' heads='1'/>
    </video>
         <sound model='ich6' />
    <channel type='spicevmc'>
        <target type='virtio' name='com.redhat.spice.0'/>
    </channel>
    <redirdev bus='usb' type='spicevmc'/>
    <redirdev bus='usb' type='spicevmc'/>
    <redirdev bus='usb' type='spicevmc'/>"
```

**Since OpenNebula 6.0** you should no longer need to modify the `EMULATOR` variable to point to the KVM executable; instead, `EMULATOR` now points to the symlink `/usr/bin/qemu-kvm-one`, which should link the correct KVM binary for the given OS on a Host.

### Live-Migration for Other Cache Settings

If you are using disks with a cache setting different to `none` you may have problems with live migration depending on the libvirt version. You can enable the migration by adding the `--unsafe` parameter to the virsh command. The file to change is `/var/lib/one/remotes/etc/vmm/kvm/kvmrc`. Uncomment the following line, and execute `onehost sync --force` afterwards:

```default
MIGRATE_OPTIONS=--unsafe
```

### Configure the Timeouts (Optional)

Optionally, you can set a timeout for the VM Shutdown operation. This feature is useful when a VM gets stuck in Shutdown (or simply does not notice the shutdown command). By default, after the timeout time the VM will return to Running state but is can also be configured so the VM is destroyed after the grace time. This is configured in `/var/lib/one/etc/remotes/vmm/kvm/kvmrc`:

```default
# Seconds to wait after shutdown until timeout
export SHUTDOWN_TIMEOUT=180

# Uncomment this line to force VM cancellation after shutdown timeout
export FORCE_DESTROY=yes
```

<a id="kvmg-working-with-cgroups-optional"></a>

### Working with cgroups (Optional)

Optionally, you can set up cgroups to control resources on your Hosts. By default KVM VMs will be placed in the `machine.slice`, the resources assigned in this slice can be adjusted for each hypervisor. The [libvirt cgroups documentation](https://libvirt.org/cgroups.html) describes all the cases and the way the cgroups are managed by libvirt/KVM.

OpenNebula computes the `shares` attribute of the Libvirt domain using the `CPU` parameter and the base share value, which depends on the cgroups version of the hypervisor. For example, a VM with `CPU=2` will get a cgroup value of `cpu.shares = 2048` (or `cpu.weight=200` for cgroups version 2), twice the default value. If you have a mix of cgroups combining version 1 and 2 Hosts, there will be an inconsistent resource distribution when live-migrating a VM across different versions.

<a id="kvmg-memory-cleanup"></a>

### Memory Cleanup (Optional)

Memory allocated by caches or memory fragmentation may cause the VM to fail to deploy, even if there is enough memory on the Host at first sight. To avoid such failures and provide the best memory placement for the VMs, it’s possible to trigger memory cleanup and compaction before the VM starts and/or after the VM stops (by default enabled only on stop). The feature is configured in `/var/lib/one/etc/remotes/vmm/kvm/kvmrc` on the Front-end:

```default
# Compact memory before running the VM
#CLEANUP_MEMORY_ON_START=yes

# Compact memory after VM stops
CLEANUP_MEMORY_ON_STOP=yes
```

VM actions covered - `deploy`, `migrate`, `poweroff`, `recover`, `release`, `resize`, `save`, `resume`, `save`, `suspend`, and `shutdown`.

## Usage

### KVM-Specific Attributes

The following are template attributes specific to KVM. Please refer to the [template reference documentation]({{% relref "../../operation_references/configuration_references/template#template" %}}) for a complete list of the attributes supported to define a VM.

#### DISK

- `TYPE`: this attribute defines the type of media to be exposed to the VM; possible values are `disk` (default) or `cdrom`. This attribute corresponds to the `media` option of the `-driver` argument of the `kvm` command.
- `DRIVER`: specifies the format of the disk image; possible values are `raw`, `qcow2`… This attribute corresponds to the `format` option of the `-driver` argument of the `kvm` command.
- `CACHE`: specifies the optional cache mechanism; possible values are `default`, `none`, `writethrough`, and `writeback`.
- `IO`: sets IO policy; possible values are `threads` and `native`.
- `IOTHREAD`: thread id used by this disk. It can only be used for virtio disk controllers and if `IOTHREADS` > 0.
- `DISCARD`: controls what to do with trim commands; the options are `ignore` or `unmap`. It can only be used with virtio-scsi.
- IO Throttling support - You can limit TOTAL/READ/WRITE throughput or IOPS. Also, burst control for these IO operations can be set for each disk. [See the reference guide for the attributed names and purpose]({{% relref "../../operation_references/configuration_references/template#reference-vm-template-disk-section" %}}).

#### NIC

- `TARGET`: name for the tun device created for the VM. It corresponds to the `ifname` option of the ‘-net’ argument of the `kvm` command.
- `SCRIPT`: name of a shell script to be executed after creating the tun device for the VM. It corresponds to the `script` option of the ‘-net’ argument of the `kvm` command.
- QoS to control the network traffic. We can define different kinds of controls over network traffic:
  > - `INBOUND_AVG_BW`
  > - `INBOUND_PEAK_BW`
  > - `INBOUND_PEAK_KW`
  > - `OUTBOUND_AVG_BW`
  > - `OUTBOUND_PEAK_BW`
  > - `OUTBOUND_PEAK_KW`
- `MODEL`: ethernet hardware to emulate. You can get the list of available models with this command:

```default
$ kvm -net nic,model=? -nographic /dev/null
```

- `FILTER` to define a network filtering rule for the interface. Libvirt includes some predefined rules (e.g., clean-traffic) that can be used. [Check the Libvirt documentation](http://libvirt.org/formatnwfilter.html#nwfelemsRules) for more information; you can also list the rules in your system with:

```default
$ virsh -c qemu:///system nwfilter-list
```

- `VIRTIO_QUEUES` to define how many queues will be used for the communication between CPUs and Network drivers. This attribute is only available with `MODEL="virtio"`. The `auto` keyword automatically set the number of queues to the number of vCPUs.

#### Graphics

If properly configured, libvirt and KVM can work with SPICE ([check here for more information](http://www.spice-space.org/)). To select it, just add the following to the `GRAPHICS` attribute:

- `TYPE = SPICE`

Enabling SPICE will also make the driver inject a specific configuration for these machines. The configuration can be changed in the driver configuration file, variable `SPICE_OPTIONS`.

<a id="kvm-video"></a>

#### Video

If configured, libvirt will attach a video device to the Virtual Machine with the specified attributes. Available attributes are:

- `TYPE`: Defines the device type. Can be `none`, `vga`, `cirrus`, and `virtio`. Utilizing `virtio` is required for `IOMMU` and `ATS` options.
- `IOMMU`: Enables the device to use emulated IOMMU. Requires `virtio` type.
- `ATS`: Enables the device to use Address Translation Service. Requires `virtio` type.
- `VRAM`: Defines the amount of VRAM to allocate to the video device, in kB.
- `RESOLUTION`: Defines the preferred resolution of the video device. Should be two numbers separated by an `x`. Example: `1920x1080`

<a id="kvmg-virtio"></a>

#### Virtio

Virtio is the framework for IO virtualization in KVM. You will need a Linux kernel with the virtio drivers for the guest. Check [the KVM documentation for more info](http://www.linux-kvm.org/page/Virtio).

If you want to use the virtio drivers, add the following attributes to your devices:

- `DISK`, add the attribute `DEV_PREFIX="vd"`
- `NIC`, add the attribute `MODEL="virtio"`

For disks you can also use SCSI bus (`sd`) and it will use the virtio-scsi controller. This controller also offers high speed as it is not emulating real hardware, but it also adds support to trim commands to free disk space when the disk has the attribute `DISCARD="unmap"`. If needed, you can change the number of vCPU queues this way:

```default
FEATURES = [
    VIRTIO_SCSI_QUEUES = "auto"
]
```

Furthermore, you have the option to activate multi-queue support within the virtio-blk driver, enabling simultaneous management of distinct queues by various vCPUs. The `auto` keyword automatically sets the number of queues to the number of vCPUs. When fine-tuning this configuration you may need to consider the queue depth of the underlying hardware. Additionally, this feature can also be configured by `DISK`:

```default
FEATURES = [
    VIRTIO_BLK_QUEUES = "auto"
]
```

#### Firmware

The `OS/FIRMWARE` attribute can be defined to load a specific firmware interface
for Virtual Machines.
The allowed values are:

- `BIOS`: use Basic Input/Output System (BIOS).
- `<UEFI_PATH>`: one of the valid paths to a Unified Extensible Firmware Interface
  (UEFI) blob defined in `OVMF_UEFIS` (See [Driver Defaults]({{% relref "#kvmg-default-attributes" %}})).
   Review a setting of `OVMF_NVRAM` in `/var/lib/one/remotes/etc/vmm/kvm/kvmrc` config file

The `OS/FIRMWARE_FORMAT` attribute can be used to define the format of the UEFI NVRAM image. The `FIRMWARE_FORMAT` is valid only in case the `FIRMWARE` contains custom UEFI path. The NVRAM file will be automatically converted to the specified format if the source file differs. The allowed values are as below:

- `qcow2`: store the `UEFI NVRAM` as a `qcow2` image (requires `libvirt >= 10.10`).
- `raw`: store the `UEFI NVRAM` as a `raw` image (default value).

{{< alert title="Warning" type="warning" >}}
Internal UEFI VMs snapshots are only supported with `qcow2 UEFI NVRAM` images.
{{< /alert >}}

The `OS/FIRMWARE_SECURE` attribute can be used to configure _Secure Boot_. If
this attribute is not defined, no Secure Boot is used by default.
The allowed values are:

- `true`: use Secure Boot.
- `false`: do not use Secure Boot.

{{< alert title="Warning" type="warning" >}}
If Secure Boot is enabled, the attribute `OS/MACHINE` must be set to `q35`.{{< /alert >}}

All the OS & CPU options can be accessed in Sunstone from the VM Template Update/Create dialog, in the second step (Advanced options) under the "OS & CPU" tab.

![sunstone_os_cpu_tab](/images/sunstone_os_cpu_tab.png)

#### Additional Attributes

The `RAW` attribute allows end users to pass custom libvirt/KVM attributes not yet supported by OpenNebula. Basically, everything placed here will be written literally into the KVM deployment file (**use libvirt xml format and semantics**). You can selectively disable validation of the RAW data by adding `VALIDATE="no"` to the `RAW` section. By default, the data will be checked against the libvirt schema.

```default
RAW = [
  TYPE = "kvm",
  VALIDATE = "yes",
  DATA = "<devices><serial type=\"pty\"><source path=\"/dev/pts/5\"/><target port=\"0\"/></serial><console type=\"pty\" tty=\"/dev/pts/5\"><source path=\"/dev/pts/5\"/><target port=\"0\"/></console></devices>" ]
```

<a id="libvirt-metadata"></a>

#### Libvirt Metadata

The following OpenNebula information is added to the metadata section of the Libvirt domain. The specific attributes are listed below:

- `system_datastore`
- `name`
- `uname`
- `uid`
- `gname`
- `gid`
- `opennebula_version`
- `stime`
- `deployment_time`

They correspond to their OpenNebula equivalents for the XML representation of the VM. `opennebula_version` and `deployment_time` are the OpenNebula version used during the deployment and deployment time at epoch format, respectively.

Also the VM name is included in the libvirt XML `title` field, so if the `--title` option is used for listing the libvirt domains the VM name will be shown with the domain name.

<a id="kvm-live-resize"></a>

#### Live Resize VCPU and Memory

If you need to resize the capacity of the VM in `RUNNING` state, you have to set up some extra attributes to the VM template. These attributes must be set before the VM is started.

<!-- Markdown doesn't support merged cells in tables, so as a temporary workaround these are inserted in HTML -->

<table class="docutils align-default">
<thead>
<tr class="row-odd"><th class="head"><p>Attribute</p></th>
<th class="head"><p>Description</p></th>
<th class="head"><p>Mandatory</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even"><td><p><code class="docutils literal notranslate"><span class="pre">VCPU_MAX</span></code></p></td>
<td><p>Maximum number of VCPUs which can be hotplugged.</p></td>
<td><p><strong>NO</strong></p></td>
</tr>
<tr class="row-odd"><td rowspan="2"><p><code class="docutils literal notranslate"><span class="pre">MEMORY_RESIZE_MODE</span></code></p></td>
<td><p><code class="docutils literal notranslate"><span class="pre">HOTPLUG</span></code> - default. Internally use this <code class="docutils literal notranslate"><span class="pre">virsh</span> <span class="pre">attach-device</span></code> to add more memory. To remove
memory you have to remove the exact amount which was previously added. Prefer offline removing.</p></td>
<td rowspan="2"><p><strong>NO</strong></p></td>
</tr>
<tr class="row-even"><td><p><code class="docutils literal notranslate"><span class="pre">BALLOONING</span></code> - Internally use this <code class="docutils literal notranslate"><span class="pre">virsh</span> <span class="pre">setmem</span></code> to add more memory. The new memory size
is only recommendation for the VM, the actual memory usage may be different.
The target VM displays <code class="docutils literal notranslate"><span class="pre">MEMORY_MAX</span></code> as available memory.</p></td>
</tr>
<tr class="row-odd"><td><p><code class="docutils literal notranslate"><span class="pre">MEMORY_MAX</span></code></p></td>
<td><p>Maximum memory allocated for the VM.</p></td>
<td><p><strong>NO</strong></p></td>
</tr>
<tr class="row-even"><td><p><code class="docutils literal notranslate"><span class="pre">MEMORY_SLOTS</span></code></p></td>
<td><p>Valid only for <code class="docutils literal notranslate"><span class="pre">HOTPLUG</span></code>. How many memory slots can be used to add add memory. It implies
how many times the memory can be added.</p></td>
<td><p><strong>NO</strong></p></td>
</tr>
</tbody>
</table>

<!-- End HTML table. -->

{{< alert title="Note" type="info" >}}
Live Memory resize needs QEMU version 2.4. Live VCPU resize needs QEMU version 2.7.{{< /alert >}}

### MEMORY_RESIZE_MODE

`BALLOONING` consists in dynamically adjusting the amount of RAM allocated to VMs. It enables KVM to reclaim unused memory from one VM and allocate it to another VM that needs it more, without shutting down or pausing the VMs. The parameter sets up a **balloon driver** within the VM that communicates with the Host:
* When the Host needs to reclaim memory, the driver _inflates_, reserving some of the VM’s unused memory for the Host. 
* When the VM needs additional memory, the driver _deflates_, releasing reserved memory back to the VM.

From the VM’s standpoint, it seems like the available memory is decreasing or increasing. The OS inside the VM will think it’s using more memory when the balloon inflates and think it’s using less when the balloon deflates. This can go back and forth many times during the VM’s lifecycle, always ensuring that each VM has as much memory as it needs, up to `MEMORY_MAX`, but no more than that.

In `HOTPLUG` mode the Guest OS will perceive a new virtual RAM stick being plugged into the virtual motherboard. The downside of this mode is that in order to reduce memory, you need to remove the exact memory it was added before, which emulates the RAM stick removal. By default it is limited to 16 RAM stick devices (i.e., you can increase memory by hotplug 16 times).

### Disk/NIC Hotplugging

KVM supports hotplugging to the `virtio` and the `SCSI` buses. For disks, the bus the disk will be attached to is inferred from the `DEV_PREFIX` attribute of the disk template.

- `vd`: `virtio`
- `sd`: `SCSI` (default)
- `hd`: `IDE`

{{< alert title="Note" type="info" >}}
Hotplugging is not supported for CD-ROM and floppy.{{< /alert >}}

If `TARGET` is passed instead of `DEV_PREFIX` the same rules apply (what happens behind the scenes is that OpenNebula generates a `TARGET` based on the `DEV_PREFIX` if no `TARGET` is provided).

The defaults for the newly attached disks and NICs are in `/var/lib/one/remotes/etc/vmm/kvm/kvmrc`. The relevant parameters are prefixed with `DEFAULT_ATTACH_` and explained in [Files and Parameters]({{% relref "#kvmg-files-and-parameters" %}}) below.

For Disks and NICs, if the guest OS is a Linux flavor, the guest needs to be explicitly told to rescan the PCI bus. This can be done by issuing the following command as root:

```default
# echo 1 > /sys/bus/pci/rescan
```

<a id="enabling-qemu-guest-agent"></a>

### Enabling QEMU Guest Agent

QEMU Guest Agent allows the communication of some actions with the guest OS. This agent uses a virtio serial connection to send and receive commands. One of the interesting actions is that it allows you to freeze the filesystem before doing a snapshot. This way the snapshot won’t contain half-written data. Filesystem freeze will only be used with `CEPH` and `qcow2` storage drivers.

The agent package needed in the Guest OS is available in most distributions. It’s called `qemu-guest-agent` in most of them. If you need more information you can follow these links:

- [QEMU Guest Agent - libvirt](http://wiki.libvirt.org/page/Qemu_guest_agent)
- [QEMU Guest Agent - rhel](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_virtualization/assembly_enabling-virtualization-in-rhel-9_configuring-and-managing-virtualization#enabling-qemu-guest-agent-features-on-your-virtual-machines_assembly_enabling-virtualization-in-rhel-9)
- [Guest Agent Features](https://wiki.qemu.org/Features/GuestAgent)

The communication channel with guest agent is enabled in the domain XML when the `GUEST_AGENT` feature is selected in the VM Template.

### QEMU Guest Agent Monitoring

You can enable and extend the VM monitoring information gathered by the guest agent by setting `:enabled` to **true** on the file `/var/lib/one/remotes/etc/im/kvm-probes.d/guestagent.conf`. Execute `onehost sync --force` afterwards.

When enabled, the QEMU Guest Agent will by default monitor the non-loopback IPv4 and IPv6 addresses reported by the guest network interfaces. These values are stored in the `MONITORING/GUEST_IP_ADDRESSES` attribute and will be displayed in the Sunstone interface.

### Custom QEMU Guest Agent Commands

You can also define custom guest agent commands to put specific information in the monitoring output. The configuration file `/var/lib/one/remotes/etc/im/kvm-probes.d/guestagent.conf` also contains a list of `:commands` that will be executed when running the VM monitoring probes. The result of the execution of these commands will appear on the MONITORING section on the VM instance template.

By default an example command is provided, this effectively allows us to detect VM crashes:

```yaml
:commands:
  :vm_qemu_ping: 'one-$vm_id ''{"execute":"guest-ping"}'' --timeout 5'
```

As a result you’ll see on the MONITORING section an output containing the result of executing said command and parsing the `return` key, which is `{}`

```json
{
  "CPU": "0.0",
  "DISKRDBYTES": "287175970",
  "DISKRDIOPS": "14795",
  "DISKWRBYTES": "2655895040",
  "DISKWRIOPS": "36070",
  "DISK_SIZE": [
    {
      "ID": "0",
      "SIZE": "863"
    },
    {
      "ID": "1",
      "SIZE": "1"
    }
  ],
  "ID": "159",
  "MEMORY": "1838804",
  "NETRX": "135117657",
  "NETTX": "630067",
  "TIMESTAMP": "1720712912",
  "VM_QEMU_PING": "{}"
}
```

If a VM doesn’t have the qemu guest agent or libvirt cannot query it, you’ll get in the `VM_QEMU_PING` section an output like `error: Guest agent is not responding: QEMU guest agent is not connected`.

You can define your custom commands. For example, the guest agent command `virsh qemu-agent-command one-159 '{"execute":"guest-info"}' | jq .` showcases detailed guest information:

```json
{
  "return": {
    "version": "6.2.0",
    "supported_commands": [
      {
        "enabled": true,
        "name": "guest-ssh-remove-authorized-keys",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-ssh-add-authorized-keys",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-ssh-get-authorized-keys",
        "success-response": true
      },
      {
        "enabled": false,
        "name": "guest-get-devices",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-get-osinfo",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-ping",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-sync",
        "success-response": true
      },
      {
        "enabled": true,
        "name": "guest-sync-delimited",
        "success-response": true
      }
    ]
  }
}
```

You can translate that into a command on the configuration file as follows

```yaml
:enabled: true
:commands:
  :vm_qemu_ping: 'one-$vm_id ''{"execute":"guest-ping"}'' --timeout 5'
  :guest_info: 'one-$vm_id ''{"execute":"guest-info"}'' --timeout 5'
```

You can also configure commands to be selectively executed on VMs depending on their OS and architecture. These conditional commands use an alternative syntax to allow providing one or more filters. Let's modify the previous example to only execute the `guest_info` command in VMs running Ubuntu 22.04/24.04:

```yaml
:enabled: true
:commands:
  :vm_qemu_ping: 'one-$vm_id ''{"execute":"guest-ping"}'' --timeout 5'
  :guest_info:
    :command: 'one-$vm_id ''{"execute":"guest-info"}'' --timeout 5'
    :os_ids: ['ubuntu']
    :os_versions: ['24.04', '22.04']
```

Filtering works by previously extracting and storing special OS_ attributes from `guest-get-osinfo`, whose values will then be used to check each condition. They can also be accessed in the MONITORING section. The corresponding attribute must then match exactly (case sensitive) one of the given filters for the VM to be eligible to run the command. Providing several filters requires the VM to match each of them.

This table summarizes the available filters and corresponding OS monitoring attributes:

| Filter      | Attribute Matched | Possible Values                          | Comments                                |
| ----------- | ----------------- | ---------------------------------------- | --------------------------------------- |
| os_types    | OS_TYPE           | `posix`, `mswindows`                     |                                         |
| os_ids      | OS_ID             | OS/distro ID (e.g., `ubuntu`, `freebsd`) | From os-release(5) ID attribute         |
| os_versions | OS_VERSION        | Version ID (e.g., `3.20.9`, `24.04`)     | From os-release(5) VERSION_ID attribute |
| os_machines | OS_MACHINE        | Architecture (e.g., `x86_64`, `amd64`)   | From `uname -m`                         |

## Tuning & Extending

<a id="kvm-multiple-actions"></a>

### Multiple Actions per Host or Cluster

By default the VMM driver is configured to allow more than one action to be executed per Host. Make sure the parameter `-p` is added to the driver executable. This is done in `/etc/one/oned.conf`, in the `VM_MAD` configuration section:

```default
VM_MAD = [
    NAME       = "kvm",
    EXECUTABLE = "one_vmm_exec",
    ARGUMENTS  = "-t 15 -r 0 kvm -p",
    DEFAULT    = "vmm_exec/vmm_exec_kvm.conf",
    TYPE       = "kvm" ]
```

Additionally, also in `/etc/one/oned.conf`, increase the value of the `MAX_ACTIONS_PER_HOST` (default = `1`), for example:

```default
MAX_ACTIONS_PER_HOST = 10
```

To increase the maximum number of allowed actions per cluster, increase the value of the `MAX_ACTIONS_PER_CLUSTER` parameter (default = `30`).

After changing `/etc/one/oned.conf`, restart the main OpenNebula service:

```default
$ sudo systemctl restart opennebula
```

Additionally, if you are using the Rank Scheduler, you will need to change the configuration to let the scheduler deploy more than one VM per Host. In the file `/etc/one/schedulers/rank.conf`, change the value of the `MAX_HOST` parameter. For example, to let the scheduler submit 10 VMs per Host:

```default
MAX_HOST = 10
```

Changes in `rank.conf` do not require a restart.

```default
$ sudo systemctl restart opennebula-scheduler
```

<a id="kvmg-files-and-parameters"></a>

### Files and Parameters

The driver consists of the following files:

- `/usr/lib/one/mads/one_vmm_exec` : generic VMM driver.
- `/var/lib/one/remotes/vmm/kvm` : commands executed to perform actions.

And the following driver configuration files:

- `/etc/one/vmm_exec/vmm_exec_kvm.conf` : this file contains default values for KVM domain definitions;  in other words, OpenNebula templates. It is a good practice to configure defaults for the KVM-specific attributes here, that is, attributes mandatory in the KVM driver that are not mandatory for other hypervisors. Non-mandatory attributes for KVM but specific to them are also recommended to have a default. Changes to this file **require opennebula to be restarted**.

* `/var/lib/one/remotes/etc/vmm/kvm/kvmrc` : this file holds instructions to be executed before the actual driver load to perform specific tasks or to pass environmental variables to the driver. The syntax used for the former is plain shell script that will be evaluated before the driver execution. For the latter, the syntax is the familiar:

```default
ENVIRONMENT_VARIABLE=VALUE
```

The parameters that can be changed here are as follows:

| Parameter                                   | Description                                                                                                                                                                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `LIBVIRT_URI`                               | Connection string to libvirtd.                                                                                                                                                                                     |
| `QEMU_PROTOCOL`                             | Protocol used for live migrations.                                                                                                                                                                                 |
| `SHUTDOWN_TIMEOUT`                          | Seconds to wait after shutdown until timeout.                                                                                                                                                                      |
| `VIRSH_RETRIES`                             | Number of “virsh” command retries when required. Currently used in detach-interface and restore.                                                                                                                   |
| `VIRSH_TIMEOUT`                             | Default “virsh” timeout for operations which might block indefinitely.                                                                                                                                             |
| `SYNC_TIME`                                 | Trigger VM time synchronization from RTC on resume and after migration. QEMU guest agent must be running.<br/>Valid values: `no` or `yes` (default).                                                               |
| `FORCE_DESTROY`                             | Force VM cancellation after shutdown timeout.                                                                                                                                                                      |
| `CANCEL_NO_ACPI`                            | Force VMs without ACPI enabled to be destroyed on shutdown.                                                                                                                                                        |
| `MIGRATE_OPTIONS`                           | Set options for the virsh migrate command.                                                                                                                                                                         |
| `CLEANUP_MEMORY_ON_START`                   | Compact memory before running the VM. Values `yes` or `no` (default).                                                                                                                                              |
| `CLEANUP_MEMORY_ON_STOP`                    | Compact memory after VM stops. Values `yes` or `no` (default).                                                                                                                                                     |
| `DEFAULT_ATTACH_CACHE`                      | This parameter will set the default cache type for new attached disks. It will be used in case the attached disk does<br/>not have a specific cache method set (can be set using templates when attaching a disk). |
| `DEFAULT_ATTACH_DISCARD`                    | Default discard option for newly attached disks, if the attribute is missing in the template.                                                                                                                      |
| `DEFAULT_ATTACH_IO`                         | Default I/O policy for newly attached disks, if the attribute is missing in the template.                                                                                                                          |
| `DEFAULT_VIRTIO_BLK_QUEUES`                 | The default number of queues for virtio-blk driver.                                                                                                                                                                |
| `DEFAULT_ATTACH_TOTAL_BYTES_SEC`            | Default total bytes/s I/O throttling for newly attached disks, if the attribute is missing. in the template                                                                                                        |
| `DEFAULT_ATTACH_TOTAL_BYTES_SEC_MAX`        | Default Maximum total bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                                |
| `DEFAULT_ATTACH_TOTAL_BYTES_SEC_MAX_LENGTH` | Default Maximum length total bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                         |
| `DEFAULT_ATTACH_READ_BYTES_SEC`             | Default read bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                                         |
| `DEFAULT_ATTACH_READ_BYTES_SEC_MAX`         | Default Maximum read bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                                 |
| `DEFAULT_ATTACH_READ_BYTES_SEC_MAX_LENGTH`  | Default Maximum length read bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                          |
| `DEFAULT_ATTACH_WRITE_BYTES_SEC`            | Default write bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                                        |
| `DEFAULT_ATTACH_WRITE_BYTES_SEC_MAX`        | Default Maximum write bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                                |
| `DEFAULT_ATTACH_WRITE_BYTES_SEC_MAX_LENGTH` | Default Maximum length write bytes/s I/O throttling for newly attached disks, if the attribute is missing in the template.                                                                                         |
| `DEFAULT_ATTACH_TOTAL_IOPS_SEC`             | Default total IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                               |
| `DEFAULT_ATTACH_TOTAL_IOPS_SEC_MAX`         | Default Maximum total IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                       |
| `DEFAULT_ATTACH_TOTAL_IOPS_SEC_MAX_LENGTH`  | Default Maximum length total IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                |
| `DEFAULT_ATTACH_READ_IOPS_SEC`              | Default read IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                                |
| `DEFAULT_ATTACH_READ_IOPS_SEC_MAX`          | Default Maximum read IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                        |
| `DEFAULT_ATTACH_READ_IOPS_SEC_MAX_LENGTH`   | Default Maximum length read IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                 |
| `DEFAULT_ATTACH_WRITE_IOPS_SEC`             | Default write IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                               |
| `DEFAULT_ATTACH_WRITE_IOPS_SEC_MAX`         | Default Maximum write IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                       |
| `DEFAULT_ATTACH_WRITE_IOPS_SEC_MAX_LENGTH`  | Default Maximum length write IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                |
| `DEFAULT_ATTACH_SIZE_IOPS_SEC`              | Default size of IOPS throttling for newly attached disks, if the attribute is missing in the template.                                                                                                             |
| `DEFAULT_ATTACH_NIC_MODEL`                  | Default NIC model for newly attached NICs, if the attribute is missing in the template.                                                                                                                            |
| `DEFAULT_ATTACH_NIC_FILTER`                 | Default NIC libvirt filter for newly attached NICs, if the attribute is missing in the template.                                                                                                                   |
| `OVMF_NVRAM`                                | Virtual Machine Firmware path to the NVRAM file.                                                                                                                                                                   |

See the [Virtual Machine drivers reference]({{% relref "../../../product/integration_references/infrastructure_drivers_development/devel-vmm#devel-vmm" %}}) for more information.

<a id="arm64specifics"></a>

## ARM64 Specifics

We suggest the following adjustments for the ARM64 architecture. In `/etc/one/oned.conf`, switch to `sd` or `vd` for the CD-ROM device:

```default
DEFAULT_CDROM_DEVICE_PREFIX = "sd"
```

This is necessary as IDE disk support is usually missing in ARM64.

Additionally, we recommend adding a virtio keyboard using the `RAW` attribute in `/etc/one/vmm_exec/vmm_exec_kvm.conf` to ensure keyboard functionality over VNC:

```default
RAW = "<devices><input type='keyboard' bus='virtio'/></devices>"
```

The following OS section is recommended for an ARM64 Host template. Here, `virt` is typically an alias for the most recent `QEMU ARM Virtual Machine`:

```default
OS=[
  ARCH="aarch64",
  FIRMWARE="/usr/share/AAVMF/AAVMF_CODE.fd",
  FIRMWARE_FORMAT='raw',
  FIRMWARE_SECURE="no",
  MACHINE="virt"
]
```

## Troubleshooting

### Image Magic Is Incorrect

When trying to restore the VM from a suspended state this error is returned:

```default
libvirtd1021: operation failed: image magic is incorrect
```

It can be fixed by applying:

```default
options kvm_intel nested=0
options kvm_intel emulate_invalid_guest_state=0
options kvm ignore_msrs=1
```
