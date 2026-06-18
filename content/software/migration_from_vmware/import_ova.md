---
title: "Managing OVAs and VMDKs"
description:
categories:
pageintoc: ""
tags:
weight: "2"
---

<a id="ova-management-overview"></a>

## Overview

OpenNebula supports importing OVAs that have been exported from vCenter / ESXi environments, generating the necessary VM Template and Images.

It is possible to import **.ova** files or a folder containing the OVF files (VMDK disk files and manifest file in **.ovf** format). The import tool will inject [context packages]({{% relref "kvm_contextualization#kvm-contextualization" %}}) in the target Images, automatically detecting the guest operating system.

The same command allows users to import single VMDK disks as OpenNebula Images, converting the VMDK to qcow2 format and then creating the associated Image. It is possible to inject context, install [virtio drivers](#windows-virtio-drivers) and uninstall VMware Tools.

<a id="import-ova"></a>

<!--# OVA/VMDK Import -->

## Install

OneSwap is developed and maintained by OpenNebula on a [dedicated github repository](https://github.com/OpenNebula/one-swap). Starting from OpenNebula 7.0, OneSwap is being shipped as a package called `opennebula-swap` in the [OpenNebula Repositories]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration.md" %}}) for Ubuntu 24.04, AlmaLinux 9 and Debian 12. Install the `opennebula-swap` package with your package manager.

The required dependencies (`virt-v2v`, `guestfs-tools`, `qemu-img`, `ovmf`, etc.) are installed automatically with the package. The complete list is available in the [System Requirements]({{% relref "oneswap#system-requirements" %}}) section of the OneSwap guide. For Windows guests, also check the [required software for migrating Windows Virtual Machines]({{% relref "oneswap#required-software-for-migrating-windows-virtual-machines" %}}) (VirtIO drivers and RHsrvany) and, if the guest uses NTFS system compression, the [Windows CompactOS Support]({{% relref "oneswap#windows-compactos-support" %}}) section.

### Configure

The `oneswap import` command reads its default values from the file `/var/lib/one/oneswap.yaml`. In here you can configure multiple items related to several aspects of OneSwap. For example, the OVA import process takes place by default at `/var/tmp`. The resulting qcow2 image is then imported with a `one.image.allocate` call that takes `/var/tmp/<vm_name>/conversions/<qcow2_disk>.qcow2` as the path argument. By setting a `:work_dir` you can customize where these two operations take place.

```yaml
# virt-v2v Options
#:work_dir: '/var/tmp'                    # Directory where disk conversion takes place, will make subdir for each VM
#:format: 'qcow2'                         # Disk format [ qcow2 | raw ]
#:qemu_ga_win:                            # Path to QEMU Guest Agent ISO for Windows
#:qemu_ga_linux:                          # Install QEMU Guest Agent for Linux
#:virtio_path:                            # Path to VirtIO drivers for Windows
#:virt_tools: /usr/local/share/virt-tools # Path to the directory containing rhsrvany.exe
#:v2v_path: 'virt-v2v'                    # Path to virt-v2v
#:root: 'first'                           # Choose the root filesystem to be converted

# Extra Options
#:delete: false                           # Delete the VM Disks after transfer
#:context: '/usr/share/one/context/'      # Path to OpenNebula context packages
#:context_min_free: 1024                  # Minimum free MB on the guest root filesystem before context injection (0 to disable)
#:context_fail_on_low_space: false        # Fail the disk conversion (instead of warning and skipping) when free space is below the threshold
#:context_timeout: 600                    # Max seconds for each context injection command before it is aborted (0 to disable)
#:remove-vmtools: false                   # Add context script to force remove of VMWare Tools
#:uefi_path: '/usr/share/OVMF/OVMF_CODE.fd'                 # Path to the UEFI file to be configured in the VM template.
#:uefi_sec_path: '/usr/share/OVMF/OVMF_CODE.secboot.fd'     # Path to the UEFI Secure file to be configured in the VM template.

# OpenNebula Ownership Options
#:one_user:                               # Assign migrated objects to this OpenNebula user (name or numeric ID)
#:one_group:                              # Assign migrated objects to this OpenNebula group (name or numeric ID)
```

### Windows VirtIO Drivers

Before converting Windows VMs, download the required VirtIO drivers for the Windows VM distribution. These drivers can be downloaded from the [virtio-win repository](https://github.com/virtio-win/virtio-win-pkg-scripts/blob/master/README.md).

{{< alert title="Note" type="info" >}}
The converted VM will reboot several times after instantiation in order to install and configure the VirtIO drivers.{{< /alert >}}

## Usage

The full documentation for OneSwap is maintained in [Migrating VMs with OneSwap]({{% relref "oneswap" %}}). Refer to `man oneswap` for the complete reference of the `oneswap` command.

OneSwap will assume that the provided OVA has been exported from a VMware environment. Users must make sure that the provided OVA is compatible with VMware environments. Other sources are currently not supported (i.e., Xen or VirtualBox).

When converting an OVA or VMDK you will need enough space both in the working directory `/var/tmp` (can be changed with `--work-dir`) and in the destination Datastore where the disk images are going to be imported.

The parent OVA directory name should match the name of the OVA files inside it. For example

```
ovf_test/
├── ovf_test-1.vmdk
├── ovf_test-2.nvram
├── ovf_test.mf
└── ovf_test.ovf
```


It is possible to specify the target Datastore and VNET for the OVA to be imported. Available options for the `oneswap import` command are:

| Parameter                              | Description                                                                                                                                                                                                     |
|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--ova file.ova \| /path/to/ovf/files/` | Path to the OVA file or folder containing the OVF files.                                                                                                                                                        |
| `--vmdk /path/to/disk.vmdk`            | Path to the VMDK disk file.                                                                                                                                                                                     |
| `--datastore ID`                       | ID of the Image Datastore to store the new Image. Default: `1`. Accepts one or more Datastore IDs (i.e. `--datastore 101,102`). When more than one Datastore is provided, each disk will be allocated in a different one. |
| `--network ID`                         | ID of the VNET to assign in the VM Template. Accepts one or more VNET IDs (i.e. `--network 0,1`). When more than one VNET is provided, each interface from the OVA will be assigned to each VNET. **Not supported for VMDK**.     |
| `--virtio /path/to/virtio.iso`         | Path to the ISO file with the VirtIO drivers for the Windows version.                                                                                                                                           |
| `--skip-context`                       | Skip injection of the context package.                                                                                                                                                                                                 |
| `--remove-vmtools`                     | Add contextualization script to force remove VMware tools from the VM on its first boot (supported for Linux and Windows guests).                                                                                |
| `--inject-dns host\|ip`                | Pass `host` to copy the host's `/etc/resolv.conf` into the guest, or pass one or more comma-separated DNS server IPs (e.g. `8.8.8.8` or `8.8.8.8,1.1.1.1`) to generate a custom `resolv.conf`.                  |
| `--context-min-free MB`                | Minimum free space (in MB) required on the guest root filesystem before context injection. If free space is below this threshold OneSwap warns and skips the injection. Set to `0` to disable. Default: `1024`. |
| `--context-fail-on-low-space`          | Fail the disk conversion instead of warning and skipping when the guest root filesystem free space is below `--context-min-free`.                                                                               |
| `--context-timeout SECONDS`            | Maximum time allowed for each context injection command before it is aborted. Set to `0` to disable. Default: `600`.                                                                                            |
| `--uefi-path /path/to/uefi`            | Path to the UEFI firmware file to be configured in the VM template for UEFI guests.                                                                                                                             |
| `--uefi-sec-path /path/to/uefi.secboot` | Path to the UEFI Secure Boot firmware file to be configured in the VM template.                                                                                                                                 |
| `--one-user user`                      | Assign the migrated objects (Images, VM Template) to this OpenNebula user (name or numeric ID).                                                                                                                 |
| `--one-group group`                    | Assign the migrated objects (Images, VM Template) to this OpenNebula group (name or numeric ID).                                                                                                                |

{{< alert title="Note" type="info" >}}
The options `--ova` and `--vmdk` are mutually exclusive, they cannot be used together.{{< /alert >}}

If multiple network interfaces are detected when importing an OVA and only one VNET ID or not enough VNET IDs are provided for all interfaces using `--network ID`, the last provided VNET will be used for the remaining interfaces. For Datastores, when not enough Datastore IDs are provided with `--datastore ID`, the remaining disks will be allocated in the first provided Datastore.

When the imported guest is detected as Windows, OneSwap automatically tunes the resulting VM Template following KVM best practices for Windows (Hyper-V enlightenments, `host-passthrough` CPU model, q35 machine type, virtio devices). See the [Windows notes in the OneSwap guide]({{% relref "oneswap#on-windows-vms" %}}) for the details.

### Example of Importing an OVA

Example command on how to import an OVA using the Datastore ID 101 and VNET ID 1:

```default
$ oneswap import --ova /ovas/vm-alma9/ --datastore 101 --network 1
Running: virt-v2v -v --machine-readable -i ova /ovas/vm-alma9/ -o local -os /var/tmp/vm-alma9/conversions/ -of qcow2 --root=first

Setting up the source: -i ova /home/onepoc/ovas/vm-alma9/

(...)

$ onetemplate list
ID USER     GROUP    NAME               REGTIME
63 onepoc   oneadmin vm-alma9    03/24 16:34:34

$ onetemplate instantiate 63
VM ID: 103
```

### Example of Importing an OVA with Multiple DSs and VNETs

The source OVA has two disks and two NICs, as can be seen from the `.ovf` file:

```default
<DiskSection>
    <Info>List of the virtual disks</Info>
    <Disk ovf:capacityAllocationUnits="byte" ovf:format="http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized" ovf:diskId="vmdisk1" ovf:capacity="8589934592" ovf:fileRef="file1"/>
    <Disk ovf:capacityAllocationUnits="byte" ovf:format="http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized" ovf:diskId="vmdisk2" ovf:capacity="2147483648" ovf:fileRef="file2"/>
</DiskSection>
<NetworkSection>
    <Info>The list of logical networks</Info>
    <Network ovf:name="VM Network 0">
    <Description>The VM Network 0 network</Description>
    </Network>
    <Network ovf:name="VM Network 1">
    <Description>The VM Network 1 network</Description>
    </Network>
</NetworkSection>
```

Example command on how to import an OVA with two disks and two network interfaces, importing each disk to a different Datastore and assigning each NIC to a different VNET:

```default
$ oneswap import --ova /home/onepoc/ovas/ubuntu2404.ova --datastore 1,101 --network 1,0
Running: virt-v2v -v --machine-readable -i ova /home/onepoc/ovas/ubuntu2404.ova -o local -os /var/tmp/ubuntu2404/conversions/ -of qcow2 --root=first

Setting up the source: -i ova /home/onepoc/ovas/ubuntu2404.ova

(...)

$ onetemplate list
ID  USER     GROUP    NAME                  REGTIME
101 onepoc   oneadmin ubuntu2404    04/10 12:55:03
```

The OS Image is imported in Datastore 1 and the Datablock Image is imported in Datastore 101, and the VM Template has one NIC using VNET 1 and a second NIC using VNET 0.

```default
$ oneimage list
ID  USER     GROUP    NAME            DATASTORE     SIZE TYPE PER STAT RVMS
151 onepoc   oneadmin ubuntu2404_1    NFS image       2G DB    No rdy     0
150 onepoc   oneadmin ubuntu2404_0    default         8G OS    No rdy     0

$ onetemplate show 101 | grep NIC -A 1
NIC=[
    NETWORK_ID="1" ]
NIC=[
    NETWORK_ID="0" ]
```

### Example of Importing VMDK Uninstalling VMware Tools

Example command on how to import a VMDK disk using the Datastore ID 101:

```default
[onepoc@nebulito ~]$ oneswap import --vmdk /home/onepoc/ovas/vm-debian125/vm-debian125-1.vmdk --datastore 101 --remove-vmtools
Converting the Image => Converting disk /home/onepoc/ovas/vm-debian125/vm-debian125-1.vmdk to qcow2...
    (100.00/100%)
Disk converted successfully in 58.15 seconds.
Converted image: /var/tmp/vm-debian125-1/conversions/vm-debian125-1.qcow2

(...)

Allocating image 0 in OpenNebula
Waiting for image to be ready. Timeout: 120 seconds.
Created image: 174

[onepoc@nebulito ~]$ oneimage list
ID  USER     GROUP    NAME                DATASTORE     SIZE TYPE PER STAT RVMS
174 onepoc   oneadmin vm-debian125-1_0    NFS image       5G OS    No rdy     0
```

## Context Injection

OneSwap will detect the guest operating system and try to inject the context packages available from the [one-apps](https://github.com/opennebula/one-apps) repository. The packages are searched by default in `/usr/share/one/context`.

Before injecting the context, OneSwap checks that the guest root filesystem has enough free space (1024 MB by default, configurable with `--context-min-free`). If there is not enough free space, OneSwap warns and skips the injection — the context packages must then be installed manually — or aborts the conversion if `--context-fail-on-low-space` was given. Each injection command is also limited to `--context-timeout` seconds (600 by default).

For Linux guests, context injection will be performed following these steps:

1. Install context using package manager for the distro. However, this step may fail and trigger the execution of the fallback context installation command:

```default
Inspecting disk...Done (3.92s)
Injecting one-context...Running: virt-customize -q -a /var/tmp/vm-alma9/conversions/vm-alma9-sda --run-command 'subscription-manager repos --enable codeready-builder-for-rhel-9-$(arch)-rpms' --run-command 'yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm' --copy-in /usr/share/one/context/one-context-6.10.0-3.el9.noarch.rpm:/tmp --install /tmp/one-context-6.10.0-3.el9.noarch.rpm --delete /tmp/one-context-6.10.0-3.el9.noarch.rpm --run-command 'systemctl enable NetworkManager.service || exit 0'
Failed (6.31s)
```

2. Context will be installed using a fallback method of copying the context packages into the guest OS and installing it on the first boot in case the previous step fails. Sometimes it will be necessary to boot twice in order for this method to work.

```default
Running: virt-customize -q -a /var/tmp/vm-alma9/conversions/vm-alma9-sda --firstboot-install epel-release --copy-in /usr/share/one/context/one-context-6.10.0-3.el9.noarch.rpm:/tmp --firstboot-install /tmp/one-context-6.10.0-3.el9.noarch.rpm --run-command 'systemctl enable network.service || exit 0'
Success (42.24s)
Context will install on first boot, you may need to boot it twice.
```

For Windows guests, the context MSI package is copied into the guest and installed silently on the first boot.

With `--inject-dns`, OneSwap also configures the DNS resolvers in the guest (copying the host's `/etc/resolv.conf` or generating one from the provided server IPs), which is useful when the context installation on first boot needs working name resolution.

{{< alert title="Note" type="info" >}}
If context injection does not work after importing, it is also possible to install one-context **before exporting the OVA** from VMware using the packages available in the one-apps repository and uninstalling VMware Tools. In this case it is important to be aware that the one-context service will get rid of any manual network configurations done to the guest OS and the VM won’t be able to get the network configuration from VMware anymore.{{< /alert >}}

## Additional `virt-v2v` Options

The following parameters can be tuned for virt-v2v, defaults will be applied if no options are provided.

| Parameter                             | Description                                                                                                                                                                   |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--v2v-path /path/to/custom/v2v`      | Path to a custom `virt-v2v` executable if necessary. Default: `virt-v2v`.                                                                                                     |
| `--work-dir \| -w /path/to/work/dir` | Directory where disk conversion takes place, will make subdir for each VM. Default: `/var/tmp`.                                                                               |
| `--format \| -f name [ qcow2 \| raw ]` | Disk format `[ qcow2 \| raw ]`. Default: `qcow2`.                                                                                                                               |
| `--virtio /path/to/iso`             | Full path of the win-virtio ISO file. Required to inject VirtIO drivers to Windows Guests.                                                                                |
| `--win-qemu-ga /path/to/iso`        | Install QEMU Guest Agent to a Windows guest.                                                                                                                                  |
| `--qemu-ga`                           | Install qemu-guest-agent package to a Linux guest.                                                                                                                            |
| `--delete-after`                      | Removes the leftover conversion directory in the working directory which contains the converted VM disks and descriptor files.                                            |
| `--virt-tools /path/to/virt-tools`    | Path to the directory containing `rhsrvany.exe`, defaults to `/usr/local/share/virt-tools`. See [https://github.com/rwmjones/rhsrvany](https://github.com/rwmjones/rhsrvany). |
| `--root option`                       | Choose the root filesystem to be converted. Can be `ask`, `single`, `first` or `/dev/sdX`. Default: `first`.                                                                  |
