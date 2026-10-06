---
title: "Open OnDemand"
linkTitle: "Open OnDemand"
date: "2026-10-06"
description: "Give the users of your Slurm clusters a web portal to manage files, submit jobs and open a terminal."
categories:
tags:
type: docs
weight: "1"
aliases:
  - /solutions/integration_blueprints/open_ondemand/
  - /solutions/integration_blueprints/open_ondemand/overview/
  - /solutions/integration_blueprints/open_ondemand/architecture/
  - /solutions/integration_blueprints/open_ondemand/quick_start/
  - /solutions/integration_blueprints/open_ondemand/configuration/
  - /solutions/integration_blueprints/open_ondemand/operations/
  - /solutions/integration_blueprints/open_ondemand/monitoring_and_troubleshooting/
---

[Open OnDemand](https://openondemand.org/) is a web portal for HPC users, developed by the Ohio Supercomputer Center. The Open OnDemand appliance runs the portal in one VM for your OneSlurm clusters. Users sign in with their LDAP account and use a web browser to manage their files, submit and watch jobs, and open a terminal on a cluster.

The portal runs no Slurm of its own. It sends the Slurm commands of each user to the controller of a cluster over SSH. The portal and the clusters use the same LDAP directory and the same NFS export for `/home`, so a user has the same account and the same files in the portal and on every cluster. One portal can serve several OneSlurm clusters.

The appliance is available in the [OpenNebula Public Marketplace](https://marketplace.opennebula.io/appliance/d3c8ea14-f6f0-455c-8a41-6129affa9a0e). It uses Ubuntu 26.04 LTS and Open OnDemand 4.2.

## How It Works

When the VM boots, the appliance does these steps in order.

1. It checks the four inputs of the wizard.
2. It mounts the NFS export on `/home`.
3. It reads the users from the LDAP directory, with SSSD for the system and with Dex for the login page.
4. It creates a self-signed certificate for the IP address of the VM.
5. It writes one Open OnDemand cluster file for each Slurm cluster and saves the SSH host key of each controller.
6. It starts the portal and publishes its URL in OneGate.

The first time a user opens the portal, the appliance creates an SSH key for that user in `~/.ssh/id_ed25519_portal` and adds it to `~/.ssh/authorized_keys` in the same home. The key is accepted only from the IP addresses of the portal. The controllers read this home from the NFS export, so the portal can run `sbatch`, `squeue` and `scancel` on them as the user. The terminal in the portal uses the same key.

The portal runs each user's programs as that user's Unix account, with the same UID and the same home as on the clusters. A user cannot read the files or cancel the jobs of another user.

## Requirements

* One or more OneSlurm clusters in `RUNNING` state. The portal needs the IP address of the controller of each cluster. The first time the portal is configured with a cluster, its controller must answer on the SSH port, because the portal saves the SSH host key of the controller.
* The LDAP server of the clusters. The portal needs its URL with `ldap://` and its domain, the same value as `ONEAPP_LDAP_DOMAIN` in OneSlurm (by default `slurm.local`). The domain can also be a base DN such as `dc=example,dc=org`. The portal has no bind user, so the LDAP server must allow anonymous search under `ou=People`. The LDAP server of OneSlurm allows it. The users must be `posixAccount` entries under `ou=People`, as in the LDAP server of OneSlurm.
* The NFS export with the homes of the users, the same value as `ONEAPP_SLURM_NFS_HOME` in OneSlurm, for example `10.0.0.10:/export/home`. The appliance mounts it with NFS version 4, and the export can use `root_squash`. The NFS server must allow the IP address of the portal in the export.
* A home on the NFS export for each user, owned by the user and with mode `700`. The administrator creates the users in LDAP and their homes.
* A virtual network that reaches the controllers, the LDAP server and the NFS server. The portal uses the IPv4 address of its first NIC, so the users must reach that address with a web browser.
* [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate" %}}), reachable from the network of the VM, so that the appliance can publish the URL of the portal and its errors.

The default VM has 2 vCPU, 4 GB of memory and a 10 GB disk. Each active user needs about 200 MB of memory on the portal, measured with six users. Add memory for more users at the same time.

## Deploy the Portal

Import the appliance from the OpenNebula Public Marketplace into a datastore. In Sunstone, go to **Storage > Apps**, select **Open OnDemand**, click **Import** and choose the image datastore. With the CLI, run this command on the Front-end.

```shell
$ onemarketapp export "Open OnDemand" "Open OnDemand" --datastore default
```

This creates the image and the VM template **Open OnDemand**. In Sunstone, go to **Templates > VM Templates**, select **Open OnDemand** and click **Instantiate**. Give the VM a name and click **Next**.

In **User inputs**, fill in the three tabs. In the **LDAP** tab, enter the URL of the LDAP server of the clusters, for example `ldap://10.0.0.20`, and its domain or base DN. The default domain is `slurm.local`, the default of OneSlurm.

{{< image path="/images/slurm/open_ondemand/ood_wizard_ldap.png"
alt="LDAP tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

In the **Home** tab, enter the NFS export with the homes, for example `10.0.0.10:/export/home`.

{{< image path="/images/slurm/open_ondemand/ood_wizard_home.png"
alt="Home tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

In the **Slurm** tab, enter the clusters, one per line, as `name:IP`, for example `cpu:10.0.0.20`. The name is the one users see in the portal. It starts with a letter or a digit, has up to 63 letters, digits, `-` and `_`, and must be unique. The IP address must be IPv4. Each cluster must use the same LDAP server and the same `/home` as the portal.

{{< image path="/images/slurm/open_ondemand/ood_wizard_slurm.png"
alt="Slurm tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

Click **Next**. In **Advanced options**, open the **Network** tab, click **Attach NIC** and select the virtual network of the clusters. Then click **Finish**.

{{< image path="/images/slurm/open_ondemand/ood_wizard_network.png"
alt="Network tab of the Open OnDemand wizard with the NIC of the clusters" align="center" width="90%" mb="20px" >}}

With the CLI, pass the same values with `--user-inputs`. Separate the clusters with spaces.

```shell
$ onetemplate instantiate "Open OnDemand" --name open-ondemand --nic <network> \
    --user-inputs "ONEAPP_LDAP_SERVER_URL=ldap://10.0.0.20,ONEAPP_LDAP_SERVER_DOMAIN=slurm.local,ONEAPP_HOME_NFS_EXPORT=10.0.0.10:/export/home,ONEAPP_SLURM_CLUSTERS_LIST=cpu:10.0.0.20 gpu:10.0.0.30"
```

The portal is ready when the VM shows `READY` with value `YES` in OneGate. In Sunstone, open the VM and look at **Info > Attributes**. The attribute `OOD_URL` has the address of the portal, for example `https://10.0.0.50/`. With the CLI, run `onevm show <VM ID>` and look for these attributes in the user template.

If the configuration fails, the VM shows the attribute `OOD_ERROR` with the reason, and the portal does not answer. For example, the message can be `Cannot mount 10.0.0.10:/export/nope on /home` or `The controller 10.0.0.30 does not answer on the SSH port`. If a service was the cause, fix it and reboot the VM. If a value was wrong, change it with **Update configuration**, as described in [Add or Remove a Cluster](#add-or-remove-a-cluster), and then reboot the VM, so that OneGate shows the new result.

## Use the Portal

Open the address in `OOD_URL` in a web browser. The certificate is self-signed, so the browser shows a warning the first time. Sign in with the LDAP user name and password.

{{< image path="/images/slurm/open_ondemand/ood_login.png"
alt="Login page of Open OnDemand" align="center" width="80%" mb="20px" >}}

The menus of the portal give users these tools. The portal has no remote desktop app, because the OneSlurm workers have no VNC server.

| Menu | Tool | What the user does |
|------|------|--------------------|
| Files | Home Directory | Browse, upload, download and delete files in the home. |
| Jobs | Active Jobs | See the jobs on every cluster, with their state, and cancel them. |
| Jobs | Job Composer | Create a job from a script or a template, choose the cluster and submit it. |
| Jobs | Project Manager | Group job scripts in a project folder. |
| Clusters | `<name>` Shell Access | Open a terminal on the controller of a cluster, as the user. |
| Clusters | System Status | See the nodes, CPUs and jobs of each cluster. |

{{< image path="/images/slurm/open_ondemand/ood_files.png"
alt="Files app of Open OnDemand with the home of the user" align="center" width="90%" mb="20px" >}}

A file uploaded in **Files** is in the home on every cluster at once, because the portal and the clusters mount the same export. The **Open in Terminal** button opens a terminal on the controller of the first cluster in the list.

{{< image path="/images/slurm/open_ondemand/ood_shell.png"
alt="Terminal on the controller of a cluster, with a job submitted with sbatch" align="center" width="90%" mb="20px" >}}

A job submitted from the terminal or from the Job Composer appears in **Active Jobs**.

{{< image path="/images/slurm/open_ondemand/ood_active_jobs.png"
alt="Active Jobs with a running job on the cpu cluster" align="center" width="90%" mb="20px" >}}

{{< image path="/images/slurm/open_ondemand/ood_job_composer.png"
alt="Job Composer with jobs on two clusters" align="center" width="90%" mb="20px" >}}

## Add Users

Create the user in the LDAP server of the clusters and the home on the NFS export, owned by the user and with mode `700`, and the portal needs no change. If the user signs in before the home exists, the portal shows **Home directory not found**. After the home is created, the user clicks **Restart Web Server** on that page.

## Add or Remove a Cluster

To change the clusters of a running portal, change `ONEAPP_SLURM_CLUSTERS_LIST`. Before you add a cluster, check that its controller is running, because the portal saves its SSH host key at this step. If the cluster is on a different network, attach the VM to that network first. In Sunstone, open the VM and go to **Configuration > Update configuration > Context > Context Custom Variables**. Edit the value, with one cluster per line or the clusters separated by spaces, and save the change. The appliance configures the portal again, which takes about three minutes. A cluster removed from the list disappears from the portal, and a new cluster appears in the menus of the portal.

After **Update configuration**, OneGate does not answer the VM until its next reboot, so `OOD_URL` and `OOD_ERROR` keep their old values. Read the result in `/var/log/one-appliance/configure.log` in the VM. This is a known issue of the `one-context` package 7.4.0.

## Security

* Limit the inbound traffic of the portal, for example with a [security group]({{% relref "product/virtual_machines_operation/virtual_machines_networking/security_groups" %}}). Users need TCP ports 443 and 80 (port 80 only redirects to 443), and administrators need port 22. The login service of the portal (Dex) also listens on port 5558 for metrics without authentication, and Open OnDemand does not allow changing that address. The portal must still reach the controllers on port 22, the LDAP server on port 389, the NFS server on port 2049 and OneGate.
* The connection to LDAP uses `ldap://` without TLS, as the LDAP server of OneSlurm. Passwords travel without encryption between the portal and the LDAP server, so keep the portal, the clusters and the LDAP server on a private network.
* Only `root` can sign in to the portal VM over SSH, with the key of the OpenNebula user that created it. LDAP users cannot open SSH sessions or copy files to the portal VM. They use the portal or a cluster controller.

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `OOD_ERROR` in the VM attributes | The appliance stopped at that step, and the portal is closed. Fix the input or the service named in the message and reboot the VM. The full log is in `/var/log/one-appliance/configure.log`. |
| The browser does not open the portal | Check that the VM has `READY=YES` and that your network reaches the IP of `OOD_URL` on port 443. Read the logs with `journalctl -u apache2 -u ondemand-dex`. |
| Login fails with the right password | The user is not under `ou=People` of the LDAP domain, or the LDAP server does not answer. Check with `ldapsearch -x -H <URL> -b ou=People,<base DN> uid=<user>` in the VM. For the domain `slurm.local`, the base DN is `dc=slurm,dc=local`. |
| **Home directory not found** | The user has no home on the NFS export. Create it, then click **Restart Web Server** on that page. |
| Active Jobs is empty, or Submit or the terminal says `Permission denied` | Click **Help > Restart Web Server**. This adds the portal key of the user to `~/.ssh/authorized_keys` again. The messages are in `journalctl -t ood-prehook`. |
| System Status shows an error page | A controller in the list does not answer. Active Jobs shows that cluster as empty, and the Job Composer and the terminal show an SSH error. Everything works again when the controller is back, without any action on the portal. |
| Pages wait with no message | The NFS server does not answer. The portal continues by itself when NFS is back. Use the VM console in Sunstone meanwhile, because an SSH session to the VM can also wait. |

## Known Limitations

* The upload limit of **Files** is 256 MiB per request. Users copy bigger files with `scp` or `rsync` to a cluster controller, which has the same home.
* Users open the Job Composer for the first time from the **Jobs** menu. If the first visit is a direct link to `/pun/sys/myjobs/`, the Job Composer creates an empty database and shows an error 500 from then on. To fix it, delete `~/ondemand/data/sys/myjobs/production.sqlite3` of that user, only if the file has no tables, and open the Job Composer from the menu.
* In the Job Composer, **New Job > From Template** creates a job with no script name, and the job cannot be submitted. Open **Job Options**, select the script and click **Save**.
* OneSlurm runs without Slurm accounting, so a cancelled job shows `Completed` in Active Jobs and `Failed` in the Job Composer. Check the real state with `scontrol show job <ID>` or in the output file of the job.
* Deleting a project in **Project Manager** removes only the project from the list. The files stay in the home, and users delete them in **Files**.
* A terminal closes when the user reloads the page. Users run long interactive work under `tmux` or `screen` on the controller.
* Use one portal for each NFS home export. Two portals on the same homes work for files, jobs and the terminal, but the Job Composer fails with an error 500 when the same user opens it on both portals at the same time.
* The portal cannot add a new cluster while its controller is stopped. The configuration stops with `OOD_ERROR` until the controller answers. Controllers the portal already knows can be stopped for maintenance.
