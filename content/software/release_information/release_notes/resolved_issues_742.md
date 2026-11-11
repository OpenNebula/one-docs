---
title: "Resolved Issues in 7.4.2 (EE)"
date: "2026-09-01"
---

A complete list of solved issues for 7.4.2 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/95).

## Upgrading to 7.4.2

{{< alert title="Important" type="warning" >}}
OpenNebula 7.4.2 includes changes to the stock configuration files and ships `onecfg` migrators from 7.4.0 to 7.4.2 and 7.4.1 to 7.4.2. After upgrading the packages, you **must run** `onecfg upgrade` on the Front-end command line to migrate your configuration, as described in the [upgrade guide]({{% relref "software/upgrade_process/upgrade_guide/upgrading_single/#upgrading-from-74x" %}}).

You may also need to update the Sunstone configuration files to expose the Sunstone features backported to 7.4.2 and 7.4.1, please see the [configuration instructions]({{% relref "software/release_information/release_notes/resolved_issues_742.md#updating-sunstone-configuration-files" %}}) at the end of this document.
{{< /alert >}}

## Backported Features

The following new features have been backported to 7.4.2:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

* Add a dedicated [FINISH frame to gracefully finalize interactive restore transfers]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#restoring-interactive-backups" %}}), eliminating the need to manually terminate the OneBEX writer process [#8064](https://github.com/OpenNebula/one/issues/8064).
* Add an option to [cancel an ongoing Virtual Machine backup from Sunstone]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations#cancel-backup" %}}) [#8069](https://github.com/OpenNebula/one/issues/8069).
* Add [Port Mirroring]({{% relref "product/cluster_configuration/networking_system/port_mirroring.md" %}}) for Virtual Networks using the `ovswitch` and `ovswitch_vxlan` drivers, supporting RSPAN, GRE, and ERSPAN types II and III, traffic direction selection, and optional source VLAN filters. Manage mirrors and source interfaces through the API, `onevnet mirror-*` commands, or [Sunstone]({{% relref "product/cluster_configuration/networking_system/manage_vnets.md#port-mirroring" %}}). Driver updates are asynchronous and capture is reconstructed after VM migration. Enable the Sunstone tab and form routes using the configuration [instructions below](#enable-port-mirroring-in-sunstone-8149) [#7638](https://github.com/OpenNebula/one/issues/7638), [#6783](https://github.com/OpenNebula/one/issues/6783).
* Improve selection controls in Sunstone forms with icons and descriptions, using Card Buttons, Button Groups, radio buttons, and dropdowns according to the type of choice [#8216](https://github.com/OpenNebula/one/issues/8216).
* Add [SPICE console support]({{% relref "product/operation_references/hypervisor_configuration/kvm_driver.md#graphics" %}}) in Sunstone for KVM Virtual Machines [#7667](https://github.com/OpenNebula/one/issues/7667).
* Add support for Ceph VM backups through the [interactive backup integration]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}) [#7900](https://github.com/OpenNebula/one/issues/7900).
* Allow oneadmin users and members of the oneadmin group to override `CLUSTER_IDS` when instantiating Virtual Network Templates [#8065](https://github.com/OpenNebula/one/issues/8065).
* Improve OneBEX performance by allowing concurrent reads when exposing disk data and removing the idle-session and overall export timeouts [#7961](https://github.com/OpenNebula/one/issues/7961).
* Add a [log warning when a driver's action queue is larger than its number of threads]({{% relref "product/operation_references/opennebula_services_configuration/oned.md#action-queue-warning" %}}) [#7079](https://github.com/OpenNebula/one/issues/7079).
* Add a [OneKS Application Catalog]({{% relref "platform_services/oneks/management/k8s_cluster_lifecycle_management/#managing-applications" %}}) of validated Helm-based applications that can be deployed on running K8s Clusters and managed through Sunstone or the CLI, with application lifecycle monitoring and configurable installation options [#7302](https://github.com/OpenNebula/one/issues/7302).
* Enable [OneDRS balancing by storage space]({{% relref "product/cloud_system_administration/scheduler/drs#load-balancing-objectives" %}}) through the `STORAGE_WEIGHT` Cluster attribute, configurable in Sunstone. Administrators can combine datastore space utilization with other balancing objectives, such as disk I/O, to optimize storage distribution across the Cluster [#7930](https://github.com/OpenNebula/one/issues/7930).
* Add [automatic bridge management for switchdev SR-IOV networks]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#switchdev-mode" %}}) through `BRIDGE="switchdev"` with the `ovswitch` driver. OpenNebula creates or reuses a dedicated Open vSwitch bridge for each parent Physical Function (PF) and connects the PF and its VF representors, allowing one Virtual Network to serve VFs from multiple PFs without separate per-PF network definitions [#7960](https://github.com/OpenNebula/one/issues/7960).
* Add the OneSwap [`--machine` and `--cpu-features`]({{% relref "software/migration_from_vmware/oneswap.md#customizing-the-created-vm-template" %}}) options to set the KVM machine type and CPU model features for a migration profile. Configure them in `/etc/one/oneswap.yaml` or on the command line; `--cpu-features` requires a CPU model set with `--cpu-model` or `:cpu_model` [#8112](https://github.com/OpenNebula/one/issues/8112).
* Add support for VDDK transport in OneSwap delta migrations, allowing `--delta` and `--vddk` to be used together. vSAN-backed VMs are not supported [#7903](https://github.com/OpenNebula/one/issues/7903).
* Add [SR-IOV PF/VF relationship monitoring]({{% relref "product/cluster_configuration/hosts_and_clusters/hosts.md#host-pci-devices" %}}) and [VF selection by parent PF]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#selecting-virtual-functions-by-physical-function" %}}) through `PF_IFNAME` or `PF_ADDRESS`. Select the same PF to keep VFs together (affinity), or different PFs to spread them (anti-affinity). Monitoring also reports passthrough eligibility and the network PF e-switch mode when available [#7671](https://github.com/OpenNebula/one/issues/7671), [#7619](https://github.com/OpenNebula/one/issues/7619), [#7973](https://github.com/OpenNebula/one/issues/7973).
* Add the [`SSH_PUBLIC_KEY_EXCLUSIVE`]({{% relref "product/operation_references/configuration_references/template#template-context" %}}) context attribute to the Linux contextualization packages. The keys from `SSH_PUBLIC_KEY` are now kept in a managed block of the user `authorized_keys` file, which is synchronized with the context every time the VM is contextualized, so keys removed from the context are also removed from the guest. With `SSH_PUBLIC_KEY_EXCLUSIVE=YES` any key outside of the managed block is removed as well [one-apps#387](https://github.com/OpenNebula/one-apps/issues/387).
* Improve OneBEX NBD and RBD exporters to detect and report zero-filled and sparse (hole) regions during full backups [#8230](https://github.com/OpenNebula/one/issues/8230).
* Improve OneForm provisioning with persistent Ansible and Terraform workflows, [recovery after service restarts]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations.md#recovering-failed-provisions" %}}), and [operation cancellation]({{% relref "product/cluster_provisioning/cluster_operations/provision_operations.md#cancelling-provision-operations" %}}) [#7579](https://github.com/OpenNebula/one/issues/7579), [#7580](https://github.com/OpenNebula/one/issues/7580).
* Display available [GPU utilization, memory bandwidth utilization, and power metrics]({{% relref "product/cloud_system_administration/resource_monitoring/metrics.md#virtual-machine" %}}) in the Sunstone VM PCI tab [#7282](https://github.com/OpenNebula/one/issues/7282).
* Apply the [requested NIC `MTU`]({{% relref "product/cluster_configuration/pci_passthrough_sriov/network_interfaces.md#eswitch-modes" %}}) to SR-IOV Physical Functions and, in switchdev mode, to VF representors, preserving the highest MTU requested on a shared PF [#7926](https://github.com/OpenNebula/one/issues/7926).

## Resolved Issues

The following issues have been solved in 7.4.2:

* Fix guest data loss during live migration with `lvm`, or with `fs_lvm_ssh` and `LVM_THIN_ENABLE=YES`. These migrations now pause the guest throughout memory transfer and storage handover, which can increase application interruption [#8163](https://github.com/OpenNebula/one/issues/8163).
* Fix potential disk data loss by rejecting live datastore migration of VMs with qcow2 disks containing internal snapshots [#8092](https://github.com/OpenNebula/one/issues/8092).
* Fix update any item without having permissions to create it on yaml FireEdge views [#6416](https://github.com/OpenNebula/one/issues/6416).
* Fix VM template instantiation to allow precise memory values to be entered directly when memory modification is configured as a range [#7426](https://github.com/OpenNebula/one/issues/7426).
* Fix Restic Datastore - the password field is not masking the password [#7444](https://github.com/OpenNebula/one/issues/7444).
* Fix missing theme colors in Sunstone quota panels and improve quota usage readability with per-metric values and progress bars [#6869](https://github.com/OpenNebula/one/issues/6869).
* Fix update VM Template dialog fails to open on FireEdge Sunstone if the user doesn't have IMAGE permissions [#6994](https://github.com/OpenNebula/one/issues/6994).
* Fix unable to flush offline Host in Sunstone [#7407](https://github.com/OpenNebula/one/issues/7407).
* Fix security groups assignment when attaching a NIC in Sunstone [#7569](https://github.com/OpenNebula/one/issues/7569).
* Fix missing service template instantiation dialog [#8037](https://github.com/OpenNebula/one/issues/8037).
* Fix missing VRouter NIC attach/detach action [#7708](https://github.com/OpenNebula/one/issues/7708).
* Fix VNC console reliability for LXC virtual machines by increasing Guacamole tunnel timeouts and preventing premature disconnections due to svncterm inactivity [#8095](https://github.com/OpenNebula/one/issues/8095).
* Fix service template updates in Sunstone [#7193](https://github.com/OpenNebula/one/issues/7193).
* Fix Zendesk support ticket comments by preventing replies to closed tickets and displaying errors when comment delivery fails [#7280](https://github.com/OpenNebula/one/issues/7280).
* Fix Disable restricted capacity modification fields for non-admins [#7516](https://github.com/OpenNebula/one/issues/7516).
* Fix Force option missing when removing address range in Sunstone [#8070](https://github.com/OpenNebula/one/issues/8070).
* Fix EVC options filtering in Sunstone [#8205](https://github.com/OpenNebula/one/issues/8205).
* Fix FireEdge failing to connect when VNC `LISTEN` is set to a DNS name [#6976](https://github.com/OpenNebula/one/issues/6976).
* Fix OneBEX interactive exports when backup datastores use non-default paths by passing the backup directory in the export request [#8093](https://github.com/OpenNebula/one/issues/8093).
* Fix [FireEdge] Service Template chmod fails silently [#8096](https://github.com/OpenNebula/one/issues/8096).
* Fix usage of HTTP proxy credentials for marketplace monitoring [#8043](https://github.com/OpenNebula/one/issues/8043).
* Fix default `VCPU` to 1 when CPU hotplug (`VCPU_MAX`) is defined without `VCPU` [#7434](https://github.com/OpenNebula/one/issues/7434).
* Fix duplicate `SECURITY_GROUPS` attributes in Virtual Network templates on template update [#7435](https://github.com/OpenNebula/one/issues/7435).
* Fix `onetemplate instantiate` erroneously requiring Template `CREATE` permissions [#7020](https://github.com/OpenNebula/one/issues/7020).
* Fix truncation of snapshot and backup IDs for CLI `oneimage show` and `onevm show` commands [#8108](https://github.com/OpenNebula/one/issues/8108).
* Fix onezone serversync to synchronize OneForm, OneKS, and FireEdge configuration files across Front-end Hosts and restart the corresponding services when those files change [#8039](https://github.com/OpenNebula/one/issues/8039).
* Fix OneSwap conversion of Windows guests using CompactOS/WOF-compressed NTFS system files [#7342](https://github.com/OpenNebula/one/issues/7342).
* Fix OneSwap context injection running the RHEL-specific `subscription-manager` command on RHEL-compatible distributions [#8111](https://github.com/OpenNebula/one/issues/8111).
* Fix issues with FireEdge in federated environments, including zone switching, stale resource views, and VNC/Guacamole console access across zones. [#7310](https://github.com/OpenNebula/one/issues/7310).
* Fix OneSwap Delta migration failures caused by empty VMware CD-ROM devices being incorrectly detected as virtual disks [#8170](https://github.com/OpenNebula/one/issues/8170).
* Fix search field missing in Service Template Edit screen [#8097](https://github.com/OpenNebula/one/issues/8097).
* Fix missing network security risk warnings in documentation for interactive backups and restores [#8061](https://github.com/OpenNebula/one/issues/8061).
* Fix multiple security groups issues [#8126](https://github.com/OpenNebula/one/issues/8126).
* Fix VM Template custom attributes not being removed when edited in FireEdge. [#8098](https://github.com/OpenNebula/one/issues/8098).
* Fix support for creating VNETs with Dummy/Custom VN_MAD in FireEdge. [#7715](https://github.com/OpenNebula/one/issues/7715).
* Fix misleading LDAP login errors in FireEdge by reporting when all LDAP servers selected for the user are unreachable [#6813](https://github.com/OpenNebula/one/issues/6813).
* Fix NetApp Datastore values in creation tab [#8035](https://github.com/OpenNebula/one/issues/8035).
* Fix missing CPU Model field in VM Update Configuration [#8034](https://github.com/OpenNebula/one/issues/8034).
* Fix missing `IOTHREADS` in VM `OS & CPU Features` configuration tab [#7585](https://github.com/OpenNebula/one/issues/7585).
* Fix OneGate service role scaling from inside VMs, which could fail due to the request body being consumed before processing [#7954](https://github.com/OpenNebula/one/issues/7954).
* Fix DRS Cluster workload optimization attempting to migrate VMs in `UNDEPLOYED` or `STOPPED` states [#8073](https://github.com/OpenNebula/one/issues/8073).
* Fix OneKS/Sunstone: "Cluster: Unknown (0)" for every worker [#8189](https://github.com/OpenNebula/one/issues/8189).
* Fix an issue preventing long attribute values from being expanded in FireEdge [#8131](https://github.com/OpenNebula/one/issues/8131).
* Fix multi-line formatting in VM descriptions [#8130](https://github.com/OpenNebula/one/issues/8130).
* Fix oned crashing when a KVM Host reports a NUMA node without cores [#8133](https://github.com/OpenNebula/one/issues/8133).
* Fix reserved VNC ports leaking when `onevm updateconf` removes `GRAPHICS` [#8201](https://github.com/OpenNebula/one/issues/8201).
* Fix Veeam checkpoint deletion by marking deleted checkpoints invalid and rejecting incremental backups based on invalid or outdated checkpoints [#8062](https://github.com/OpenNebula/one/issues/8062).
* Fix the “Allocated CPU” slider on the Hosts [#8208](https://github.com/OpenNebula/one/issues/8208).
* Fix OneKS deployment failures when using an image datastore other than the default datastore [#8081](https://github.com/OpenNebula/one/issues/8081).
* Fix OneKS deployment failures when using virtual networks not owned by the user [#8128](https://github.com/OpenNebula/one/issues/8128).
* Fix failed LVM backups leaving snapshots active, and clean up obsolete snapshots from previous failed backups [#8226](https://github.com/OpenNebula/one/issues/8226).
* Fix Veeam backups failing after a persistent LVM VM disk is resized because oVirtAPI reports its outdated image size [#8203](https://github.com/OpenNebula/one/issues/8203).
* Fix invalid `host-passthrough` option appearing in the Sunstone machine type selector [#8018](https://github.com/OpenNebula/one/issues/8018).
* Fix incompatible target system datastores being offered in the Sunstone VM live migration dialog by filtering them to match the source `TM_MAD` [#8164](https://github.com/OpenNebula/one/issues/8164).
* Fix `VM_EXEC` reaper blocked by stale PID file [#8232](https://github.com/OpenNebula/one/issues/8232).
* Fix loss of VM firewall rules when a Security Group update is immediately followed by a commit [#8143](https://github.com/OpenNebula/one/issues/8143).
* Fix OneDRS optimization failing with `PulpError` when VM monitoring data contains missing usage values [#8224](https://github.com/OpenNebula/one/issues/8224).
* Fix incorrect quota limit errors when quota entries omit metrics, preventing powered-off VMs from resuming when `RUNNING_VMS` is missing [#8183](https://github.com/OpenNebula/one/issues/8183).
* Fix potential incorrect user and group quota usage after a failed VM migration between Clusters, restoring source Cluster usage and releasing target cluster usage [#8191](https://github.com/OpenNebula/one/issues/8191).
* Fix S3 Marketplace image imports ignoring the configured `READ_LENGTH` chunk size [#8194](https://github.com/OpenNebula/one/issues/8194).
* Fix CPU monitoring errors when system CPU counters do not advance and negative CPU usage when a monitored process exits during sampling [#8195](https://github.com/OpenNebula/one/issues/8195).
* Fix removal of user-defined `ETHx_*` context variables when detaching a NIC or NIC alias with `NETWORK` not set to `YES`, and allow updating these variables with `onevm updateconf` [#8214](https://github.com/OpenNebula/one/issues/8214).
* Fix Veeam VM backups ignoring the selected disks and backing up all VM disks [#8236](https://github.com/OpenNebula/one/issues/8236).
* Fix interactive VM backups failing when an attached disk excluded from the backup does not support interactive backups [#8249](https://github.com/OpenNebula/one/issues/8249).
* Fix Unable to instantiate VM if SVM SnapMirror is enabled [#7402](https://github.com/OpenNebula/one/issues/7402).
* Fix FireEdge DNS resolution on IPv6-only systems by preserving the resolver result order instead of forcing IPv4 first [#7557](https://github.com/OpenNebula/one/issues/7557).
* Fix `oneform sync` leaving stale resources and symbolic links after drivers are removed [#7591](https://github.com/OpenNebula/one/issues/7591).
* Fix OneForm provisioning using Community Edition repositories for Enterprise Edition deployments [#7728](https://github.com/OpenNebula/one/issues/7728).
* Fix FireEdge remote authentication failing when the browser sends an expired `FireedgeToken` cookie [#7741](https://github.com/OpenNebula/one/issues/7741).
* Fix Prometheus exporter permissions by running the LVM exporter as `oneadmin` and allowing the Open vSwitch exporter to access privileged OVS commands [#7759](https://github.com/OpenNebula/one/issues/7759).
* Fix Veeam worker VM discovery when multiple network interfaces are attached [#8025](https://github.com/OpenNebula/one/issues/8025).
* Fix excessive memory consumption during Veeam worker deployment by streaming image uploads to OneBEX [#8078](https://github.com/OpenNebula/one/issues/8078).
* Fix OneForm selecting unpublished OpenNebula package versions by using an available stable major/minor repository series [#8118](https://github.com/OpenNebula/one/issues/8118).
* Fix Veeam backups starting after a failed backup configuration update and remaining in the starting phase after failure [#8146](https://github.com/OpenNebula/one/issues/8146).
* Fix Veeam backup mappings becoming corrupted when parallel backups update the mapping file [#8147](https://github.com/OpenNebula/one/issues/8147).
* Fix Virtual Network updates no longer reaching a VM after one of its multiple NICs on the same network is detached [#8228](https://github.com/OpenNebula/one/issues/8228).

## Security Issues

* Fix the reported Brotli vulnerability in FireEdge by updating its Node.js runtime and bundled dependencies ([CVE-2026-111497](https://github.com/advisories/GHSA-9v8h-qqgm-4m35)).
* Fix exposure of restic repository passwords in backup image error messages when backup operations fail.
* Fix shell command injection through malicious `MD5` or `SHA1` values in image templates.
* Fix FireEdge SSH tunnel handling that could connect a Guacamole VNC session to the wrong VM.
* Fix stored cross-site scripting in Sunstone when displaying unsanitized Zendesk support ticket comments.
* Fix outdated Lodash dependencies in FireEdge by upgrading to version `4.18.1` ([CVE-2025-13465](https://github.com/advisories/GHSA-xxjr-mmjv-4gpg), [CVE-2026-4800](https://github.com/advisories/GHSA-r5fr-rjxr-66jc)).
* Fix padding oracle and target-user bypass vulnerabilities in server authentication, and increase the entropy of generated passwords.

---

## Updating OneKS Appliance and Monitoring

After upgrading OpenNebula from 7.4.0 or 7.4.1 to 7.4.2, delete the previously imported OneKS appliance and reimport the latest version from the Marketplace to enable the new monitoring and application management features. See [Appliance Configuration]({{% relref "platform_services/oneks/management/configuration/#appliance-configuration" %}}) for import details.

These features also require enabling the `:monitor` section in `/etc/one/oneks-server.conf` and restarting the OneKS service. Follow the [Monitor Configuration]({{% relref "platform_services/oneks/management/configuration/#monitor-configuration" %}}) instructions, including the required transparent proxy settings.

Reimporting the appliance does not affect existing Kubernetes Clusters. The monitor is deployed in new Clusters created after it has been enabled.

---

## Updating Sunstone Configuration Files

After upgrading to 7.4.2 and successfully completing `onecfg upgrade`, check the following settings to enable the new Sunstone functionality in the intended views. When upgrading directly from 7.4.0, also review the [Sunstone configuration updates for 7.4.1]({{% relref "software/release_information/release_notes/resolved_issues_741.md#updating-sunstone-configuration-files" %}}). All paths below are relative to `/etc/one/fireedge/` on the OpenNebula Front-end Host.

Merge these settings into the existing YAML sections, preserving other settings and actions. Do not create duplicate `info-tabs` or `filters` keys.

### Enable Port Mirroring in Sunstone [#8149](https://github.com/OpenNebula/one/issues/8149)

The 7.4.2 configuration migration adds the Port Mirroring tab settings to the standard `admin`, `groupadmin`, and `user` views. Add the form routes manually, then verify the tab settings below. Enabling the tab alone does not register the creation and editing forms.

In `sunstone/tab-manifest.yaml`, locate the entry with title: Networks. Within its `routes` section, after the following entry:

```yaml
    - title: Create mirror
      path: /virtual-network/:id/mirror/create
      Component: CreateVirtualNetworkMirror
    - title: Edit mirror
      path: /virtual-network/:id/mirror/:mirrorId/update
      Component: CreateVirtualNetworkMirror
```

In `sunstone/views/admin/vnet-tab.yaml` and `sunstone/views/user/vnet-tab.yaml`, verify the following block under the existing `info-tabs` key. Add any missing settings:

```yaml
info-tabs:
  port_mirroring:
    enabled: true
    actions:
      mirror_create: true
      mirror_update: true
      mirror_addport: true
      mirror_delport: true
      mirror_delete: true
```

In `sunstone/views/groupadmin/vnet-tab.yaml`, verify that the tab is enabled with management actions disabled. Add any missing settings:

```yaml
info-tabs:
  port_mirroring:
    enabled: true
    actions:
      mirror_create: false
      mirror_update: false
      mirror_addport: false
      mirror_delport: false
      mirror_delete: false
```

For custom views that expose Virtual Networks, add the `port_mirroring` block to their `vnet-tab.yaml` files and enable only the intended actions. These flags control the UI and do not grant OpenNebula permissions.

Restart FireEdge and reload Sunstone in the browser after applying the changes.

### Enable VM Backup Cancellation in Sunstone [#8069](https://github.com/OpenNebula/one/issues/8069)

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

### Expose Virtual Router NIC attach/detach Actions [#7708](https://github.com/OpenNebula/one/issues/7708)

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

### Add the SPICE Console [#7667](https://github.com/OpenNebula/one/issues/7667).

Add the file `sunstone/tabs/81-spice-tab.yaml`

```yaml
    - title: SPICE
      path: /spice/:id
      sidebar: false
      Component: Spice
```

In `sunstone/views/admin/vm-tab.yaml`, `sunstone/views/cloud/vm-tab.yaml`, `sunstone/views/groupadmin/vm-tab.yaml`, and `sunstone/views/user/vm-tab.yaml`, add `spice: true` under the existing top-level `actions` key. Merge this entry with the existing actions:

```yaml
actions:
  spice: true
```

### Service Template Instantiate Missing Selection Dialog [#8037](https://github.com/OpenNebula/one/issues/8037)

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

### Enable OneKS Application Tab [#7302](https://github.com/OpenNebula/one/issues/7302)

{{< alert title="Note" type="info" >}}
To install and manage applications, enable the OneKS monitor as described in [Monitor Configuration]({{% relref "platform_services/oneks/management/configuration/#monitor-configuration" %}}).
{{< /alert >}}

In `sunstone/views/*/oneks-tab.yaml`, as part of the `info-tabs` attribute, add the following entry:

```yaml
   applications:
    enabled: true
```

In `sunstone/tabs/oneks-tab.yaml`, add the following entry to the existing `routes` list, before the `/kubernetes/:id` detail route:

```yaml
   - title: Install Application
     path: /kubernetes/:id/applications/install
     Component: InstallOneKsApplication
```

### Configure Guacamole Connection Defaults and Enforced Settings

In `/etc/one/fireedge-server.conf`, add the following top-level `guacamole` section alongside the existing `guacd` section. The `guacd` section configures the daemon connection while `guacamole` configures VNC, SSH and RDP console connections. These settings replace connection defaults previously defined in FireEdge code and its Guacamole bridge.

If a `guacamole` section already exists, merge the settings into it without creating duplicate keys.

```yaml
guacamole:
  common:
    width: 1024
    height: 768
    dpi: 96

  rdp:
    port: 3389
    # Disable audio and microphone
    disable-audio: true
    enable-audio-input: false

    # Display and performance
    resize-method: display-update
    enable-wallpaper: false
    enable-theming: false
    enable-font-smoothing: false
    enable-full-window-drag: false
    enable-desktop-composition: false
    enable-menu-animations: false
    disable-bitmap-caching: false
    disable-offscreen-caching: false
    disable-glyph-caching: false

  vnc:
    port: 5900

  ssh:
    port: 22

  # Server policy, applied whenever a Guacamole connection opens
  enforced:
    common:
      disable-copy: true
      disable-paste: true
      enable-sftp: false
    rdp:
      # Requires NLA credentials; ignores certificate validation errors
      security: nla
      ignore-cert: true
      enable-drive: false
      enable-printing: false
```

Connection settings are applied in the following order, with later values overriding earlier ones: `common`, the protocol section (`vnc`, `ssh` or `rdp`), VM/NIC settings, browser settings, and `enforced`. Browser overrides are limited to display and terminal settings and `rangeports`. Within `enforced`, protocol settings override `enforced.common`. VM/NIC and browser settings cannot override enforced values.

The block above disables clipboard copy/paste and SFTP for all three protocols. For RDP, it also disables drive and printer redirection and requires Network Level Authentication (NLA). With `ignore-cert: true`, certificate validation errors are ignored. Ensure that RDP guests support NLA and provide the required credentials. Set `guacamole.enforced.rdp.ignore-cert` to `false` to require a guest certificate trusted by the Guacamole daemon. With `enforced.rdp.security: nla`, the VM's `RDP_SECURITY` setting cannot select another security mode; change the enforced policy if a different mode is required.

Restart FireEdge on the Front-end command line after saving the configuration:

```shell
systemctl restart opennebula-fireedge
```
