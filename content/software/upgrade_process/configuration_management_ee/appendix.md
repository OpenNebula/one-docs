---
title: "Appendix - List of Configurations"
date: "2025-02-17"
description:
categories:
pageintoc: "255"
tags:
weight: "5"
---

<!-- The table in this document is generated automatically using a Hugo shortcode from a 
CSV file: /assets/tables/config_files.csv. Modify the CSV in order to update the table.

A helper script /scripts/compare_config_files.py exists to compare the contents of the 
CSV with the config files of an OpenNebula installation for audit purposes.  -->

The following table describes all configuration files and their type from the following directories:

- `/etc/one/`
- `/var/lib/one/remotes/`

These files can be managed using the `onecfg` tool, refer to the [onecfg documentation]({{% relref "software/upgrade_process/configuration_management_ee/usage/" %}}) for more details:

{{< config-files-table >}}
