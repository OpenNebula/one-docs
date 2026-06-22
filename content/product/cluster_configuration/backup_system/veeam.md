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
| LVM          | No†  | No†         |
| NetApp       | No†  | No†         |

<sup>†</sup> These backup modes were supported in previous OpenNebula versions, such as 7.0 and 7.2. From OpenNebula version 7.4 onwards, they are not supported by the current OneBEX-based integration.

## Limitations

The following is a list of the limitations affecting the Veeam integration with OpenNebula:

- The KVM appliance deployed by Veeam does not include context packages. To configure the appliance network, either manually choose the first available free IP in the management network or set up a DHCP service router.
- Alpine Virtual Machines cannot be backed up.
- During image transfers, you may see a warning message stating `Unable to use transfer URL for image transfer: Switched to proxy URL. Backup performance may be affected`. This is expected and shouldn't affect performance.
- Spaces are not allowed in Virtual Machine names in the integration. Avoid using them, even if they are allowed in OpenNebula itself, to prevent issues when performing in-place restores.

If you encounter other issues or bugs, check the [Known Issues page]({{% relref "software/release_information/release_notes/known_issues/" %}}) for Veeam-related issues.

## Architecture

To ensure a compatible integration between OpenNebula and Veeam Backup, the following components and network configuration are required:

- **Backup Server**: Hosts the **OpenNebula oVirtAPI Server**.
- **Veeam Backup Appliance**: Automatically deployed by Veeam when OpenNebula is added as a hypervisor.
- **OpenNebula Backup Exporter (OneBEX)**: Runs on demand on the OpenNebula hypervisors and exposes VM backup data to Veeam. See [Interactive Backup Integrations]({{% relref "product/integration_references/infrastructure_drivers_development/interactive_backup.md#interactive-backup-integration" %}}) for implementation details.
- **Veeam (interactive) Backup Datastore**: An OpenNebula `BACKUP_DS` using `DS_MAD="interactive"` and `VEEAM_DS="YES"`. This datastore coordinates Veeam backup operations and tracks backup metadata. The backup itself is stored in the Veeam repository.
- **Management Network**: Provides connectivity between all of the following components:
     - OpenNebula Front-end
     - OpenNebula oVirtAPI Server
     - OpenNebula OneBEX endpoint on each hypervisor
     - All OpenNebula Hosts running VMs to be backed up
     - Veeam Server
     - Veeam Backup Appliance
<br>
<br>

{{< image path="/images/veeam/interactive_backup_veeam_architecture.svg" alt="Architecture of the OpenNebula-Veeam Backup Integration" align="center" width="90%" mb="20px" border="false" >}}

## Backup Server Requirements

To ensure full compatibility with the oVirtAPI module, the Backup Server must run one of the following operating systems:

- AlmaLinux 9
- Ubuntu 22.04 or 24.04
- RHEL 9
- Debian 12

The minimum hardware specifications are:

- **CPU**: 8 cores
- **Memory**: 16 GB RAM
- **Disk**: No hard requirement for backup payload storage. Backup data is stored in the Veeam repository.

## Veeam Backup Appliance Requirements

When OpenNebula is added as a platform in Veeam, Veeam deploys a KVM appliance as a VM in OpenNebula. This appliance has the following minimum requirements:

- **CPU**: 6 cores
- **Memory**: 6 GB RAM
- **Disk**: 100 GB

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

### 2. Prepare the Environment for the oVirtAPI Server

A server should be configured to function as the oVirtAPI Server and expose the oVirtAPI. This server should be accessible from all the Clusters intended for backup via the management network shown in the architecture diagram. The oVirtAPI Server acts as the communication gateway between Veeam and OpenNebula.

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

* `one_xmlrpc`: Address of the OpenNebula Front-end. Please do not include any prefixes such as `http://`, only the IP address itself is needed.
* `endpoint_port`: Port used by the OpenNebula RPC endpoint (defaults to 2633).
* `public_ip`: IP address that Veeam uses to communicate with the oVirtAPI server.
* `one_sshkey`: Path to the private key file used by the oVirtAPI server to reach the OpenNebula Front-end.
* `one_sshkey_host`: Path to the private key file used by the OpenNebula Front-end to reach hypervisor Hosts. Local path as seen on the Front-end.
* `backup_freeze`: (Optional) Controls which filesystem freeze mode OpenNebula requests when performing backups initiated via the oVirtAPI/Veeam integration. Valid values are `NONE`, `AGENT`, and `SUSPEND`. For details on each mode see the Backup Modes section in the backup guide: [Backup Modes]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations/#backup-modes" %}}).

In the same configuration file, configure the OneBEX port and the port range reserved for interactive restores:

* `onebex_port`: Port where OneBEX listens on the hypervisors. It must match the port configured in `onebex-server.conf`.
* `port_min` and `port_max`: Range of available ports reserved for interactive restores.
* `ports_path`: File where the oVirtAPI Server tracks ports used for interactive restores.

{{< alert title="Important" type="info" >}}
You may see the 5554 port in the `public_ip` variable in the default settings, this is no longer needed so avoid using it. Leave only the IP address in the variable, no port needed.

You may also have a variable named `instance_id`, which you should delete if you are running a version of the package >=7.0.1.
{{< /alert >}}

During installation a self-signed certificate is generated at `/etc/one/ovirtapi-ssl.crt` for encryption. You can replace this certificate with your own and change the `cert_path` configuration variable.

After installing the package, make sure that the `oneadmin` user in the Backup Server can perform passwordless SSH to the `oneadmin` user in the Front-end server.

Finally, start the service with either `systemctl start apache2` (Ubuntu/Debian) or `systemctl start httpd` (RHEL/Alma).

{{< alert title="Important" type="info" >}}
Once the package is installed, a `oneadmin` user is created. This user and the `oneadmin` user in the Front-end must be able to establish passwordless SSH connections in both directions.
{{< /alert >}}

{{< alert title="Package dependency" type="info" >}}
In RHEL and Alma environments, you may face issues with the passenger package dependencies (`mod_passenger` and `mod_ssl`). You may add the correct repository and install the packages with the following:

```shell
curl --fail -sSLo /etc/yum.repos.d/passenger.repo https://oss-binaries.phusionpassenger.com/yum/definitions/el-passenger.repo
dnf install -y passenger mod_passenger mod_ssl
```

{{< /alert >}}

### 5. Add OpenNebula to Veeam

To add OpenNebula as a hypervisor to Veeam, configure it as an oVirt KVM Manager in Veeam and choose the IP address of the oVirtAPI module. You can follow the [official Veeam documentation](https://helpcenter.veeam.com/docs/vbrhv/userguide/connecting_manager.html?ver=6) for this step or follow the next steps:

#### 5.1. Add the New Virtualization Manager

The first step is to add the oVirtAPI Backup Server to Veeam. Go to **Backup Infrastructure**, then **Managed Servers**, and click **Add Manager**:

{{< image path="/images/veeam/add_manager.png" alt="Veeam Add Manager" align="center" width="90%" mb="20px" >}}

Then, choose to add a new **Virtualization Platform**:

{{< image path="/images/veeam/virtualization_platform.png" alt="Veeam Virtualization Platform" align="center" width="90%" mb="20px" >}}

Then select **Oracle Linux Virtualization Manager**:

{{< image path="/images/veeam/virtualization_platform_olvm.png" alt="Veeam Oracle Linux Virtualization Manager" align="center" width="90%" mb="20px" >}}

This opens a new dialog box. In the **Address** field, use the IP address or DNS name of the server where the oVirtAPI module is installed:

{{< image path="/images/veeam/new_manager.png" alt="Veeam New Manager" align="center" width="90%" mb="20px" >}}

On the **Credentials** tab, set the user and password used to access the OpenNebula Front-end. Use the `oneadmin` user or another OpenNebula user with equivalent privileges. This is an OpenNebula user, not a system user. The user should be listed in the System/Users tab of FireEdge or through the CLI with `oneuser list`.

If the default certificate is used, Veeam may show an untrusted certificate warning. This warning can be accepted:

{{< image path="/images/veeam/one_credentials.png" alt="One Credentials" align="center" width="90%" mb="20px" >}}

Click **Finish**. The new oVirtAPI server should be listed under Managed Servers as an **oVirt KVM** hypervisor.

{{< image path="/images/veeam/hypervisor_added.png" alt="Hypervisor Added" align="center" width="90%" mb="20px" >}}

#### 5.2. Deploy the KVM appliance

For Veeam to perform backup and restore operations, it must deploy a dedicated Virtual Machine to act as a worker. To deploy it, go to the **Backup Infrastructure** tab, then **Backup Proxies**, and click **Add Proxy**:

{{< image path="/images/veeam/add_proxy.png" alt="Veeam Add Proxy" align="center" width="90%" mb="20px" >}}

A new dialog box will open. Select the **Oracle Linux Virtualization Manager**:

{{< image path="/images/veeam/add_proxy_olvm.png" alt="Veeam Add Proxy OLVM" align="center" width="90%" mb="20px" >}}

The select the **Oracle Linux Virtualization Manager backup appliance** to deploy:

{{< image path="/images/veeam/add_proxy_app.png" alt="Veeam Add Proxy OLVM Appliance" align="center" width="90%" mb="20px" >}}

This opens a new wizard to deploy the appliance. You should choose to deploy a new appliance:

{{< image path="/images/veeam/new_appliance.png" alt="Veeam New Appliance" align="center" width="90%" mb="20px" >}}

Next choose the Cluster on which to deploy the appliance, as well as a name and the storage domain where the appliance image should be stored:

{{< image path="/images/veeam/appliance_virtual_machine.png" alt="Veeam Appliance Machine" align="center" width="90%" mb="20px" >}}

For the appliance credentials, choose the same ones that you set up when configuring the virtualization manager in the previous steps:

{{< image path="/images/veeam/appliance_credentials.png" alt="Veeam Appliance Credentials" align="center" width="90%" mb="20px" >}}

In the **Network Settings** tab, choose the management network that the appliance will use. It is recommended to manually choose the IP address configuration. If no DHCP service is setup, use the first available free IP in the address range of the management network.

{{< image path="/images/veeam/appliance_network.png" alt="Veeam Appliance Network" align="center" width="90%" mb="20px" >}}

In the next step, Veeam will take care of deploying the appliance. Once finished, you should see it listed in the same tab:

{{< image path="/images/veeam/appliance_listed.png" alt="Veeam Appliance in List" align="center" width="90%" mb="20px" >}}

#### 5.3. Verification

If the integration is configured correctly, the available Virtual Machines appear in the **Inventory** tab under the **Virtual Infrastructure -> oVirt KVM** section.

{{< image path="/images/veeam/verification.png" alt="Veeam Verification" align="center" width="90%" mb="20px" >}}

## Logging Information

The oVirtAPI server writes logs in the following directory depending on the operating system:

* Ubuntu/Debian: `/var/log/apache2`
* Alma/RHEL: `/var/log/httpd`

Additional logs for interactive backups are available on the hypervisors:

* OneBEX logs: `/var/log/one/onebex.log`

## Performance Improvements

Backup data is transferred from the OpenNebula hypervisors through OneBEX. The oVirtAPI server handles inventory, authentication, and orchestration requests from Veeam.

If oVirtAPI requests are queued under load, increase the number of Passenger processes available to the oVirtAPI service. This is controlled by the `PassengerMaxPoolSize` parameter in the Apache configuration file. After changing `PassengerMaxPoolSize`, balance the value with the available RAM and CPU in the Backup Server.

### Adjusting the Process Pool

The configuration file is available in the following locations depending on your distribution:

* Debian/Ubuntu: `/etc/apache2/sites-available/ovirtapi-server.conf`
* Alma/RHEL: `/etc/httpd/conf.d/ovirtapi-server.conf`

After editing and saving the file, you must restart the web server for the change to take effect:

* Debian/Ubuntu: `sudo systemctl restart apache2`
* Alma/RHEL: `sudo systemctl restart httpd`


**Memory**

Each active Passenger process consumes approximately 150-200 MB of RAM. You can use the following formula as a starting point to determine a safe maximum, leaving a 30% buffer for the OS and other services:

`(TOTAL_SERVER_RAM_MB * 0.70) / 200 = Recommended MaxPoolSize`

**CPU**

While increasing the pool size, monitor CPU usage. If the CPU load becomes the bottleneck, adding more processes will not increase throughput and may reduce performance. In that case, increase the number of CPUs or vCPUs assigned to the Backup Server.

OneBEX concurrency is controlled separately in `/var/lib/one/remotes/etc/onebex/onebex-server.conf` through the Puma settings. Increase these values only when the hypervisor, storage, and network can handle the additional concurrent requests.

### Interpreting Veeam Job Statistics

The Veeam job statistics window shows a breakdown of the load, which is crucial for identifying the true bottleneck in your backup chain.

* **Source**: This represents the OpenNebula side serving the backup data, typically the hypervisor and OneBEX endpoint. A high load here indicates that the source is the active bottleneck.
* **Proxy**: This is the KVM appliance deployed by Veeam. If its load is consistently high (e.g., >90%), it is the bottleneck and requires more resources (vCPU/RAM).
* **Network**: This indicates that the transfer speed is being limited by the available bandwidth on the management network connecting the components.

## Volatile Disk Backups

To back up volatile disks, enable this functionality in the OpenNebula Virtual Machine configuration by setting the `BACKUP_VOLATILE` parameter to `YES`. Otherwise, the disk is not listed in Veeam. For more information about volatile disk backups in OpenNebula, see the [backup documentation page]({{% relref "product/virtual_machines_operation/virtual_machine_backups/operations.md" %}}).
