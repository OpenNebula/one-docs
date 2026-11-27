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

<a id="sles15-ruby34"></a>

## Ruby 3.4 on SUSE Linux Enterprise Server 15

OpenNebula packages for SUSE Linux Enterprise Server 15 now run on Ruby 3.4 (`ruby3.4` package from the Basesystem module, available since SP7) instead of the distribution default Ruby 2.5. The new Ruby is installed automatically as a package dependency and all OpenNebula services, commands, and drivers use it, so no action is required.

The system default `/usr/bin/ruby` remains Ruby 2.5. Custom Ruby scripts, hooks, or drivers that load the OpenNebula Ruby libraries must be run with `/usr/bin/ruby.ruby3.4`.
