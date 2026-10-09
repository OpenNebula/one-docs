---
title: "Worker Profiles and Accelerators"
linkTitle: "Worker Profiles"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "3"
---

CPU, memory, disk and GPUs are settings of the worker VM template, not service inputs. Change the template before you create the service or before you add workers.

```shell
onetemplate update <WORKER_TEMPLATE_ID>
```

Each worker reports its CPUs, memory and GPUs to Slurm when it joins, so Slurm always uses the real size of the VM.

## CPU and Memory

The Marketplace worker template has 1 CPU and 1 GB of memory. Set values for `CPU`, `VCPU` and `MEMORY` in the template appropriately for your jobs. For CPU pinning and NUMA, refer to the documentation about [NUMA and CPU Pinning]({{% relref "product/cluster_configuration/hosts_and_clusters/numa" %}}).

## NVIDIA GPUs

The worker image includes the NVIDIA driver packages (`nvidia-driver-595-server-open`). The worker template has no attached GPU by default.

1. Add a GPU to the worker VM template, as a PCI device or a PCI profile of your Host. See [PCI Passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov" %}}). This example requests an NVIDIA H100 PCIe:

   ```text
   PCI = [
     VENDOR = "10de",
     DEVICE = "2331",
     CLASS  = "0302" ]
   ```

   The device ID and the PCI profiles depend on your Hosts. You can find the relevant parameters by running `lspci -nn | grep -i nvidia` on the Host's command line.

2. Create the service or add workers. Each worker counts its GPUs with `nvidia-smi` and starts `slurmd` with `Gres=gpu:<count>`.

3. Check from the controller:

   ```shell
   scontrol show nodes | grep Gres
   srun -N1 -n1 --gres=gpu:1 nvidia-smi -L
   ```

## InfiniBand

Workers for MPI jobs need an InfiniBand HCA in the VM template. Refer to [InfiniBand and High-Performance Networking]({{% relref "platform_services/slurm/management/infiniband" %}}).
