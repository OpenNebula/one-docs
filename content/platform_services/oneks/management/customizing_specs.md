---
title: "Kubernetes Cluster Profiles Customization"
linkTitle: "Profiles Customization"
date: "2026-05-12"
description:
categories:
tags:
weight: "4"
type: docs
---

OpenNebula Elastic Kubernetes Service (OneKS) defines Kubernetes deployment profiles exposed to users through families, flavours, dependencies, and user inputs. Administrators can customize these specs to change the capacities offered by each flavour, expose new input parameters, update supported Kubernetes versions, or tune the dependencies used during provisioning.

Profiles are used by both control-plane and node-group profiles. By default, the OneKS profile configuration files are located in the following paths:

```default
/var/lib/one/oneks/controlplanes/general/controlplane.conf
/var/lib/one/oneks/nodegroups/general/nodegroup.conf
```

After changing a profile configuration, restart the OneKS service so the updated profile definition is loaded. For service commands, see [Service Management]({{% relref "platform_services/oneks/management/configuration/#service-management" %}}).

## Example Spec

The following example shows a control-plane spec for the `general` family profile:

```yaml
---
name: "General Purpose"
description: "Cluster configuration for general workloads"
family: "general"
supported_k8s_versions:
  - v1.33.7
  - v1.34.2

dependencies:
  - object: seed_vm
    options:
      creation_timeout: 2000
      destroy_on_running: true
      appliance_id: c3ecb387-e726-49fe-975d-fa39c6d40d05
  - object: cluster_router
    options:
      creation_timeout: 500
      destroy_on_running: false

user_inputs:
  - name: count
    description: "Number of Control Plane nodes"
    type: number
    mandatory: true
    match:
      type: number
      values:
        min: 1
  - name: cpu
    description: "CPU cores per Control Plane node"
    type: number
    mandatory: true
    match:
      type: number
      values:
        min: 1
  - name: vcpu
    description: "Number of VCPUs per Control Plane node"
    type: number
    mandatory: true
    match:
      type: number
      values:
        min: 1
  - name: memory
    description: "RAM in MB per Control Plane node"
    type: number
    mandatory: true
    match:
      type: number
      values:
        min: 2048
  - name: disk_size
    description: "Disk size in MB per Control Plane node"
    type: number
    mandatory: true
    match:
      type: number
      values:
        min: 4096

flavours:
  standalone:
    label: "Single-Node Control Plane"
    description: |
      <p>Single Control Plane node deployment.<br>Suitable for development, evaluation, and non-critical workloads.</p>
    override_defaults: false
    defaults:
      count: 1
      cpu: 2
      vcpu: 2
      memory: 4096
      disk_size: 16384

  ha:
    label: "Highly Available Control Plane"
    description: |
      <p>Three-node Control Plane deployment with built-in redundancy.<br>Suitable for production and other environments that require higher availability.</p>
    override_defaults: false
    defaults:
      count: 3
      cpu: 2
      vcpu: 2
      memory: 4096
      disk_size: 16384
```

## Spec Sections

| **Section**                    | **Purpose** |
|----------------------------|---------|
| `name`                     | Human-readable profile name shown to users. |
| `description`              | Short description of the profile purpose. |
| `family`                   | Family identifier used when selecting the profile. |
| `supported_k8s_versions`   | Kubernetes versions that can be deployed with this family. |
| `dependencies`             | Internal resources required by the profile, such as `seed_vm` or `cluster_router`. |
| `user_inputs`              | Parameters accepted from users or profile defaults. |
| `flavours`                 | Named deployment choices exposed to users. |
| `metadata`                 | Extra metadata consumed by UI or integration layers. |

## Changing Flavour Capacity

To modify the capacity offered by a flavour, edit its `defaults` block. These values are applied when a user selects that flavour.

For example, to make the `standalone` control-plane flavour larger:

```yaml
flavours:
  standalone:
    label: "Single-Node Control Plane"
    override_defaults: false
    defaults:
      count: 1
      cpu: 4
      vcpu: 4
      memory: 8192
      disk_size: 32768
```

Common capacity defaults are:

| **Default**       | **Description** |
|---------------|-------------|
| `count`       | Number of nodes created for the flavour. |
| `cpu`         | CPU cores assigned to each node. |
| `vcpu`        | Virtual CPUs assigned to each node. |
| `memory`      | RAM in MB assigned to each node. |
| `disk_size`   | Disk size in MB assigned to each node. |

For node-group specs, the same pattern is used to define worker sizes such as `small`, `medium`, or `large`.

## Controlling User Overrides

The `override_defaults` attribute controls whether users can override the defaults defined by a flavour:

- When set to `false`, the flavour defaults take precedence and users can select the flavour, but they cannot change its default values.
- When set to `true`, user-provided input values can override the flavour defaults.

For example, to let users select the `ha` flavour but customize capacity values:

```yaml
flavours:
  ha:
    label: "Highly Available Control Plane"
    override_defaults: true
    defaults:
      count: 3
      cpu: 2
      vcpu: 2
      memory: 4096
      disk_size: 16384
```

Use `override_defaults: false` for fixed, administrator-controlled offerings. Use `override_defaults: true` when the flavour should provide defaults but still allow user customization.

## Adding New User Inputs

Add new inputs under `user_inputs`. Each input defines the name, description, type, whether it is mandatory, and the validation rule applied to values.

Example input:

```yaml
user_inputs:
  - name: extra_disk_size
    description: "Extra disk size in MB per node"
    type: number
    mandatory: false
    match:
      type: number
      values:
        min: 0
        max: 1048576
```

Then reference the input from a flavour default if the profile templates support it:

```yaml
flavours:
  large:
    label: "Large Worker Nodes"
    override_defaults: true
    defaults:
      count: 3
      cpu: 8
      vcpu: 8
      memory: 16384
      disk_size: 65536
      extra_disk_size: 0
```

{{< alert title="Important" type="warning" >}}
Adding an input only exposes and validates the value. The underlying profile templates or scripts must also consume that input for it to affect the deployed infrastructure.
{{< /alert >}}

## Input Validation

The `match` block defines validation rules. Numeric inputs commonly use minimum and maximum values:

```yaml
match:
  type: number
  values:
    min: 1
    max: 10
```

Use validation to keep exposed options within the capacity and topology limits supported by your environment.

## Changing Supported Kubernetes Versions

The `supported_k8s_versions` list controls which Kubernetes versions can be selected for a family:

```yaml
supported_k8s_versions:
  - v1.33.7
  - v1.34.2
```

Add a version only after verifying that the corresponding images, templates, bootstrap logic, CAPONE integration, and profile templates support it.

## Customizing Dependencies

The `dependencies` section defines auxiliary resources required by the profile. Control-plane specs commonly use:

| Dependency          | Purpose |
|---------------------|---------|
| `seed_vm`           | Temporary VM used to bootstrap the control plane. |
| `cluster_router`    | Routing component used to connect the Cluster to the required networks. |

Example:

```yaml
dependencies:
  - object: seed_vm
    options:
      creation_timeout: 2000
      destroy_on_running: true
      appliance_id: c3ecb387-e726-49fe-975d-fa39c6d40d05
```

Common dependency options include:

| Option                 | Description |
|------------------------|-------------|
| `creation_timeout`     | Time allowed for the dependency to become ready. |
| `destroy_on_running`   | Whether the dependency resource is removed when the group reaches `RUNNING`. |
| `appliance_id`         | Marketplace appliance ID used by the Seed VM dependency. |
| `appliance_ds`         | Optional image datastore used for automatic appliance import. Overrides the default datastore (`default`, ID `1`). |

For more information about the Seed VM appliance, see [Automatically Generated Resources]({{% relref "platform_services/oneks/getting_started/basic_configuration/#automatically-generated-resources" %}}).

## Updating Labels and Descriptions

Use `label` and `description` to control how flavours are presented to users:

```yaml
flavours:
  gpu:
    label: "GPU Worker Nodes"
    description: |
      <p>Worker nodes intended for GPU-enabled workloads.</p>
    override_defaults: false
    defaults:
      count: 1
      cpu: 8
      vcpu: 8
      memory: 32768
      disk_size: 131072
```

Descriptions can contain simple HTML when they are rendered by Sunstone.

## Validation Checklist

After customizing a spec:

* Validate the YAML syntax.
* Confirm that every new user input is consumed by the relevant templates or scripts.
* Confirm that each flavour has defaults for the required inputs.
* Confirm that resource sizes match the capacity of the target OpenNebula Hosts and datastores.
* Confirm that dependency options are valid.
* Restart the OneKS service.
* Create a test K8s Cluster or node group using the modified family and flavour.
* Monitor the lifecycle logs until the resource reaches `RUNNING`.
