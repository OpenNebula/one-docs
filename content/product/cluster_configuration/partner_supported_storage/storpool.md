---
title: "StorPool Datastore"
linktitle: "StorPool"
date: "2026-09-30"
description:
categories:
tags:
weight: "1"
---

## Overview

StorPool is a distributed, software-defined block storage platform that transforms standard x86 servers into enterprise-grade shared storage. Native integration with OpenNebula enables full VM disk lifecycle management — provisioning, cloning, snapshots, live migration, and cleanup — with the performance, reliability, and operational simplicity that production clouds demand.

With StorPool, OpenNebula clouds gain storage that scales linearly, eliminates single points of failure, and delivers consistent sub-millisecond latency regardless of load — all managed through the familiar OpenNebula interface without manual storage operations.

### Why StorPool \+ OpenNebula

|       |       |
| ----- | ----- |
| **Ultra-Low Latency** | Sub-millisecond in-VM response times with custom networking protocols designed for maximum throughput |
| **Enterprise Reliability** | Distributed shared-nothing architecture with no single point of failure and three-way synchronous replication |
| **Proven Scale** | 13+ million IOPS demonstrated on production Clusters; linear scaling as you add nodes |
| **Operational Simplicity** | In-service upgrades, online configuration changes, and automatic failure recovery |
{.no-header}


## StorPool Capabilities

When you deploy StorPool with OpenNebula, your infrastructure benefits from the following enterprise-grade storage capabilities:

### Reliability and Data Protection

* **End-to-end data integrity** — Proprietary 64-bit checksums protect against silent data corruption, phantom writes, and bit rot across the full data lifecycle  
* **Three-way synchronous replication** — Configurable per-volume; system continues operating even during simultaneous drive failures  
* **Automatic recovery** — Self-healing Cluster detects failures and recovers automatically, reducing operational burden  
* **Fault sets** — Isolate failure domains to ensure copies are distributed across physical boundaries

### Performance and Efficiency

* **Erasure Coding** — Massive capacity savings with near-zero performance impact; per-volume policy management  
* **NVMe and multi-core optimization** — Direct NVMe drivers bypass kernel overhead; **Thin provisioning and zero detection** — Provision more than physical capacity; empty blocks consume no space  
* **Instant snapshots and clones** — Copy-on-write technology for space-efficient, high-performance copies

### Flexible Deployment

* **Hyper-converged or dedicated** — Run storage alongside compute or on dedicated storage nodes  
* **Data tiering and storage pools** — Multiple performance profiles within a single Cluster with no data migration  
* **10/25/40/100 GbE support** — Scale network bandwidth to match your requirements

### Operations and Integration

* **RESTful JSON API** — Full automation and integration with existing management systems  
* **In-service upgrades** — Rolling updates without service interruption  
* **Storage QoS** — Per-volume IOPS and bandwidth limits ensure SLA compliance  
* **iSCSI and NVMe/TCP** — Connect systems that don't support the native StorPool driver

[See all StorPool features](https://storpool.com/features)

## OpenNebula Integration Features

### Standard Datastore Operations

**StorPool supports all standard OpenNebula datastore features**, including image provisioning, VM disk management, live migration, snapshots, and cloning operations. For limitations and exceptions, see the Compatibility Notes section below.

### Extra Features

| **Feature** | **Supported** | **Notes & Documentation** |
| ----- | ----- | ----- |
| Delayed disk termination | ✅ Yes | Deleted VM disks are preserved for 48 hours (configurable), allowing recovery from accidental deletions. |
| StorPool VolumeCare tags | ✅ Yes | Automated snapshot policies per VM. [**--> StorPool Knowledge Base**](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/volumecare.html) |
| StorPool QoS Class tags | ✅ Yes | Per-VM performance policies. [**--> StorPool Knowledge Base**](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/qosclass.html) |
| Multiple StorPool Clusters | ✅ Yes | Different Clusters as separate datastores. |
| StorPool MultiCluster | ✅ Preview | Technology preview. [**--> StorPool Knowledge Base**](https://kb.storpool.com/admin_guide/multi/multicluster_intro.html) |
| Multiple OpenNebula instances | ✅ Yes | Multiple controllers sharing a single StorPool Cluster. |
| CDROM hotplug | ✅ Yes | Attach/detach CD images to running VMs. |
|  |  |  |

### Optional Features

| **Feature** | **Supported** | **Notes & Documentation** |
| ----- | ----- | ----- |
| VM disk snapshot limits | ✅ Optional | Disk snapshot limits with configurable thresholds. |
|  |  |  |
| Remote snapshot transfer | ✅ Optional | Optionally send a StorPool snapshot of VM disk or Image data to a secondary StorPool Cluster when deleted from OpenNebula (e.g., for regulatory compliance or law enforcement requirements). |
| Domain XML deploy tweaks | ✅ Optional | Additional libvirt customizations via deploy scripts (for options not yet exposed in OpenNebula templates) [**--> StorPool Knowledge Base**](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/deploy_tweaks.html) |
| VM checkpoint on StorPool | ✅ Optional | Option to keep the VM checkpoint files on StorPool block devices. |
| Atomic VM disk snapshots | ✅ Optional | Replace the default VM snapshot interface in OpenNebula  with a custom VM snapshot interface managable to do atomic disk snapshots. |

## Compatibility Notes

| **Item** | **Status** |
| ----- | ----- |
| **VM State Snapshots** | Not supported related to libvirt limitation with RAW disks. Alternative: reconfigure OpenNebula's 'VM snapshot' interface to perform atomic disk only snapshots via StorPool. |
| **OpenNebula Backups** | Only FULL backup mode is supported. Incremental backups are not available. Also require temporary space on the Hosts before transferring to the backup backend. |
| **Persistent Image Attributes** | Persistent images with SHAREABLE or IMMUTABLE attributes are not supported. |
| **Tested Platforms** | KVM hypervisor on current Alma Linux and Ubuntu, and other StorPool-supported Linux distributions. |
| **vTPM support** | limited compatibility due to the current upstream design/implementation \- the vault is stored on file, so it is not compatible StorPool snapshots and extra functionalities like volumecare and disaster recovery engine |

For current known issues visit the [StorPool Knowledge Base Known Issues Page](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/known_issues.html).

## Architecture Overview

At a high level, the integration works as follows:

* **StorPool Cluster**: A set of Linux servers run the StorPool distributed storage software. Their local drives are aggregated into a single pool of shared block storage with synchronous replication and linear scaling of capacity and performance.

* **OpenNebula Front-end**: The OpenNebula Front-end runs the StorPool datastore (DS\_MAD) and transfer manager (TM\_MAD) drivers. It communicates with the StorPool API management interface to create, clone, rename, and delete volumes corresponding to OpenNebula images and VM disks. The controller is running on a Highly Available VM managed by storpool\_havm service. 

* **OpenNebula Nodes (Hypervisors)**: KVM hypervisor nodes run the `storpool_block` initiator driver to access StorPool volumes as block devices. In **Hyper-Converged Infrastructure (HCI)** deployments, these nodes run both compute workloads and the StorPool storage service on the same physical hardware. VM disks are attached directly from StorPool to the hypervisors, with OpenNebula orchestrating which volumes attach to which Hosts.

When a VM is created, scaled, migrated, or terminated in OpenNebula, the driver translates these operations into volume and snapshot operations on StorPool. This keeps VM lifecycle management in OpenNebula while StorPool ensures the underlying storage is fast, resilient, and efficiently utilized.

For a deeper architectural description and reference designs, see the [**Hyperconverged Cloud Architecture with OpenNebula and StorPool**](https://cloud.storpool.com/hubfs/content-downloads/Hyperconverged-Cloud-Reference-Architecture-StorPool-and-OpenNebula.pdf) whitepaper.

## Requirements 

For detailed installation requirements, compatibility information, and version-specific prerequisites, see the [addon-storpool GitHub repository](https://github.com/OpenNebula/addon-storpool).

The integration requires a working StorPool Cluster. The OpenNebula Front-end requires network access to the StorPool management API and the StorPool Python 3 package. KVM Hosts require the `storpool_block` initiator. Image preparation Hosts require `qemu-img` and access to StorPool block devices. See the [driver requirements](https://github.com/OpenNebula/addon-storpool#requirements) and [StorPool system requirements](https://storpool.com/latest/StorPool-System-Requirements-latest.pdf).

Support for the add-on is included in the StorPool Storage license. Supported releases are governed by the [StorPool OpenNebula support lifecycle policy](https://kb.storpool.com/integrations/OpenNebula/support-lifecycle.html).

## Getting Started

| **Topic** | **Description** | **Link** |
| ----- | ----- | ----- |
| Installation and Upgrade | Step-by-step guide to installing the storpool\_block initiator and driver components | [Installation and Upgrade](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/installation.html) |
| OpenNebula Configuration | Required settings for oned.conf, TM\_MAD, DS\_MAD, and Datastore templates | [OpenNebula Configuration](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/one_configuration.html) |
| Support Life Cycles | Support policy for OpenNebula releases and the StorPool add-on | [Support Life Cycles](https://kb.storpool.com/storpool_integrations/OpenNebula/support_lifecycle.html) |

## Configuration examples

Example Image datastore:

```default
NAME = "StorPool IMAGE"

TYPE = "IMAGE_DS"

DS_MAD = "storpool"

TM_MAD = "storpool"

DISK_TYPE = "block"

BRIDGE_LIST = "node1 node2 node3"

Example System datastore:

NAME = "StorPool SYSTEM"

TYPE = "SYSTEM_DS"

TM_MAD = "storpool"

BRIDGE_LIST = "node1 node2 node3"
```

Replace the example hostnames with the environment’s bridge Hosts. Create each datastore with `onedatastore create <template_file>`, then create its corresponding StorPool volume template; the default naming pattern is `one-ds-<DATASTORE_ID>`. If `BRIDGE_LIST` is omitted, the Front-end requires working StorPool block access.

Follow the [configuration guide](https://kb.storpool.com/integrations/OpenNebula/docs/one_configuration.html) for driver registration, Host resource reservations, and datastore settings. For a datastore using another StorPool Cluster, [advanced configuration](https://kb.storpool.com/integrations/OpenNebula/docs/advanced_configuration.html) describes `SP_API_HTTP_HOST`, `SP_API_HTTP_PORT`, and `SP_AUTH_TOKEN`.

###   Advanced Features

| **Topic** | **Description** | **Link** |
| ----- | ----- | ----- |
| Advanced Configuration Variables | All tunables exposed via addon-storpoolrc: QoS, tags, monitoring, MultiCluster | [Advanced Configuration](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/advanced_configuration.html) |
| StorPool QoS Class Configuration | How to configure and apply Performance Tiers to your VMs | [QoS Configuration](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/qosclass.html) |
| StorPool VolumeCare | Setting up automated snapshot policies and retention tags | [VolumeCare](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/volumecare.html) |
| Deployment Tweaks | Optimizing KVM/Libvirt XML for maximum storage performance (iothreads, queues) | [Deployment Tweaks](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/deploy_tweaks.html) |

## Operations and Troubleshooting

For a failed image or VM disk operation:

1. Record the operation, timestamp, VM or image ID, datastore ID, and affected Host.  
2. Review the OpenNebula error and relevant logs: `/var/log/one/oned.log,` `/var/log/one/<VM_ID>.log and the addon-storpool logs in syslog/journal`.   
3. Check the [known issues](https://kb.storpool.com/integrations/OpenNebula/docs/known_issues.html). If the issue persists, contact StorPool Support with the collected information, logs, and software versions.

| **Topic** | **Description** | **Link** |
| ----- | ----- | ----- |
| StorPool Naming Convention | Understanding how OpenNebula images map to StorPool volumes | [Naming Convention](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/naming_convention.html) |
| Revert Volume from Snapshot | Procedures for rolling back data at the storage level | [Revert from Snapshot](https://kb.storpool.com/storpool_integrations/OpenNebula/storpool_revert_volume.html) |
| Copying a VM Between Clusters | Workflows for moving workloads across StorPool Clusters | [Copying VMs](https://kb.storpool.com/storpool_integrations/OpenNebula/vm_copy.html) |
| Live Resizing CPU and Memory | Recommended procedures and storage-related caveats | [Live Resizing](https://kb.storpool.com/storpool_integrations/OpenNebula/docs/resizeCpuMem.html) |
| Tips | Operational best practices for performance, troubleshooting, and day-to-day use | [Tips](https://kb.storpool.com/integrations/OpenNebula/docs/tips.html) |
| Known Issues | Continuously updated list of driver and integration issues with workarounds | [Known Issues](https://kb.storpool.com/integrations/OpenNebula/docs/known_issues.html) |

## Development and Support

The StorPool datastore driver for OpenNebula is open source under the Apache License 2.0.

This is a **Partner-Supported Storage Integration**. StorPool develops, maintains, and supports the integration drivers and StorPool components. OpenNebula supports the OpenNebula platform according to the customer’s OpenNebula Subscription. For storage or integration assistance, contact StorPool Support; see the [support lifecycle policy](https://kb.storpool.com/integrations/OpenNebula/support-lifecycle.html) for scope and eligibility.

| **Resource** | **Link** |
| ----- | ----- |
| **GitHub Repository** | [addon-storpool](https://github.com/OpenNebula/addon-storpool) |
| **Community** | [OpenNebula Forum](https://forum.opennebula.io/c/integration/33) |
| **Lead Developer** | Anton Todorov ([a.todorov@storpool.com](mailto:a.todorov@storpool.com))  |

---

*For the latest documentation and updates, visit the [StorPool Knowledge Base](https://kb.storpool.com/integrations/OpenNebula/index.html).*

