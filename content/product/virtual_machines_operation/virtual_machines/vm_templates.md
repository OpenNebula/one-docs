---
title: "Virtual Machine Templates"
linkTitle: "Templates"
date: "2025-02-17"
description:
categories:
pageintoc: "84"
tags:
weight: "2"
---

<a id="vm-guide"></a>

<a id="vm-templates"></a>

<!--# Virtual Machine Templates -->

In OpenNebula, VMs are defined with VM Templates. This section explains how to describe a Virtual Machine, and how users typically interact with the system.

OpenNebula administrators and users can register Virtual Machine definitions (VM Templates) in the system, to be instantiated later as Virtual Machine instances. These VM Templates can be instantiated several times and also shared with other users.

<a id="vm-guide-defining-a-vm-in-3-steps"></a>

## Defining a VM

A Virtual Machine Template, in basic terms, consists of:

- A capacity in terms of memory and CPU
- A set of NICs attached to one or more Virtual Networks
- A set of disk images
- Optional attributes like VNC graphics, the booting order, context information, etc.

VM Templates are stored in the system and can be easily browsed and used to instantiate VMs.

### Capacity & Name

Defines the basic attributes of the VM including its NAME, amount of RAM (`MEMORY`), or number of Virtual CPUs.

[See Capacity Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-capacity-section" %}}).

<a id="vm-disks"></a>

### Disks

Each disk is defined with a DISK attribute. A VM can use three types of disk:

- **Use a persistent Image**: changes to the disk Image will persist after the VM is terminated.
- **Use a non-persistent Image**: a copy of the source Image is used, changes made to the VM disk will be lost.
- **Volatile**: disks are created on-the-fly on the target Host. After the VM is terminated the disk is disposed.

[See Disks Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-disks-section" %}}).

### Network Interfaces & Alias

Network interfaces can be defined in two different ways:

- **Manual selection**: interfaces are attached to a pre-selected Virtual Network. Note that this may require building multiple templates that consider the available networks in each cluster.
- **Automatic selection**: Virtual Networks will be scheduled like other resources needed by the VM (like Hosts or datastores). This way, you can specify the type of network the VM will need and it will be automatically selected among those available in the cluster. [See more details here]({{% relref "../../cluster_configuration/networking_system/manage_vnets#vgg-vm-vnets" %}}).

KVM Templates can also define dummy interfaces, which create a guest NIC without attaching it to any OpenNebula Virtual Network. They do not inherit Virtual Network attributes such as gateway, DNS, security groups, or contextualization values. If no `MAC` is provided, OpenNebula generates one automatically. A dummy interface is defined with `NETWORK_MODE = "dummy"` in a `NIC` section:

```default
NIC = [
  NETWORK_MODE = "dummy",
  MAC          = "02:00:5e:00:00:01"
]
```

Network **interface alias** allows you to have more than one IP on each network interface. This does not create a new virtual interface on the VM. The alias address is added to the network interface. An alias can be attached and detached. Note also that when an NIC with an alias is detached, all the associated aliases are also detached.

The alias takes a lease from the network which it belongs to. So, for the OpenNebula it is the same as an NIC and exposes the same management interface, it is just different in terms of the associated Virtual Network interface within the VM.

{{< alert title="Note" type="info" >}}
The Virtual Network used for the alias can be different from that of the NIC of which it is an alias.{{< /alert >}}

[See Network Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-network-section" %}}).

### TPM

A virtual TPM (vTPM) can be added to KVM virtual machines by specifying the [TPM attribute]({{%
relref "../../operation_references/configuration_references/template#tpm-section" %}}). When doing
so, every VM instance will also spawn a companion TPM emulator process (swtpm) in charge of
emulating a physical TPM device for its VM.

In Sunstone the TPM attribute can be added to a VM Template in the Update/Create dialog, in the second step (Advanced options) under the "OS & CPU" tab.
![sunstone_vtpm_selector](/images/sunstone_vtpm_selector.png)

#### Initial host setup

{{< alert title="Note" type="info" >}}
**Only required for manual installations**. This setup is automatically done when installing the
`opennebula-node-kvm` package.
{{< /alert >}}

`swtpm` processes need to be launched with user/group `oneadmin`, as it opens a socket which will be
controlled by the qemu process, generate state files which need to be moved by OpenNebula, etc. So,
this is the required setup procedure to be executed **in each KVM host** beforehand in order to
deploy TPM-enabled VMs:

1. Edit `/etc/libvirt/qemu.conf` and set

```
swtpm_user = "oneadmin"
swtpm_group = "oneadmin"
```

2. Change the owner of the swtpm's CA directory:

```
chown -R oneadmin:oneadmin /var/lib/swtpm-localca/
```

3. Restart libvirtd. For example:

```
systemctl restart libvirtd
```

#### vTPM state quirks

The emulator needs to store a state and this introduces some additional complexities, although most
of them will be handled by either OpenNebula or libvirt itself:

- VM migration implies moving the TPM state too. This is done by libvirt automatically for both
  offline and live migrations.
- VM backups will also store the TPM state. OpenNebula will internally treat the TPM as an special
  kind of disk, so it will be stored in the backup server in a similar way.
- Then, recovering from a backup image will put the saved TPM state into the new VM template as a
  Base64 encoded attribute (`TPM_STATE`), which will be used to initialize the TPM during VM
  instantiation.
- When restoring a virtual machine (VM) from a backup, the user may choose to restore all disks or
  only a single disk. Restoring all disks also restores the TPM state, while restoring a single disk
  will only restore the TPM state if the selected disk is the root disk (ID 0), which is assumed to
  contain the operating system.
- Performing operations which involve temporally destroying the libvirt VM, such as
  poweroff/undeploy or stop/suspend, make libvirt destroy the TPM state too. In those cases,
  OpenNebula takes care of saving and restoring it in a transparent way.

{{< alert title="Warning" type="warning" >}}
You must be extra careful with manual operations, such as shutting down the VM using `virsh`, as the
TPM state is not persisted the same way as disks and could be deleted by libvirt. Depending on the
way the VM uses the TPM, losing its state ranges from being innocuous to quite catastrophic, for
example, when using it to store the keys of an encrypted disk. As a rule of thumb, remember to
always use the OpenNebula provided interfaces (Sunstone, CLI, etc) to operate VMs, particularly the
ones depending on a TPM state.
{{< /alert >}}

[See TPM Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#tpm-section" %}}).

### Memory Encryption

Memory encryption can be enabled in Virtual Machines by adding the following information to the VM Template

```none
MEMORY_ENCRYPTION=[
  TYPE="SEV"
]
```

There are several **virtualization security types**. We currently support `SEV` and `SEV-ES`. The KVM driver monitoring will automatically detect the memory encryption supported by each host. Depending on the CPU capabilities and BIOS configuration, different values can be shown by the monitoring probe.

```none
oneadmin@one-fe:~$ onehost show 5 -j | jq .HOST.TEMPLATE.MEMORY_ENCRYPTION
"SEV"
```

Possible values are: `NONE|SEV|SEV-ES|SEV-SNP|TDX`

More template configuration is required, otherwise the Guest OS might not load correctly.

```none
CPU_MODEL=[
  MODEL="host-passthrough" ]
OS=[
  FIRMWARE="UEFI",
  MACHINE="q35" ]
```

The VM will be automatically deployed to hosts with the desired memory encryption.

A VM with encrypted memory will have a report in the Guest OS kernel message

```none
localhost:~ # dmesg | grep -i sev
[    0.054053] Memory Encryption Features active: AMD SEV
```

#### Host Preparation - SEV

You need a CPU in the KVM host that is able to encrypt memory. You can check this capability on the CPU flags. Note the following AMD CPU includes `sev` and `sev_es`

```none
oneadmin@sm23:~$ lscpu | grep -i sev
Flags:                                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good amd_lbr_v2 nopl nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba perfmon_v2 ibrs ibpb stibp ibrs_enhanced vmmcall fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a avx512f avx512dq rdseed adx smap avx512ifma clflushopt clwb avx512cd sha_ni avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local user_shstk avx_vnni avx512_bf16 clzero irperf xsaveerptr rdpru wbnoinvd amd_ppin cppc amd_ibpb_ret arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif x2avic v_spec_ctrl vnmi avx512vbmi umip pku ospke avx512_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg avx512_vpopcntdq la57 rdpid bus_lock_detect movdiri movdir64b overflow_recov succor smca fsrm avx512_vp2intersect flush_l1d sev sev_es debug_swap
```

Then you need to make sure the capability is enabled in the BIOS. The following host has SEV enabled but SEV-ES disabled

```none
root@sm23:/home/one# dmesg | grep -i sev
[    7.284091] ccp 0000:a3:00.5: sev enabled
[    7.705036] ccp 0000:a3:00.5: SEV API:1.55 build:61
[    7.719788] kvm_amd: SEV enabled (ASIDs 1 - 1006)
[    7.719791] kvm_amd: SEV-ES disabled (ASIDs 0 - 0)
```

Now check if libvirt is able to make use of this feature. To do this, you can run the `virsh domcapabilities` command.

```none
oneadmin@sm23:~$ virsh domcapabilities | xmllint --xpath "/domainCapabilities/features/sev" -
<sev supported="yes">
      <cbitpos>51</cbitpos>
      <reducedPhysBits>1</reducedPhysBits>
      <maxGuests>1006</maxGuests>
      <maxESGuests>0</maxESGuests>
      <cpu0Id>ey5j9CwuSUE=</cpu0Id>
    </sev>
```

After that, both oneadmin and libvirt need to be able to use the `/dev/sev` device.
- Set `/dev/sev rw,` in `/etc/apparmor.d/abstractions/libvirt-qemu` if using an Operating System that relies on apparmor.
- Run the command `chmod o+wr /dev/sev` to allow oneadmin to use that device.
  - These permissions will not persist. You can automate them with [udev rules](https://www.freedesktop.org/software/systemd/man/latest/udev.html)
  - You can also restrict the ownership so that just oneadmin and libvirt are able to read and write `/dev/sev` instead of every other non root group user.

### A Complete Example

The following example shows a VM Template file with a couple of disks and a network interface. A VNC section and an alias were also added:

```none
NAME   = test-vm
MEMORY = 128
CPU    = 1

DISK = [ IMAGE  = "Arch Linux" ]
DISK = [ TYPE     = swap,
         SIZE     = 1024 ]

NIC = [ NETWORK = "Public", NETWORK_UNAME="oneadmin" ]

NIC = [ NETWORK = "Private", NAME = "private_net" ]
NIC_ALIAS = [ NETWORK = "Public", PARENT = "private_net" ]

GRAPHICS = [
  TYPE    = "vnc",
  LISTEN  = "0.0.0.0"]

TPM = [
  MODEL = "tpm-crb" ]
```

{{< alert title="Important" type="info" >}}
Check the [VM definition file for a complete reference]({{% relref "../../operation_references/configuration_references/template#template" %}}){{< /alert >}}

Simple Templates can be also created using the command line instead of creating a Template file. For example, a similar Template as the previous example can be created with the following command:

```default
$ onetemplate create --name test-vm --memory 128 --cpu 1 --disk "Arch Linux" --nic Public
```

For a complete reference of all the available options for `onetemplate create`, go to the [CLI reference]({{% relref "../../operation_references/command_line_interface/cli#cli" %}}), or run `onetemplate create -h`.

{{< alert title="Note" type="info" >}}
OpenNebula Templates are designed to be hypervisor-agnostic, but there are additional attributes that are supported for each hypervisor. Check the corresponding hypervisor guide for specific details.{{< /alert >}}

<a id="context-overview"></a>

## Virtual Machine Contextualization

OpenNebula uses a method called contextualization to send information to the VM at boot time. Its most basic usage is to share networking configuration and login credentials with the VM so it can be configured. More advanced cases can be starting a custom script on VM boot or preparing configuration to use [OpenNebula Gate]({{% relref "../multi-vm_workflows/onegate_usage#onegate-usage" %}}).

You can define contextualization data in the VM Template. [See Context Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-context" %}}).

<a id="vm-templates-endusers"></a>

## Preparing VM Templates for End Users

Besides the basic VM definition attributes, you can set up some extra options in your VM Template to make sharing it with other users easier.

### Customizable Capacity

The capacity attributes (`CPU`, `MEMORY`, `VCPU`) can be modified each time a VM Template is instantiated. The Template owner can decide if and how each attribute can be customized. The modification options available are:

- **fixed** (`fixed`): The value cannot be modified.
- **any value** (`text`): The value can be changed to any number by the user instantiating the Template.
- **range** (`range`): Users will be offered a range slider between the given minimum and maximum values.
- **list** (`list`): Users will be offered a drop-down menu to select one of the given options.

If you are using a Template file instead of Sunstone, the modification is defined with user input (`USER_INPUT`) attributes ([see below]({{% relref "#vm-guide-user-inputs" %}})). The absence of user input is an implicit _any value_. For example:

```none
CPU    = "1"
MEMORY = "2048"
VCPU   = "2"
USER_INPUTS = [
  VCPU   = "O|fixed|| |2"
  CPU    = "M|list||0.5,1,2,4|1",
  MEMORY = "M|range||512..8192|2048" ]
```

{{< alert title="Note" type="info" >}}
Use float types for CPU, and integer types for MEMORY and VCPU. More information in [the Template reference documentation]({{% relref "../../operation_references/configuration_references/template#template-user-inputs" %}}).{{< /alert >}}

{{< alert title="Note" type="info" >}}
This capacity customization can be forced to be disabled for any Template in the cloud view. Read more in the [Cloud View Customization documentation]({{% relref "../../../product/control_plane_configuration/graphical_user_interface/cloud_view.md" %}}).{{< /alert >}}

<a id="vm-guide-user-inputs"></a>

### User Inputs

The User Inputs functionality provides the VM Template creator with the possibility to ask for dynamic values. This is a convenient way to parametrize a base installation. These inputs will be presented to the user when the VM Template is instantiated. The VM guest needs to have the OpenNebula contextualization packages installed to make use of the values provided by the user. The following example shows how to pass some user inputs to a VM:

```none
USER_INPUTS = [
  BLOG_TITLE="M|text|Blog Title",
  MYSQL_PASSWORD="M|password|MySQL Password",
]

CONTEXT=[
  BLOG_TITLE="$BLOG_TITLE",
  MYSQL_PASSWORD="$MYSQL_PASSWORD" ]
```

{{< alert title="Note" type="info" >}}
If a VM Template with user inputs is used by a [Service Template Role]({{% relref "../multi-vm_workflows/appflow_use_cli#appflow-use-cli" %}}), the user will be also asked for these inputs when the Service is created.{{< /alert >}}

{{< alert title="Note" type="info" >}}
You can use the flag `--user-inputs ui1,ui2,ui3` to use them in a non-interactive way.{{< /alert >}}

[See User Inputs Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-user-inputs" %}}).

<a id="vm-guide-user-inputs-sunstone"></a>

#### User Inputs in Sunstone

When a Virtual Machine template is instantiated using Sunstone, the user will be asked to fill in the user inputs that are defined in the Virtual Machine template. So, using the following user inputs:

```none
USER_INPUTS = [
  BLOG_TITLE="M|text|Blog Title",
  BLOG_DESCRIPTION="O|text|Blog Description",
  MYSQL_ENDPOINT="M|text|MySQL Endpoint",
  MYSQL_USER="O|password|MySQL User",
  MYSQL_PASSWORD="O|password|MySQL Password",
  MYSQL_ADDITIONAL="O|boolean|Define additional parameters",
  MYSQL_SOCKET="O|text|MySQL Socket",
  MYSQL_CHARSET="O|text|MySQL Charset"
]
```

The result will be a step with all the user inputs that are defined in the Template:

![sunstone_user_inputs_no_convention](/images/sunstone_user_inputs_no_convention.png)

In order to improve the user experience, Sunstone can render these user inputs in a different way that is easy to understand for the Sunstone user. To do that, Sunstone uses rules based on the name of the user inputs. These rules are:

<a id="sunstone-layout-rules"></a>

- User input name has to meet the following convention `ONEAPP_<APP>_<GROUP>_<FIELD>` where all the user inputs that meet this convention will be grouped by APP and GROUP. An APP will be rendered as a tab in Sunstone and a GROUP will group the user inputs that belong to this group.
- If `FIELD` displays the word `ENABLED` and the user input type is boolean, all the user inputs that have the same APP and GROUP will be hidden until the ENABLED user input is turned on.
- If a user input does not meet the convention, it will be placed in a tab called Others.
- If all the user inputs do not meet the convention name, no tabs will be rendered (as in the previous example).

So, if the previous Template is modified as follows:

```none
USER_INPUTS = [
  ONEAPP_BLOG_CONF_TITLE="M|text|Blog Title",
  ONEAPP_BLOG_CONF_DESCRIPTION="O|text|Blog Description",
  ONEAPP_MYSQL_CONFIG_ENDPOINT="M|text|MySQL Endpoint",
  ONEAPP_MYSQL_CONFIG_USER="O|password|MySQL User",
  ONEAPP_MYSQL_CONFIG_PASSWORD="O|password|MySQL Password",
  ONEAPP_MYSQL_ADDITIONAL_ENABLED="O|boolean|Define additional parameters",
  ONEAPP_MYSQL_ADDITIONAL_SOCKET="O|text|MySQL Socket",
  ONEAPP_MYSQL_ADDITIONAL_CHARSET="O|text|MySQL Charset"
]
```

The user inputs will be grouped in a tab called BLOG with a group called CONF:

![sunstone_user_inputs_convention_blog](/images/sunstone_user_inputs_convention_blog.png)

Also, there will be a tab called MYSQL with two groups, CONFIG and ADDITIONAL:

![sunstone_user_inputs_convention_mysql_1](/images/sunstone_user_inputs_convention_mysql_1.png)

To set the user inputs in the ADDITIONAL group, activate the **Define additional parameters** option:

![sunstone_user_inputs_convention_mysql_2](/images/sunstone_user_inputs_convention_mysql_2.png)

#### Additional Data for User Inputs in Sunstone

In order to help the Sunstone user, the Virtual Machine templates can be extended with an attribute called USER_INPUTS_METADATA that will be adding some info to the APPS and GROUPS.

[See User Inputs Section Metadata in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-user-inputs-metadata" %}}).

{{< alert title="Note" type="info" >}}
The attribute `USER_INPUTS_METADATA` only will be used in Sunstone, not in other components of OpenNebula.{{< /alert >}}

So, if we use the previous Template and add the following information:

```default
USER_INPUTS_METADATA=[
  DESCRIPTION="This tab includes all the information about the blog section in this template.",
  NAME="BLOG",
  TITLE="Blog",
  TYPE="APP" ]
USER_INPUTS_METADATA=[
  NAME="MYSQL",
  TITLE="MySQL",
  TYPE="APP" ]
USER_INPUTS_METADATA=[
  DESCRIPTION="MySQL configuration parameters",
  NAME="CONFIG",
  TITLE="Configuration",
  TYPE="GROUP" ]
USER_INPUTS_METADATA=[
  DESCRIPTION="Additional MySQL parameters",
  NAME="ADDITIONAL",
  TITLE="Additional parameters",
  TYPE="GROUP" ]
```

Due to the elements with TYPE equal to APP, the BLOG tab has the title Blog and the MYSQL tab has the title MySQL (TITLE attribute). Also, due to these elements we have an info note in the Blog tab (DESCRIPTION attribute):

![sunstone_user_inputs_metadata_1](/images/sunstone_user_inputs_metadata_1.png)

Due to the elements with TYPE equal to GROUP, CONFIG group has the title Configuration and ADDITIONAL group has the title Additional parameters (TTILE attribute). Also, due to these elements Sunstone shows an info text in both groups (DESCRIPTION attribute):

![sunstone_user_inputs_metadata_2](/images/sunstone_user_inputs_metadata_2.png)

<a id="sched-actions-templ"></a>

### Schedule Actions

If you want to perform a pre-defined operation on a VM, you can use the Scheduled Actions. The selected operation will be performed on the VM at a specific time, e.g., _“Shut down the VM 5 hours after it started”_. You can also add a Scheduled action at [VM instantiation]({{% relref "./vm_instances#scheduled-actions-for-virtual-machines" %}}).

[See Schedule Actions Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-schedule-actions" %}}).

### Set a Cost

Each VM Template can have a cost per hour. This cost is set by the CPU unit and MEMORY MB, and disk MB. VMs with a cost will appear in the [showback reports]({{% relref "../../cloud_system_administration/multitenancy/showback#showback" %}}).

[See Showback Section in the VM Template reference]({{% relref "../../operation_references/configuration_references/template#template-showback-section" %}}).

<a id="cloud-view-features"></a>

### Enable End User Features

There are a few features of the [Cloud View]({{% relref "../../control_plane_configuration/graphical_user_interface/cloud_view#cloud-view" %}}) that will work if you configure the Template to make use of them:

- The Cloud View gives access to the VM’s VNC, but only if it is configured in the Template.
- End users can upload their public ssh key. This requires the VM guest to be [contextualized]({{% relref "#context-overview" %}}), and the Template must have the ssh contextualization enabled.

### Make the Images Non-Persistent

If a Template is meant to be consumed by end users, its Images should not be persistent. A persistent Image can only be used by one VM at a time. The next user will find the changes made by the previous user.

If the users need persistent storage, they can use the [“instantiate to persistent” functionality]({{% relref "../virtual_machines/vm_instances#vm-guide2-clone-vm" %}}).

### Prepare the Network Interfaces

End users can select the VM network interfaces when launching new VMs. You can create templates without any NIC or set the default ones. If the Template contains any NIC, users will still be able to remove them and select new ones.

When users add network interfaces, you need to define a default NIC model in case the VM guest needs a specific one (e.g., virtio for KVM). This can be done with the [NIC_DEFAULT]({{% relref "../../operation_references/configuration_references/template#nic-default-template" %}}) attribute, or through the Template wizard. Alternatively, you can change the default value for all VMs in the driver configuration file (see the [KVM one]({{% relref "../../operation_references/hypervisor_configuration/kvm_driver#kvmg-default-attributes" %}}) for example).

{{< alert title="Note" type="info" >}}
This networking customization can be forced to be disabled for any Template in the cloud view. Read more in the [Cloud View Customization documentation]({{% relref "../../../product/control_plane_configuration/graphical_user_interface/cloud_view.md" %}}).{{< /alert >}}

## Instantiating Templates

You can create a VM out of an existing VM Template using the `onetemplate instantiate` command . It accepts a Template ID or name, and creates a VM instance from the given Template. You can create more than one instance simultaneously with the `--multiple num_of_instances` option.

```default
$ onetemplate instantiate 6
VM ID: 0

$ onevm list
    ID USER     GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
     0 oneuser1 users    one-0        pend   0      0K                 00 00:00:16
```

### Overwrite VM Template Values

Users can overwrite some of the VM Template values, limited to those not listed in the restricted attributes. This allows users some safe, degree of customization for predefined templates.

Let’s say the administrator wants to provide base Templates that the users can customize, but with some restrictions. Having the following [restricted attributes in oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-restricted-attributes-configuration" %}}):

```none
VM_RESTRICTED_ATTR = "CPU"
VM_RESTRICTED_ATTR = "VPU"
VM_RESTRICTED_ATTR = "NIC"
```

And the following Template:

```none
CPU     = "1"
VCPU    = "1"
MEMORY  = "512"
DISK=[
  IMAGE = "BaseOS" ]
NIC=[
  NETWORK_ID = "0" ]
```

Users can instantiate it and customize anything except the CPU, VCPU, and NIC. To create a VM with different memory and disks:

```default
$ onetemplate instantiate 0 --memory 1G --disk "Ubuntu 16.04"
```

Also, a user cannot delete any element of a list that has any restricted attributes. By having the following [restricted attributes in oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-restricted-attributes-configuration" %}}):

```none
VM_RESTRICTED_ATTR = "DISK/TOTAL_BYTES_SEC"
```

And the following template:

```none
CPU     = "1"
VCPU    = "1"
MEMORY  = "512"
DISK=[
  IMAGE = "BaseOS"
  TOTAL_BYTES_SEC = 1 ]
DISK=[
  IMAGE = "BaseOS2" ]
NIC=[
  NETWORK_ID = "0" ]
```

A user can delete the second disk but cannot delete the first disk because it has a restricted attribute.

{{< alert title="Warning" type="warning" >}}
The provided attributes replace the existing ones. To add a new disk, the current one needs to be added also.{{< /alert >}}

```default
$ onetemplate instantiate 0 --disk BaseOS,"Ubuntu 16.04"
```

```default
$ cat /tmp/file
MEMORY = 512
COMMENT = "This is a bigger instance"

$ onetemplate instantiate 6 /tmp/file
VM ID: 1
```

### Deployment

The OpenNebula Scheduler will automatically deploy the VMs in one of the available Hosts, if they meet the requirements. The deployment can be forced by an administrator using the `onevm deploy` command.

Use `onevm terminate` to shutdown and delete a running VM.

Continue to the [Managing Virtual Machine Instances Guide]({{% relref "../virtual_machines/vm_instances#vm-guide-2" %}}) to learn more about the VM States and the available operations that can be performed.

<a id="instantiate-as-uid-gid"></a>

### Instantiating as Another User and/or Group

The `onetemplate instantiate` command accepts option `--as_uid` and `--as_gid` with the User ID or Group ID to define the owner or group for the new VM.

```default
$ onetemplate instantiate 6 --as_uid 2 --as_gid 1
VM ID: 0

$ onevm list
    ID USER      GROUP    NAME         STAT CPU     MEM        HOSTNAME        TIME
     0 test_user users    one-0        pend   0      0K                 00 00:00:16
```

## Managing Templates

Users can manage the VM Templates using the command `onetemplate`, or the graphical interface [Sunstone]({{% relref "../../../product/control_plane_configuration/graphical_user_interface/fireedge_sunstone.md" %}}). For each user, the actual list of templates available are determined by the ownership and permissions of the Templates.

### Adding and Deleting Templates

Using `onetemplate create`, users can create new Templates for private or shared use. The `onetemplate delete` command allows the owner -or the OpenNebula administrator- to delete it from the repository.

For instance, if the previous example Template is written in the vm-example.txt file:

```default
$ onetemplate create vm-example.txt
ID: 6
```

Via Sunstone, you can easily add Templates using the provided wizards and delete them by clicking on the delete button.

<a id="vm-template-clone"></a>

### Cloning Templates

You can also clone an existing Template with the `onetemplate clone` command:

```default
$ onetemplate clone 6 new_template
ID: 7
```

If you use the `onetemplate clone --recursive` option, OpenNebula will clone each one of the Images used in the Template Disks. These Images are made persistent and the cloned template DISK/IMAGE_ID attributes are replaced to point to the new Images.

### Updating a Template

It is possible to update a Template by using the `onetemplate update`. This will launch the editor defined in the variable `EDITOR` and let you edit the template.

```default
$ onetemplate update 3
```

### Restricted Attributes When Creating or Updating a Template

When a user creates or updates a Template, there are some restricted attributes that they cannot create or update. By having the following [restricted attributes in oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-restricted-attributes-configuration" %}}):

```none
VM_RESTRICTED_ATTR = "CPU"
VM_RESTRICTED_ATTR = "VPU"
VM_RESTRICTED_ATTR = "NIC"
```

And the following Template:

```none
CPU     = "1"
VCPU    = "1"
MEMORY  = "512"
DISK=[
  IMAGE = "BaseOS" ]
NIC=[
  NETWORK_ID = "0" ]
```

Users can create or update a Template and customize anything except the CPU, VCPU, and NIC.

Also, a user cannot delete any element of a list that has a restricted attributes. By having the following [restricted attributes in oned.conf]({{% relref "../../operation_references/opennebula_services_configuration/oned#oned-conf-restricted-attributes-configuration" %}}):

```none
VM_RESTRICTED_ATTR = "DISK/TOTAL_BYTES_SEC"
```

And the following Template:

```none
CPU     = "1"
VCPU    = "1"
MEMORY  = "512"
DISK=[
  IMAGE = "BaseOS"
  TOTAL_BYTES_SEC = 1 ]
DISK=[
  IMAGE = "BaseOS2" ]
NIC=[
  NETWORK_ID = "0" ]
```

A user can delete the second disk but cannot delete the first disk because it contains a restricted attribute.

### Sharing Templates with Other Users

The users can share their Templates with other users in their group or with all the users in OpenNebula. See the [Managing Permissions documentation]({{% relref "../../cloud_system_administration/multitenancy/chmod#chmod" %}}) for more information.

Let’s see a quick example. To share the Template 0 with users in the group, the **USE** right bit for **GROUP** must be set with the **chmod** command:

```default
$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : ---
OTHER          : ---

$ onetemplate chmod 0 640

$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : u--
OTHER          : ---
```

The following command allows users in the same group to **USE** and **MANAGE** the Template, and the rest of the users to **USE** it:

```default
$ onetemplate chmod 0 664

$ onetemplate show 0
...
PERMISSIONS
OWNER          : um-
GROUP          : um-
OTHER          : u--
```

The `onetemplate chmod --recursive` option will also perform the chmod action on each one of the Images used in the Template disks.

Sunstone offers an “alias” for `onetemplate chmod --recursive 640`, the share action:

![sunstone_template_share](/images/sunstone_template_share.png)

## Managing VM Templates with Sunstone

Sunstone exposes the above functionality in the Templates > VM Templates tab:

![sunstone_template_create](/images/sunstone_template_create.png)
