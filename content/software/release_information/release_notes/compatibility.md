---
title: "Compatibility Guide"
date: "2026-07-24"
description:
categories:
pageintoc: "247"
tags:
weight: "5"
---

<a id="compatibility"></a>

<!--# Compatibility Guide -->

This guide is aimed at OpenNebula 7.4.x users and administrators who want to upgrade to the latest version. The following sections summarize the new features and usage changes that should be taken into account or could perhaps cause confusion. You can check the upgrade process in the [corresponding section]({{% relref "software/upgrade_process/" %}}). If upgrading from previous versions, please make sure you read all the intermediate versions’ Compatibility Guides for possible pitfalls.

## QEMU Guest Agent Monitoring Commands

The KVM monitoring probes no longer run `virsh` to query the guest agent; the commands defined in `/var/lib/one/remotes/etc/im/kvm-probes.d/guestagent.conf` are now sent through the libvirt Ruby bindings. The syntax of the file is preserved, but [custom commands]({{% relref "kvm_driver#custom-qemu-guest-agent-commands" %}}) are only accepted in the following form:

```default
<domain> '<json>' [--timeout <seconds>] [| <shell command>]
```

The JSON must be enclosed in single quotes. Other `virsh qemu-agent-command` options or shell constructs are not supported. If you have defined custom commands, review them after the upgrade.
