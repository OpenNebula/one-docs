---
title: "Marketplaces in Sunstone"
date: "2025-02-17"
description:
categories:
pageintoc: "193"
tags:
weight: "3"
---

<a id="sunstone-marketplaces"></a>

<!--# Managing Marketplaces in Sunstone -->

The [Sunstone web UI]({{% relref "../../../product/control_plane_configuration/graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}) allows you to graphically manage Marketplaces. Within Sunstone, open the left-hand pane then select **Storage** -> **Marketplaces** to perform the following operations:

* [Create a marketplace]({{% relref "#sunstone-marketplaces-create" %}})
* [Update a marketplace]({{% relref "#sunstone-marketplaces-update" %}})
* [Delete a marketplace]({{% relref "#sunstone-marketplaces-delete" %}})
* [Enable or disable a marketplace]({{% relref "#sunstone-marketplaces-enable" %}})
* [Change the owner or the group of a marketplace]({{% relref "#sunstone-marketplaces-change" %}})
* [Check details of a marketplace]({{% relref "#sunstone-marketplaces-details" %}})
* [See the appliances that have a marketplace]({{% relref "#sunstone-marketplaces-appliances" %}})

{{< alert title="Note" type="info" >}}
Only [OpenNebula Systems]({{% relref "../public_marketplaces/opennebula#market-one" %}}), [LinuxContainers]({{% relref "../public_marketplaces/lxc#market-linux-container" %}}), [HTTP]({{% relref "../private_marketplaces/market_http#market-http" %}}) and [S3]({{% relref "../private_marketplaces/market_s3#market-s3" %}}) Marketplaces can be created with Sunstone.{{< /alert >}} 

{{< image
  pathDark="/images/marketplaces/dark/marketplace_dashboard_dark.png"
  path="images/marketplaces/light/marketplace_dashboard_light.png"
  alt="Marketplace dashboard" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-create"></a>

## Create a Marketplace

1. Click on the **+ Create Marketplace** button:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_create_dark.png"
  path="images/marketplaces/light/marketplace_create_light.png"
  alt="Marketplace create" align="center" width="90%" mb="20px"
>}}

2. Fill in the name, description, and type of the Marketplace:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_create_step1_dark.png"
  path="images/marketplaces/light/marketplace_create_step1_light.png"
  alt="Marketplace create 1" align="center" width="90%" mb="20px"
>}}


3. Fill in the fields of the Marketplace. Depending on the Marketplace type, these fields are different. Please see [Public]({{% relref "../public_marketplaces/index#public-marketplaces" %}}) and [Private]({{% relref "../private_marketplaces/index#private-marketplaces" %}}) Marketplaces documentation:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_create_step2_dark.png"
  path="images/marketplaces/light/marketplace_create_step2_light.png"
  alt="Marketplace create 2" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-update"></a>

## Update a Marketplace

Select a Marketplace and click on the update button:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_update_dark.png"
  path="images/marketplaces/light/marketplace_update_light.png"
  alt="Marketplace update" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-delete"></a>

## Delete a Marketplace

Select a Marketplace and click on the delete button:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_delete_dark.png"
  path="images/marketplaces/light/marketplace_delete_light.png"
  alt="Marketplace delete" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-enable"></a>

## Enable or Disable a Marketplace

Select a Marketplace and click on the enable/disable menu:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_disable_dark.png"
  path="images/marketplaces/light/marketplace_disable_light.png"
  alt="Marketplace disable" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-change"></a>

## Change the Owner or the Group of a Marketplace

Select a Marketplace and click on the change owner/change group menu:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_change_owner1_dark.png"
  path="images/marketplaces/light/marketplace_change_owner1_light.png"
  alt="Marketplace owner" align="center" width="90%" mb="20px"
>}}

Select the new owner and press **Continue**:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_change_owner2_dark.png"
  path="images/marketplaces/light/marketplace_change_owner2_light.png"
  alt="Marketplace owner" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-details"></a>

## Check Details of a Marketplace

Select a Marketplace and click on Info tab to see its details:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_info_dark.png"
  path="images/marketplaces/light/marketplace_info_light.png"
  alt="Marketplace info" align="center" width="90%" mb="20px"
>}}

<a id="sunstone-marketplaces-appliances"></a>

## See Appliances Available in a Marketplace

Select a Marketplace and click on Apps tab to see the Appliances available:

{{< image
  pathDark="/images/marketplaces/dark/marketplace_appliances_dark.png"
  path="/images/marketplaces/light/marketplace_appliances_light.png"
  alt="Marketplace appliances" align="center" width="90%" mb="20px"
>}}
