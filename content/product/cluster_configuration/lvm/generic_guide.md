---
title: "SAN/LVM: Generic setup"
linkTitle: "Generic SAN setup"
weight: "4"
---


This guide describes how to configure a generic SAN-backed LVM datastore for OpenNebula.

<a id="hosts-san-configuration"></a>

## Hosts SAN Configuration

The LUNs used by the LVM datastore must be exposed as block devices to all hypervisor hosts using the datastore. They can be accessed using iSCSI or Fibre Channel, with DM Multipath providing path redundancy when multiple paths to the storage are available.

The storage system, iSCSI targets or Fibre Channel fabric, and LUN mappings must be configured according to the storage vendor's documentation. The following sections describe the host-side configuration for iSCSI, Fibre Channel, and DM Multipath.

### iSCSI

When iSCSI is used to provide access to the SAN, each OpenNebula Host must have an iSCSI initiator configured and network connectivity to the storage targets.

Before configuring the iSCSI initiator, ensure that:

- The iSCSI target is configured on the storage system.
- The required LUNs are mapped to the corresponding iSCSI initiators.
- All OpenNebula Hosts that need access to the datastore can access the same LUNs.
- Network connectivity between the OpenNebula Hosts and the iSCSI target is available.
- For redundant configurations, multiple paths to the storage are  available.

####  Install the iSCSI initiator tools.

##### RHEL/AlmaLinux

On RHEL and AlmaLinux, the iSCSI initiator tools are provided by the `iscsi-initiator-utils` package:

```bash 
dnf install iscsi-initiator-utils sg3-utils
```

##### Debian/Ubuntu

On Debian and Ubuntu, the iSCSI initiator tools are provided by the `open-iscsi` package:

```bash
apt update
apt install open-iscsi sg3-utils
```

##### SUSE/openSUSE

On SUSE and openSUSE, install the iSCSI initiator tools with:

```bash
zypper install open-iscsi sg3_utils
```

#### Configure the iSCSI Initiator

Enable and start the `iscsid` service:

```bash
systemctl enable --now iscsid
```

The initiator IQN required when configuring LUN mapping or access control on the storage system.

The iSCSI initiator name assigned to the Host can be checked in `/etc/iscsi/initiatorname.iscsi`:

Discover the iSCSI targets available on the storage system:

```bash
iscsiadm -m discovery -t sendtargets -p <TARGET_IP>
```

The discovery operation creates node records for the targets returned by the storage system. The configured nodes can be listed with:

```bash
iscsiadm -m node
```

Log in to the required iSCSI target:

```bash
iscsiadm -m node -T <TARGET_IQN> -p <TARGET_IP> --login
```

If the same target is accessible through multiple storage interfaces, repeat the discovery and login process for each required path.

Verify the active iSCSI sessions:

```bash
iscsiadm -m session
```

Configure the target to be automatically connected after the Host reboots:

```bash
iscsiadm -m node -T <TARGET_IQN> -p <TARGET_IP> --op update -n node.startup -v automatic
```

After logging in to the target, the LUNs mapped to the initiator should be detected by the Linux SCSI subsystem and exposed as block devices.

Verify that the SAN LUNs are visible:

```bash
lsblk
```
The detected SCSI devices can also be inspected with:

```bash
lsscsi
```

If new LUNs are presented to an already connected Host, or the expected LUNs are not detected automatically, rescan the SCSI buses to discover new devices.

```bash
rescan-scsi-bus.sh
```

### Fibre Channel

When Fibre Channel is used to provide access to the SAN, each OpenNebula Host must have one or more Fibre Channel HBAs configured and connected to the SAN fabric.

Before configuring the operating system, ensure that:

- The Fibre Channel HBAs are detected by the operating system.
- The required zoning is configured on the Fibre Channel switches.
- The SAN LUNs are mapped to the WWPNs of the corresponding OpenNebula Hypervisors.
- All Hosts that need access to the datastore can access the same LUNs.
- For redundant configurations, multiple independent paths to the storage are available.

The exact zoning, LUN mapping, and HBA configuration depends on the SAN and Fibre Channel infrastructure. Refer to the storage and Fibre Channel switch vendor documentation for the recommended configuration.

Check the Fibre Channel HBA ports available on the Host:
```bash
ls /sys/class/fc_host/
```

The WWPNs of the Fibre Channel HBA ports can be obtained with:

```bash
cat /sys/class/fc_host/host*/port_name
```

Check the state of the Fibre Channel ports:

```bash
cat /sys/class/fc_host/host*/port_state
```

Verify that the SAN LUNs are visible:

```bash
lsblk
```

If `lsscsi` is installed, the discovered SCSI devices can also be verified with:

```bash
lsscsi
```

If new LUNs are presented to an already connected Host, or the expected LUNs are not detected automatically, rescan the SCSI buses to discover new devices.

```bash
rescan-scsi-bus.sh
```

### DM Multipath

DM Multipath provides path redundancy by combining multiple paths to the same SAN LUN into a single block device. It should be configured on all hypervisor hosts that have multiple paths to the storage.

The exact Multipath configuration depends on the storage system. Refer to the storage vendor's documentation for the recommended configuration and device-specific settings.

#### Install the Multipath tools.

##### RHEL/AlmaLinux

```bash
dnf install -y device-mapper-multipath
```

#### Debian/Ubuntu

```bash
apt update
apt install -y multipath-tools
```

##### SLES/openSUSE

```bash
zypper install -y multipath-tools
```

#### Configure DM Multipath

Enable and start the `multipathd` service:

```bash
systemctl enable --now multipathd
```

Create `/etc/multipath.conf` with the basic Multipath configuration:

```text
defaults {
    user_friendly_names yes
    find_multipaths yes
}
```

Restart `multipathd` to apply the configuration:

```bash
systemctl restart multipathd
```

Verify the detected Multipath devices and their paths:

```bash
multipath -ll
```

For example, a LUN available through multiple paths should be represented
by a single Multipath device:

```text
mpatha (360000000000000000000000000000001) dm-2 VENDOR,MODEL
size=1.0T features='1 queue_if_no_path' hwhandler='0' wp=rw
`-+- policy='service-time 0' prio=1 status=active
  |- 2:0:0:1 sdb 8:16 active ready running
  `- 3:0:0:1 sdc 8:32 active ready running
```

The resulting Multipath device is available under `/dev/mapper/`, for example `/dev/mapper/mpatha`. Use the Multipath device for the LVM configuration instead of an individual SCSI path such as `/dev/sdb` or `/dev/sdc`.

<a id="frontend-configuration"></a>

## Front-end Configuration

The Front-end needs access to the shared SAN storage to perform LVM operations. It can either access the SAN directly or use one or more hypervisor hosts as SAN proxies.

For direct access, the Front-end must be configured in the same way as the hypervisor hosts. For iSCSI storage, it must have connectivity to the iSCSI target and be configured as an iSCSI initiator. For Fibre Channel storage, it must have Fibre Channel connectivity to the SAN, and the required LUNs must be presented to the WWPNs of its Fibre Channel HBA ports.

When DM Multipath is used, it must also be configured on the Front-end so that the SAN LUNs are available as Multipath devices. No additional OpenNebula configuration is required for direct SAN access.

Example for illustration purposes:

```text
-------------
| Front-end | ---- /dev/mapper/mpath* ------+
-------------
                (iSCSI/FC + Multipath)       |
                                             |
                                             v
---------                                ---------------
| host2 | ---- /dev/mapper/mpath* -----> | SAN  Target |
---------       (iSCSI/FC + Multipath)   ---------------
                                             ^
                                             |
---------                                    |
| hostN | ---- /dev/mapper/mpath* -----------+
---------
                (iSCSI/FC + Multipath)
```

If direct SAN connectivity cannot be provided to the Front-end, set the `BRIDGE_LIST` attribute in both the System and Image datastores to specify one or more hypervisor hosts that will act as SAN proxies.

This configuration is particularly useful with Fibre Channel storage when the Front-end does not have an FC HBA or cannot be connected to the Fibre Channel fabric. The hosts specified in `BRIDGE_LIST` must have access to the SAN and be configured with the corresponding iSCSI or Fibre Channel connectivity and DM Multipath configuration.

## Troubleshooting

### LVM Devices File

**Problem:** LVM does not show my iSCSI/multipath devices (with e.g., `pvs`), although I can see them
with `multipath -ll` or `lsblk`.

**Possible solution:**

The LVM version in some operating systems or Linux distributions, by default,
doesn't scan the whole `/dev` directory for possible disks. Instead, you need to explicitly
**whitelist** them in `/etc/lvm/devices/system.devices`. You can check whether that's your case by
running:

```
lvmconfig --type full devices/use_devicesfile
```

If it returns `devices/use_devicesfile=1`, then the devices file is being used and enforced. In that
case, just add the device path to the whitelist and check again:

```
# echo /dev/mapper/mpatha >> /etc/lvm/devices/system.devices
# pvs
```

### Pool becomes full after live datastore migration

**Problem:** After a live datastore migration between two `fs_lvm_ssh` datastores with `LVM_THIN_ENABLE=yes` the disk now shows full:

```
# lvs
  LV             VG       Attr       LSize   Pool           Origin Data%  Meta%
  lv-one-11-0    vg-one-0 Vwi-aotz-k 256.00m lv-one-11-pool        100.00
  lv-one-11-pool vg-one-0 twi---tz-k 256.00m                       100.00 12.60
```

**Impact:** Everything should work as expected. The 100% in the `Data%` column only signifies that the thin volume is using the full space allocated by the pool. The filesystem is not affected and maintains the same space available as before. However, if that figure is used for monitoring, this should be taken into account to avoid false positives.

**Explaination:** The libvirt operation that implements live migration between datastores ([blockcopy](https://www.libvirt.org/manpages/virsh.html#blockcopy)) copied all blocks in the source LV, including the empty ones. This is due to the copy being made between raw block devices that don't expose information about empty blocks; LVM returns zero-filled blocks when reading from an unallocated part of the volume. For some operations like [migrate](https://www.libvirt.org/manpages/virsh.html#migrate), libvirt is able to detect blocks consisting of only zeroes and omit them by using the `--migrate-disks-detect-zeroes` option. Currently that option is not available on the `blockcopy` command.

**Mitigation:** If for any reason this situation unacceptable, an offline datastore migration should fix the issue (until libvirt supports the `--migrate-disks-detect-zeroes` option detailed above). A different mechanism is used for that case (`dd` with `conv=sparse`) which omits empty blocks from the copy.
