---
title: "Resolved Issues in 7.4.2 (EE)"
date: "2026-11-01"
---

A complete list of solved issues for 7.4.2 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/95).

## Backported Features

The following new features have been backported to 7.4.2:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

* Add support for Ceph VM backups through the [interactive backup integration]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}).

## Resolved Issues

The following issues have been solved in 7.4.2:

* Fix update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416).
* Fix VM template instantiation to allow precise memory values to be entered directly when memory modification is configured as a range [#7426](https://github.com/OpenNebula/one/issues/7426).
* Fix Restic Datastore - the password filed is not masking the password [#7444](https://github.com/OpenNebula/one/issues/7444).
* Fix missing theme colors in Sunstone quota panels and improve quota usage readability with per-metric values and progress bars [#6869](https://github.com/OpenNebula/one/issues/6869).
* Fix unable to flush offline host in Sunstone [#7407](https://github.com/OpenNebula/one/issues/7407).
- Fix security groups assignment when attaching a NIC in Sunstone [#7569](https://github.com/OpenNebula/one/issues/7569).
* Fix missing VRouter NIC attach/detach action [#7708](https://github.com/OpenNebula/one/issues/7708).
* Fix VNC console reliability for LXC virtual machines by increasing Guacamole tunnel timeouts and preventing premature disconnections due to svncterm inactivity [#8095](https://github.com/OpenNebula/one/issues/8095).
* Fix SPICE support in Sunstone [#7667](https://github.com/OpenNebula/one/issues/7667).
* Fix service template updates in Sunstone [#7193](https://github.com/OpenNebula/one/issues/7193).
* Fix security groups assignment when attaching a NIC in Sunstone [#7569](https://github.com/OpenNebula/one/issues/7569).
* Fix Zendesk support ticket comments by preventing replies to closed tickets and displaying errors when comment delivery fails [#7280](https://github.com/OpenNebula/one/issues/7280).
* Fix OneBEX interactive exports when backup datastores use non-default paths by passing the backup directory in the export request [#8093](https://github.com/OpenNebula/one/issues/8093).
* Fix [FireEdge] Service Template chmod fails silently [#8096](https://github.com/OpenNebula/one/issues/8096).
* Fix usage of HTTP proxy credentials for marketplace monitoring [#8043](https://github.com/OpenNebula/one/issues/8043).
* Fix onezone serversync to synchronize OneForm, OneKS, and FireEdge configuration files across Front-end hosts and restart the corresponding services when those files change [#8039](https://github.com/OpenNebula/one/issues/8039).
* Fix OneSwap conversion of Windows guests using CompactOS/WOF-compressed NTFS system files [#7342](https://github.com/OpenNebula/one/issues/7342).
* Fix OneSwap context injection running the RHEL-specific `subscription-manager` command on RHEL-compatible distributions [#8111](https://github.com/OpenNebula/one/issues/8111).
* Fix search field missing in Service Template Edit screen [#8097](https://github.com/OpenNebula/one/issues/8097).

---

## Updating Sunstone Configuration Files

After upgrading to 7.4.2, check the following settings to enable the new Sunstone functionality in the intended views. All paths below are relative to `/etc/one/fireedge/` on the OpenNebula Front-end Host.

Merge these settings into the existing YAML sections, preserving other settings and actions. Do not create duplicate `info-tabs` or `filters` keys.

### Update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416)

In `sunstone/tabs/40-networks-tab.yaml`, as part of `routes` attributes after the entry:

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

In `sunstone/tabs/60-systems-tab.yaml`, as part of `routes` attributes after the entry:

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
