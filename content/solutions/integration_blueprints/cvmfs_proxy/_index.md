---
title: "CernVM-FS Proxy"
linkTitle: "CernVM-FS Proxy"
date: "2026-09-24"
description: ""
categories:
pageintoc: "15"
tags:
type: docs
weight: "2"
no_list: true
---

[CernVM-FS](https://cernvm.cern.ch/fs/), the CernVM File System, is a read-only file system developed at CERN to distribute software to many machines. Each machine mounts it under `/cvmfs` and downloads a file over HTTP only when a program reads it. The [EESSI](https://www.eessi.io/) scientific software catalogue reaches every machine this way.

The CernVM-FS documentation asks each site to put a caching proxy between its clients and the internet. The CernVM-FS Proxy appliance of the Community Marketplace is that proxy, one VM with Squid on port 3128. Each file comes from the internet once, and every later client reads it from the cache of the proxy. The clients can be VMs, the workers of a OneSlurm cluster, the pods of a OneKS cluster or the Open OnDemand Service.

## Deploy the Proxy

1. On the Front-end, as `oneadmin`, export the appliance from the Community Marketplace. You get an image and a VM template.

   ```
   onemarketapp export 'CernVM-FS Proxy' cvmfs-proxy --datastore default
   ```

2. Instantiate the VM template on a Virtual Network with internet access on ports 80 and 8000. The default VM has 2 vCPU, 2 GB of memory and a 30 GB system disk. The wizard has these inputs.

   | Tab | Input | Default | Description |
   |---|---|---|---|
   | Access | `ONEAPP_ACCESS_CLIENTS_NETWORKS` | empty | Networks that may use the proxy, separated by spaces, for example `10.0.0.0/24 192.168.1.0/24`. Empty allows only the network of the first NIC of the proxy. |
   | Access | `ONEAPP_ACCESS_DESTINATIONS_DOMAINS` | `.cern.ch .gridpp.rl.ac.uk .opensciencegrid.org .eessi.science` | Domains the proxy may download from. Add the domain of another public repository to use it. |
   | Cache | `ONEAPP_CACHE_SIZE_DISK` | `20000` | Disk cache in MB. |
   | Cache | `ONEAPP_CACHE_SIZE_MEMORY` | `1024` | Memory cache in MB. |
   | Cache | `ONEAPP_CACHE_DISK_ENABLED` | `NO` | Keep the disk cache on a second disk. Add that disk in the **Storage** tab of the **Advanced options** step of the same wizard, for example an empty volatile disk. The proxy finds the disk and formats it when it is blank. |
   | Cache | `ONEAPP_CACHE_DISK_DEVICE` | empty | Device of the second disk, only needed when the VM has more than one extra disk. |

3. Wait about one minute. The VM reports `READY=YES` and publishes the URL of the proxy as `CVMFS_PROXY_URL`. In Sunstone, open the VM and read the value in the **Template** tab, under **User Template**, next to `READY`. From the command line, run this.

   ```
   onevm show <VM_ID> | grep CVMFS_PROXY_URL
   CVMFS_PROXY_URL="http://192.168.100.191:3128"
   ```

   A wrong input stops the boot, and the reason appears as `ERROR` in the same place. The VM publishes these values through OneGate, and without OneGate the URL is `http://<IP of the first NIC>:3128`, also written in `/etc/one-appliance/config` on the VM.

Clients reach the proxy on port 3128, and a client on another network needs a route to it. The proxy answers a client with a 403 unless its network is in `ONEAPP_ACCESS_CLIENTS_NETWORKS`, and for a client behind a NAT router it checks the address of the router.

## Connect the Clients

Replace `<proxy>` in the commands and files below with the value of `CVMFS_PROXY_URL`, for example `http://192.168.100.191:3128`.

### A Virtual Machine

On an Ubuntu VM, install the CernVM-FS client and the EESSI configuration.

```
wget https://cvmrepo.s3.cern.ch/cvmrepo/apt/cvmfs-release-latest_all.deb
sudo dpkg -i cvmfs-release-latest_all.deb
sudo apt-get update && sudo apt-get install -y cvmfs
wget https://github.com/EESSI/filesystem-layer/releases/download/latest/cvmfs-config-eessi_latest_all.deb
sudo dpkg -i cvmfs-config-eessi_latest_all.deb
```

As root, write these lines in `/etc/cvmfs/default.local`, then apply them with the two commands that follow. `CVMFS_HTTP_PROXY` holds only the proxy, with no `;DIRECT` at the end, so the client never connects to the internet directly. `CVMFS_QUOTA_LIMIT` is the local cache of the client in MB and must fit in its disk.

```
CVMFS_CLIENT_PROFILE="single"
CVMFS_HTTP_PROXY="<proxy>"
CVMFS_QUOTA_LIMIT=10000
```

```
sudo cvmfs_config setup
cvmfs_config probe software.eessi.io
```

The last command prints `Probing /cvmfs/software.eessi.io... OK`.

### The Workers of a OneSlurm Cluster

The OneSlurm workers do not include the CernVM-FS client. Two scripts of the appliance add it. [`oneslurm-start.sh`](https://github.com/OpenNebula/marketplace-community/blob/master/appliances/cvmfs-proxy/clients/oneslurm-start.sh) installs and configures the client on every worker when it boots, including the workers that OneFlow adds later. Slurm then waits until `/cvmfs` works on a new worker before it starts a job there. [`oneslurm-enable-cvmfs.sh`](https://github.com/OpenNebula/marketplace-community/blob/master/appliances/cvmfs-proxy/clients/oneslurm-enable-cvmfs.sh) makes a copy of the OneSlurm service template that runs the first script.

1. On the Front-end, as `oneadmin`, find the ID of the OneSlurm service template with `oneflow-template list`.
2. Download the two scripts and create the copy.

   ```
   base=https://raw.githubusercontent.com/OpenNebula/marketplace-community/master/appliances/cvmfs-proxy/clients
   wget $base/oneslurm-start.sh $base/oneslurm-enable-cvmfs.sh
   bash oneslurm-enable-cvmfs.sh <OneSlurm service template ID>
   ```

   The last command prints the ID of the new service template, whose name ends in `with CernVM-FS`.
3. Instantiate the new service template as usual, and write `<proxy>` in its **CVMFS_HTTP_PROXY** input. The workers reach the proxy with their own addresses, so their network must be the network of the first NIC of the proxy or be listed in `ONEAPP_ACCESS_CLIENTS_NETWORKS`.

The worker disk of OneSlurm is 10 GB, so the start script sets the local cache of each worker to 3000 MB. Tested with OneSlurm 7.4.0-1 on Ubuntu 26.04.

### A OneKS Cluster

Pods mount CernVM-FS through the [cvmfs-csi](https://github.com/cvmfs-contrib/cvmfs-csi) driver, a Kubernetes storage plugin. Deploy the proxy with its first NIC on the public network of the cluster, the network you chose as public when you created the cluster. The nodes reach the proxy through the NAT of the cluster router, so the proxy sees the public address of the router and accepts it with its default setting.

1. **Give the nodes a CPU model with x86-64-v2.** The driver needs a CPU with the x86-64-v2 instruction set, and x86 OneKS nodes boot with the default QEMU CPU, which lacks it, so the driver pods crash with `Fatal glibc error: CPU does not support x86-64-v2`. For new clusters, as `root` on the Front-end, add this block after the `OS = [ ... ]` block of the three files `controlplanes/general/templates/controlplane.erb`, `controlplanes/general/templates/router.erb` and `nodegroups/general/templates/node.erb` in `/var/lib/one/oneks/`.

   ```
   CPU_MODEL = [
     MODEL = "host-passthrough"
   ]
   ```

   Then run `systemctl restart opennebula-ks`. Clusters created after this get the CPU model, and a cluster created before keeps the old CPU, so create a new cluster after the change. `host-passthrough` prevents live migration between Hosts with different CPUs. If you need live migration, use a named model that every Host lists in `KVM_CPU_MODELS` (`onehost show <HOST_ID>`), for example `Nehalem`.

2. **Get the kubeconfig of the cluster.** Run `oneks` as `oneadmin` on the Front-end, where `oneks list clusters` shows `<CLUSTER_ID>`. Run `kubectl` and `helm` there too, or on another machine that has them and reaches the cluster, with a copy of the `kubeconfig` file.

   ```
   oneks show cluster <CLUSTER_ID> --kubeconfig > kubeconfig
   export KUBECONFIG=$PWD/kubeconfig
   ```

3. **Install the driver.** Save these values as `values.yaml`. The chart reads the proxy from the key `cmvfsHttpProxy`, with that spelling, and ignores any other.

   ```
   cmvfsHttpProxy: "<proxy>"
   cache:
     local:
       cvmfsQuotaLimit: 4000
   automountStorageClass:
     create: true
     name: cvmfs
   ```

   ```
   helm install cvmfs-csi oci://registry.cern.ch/kubernetes/charts/cvmfs-csi \
       --version 2.6.0 --namespace cvmfs --create-namespace -f values.yaml
   ```

   After about a minute, `kubectl -n cvmfs get pods` shows the `nodeplugin` pods as `5/5` and `Running`. A pod in `CrashLoopBackOff` runs on a node without the CPU model of step 1.

4. **Mount EESSI in a pod.** Save this manifest as `eessi.yaml`. A pod reaches every repository through a volume claim of the `cvmfs` storage class, and EESSI needs no extra configuration.

   ```
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

   ```
   kubectl apply -f eessi.yaml
   kubectl wait --for=condition=Ready pod/eessi-test --timeout=180s
   kubectl logs eessi-test
   ```

   The log lists `README.eessi`, `defaults`, `host_injections`, `init` and `versions`.

The `cache.local.cvmfsQuotaLimit` value is the local cache of each node in MB and must fit in the node disk, 16 GB for the `small` flavour. Tested with OneKS 7.4 (RKE2 v1.34.2) and cvmfs-csi 2.6.0.

### The Open OnDemand Service

In the instantiate wizard of the Open OnDemand service template, enable **CernVM-FS proxy of your own** in the **Software catalogue** tab, with `ONEAPP_SOFTWARE_PROXY_ENABLED=YES` and `ONEAPP_SOFTWARE_PROXY_URL=<proxy>`. The portal and the workers then use the proxy, and the storage role runs no cache of its own. The portal and the workers reach the proxy from the compute network of the service, so that network needs a route to the proxy and must be in `ONEAPP_ACCESS_CLIENTS_NETWORKS`, unless it is the network of the first NIC of the proxy. See the [Open OnDemand configuration]({{% relref "solutions/integration_blueprints/open_ondemand/configuration/" %}}).

## Check the Proxy

From a client, fetch the file that the EESSI documentation uses to test a proxy. The first line of the answer is `HTTP/1.1 200 OK`, and a 403 means that the network of the client is not in `ONEAPP_ACCESS_CLIENTS_NETWORKS` or that the domain of the server is not in `ONEAPP_ACCESS_DESTINATIONS_DOMAINS`.

```
http_proxy=<proxy> curl --head \
    http://aws-eu-central-s1.eessi.science/cvmfs/software.eessi.io/.cvmfspublished
```

`cvmfs_config stat -v software.eessi.io` on a client shows `through proxy <proxy> (online)`. On the proxy, `/var/log/squid/access.log` lists every request, and `TCP_HIT` or `TCP_MEM_HIT` marks a file served from the cache.

## Limits

* The appliance is x86_64 only.
* One VM is one proxy. For redundancy, deploy two and list both on the clients, for example `CVMFS_HTTP_PROXY="http://10.0.0.5:3128|http://10.0.0.6:3128"`.
