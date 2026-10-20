---
title: "Resolved Issues in 7.4.2 (EE)"
date: "2026-09-01"
---

A complete list of solved issues for 7.4.2 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/95).

## Backported Features

The following new features have been backported to 7.4.2:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

* Add a dedicated [FINISH frame to gracefully finalize interactive restore transfers]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}), eliminating the need to manually terminate the OneBEX writer process.
* Add an option to [cancel an ongoing Virtual Machine backup from Sunstone]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations#cancel-backup" %}}) [#8069](https://github.com/OpenNebula/one/issues/8069).
* Added a dedicated [FINISH frame to gracefully finalize interactive restore transfers]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}), eliminating the need to manually terminate the OneBEX writer process.
* Add support for Ceph VM backups through the [interactive backup integration]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}).
* Allow overriding `CLUSTER_IDS` when instantiating Virtual Network Templates [#8065](https://github.com/OpenNebula/one/issues/8065).
* Improve OneBEX performance by allowing concurrent reads when exposing disk data and remove OneBEX timeouts [#7961](https://github.com/OpenNebula/one/issues/7961).
* Add a [log warning when a driver's action queue is larger than its number of threads]({{% relref "product/operation_references/opennebula_services_configuration/oned.md#action-queue-warning" %}}).
* Add a [OneKS Application Catalog]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) of validated Helm-based applications that can be deployed on runing K8s Clusters and managed through Sunstone or the CLI, with application lifecycle monitoring and configurable installation options [#7302](https://github.com/OpenNebula/one/issues/7302).
* Enable [OneDRS balancing by storage space]({{% relref "product/cloud_system_administration/scheduler/drs#load-balancing-objectives" %}}) through the `STORAGE_WEIGHT` Cluster attribute, configurable in Sunstone. Administrators can combine datastore space utilization with other balancing objectives, such as disk I/O, to optimize storage distribution across the Cluster [#7930](https://github.com/OpenNebula/one/issues/7930).
* Allow [attaching and detaching disks on Virtual Machines in the `HOLD` state]({{% relref "product/virtual_machines_operation/virtual_machines/vm_instances.md#disk-hotplugging" %}}).
* Add [automatic bridge management for switchdev SR-IOV networks]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#switchdev-mode" %}}) through `BRIDGE="switchdev"` with the `ovswitch` driver. OpenNebula creates or reuses a dedicated Open vSwitch bridge for each parent Physical Function (PF) and connects the PF and its VF representors, allowing one Virtual Network to serve VFs from multiple PFs without separate per-PF network definitions [#7960](https://github.com/OpenNebula/one/issues/7960).
* Add the OneSwap [`--machine` and `--cpu-features`]({{% relref "software/migration_from_vmware/oneswap.md#customizing-the-created-vm-template" %}}) options to set the KVM machine type and CPU model features for a migration profile. Configure them in `/etc/one/oneswap.yaml` or on the command line; `--cpu-features` requires `--cpu-model` [#8112](https://github.com/OpenNebula/one/issues/8112).

* Add [SR-IOV PF/VF relationship monitoring]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts.md#host-pci-devices" %}}) and [VF selection by parent PF]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#selecting-virtual-functions-by-physical-function" %}}) through `PF_IFNAME` or `PF_ADDRESS`. Select the same PF to keep VFs together (affinity), or different PFs to spread them (anti-affinity). Monitoring also reports passthrough eligibility and the network PF e-switch mode when available [#7671](https://github.com/OpenNebula/one/issues/7671), [#7619](https://github.com/OpenNebula/one/issues/7619).
* Add the [`SSH_PUBLIC_KEY_EXCLUSIVE`]({{% relref "product/operation_references/configuration_references/template#template-context" %}}) context attribute to the Linux contextualization packages. The keys from `SSH_PUBLIC_KEY` are now kept in a managed block of the user `authorized_keys` file, which is synchronized with the context every time the VM is contextualized, so keys removed from the context are also removed from the guest. With `SSH_PUBLIC_KEY_EXCLUSIVE=YES` any key outside of the managed block is removed as well [one-apps#387](https://github.com/OpenNebula/one-apps/issues/387).

## Resolved Issues

The following issues have been solved in 7.4.2:

* Fix potential disk data loss by rejecting live datastore migration of VMs with qcow2 disks containing internal snapshots [#8092](https://github.com/OpenNebula/one/issues/8092).
* Fix update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416).
* Fix VM template instantiation to allow precise memory values to be entered directly when memory modification is configured as a range [#7426](https://github.com/OpenNebula/one/issues/7426).
* Fix Restic Datastore - the password filed is not masking the password [#7444](https://github.com/OpenNebula/one/issues/7444).
* Fix missing theme colors in Sunstone quota panels and improve quota usage readability with per-metric values and progress bars [#6869](https://github.com/OpenNebula/one/issues/6869).
* Fix update VM Template dialog fails to open on FireEdge Sunstone if the user doesn't have IMAGE permissions [#6994](https://github.com/OpenNebula/one/issues/6994).
* Fix unable to flush offline host in Sunstone [#7407](https://github.com/OpenNebula/one/issues/7407).
* Fix security groups assignment when attaching a NIC in Sunstone [#7569](https://github.com/OpenNebula/one/issues/7569).
* Fix missing service template instantiation dialog [#8037](https://github.com/OpenNebula/one/issues/8037).
* Fix missing VRouter NIC attach/detach action [#7708](https://github.com/OpenNebula/one/issues/7708).
* Fix VNC console reliability for LXC virtual machines by increasing Guacamole tunnel timeouts and preventing premature disconnections due to svncterm inactivity [#8095](https://github.com/OpenNebula/one/issues/8095).
* Fix SPICE support in Sunstone [#7667](https://github.com/OpenNebula/one/issues/7667).
* Fix service template updates in Sunstone [#7193](https://github.com/OpenNebula/one/issues/7193).
* Fix security groups assignment when attaching a NIC in Sunstone [#7569](https://github.com/OpenNebula/one/issues/7569).
* Fix Zendesk support ticket comments by preventing replies to closed tickets and displaying errors when comment delivery fails [#7280](https://github.com/OpenNebula/one/issues/7280).
* Fix Disable restricted capacity modification fields for non-admins [#7516](https://github.com/OpenNebula/one/issues/7516).
* Fix Force option missing when removing address range in Sunstone [#8070](https://github.com/OpenNebula/one/issues/8070).
* Fix FireEdge failing to connect when VNC `LISTEN` is set to a DNS name [#6976](https://github.com/OpenNebula/one/issues/6976).
* Fix OneBEX interactive exports when backup datastores use non-default paths by passing the backup directory in the export request [#8093](https://github.com/OpenNebula/one/issues/8093).
* Fix [FireEdge] Service Template chmod fails silently [#8096](https://github.com/OpenNebula/one/issues/8096).
* Fix usage of HTTP proxy credentials for marketplace monitoring [#8043](https://github.com/OpenNebula/one/issues/8043).
* Fix default `VCPU` to 1 when CPU hotplug (`VCPU_MAX`) is defined without `VCPU` [#7434](https://github.com/OpenNebula/one/issues/7434).
* Fix duplicate `SECURITY_GROUPS` attributes in Virtual Network templates on template update [#7435](https://github.com/OpenNebula/one/issues/7435).
* Fix `onetemplate instantiate` erroneously requiring Template `CREATE` permissions [#7020](https://github.com/OpenNebula/one/issues/7020).
* Fix truncation of snapshot and backup IDs for CLI `oneimage show` and `onevm show` commands [#8108](https://github.com/OpenNebula/one/issues/8108).
* Fix onezone serversync to synchronize OneForm, OneKS, and FireEdge configuration files across Front-end hosts and restart the corresponding services when those files change [#8039](https://github.com/OpenNebula/one/issues/8039).
* Fix OneSwap conversion of Windows guests using CompactOS/WOF-compressed NTFS system files [#7342](https://github.com/OpenNebula/one/issues/7342).
* Fix OneSwap context injection running the RHEL-specific `subscription-manager` command on RHEL-compatible distributions [#8111](https://github.com/OpenNebula/one/issues/8111).
* Fix OneSwap Delta migration failures caused by empty VMware CD-ROM devices being incorrectly detected as virtual disks [#8170](https://github.com/OpenNebula/one/issues/8170).
* Fix search field missing in Service Template Edit screen [#8097](https://github.com/OpenNebula/one/issues/8097).
* Fix `oneimage` and `onevm` commands to not truncate IDs greater than 999 [#8108](https://github.com/OpenNebula/one/issues/8108)
* Fix missing network security risk warnings in documentation for interactive backups and restores [#8061](https://github.com/OpenNebula/one/issues/8061).
* Fix multiple security groups issues [#8126](https://github.com/OpenNebula/one/issues/8126).
* Fix VM Template custom attributes not being removed when edited in FireEdge. [#8098](https://github.com/OpenNebula/one/issues/8098).
* Fix LDAP authentication errors in FireEdge when the LDAP server is unreachable. [#6813](https://github.com/OpenNebula/one/issues/6813).
* Fix NetApp Datastore values in creation tab [#8035](https://github.com/OpenNebula/one/issues/8035).
* Fix missing CPU Model field in VM Update Configuration [#8034](https://github.com/OpenNebula/one/issues/8034).
* Fix missing `IOTHREADS` in VM `OS & CPU Features` configuration tab [#7585](https://github.com/OpenNebula/one/issues/7585).
* Fix OneGate service role scaling from inside VMs, which could fail due to the request body being consumed before processing [#7954](https://github.com/OpenNebula/one/issues/7954).
* Fix DRS cluster workload optimization attempting to migrate VMs in `UNDEPLOYED` or `STOPPED` states [#8073](https://github.com/OpenNebula/one/issues/8073).
* Fix an issue preventing long attribute values from being expanded in FireEdge [#8131](https://github.com/OpenNebula/one/issues/8131).
* Fix multi-line formatting in VM descriptions [#8130](https://github.com/OpenNebula/one/issues/8130).
* Fix oned crashing when a KVM host reports a NUMA node without cores [#8133](https://github.com/OpenNebula/one/issues/8133).

---

## Updating Sunstone Configuration Files

After upgrading to 7.4.2, check the following settings to enable the new Sunstone functionality in the intended views. All paths below are relative to `/etc/one/fireedge/` on the OpenNebula Front-end Host.

Merge these settings into the existing YAML sections, preserving other settings and actions. Do not create duplicate `info-tabs` or `filters` keys.

### Enable VM backup cancellation in Sunstone [#8069](https://github.com/OpenNebula/one/issues/8069)

In `sunstone/views/admin/vm-tab.yaml`, `sunstone/views/groupadmin/vm-tab.yaml` and `sunstone/views/user/vm-tab.yaml`, add `backup-cancel: true` under `info-tabs.backup.actions`:

```yaml
info-tabs:
  backup:
    enabled: true
    actions:
      backup-cancel: true
```

The `admin` view already has an `actions` section for backups; add the new entry alongside its existing actions. In the `groupadmin` and `user` views, create the `actions` section under `backup` if it does not already exist. Restart FireEdge for the configuration changes to take effect.

### Update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416)

In `sunstone/tab-manifest.yaml`, locate the entry with title: Networks. Within its `routes` section, after the following entry:

```yaml
    - title: Create Virtual Network
      path: /virtual-network/create
      Component: CreateVirtualNetwork
```

Add the following content:

```yaml
    - title: Update Virtual Network Template
      path: /network-template/update
      Component: CreateVnTemplate
```

Also, after the entry:

```yaml
    - title: Create Security Group
      path: /security-group/create
      Component: CreateSecurityGroup
```

Add the following content

```yaml
    - title: Update Security Group
      path: /security-group/update
      Component: CreateSecurityGroup
```

In `sunstone/tab-manifest.yaml`, locate the entry with title: System. Within its `routes` section, after the following entry:

```yaml
    - title: Groups
      path: /group
      sidebar: true
      icon: Group
      Component: Groups
```

Add the following content:

```yaml
    - title: Update Group
      path: /group/update
      Component: CreateGroup
```

### Expose virtual router NIC attach/detach actions [#7708](https://github.com/OpenNebula/one/issues/7708)

In `sunstone/views/*/vrouter-tab.yaml`, as part of `nics` attributes after the entry:

```yaml
   nics:
    enabled: true
```

Add the following content:

```yaml
    actions:
      nic-attach: true
      nic-detach: true
```

### Add the SPICE console [#7667](https://github.com/OpenNebula/one/issues/7667).

Add the file `sunstone/tabs/81-spice-tab.yaml`

```yaml
    - title: SPICE
      path: /spice/:id
      sidebar: false
      Component: Spice
```

In `sunstone/views/admin/vm-tab.yaml`, `sunstone/views/cloud/vm-tab.yaml`, `sunstone/views/groupadmin/vm-tab.yaml`, `sunstone/views/admin/user-tab.yaml`, in the `actions` section add the following content:

```yaml
    - spice: true
```

### Service template instantiate missing selection dialog [#8037](https://github.com/OpenNebula/one/issues/8037)

In `sunstone/tab-manifest.yaml`, locate the entry with title: Instances. Under Instances entry, locate the entry with title: Instantiate Service Template and replace the content:

```yaml
    - title: Instantiate Service Template
      path: /service/instantiate/
      Component: InstantiateServiceTemplate
```

With the following content:

```yaml
    - title: Instantiate Service Template
      path: /service/instantiate/
      Component: CreateService
```