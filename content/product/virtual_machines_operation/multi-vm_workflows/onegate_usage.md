---
title: "OneGate Usage"
linkTitle: "OneGate"
date: "2025-02-17"
description:
categories:
pageintoc: "107"
tags:
weight: "4"
---

<a id="onegate-overview"></a>

<a id="onegate-usage"></a>

<!--# OneGate Usage -->

The OneGate component allows Virtual Machine guests to pull and push VM information from OpenNebula. Users and administrators can use it to gather metrics, detect problems in their applications, and trigger OneFlow elasticity rules from inside the VM.

For Virtual Machines that are part of a Multi-VM Application ([OneFlow Service]({{% relref "overview#oneflow-overview" %}})), they can also retrieve the Service information directly from OneGate and trigger actions to reconfigure the Service or pass information among different VMs.

## OneGate Workflow Explained

OneGate is a server that listens to http connections from the Virtual Machines. OpenNebula assigns an individual token to each VM instance and Applications running inside the VM use this token to interact with the OneGate API. This token is generated using VM information and signed with the owner User template attribute `TOKEN_PASSWORD`. This password can be changed by updating the User template, but tokens from existing VMs will not work anymore.

{{< image path="/images/onegate_arch.svg" alt="OneGate Architecture" align="center" width="90%" mb="20px" border="false" >}}

## OneGate Usage

First, the cloud administrator must configure and start the [OneGate server]({{% relref "../../operation_references/opennebula_services_configuration/onegate#onegate-conf" %}}).

### Set up the VM Template

Your VM Template must set the `CONTEXT/TOKEN` attribute to `YES`.

```none
CPU     = "0.5"
MEMORY  = "1024"

DISK = [
  IMAGE_ID = "0" ]
NIC = [
  NETWORK_ID = "0" ]

CONTEXT = [
  TOKEN = "YES" ]
```

or check the OneGate checkbox in Sunstone:

{{< image
  path="/images/onegate/light/vm-gate-token.png"
  pathDark="/images/onegate/dark/vm-gate-token.png"
  alt="OneGate VM token setting"
  align="center"
  width="90%"
  mb="20px"
>}}

When this Template is instantiated, OpenNebula will automatically add the `ONEGATE_ENDPOINT` context variable, and a `token.txt` will be placed in the [context cdrom]({{% relref "../virtual_machines/vm_templates#context-overview" %}}). This `token.txt` file is only accessible from inside the VM.

```none
...

CONTEXT=[
  DISK_ID="1",
  ONEGATE_ENDPOINT="http://192.168.0.1:5030",
  TARGET="hdb",
  TOKEN="YES" ]
```

### Using the OneGate Client inside the Guest VM

A Ruby client that implements the OneGate API is included in the official [OpenNebula context packages](https://github.com/OpenNebula/one-apps). This is a simple command line interface to interact with the OneGate server, it will handle the complex authentication and requests.

### OneGate Client Usage

Available commands and usage are shown with `onegate -h`.

With the appropriate policies implemented in the Service, these mechanisms allow Services to be self-managed, enabling self-configuration, self-healing, self-optimization, and self-protection.

#### Self-Awareness

There are several actions available to retrieve the information of the Virtual Machine and the Service it belongs to. A Virtual Machine can also retrieve information of other Virtual Machines that are part of the Service.

{{< alert title="Note" type="info" >}}
For a detailed version use the `--json` option and all the information will be returned in JSON format. Use the option `--extended` to increase the information retrieved.{{< /alert >}} 

##### Retrieving Information of the VM

Use the command `onegate vm show`. If no argument is provided, the information of the current Virtual Machine will be retrieved. Alternatively, a VM ID can be provided to retrieve the information of a specific Virtual Machine.

```default
$ onegate vm show
VM 8
NAME                : master_0_(service_1)
STATE               : RUNNING
IP                  : 192.168.122.23
```

{{< alert title="Note" type="info" >}}
Specifying a VM ID different of a different VM will only work to retrieve information of VMs in the same OneFlow Service or the same Virtual Router.{{< /alert >}} 

##### Retrieving information of the Service

Use the command `onegate service show`.

```default
$ onegate service show
SERVICE 1
NAME                : PANACEA service
STATE               : RUNNING

ROLE master
VM 8
NAME                : master_0_(service_1)

ROLE slave
VM 9
NAME                : slave_0_(service_1)
```

You can use the option `onegate service show --extended` to get all the information from Virtual Machines.

```default
$ onegate service show --extended
SERVICE 1
NAME                : PANACEA service
STATE               : RUNNING

ROLE master
VM 8
NAME                : master_0_(service_1)
STATE               : RUNNING
IP                  : 192.168.122.23


ROLE slave
VM 9
NAME                : slave_0_(service_1)
STATE               : RUNNING
```

##### Retrieving Information of the Virtual Router

Use the command `onegate vrouter show`.

```default
$ onegate vrouter show
VROUTER 0
NAME                : vr
VMS                 : 1
```

##### Retrieving Information of the Virtual Network

Use the command `onegate vnet show <ID>` to get the information of a Virtual Network.

```default
$ onegate vnet show 0
  VNET
  ID                  : 0
```

{{< alert title="Note" type="info" >}}
This option is only available for Virtual Routers and only for Virtual Networks related to that Virtual Router, i.e., only Virtual Networks attached or related somehow in the reservation hierarchy to another attached Virtual Network can be retrieved.{{< /alert >}} 

##### Updating the VM Information

The Virtual Machine can update its own information or that of other Virtual Machines of the Service. This information can be retrieved from any of the Virtual Machines.

For example, the master Virtual Machine can change the `ACTIVE` attribute from one Virtual Machine to another. Then, this information can be used to trigger any kind of action in the other Virtual Machine.

```default
$ onegate vm update 9 --data ACTIVE=YES
$ onegate vm show 9 --json
{
  "VM": {
    "NAME": "slave_0_(service_1)",
    "ID": "9",
    "STATE": "3",
    "LCM_STATE": "3",
    "USER_TEMPLATE": {
      "ACTIVE": "YES",
      "FROM_APP": "4fc76a938fb81d3517000003",
      "FROM_APP_NAME": "ttylinux - kvm",
      "LOGO": "images/logos/linux.png",
      "ROLE_NAME": "slave",
      "SERVICE_ID": "1"
    },
    "TEMPLATE": {
      "NIC": [

      ]
    }
  }
}
```

##### Deleting attributes from VM Information

The Virtual Machine can delete attributes from its own template or from other Virtual Machines in its Service.

For example, to erase the `ACTIVE` attribute from Virtual Machine 9 you can execute the following in any Service VM:

```default
$ onegate vm update 9 --erase ACTIVE
$ onegate vm show 9 --json
{
  "VM": {
    "NAME": "slave_0_(service_1)",
    "ID": "9",
    "STATE": "3",
    "LCM_STATE": "3",
    "USER_TEMPLATE": {
      "FROM_APP": "4fc76a938fb81d3517000003",
      "FROM_APP_NAME": "ttylinux - kvm",
      "LOGO": "images/logos/linux.png",
      "ROLE_NAME": "slave",
      "SERVICE_ID": "1"
    },
    "TEMPLATE": {
      "NIC": [

       ]
    }
  }
}
```

#### Self-Configuration

There are several actions to adapt the Service to a given situation. Actions on any of the Virtual Machines can be performed individually. Also, the size of the Service can be customized simply by specifying a cardinality for each of the Roles.

##### Performing actions on a VM

The following actions can be performed in any of the Virtual Machines of the Service.

* `onegate vm resume`
* `onegate vm stop`
* `onegate vm suspend`
* `onegate vm terminate`
* `onegate vm reboot`
* `onegate vm poweroff`
* `onegate vm resched`
* `onegate vm unresched`
* `onegate vm hold`
* `onegate vm release`

Check [this guide]({{% relref "../virtual_machines/vm_instances#vm-instances" %}}) to know more about states and operations.

##### Change Service cardinality

The number of Virtual Machines of a Service can be also modified from any of the Virtual Machines that have access to the OneGate Server.

```default
$ onegate service scale --role slave --cardinality 2
$ onegate service show
SERVICE 1
NAME                : PANACEA service
STATE               : SCALING

ROLE master
VM 8
NAME                : master_0_(service_1)
STATE               : RUNNING
IP                  : 192.168.122.23

ROLE slave
VM 9
NAME                : slave_0_(service_1)
STATE               : RUNNING
VM 10
NAME                : slave_1_(service_1)
STATE               : PENDING
```
