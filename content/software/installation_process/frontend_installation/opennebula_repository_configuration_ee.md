---
title: "Manual Installation - OpenNebula Repositories for Enterprise Edition"
linkTitle: "Manual - Repositories (EE)"
date: "2025-02-17"
description:
categories:
pageintoc: "172"
tags:
weight: "5"
---

OpenNebula Systems provides the OpenNebula Enterprise Edition (EE) to customers with an active support subscription. To distribute the packages of the Enterprise Edition there is a private repository accessible only to Enterprise Edition customers that contains all packages (including major, minor, and maintenance releases). You only need to change your repository configuration on your OpenNebula Front-end once per major release and you’ll have access to every package in that series. OpenNebula's private repositories contain all OpenNebula released packages.

{{< alert title="Important" color="success" >}}
You should have received credentials, token in format `username:password` to access these private repositories with your OpenNebula EE subscription. Replace `<user>` and `<password>` in the examples below with your customer-specific credentials.{{< /alert >}}

### AlmaLinux/RHEL

Some dependencies require enabling the CodeReady Linux Builder repository:

```shell
crb enable
```

To add the OpenNebula Enterprise Edition repository, execute the following commands for your respective OS as user `root`:

**RHEL 9, 10**

```shell
cat << "EOT" > /etc/yum.repos.d/opennebula.repo
[opennebula]
name=OpenNebula Enterprise Edition
baseurl=https://enterprise.opennebula.io/repo/{{< release >}}/RedHat/$releasever/$basearch
username=<user>
password=<password>
enabled=1
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT
chmod 600 /etc/yum.repos.d/opennebula.repo
dnf makecache
```

**AlmaLinux 9, 10**

```shell
cat << "EOT" > /etc/yum.repos.d/opennebula.repo
[opennebula]
name=OpenNebula Enterprise Edition
baseurl=https://enterprise.opennebula.io/repo/{{< release >}}/AlmaLinux/$releasever/$basearch
username=<user>
password=<password>
enabled=1
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT
chmod 600 /etc/yum.repos.d/opennebula.repo
dnf makecache
```

### Debian/Ubuntu

{{< alert title="Note" color="success" >}}
If the commands below fail, ensure you have `gnupg`, `wget` and `apt-transport-https` packages installed and retry:

```shell
apt-get update
apt-get -y install gnupg wget apt-transport-https
```
{{< /alert >}}

First, add the repository signing GPG key on the Front-end by executing as user `root`:

{{< alert title="Note" color="success" >}}
If `/etc/apt/keyrings` does not exist, create it:

```shell
mkdir -p /etc/apt/keyrings
```{{< /alert >}}

```shell
wget -q -O- https://downloads.opennebula.io/repo/repo2.key | gpg --dearmor --yes --output /etc/apt/keyrings/opennebula.gpg
```

And then continue with repository configuration:

**Debian 12**

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/{{< release >}}/Debian/12 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Debian 13**

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/{{< release >}}/Debian/13 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 22.04**

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/{{< release >}}/Ubuntu/22.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 24.04**

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/{{< release >}}/Ubuntu/24.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 26.04**

Ubuntu 26.04 ships Node.js 22 in its base repositories, but OpenNebula FireEdge requires Node.js 20, which is provided by the OpenNebula repository. Add an APT pin so that `apt` installs Node.js 20 from the OpenNebula repository instead of the newer version shipped by Ubuntu:

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
cat << "EOT" > /etc/apt/preferences.d/opennebula-nodejs
Package: nodejs
Pin: release o=OpenNebula
Pin-Priority: 600
EOT
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/{{< release >}}/Ubuntu/26.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

### SUSE

#### SUSE Linux Enterprise Server 15 SP7

Execute the following as user `root`:

```shell
arch=$(uname -m)

SUSEConnect -p PackageHub/15.7/$arch
SUSEConnect -p sle-module-desktop-applications/15.7/$arch
SUSEConnect -p sle-module-public-cloud/15.7/$arch

rpm --import https://downloads.opennebula.io/repo/repo2.key

mkdir -p /etc/zypp/credentials.d
cat << "EOT" > /etc/zypp/credentials.d/opennebula.conf
username=<user>
password=<password>
EOT
chmod 600 /etc/zypp/credentials.d/opennebula.conf

cat << "EOT" > /etc/zypp/repos.d/opennebula.repo
[opennebula]
name=OpenNebula Enterprise Edition
enabled=1
autorefresh=1
baseurl=https://enterprise.opennebula.io/repo/{{< release >}}/SLES/15/$basearch?credentials=opennebula.conf
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT

zypper refresh
```

#### openSUSE Leap 16.0

openSUSE Leap 16.0 requires the OpenNebula repository and the openSUSE Science repository for SciPy. Execute the following as user `root`:

```shell
rpm --import https://downloads.opennebula.io/repo/repo2.key

mkdir -p /etc/zypp/credentials.d
cat << "EOT" > /etc/zypp/credentials.d/opennebula.conf
username=<user>
password=<password>
EOT
chmod 600 /etc/zypp/credentials.d/opennebula.conf

cat << "EOT" > /etc/zypp/repos.d/opennebula.repo
[opennebula]
name=OpenNebula Enterprise Edition
enabled=1
autorefresh=1
baseurl=https://enterprise.opennebula.io/repo/{{< release >}}/openSUSE/16/$basearch?credentials=opennebula.conf
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT

zypper ar -f https://download.opensuse.org/repositories/science/openSUSE_Leap_16.0/ science
zypper refresh
```

{{< alert title="Note" color="success" >}}
You can point to a specific 7.2.x version by changing the occurrence of shorter version number 7.2 in any of the above commands to the full three components. For instance, to point to version 7.2.1 on Ubuntu 22.04, use the following command:

```shell
cat << "EOT" > /etc/apt/auth.conf.d/opennebula.conf
machine enterprise.opennebula.io
login <user>
password <password>
EOT
chmod 600 /etc/apt/auth.conf.d/opennebula.conf
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://enterprise.opennebula.io/repo/7.2.1/Ubuntu/22.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```
{{< /alert >}}

## Next Steps

After configuring the OpenNebula Enterprise Edition repositories, you can proceed to install the OpenNebula Front-end. Continue to the [Single Front-end Installation Documentation]({{% relref "software/installation_process/frontend_installation/frontend_install/" %}}) to complete the installation.
