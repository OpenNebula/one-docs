---
title: "Disaster Recovery Architecture with NetApp ONTAP"
linkTitle: "NetApp"
weight: 3
---

{{< alert title="Work In Progress" type="primary" >}}
This document is a work in progress.
{{< /alert >}} 

## Overview

Disaster Recovery involves anticipating and designing an adequate response for any situation that prevents the correct functioning of a system in an organization. DR plays a key role in an organization’s business and operations continuity, and is a critical aspect in the planning and maintenance of cloud infrastructure.

A complete DR solution involved two main processes:

- **Failover**, the process of moving business operations from a primary site which has suffered an outage, to a temporary site designated and preconfigured for such emergencies.  
- **Failback**, the process of moving business operations back to the primary site, after the site’s normal operation has been restored.

This guide intends to provide a comprehensive overview of the architecture and actions necessary to perform Disaster Recovery using a NetApp backed NFS datastore. Ideally after reviewing this guide you should be able to:

- Configure your own DR Solution  
- Design the recovery procedures for failover and failback  
- Test the DR Solution

**Note**: This guide does not cover setting up the NetApp ONTAP clusters or adding the NFS datastores to your OpenNebula infrastructure. For details on configuring NetApp as your storage system, see SAN/NFS Datastore. You can also deploy opennebula with NFS storage using OneDeploy.

## Architecture

The reference architecture used in this guide consists of two OpenNebula clusters with independent Front-ends, on Site A and Site B.

Each site contains an OpenNebula Front-end, three KVM compute nodes, and an independent NetApp ONTAP cluster with a SnapMirror relationship between them.  The Virtual Machines running production workloads reside on Site A. The ONTAP clusters must be in contact with each other but each site only needs to contact its own ONTAP cluster

The following diagram shows a basic state of before and after of a Disaster Recovery scenario where a failover has been performed:

|  |
| :---: |

### Specifications

The setup tested in this reference architecture utilizes the same versions of software components, details below, on both sites. Note that the NetApp ONTAP SnapMirror relationship is active between the two ONTAP clusters.

#### Site A (source):

- OpenNebula Controller (Front-end)  
  - OpenNebula 7.4.1  
  - OS: Ubuntu 24.04  
- 3x Compute KVM Nodes   
- NetApp ONTAP Cluster serving an NFS mount  
  - SnapMirror Relationship configured: [Version Compatibility Chart](https://docs.netapp.com/us-en/ontap/data-protection/compatible-ontap-versions-snapmirror-concept.html#unified-replication-relationships)  
- VMs running production workloads

#### Site B (target):

- OpenNebula Controller (Front-end)  
  - OpenNebula 7.4.1  
  - OS: Ubuntu 24.04  
- 3x Compute KVM Nodes   
- NetApp ONTAP Cluster serving an NFS mount  
  - SnapMirror Relationship configured: [Version Compatibility Chart](https://docs.netapp.com/us-en/ontap/data-protection/compatible-ontap-versions-snapmirror-concept.html#unified-replication-relationships)  
- VMs running production workloads

### Basic Configuration

This guide will assume that the OpenNebula Datastores are of QCOW2 or Shared types, which are backed by an NFS mount that is served by a NetApp ONTAP Cluster. 

To enable the possibility of Disaster Recovery, the ONTAP Volume(s) attached to Site A should be configured to have a SnapMirror relationship to a Site B volume which acts as the destination. Depending on your infrastructure this could be either a synchronous or asynchronous relationship. When using an asynchronous relationship there could be potential data loss if Site A is completely lost without any warning, because they only sync on a specific timer.

There are two configurations to be aware of with the NFS datastores as well. You can have one very large volume which contains both the image and system datastores, in which case your mount point would be symlinked to from \`/var/lib/one/datastores\`, and this would work fine with this process. 

The other configuration is by having separate volumes and mount points for each image and system data store. This would put your mount points as \`/var/lib/one/datastores/0\` for the system datastore and \`/var/lib/one/datastores/1\` for the images datastore. In this configuration you would need to either enable \`QCOW2\_STANDALONE=”YES”\` for your datastores, or set up SnapMirror relationships for both of the datastores and perform the failover/failback actions on both of the volumes as well. This is because QCOW2/Shared datastores by default will make backing chains with the QCOW2 files which means the image datastore is also necessary for running VMs in that configuration.

#### Enable Mirroring

To enable SnapMirror Relationships you should follow [the guidance of NetApp’s Documentation](https://docs.netapp.com/us-en/ontap/data-protection/create-replication-relationship-one-step-task.html), or reach out to their technical support for assistance

The relationship should be created so that Site A is the source and therefore read-write status. Site B is the destination and will be read-only status. Verifying the status of your SnapMirror relationships can be found in [NetApp’s Documentation](https://docs.netapp.com/us-en/ontap-cli/snapmirror-show.html#parameters).

## Failover

There are two cases for Disaster Recovery scenarios: planned and unplanned. There are only a few extra steps that can be taken for a planned failover to reduce the amount of data loss. This can be useful if one site is in degraded condition and needs some hardware replacements which would take down the entire network or would pull multiple hosts offline.

During a planned failover, the main steps that can be taken to prevent data loss are:

1. Undeploy/power-off all Virtual Machines  
2. Run a [SnapMirror Resync](https://docs.netapp.com/us-en/ontap-cli/snapmirror-resync.html#examples) if the relationship is asynchronous.

During an unplanned failover, these steps obviously cannot be taken since that would normally indicate a complete loss of connectivity to Site A for some reason.

Beyond this, both situations are effectively the same. If possible, fencing should be executed on Site A to ensure that there is actually nothing using the datastore. then the following actions should be taken:

1. Break the SnapMirror Relationship either on [the CLI](https://docs.netapp.com/us-en/ontap-cli/snapmirror-break.html) or the [ONTAP Web UI](https://docs.netapp.com/us-en/ontap-system-manager-classic/volume-disaster-recovery/task_breaking_snapmirror_relationship.html) so that the Destination(Site B) becomes read-write.  
2. Disable the hosts in Site A. They may be in error status but disable/offline all of them anyways. This does not perform fencing.  
3. Attach the Datastore to the Cluster for Site B so it can be used at this location.  
4. Detach the Datastore from the Cluster for Site A  
5. Update the Datastore  
   1. If using NFS Auto Mount, then you’ll need to update the attributes:  
      NFS\_AUTO\_HOST to match the new Cluster  
      NFS\_AUTO\_PATH to match the new Volume  
   2. If not using NFS Auto Mount, mount the datastore at the appropriate location in Site B’s hosts and front-end, which should be the same filesystem location on Site A. The Datastore ID will not change.  
6. Resume/power-on the Virtual Machines. They should now deploy to the hosts on Site B using the latest SnapMirror data available.  
7. Once the Site A NetApp ONTAP Cluster is available again, rebuild the SnapMirror relationship setting Site B as the Source (read-write) and Site A as the Destination (read-only). This will make Failback much faster.

## Failback

The Failback scenario is nearly identical to the Failover scenario just backwards. If you were unable to establish the SnapMirror relationship previously, ensure that you do so and it is in a healthy state for these operations.

The perform the failback you should perform the following:

1. Enable hosts on Site A if you have not already.  
2. Undeploy/power-off all the Virtual Machines.  
3. Perform a SnapMirror Resync to ensure the data is up-to-date  
4. Break the SnapMirror relationship so Site A becomes read-write  
5. Attach the Datastore back to the Cluster for Site A  
6. Detach the Datastore from the Cluster for Site B  
7. Update the Datastore  
   1. If using NFS Auto Mount, then revert the following to their original values before the failover:  
      NFS\_AUTO\_HOST  
      NFS\_AUTO\_PATH  
   2. If not using NFS auto mount, then ensure the datastore is mounted correctly in your Site A hosts and Front-end.  
8. Resume/Power-on the Virtual Machines. They should now deploy to the hosts on Site A again, using this SnapMirror data  
9. Re-establish the SnapMirror relationship to its original state where Site A is the source and Site B is the destination.

