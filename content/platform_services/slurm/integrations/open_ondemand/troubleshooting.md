---
title: "Troubleshooting and Limitations"
linkTitle: "Troubleshooting"
date: "2026-10-14"
description: "Solve common problems of the portal and learn its known limitations."
categories:
tags:
type: docs
weight: "5"
aliases:
  - /solutions/integration_blueprints/open_ondemand/monitoring_and_troubleshooting/
---

## Troubleshooting

The following table lists common problems and how to solve them:

| **Problem** | **What to do** |
|---------|------------|
| The VM shows `OOD_ERROR` | Fix the value or the service named in the message, then reboot the VM. Full log in `/var/log/one-appliance/configure.log`. |
| The browser does not open the portal | Check that the VM shows `READY=YES` and that your network reaches the IP of `OOD_URL` on port 443. Logs: `journalctl -u apache2 -u ondemand-dex`. |
| Login fails with the right password | The user is not under `ou=People`, or LDAP does not answer. Test in the VM with `ldapsearch -x -H <URL> -b ou=People,<base DN> uid=<user>`. For `slurm.local`, the base DN is `dc=slurm,dc=local`. |
| Home directory not found | Create the home directory of the user, then click **Restart Web Server** on that page. |
| Active Jobs is empty, or `Permission denied` in Submit or the terminal | Click **Help -> Restart Web Server**. This adds the key of the user to `~/.ssh/authorized_keys` again. Logs: `journalctl -t ood-prehook`. |
| System Status shows an error page | A controller does not answer. That Cluster shows no jobs, and the Job Composer and the terminal show an SSH error. Everything works again when the controller is back. |
| Pages load forever with no message | The NFS server does not answer. The portal works again by itself when NFS is back. Meanwhile, use the VM console in Sunstone, because SSH to the VM can also hang. |

## Known Limitations

| **Area** | **Limitation** | **What to do** |
|------|------------|------------|
| Files | Uploads are limited to 256 MiB. | Copy bigger files with `scp` or `rsync` to a Cluster controller, which has the same home. |
| Terminal | The terminal closes when the page reloads. | Run long work under `tmux` or `screen` on the controller. |
| Job Composer | If the first visit is a direct link to `/pun/sys/myjobs/`, it creates an empty database and shows error 500 from then on. | Open it the first time from the **Jobs** menu. To fix it, delete `~/ondemand/data/sys/myjobs/production.sqlite3` of that user (only if the file has no tables) and open the Job Composer from the menu. |
| Job Composer | **New Job -> From Template** creates a job without a script. | Open **Job Options**, select the script and click **Save**. |
| Job states | OneSlurm has no Slurm accounting, so a cancelled job shows `Completed` in Active Jobs and `Failed` in the Job Composer. | Check the real state with `scontrol show job <ID>` or in the output file of the job. |
| Project Manager | Deleting a project only removes it from the list. The files stay. | Delete the files in **Files**. |
| Two portals | With two portals on the same homes, the Job Composer fails with error 500 when a user opens it on both at the same time. | Use one portal for each NFS home export. |
| New Clusters | A new Cluster needs a running controller. If it does not answer, the configuration stops with `OOD_ERROR`. | Start the controller first. Clusters the portal already knows can be stopped for maintenance. |
