---
title: "Deploy OpenNebula On-prem with an ISO"
linkTitle: "ISO-based Deployment"
description:
weight: 3

---

# 

## 1. Introduction

OpenNebula provides an ISO image for rapid deployment of an OpenNebula Front-end or processing node. The ISO installs a pre-configured deployment of OpenNebula Enterprise Edition running on a minimal installation of AlmaLinux 9. The ISO image can be flashed to bootable, removable media (such as a USB disk) for local installation or mapped via IPMI Virtual Media for remote hardware management.  

Once the ISO has booted and finished setup, a pre-configured OpenNebula cloud will be ready for immediate use, installed on a single bare-metal server, complete with the OpenNebula Front-end server and a KVM hypervisor node. The same ISO can be used to install other KVM hypervisor nodes on the same infrastructure. The installed software includes a menu and a set of ansible playbooks to make the OpenNebula infrastructure management simpler.

{{< image path="/images/ISO/00-onepoc_architecture.svg" alt="OnePOC Architecture" align="center" width="90%" mb="20px"  >}}

## 1.1 Disclaimer

**This Proof of Concept is intended to run on a controlled testbed isolated from productive environments. Please ensure production and PoC networks are isolated to avoid production impact.**

## 1.2 Hardware and Personnel Requirements

The OpenNebula PoC deployment needs a server with a processor with x86_64-v2 capabilities. Any CPU supporting at least the extensions of Intel Nehalem/Silvermont or AMD Bulldozer/Jaguar should be enough. See the minimal hardware requirements in Table 1.1.  

<center>

| Component   | Required                                                                                               |
|:----------- |:------------------------------------------------------------------------------------------------------ |
| **CPU**     | - Intel - Nehalem/Silvermont<br/>- AMD -  Bulldozer/Jaguar<br />- Virtualization enabled at BIOS level |
| **Memory**  | - 64 GB for Front-end and nodes                                                                        |
| **Disk**    | - 512 GB                                                                                               |
| **Network** | [Single Node] Not required for the installation<br/>[Multiple Node] 1 Network Interface                |

<sup>Table 1.1. Hardware requirements</sup>

</center>
Also the network connectivity needs to be configured properly:

| Service           | Port | Comment                                                                                                                                                     |
| ----------------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sshd              | 22   | used for the OpenNebula core interactions with hypervisor nodes. Should be accessible on all hypervisor nodes  from the OpenNebula front-end and vice versa |
| FireEdge Sunstone | 2616 | web-based graphical user interface. Should be accessible from OpenNebula front-end node to PoC users                                                        |

<sup>Table 1.2 Ports accessibility</sup>

Personnel who execute and operate the OpenNebula PoC are expected to possess the following hands-on skills and knowledge:  

- Generic Linux administration skills, such as managing users and groups, navigating the Linux filesystem and managing files.

- A good understanding of virtualization concepts, including virtualized networking and storage.

- Knowledge of common linux utilities, services and tools; such as, but not limited to:
  
  - Linux storage subsystem: local disks management
  
  - Networking utilities: iptables, tcpdump, iproute2 and Linux bridges
  
  - Virtualization management: KVM, QEMU, libvirt/virsh
    
    - Linux services configuration and operation: passwordless SSH configuration

# 

## 2. ISO download and preparation

{{< alert title="Warning" type="warning" >}}
**Installing the ISO will delete all the disk data on the server during the installation.**
{{< /alert >}}

In order to obtain an installation ISO image, contact us by [filling the form](https://opennebula.io/evaluate-opennebula/) or by email at: sales@opennebula.io
Installation images are generated for each deployment individually, therefore distribution needs to be arranged by your PoC coordinator.

<br>Once your OpenNebula Systems contact makes the ISO available, there are two different  installation options:

- Installation via IPMI virtual media

- Installation using external USB disk

Other installation methods (such as PXE-based installations), while possible, are out of the scope of this guide.

Note that the recommended way to mount the ISO is over the LAN using one of the mechanisms supported by your BMC protocols (e.g HTTP, HTTPS, NFS, CIFS). Mounting the ISO via HTML5/java virtual console could be less reliable because of network glitches between the client PC you are accessing the server’s BMC from and the BMC itself.

As soon as the ISO is mounted as Virtual media  select the “Boot from Virtual media” option in the BMC settings, and restart the server.

If installing from the external USB disk, the bootable USB disk should be prepared before beginning the installation. Once the USB disk is ready, it should be attached to the server you will install OpenNebula on. The procedure for preparing the bootable PoC disk depends on your client workstation operating system. Below you will find instructions for preparing the USB disk on different operating systems.

Whichever OS you choose to use, make sure you are writing the image in DD mode (disk dump). Modern software adds some persistence to the USB units that will not allow the installation.

## 2.1 Windows 11

You can create a bootable USB disk using a third-party utility such as [Rufus](https://rufus.ie/en/) . The below instructions assume that Rufus is used..

1. Launch the Rufus application.

2. In the Device list, select the USB disk you want to write PoC ISO to.

3. Click the “Select” button, then select the PoC ISO that you downloaded before.

4. Please, set up the DD mode for the image creation, all other options should be at their default values, and click “Start.”

5. The app will display a number of warnings about destroying the data on the USB disk. Accept them, and wait until the write process is completed.

## 2.2 Linux

1. Attach your removable media, then identify it by running diskutil list. Typically, it should be listed as something like /dev/sdX, e.g. /dev/sdb1.

2. Write down the path of the downloaded ISO, as this will be needed in the next command.

3. To copy the ISO to your removable media, run the dd command as below, changing the path to the ISO and the device file according to your system.  
   
   `dd if=/path/to/iso/AlmaLinux-OnePoC.iso of=/dev/sdX  `

4. Wait for the process to complete, then safely remove the media from your workstation.

## 2.3 Mac OSX

1. Attach your removable media, then identify it by running diskutil list. Typically, it should be listed as something like` /dev/sdX`, e.g.` /dev/sdb1`.

2. Write down the path of the downloaded ISO, as this will be needed in the next command.

3. To copy the ISO to your removable media, run the dd command as below, changing the path to the ISO and the device file according to your system.  
   
   `dd if=/path/to/iso/AlmaLinux-OnePoC.iso of=/dev/sdX`  

4. Wait for the process to complete, then safely remove the media from your workstation.
   
   # 
   
   ## 3. Installation guide

5. Ensure that the environment where you wish to install the ISO meets the requirements listed in the table of the [section 1.1]

6. Copy the prepared ISO file to a removable drive that can be inserted into the physical OpenNebula server. Please note that if you perform the install via IPMI (or other out-of-band systems), you may have the option to upload the ISO and connect virtually.

7. Set up your server to boot from the removable media.

8. Restart the server. It will boot from the first boot disk device. The bootloader will appear, depending if your server is using UEFI or MBR boot, you will see one of the following screens during 30 seconds

| {{< image path="/images/ISO/0-uefi_boot_screen.png" alt="OnePOC Architecture" align="center" width="90%" mb="20px"  >}}  UEFI boot screen | {{< image path="/images/ISO/0-mbr_boot_screen.png" alt="OnePOC Architecture" align="center" width="90%" mb="20px"  >}} MBR boot screen |
| ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |

- <u>“Install OpenNebula POC”</u> will install a OpenNebula frontend on the server. This frontend will work as well as an OpenNebula host.

- <u>“Install OpenNebula Node” </u>will install a OpenNebula host. This is only necessary if you want to add this server to an already running frontend.

- The options that start with <u>“Test this media”</u> will do a checksum of the image before installing it.  
5. There will be no more prompts—please wait for the installation to complete. You will know the installation is finished when the machine reboots. Once the installation has completed, you can log in to the server with the following credentials.

```
User: root
Password:  0p3nN3bul4
```

6. Once you are logged in, run onefemenu (or sudo nmtui) command to configure your Management Network so you can access the OpenNebula web interface. Please ensure this is configured on the physical interface that is connected to your internal infrastructure, and do not touch the pre-configured bridge interface that was created for OpenNebula internal networking.

7. Restart networking.

8. Access the OpenNebula web interface via the IP you configured in Step 6 above, on port 2616 using http (i.e. point your browser to `http://<ASSIGNED-IP>:2616)`. 

9. The PoC OpenNebula instance generates a random password for the user oneadmin. It can be checked running onefemenu and selecting Show oneadmin password 

10. Use the user oneadmin with the previously obtained password to access to the fireedge web interface
    
    # 
    
    ## 4. Cloud Use Cases Validation

Once the OpenNebula platform is deployed, it is recommended to execute basic use cases to ensure that the PoC cloud operates as expected. The OpenNebula PoC cloud includes a preconfigured virtual network and storage, as well as a pre-installed VM image and template which you can use to instantiate a test VM.

## 4.1 Setting up VXLAN virtual network

Before starting with instantiating VMs it’s desirable to have at least a single virtual network (VNET) the VMs can be connected to.

To do that follow the steps below.

1. Log in to the OpenNebula web interface as user oneadmin, as instructed in steps 9 and 10 in the previous section.

2. Click on Virtual networks tile
   {{< image path="/images/ISO/1-vnet-select.png" align="center" width="90%" mb="20px">}}

3. Press the Create Virtual Network button
   {{< image path="/images/ISO/2-vnet-create.png" align="center" width="90%" mb="20px">}}

4. Choose the "Create from scratch" option
   {{< image path="/images/ISO/3-vnet-fromscratch.png" align="center" width="90%" mb="20px">}}

5. Specify VNET name and select a cluster the VNET needs to be associated with and press "Next" button to proceed further.
   {{< image path="/images/ISO/4-vnet-vlan_100.png" align="center" width="90%" mb="20px">}}

6. Select VXLAN tab and specify the device name of the physical network card on the host to route traffic. Use the real name on your host as shown by `ip link` command. Just in this example we use enX0. Set the VXLAN ID and VXLAN mode to `evpn`.
   {{< image path="/images/ISO/5-vnet-vxlan_100.png" align="center" width="90%" mb="20px">}}

7. Go to the "Addresses" tab and click "Add address range" button.
   {{< image path="/images/ISO/6-vnet-address.png" align="center" width="90%" mb="20px">}}

8. Specify first IP address and network size
   {{< image path="/images/ISO/7-vnet-range.png" align="center" width="90%" mb="20px">}}

9. Click on Context tab, provide network address, network mask, MTU value for the Guest interface and other parameters in case of necessity.
   {{< image path="/images/ISO/8-vnet-MTU.png" align="center" width="90%" mb="20px">}}

10. Press the **Finish** button to end with VNET creation.

## 4.2 Updating VM template

To avoid changing network settings on each VM instantiation, a proper network configuration can be specified in the VM template.

1. Use "VM template" section in the menu. Select the desired VM template and press **update** button.

{{< image path="/images/ISO/9-vmtemplate-update.png" align="center" width="90%" mb="20px">}}

2. Click "**Next**" to proceed and on the next pane select "**Network**" tab. Use "**Attach NIC**" button to configure a new network adapter.
   {{< image path="/images/ISO/10-vmtemplate-NIC.png" align="center" width="90%" mb="20px">}}

3. Click "**Next**" to move to the "**Select network**" stage and choose previously created VNET. Finish by clicking "**Next**" on subsequent stages and "**Finish**" at the end.
   {{< image path="/images/ISO/11-vmtemplate-select.png" align="center" width="90%" mb="20px">}}

## 4.3 Instantiating a Single VM

To instantiate a VM via the OpenNebula web interface, perform the following steps:

1. Log in to the OpenNebula web interface as user oneadmin

2. Click on the "**Create VM**" button

{{< image path="/images/ISO/12-vm-create.png" align="center" width="90%" mb="20px">}}

3. Select an available template and you will be taken to the instance config pane.

{{< image path="/images/ISO/13-vm-select.png" align="center" width="90%" mb="20px">}}

4. In the next screen you can configure various parameters for the VM. The only mandatory parameter is the VM name; you can leave all others at their default values. Enter the VM name, then click Next.

{{< image path="/images/ISO/14-vm-name.png" align="center" width="90%" mb="20px">}}

5. Since the virtual network and datastores have been previously configured, in the next screen all parameters are already set to their default values. To deploy the VM, click Finish.

{{< image path="/images/ISO/15-vm-finish.png" align="center" width="90%" mb="20px">}}

6. The VM deployment process begins in the background. After a few moments the VM will be fully deployed, and its status will change to RUNNING.
   {{< image path="/images/ISO/16-vm-running.png" align="center" width="90%" mb="20px">}}

7. Select the running VM, click on the actions menu (three dots) and navigate to the "VNC" menu item.
   {{< image path="/images/ISO/17-vm-VNC.png" align="center" width="90%" mb="20px">}}

8. Confirm that you see the startup screen of the VM.
   {{< image path="/images/ISO/18-vm-console.png" align="center" width="90%" mb="20px">}}

9. Log in to the deployed VM with the following credentials:
   
   ```
   User: root
   Password:  opennebula
   ```

## 4.4 Instantiating Multiple VMs

1. Instantiate one more VMs following the steps specified in the section 4.3. Once a VM is up, capture the IP address assigned to it (note that actual IP addresses might vary).
   {{< image path="/images/ISO/19-vm-IP.png" align="center" width="90%" mb="20px">}}

2. Open the new VM’s console and log in with the following credentials:
   
   ```
    User: root
    Password:  opennebula
   ```

Check the IP address assigned to the previous VM (in the example below, 172.31.0.11). Run the ping command to validate connectivity between VMs.

## 4.5 Instantiating a VM Using a Custom Image

Before attempting to upload a custom image, it is recommended to review the official documentation on [managing images](https://docs.opennebula.io/7.4/product/virtual_machines_operation/guest_operating_systems/creating_images/) in OpenNebula. To create a VM using the custom image, follow these steps:

1. Navigate to **Storage** -> **Images**, then click the "**Create image**"  button to create a new image:
   {{< image path="/images/ISO/20-vm-newimg.png" align="center" width="90%" mb="20px">}}

2. Enter a name for your custom image, then click the **Upload** tab. Select the image file you wish to upload, then click **Next**.
   {{< image path="/images/ISO/21-vm-upload.png" align="center" width="90%" mb="20px">}}

3. Select the datastore to save your image. Caution: Check the size of the raw image to upload, and ensure there is enough space available for it in the target datastore. Once selected, proceed with "**Next**" and then "**Finish**" buttons.

{{< image path="/images/ISO/22-vm-datastore.png" align="center" width="90%" mb="20px">}}

4. Wait for the image to finish uploading

{{< image path="/images/ISO/23-vm-imgloading.png" align="center" width="90%" mb="20px">}}

5. Once uploaded, image will be processed by OpenNebula. It may take a while and during that process the new image remains in LOCKED state.

{{< image path="/images/ISO/24-vm-imglocked.png" align="center" width="90%" mb="20px">}}

6. After the image file is processed, Sunstone should display the new image on the Images screen as READY

{{< image path="/images/ISO/25-vm-imgready.png" align="center" width="90%" mb="20px">}}

7. Now you will need to create a new VM template using the custom image. Navigate to **Templates -> VM Templates**, then click the "**Create template**" button to create a new VM template. 

{{< image path="/images/ISO/26-vm-createtemplate.png" align="center" width="90%" mb="20px">}}

8. On the template screen, select **KVM** for the hypervisor. Enter a name for the VM, and the physical/virtual CPU and memory settings for the VM template. Click **Next**.

{{< image path="/images/ISO/27-vm-templatekvm.png" align="center" width="90%" mb="20px">}}

9. On the **Advanced Options** screen, select the **Storage** tab, then click **Attach disk***

{{< image path="/images/ISO/28-vm-templateattachdisk.png" align="center" width="90%" mb="20px">}}

10. Select **Image** option

{{< image path="/images/ISO/29-vm-templateimage.png" align="center" width="90%" mb="20px">}}

11. Choose the recently uploaded image and click "**Next**" followed by "**Finish**"

{{< image path="/images/ISO/30-vm-templatechoice.png" align="center" width="90%" mb="20px">}}

12. Now you are back on "Advanced options" pane. Switch to the "Network" tab and click "Attach NIC" button.

{{< image path="/images/ISO/31-vm-templateNIC.png" align="center" width="90%" mb="20px">}}

13. Select "**Automatic**" and click "**Next**" button on following panes till "**Finish**"

{{< image path="/images/ISO/32-vm-templateauto.png" align="center" width="90%" mb="20px">}}

14. Finish the process with "**Next**" followed by "Finish" **buttons**. 

{{< image path="/images/ISO/33-vm-templatenext.png" align="center" width="90%" mb="20px">}}

15. The new template will show up on the list

{{< image path="/images/ISO/34-vm-templateready.png" align="center" width="90%" mb="20px">}}

16. Select the new template and click on "**Instantiate**"

{{< image path="/images/ISO/35-vm-templateinstantiate.png" align="center" width="90%" mb="20px">}}

17. Follow the process as described in chapter 4.3, points 4-9. After finish, you should see the new VM in RUNNING state

{{< image path="/images/ISO/36-vm-templaterunning.png" align="center" width="90%" mb="20px">}}

# 

## 5. Adding another OpenNebula node (hypervisor)

If you have another server to be used as a new node, use  same ISO and choose “**Install OpenNebula Node**” in boot menu. 

You can log into the node with the following credentials (the same as the frontend):

```
User: root
Password:  0p3nN3bul4
```

On the host, `onehostmenu` will invoke a dialog that, among other options, allows you to set up the network calling `nmtui` (nmtui can be invoked as well).

Once the node is installed and the network configured, please follow the following steps on the frontend

- Execute onefemenu
- Select Add OpenNebula host
- Enter the IP of the node
- Enter the user to access the node. It must have sudo permissions (root, for instance)
- The user password will be asked (not printed)

The node will be set up and after a short amount of time will appear online.

# 

## 6. Assistance and Support

While we commend setting up your PoC before applying any advanced configuration, the OpenNebula engineering team will be available during the PoC process if you wish to look into more advanced functionality, such as configuring virtual machines for outbound internet access. Simply reach out to your assigned engineering resource, and they will be more than happy to discuss advanced configuration options with you.

You can reach out to the OpenNebula Solution Architect team for your PoC at any time, by emailing `sales@opennebula.io`. OpenNebula also includes very concise documentation at https://docs.opennebula.io/, highly useful for day-to-day management of your cloud. 
Lastly, the OpenNebula forum is also a great database of knowledge from the OpenNebula community: [OpenNebula Community Forum](https://forum.opennebula.io/).

# 

## Annex A1. Frontend and Node Menu

## A1.1 Frontend menu (onefemenu)

In command line, execute `onefemenu` as the user root on OpenNebula frontend to access to the following menu

```
┌──────────────────────OpenNebula node Setup─────────────────────────┐
│ Setup menu                                                         │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │           netconf     Configure network                        │ │
│ │           enable_fw   Enable firewalld                         │ │
│ │           disable_fw  Disable firewalld                        │ │
│ │           add_host    Add OpenNebula Host                      │ │
│ │           setup_frr   Setup FRR for BGP-EVPN                   │ │
│ │           proxy       Configure proxy settings                 │ │
│ │           tmate       Remote console support                   │ │
│ │           quit        Exit to Shell                            │ │
│ └────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                   <  OK  >          <Cancel>                       │
└────────────────────────────────────────────────────────────────────┘
```

The `onefemenu` options are:

- **netconf**: configures the network with `nmtui`, sets up some internal variables and disables the firewall.
- **enable_fw** / **disable_fw**: enable and disable the firewall.
- **add_host**: adds OpenNebula node. It will ask for the ip/name of the host and the user that will be used to add it. After it runs it will ask for the password for this user.
- **proxy**: Configure the proxy. This will edit the skeleton file for setting up the proxy server and restart/reconfigure the necessary services. Please check Annex: Configuring a proxy server .
- **tmate**: This option invokes tmate, a remote console program, that will connect to a remote OpenNebula server and will allow OpenNebula support engineers to help you solve the problems
- **setup_frr**: Configures a skeleton for a BGP-EVN route reflector. By default it will allow the default network (the one with the default gateway) to listen to the BGP server. The configuration can be edited before the service FRR is restarted.

## A1.2 Host menu (onehostmenu)

In command line, execute `onehostmenu` as the user root on OpenNebula frontend to access to the following menu:

```
┌──────────────────────OpenNebula node Setup─────────────────────────┐
│ Setup menu                                                         │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │                netconf     Configure network                   │ │
│ │                enable_fw   Enable firewalld                    │ │
│ │                disable_fw  Disable firewalld                   │ │
│ │                setup_frr   Setup FRR for BGP-EVPN              │ │
│ │                quit        Exit to Shell                       │ │
│ └────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                   <  OK  >          <Cancel>                       │
└────────────────────────────────────────────────────────────────────┘
```

The onehost options are:

- **netconf**: Allows you to configure the network with nmtui and disables the firewall.
- **enable_fw** / disable_fw: Enable/Disable the firewall.
- **setup_frr**: Configures a skeleton for a BGP-EVPN client. It will ask for an existing BGP route. reflector. Allows the user to edit the configuration before restarting FRR.

# 

## Annex A2. Configuring Network interfaces with nmtui

`nmtui` is a ncurses interface to set up Network Manager devices.

If your administration interface (the one that you are using to access the PoC server) is on a tagged interface (no need to configure a VLAN on it), the steps to configure it are the following:

- Select “**Edit a connection**” and press enter
- Identify the network interface (under the “**Ethernet**” category)
- Select “**Edit**” (in this example we will use the interface ens3)
- Default interface MTU is 1500. If you need to modify it, please show the ETHERNET section of the dialog and set it up accordingly. For instance, to set up the MTU to 9000 bytes, the dialog should look like the following one

```
┌───────────────────────────┤ Edit Connection ├───────────────────────────┐
│                                                                         │
│         Profile name ens3____________________________________           │
│               Device ens3 (02:00:AC:14:00:04)________________           │
│                                                                         │
│ ╤ ETHERNET                                                    <Hide>    │
│ │ Cloned MAC address ________________________________________           │
│   │                MTU 9000______ bytes                                   │
│ └                                                                       │
│ ═ 802.1X SECURITY                                             <Show>    │
│                                                                         │
│ ═ IPv4 CONFIGURATION <Manual>                                 <Show>    │
│ ═ IPv6 CONFIGURATION <Automatic>                              <Show>    │
│                                                                         │
│ [X] Automatically connect                                               │
│ [X] Available to all users                                              │
│                                                                         │
│                                                           <Cancel> <OK> │
└─────────────────────────────────────────────────────────────────────────┘
```

- On the IPv4 configuration section press “Show”. We recommend to set up the IP Manual. An example of the modified fields to set the interface (IP 172.20.0.4/24, default GW 172.20.0.1, DNS 8.8.8.8) would be the following
  
  ```
  ┌───────────────────────────┤ Edit Connection ├───────────────────────────┐
  │         Profile name ens3____________________________________           │
  │               Device ens3 (02:00:AC:14:00:04)________________           │
  │                                                                         │
  │ ═ ETHERNET                                                    <Show>    │
  │ ═ 802.1X SECURITY                                             <Show>    │
  │                                                                         │
  │ ╤ IPv4 CONFIGURATION <Manual>                                 <Hide>    │
  │ │          Addresses 172.20.0.4/24____________ <Remove>                 │
  │ │                    <Add...>                                           │
  │ │            Gateway 172.20.0.1_______________                          │
  │ │        DNS servers 8.8.8.8__________________ <Remove>                 │
  │ │                    <Add...>                                           │
  │ │     Search domains <Add...>                                           │
  │ │                                                                       │
  │ │            Routing (No custom routes) <Edit...>                       │
  │ │ [ ] Never use this network for default route                          │
  │ │ [ ] Ignore automatically obtained routes                              │
  │ │ [ ] Ignore automatically obtained DNS parameters                      │
  │ │                                                                       │
  │ │ [X] Require IPv4 addressing for this connection                       │
  │ └                                                                       │
  │ ═ IPv6 CONFIGURATION <Automatic>                              <Show>    │
  │                                                                         │
  │ [X] Automatically connect                                               │
  │ [X] Available to all users                                              │
  │                                                           <Cancel> <OK> │
  └─────────────────────────────────────────────────────────────────────────┘
  ```
  
  Once finished , please press OK and go back and quit nmtui.

If the interface is a trunk and you need to set up a VLAN on the interface, you should previously do the following:

Choose “**Edit a connection**”, after that choose “**VLAN**” and press create

```
┌──────────────────────┤ New Connection ├──────────────────────┐
│                                                              │
│ Select the type of connection you wish to create.            │
│                                                              │
│                        MACsec      ↑                         │
│                        Team        ▒                         │
│                        VLAN        ▮                         │
│                        Veth        ▒                         │
│                        WireGuard   ↓                         │
│                                                              │
│                                            <Cancel> <Create> │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

You will get the following dialog after it. In this case, filling up the “**Device**” field with the value “**ens8.800**” will automatically know that the parent interface is ens8 and the VLAN ID will be 800. The Profile name was set up to VLAN 800 in order to have a readable name

```
┌───────────────────────────┤ Edit Connection ├───────────────────────────┐
│                                                                         │
│         Profile name VLAN 800________________________________           │
│               Device ens8.800________________________________           │
│                                                                         │
│ ╤ VLAN                                                        <Hide>    │
│ │             Parent ens8____________________________________           │
│ │            VLAN id 800_____                                           │
│ │                                                                       │
│ │ Cloned MAC address ________________________________________           │
│ │                MTU __________ (default)                               │
│ └                                                                       │
│                                                                         │
│ ═ IPv4 CONFIGURATION <Automatic>                              <Show>    │
│ ═ IPv6 CONFIGURATION <Automatic>                              <Show>    │
│                                                                         │
│ [X] Automatically connect                                               │
│ [X] Available to all users                                              │
│                                                                         │
│                                                           <Cancel> <OK> │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

After that, the “IPv4 CONFIGURATION” section is configured the same as a tagged interface.
#

## Annex A3. Configuring a proxy server

If your network does not allow you to download files from the internet via proxy you will find problems downloading the appliances and the images from OpenNebula marketplace. To set up the proxy server on the frontend(s), please edit the file 

```
/etc/systemd/system/opennebula.service.d/http_proxy.conf
```

The file must have the following syntax (a skeleton with commented values is provided)

```
[Service]
Environment="http_proxy=http://proxy.example.com:8080"
Environment="https_proxy=http://proxy.example.com:8080"
Environment="no_proxy=172.20.0.,192.168.1."
```

After the modification, the service must be restarted

```
sudo systemctl restart opennebula
```

# 

## Annex A4. Spinning up Windows Virtual Machines

## A4.1 Download installation ISO Image

Copy the Windows ISO image to the PoC front-end /var/tmp directory. Genuine Windows images can be quickly obtained through the [Microsoft downloads](https://www.microsoft.com/en-us/software-download/windows11) webpage.

## A4.2 Register the Windows image

Prerequisite: Windows ISO is available at: `/var/tmp/Win11_25H2_EnglishInternational_x64_v2.iso`

1. Navigate to **Storage** -> **Images**, then click the "**Create image**" button to create a new image:
   {{< image path="/images/ISO/20-vm-newimg.png" align="center" width="90%" mb="20px">}}

2. Fill the **name** and optionally description for the new image. Choose "**CD-ROM**" type and use "**PATH/URL**" option to enter the downloaded ISO location. Click **Next** to proceed.
   {{< image path="/images/ISO/37-vm-winiso.png" align="center" width="90%" mb="20px">}}

3. Select the datastore to save your image. Caution: Check the size of the raw image to upload, and ensure there is enough space available for it in the target datastore. Once selected, proceed with "**Next**" and then "**Finish**" buttons.

{{< image path="/images/ISO/22-vm-datastore.png" align="center" width="90%" mb="20px">}}

4. As we have the file on disk already, image processing will start immediatelly (no upload). Nevertheless, Windows ISO is large and it may take longer than previously tested Linux image so be patient while the new image remains in LOCKED state.

{{< image path="/images/ISO/38-vm-winlocked.png" align="center" width="90%" mb="20px">}}

5. You can proceed once Sunstone displays the new image on the Images screen as READY

{{< image path="/images/ISO/39-vm-winready.png" align="center" width="90%" mb="20px">}}

6. Now create an empty disk for Windows installation. Click the "**Create image**" button again to create a new image, but this time choose "**Empty disk image**" option and set **60GB** size. Toggle "**Make Persistent**" and click "**Next**"
   {{< image path="/images/ISO/42-vm-windisk.png" align="center" width="90%" mb="20px">}}

7. Select the datastore to save your image. Once selected, proceed with "**Next**" and then "**Finish**" buttons.
   {{< image path="/images/ISO/22-vm-datastore.png" align="center" width="90%" mb="20px">}}

8. Now you will need to create a new VM template using the registered Windows image. Navigate to **Templates -> VM Templates**, then click the "**Create template**" button to create a new VM template.

{{< image path="/images/ISO/26-vm-createtemplate.png" align="center" width="90%" mb="20px">}}

9. On the template screen, select **KVM** for the hypervisor. Use the "**Profile**" list to load optimized defaults and set the physical/virtual CPU and memory settings for the VM template. Click **Next**.

{{< image path="/images/ISO/40-vm-winconfig1.png" align="center" width="90%" mb="20px">}}

10. On the **Advanced Options** screen, select the **Storage** tab, then click **Attach disk***

{{< image path="/images/ISO/28-vm-templateattachdisk.png" align="center" width="90%" mb="20px">}}

10. Select **Image** option

{{< image path="/images/ISO/29-vm-templateimage.png" align="center" width="90%" mb="20px">}}

11. Choose the Windows ISO  image and click "**Next**".

{{< image path="/images/ISO/43-vm-winattachiso.png" align="center" width="90%" mb="20px">}}

12. On the "Advanced" tab ensure it's in Read-only mode and choose SCSI/SATA in BUS field.

{{< image path="/images/ISO/50-vm-winsata.png" align="center" width="90%" mb="20px">}}

13. Next, attach the drivers "ONE_WIN_Drivers" disk bundled with PoC ISO:
    {{< image path="/images/ISO/55-vm-windrivers.png" align="center" width="90%" mb="20px">}}

14. Similarily, attach the empty disk :

{{< image path="/images/ISO/44-vm-winattachempty.png" align="center" width="90%" mb="20px">}}
and on its "**Advanced**" tab ensure it's <u>not</u> in Read-only mode and choose SCSI/SATA in BUS field.
{{< image path="/images/ISO/51-vm-winnoro.png" align="center" width="90%" mb="20px">}}

14. As a result, you should have three images attached now: CDROM and OS:

{{< image path="/images/ISO/45-vm-windisksattached.png" align="center" width="90%" mb="20px">}}

15. Now you are back on the "Advanced options" pane. Switch to the "**OS & CPU**" tab. 
    Ensure that boot order is correct and both devices selected as boot candidates:
    {{< image path="/images/ISO/52-vm-winboot.png" align="center" width="90%" mb="20px">}}
    
    Most of the values are populated thanks to the optimized Windows profile you have chosen earlier. The only thing to decide is the **TPM** version, according to the model supported by your host. Usual choice is "**tpm-tis**".

{{< image path="/images/ISO/41-vm-winconfig2.png" align="center" width="90%" mb="20px">}}

16. Proceed with "**Next**" button on following panes till "**Finish**". The new template will appear on the list:

{{< image path="/images/ISO/46-vm-wintemplate.png" align="center" width="90%" mb="20px">}}

17. Select the new template and click on "**Instantiate**"

{{< image path="/images/ISO/47-vm-wininstantiate.png" align="center" width="90%" mb="20px">}}

18. Follow the process as described in chapter 4.3, points 4-9. After finish, you should see the new VM in RUNNING state. From the VMs list, select the Windows VM and click on options (three dots), then launch VNC console

{{< image path="/images/ISO/48-vm-winVNC.png" align="center" width="90%" mb="20px">}}

19. Windows installer should boot and you can proceed with installation.

{{< image path="/images/ISO/54-vm-wininstall.png" align="center" width="90%" mb="20px">}}

Note: the generic Windows installation ISO has a very short timeout to confirm booting (Press any key to boot from this CD/DVD). If your VNC console shows boot error, keep the console window open and in another browser tab force VM reboot with "**Hard reboot**" option. Now you should manage to press any key and start Windows installation.

{{< image path="/images/ISO/49-vm-winreboot.png" align="center" width="90%" mb="20px">}}

Alternatively, you may use a sys-prepped Windows cloud image of your choice to save time. In such case you just need to create a VM template with one disk (no CD) - the Windows cloud image. 

20. During the installation, browse ONE_WIN_Drivers cdrom device to find appropriate virtio-scsi drivers and install them.

{{< image path="/images/ISO/56-vm-windrivers2.png" align="center" width="90%" mb="20px">}}

Go through the Windows installation steps. Virtual Machine will be rebooted a few times according to the installation procedure.

Complete installation steps after reboot and install next packages from the ONE_WIN_Drivers cdrom:

- one-context

- virtio-win-guest-tools
  {{< image path="/images/ISO/57-vm-wincontext.png" align="center" width="90%" mb="20px">}}
21. Once the installation of Windows has been completed, and all packages are installed you can perform a sysprep procedure and power off the VM. Next steps include changing Windows_11 OS image type from persistent to non persistent. That way you can have an ephemeral Windows instance for spawning VDIs or clone the prepared VM to distribute among users. Windows use cases differ significantly, therefore PoC test run finishes at successful Windows machine run without further customization. 
