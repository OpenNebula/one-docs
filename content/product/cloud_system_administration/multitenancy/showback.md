---
title: "Showback"
date: "2025-02-17"
description:
categories:
pageintoc: "120"
tags:
weight: "8"
---

The Showback toolset reports resource usage cost and allows the integration with Chargeback and billing platforms. The toolset generates Showback reports using the information retrieved from OpenNebula.

## Set the VM Cost

Each VM Template can optionally define a cost (see the [syntax here]({{% relref "product/operation_references/configuration_references/template#template-showback-section" %}})). The cost is defined as **cost per cpu per hour**, and **cost per memory MB per hour**. The cost units are abstract and their equivalent to monetary or other cost metrics have to be defined in each deployment. In Sunstone, go to **Templates -> VM Templates**, choose a template and select **Update**, the cost section can be found in the lower left part of the **General** view:

{{< image pathDark="/images/sunstone/common/dark/vm_template_cost.png"
        path="/images/sunstone/common/light/vm_template_cost.png" 
        alt="Sunstone accounting view" align="center" width="70%" mb="20px">}}

There is a default cost that will be applied to VM Templates without a cost defined. It can be set in the [oned.conf file]({{% relref "product/operation_references/opennebula_services_configuration/oned#oned-conf-default-showback" %}}).

Using this cost schema allows users to see the storage cost when resizing the Virtual Machine instances.

{{< image pathDark="/images/sunstone/common/dark/vm_template_cost_field.png"
        path="/images/sunstone/common/light/vm_template_cost_field.png" 
        alt="Sunstone accounting view" align="center" width="70%" mb="20px">}}

{{< image pathDark="/images/sunstone/common/dark/storage_cost_field.png"
        path="/images/sunstone/common/light/storage_cost_field.png" 
        alt="Sunstone accounting view" align="center" width="70%" mb="20px">}}

{{< alert title="Warning" type="warning" >}}
If your users can access the [Sunstone ‘user’ view]({{% relref "fireedge_sunstone_views#fireedge-suns-views" %}}), it’s important to set a default cost. These users can manage their own Templates, which won’t have a specific cost assigned.{{< /alert >}} 

## Calculate Monthly Reports

Before the cost reports can be seen by the users, the administrator has to generate them. To create the monthly cost reports use Sunstone or the `oneshowback` command:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}

Log into Sunstone as an administrator user and go to the Settings section. Select a start date and a end date and press **Calculate Showback** button:

{{< image pathDark="/images/sunstone/common/dark/showback_calculate.png"
        path="/images/sunstone/common/light/showback_calculate.png" 
        alt="Sunstone accounting view" align="center" width="90%" mb="20px">}}

{{% /tab %}}

{{% tab header="CLI"%}}

To calculate monthly reports, run the `oneshowback command`as the oneadmin user. 

```shell
oneshowback calculate -h
Usage: oneshowback [options]
    -s, --start TIME                 First month of the data
    -e, --end TIME                   Last month of the data
```

Some examples:

* To calculate all records, starting from March up to today:

  ```shell
  oneshowback calculate --start "03/2016"
  ```

* To calculate only September:

  ```shell
  oneshowback calculate --start "09/2016" --end "09/2016"
  ```

When you run this command, the OpenNebula core reads all the accounting records and calculates the total cost for each month. The records include the total cost of the month, and basic information about the VM and its owner. This information is then stored in the database to be consumed with the `oneshowback list` command.

The monthly cost of each VM is calculated as the sum of:

* `CPU_COST` \* `CPU` \* `HOURS`
* `MEMORY_COST` \* `MEMORY` \* `HOURS`
* `DISK_COST` \* `DISK_SIZE` \* `HOURS`

The number of hours is calculated as the total number of hours that a VM has been `active`. This accounts for every VM state that keeps Host resources secured, like `poweroff` or `suspended`, but not in `stopped` or `undeploy`.

Optionally, compute CPU and MEMORY cost only for VMs in `running` state, see `SHOWBACK_ONLY_RUNNING` in [oned.conf file]({{% relref "product/operation_references/opennebula_services_configuration/oned#oned-conf-default-showback" %}})

Important considerations:

* If the time range includes the current month, OpenNebula will calculate the cost up to today’s date.
* There is a timer in the front-end, called `opennebula-showback.timer` that automatically calculates the Showback every day. Check the status by running `systemctl status opennebula-showback.timer`
* Existing records can be re-calculated. This can be useful to update old records when a VM is renamed or the owner is changed. In this case, the cost of previous months will be also assigned to the new user.

**Bear in mind that this is a resource intensive operation**. For big deployments, add the `--start` option to process only the last missing months.

{{% /tab %}}
{{< /tabpane >}}


## Retrieve Monthly Reports

View, as an administrator or a regular user, your monthly Showback reports from Sunstone or the CLI:

{{< tabpane text=true right=false >}}
{{% tab header="**Interfaces**:" disabled=true /%}}

{{% tab header="Sunstone"%}}
1. Log into Sunstone.
2. Go to either **Users** or **Groups**.
3. Click on a user or a group.
4. Select the **Showback** tab.

{{< image pathDark="/images/sunstone/common/dark/showback_user.png"
        path="/images/sunstone/common/light/showback_user.png" 
        alt="Sunstone accounting view" align="center" width="90%" mb="20px">}}
{{% /tab %}}

{{% tab header="CLI"%}}

```shell
## USAGE
list
        Returns the showback records
        valid options: start_time, end_time, userfilter, group, xml, json, verbose, help, version, describe, list, csv, user, password, endpoint

## OPTIONS
     -s, --start TIME          First month of the data
     -e, --end TIME            Last month of the data
     -u, --userfilter user     User name or id to filter the results
     -g, --group group         Group name or id to filter the results
     -x, --xml                 Show the resource in xml format
     -j, --json                Show the resource in json format
     -v, --verbose             Verbose mode
     -h, --help                Show this message
     -V, --version             Show version and copyright information
     --describe                Describe list columns
     -l, --list x,y,z          Selects columns to display with list command
     --csv                     Write table in csv format
     --user name               User name used to connect to OpenNebula
     --password password       Password to authenticate with OpenNebula
     --endpoint endpoint       URL of OpenNebula xmlrpc frontend
```

{{% /tab %}}

{{< /tabpane >}}

## Disable Showback in Sunstone

Showback reports can be disabled in any of the Sunstone views by modifying the yaml file called `user-tab.yaml` in the corresponding view ([See Sunstone views to get more information]({{% relref "fireedge_sunstone_views#fireedge-suns-views" %}})):

```yaml
...
info-tabs:
  showback:
    enabled: false
```

## Tuning and Extending

To integrate the Showback reports with external tools, you can get the CLI output as **xml**, **json**, or **csv** data.

```shell
oneshowback list -u cloud_user --list YEAR,MONTH,VM_ID,COST --csv
YEAR,MONTH,VM_ID,COST
2015,10,4258,1824279.62
2015,10,4265,433749.03
2015,11,4258,34248600
```

Developers interacting with OpenNebula using the Ruby bindings can use the [VirtualMachinePool.showback method](http://docs.opennebula.io/doc/{{< version >}}/oca/ruby/OpenNebula/VirtualMachinePool.html#showback-instance_method) to retrieve Showback information and filter and order by multiple parameters.