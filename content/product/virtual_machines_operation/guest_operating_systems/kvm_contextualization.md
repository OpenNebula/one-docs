---
title: "Contextualization"
date: "2025-02-17"
description:
categories:
pageintoc: "99"
tags:
weight: "2"
---

<a id="kvm-contextualization"></a>

<!--# Open Cloud Contextualization -->

OpenNebula provides a set of contextualization packages for different operating systems that integrates the VM guests with the OpenNebula services. The OpenNebula contextualization process allows to automatically:

* Configure guest networking and hostname settings.
* Set up user credentials for seamless VM access.
* Define the system timezone.
* Resize disk partitions as needed.
* Execute custom actions during boot.

All the OS appliances available in the [OpenNebula Marketplace](https://marketplace.opennebula.io) come with all the software pre-installed. If you want to build these images yourself, take a look at the [OpenNebula Apps project](https://github.com/OpenNebula/one-apps).

## Install the Context Packages

Additionally you can install the packages manually in any running VM guest, just grab the [latest version of the context packages for your operating system](https://github.com/OpenNebula/one-apps/releases) and install them (don’t forget to save your changes to the VM disk!).

## Using the Context Packages

Configuration parameters are passed to the contextualization packages through the `CONTEXT` attribute of the Virtual Machine. The most common attributes are network configuration, user credentials, and startup scripts. These parameters can be added by using either the CLI or the Sunstone Template wizard. Here is an example of the context section using the CLI:

```default
CONTEXT = [
    TOKEN = "YES",
    NETWORK = "YES",
    SSH_PUBLIC_KEY = "$USER[SSH_PUBLIC_KEY]",
    START_SCRIPT = "yum install -y ntpdate"
]
```

From the following links you can learn more about:

* [Network configuration](https://github.com/OpenNebula/one-apps/wiki/linux_feature#network-configuration).
* [Setup user credentials](https://github.com/OpenNebula/one-apps/wiki/linux_feature#user-credentials).
* [Execute scripts on boot](https://github.com/OpenNebula/one-apps/wiki/linux_feature#execute-scripts-on-boot).
* [Filesystem tuning](https://github.com/OpenNebula/one-apps/wiki/linux_feature#file-system-configuration).
* [Other OS settings and OneGate](https://github.com/OpenNebula/one-apps/wiki/linux_feature#other-system-configuration).

## Compatibility Overview

OpenNebula contextualization is designed to be highly flexible, supporting compatibility in both directions within the official release window.

There is a single OpenNebula contextualization package maintained on the OpenNebula Marketplace that always represents the newest version. This latest package is continuously updated to support a wide range of OpenNebula releases. See the [contextualization package on the OpenNebula Marketplace](https://marketplace.opennebula.io/appliance/6f7a1735-5b88-4667-a319-07ffe5e684ee), where the compatible releases are listed.

| **Scenario** | **Supported** | **Details** |
| ---- | ---- | ---- |
| Newer OpenNebula (e.g., v7.x) managing older Context (e.g., v6.x) | **Yes** | The upgraded `oned` daemon natively understands how to manage VMs running older contextualization packages. |
| Older OpenNebula (e.g., v6.x) deploying newer Context (e.g., v7.x) | **Yes** | You can run the latest contextualization package inside VM guests instantiated on older, compatible LTS infrastructure. |

## Contextualization Reference

The full list of options and attributes in the contextualization section are described in the [Virtual Machine Definition File reference section]({{% relref "../../operation_references/configuration_references/template#template-context" %}})
