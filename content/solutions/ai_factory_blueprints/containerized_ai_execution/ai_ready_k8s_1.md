---
title: Deployment of AI-ready Kubernetes 1
linkTitle: AI-ready Kubernetes 1
weight: 5
tags: ['AI', 'Kubernetes']
---

## Install OneKS

```shell
sudo apt install -y opennebula-ks
```

### Set up transparent proxy:

```shell
nano /var/lib/one/remotes/etc/vnm/OpenNebulaNetwork.conf
```

```yaml
:tproxy:
  - :remote_addr: 192.168.150.1 # Front-end IP
    :remote_port: 5030
    :service_port: 5030
  - :remote_addr: 192.168.150.1 # Front-end IP
    :remote_port: 2633
    :service_port: 2633
```

### Start OneKS

```shell
sudo systemctl start opennebula-ks.service
```

```shell
sudo systemctl status opennebula-ks.service
```

### Update Nodegroup Template

```shell
nano /var/lib/one/oneks/nodegroups/general/templates/node.erb
```

Add PCI section to the template:

```
...
PCI=[
  CLASS="0302",
  DEVICE="26b9",
  VENDOR="10de" ]
```

Restart the OneKS service:

```shell
sudo systemctl restart opennebula-ks.service
```

## Install kubectl

{{< tabpane text=true right=false >}}
{{% tab header="**Architecture**:" disabled=true /%}}

{{% tab header="x86-64"%}}
```shell
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```
{{% /tab %}}

{{% tab header="ARM64"%}}
```shell
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl"
```
{{% /tab %}}
{{< /tabpane >}}

Then install kubectl:

```shell
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## Create a Private Network
