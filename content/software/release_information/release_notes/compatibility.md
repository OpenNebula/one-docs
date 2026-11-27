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

## Ruby 3.3 on AlmaLinux 9 and RHEL 9

The OpenNebula packages for AlmaLinux 9 and RHEL 9 are now built for Ruby 3.3 instead of the distribution default Ruby 3.0. Ruby 3.3 comes from the `ruby:3.3` module stream of the AppStream repository, which has to be enabled before the installation or upgrade of the Front-end and the hypervisor Nodes:

```shell
dnf -y module enable ruby:3.3
```

Take into account the following:

* The module stream replaces the system Ruby, i.e., `/usr/bin/ruby` is Ruby 3.3 after the upgrade. Review any other Ruby software running on the Front-end and the hypervisor Nodes.
* The upgrade fails on unresolved dependencies if the stream is not enabled, see the [upgrade guide]({{% relref "upgrading_single#upgrade-single" %}}).
* Custom drivers, hooks and other integrations running on the Front-end need to be compatible with Ruby 3.3.
* The hypervisor Nodes need Ruby 3.3 as well, the Node packages depend on the bundled Ruby gems built for it.
