---
title: "Host Overcommitment"

description:
categories:
pageintoc: ""
tags:
weight: "3"
---

<a id="overcommitment"></a>

<!--# Host Overcommitment -->

Before allocating a VM to a Host, the Scheduler checks that the capacity requested by the VM fits in the available capacity of the Host. The overall number of VMs assigned to a Host can be controlled by:

> - Adjusting the total capacity announced by each Host.
> - Adjusting the capacity requested by the VM.

## Virtual Machine Capacity

The resource allocation of the VM is expressed with the following attributes:

> - `CPU` (Physical CPU): Represents the relative scheduling priority and weight given to the VM. **This field does not cap, throttle, or limit actual CPU cycles; it strictly defines priority during resource contention.**
>   - **Cgroups Shares**: The value entered in this field is automatically multiplied by 100, aligning it with the base allocation metric exposed by Linux `cgroups` for CPU shares. This calculated total is then subtracted from the host's **Allocated CPU** metric.
>   - **Priority Groups**: Utilizing values across different orders of magnitude allows administrators to define distinct priority groups among various VMs specifically for cases of host oversubscription. To leverage this setup, you must increase the total available **Allocated CPU** on the host, since the default maximum is bounded by the number of physical host CPUs multiplied by the base of 100.
>   - **Configuration Caps**: Note that weight values greater than 10,000 (e.g., 50,000) will be capped strictly at 10,000 within the VM's internal `cgroups` configuration. However, the host's **Allocated CPU** tracking counter will still deduct the full, un-capped calculation (e.g., 50,000 * 100).
> - `MEMORY`: The total memory allocated to the VM, expressed in MB.

### Understanding CPU vs. VCPU

It is important not to confuse the `CPU` allocation weight with `VCPU` (Virtual CPU):

* **CPU** dictates relative scheduling priority via hypervisor shares. It does not restrict a VM's access to CPU cycles if the host has idle resources. However, under heavy load or CPU contention, the hypervisor uses these weights to distribute resources proportionally. For example, a VM configured with `CPU=1.0` will receive twice the scheduling priority of a VM configured with `CPU=0.5`.
* **VCPU** represents the actual number of virtual processors that the Guest OS will see.

For example, a Host with eight processors has a default `TOTAL CPU=800` (8 physical processors * 100 base). This host can naturally accommodate eight VMs with a priority weight of `CPU=1` or 16 VMs with `CPU=0.5`. By leveraging these weights, you can establish clear priority hierarchies when packing more VMs onto an overcommitted Host.

## Host Capacity

The capacity of a Host is obtained by the monitor probes. You may alter the overall resources available to the VMs by reserving an amount of that capacity:

* Cluster-wise, by updating the Cluster template (e.g., `onecluster update`). All Hosts in the Cluster will reserve the same amount of capacity.
* Host-wise, by updating the Host template (e.g., `onehost update`). This value will override those defined at the Cluster level.

In particular, the following capacity attributes can be reserved:

| Attribute      | Description                                                |
|----------------|------------------------------------------------------------|
| `RESERVED_CPU` | (CPU priority shares) It will be subtracted from the TOTAL CPU. |
| `RESERVED_MEM` | (KB) It will be subtracted from the TOTAL MEM.             |

{{< alert title="Important" type="info" >}}
These values can be negative, in which case you would actually be increasing the overall capacity, thus overcommitting Host capacity.{{< /alert >}} 

The above values can be absolute, for example `RESERVED_MEM=-10240` will add 1GB of memory to the Host. Alternatively, they can be expressed in percentage terms, for example `RESERVED_MEM=-10%` will increase the memory of the Host by 10%.

Note also that the available storage capacity in a System Datastore is also checked before allocating a VM to it. However, you cannot overcommit this capacity.
