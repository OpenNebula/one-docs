---
title: "Bare-metal Instances Overview"
linkTitle: "Overview"
date: "2026-07-01"
description:
categories:
pageintoc: "82"
tags:
weight: "1"
---

Metal Instances extend OpenNebula workload operation to dedicated physical servers, allowing cloud users and operators to consume bare-metal resources through controlled, automated service workflows. They are designed for environments where workloads need direct access to the underlying hardware, predictable performance, strong isolation, or specialized acceleration devices.

This model is particularly useful for AI Factory, HPC, edge, sovereign cloud, and service-provider environments, where virtualized infrastructure may not always provide the required level of hardware control or performance. Metal Instances make it possible to manage these resources as part of a broader OpenNebula cloud, while preserving the benefits of automation, multi-tenancy, capacity control, and operational consistency.

This section provides guides for deploying and operating Bare Metal as a Service and related metal workload services with OpenNebula. The first guide of this section covers integration with the [NVIDIA Infra Controller (NICo)]({{% relref "product/virtual_machines_operation/metal_instances/bare_metal_nico/" %}}), enabling automated bare-metal lifecycle management for accelerated infrastructure, including systems built around NVIDIA networking, GPUs, and DPUs.

Future guides in this section will cover additional Metal Instance services and operational patterns as the OpenNebula bare-metal ecosystem expands.