---
title: "WHMCS Integration (EE)"
linkTitle: "WHMCS (EE)"
date: "2025-02-17"
categories:
tags:
weight: "1"
aliases:
  - /product/integration_references/billing_extensions/
  - /product/integration_references/billing_extensions/overview/
  - /product/integration_references/billing_extensions/whmcs/
---

## Overview

**WHMCS** (Web Host Manager Complete Solution) is a web Host billing automation platform that can be configured for many uses.  We provide a module for WHMCS that allows you to automate the creation and management of users, groups, and their Access Control Lists in OpenNebula, as well as providing billing based on their usage metrics.

You can define these resource packages to control the usage and cost of your OpenNebula resources.

When an order is accepted in WHMCS, setup is performed: a user and a group are created for the service.  This group will then be assigned a Usage Quota that is defined during the package configuration.

## How Should I Read This Guide

Before reading this guide you should be aware of the [WHMCS Documentation](https://docs.whmcs.com/Documentation_Home) and have it installed on a server that can access your OpenNebula installation.  You should also be familiar with OpenNebula’s [Users]({{% relref "product/cloud_system_administration/multitenancy/manage_users" %}}), [Groups]({{% relref "product/cloud_system_administration/multitenancy/manage_groups" %}}), [Usage Quotas]({{% relref "product/cloud_system_administration/capacity_planning/quotas" %}}), and [Permissions]({{% relref "product/cloud_system_administration/multitenancy/chmod" %}}) management features.

This guide is divided into three parts for this module:

* [Install/Configure](#whmcs-tenants-instcfg)
* [Admin Usage](#whmcs-admin-usage)
* [User Guide](#whmcs-tenants-module-user-guide)

## Hypervisor Compatibility

This guide is compatible with all hypervisors.

<a id="whmcs-tenants-instcfg"></a>

## WHMCS Tenants Module Install/Update

{{< alert title="Warning" type="warning" >}}
You must use PHP 7.4; currently PHP 8.x causes an error when creating the user.
WHMCS Version 9.x has dropped support for PHP 7.x, so please also use the LTS 8.x version of WHMCS.
{{< /alert >}}

The install and update process are essentially identical. The module files can be found in  `/usr/share/one/whmcs` after you have installed the `opennebula-whmcs-tenants` package via your package manager. You just need to merge the `modules` directory to the main WHMCS directory on the server hosting WHMCS. When updating the module just copy the files on top of the existing files and overwrite them. An example command for copying the files is here:

```shell
cp -rf /usr/share/one/whmcs/modules /path/to/web/root/whmcs/.
```

{{< alert title="Note" type="info" >}}
Make sure you download the updated package from the OpenNebula EE repository before doing either an install or an update.{{< /alert >}} 

## WHMCS Tenants Module Configuration

In this section we will go over adding a server and creating the group for it. Configuring a product is covered in [WHMCS Admin Usage](#whmcs-admin-usage).

### Adding a Server

{{< image
  path="/images/integration_blueprints/whmcs_tenants_system_settings.png"
  alt="WHCMS System Settings" align="center" width="90%" mb="20px"
>}}

To configure your WHMCS Tenants Module, first log in to your WHMCS admin area and navigate to **System Settings -> Servers** and click on the button **Add New Server**.

{{< image
  path="/images/integration_blueprints/whmcs_tenants_add_server.png"
  alt="WHMCS Add Server" align="center" width="90%" mb="20px"
>}}

Fill in the **Hostname** for your OpenNebula server. Under the **Server Details** section select **OpenNebula Tenants** as the module and fill in the **Username** and **Password** with a user in the *oneadmin* group in your OpenNebula installation.

Now click the button on top labelled **Go to Advanced Mode**.  This will open a larger form. Fill in a name for the server and scroll down to the bottom to verify that the port and SSL settings are correct. By default, the XML-RPC traffic is not encrypted with SSL so you may need to disable that unless you’ve [set up SSL for XML-RPC](https://support.opennebula.pro/hc/en-us/articles/5101146829585).

Once these are filled out, click the **Test Connection** button to verify the module can authenticate with your OpenNebula server.

Don't forget to click **Save Changes** once this is verified in order to complete adding the server.

### Creating a Server Group

After the server is added it should return you to the list of servers. Here you can click **Create New Group** to make a server group to contain your OpenNebula Server(s).

Fill in the **Name** of your Server Group, then highlight your OpenNebula Server and click **Add** to add it to your new group.  Once this is done, click **Save Changes**.

<a id="whmcs-tenants-admin"></a>

## WHMCS Admin Usage

### Creating a Product Group

Before creating products you should create groups to better organize your offerings.  To create a new product group, navigate to **System Settings -> Products/Services**, then click on the **Create a New Group** button there. Fill in the Product Group Name and any other pieces of this form, such as Template and Payment Gateways, then click **Save Changes** once you’re done.

### Creating a Product

Navigate to **System Settings** -> **Products/Services**.

From the Products/Services page, click on **Create a New Product**.  Select the **Product Type**, **Product Group**, and a **Product Name**.  The **Module** should be **OpenNebula Tenants**.  Once this is all done, click **Continue**.

{{< image
  path="/images/integration_blueprints/whmcs_tenants_new_product.png"
  alt="WHMCS New Product" align="center" width="90%" mb="20px"
>}}

On this page, click on the **Module Settings** tab then select **OpenNebula Tenants** for the **Module Name**, then select your recently created **Server Group**.  Here, you can fill in the maximum resources usable by this product. You can also set the ACL parameters that will be created in OpenNebula for this product.

These resource limits correlate to the [Quota]({{% relref "product/cloud_system_administration/capacity_planning/quotas" %}}) for the Group in OpenNebula, so this will limit the amount of resources used in OpenNebula for each product.  You can also enable Metric Billing and set pricing for each of these metrics:

* IP Addresses
* RAM
* CPU cores
* Supporting Multiple VDCs
* Datastore Images
* Datastore Size
* NETRX
* NETTX

Below the resources you can determine if the User should be automatically set up or if the system should wait for the Administrator to accept the order:

{{< image
  path="/images/integration_blueprints/whmcs_tenants_module_settings.png"
  alt="WHMCS Module Settings" align="center" width="90%" mb="20px"
>}}

{{< alert title="Note" type="info" >}}
For more information about managing VDCs refer to the [Managing VDCs]({{% relref "product/cloud_system_administration/multitenancy/manage_vdcs" %}}) page.{{< /alert >}} 

The **Upgrades** tab can also be a useful feature to make use of. If you create multiple products with different resource quotas, you can select the products here which your users can upgrade to.  You can select multiple products by holding the **Shift** or **Ctrl** key.

### Managing Orders

To view the orders waiting to be accepted navigate to **Orders -> Pending Orders** in the navigation bar. On this page you can view the information about the client and the service they are ordering. Here you can accept, cancel, set as fraud, or delete the orders:

{{< image
  path="/images/integration_blueprints/whmcs_tenants_accept_order.png"
  alt="WHMCS Module Settings" align="center" width="90%" mb="20px"
>}}

If your product is configured to be set up after manually accepting the order, you will need to accept the order created before any changes are made in OpenNebula. This is also true for package upgrades your users might request.

Once orders are set up there is a User, Group, and ACL created which correspond to the Service in WHMCS. Then, the Quota will be created for the Group linked to this order. On the service page for the customer, they will have a Login link.

{{< alert title="Note" type="info" >}}
If there are issues when upgrading products, the user and group may need to be recreated. Any existing VMs can be assigned to the admin user temporarily while this is done. This will be fixed in a future release.{{< /alert >}} 

### Checking Metrics

To view metrics for your customers, navigate to **View/Search Clients** and click on the ID of any user. Click on the **Products/Services** tab, there should be a Metric Statistics section with a table. You can click **Refresh Now** to update the information manually.

<a id="whmcs-tenants-user"></a>

## WHMCS Tenants Module User Guide

### Registering an Account

To register a new account, navigate to the client area of your WHMCS install and then go to **Account -> Register**.  Fill out the following form and proceed with user creation. After it’s completed you should be able to log in as that new user.

### Ordering a New Service

To view the available products, navigate to **Services -> Order New Services**. This page will display all available services which can be purchased.  These can be added to the cart by clicking the corresponding **Order Now** button. After checking out, the new order will be created.

### Upgrading a Service

To upgrade a product, navigate to the product’s page.  On the left side there should be a button to **Upgrade Product**, which should show you a list of available packages to upgrade to. Simply add to the cart and check out similarly to ordering a new service. A new order will be created to upgrade your product.

### Managing Services

When viewing a Product/Service, there should be an action **Login** which redirects users to the OpenNebula interface where can manage their Virtual Machines within the limits that the product allows.
