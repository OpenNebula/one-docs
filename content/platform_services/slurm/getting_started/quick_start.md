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

This guide deploys a Slurm cluster with one controller and one worker, then runs a first job. You can create the service from Sunstone or from the CLI. Check the [Requirements]({{% relref "platform_services/slurm/getting_started/requirements" %}}) first.

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

In Sunstone, go to **Templates > Service Templates**, select **Service OneSlurm** and click the **Instantiate** button (the play icon). The wizard has four steps.

1. **General**. Keep the name or type your own, then click **Next**.

2. **Networks**. Keep **Existing** and select your Virtual Network in the table, then click **Next**.

3. **Service Inputs**. Click **Next** to keep the defaults. LDAP, InfiniBand and NFS stay disabled.
4. **Charter**. Click **Finish**.

### From the CLI

```shell
$ oneflow-template instantiate 'Service OneSlurm'
```

The command asks for the inputs, then for the network.

1. Press Enter on every input to keep the defaults.
2. For `Service`, choose `1` (existing network), then give the ID of your Virtual Network.

```shell
  * (Service) Service
    TYPE Existing(1), Create(2), Reserve(3). Press enter for default. 1
    VN ID. 2
ID: 233
```

The command prints the ID of the new service.

## Step 4. Wait for the Service

OneFlow creates the controller first. It creates the worker only when the controller reports that it is ready, so the service needs a few minutes to reach `RUNNING`.

In Sunstone, go to **Instances > Services** and open the service. The **Roles** tab shows the controller and the worker. Select both roles to see their VMs.

{{< image path="/images/slurm/oneslurm/light/oneslurm_service_roles.png"
   pathDark="/images/slurm/oneslurm/dark/oneslurm_service_roles.png"
alt="Roles tab of a running OneSlurm service with the controller and the worker" align="center" width="90%" mb="30px" >}}

From the CLI.

```shell
$ oneflow list
  ID USER     GROUP    NAME                  STARTTIME STAT
 233 oneadmin oneadmin Service OneSlurm  10/07 14:42:30 RUNNING
$ onevm list -f NAME~'service_233' -l NAME,STAT
NAME                          STAT
worker_0_(service_233)        runn
controller_0_(service_233)    runn
```

## Step 5. Run a First Job

1. Connect to the controller.

   ```shell
   $ onevm ssh <controller_vm_id>
   ```

2. Run `sinfo`. The worker must be in state `idle`.
3. Run a job on the worker with `srun -N1 hostname`. It prints the name of the worker.

{{< image path="/images/slurm/oneslurm/light/oneslurm_first_job.png"
   pathDark="/images/slurm/oneslurm/dark/oneslurm_first_job.png"
alt="Terminal on the controller with the output of sinfo and srun" align="center" width="70%" mb="30px" >}}

## Next Steps

* Add workers with `oneflow scale`, as shown in [Cluster Lifecycle Management]({{% relref "platform_services/slurm/management/cluster_lifecycle_management" %}}).
* Add shared users with [Identity Management]({{% relref "platform_services/slurm/management/identity_management" %}}).
* Add a shared `/home` with [Shared Storage]({{% relref "platform_services/slurm/management/shared_storage" %}}).
