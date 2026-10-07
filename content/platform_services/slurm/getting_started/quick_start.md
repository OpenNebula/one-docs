---
title: "Quick Start"
linkTitle: "Quick Start"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "3"
---

This guide deploys a Slurm cluster with one controller and one worker from the CLI, then runs a first job. Check the [Requirements]({{% relref "platform_services/slurm/getting_started/requirements" %}}) first.

## Step 1. Import the Appliance

Export `Service OneSlurm` from the OpenNebula Public Marketplace. This creates the two images, the two VM templates and the OneFlow service template.

```shell
$ onemarketapp export 'Service OneSlurm' 'Service OneSlurm' --datastore default
IMAGE
    ID: 34
    ID: 35
VMTEMPLATE
    ID: 62
    ID: 63
SERVICE_TEMPLATE
    ID: 64
```

## Step 2. Adjust the Templates (Optional)

The defaults are enough for a first cluster. For real workloads you can change, for example, the CPU and memory of the workers, or add a GPU.

```shell
$ onetemplate list                              # find the worker VM template
$ onetemplate update <worker_template_id>
$ oneflow-template update 'Service OneSlurm'
```

[Worker Profiles and Accelerators]({{% relref "platform_services/slurm/management/worker_profiles_and_accelerators" %}}) explains the common changes.

## Step 3. Create the Service

```shell
$ oneflow-template instantiate 'Service OneSlurm'
```

The command asks for the inputs, then for the network.

1. Press Enter on every input to keep the defaults. LDAP, InfiniBand and NFS stay disabled.
2. For `Service`, choose `1` (existing network), then give the ID of your Virtual Network.

```shell
  * (Service) Service
    TYPE Existing(1), Create(2), Reserve(3). Press enter for default. 1
    VN ID. 2
ID: 233
```

The command prints the ID of the new service.

## Step 4. Wait for the Service

```shell
$ oneflow list
  ID USER     GROUP    NAME                  STARTTIME STAT
 233 oneadmin oneadmin Service OneSlurm  10/07 14:42:30 RUNNING
```

OneFlow creates the controller first. It creates the worker only when the controller reports that it is ready, so the service needs a few minutes to reach `RUNNING`.

```shell
$ onevm list -f NAME~'service_233' -l NAME,STAT
NAME                          STAT
worker_0_(service_233)        runn
controller_0_(service_233)    runn
```

## Step 5. Run a First Job

Connect to the controller.

```shell
$ onevm ssh <controller_vm_id>
```

Check that the worker is in the cluster. Its state must be `idle`.

```shell
$ sinfo
PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
all*         up   infinite      1   idle worker-0--service-233
```

Run a job on the worker.

```shell
$ srun -N1 hostname
worker-0--service-233
```

## Next Steps

* Add workers with `oneflow scale`, as shown in [Cluster Lifecycle Management]({{% relref "platform_services/slurm/management/cluster_lifecycle_management" %}}).
* Add shared users with [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}).
* Add a shared `/home` with [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}).
