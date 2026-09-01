---
title: "Validate Certified Hardware Deployments"
linkTitle: "Validation"
date: "2025-07-16"
categories:
pageintoc: ""
tags:
weight: 4
---

<a id="validate-certified-hardware"></a>

{{< alert title="Tip" type="tip" >}}
This guide provides the basic steps. If you wish to see a more detailed guide, please refer to [Deploying a Virtual Machine Locally]({{% relref "deploy_opennebula_onprem_with_minione#deploying-a-virtual-machine-locally" %}}).
{{< /alert >}}

After successfully verifying the infrastructure deployed by the automations, to run a Virtual Machine access the OpenNebula web UI at:

`http://<Front-end IP>:2616/fireedge/sunstone`

To log in, use the default username `oneadmin`, and the password specified in the `one_pass` variable of the inventory file.

The image below shows the **Alpine Linux 3.20** Virtual Machine included in the OpenNebula installation:

<a id="one-marketplace"></a>

{{< image
    pathDark="/images/sunstone/misc/dark/alpine_320_marketplace.png"
    path="/images/sunstone/misc/light/alpine_320_marketplace.png"
    alt="Alpine 3.20 in marketplace" align="center" width="90%" mb="20px"
  >}}

{{< alert title="Warning" type="warning" >}}
Make sure to choose the correct variant of the image, which fits the certified hardware's architecture. For example for ARM-based architectures the correct Alpine Linux 3.20 Virtual Machine template is **Alpine Linux 3.20 (aarch64)**.
{{< /alert >}}

To instantiate the VM, in the Sunstone UI's left-hand menu go to **Instances** --> **VMs**. Click the **Create** icon highlighted below, then select the Virtual Machine template. Follow the steps of the VM instantiation wizard. For this basic guide, all values can be left empty or at their defaults.

<a id="one-new-vm"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/create_vm.png"
    path="/images/sunstone/misc/light/create_vm.png"
    alt="Create VM" align="center" width="90%" mb="20px"
  >}}

In the **Instances -> VMs** view select the new VM in the list to open the details page **Configuration** tab. Select **Update configuration**.

<a id="one-vm-config"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/update_vm_config.png"
    path="/images/sunstone/misc/light/update_vm_config.png"
    alt="Create VM" align="center" width="90%" mb="20px"
  >}}

In the **Context** tab of the modal dialog that opens, scroll down to the **Context Custom Variables** section and expand it. Find the `PASSWORD` field and select **Update** (the pencil icon), then specify the desired root password for the VM, then click **Accept**, as shown below, then press **Continue**.

{{< image
    pathDark="/images/sunstone/misc/dark/update_vm_password.png"
    path="/images/sunstone/misc/light/update_vm_password.png"
    alt="Update VM password" align="center" width="90%" mb="20px"
  >}}

Log in to the VM via VNC, go to the ellipsis drop-down menu and select **Console -> VNC**. Log in as user `root` with the password that you specified in the previous step.

<a id="one-vnc-connect"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/vm_vnc.png"
    path="/images/sunstone/misc/light/vm_vnc.png"
    alt="VNC" align="center" width="90%" mb="20px"
  >}}

After accessing the deployed VM's command line interface, verify that the terminal is responsive. For example, change to the home folder of user `root`:

```bash
root@vm:~# cd ~
root@vm:~# pwd
/root
```

Finally, as a cleanup step, terminate the VM by clicking the red “Trash can” icon, then verify that the VM transitions to state `DONE`, as shown below.

<a id="one-terminate-vm"></a>
{{< image
    pathDark="/images/sunstone/misc/dark/shutdown_done.png"
    path="/images/sunstone/misc/light/shutdown_done.png"
    alt="Shutdown" align="center" width="90%" mb="20px"
  >}}

[one-marketplace]: /images/guides/common_101_ui/one-marketplace.png
[one-new-vm]: /images/guides/common_101_ui/one-new-vm.png
[one-vm-config]: /images/guides/common_101_ui/one-vm-config.png
[one-vnc-connect]: /images/guides/common_101_ui/one-vnc-connect.png
[one-terminate-vm]: /images/guides/common_101_ui/one-terminate-vm.png
