---
title: "Compatibility Guide"
date: "2025-02-17"
description:
categories:
pageintoc: "247"
tags:
weight: "5"
---

<a id="compatibility"></a>

<!--# Compatibility Guide -->

This guide is aimed at OpenNebula 7.2.x users and administrators who want to upgrade to the latest version. The following sections summarize the new features and usage changes that should be taken into account or could perhaps cause confusion. You can check the upgrade process in the [corresponding section](../../upgrade_process). If upgrading from previous versions, please make sure you read all the intermediate versions’ Compatibility Guides for possible pitfalls.

Visit the [Features list](../../../getting_started/understand_opennebula/opennebula_concepts/key_features) and the [What’s New guide](whats_new#whats-new) for a comprehensive list of what’s new in OpenNebula 7.4.

## Daemon Logs Are No Longer Truncated on Start

The OpenNebula daemons (`oned`, the monitor, and the scheduler) now open their log files in append mode instead of truncating them on start. Previously the log was reset on every service start and relied on the forced log rotation (see below) to preserve its contents; with that rotation no longer triggered on start, restarts would otherwise have discarded the existing log. No action is required.

## Log Rotation No Longer Triggered on Service Start

OpenNebula systemd services no longer force a log rotation on start. The `ExecStartPre=-/usr/sbin/logrotate -f ...` directive has been removed from all services (`opennebula`, `opennebula-hem`, `opennebula-flow`, `opennebula-gate`, `opennebula-form`, `opennebula-fireedge`, and `opennebula-ks`). Logs under `/var/log/one/` are still rotated by the files in `/etc/logrotate.d/` via the system's own `logrotate` timer/cron, so no action is required.

To keep the old behavior for a service, add a systemd drop-in, e.g. for `opennebula`:

```
# /etc/systemd/system/opennebula.service.d/logrotate.conf
[Service]
ExecStartPre=-/usr/sbin/logrotate -f /etc/logrotate.d/opennebula -s /var/lib/one/.logrotate.status
```

Then run `systemctl daemon-reload`.
