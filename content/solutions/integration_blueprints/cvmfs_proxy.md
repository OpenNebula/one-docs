---
title: "Deploy the CernVM-FS Proxy"
linkTitle: "CernVM-FS Proxy"
cardTitle: "CernVM-FS Proxy"
date: "2026-10-26"
description: ""
categories:
tags:
type: docs
weight: "1"
---

[CernVM-FS](https://cernvm.cern.ch/fs/), the CernVM File System, is a read-only file system developed at CERN to distribute software to many machines. Each machine mounts it under `/cvmfs` and downloads a file over HTTP only when a program reads it. The [EESSI](https://www.eessi.io/) scientific software catalogue reaches every machine this way.

The CernVM-FS documentation requests users to put a caching proxy between its clients and the internet to improve performance, reduce internet traffic, and reduce load on the distribution infrastructure. The CernVM-FS Proxy appliance of the Community Marketplace is that proxy, a single VM with [Squid](https://www.squid-cache.org/) on port 3128. Each file comes from the internet once, and every later client reads it from the cache of the proxy. The clients can be VMs, workers of a OneSlurm Cluster, pods of a OneKS Cluster or the Open OnDemand Service.

## Deploy the Proxy

1. On the Front-end, as `oneadmin`, export the appliance from the Community Marketplace. An image and a VM template are imported:

   ```shell
   onemarketapp export 'CernVM-FS Proxy' cvmfs-proxy --datastore default
   ```

2. Instantiate the VM template on a Virtual Network with internet access on ports 80 and 8000. The default VM has 2 vCPU, 2 GB of memory and a 30 GB system disk. The wizard has the following inputs:

   | **Tab** | **Input** | **Default** | **Description** |
   |---|---|---|---|
   | Access | `ONEAPP_ACCESS_CLIENTS_NETWORKS` | empty | Networks that may use the proxy, separated by spaces, for example `10.0.0.0/24 192.168.1.0/24`. If left empty it permits only the network of the first NIC of the proxy. |
   | Access | `ONEAPP_ACCESS_DESTINATIONS_DOMAINS` | `.cern.ch .gridpp.rl.ac.uk .opensciencegrid.org .eessi.science` | Domains the proxy is permitted to download from. Add the domains of other public repositories here to use them. |
   | Cache | `ONEAPP_CACHE_SIZE_DISK` | `20000` | Disk cache in MB. |
   | Cache | `ONEAPP_CACHE_SIZE_MEMORY` | `1024` | Memory cache in MB. |
   | Cache | `ONEAPP_CACHE_DISK_ENABLED` | `NO` | Use this parameter to maintain the disk cache on a second disk. Add that disk in the **Storage** tab of the **Advanced options** step of the same wizard. For example an empty volatile disk. The proxy finds the disk and formats it when it is blank. |
   | Cache | `ONEAPP_CACHE_DISK_DEVICE` | empty | Device of the second disk, only required when the VM has more than one extra disk. |

3. Wait about one minute. The VM reports `READY=YES` and publishes the URL of the proxy as `CVMFS_PROXY_URL`. In Sunstone, open the VM and read the value in the **Template** tab, under **User Template**, next to `READY`. From the command line, run the following command:

   ```shell
   onevm show <VM_ID> | grep CVMFS_PROXY_URL
   CVMFS_PROXY_URL="http://192.168.100.191:3128"
   ```

   An incorrect input parameter prevents boot, and the reason appears as `ERROR` in the same place. The VM publishes these values through OneGate, and without OneGate the URL is `http://<IP of the first NIC>:3128`, also saved in `/etc/one-appliance/config` on the VM.

Clients can reach the proxy on port 3128, and a client on another network needs an established route to reach it. The proxy answers a client with a 403 unless its network is in `ONEAPP_ACCESS_CLIENTS_NETWORKS`, and for a client behind a NAT router it checks the address of the router.

## Connect the Clients

Replace `<proxy>` in the commands and files below with the value of `CVMFS_PROXY_URL`, for example `http://192.168.100.191:3128`.

### A Virtual Machine

On an Ubuntu VM, install the CernVM-FS client and the EESSI configuration:

```shell
wget https://cvmrepo.s3.cern.ch/cvmrepo/apt/cvmfs-release-latest_all.deb
sudo dpkg -i cvmfs-release-latest_all.deb
sudo apt-get update && sudo apt-get install -y cvmfs
wget https://github.com/EESSI/filesystem-layer/releases/download/latest/cvmfs-config-eessi_latest_all.deb
sudo dpkg -i cvmfs-config-eessi_latest_all.deb
```

As root, open `/etc/cvmfs/default.local` with an editor and add the following lines: 

```
CVMFS_CLIENT_PROFILE="single"
CVMFS_HTTP_PROXY="<proxy>"
CVMFS_QUOTA_LIMIT=10000
```

`CVMFS_HTTP_PROXY` holds only the proxy, with no `;DIRECT` at the end, so the client never connects to the internet directly. `CVMFS_QUOTA_LIMIT` is the local cache of the client in MB and must fit in its disk.

Then apply these parameters with the following commands:

```shell
sudo cvmfs_config setup
cvmfs_config probe software.eessi.io
```

The last command should output `Probing /cvmfs/software.eessi.io... OK`.

### The Workers of a OneSlurm Cluster

The OneSlurm workers do not include the CernVM-FS client. Two scripts included with the appliance include it. [`oneslurm-start.sh`](https://github.com/OpenNebula/marketplace-community/blob/master/appliances/cvmfs-proxy/clients/oneslurm-start.sh) installs and configures the client on every worker when it boots, including the workers that OneFlow later adds. Slurm then waits until `/cvmfs` is functioning on a new worker before proceeding with a job there. [`oneslurm-enable-cvmfs.sh`](https://github.com/OpenNebula/marketplace-community/blob/master/appliances/cvmfs-proxy/clients/oneslurm-enable-cvmfs.sh) makes a copy of the OneSlurm service template that runs the first script.

1. On the Front-end, as `oneadmin`, find the ID of the OneSlurm service template with `oneflow-template list`.
2. Download the two scripts and create the copy:

   ```shell
   base=https://raw.githubusercontent.com/OpenNebula/marketplace-community/master/appliances/cvmfs-proxy/clients
   wget $base/oneslurm-start.sh $base/oneslurm-enable-cvmfs.sh
   bash oneslurm-enable-cvmfs.sh <ONESLURM_SERVICE_TEMPLATE_ID>
   ```

   The last command prints the ID of the new service template, whose name ends in `with CernVM-FS`.
3. Instantiate the new service template as usual, and enter `<proxy>` in its **CVMFS_HTTP_PROXY** input. The workers reach the proxy with their own addresses, so their network must be the network of the first NIC of the proxy or be listed in `ONEAPP_ACCESS_CLIENTS_NETWORKS`.

{{< alert title="Important" type="info" >}}
The default worker disk size of OneSlurm is 10 GB, so the start script sets the local cache of each worker to 3000 MB. Tested with OneSlurm 7.4.0-1 on Ubuntu 26.04.{{< /alert >}}

### A OneKS Cluster

Kubernetes pods mount CernVM-FS through the [cvmfs-csi](https://github.com/cvmfs-contrib/cvmfs-csi) driver, a Kubernetes storage plugin. Deploy the proxy with its first NIC on the public network of the Cluster (the network you chose as the public network when you created the Cluster). The nodes reach the proxy through the NAT of the Cluster router, so the proxy sees the public address of the router and accepts it with its default setting.

1. **Give the Nodes a CPU Model with x86-64-v2**: The driver needs a CPU with the x86-64-v2 instruction set, and x86 OneKS nodes boot with the default QEMU CPU, which lacks it, so the driver pods crash with `Fatal glibc error: CPU does not support x86-64-v2`. For new Clusters, as `root` on the Front-end, add this block after the `OS = [ ... ]` block of the three following files in `/var/lib/one/oneks/`:

    * `controlplanes/general/templates/controlplane.erb`
    * `controlplanes/general/templates/router.erb`
    * `nodegroups/general/templates/node.erb`

   ```
   CPU_MODEL = [
     MODEL = "host-passthrough"
   ]
   ```

   Then restart the OneKS service `systemctl restart opennebula-ks`. Clusters created after this modification get the CPU model, and a Cluster created before keeps the old CPU, therefore it is necessary to create a new Clusters instead of reusing old ones. `host-passthrough` prevents live migration between Hosts with different CPUs. If you need live migration, use a named model that every Host lists in `KVM_CPU_MODELS` (`onehost show <HOST_ID>`), for example `Nehalem`.

2. **Get the kubeconfig of the Cluster**: Run `oneks` as `oneadmin` on the Front-end command line, where `oneks list clusters` shows `<CLUSTER_ID>`. Run `kubectl` and `helm` there too, or on another machine that has them and reaches the Cluster, with a copy of the `kubeconfig` file.

   ```shell
   oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
   export KUBECONFIG=$PWD/kubeconfig
   ```

3. **Install the Driver**: Save these values in `values.yaml`. The chart reads the proxy from the key `cmvfsHttpProxy`, with that case-sensitive spelling, and ignores any other:

   ```yaml
   cmvfsHttpProxy: "<proxy>"
   cache:
     local:
       cvmfsQuotaLimit: 4000
   automountStorageClass:
     create: true
     name: cvmfs
   ```
   Install the chart with Helm: 

   ```shell
   helm install cvmfs-csi oci://registry.cern.ch/kubernetes/charts/cvmfs-csi \
       --version 2.6.0 --namespace cvmfs --create-namespace -f values.yaml
   ```

   After about a minute, `kubectl -n cvmfs get pods` should show the `nodeplugin` pods as `5/5` and `Running`. If a node does not have the CPU model defined in Step 1., a pod may get stuck in `CrashLoopBackOff`.

4. **Mount EESSI in a Pod**: Save the following manifest as `eessi.yaml`. A pod reaches every repository through a volume claim of the `cvmfs` storage class, and EESSI needs no extra configuration:

   ```yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: cvmfs
   spec:
     accessModes: [ReadOnlyMany]
     storageClassName: cvmfs
     resources:
       requests:
         storage: 1
   ---
   apiVersion: v1
   kind: Pod
   metadata:
     name: eessi-test
   spec:
     containers:
     - name: test
       image: busybox:1.36
       command: ["sh", "-c", "ls /cvmfs/software.eessi.io && sleep 3600"]
       volumeMounts:
       - name: cvmfs
         mountPath: /cvmfs
         mountPropagation: HostToContainer
     volumes:
     - name: cvmfs
       persistentVolumeClaim:
         claimName: cvmfs
   ```

   Apply the manifest with kubectl:

   ```shell
   kubectl apply -f eessi.yaml
   kubectl wait --for=condition=Ready pod/eessi-test --timeout=180s
   kubectl logs eessi-test
   ```

   The log lists `README.eessi`, `defaults`, `host_injections`, `init` and `versions`.

{{< alert title="Important" type="info" >}}
The `cache.local.cvmfsQuotaLimit` value is the local cache of each node in MB and must fit in the node disk, 16 GB for the `small` flavour. Tested with OneKS 7.4 (RKE2 v1.34.2) and cvmfs-csi 2.6.0.{{< /alert >}}

### The Open OnDemand Service

In the instantiate wizard of the Open OnDemand service template, enable **CernVM-FS proxy of your own** in the **Software catalogue** tab, with `ONEAPP_SOFTWARE_PROXY_ENABLED=YES` and `ONEAPP_SOFTWARE_PROXY_URL=<proxy>`. The portal and the workers then use the proxy, and the storage role runs no cache of its own. The portal and the workers reach the proxy from the compute network of the service, so that network needs a route to the proxy and must be in `ONEAPP_ACCESS_CLIENTS_NETWORKS`, unless it is the network of the first NIC of the proxy. See the [Open OnDemand configuration]({{% relref "platform_services/slurm/integrations/open_ondemand/operations.md" %}}).

## Checking the Proxy

From a client, fetch the file that the EESSI documentation uses to test a proxy. The first line of the answer is `HTTP/1.1 200 OK`, and a 403 means that the network of the client is not in `ONEAPP_ACCESS_CLIENTS_NETWORKS` or that the domain of the server is not in `ONEAPP_ACCESS_DESTINATIONS_DOMAINS`.

```shell
http_proxy=<proxy> curl --head \
    http://aws-eu-central-s1.eessi.science/cvmfs/software.eessi.io/.cvmfspublished
```

`cvmfs_config stat -v software.eessi.io` on a client shows `through proxy <proxy> (online)`. On the proxy, `/var/log/squid/access.log` lists every request, and `TCP_HIT` or `TCP_MEM_HIT` marks a file served from the cache.

## Limitations

* The appliance is x86_64 only.
* A single VM is only a single proxy. To add redundancy, deploy two and list both on the clients, for example `CVMFS_HTTP_PROXY="http://10.0.0.5:3128|http://10.0.0.6:3128"`.
