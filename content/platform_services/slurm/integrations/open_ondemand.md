---
title: "Open OnDemand"
linkTitle: "Open OnDemand"
date: "2026-10-06"
description: ""
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


[Open OnDemand](https://openondemand.org/) is a web portal for HPC users. The Open OnDemand appliance runs this portal in one VM, connected to your OneSlurm clusters. Users sign in with their LDAP account and, from a web browser, they can:

* manage the files in their home,
* submit jobs and follow them,
* open a terminal on a cluster.

The appliance is available in the [OpenNebula Public Marketplace](https://marketplace.opennebula.io/appliance/d3c8ea14-f6f0-455c-8a41-6129affa9a0e). It uses Ubuntu 26.04 LTS and Open OnDemand 4.2.

## How It Works

The portal does not run Slurm. It sends the Slurm commands of each user to the controller of the cluster over SSH.

The portal and the clusters share two services:

* the same LDAP directory, so users have the same account everywhere,
* the same NFS export for `/home`, so users see the same files everywhere.

One portal can serve several OneSlurm clusters.

### What Happens at Boot

1. The appliance checks the values of the wizard.
2. It mounts the NFS export on `/home`.
3. It reads the users from LDAP.
4. It creates a self-signed certificate for the IP address of the VM.
5. It adds each Slurm cluster to the portal and saves the SSH host key of each controller.
6. It starts the portal and publishes its URL in OneGate.

### What Happens at the First Login of a User

* The portal creates an SSH key for the user in `~/.ssh/id_ed25519_portal`.
* It adds the key to `~/.ssh/authorized_keys`, accepted only from the IP addresses of the portal.
* The controllers read the same home over NFS, so the portal can run `sbatch`, `squeue` and `scancel` as that user. The terminal uses the same key.

Each user works with their own Unix account, with the same UID as on the clusters. Users cannot read the files or cancel the jobs of other users.

## Requirements

Before you deploy the portal, check that you have these elements.

| Requirement | What the portal needs |
|-------------|-----------------------|
| OneSlurm clusters | One or more clusters in `RUNNING` state, and the IP address of each controller. |
| LDAP server | The LDAP server of the clusters, with a `ldap://` URL. |
| NFS export | The export with the homes of the users, for example `10.0.0.10:/export/home`. |
| User homes | One home for each user on that export, owned by the user, with mode `700`. |
| Virtual network | A network that reaches the controllers, the LDAP server and the NFS server. |
| [OneGate]({{% relref "product/operation_references/opennebula_services_configuration/onegate" %}}) | Reachable from that network. The portal publishes its URL and its errors there. |

### LDAP Details

* Use the same domain as `ONEAPP_LDAP_DOMAIN` in OneSlurm. The default is `slurm.local`.
* You can also use a base DN, such as `dc=example,dc=org`.
* Users must be `posixAccount` entries under `ou=People`.
* The portal has no bind user, so the LDAP server must allow anonymous search under `ou=People`.

The LDAP server of OneSlurm meets all of these points.

### NFS Details

* Use the same export as `ONEAPP_SLURM_NFS_HOME` in OneSlurm.
* The NFS server must allow the IP address of the portal.
* The portal uses NFS version 4. The export can use `root_squash`.

### Size of the VM

The default VM has 2 vCPU, 4 GB of memory and a 10 GB disk. Each active user needs about 200 MB of memory (measured with six users). Add memory if more users work at the same time.

## Deploy the Portal

### Step 1. Import the Appliance

In Sunstone:

1. Go to **Storage > Apps**.
2. Select **Open OnDemand**.
3. Click **Import** and choose the image datastore.

Or, with the CLI on the Front-end:

```shell
$ onemarketapp export "Open OnDemand" "Open OnDemand" --datastore default
```

This creates an image and a VM template, both called **Open OnDemand**.

### Step 2. Start the Wizard

1. Go to **Templates > VM Templates**.
2. Select **Open OnDemand** and click **Instantiate**.
3. Enter a name for the VM and click **Next**.

### Step 3. Fill in the User Inputs

The wizard has three tabs.

| Tab | Field | Example |
|-----|-------|---------|
| LDAP | LDAP URL | `ldap://10.0.0.20` |
| LDAP | LDAP domain or base DN | `slurm.local` (default) |
| Home | NFS export for `/home` | `10.0.0.10:/export/home` |
| Slurm | Slurm clusters, one per line | `cpu:10.0.0.20` |

{{< image path="/images/slurm/open_ondemand/ood_wizard_ldap.png"
alt="LDAP tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

{{< image path="/images/slurm/open_ondemand/ood_wizard_home.png"
alt="Home tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

Each line of the **Slurm** tab is `name:IP`, with the IP address of the controller.

* The name is what users see in the portal.
* The name starts with a letter or a digit. It has up to 63 characters, with letters, digits, `-` and `_`.
* Each name is used only once.
* The IP address is IPv4.
* Every cluster uses the same LDAP server and the same `/home` as the portal.

{{< image path="/images/slurm/open_ondemand/ood_wizard_slurm.png"
alt="Slurm tab of the Open OnDemand wizard" align="center" width="90%" mb="20px" >}}

### Step 4. Attach the Network of the Clusters

1. Click **Next**.
2. In **Advanced options**, open the **Network** tab.
3. Click **Attach NIC** and select the virtual network of the clusters.
4. Click **Finish**.

{{< image path="/images/slurm/open_ondemand/ood_wizard_network.png"
alt="Network tab of the Open OnDemand wizard with the NIC of the clusters" align="center" width="90%" mb="20px" >}}

The portal uses the IPv4 address of the first NIC. Users must reach that address with their web browser.

### Deploy with the CLI

Pass the same values with `--user-inputs`. Separate the clusters with spaces.

```shell
$ onetemplate instantiate "Open OnDemand" --name open-ondemand --nic <network> \
    --user-inputs "ONEAPP_LDAP_SERVER_URL=ldap://10.0.0.20,ONEAPP_LDAP_SERVER_DOMAIN=slurm.local,ONEAPP_HOME_NFS_EXPORT=10.0.0.10:/export/home,ONEAPP_SLURM_CLUSTERS_LIST=cpu:10.0.0.20 gpu:10.0.0.30"
```

### Step 5. Check That the Portal Is Ready

Open the VM in Sunstone and go to **Info > Attributes**. With the CLI, run `onevm show <VM ID>`.

| Attribute | Meaning |
|-----------|---------|
| `READY` = `YES` | The portal is ready. |
| `OOD_URL` | The address of the portal, for example `https://10.0.0.50/`. |
| `OOD_ERROR` | The configuration failed. The value says why, and the portal stays closed. |

Examples of `OOD_ERROR`:

* `Cannot mount 10.0.0.10:/export/nope on /home`
* `The controller 10.0.0.30 does not answer on the SSH port`

| Cause of the error | How to fix it |
|--------------------|---------------|
| A service was down | Fix the service and reboot the VM. |
| A value was wrong | Change it as shown in [Change the Clusters](#change-the-clusters), then reboot the VM so that OneGate shows the new result. |

## Use the Portal

1. Open the address of `OOD_URL` in a web browser.
2. Accept the certificate warning. The certificate is self-signed.
3. Sign in with the LDAP user name and password.

{{< image path="/images/slurm/open_ondemand/ood_login.png"
alt="Login page of Open OnDemand" align="center" width="80%" mb="20px" >}}

### Tools for Users

| Menu | Tool | What users do |
|------|------|---------------|
| Files | Home Directory | Browse, upload, download and delete files. |
| Jobs | Active Jobs | See their jobs on every cluster and cancel them. |
| Jobs | Job Composer | Create a job from a script or a template and submit it to a cluster. |
| Jobs | Project Manager | Group job scripts in project folders. |
| Clusters | `<name>` Shell Access | Open a terminal on the controller of a cluster. |
| Clusters | System Status | See the nodes, CPUs and jobs of each cluster. |

The portal has no remote desktop, because the OneSlurm workers have no VNC server.

{{< image path="/images/slurm/open_ondemand/ood_files.png"
alt="Files app of Open OnDemand with the home of the user" align="center" width="90%" mb="20px" >}}

* A file uploaded in **Files** is on every cluster at once, because they share `/home`.
* **Open in Terminal** opens a terminal on the first cluster of the list.

{{< image path="/images/slurm/open_ondemand/ood_shell.png"
alt="Terminal on the controller of a cluster, with a job submitted with sbatch" align="center" width="90%" mb="20px" >}}

Jobs submitted from the terminal or from the Job Composer appear in **Active Jobs**.

{{< image path="/images/slurm/open_ondemand/ood_active_jobs.png"
alt="Active Jobs with a running job on the cpu cluster" align="center" width="90%" mb="20px" >}}

{{< image path="/images/slurm/open_ondemand/ood_job_composer.png"
alt="Job Composer with jobs on two clusters" align="center" width="90%" mb="20px" >}}

## Add Users

1. Create the user in the LDAP server of the clusters.
2. Create the home on the NFS export, owned by the user, with mode `700`.

The portal needs no change. If the user signs in before the home exists, the portal shows **Home directory not found**. Create the home, then the user clicks **Restart Web Server** on that page.

## Change the Clusters

You can add or remove clusters on a running portal.

Before you add a cluster:

* Check that its controller is running. The portal saves its SSH host key at this step.
* If the cluster is on another network, attach that network to the VM first.

Then:

1. In Sunstone, open the VM.
2. Go to **Configuration > Update configuration > Context > Context Custom Variables**.
3. Edit `ONEAPP_SLURM_CLUSTERS_LIST`. Use one cluster per line, or separate them with spaces.
4. Save the change.

The appliance configures the portal again in about three minutes. Removed clusters disappear from the portal, and new clusters appear in its menus.

{{< alert title="Note" type="info" >}}
After **Update configuration**, OneGate does not answer the VM until it reboots, so `OOD_URL` and `OOD_ERROR` keep their old values. Read the result in `/var/log/one-appliance/configure.log` in the VM. This is a known issue of the `one-context` package 7.4.0.
{{< /alert >}}

## Security

### Network Ports

Limit the traffic of the portal, for example with a [security group]({{% relref "product/virtual_machines_operation/virtual_machines_networking/security_groups" %}}).

| Direction | Port | Use |
|-----------|------|-----|
| Inbound | TCP 443 | Users open the portal. |
| Inbound | TCP 80 | Redirects to 443. |
| Inbound | TCP 22 | Administrators only. |
| Outbound | TCP 22 | SSH to the controllers. |
| Outbound | TCP 389 | LDAP server. |
| Outbound | TCP 2049 | NFS server. |
| Outbound | OneGate port | OneGate. |

Do not open port 5558. The login service of the portal (Dex) shows metrics there without authentication, and Open OnDemand does not allow changing it.

### LDAP Without TLS

The portal connects to LDAP with `ldap://`, like OneSlurm. Passwords travel without encryption between the portal and the LDAP server. Keep the portal, the clusters and the LDAP server on a private network.

### SSH to the Portal VM

Only `root` can open an SSH session on the portal VM, with the key of the OpenNebula user that created it. LDAP users cannot use SSH or copy files to the portal VM. They use the portal or a cluster controller.

## Troubleshooting

| Problem | What to do |
|---------|------------|
| The VM shows `OOD_ERROR` | Fix the value or the service named in the message, then reboot the VM. Full log in `/var/log/one-appliance/configure.log`. |
| The browser does not open the portal | Check that the VM shows `READY=YES` and that your network reaches the IP of `OOD_URL` on port 443. Logs: `journalctl -u apache2 -u ondemand-dex`. |
| Login fails with the right password | The user is not under `ou=People`, or LDAP does not answer. Test in the VM with `ldapsearch -x -H <URL> -b ou=People,<base DN> uid=<user>`. For `slurm.local`, the base DN is `dc=slurm,dc=local`. |
| **Home directory not found** | Create the home of the user, then click **Restart Web Server** on that page. |
| Active Jobs is empty, or `Permission denied` in Submit or the terminal | Click **Help > Restart Web Server**. This adds the key of the user to `~/.ssh/authorized_keys` again. Logs: `journalctl -t ood-prehook`. |
| System Status shows an error page | A controller does not answer. That cluster shows no jobs, and the Job Composer and the terminal show an SSH error. Everything works again when the controller is back. |
| Pages load forever with no message | The NFS server does not answer. The portal works again by itself when NFS is back. Meanwhile, use the VM console in Sunstone, because SSH to the VM can also hang. |

## Known Limitations

| Area | Limitation | What to do |
|------|------------|------------|
| Files | Uploads are limited to 256 MiB. | Copy bigger files with `scp` or `rsync` to a cluster controller, which has the same home. |
| Terminal | The terminal closes when the page reloads. | Run long work under `tmux` or `screen` on the controller. |
| Job Composer | If the first visit is a direct link to `/pun/sys/myjobs/`, it creates an empty database and shows error 500 from then on. | Open it the first time from the **Jobs** menu. To fix it, delete `~/ondemand/data/sys/myjobs/production.sqlite3` of that user (only if the file has no tables) and open the Job Composer from the menu. |
| Job Composer | **New Job > From Template** creates a job without a script. | Open **Job Options**, select the script and click **Save**. |
| Job states | OneSlurm has no Slurm accounting, so a cancelled job shows `Completed` in Active Jobs and `Failed` in the Job Composer. | Check the real state with `scontrol show job <ID>` or in the output file of the job. |
| Project Manager | Deleting a project only removes it from the list. The files stay. | Delete the files in **Files**. |
| Two portals | With two portals on the same homes, the Job Composer fails with error 500 when a user opens it on both at the same time. | Use one portal for each NFS home export. |
| New clusters | A new cluster needs a running controller. If it does not answer, the configuration stops with `OOD_ERROR`. | Start the controller first. Clusters the portal already knows can be stopped for maintenance. |
