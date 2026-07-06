---
title: "Veeam Backup (EE)"
linkTitle: "Veeam (EE)"
weight: "4"
---

<a id="vm-backups-veeam"></a>


The OpenNebula-Veeam&reg; Backup Integration exposes an **oVirt-compatible REST API** through the oVirtAPI server component, allowing Veeam to connect to OpenNebula as if it were an oVirt/RHV hypervisor. Veeam discovers OpenNebula resources through oVirtAPI and pulls backup data from hypervisors through the OpenNebula Backup Exporter (OneBEX). This integration enables image-level backups — incremental backups based on Changed Block Tracking (CBT) — and granular restores such as full VM and file-level restores from the Veeam console. This integration is exclusive to the OpenNebula Enterprise Edition (EE).

## Features

| Area               | Benefit                        | Description                                                                                                           |
|--------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Data Protection    | Agentless, Image-Level Backups | Protect entire VMs without installing or managing agents inside the guest OS.                                         |
| Efficiency         | Incremental Backups (CBT)      | Leverages Change Block Tracking (CBT) via the API to back up only the data that has changed, reducing backup windows. |
| Native Integration | Uses Standard Veeam Workflow   | Connect OpenNebula as a standard "oVirt" hypervisor in Veeam. No additional custom Veeam plug-ins are required.       |
| Recovery           | Flexible Restore Options       | Enables Full VM restores, instant VM recovery, and file-level restores directly from the Veeam B&amp;R console.       |
| Automation         | Full Discovery                 | Veeam automatically discovers and displays the OpenNebula Cluster hierarchy (Clusters, Hosts, VMs, and storage).      |
| Portability        | VMWare import                  | Enables restoring Virtual Machines backed up in Veeam from VMWare into OpenNebula.                                    |

## Compatibility

The oVirtAPI module is compatible with the Veeam Backup & Replication version specified in the [Platform Notes]({{% relref "../../../software/release_information/release_notes/platform_notes/#monitoring-and-backups" %}}).

The following table summarizes the supported backup modes for each storage system:

| Storage      | Full | Incremental |
|--------------|------|-------------|
| File (qcow2) | Yes  | Yes         |
| File (raw)   | No†  | No†         |
| Ceph         | No†  | No†         |
| LVM          | Yes  | Yes         |
| NetApp       | No†  | No†         |

<sup>†</sup> These backup modes were supported in previous OpenNebula versions, such as 7.0 and 7.2. In OpenNebula version 7.4, they are not supported by the current OneBEX-based integration, but are planned to be supported in a future maintenance releases.

### Volatile Disk Backups

Volatile disks cannot be backed up by default. To back up volatile disks, enable this functionality in the OpenNebula Virtual Machine configuration by setting the `BACKUP_VOLATILE` parameter to `YES`. Otherwise, the disk is not listed in Veeam. For more information about volatile disk backups in OpenNebula, see the [backup documentation page]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations.md" %}}).

## Limitations

The following is a list of the limitations affecting the Veeam integration with OpenNebula:

- The KVM appliance deployed by Veeam does not include context packages. To configure the appliance network, either manually choose any available free IP in the management network or set up a DHCP service.
- Alpine Virtual Machines cannot be backed up.
- During upload image transfers, you may see a warning message stating `Unable to use transfer URL for image transfer: Switched to proxy URL. Backup performance may be affected`. This is expected and shouldn't affect performance.
- Spaces are not allowed in Virtual Machine names in the integration. Avoid using them, even if they are allowed in OpenNebula itself, to prevent issues when performing in-place restores.

If you encounter other issues or bugs, check the [Known Issues page]({{% relref "software/release_information/release_notes/known_issues/" %}}) for Veeam-related issues.

## Architecture

To ensure a compatible integration between OpenNebula and Veeam Backup, the following components and network configuration are required:

- **Veeam Workers**: Deployed from the Veeam server to process backups and restores.
- **OpenNebula Backup Exporter (OneBEX)**: Runs on demand on the OpenNebula hypervisors and exposes VM backup data to Veeam. See [Interactive Backup Integrations]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}) for implementation details.
- **Veeam (interactive) Backup Datastore**: An OpenNebula `BACKUP_DS` using `DS_MAD="interactive"` and `VEEAM_DS="YES"`. This datastore coordinates Veeam backup operations and tracks backup metadata. The backup itself is stored in the Veeam repository.
- **Management Network**: Provides connectivity between all of the following components:
     - OpenNebula Front-end
     - OpenNebula OneBEX endpoint on each hypervisor
     - All OpenNebula Hosts running VMs to be backed up
     - Veeam Server
     - Veeam Workers
<br>
<br>

{{< image path="/images/veeam/interactive_backup_veeam_architecture.svg" alt="Architecture of the OpenNebula-Veeam Backup Integration" align="center" width="90%" mb="20px" border="false" >}}

## Installation and Configuration

### 1. Configure OneBEX

Configure OneBEX on every OpenNebula hypervisor that can run VMs backed up by Veeam. OneBEX starts on demand during the backup operation and exposes the prepared disk exports directly to Veeam.

The Veeam Server and Veeam Backup Appliance must be able to connect to the configured OneBEX address and port on each hypervisor.

Edit the OneBEX configuration in the OpenNebula remotes directory. Open the file in the following location:

```default
/var/lib/one/remotes/etc/onebex/onebex-server.conf
```

After updating the configuration file, synchronize the Hosts:

```shell
onehost sync -f
```

For OneBEX parameters and API details, see [Interactive Backup Integrations]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}).

{{< alert title="High Availability" type="info" >}}
If using High Availability, any changes to ``/var/lib/one/remotes/etc/onebex/onebex-server.conf`` need to be performed on all frontends.
{{< /alert >}}

### 2. Enable VM Guest Agent Monitoring

The integration needs VM Guest Agent monitoring to be enabled. To do so set ``:enabled`` to ``true`` on the following file in the frontend: 

```default
/var/lib/one/remotes/etc/im/kvm-probes.d/guestagent.conf
```

Then, in the same frontend server execute the following command to propagate the remote into the KVM hosts: 

```shell
onehost sync --force
```

{{< alert title="High Availability" type="info" >}}
If using High Availability, any changes to ``/var/lib/one/remotes/etc/im/kvm-probes.d/guestagent.conf`` need to be performed on all frontends.
{{< /alert >}}

### 3. Create the Veeam Backup Datastore

Create and configure the Veeam backup datastore in OpenNebula. This datastore uses the interactive datastore driver to start OneBEX, coordinate backup sessions initiated from Veeam, and store the corresponding OpenNebula backup metadata. **The backup itself is stored in the Veeam repository**.

The datastore template must include `VEEAM_DS="YES"` so the oVirtAPI Server can identify the datastore used by the Veeam integration, and also `DS_MAD="interactive"` so OpenNebula can handle the OneBEX workflow.

The following example template creates a Veeam backup datastore:

```shell
cat << EOF > /tmp/interactive-datastore.txt
NAME="VeeamDS"
DS_MAD="interactive"
TM_MAD="-"
TYPE="BACKUP_DS"
VEEAM_DS="YES"
RESTRICTED_DIRS="/"
SAFE_DIRS="/var/tmp"
EOF

onedatastore create /tmp/interactive-datastore.txt
```

Add the datastore to each Cluster containing VMs that will be backed up by Veeam:

```shell
onecluster adddatastore <cluster-name> <datastore-name>
```

For more information about the `interactive` driver internals, see [Interactive Backup Integrations]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration#interactive-backup-integration" %}}).

### 4. Install and Configure the oVirtAPI Module

To install the oVirtAPI module, configure the OpenNebula repository on the Backup Server by following the [OpenNebula Enterprise Edition Repository Setup Guide]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ee.md" %}}). Then install the `opennebula-ovirtapi` package with the relevant package manager for your OS.

The configuration file can be found at `/etc/one/ovirtapi-server.yml`. Change the following variables before starting the service:

* `public_ip`: IP address that Veeam will use to communicate with the frontend node. 
* `endpoint_port`: Port used by the OpenNebula RPC endpoint (defaults to 2633).
* `backup_freeze`: (Optional) Controls which filesystem freeze mode OpenNebula requests when performing backups initiated via the oVirtAPI/Veeam integration. Valid values are `NONE`, `AGENT`, and `SUSPEND`. For details on each mode see the Backup Modes section in the backup guide: [Backup Modes]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations/#backup-modes" %}}).

In the same configuration file, configure the OneBEX port and the port range reserved for interactive restores:

* `onebex_port`: Port where OneBEX listens on the hypervisors. It must match the port configured in `onebex-server.conf`.
* `port_min` and `port_max`: Range of available ports reserved for interactive restores.
* `ports_path`: File where the oVirtAPI Server tracks ports used for interactive restores.

During installation a self-signed certificate is generated at `/etc/one/ovirtapi-ssl.crt` for encryption. You can replace this certificate with your own and change the `cert_path` configuration variable.

Finally, start the service with either `systemctl start apache2` (Ubuntu/Debian) or `systemctl start httpd` (RHEL/Alma).

{{< alert title="Package dependency" type="warning" >}}
In RHEL and Alma environments, you may face issues with the passenger package dependencies (`mod_passenger` and `mod_ssl`). You may add the correct repository and install the packages with the following:

```shell
curl --fail -sSLo /etc/yum.repos.d/passenger.repo https://oss-binaries.phusionpassenger.com/yum/definitions/el-passenger.repo
dnf install -y passenger mod_passenger mod_ssl
```

{{< /alert >}}

{{< alert title="High availability" type="info" >}}

If the ovirtapi module is going to be configured in High Availability mode, the ovirtapi package needs to be installed and configured in all frontends. Additionally, the `public_ip` must be the VIP address, which is also the one we will use when adding OpenNebula as a Virtualization Platform in Veeam. 

{{< /alert >}}

### 5. Add OpenNebula to Veeam

This section will address the necessary steps to add OpenNebula as a Virtualization Platform into Veeam and deploy the necessary workers. 

#### 5.1. Add the New Virtualization Manager

First you need to add OpenNebula as an oVirt platform. To do so, follow the [Adding oVirt KVM Manager to Backup Infrastructure](https://helpcenter.veeam.com/docs/vbr/userguide/ovirt_add_rhv_manager.html?ver=13) Veeam guide with the following considerations:

- When selecting the DNS name or the IP address, it should match the `public_ip` configured in the ovirtapi module.
- On the **Credentials** tab, set the user and password used to access the OpenNebula Front-end. Use the `oneadmin` user or another OpenNebula user with equivalent privileges. This is an OpenNebula user, not a system user. The user should be listed in the System/Users tab of FireEdge or through the CLI with `oneuser list`.
- If the default certificate is used, Veeam may show an untrusted certificate warning. This is expected and will not affect the integration.

#### 5.2. Deploy a KVM Worker

Next you need to deploy at least one KVM Worker. To do so, follow the [Adding Workers](https://helpcenter.veeam.com/docs/vbr/userguide/ovirt_workers_add.html?ver=13) Veeam guide with the following considerations:

- If you are not using a DHCP service, you will need to use a static address. You can set it to any free IP address in the management network. 
- The DNS server used must be able to resolve the hostnames of all KVM hosts.

{{< alert title="Hostnames and DNS" type="info" >}}

For backups to work, the HOSTNAME attribute inside each OpenNebula Host must be a FQDN, not a shortname, and the DNS used by the workers and frontend must be able to resolve that FQDN.

{{< /alert >}}

## Logging Information

The oVirtAPI server writes logs in the following paths depending on the operating system:

* Ubuntu/Debian: `/var/log/apache2/error.log`
* Alma/RHEL: `/var/log/httpd/error.log`

Additional logs for interactive backups are available on the hypervisors:

* OneBEX logs: `/var/log/one/onebex.log`


