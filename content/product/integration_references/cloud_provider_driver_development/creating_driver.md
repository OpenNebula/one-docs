---
title: "Developing a Provisioning Driver"
linkTitle: "Development"
date: "2025-06-05"
description:
categories:
pageintoc: "211"
tags:
weight: "3"
---

Here you will find a detailed step-by-step guide to creating a new provisioning driver for OpenNebula Formation. It covers all the necessary components starting with the basic configuration, infrastructure provisioned using Terraform, and post-deployment configuration handled by Ansible.

{{< alert title="Important" type="warning" >}}
Creating a driver requires working knowledge of both **Terraform** and **Ansible**, as they are fundamental to the provisioning and configuration workflows.
{{< /alert >}}

## Getting Started from Scratch

A driver in OneForm is a self-contained directory that bundles everything required to provision and configure infrastructure. It integrates with OpenNebula and OneForm to automate deployments across various cloud providers.

An OneForm driver must include at least the following elements:

- A `driver.conf` file: defines the basic metadata and UI configuration.
- A `terraform/` directory: contains all the Terraform logic used to provision resources.
- An `ansible/` directory: includes playbooks and templates to configure the infrastructure after it has been deployed.

Optionally, a driver contains the following directories if the cloud provider supports them:

- `ipam/`: lists optional scripts to manage IP address allocation and release. These scripts integrate with OpenNebula’s Virtual Network Manager to assign internal IPs to Virtual Machines dynamically.
- `elastic/`: implements logic to allocate and release public IP addresses from cloud providers. This is useful when creating public Virtual Networks that require internet-facing IPs.

This is an overview of a typical driver directory structure. It outlines basic elements like `driver.conf`, `terraform/`, and `ansible/`, as well as optional directories like `ipam/` and `elastic/`:

```default
mycloud/
├── driver.conf
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── validators.tf
├── ansible/
│   ├── ansible.cfg
│   ├── inventory.yaml
│   ├── site.yaml
│   └── templates/
│       └── mycluster.j2
├── ipam/               # optional
│   ├── allocate_address
│   ├── free_address
│   ├── get_address
│   ├── register_address_range
│   └── unregister_address_range
└── elastic/            # optional
    └── mycloud_vnm.rb
```

Each of these elements plays a specific role in the provisioning and configuration process. In the following sections, you will find about the required files to create your own custom driver.

## Basic Driver Information

The `driver.conf` file contains the basic metadata for your driver. It defines key information about the driver and how it is referenced across OneForm interfaces.

Here is a standard structure:

```yaml
name: 'MyCloud'
description: 'MyCloud Infrastructure Provider'
version: '1.0.0'
fireedge:
  logo: 'mycloud.png'
```

The table below summarizes the fields:

| Field           | Description                                                        |
| --------------- | ------------------------------------------------------------------ |
| `name`          | A short, unique name to identify the driver.                       |
| `description`   | A short description of the driver and its purpose.                 |
| `version`       | The driver version. Useful for tracking compatibility and updates. |
| `fireedge.logo` | Path to a logo image to be displayed in the Sunstone UI.           |

## Terraform Configuration

Every driver must include the following required files inside the Terraform subdirectory:

```default
mycloud/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── validators.tf
...
```

### main.tf

This is the main file that contains the core deployment logic. Here you define all the Terraform resources required by your infrastructure, such as Hosts, VPCs, subnets, and more.

Organize your code using modules because this improves readability and maintainability, especially in complex deployments. Create a module for each logical resource type, such as a cluster or a Host, within the `terraform/` directory and reference them from `main.tf` as depicted below:

```hcl
module "cluster" {
  source       = "./cluster"
  cidr_block   = var.cidr_block
}

module "host" {
  source             = "./host"
  oneform_hosts      = var.oneform_hosts
  instance_type      = var.instance_type
  instance_os_name   = var.instance_os_name
  instance_disk_size = var.instance_disk_size
  cloud_tags         = var.oneform_tags
}
```
<a id="variables"></a>
### variables.tf

Defines the input variables required to deploy the infrastructure. OneForm automatically parses each variable declared in `variables.tf`, using the `type` and `default` fields to build its user input interface. These user inputs are then exposed to the user when creating a Provision, and validated against the expected type. If no value is supplied, the `default` will be used.

Best Practices when working with `variables.tf`: 
- Use the prefix `instance_` for variables related to the Host configuration.
- Avoid to use the prefix `oneform_`, since it is reserved for variables that affect OneForm behavior (like `oneform_hosts`).
- **Always** add descriptions to each variable, as these descriptions are used to display the variables purpose to users who interact with the driver.

Input variables are automatically detected by OneForm to generate user inputs: 

```hcl
variable "cidr_block" {
  description = "CIDR block for the private network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "oneform_hosts" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

variable "instance_type" {
  description = "Instance type to use"
  type        = string
  default     = "standard.medium"
}

variable "instance_os_name" {
  description = "Operating system for the instance"
  type        = string
  default     = "ubuntu_2204"
}

variable "instance_disk_size" {
  description = "Root disk size"
  type        = number
  default     = 100
}

variable "oneform_tags" {
  description = "Tags to assign to the instances"
  type        = map(string)
  default     = {}
}
```

Here is an example of how OneForm interprets these variables and add them to a Provision body:

```json
{
  "name": "oneform_hosts",
  "description": "Number of instances to create",
  "type": "number",
  "default": 1,
  "match": {
    "type": "number",
    "values": {
      "min": 1,
      "max": 10
    }
  }
},
{
  "name": "instance_type",
  "description": "Instance type to use for the instance",
  "type": "string",
  "default": "c5.metal",
  "match": {
    "type": "list",
    "values": ["c5.metal", "m5.large"]
  }
}
```

While Terraform's native validation handles types and defaults, OneForm lets you define additional custom validation logic using the [`validators.tf`]({{% relref "creating_driver#validators" %}}) file.

### outputs.tf

This file defines the output values that Terraform returns once the infrastructure has been provisioned. These outputs are essential for OneForm to track and configure the deployed resources.

It is mandatory that the root module of the Terraform code returns at least two values per deployed instance inside an array named as `provisioned_hosts`:

- **`instance_id`**: the unique identifier of each Virtual Machine created by the cloud provider. OneForm uses this value internally to track the instance lifecycle, associate public IPs, and manage resource orchestration.
- **`instance_ip`**: the public (or private, depending on the deployment) IP address of the provisioned Host. It is used to establish an SSH connection so Ansible can perform configuration tasks on the Host.

If these outputs are not present, OneForm will not proceed with post-provisioning operations like inventory generation or system setup.

Here is a typical example:

```hcl
output "provisioned_hosts" {
  value = [
    for idx in range(length(module.host.id)) : {
      instance_id = module.host.id[idx]
      instance_ip = module.host.public_ip[idx]
    }
  ]
}
```

### provider.tf

This file defines Provider-specific configuration, usually including credentials and region parameters. This file is especially important since all variables declared in `provider.tf` are automatically parsed by OneForm and exposed as required inputs when a user creates a Provider.

In addition, OneForm automatically builds the `connection` section of the Provider body using these variables. This section is used internally when provisioning infrastructure so that the driver has access to the required authentication and configuration details.

Here is an example of a `provider.tf` file containing Terraform variables:

```hcl
terraform {
  required_providers {
    mycloud = {
      source  = "myorg/mycloud"
      version = "~> 1.0"
    }
  }
}

variable "api_key" {
  type        = string
  sensitive   = true
  description = "API key for the provider"
}

variable "region" {
  type        = string
  description = "Deployment region"
  default     = "us-central-1"
}

provider "mycloud" {
  api_key = var.api_key
  region  = var.region
}
```

From this file, OneForm automatically generates the following structure in the Provider body:

```json
{
  "name": "MyCloud",
  "description": "MyCloud Infrastructure Provider",
  "version": "1.0",
  "driver": "mycloud",
  "connection": {
    "api_key": "$api_key",
    "region": "$region"
  },
  "user_inputs": [
    {
      "name": "api_key",
      "description": "API key for the provider",
      "type": "string"
    },
    {
      "name": "region",
      "description": "Deployment region",
      "type": "string",
      "default": "us-central-1",
      "match": {
        "type": "list",
        "values": ["us-central-1", "us-central-2"]
      }
    }
  ]
}
```

Similar to `variables.tf`, you can extend the native validation by adding custom rules in the [`validators.tf`]({{% relref "creating_driver#validators" %}}) file.

<a id="validators"></a>
### validators.tf

This optional file allows you to define additional custom validations for user inputs. It uses Terraform local variables to describe constraints that go beyond the native validation defined in [`variables.tf`]({{% relref "creating_driver#variables" %}}).

Each validator is declared inside a `locals` block under the `validators` object. Every key inside `validators` must exactly match the name of a variable declared in [`variables.tf`]({{% relref "creating_driver#variables" %}}). This is how OneForm links the validator definition with the corresponding input.

Each validator supports different types:

- `list`: validates that the input is one of the predefined values. You must provide a `values` array of accepted strings.
- `number`: validates that the input falls within a numeric range. Use the `values` object with `min`, `max`, or both.
- `string`: validates that the input matches a given regular expression pattern. In this case, the `values` field must include a `regex` key.
- `map`: Allows for nested validations. You can use the `grouped_by` field to relate two variables; for example, a zone must belong to a selected region. The `values` field must then contain a map where keys are the parent variable’s values and each key maps to a list of valid child values.

Here’s a generic example:

```hcl
locals {
  validators = {
    # List validator example
    instance_type = {
      type   = "list"
      values = ["standard.small", "standard.medium", "standard.large"]
    }

    # Number range validator example
    oneform_hosts = {
      type   = "number"
      values = {
        min = 1
        max = 10
      }
    }

    # String validator with regex pattern
    hostname = {
      type   = "string"
      values = {
        regex = "^[a-z0-9-]{3,15}$"
      }
    }

    # Map validator with grouping logic
    region = {
      type   = "list"
      values = ["fr-par", "nl-ams", "pl-waw"]
    }

    zone = {
      type       = "map"
      grouped_by = "region"
      values = {
        fr-par = ["fr-par-1", "fr-par-2", "fr-par-3"]
        nl-ams = ["nl-ams-1", "nl-ams-2", "nl-ams-3"]
        pl-waw = ["pl-waw-1", "pl-waw-2", "pl-waw-3"]
      }
    }
  }
}
```

Each validator, when interpreted by OneForm, is added to the `match` section of the corresponding user input. This section defines the input validation rules that will be applied at runtime. Here's how the output looks for a variable like `instance_type`:

```json
{
  "name": "instance_type",
  "description": "Instance type to use",
  "type": "string",
  "default": "standard.medium",
  "match": {
    "type": "list",
    "values": ["standard.small", "standard.medium", "standard.large"]
  }
}
```

## Ansible

Ansible handles post-deployment configuration. A driver must include the following required files inside the Ansible subdirectory:

```default
mycloud/
├── ansible/
│   ├── ansible.cfg
│   ├── inventory.yaml
│   ├── site.yaml
│   └── templates/
│       └── mycluster.j2
...
```

### ansible.cfg

This file contains the base configuration needed for Ansible to interact correctly with OneForm and the dynamic inventory system.

The following configuration block should be used as-is. Although depending on the cloud provider or the target Host configuration, it might vary slightly. The only fields that require adjustments are:

- `inventory_plugins`: points to the path where the dynamic inventory plugin `opennebula_form` is located.
- `collections_path`: points to the directory where the OneDeploy Ansible collections are installed.

These paths may vary if OpenNebula has been installed in a custom location; if not, they can be left as their default values.

Below you have the recommended configuration:

```default
[defaults]
interpreter_python = auto
inventory_plugins  = /usr/share/one/ansible/plugins/inventory
roles_path         = /usr/share/one/one-deploy/roles:/usr/share/one/one-deploy/vendor/ceph-ansible/roles/
collections_path   = /usr/share/one/one-deploy/ansible_collections/
action_plugins     = /usr/share/one/one-deploy/vendor/ceph-ansible/plugins/actions/
callback_plugins   = /usr/share/one/one-deploy/vendor/ceph-ansible/plugins/callback/
filter_plugins     = /usr/share/one/one-deploy/vendor/ceph-ansible/plugins/filter/
library            = /usr/share/one/one-deploy/vendor/ceph-ansible/library/
module_utils       = /usr/share/one/one-deploy/vendor/ceph-ansible/module_utils/
callbacks_enabled  = profile_tasks
display_skipped_hosts = false
retry_files_enabled   = false
host_key_checking     = false
allow_world_readable_tmpfiles = true

[inventory]
host_pattern_mismatch = ignore

[privilege_escalation]
become = true
become_user = root

[ssh_connection]
pipelining = true
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

### site.yaml

This is the main playbook executed by Ansible and must exist in every driver. It is responsible for orchestrating all post-deployment configuration steps. The following are best practices: 

* To ensure proper integration with OpenNebula, configure this file to import the main playbook from OneDeploy (`opennebula.deploy.main`).
* Include the Host connectivity check at the beginning of the playbook. This step ensures that the remote servers are reachable and ready to be configured via SSH before proceeding with the rest of the playbook.
* Define and configure as many custom tasks or playbooks as needed before or after the OneDeploy execution. This flexibility allows for further configuration steps such as installing custom software, registering metadata, or performing health checks.

Besides OneDeploy, every task must include the `tags: always` tag to guarantee its execution. By default, OneForm only runs tasks tagged as `stage2` and `stage3` for post-provisioning steps, which are necessary for OneDeploy to function properly. These default tags can be customized in the OneForm configuration file located by default at `/etc/one/oneform-server.conf`.

```yaml
---
- name: Check hosts connectivity
  hosts: all
  gather_facts: false
  tasks:
    - name: Wait for hosts to be up
      ansible.builtin.wait_for_connection:
        timeout: 300
    - name: Wait for hosts to be reachable through SSH
      wait_for:
        host: "{{ ansible_host }}"
        port: 22
        state: started
        timeout: 60
  tags: always

# -------------------------------------------------------
# One-deploy playbooks
# -------------------------------------------------------

- ansible.builtin.import_playbook: opennebula.deploy.main

# -------------------------------------------------------
# Other playbooks (optional)
# -------------------------------------------------------

# - name: 'Example role'
#   hosts: all
#   tasks:
#     - name: 'Example task'
#       ansible.builtin.debug:
#         msg: 'Hello, world!'
#   tags: always

```

### inventory

OneForm uses a custom dynamic inventory plugin to configure Provisions. A dynamic inventory is a mechanism that generates Host information on-the-fly, based on live data from a source—in this case, a OneForm Provision.

In OneForm, dynamic inventories are powered by the `opennebula_form` plugin, which automatically connects to the OpenNebula backend and retrieves real-time deployment details for each provisioned Host.

These values are then injected into the Jinja2 inventory template defined in the `templates/` directory, allowing dynamic rendering of Host lists, variables, network mappings, and datastore references.

To enable this mechanism, you must declare a basic inventory source using the plugin:

```yaml
plugin: opennebula_form
```

### Jinja2 templates

Each file inside the `templates/` directory that uses Jinja2 syntax and includes the necessary metadata block (commented YAML at the top) is treated by OneForm as a separate deployment configuration type:

```yaml
{#
name: AWS SSH Cluster
description: It deploys a SSH cluster on AWS
fireedge:
  logo: "aws_ssh_cluster.png"
user_inputs:
  - name: instance_public_ips
    description: Number of public IPs to allocate
    type: number
    default: 0
    match:
      type: number
      values:
        min: 0
        max: 5
#}

---

# Jinja2 template content
```

This metadata is used by OneForm to define the Provision name, description and any custom user inputs. These user inputs can include validation rules using the same format shown earlier in the `variables.tf` and `validators.tf` sections.

In addition to defining how infrastructure is mapped into Ansible groups, these
templates define the objects that OneForm registers during provisioning. Set the
network definitions in `all.vars.vn`, the datastore definitions in
`all.vars.ds.config`, and, when required, the shared Host template in
`all.vars.shared.hosts.template`. OneForm derives its internal `one_objects`
structure from these sections.

For example, OneForm derives the following internal representation from these
template sections:

```json
{
  "name": "Example Cluster",
  "description": "Deploys a sample cluster",
  "user_inputs": [...],
  "one_objects": {
    "cluster": {},
    "hosts": [],
    "networks": [...],
    "datastores": [...]
  }
}
```

These values are parsed from the metadata and Jinja2 structure and become part of the internal representation of the Provision body within OneForm.

Here is an example of a Jinja2 inventory template that includes metadata and defines the full infrastructure mapping:

```jinja2
{#
name: Custom SSH Cluster
description: It deploys a SSH cluster
fireedge:
  logo: "ssh_cluster.png"
user_inputs:
  - name: instance_public_ips
    description: Number of public IPs to allocate
    type: number
    default: 0
    match:
      type: number
      values:
        min: 0
        max: 5
#}

---
---
all:
  vars:
    ansible_user: root
    one_version: {{ one.version }}
    vn:
      private_network:
        managed: true
        template:
          phydev: enp125s0
          vn_mad: vxlan
          vxlan_mode: evpn
          automatic_vlan_id: "yes"
          dns: 8.8.8.8
          gateway: 192.168.0.1
          ip_link_conf: nolearning=
          ar:
            - type: IP4
              ip: 192.168.0.100
              size: 100
      public_network:
        managed: true
        template:
          vn_mad: elastic
          bridge: br0
          netrole: public
          vxlan_mode: evpn
          vxlan_tep: dev
          ip_link_conf: nolearning=
    ds:
      mode: generic
      config:
        SYSTEM_DS:
          system_ds:
            id: {{ one.system_ds_id}}
            template:
              type: SYSTEM_DS
              tm_mad: ssh
              safe_dirs: /var/tmp /tmp
        IMAGE_DS:
          image_ds:
            id: {{ one.image_ds_id }}
            template:
              type: IMAGE_DS
              ds_mad: fs
              tm_mad: ssh
              safe_dirs: /var/tmp /tmp

frontend:
  hosts:
    f1: { ansible_user: root, ansible_host: {{ one.frontend_ip}} }

node:
  hosts:
    {% for node in one.nodes %}
    n{{ loop.index }}: { ansible_user: root, ansible_host: {{ node }} }
    {% endfor %}
```

#### Available Variables in Jinja2 Template

When a Jinja2 inventory template is rendered, it receives a structured dataset that includes all the information needed to generate the complete inventory. The most relevant structures are:

| Variable            | Description                                                                      |
| ------------------- | -------------------------------------------------------------------------------- |
| `id`                | ID of the Provision template.                                                    |
| `name`              | Name of the Provision template.                                                  |
| `description`       | Short description shown in the interface.                                        |
| `deployment_file`   | File name (without extension) used to identify the template inside `templates/`. |
| `fireedge`          | Optional UI metadata (e.g., logo).                                               |
| `user_inputs`       | Key-value pairs of inputs defined by the user or defaulted by the template.      |
| `state`             | Current lifecycle state of the Provision.                                        |
| `provider_id`       | ID of the associated Provider.                                                   |
| `registration_time` | UNIX timestamp of when the template was registered.                              |
| `one`               | Runtime deployment info for OpenNebula (see below).                              |

Inside the `one` object, the following fields are available:

| `one` Field    | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `version`      | OpenNebula version which Provision is configuring.                  |
| `frontend_ip`  | IP address of the OpenNebula frontend used for remote config.       |
| `nodes`        | List of Host IPs that have been provisioned and will be configured. |
| `network_ids`  | Array of IDs of the networks created during provisioning.           |
| `system_ds_id` | ID of the system datastore assigned to the Provision.               |
| `image_ds_id`  | ID of the image datastore assigned to the Provision.                |

This information is used to dynamically build inventories and infrastructure declarations.

Example of use:

```jinja2
one_version: {{ one.version }}
user_value: {{ user_inputs.custom_value }}
```

## Elastic and IPAM Integration

In addition to Terraform and Ansible logic, drivers include optional support for Elastic and IPAM drivers:

- **Elastic driver**: automates the request and release of public IP addresses from the cloud provider. This is useful for services that require access from the internet.
- **IPAM driver**: manages internal IP address allocation and ensures each VM receives a valid and unique IP during provisioning.

Both components are fully supported by OneForm and integrated into the networking phase.

Here is an example of how these drivers are added to the driver directory:

```default
mycloud/
│
├── ipam/
│   ├── allocate_address
│   ├── free_address
│   ├── get_address
│   ├── register_address_range
│   └── unregister_address_range
├── elastic/
│   └── mycloud_vnm.rb
...
```
