---
title: "Managing Provisions"
date: "2025-02-17"
description:
categories:
pageintoc: "222"
tags:
weight: "3"
---

<a id="provision-operations"></a>

<!--# Managing Provisions -->

In OneForm, Provisions represent fully-deployed Clusters or infrastructure stacks. Each Provision is associated with a specific cloud or on-premises Provider and contains OpenNebula resources such as Hosts, datastores, and Virtual Networks.

Here you will find details on how to:

* [Scale existing Provisions by adding or removing hosts](#scaling-provisions)
* [Manage public IP assignments](#managing-public-ips)
* [Recover failed Provisions](#recovering-failed-provisions)
* [Cancel an active Provision operation](#cancelling-an-active-operation)
* [Delete a Provision](#deleting-a-cluster)

## Scaling Provisions

Select the tab for your preferred interface to view the procedure to scale Provisions:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the Sunstone interface, go to **Infrastructure -> Clusters** and select the Cluster you want to scale. Open the **Host** tab:
{{< image
  pathDark="images/oneform/oneprovision/operations/dark/add_host_operation.png"
  path="images/oneform/oneprovision/operations/light/add_host_operation.png"
  alt="Scaling provisions"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
To increase the number of hosts in a running Provision, use `oneprovision add-host`. Alternatively, execute `oneprovision del-host` command to decrease hosts. These operations trigger an update of the infrastructure through Terraform and Ansible.

Do not set `--amount` and `--host-ids` simultaneously since the operation will fail. You must choose one method of scaling at a time:


* Add Hosts:

  ```bash
  oneprovision add-host <provision_id> --amount <number_of_hosts>
  ```

  Example:

  ```bash
  oneprovision add-host 42 --amount 2
  ```

* Remove Hosts:

  ```bash
  oneprovision del-host <provision_id> --host-ids <id1,id2,...>
  ```

  Example:

  ```bash
  oneprovision del-host 42 --host-ids 105,106
  ```

{{% /tab %}}

{{% tab header="API"%}}

Use the following example requests, replacing the appropriate parameters for your Provision:

* Add Hosts

```bash
curl -X POST "https://oneform.example.server/api/v1/provisions/<id>/hosts" \
  -u "username:password" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2
  }'
```

* Remove Hosts

```bash
curl -X DELETE "https://oneform.example.server/api/v1/provisions/<id>/hosts?ids=101,102" \
  -u "username:password"
```
<br>

For further details about the API, see the [OneForm API Reference]({{% relref "/product/integration_references/system_interfaces/oneform_api.md" %}}).
{{% /tab %}}

{{< /tabpane >}}

## Managing Public IPs

Select the tab for your preferred interface to view the procedure to manage public IPs:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the Sunstone interface, go to **Infrastructure -> Clusters** and select the Cluster you want to scale. Open the **VNet** tab and click **Add public IPs**:
{{< image
  pathDark="images/oneform/oneprovision/operations/dark/add_ip_operation_modal.png"
  path="images/oneform/oneprovision/operations/light/add_ip_operation_modal.png"
  alt="Managing IPs"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
For Provisions that support public networking like AWS and i3Dnet, dynamically manage Elastic IPs through the following commands:

* Add Public IPs

  ```bash
  oneprovision add-ip <provision_id> --amount <number_of_ips>
  ```

  Example:

  ```bash
  oneprovision add-ip 42 --amount 1
  ```

* Remove a Public IP by Address Range (AR ID)

  ```bash
  oneprovision del-ip <provision_id> --ar-id <ar_id>
  ```

  Example:

  ```bash
  oneprovision del-ip 42 --ar-id 7
  ```

To view current IP allocations, run `oneprovision show <id>` and inspect the associated public network address ranges (ARs).
{{% /tab %}}

{{% tab header="API"%}}
Use the following example requests, replacing the appropriate parameters for your Provision:

* Add Public IPs

```bash
curl -X POST "https://oneform.example.server/api/v1/provisions/<id>/public-network/ips" \
  -u "username:password" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 3
  }'
```

* Remove a Public IP

```bash
curl -X DELETE "https://oneform.example.server/api/v1/provisions/<id>/public-network/ips/42" \
  -u "username:password"
```
<br>
For further details about the API, see the [OneForm API Reference]({{% relref "/product/integration_references/system_interfaces/oneform_api.md" %}}).
{{% /tab %}}

{{< /tabpane >}}

## Recovering Failed Provisions

Recovering a Provision is a non-destructive operation that attempts to resume from the last recoverable state within its internal lifecycle.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the **Cluster Logs** view, if a Cluster installation fails. Click the **Retry** icon in the top right hand corner of the page:
{{< image
  pathDark="images/oneform/oneprovision/operations/dark/retry_operation_cluster_logs.png"
  path="images/oneform/oneprovision/operations/light/retry_operation_cluster_logs.png"
  alt="Managing IPs"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}
If a Provision fails during deployment, recover it by re-triggering its last failed action:

```bash
oneprovision recover <provision_id>
```

To force recovery even if the Provision is in an unexpected state:

```bash
oneprovision recover <provision_id> --force
```
{{% /tab %}}

{{% tab header="API"%}}
Use the following example request, replacing the appropriate parameters for your Provision:
```bash
curl -X POST "https://oneform.example.server/api/v1/provisions/<id>/recover" \
  -u "username:password" \
  -H "Content-Type: application/json" \
  -d '{}'
```
<br>

For further details about the API, see the [OneForm API Reference]({{% relref "/product/integration_references/system_interfaces/oneform_api.md" %}}).
{{% /tab %}}
{{< /tabpane >}}


## Cancelling an Active Operation

Use cancellation to request that OneForm stops the active lifecycle operation of a
Provision. The request is accepted asynchronously; it does not delete the Provision
or its resources. Only the user that started the operation, or a member of the
`oneadmin` group, can request cancellation.

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
Still in development
{{% /tab %}}

{{% tab header="CLI"%}}

To request cancellation of the active lifecycle operation of a Provision, run:

```bash
oneprovision cancel <provision_id>
```

{{% /tab %}}

{{% tab header="API"%}}

Use the following example request, replacing the appropriate parameter for your
Provision:

```bash
curl -X POST "https://oneform.example.server/api/v1/provisions/<id>/cancel" \
  -u "username:password"
```

{{% /tab %}}
{{< /tabpane >}}

## Deleting a Cluster

Deleting a Cluster triggers the following actions when infrastructure remains:
* Terraform destroy
* Ansible cleanup tasks
* OpenNebula object removal

{{< alert title="Important" type="warning" >}}
Once deleted, the associated Cluster and resources cannot be recovered. Always verify the state and content of the Provision before proceeding.
{{< /alert >}}

Select the tab for your preferred interface to view the procedure to delete a Cluster:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
In the Sunstone interface, go to **Infrastructure -> Clusters** and select the Cluster you want to deprovision. Click **Deprovision** and then **Accept**:
{{< image
  pathDark="images/oneform/oneprovision/operations/dark/deprovision_cluster.png"
  path="images/oneform/oneprovision/operations/light/deprovision_cluster.png"
  alt="Managing IPs"
>}}
{{% /tab %}}

{{% tab header="CLI"%}}

To delete all infrastructure associated with a Provision and its corresponding
OpenNebula resources, run:

```bash
oneprovision delete <provision_id>
```

Use `--force` to start deprovisioning from any state or when the Provision has unmanaged resources.

If deprovisioning cannot be completed because of an uncontrolled error, you can
remove only the Provision document:

```bash
oneprovision delete <provision_id> --from-db
```

{{< alert type="warning" >}}
**Important:** Use `--from-db` only as a last resort. It removes only the OneForm Provision
document; it does **not** delete the OpenNebula objects or resources created at
the external provider. An administrator must manually identify and remove every
remaining resource in both environments.
{{< /alert >}}

{{% /tab %}}

{{% tab header="API"%}}

```bash
curl -X DELETE "https://oneform.example.server/api/v1/provisions/<id>?force=true" \
  -u "username:password"
```

To remove only the Provision document, use `from_db=true` instead of `force=true`.
<br>

For further details about the API, see the [OneForm API Reference]({{% relref "/product/integration_references/system_interfaces/oneform_api.md" %}}).
{{% /tab %}}

{{< /tabpane >}}
