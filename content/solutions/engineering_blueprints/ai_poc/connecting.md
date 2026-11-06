---

title: "Connecting to the PoC Infrastructure via VPN"
linkTitle: "VPN Connection"
description: ""
weight: 2

---

When participating in a hosted Proof of Concept trial of the OpenNebula system, you will be given access to hosted infrastructure via VPN. This guide details the steps to connect to the VPN with the credentials provided to you by your OpenNebula PoC contact.

## Before You Start

You connect with an OpenVPN profile file plus a personal username and password; setup takes about 5 minutes on any OS.

### What You Receive From Us

* A configuration profile file ending in `.ovpn` (contains your personal certificate)  
* Your **username**  
* Your **password**, sent through a separate channel from the file

### What You Need

* An OpenVPN-compatible client (instructions per OS below)  
* A network that allows outbound **UDP port 2000**. Some corporate or guest networks block it; see Troubleshooting.
* Access to a Unix-like terminal (WSL on Windows)

### What the VPN Gives You

* Access to the PoC environment network **10.16.6.0/24** only: the servers, VMs and Kubernetes endpoints we share with you.  
* Your internet traffic keeps going through your own connection (split tunnel). Only traffic to 10.16.6.0/24 goes through the VPN.

## Windows

Use **OpenVPN Connect**; no route changes are needed.

1. Download and install OpenVPN Connect from [openvpn.net/client](https://openvpn.net/client/).  
2. Open the app and choose **Import Profile** → **Upload File**.  
3. Drag your `.ovpn` file into the window, or click **Browse** and select it.  
4. Enter your **username** and click **Connect**.  
5. Enter your **password** when prompted. Optionally tick **Save password**.  
6. The status turns **Connected**. Go to *Verify the connection* below.

OpenVPN Connect keeps only one profile active at a time. Connecting to this profile disconnects any other OpenVPN profile you have open.

## MacOS

Use **OpenVPN Connect** or **Tunnelblick**; both work without route changes.

**Option A: OpenVPN Connect**

1. Download and install OpenVPN Connect from [openvpn.net/client](https://openvpn.net/client/).  
2. Open the app and choose **Import Profile** → **Upload File**, then drag in your `.ovpn` file.  
3. Enter your **username**, click **Connect**, then enter your **password**.  
4. The status turns **Connected**. Go to *Verify the connection* below.

**Option B: Tunnelblick (free)**

1. Download and install Tunnelblick from [tunnelblick.net](https://tunnelblick.net/).  
2. Double-click your `.ovpn` file and choose **Only Me** when asked who should use it.  
3. Click the Tunnelblick icon in the menu bar → **Connect** with the profile name.  
4. Enter your **username** and **password**.  
5. In **VPN Details → Settings**, keep **Route all IPv4 traffic through the VPN** unchecked (the default).

If you use **Viscosity**, keep **Send all traffic over VPN connection** unchecked in *Edit Connection → Networking*.

## Linux

On NetworkManager you must tick one routing option, otherwise you lose internet access while connected. The openvpn command line needs no changes.

**Option A: NetworkManager (Ubuntu, Fedora and most desktops)**

1. Install the OpenVPN plugin:  
   * Ubuntu/Debian: sudo apt install network-manager-openvpn-gnome  
   * Fedora: sudo dnf install NetworkManager-openvpn-gnome  
2. Open **Settings → Network → VPN → \+** → **Import from file…** and select your `.ovpn` file.  
3. Enter your **username** and **password** in the Identity tab.  
4. Open the **IPv4** tab → **Routes** and tick **Use this connection only for resources on its network**. Do the same in the **IPv6** tab.  
5. Click **Add** (or **Apply**), then switch the VPN on.

Same setup from the terminal (replace \<name\> with the connection name the import prints, and \<username\> with yours):

nmcli connection import type openvpn file your-profile.ovpn  
nmcli connection modify \<name\> vpn.user-name \<username\> ipv4.never-default yes ipv6.never-default yes  
nmcli connection up \<name\> \--ask  
**Option B: openvpn command line**

sudo apt install openvpn        \# Fedora: sudo dnf install openvpn  
sudo openvpn \--config your-profile.ovpn  
Enter your username and password when prompted. Keep the terminal open while you work; press Ctrl+C to disconnect.

## Verify the Connection

A working connection shows a route to 10.16.6.0/24 through the VPN, your normal internet still works, and the PoC endpoint we gave you answers.

1. **Route to the PoC network goes through the VPN**

| **OS** | **Command** | **Expected** |
| :---- | :---- | :---- |
| Windows (PowerShell) | route print \-4 \| findstr 10.16.6 | a 10.16.6.0 line |
| macOS | netstat \-rn \-f inet \| grep 10.16.6 | 10.16.6 via a utun interface |
| Linux | ip route \| grep 10.16.6 | 10.16.6.0/24 ... dev tun0 |

2. **Internet still works:** open any website, or run ping 1.1.1.1.  
3. **PoC endpoint answers:** ping the IP we shared with you, or open the service in your browser (for example the OpenNebula web UI or the Kubernetes API with kubectl).

## Troubleshooting

Most issues come from the local network or from another VPN running at the same time.

| **Symptom** | **Likely cause** | **What to do** |
| :---- | :---- | :---- |
| Connected, but no internet on Linux | NetworkManager sends all traffic through the VPN | Tick *Use this connection only for resources on its network* (IPv4 and IPv6), or run nmcli connection modify \<name\> ipv4.never-default yes ipv6.never-default yes, then reconnect |
| "Authentication failed" | Wrong username or password, or another person's profile | Check upper/lower case. Each profile only works with its own username |
| Connection times out, never connects | Your network blocks outbound UDP port 2000 | Try another network (for example a phone hotspot) or ask your IT team to allow it |
| Connected, but PoC IPs don't answer | Another VPN (often a corporate one) takes all traffic, or your local network also uses 10.16.6.x | Disconnect the other VPN and try again. If your network uses 10.16.6.x, contact us |
| Other OpenVPN profile disconnects | OpenVPN Connect runs one profile at a time | Expected. Switch profiles as needed |

If none of this helps, send us your OS, the client you use and a screenshot or the last lines of the client log.

## Security and Support

Your profile is personal: keep it private and don't share it, even with colleagues.

* Each person gets their own profile, username and password. Ask us for an extra one instead of sharing.  
* The `.ovpn` file contains your private key. Don't post it in chats, tickets or shared drives.  
* If you think your file or password was exposed, tell us and we will revoke it and issue a new one.  
* Access ends when the PoC ends; your profile stops working after that.

