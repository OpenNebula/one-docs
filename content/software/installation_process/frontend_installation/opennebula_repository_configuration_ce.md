---
title: "Manual Installation - OpenNebula Repositories for Community Edition"
linkTitle: "Manual - Repositories (CE)"
date: "2025-02-17"
description:
categories:
pageintoc: "172"
tags:
weight: "5"
---

The Community Edition of OpenNebula offers the full functionality of the Cloud Management Platform. You can configure the Community Edition repositories as follows:

### AlmaLinux/RHEL

Some dependencies require enabling the CodeReady Linux Builder repository:

```shell
crb enable
```

To add the OpenNebula repositories, execute the following commands as user `root`:

**RHEL 9, 10**

```shell
cat << "EOT" > /etc/yum.repos.d/opennebula.repo
[opennebula]
name=OpenNebula Community Edition
baseurl=https://downloads.opennebula.io/repo/{{< release >}}/RedHat/$releasever/$basearch
enabled=1
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT
yum makecache
```

**AlmaLinux 9, 10**

```shell
cat << "EOT" > /etc/yum.repos.d/opennebula.repo
[opennebula]
name=OpenNebula Community Edition
baseurl=https://downloads.opennebula.io/repo/{{< release >}}/AlmaLinux/$releasever/$basearch
enabled=1
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT
yum makecache
```

### Debian/Ubuntu

{{< alert title="Note" color="success" >}}
If the commands below fail, ensure you have `gnupg`, `wget` and `apt-transport-https` packages installed and retry:

```shell
apt-get update
apt-get -y install gnupg wget apt-transport-https
```
{{< /alert >}}

First, add the repository signing GPG key on the Front-end by executing the following as user `root`:

{{< alert title="Note" color="success" >}}
If `/etc/apt/keyrings` does not exist, create it:

```shell
mkdir -p /etc/apt/keyrings
```{{< /alert >}}

```shell
wget -q -O- https://downloads.opennebula.io/repo/repo2.key | gpg --dearmor --yes --output /etc/apt/keyrings/opennebula.gpg
```

**Debian 12**

```shell
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://downloads.opennebula.io/repo/{{< release >}}/Debian/12 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Debian 13**

```shell
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://downloads.opennebula.io/repo/{{< release >}}/Debian/13 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 22.04**

```shell
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://downloads.opennebula.io/repo/{{< release >}}/Ubuntu/22.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 24.04**

```shell
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://downloads.opennebula.io/repo/{{< release >}}/Ubuntu/24.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

**Ubuntu 26.04**

Ubuntu 26.04 ships Node.js 22 in its base repositories, but OpenNebula FireEdge requires Node.js 20, which is provided by the OpenNebula repository. Add an APT pin so that `apt` installs Node.js 20 from the OpenNebula repository instead of the newer version shipped by Ubuntu:

```shell
cat << "EOT" > /etc/apt/preferences.d/opennebula-nodejs
Package: nodejs
Pin: release o=OpenNebula
Pin-Priority: 600
EOT
echo "deb [signed-by=/etc/apt/keyrings/opennebula.gpg] https://downloads.opennebula.io/repo/{{< release >}}/Ubuntu/26.04 stable opennebula" > /etc/apt/sources.list.d/opennebula.list
apt-get update
```

### SUSE

#### SUSE Linux Enterprise Server 15 SP7

Execute the following commands as user `root`:

```shell
arch=$(uname -m)

SUSEConnect -p PackageHub/15.7/$arch
SUSEConnect -p sle-module-public-cloud/15.7/$arch
SUSEConnect -p sle-module-desktop-applications/15.7/$arch

rpm --import https://downloads.opennebula.io/repo/repo2.key

cat << "EOT" > /etc/zypp/repos.d/opennebula.repo
[opennebula]
name=OpenNebula Community Edition
enabled=1
autorefresh=1
baseurl=https://downloads.opennebula.io/repo/{{< release >}}/SLES/15/$basearch
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

cat << "EOT" > /etc/zypp/repos.d/opennebula.repo
[opennebula]
name=OpenNebula Community Edition
enabled=1
autorefresh=1
baseurl=https://downloads.opennebula.io/repo/{{< release >}}/openSUSE/16/$basearch
gpgkey=https://downloads.opennebula.io/repo/repo2.key
gpgcheck=1
repo_gpgcheck=1
EOT

zypper ar -f https://download.opensuse.org/repositories/science/openSUSE_Leap_16.0/ science
zypper refresh
```

## Next Steps

After configuring the OpenNebula Community Edition repositories, you can proceed to install the OpenNebula Front-end. Continue to the [Single Front-end Installation Documentation]({{% relref "software/installation_process/frontend_installation/frontend_install/" %}}) to complete the installation.