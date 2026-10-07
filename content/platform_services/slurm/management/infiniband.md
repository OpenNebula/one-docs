---
title: "InfiniBand and High-Performance Networking"
linkTitle: "InfiniBand"
date: "2026-10-07"
description: ""
categories:
tags:
type: docs
weight: "6"
---

OneSlurm can configure IPoIB on the workers and set Slurm for MPI jobs over InfiniBand. It is disabled by default.

## Before You Start

* Each worker VM has an InfiniBand HCA, attached by PCI passthrough in the worker VM template. See [PCI Passthrough]({{% relref "product/cluster_configuration/pci_passthrough_sriov" %}}).
* The InfiniBand fabric already has a subnet manager. OneSlurm does not configure it.

## What the Images Include

| Image | Packages |
|---|---|
| Worker | `rdma-core`, `infiniband-diags`, UCX from the Canonical DOCA PPA, Open MPI runtime |
| Controller | Open MPI development packages, to compile MPI programs |

Both images set the `memlock` limit to `unlimited`, which RDMA needs.

## Enable InfiniBand

| Parameter | Default | Description |
|---|---|---|
| `ONEAPP_SLURM_INFINIBAND_ENABLE` | `NO` | `YES` configures IPoIB on the workers and MPI settings in `slurm.conf` |
| `ONEAPP_SLURM_IPOIB_SUBNET` | empty | IPv4 subnet for IPoIB, for example `10.20.0.0/24`. Without a prefix, `/24` is used. Required when InfiniBand is enabled |

With InfiniBand enabled, the controller adds two lines to `slurm.conf`.

| Setting | Effect |
|---|---|
| `MpiDefault=pmix` | `srun` and `sbatch` use PMIx without `--mpi=pmix` |
| `PropagateResourceLimitsExcept=MEMLOCK` | Jobs keep the `memlock` limit of the worker |

## IPoIB Addresses

Each worker builds its IPoIB address from the subnet and its Ethernet address. It copies the last octets of the Ethernet address, as many as the prefix leaves free.

| IPoIB subnet | Worker Ethernet IP | Worker IPoIB address |
|---|---|---|
| `10.20.0.0/24` | `172.16.0.11` | `10.20.0.11/24` |
| `10.20.0.0/16` | `172.16.5.42` | `10.20.5.42/16` |
| `10.0.0.0/8` | `172.16.5.42` | `10.16.5.42/8` |

* Only `/8`, `/16` and `/24` are valid.
* The copied octets must be different on each worker. Otherwise two workers get the same IPoIB address.
* The copied octets cannot be all `0` or all `255`.
* The worker writes the address to `/etc/netplan/90-oneslurm-ipoib.yaml`.

Slurm itself stays on the Ethernet network. Controller discovery, Munge, LDAP and `slurmd` do not use IPoIB. MPI and RDMA traffic can use InfiniBand.

## Check InfiniBand

On a worker.

```shell
$ ibstat
$ ibv_devinfo
$ ip addr show ib0
$ ucx_info -d | grep mlx5
```

On the controller.

```shell
$ mpicc --version
$ scontrol show config | grep -E 'MpiDefault|PropagateResourceLimitsExcept'
$ srun -N2 hostname
```

## Run an MPI Job

Compile on the controller and run with `srun`.

```shell
$ mpicc mpi_program.c -o mpi_program
$ srun -N2 ./mpi_program
```
