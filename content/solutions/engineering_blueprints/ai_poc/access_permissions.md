---

title: "User Access and Management"
linkTitle: "User Access and Management"
description: ""
weight: 3

---

OpenNebula's multi-tenancy model enables AI-ready clouds to be managed in a secure and flexible manner. Users can be allocated different privileges and access rights and be granted access to different resources. Users can be allocated super-admin level rights with the capacity to modify most aspects of cloud architecture down to simple tenant access levels only allowed to create, modify or consume specifically allocated resources. 

This guide demonstrates how OpenNebula's multi-tenancy functionality works with a step-by-step tutorial through creating and managing users and groups. 

## Before Starting

To complete this guide, you need to first be connected via VPN to hosted infrastructure provided by OpenNebula as part of an AI Factory PoC process. If you are not connected via VPN, please follow the [Connection Guide]({{% relref "solutions/engineering_blueprints/ai_poc/connecting/" %}}). If you are not already participating in a PoC process, please [contact the OpenNebula sales team](https://opennebula.io/contact/).

You will be given credentials via email for the following two OpenNebula user accounts, make sure to have them at hand:

* **poc-operator**
* **poc-tenant**

{{< alert title="Tip" type="info" >}}
You need to switch regularly between different accounts in Sunstone during the course of this guide. To avoid repeatedly signing in and out you can use an incognito window or a different browser.
{{< /alert >}}

## Step 1: Sign In

Sign into Sunstone with the **poc-operator** account credentials. Ensure the **Admin group** view is activated (in the top left corner) and go to **System -> Groups**. Click on the **poc-tenants** group in the list to open its information panel. Verify that in the **Users** tab you can see the **Add users** and **Edit administrators** buttons and that the **Admin** column of the **poc-operator** row of the user table shows **Yes**. This verifies that you have group management permissions:


{{< image
  pathDark="/images/poc/ai_poc/dark/poc_operator_groups.png"
  path="/images/poc/ai_poc/light/poc_operator_groups.png"
  alt="POC operator view" align="center" width="90%" mb="20px"
>}}

## Step 2: Create a Temporary Group and User

Close the **poc-tenants** group details and select **+ Create Group**. Name the group **poc-temp-group**. Leave the default settings and step through the group creation wizard with the **Next** button, then in the last step click **Finish**.

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_operator_create_group.png"
  path="/images/poc/ai_poc/light/poc_operator_create_group.png"
  alt="POC operator create group" align="center" width="90%" mb="20px"
>}}

After creating the group, you will see the group in the list in the **System -> Groups** view. Click on the item in the list to open the information panel. Now go to **System -> Users** and press **+ Create User**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_temp_user.png"
  path="/images/poc/ai_poc/light/poc_temp_user.png"
  alt="POC operator create user" align="center" width="90%" mb="20px"
>}}

Name the user **poc-temp-user** and leave the authentication type as **core**. Input a secure password and keep a note of it. Press **Next** then select the **poc-temp-group** as the **Primary Group**. Press **Next**, but do not select a **Secondary Group**, it is not mandatory. Click **Finish**. 

## Step 3: Assign a Resource Quota to the Temporary Group

Return to **System -> Groups**. Select the **poc-temp-group** and verify that the **poc-temp-user** is included in the **Users** tab. Select the **Quota** tab. Leave **Type** as **VM Quota**. Don't adjust the **Cluster ID** field. Choose **Virtual Machines** in **Identifier** and set the **Value** as 1. Then click **Apply**:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_quota.png"
  path="/images/poc/ai_poc/light/poc_quota.png"
  alt="POC operator quota" align="center" width="90%" mb="20px"
>}}

## Step 4: Test the Resource Limit

Sign out of the **poc-operator** account or in a separate browser window sign into the **poc-temp-user** account with the credentials you recorded in step 2. Go to **Storage -> Apps** and search for the **Alpine Linux 3.24** appliance. Import it:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_alpine.png"
  path="/images/poc/ai_poc/light/poc_alpine.png"
  alt="POC Alpine template" align="center" width="90%" mb="20px"
>}}

Leave the name as is is, press **Next** and choose the **default** datastore in the import wizard and click **Finish**.

Go to **Templates -> VM Templates** and select the **Alpine Linux 3.24** template, click on it and then click on the play icon to instantiate it:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_instantiate.png"
  path="/images/poc/ai_poc/light/poc_instantiate.png"
  alt="POC Alpine template instantiate" align="center" width="90%" mb="20px"
>}}

Name the VM and set the **Number of instances** to 2:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vm_name.png"
  path="/images/poc/ai_poc/light/poc_vm_name.png"
  alt="POC Alpine template instantiate" align="center" width="90%" mb="20px"
>}}

Click **Next** leave the **Advanced options** as they are and click **Finish**. You will see the following warning:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_vm_limit.png"
  path="/images/poc/ai_poc/light/poc_vm_limit.png"
  alt="POC Alpine template instantiate" align="center" width="90%" mb="20px"
>}}

This warning demonstrates that the resource limit you applied for the **poc-temp-group** of one Virtual Machine has been enforced by OpenNebula's multi-tenancy functionality. In the **Instances -> VMs** view you will see the single VM that was successfully launched within the group's resource quota:

{{< image
  pathDark="/images/poc/ai_poc/dark/poc_single_vm.png"
  path="/images/poc/ai_poc/light/poc_single_vm.png"
  alt="POC Alpine template instantiate" align="center" width="90%" mb="20px"
>}}

## Next Steps

Congratulations! You have now successfully utilized OpenNebula's multi-tenancy model to create and manage groups and tenants and apply resource quotas. You can learn more about OpenNebula's multi-tenancy functionality in the [Multi-tenancy Documentation]({{% relref "product/cloud_system_administration/multitenancy/auth_overview/" %}}).

You can now proceed to the next step in this PoC guided tour of OpenNebula's AI Factory functionality in the [Deploying a GPU-enabled Virtual Machine Guide]({{% relref "solutions/engineering_blueprints/ai_poc/gpu_vm/" %}}).

## PoC Success Criteria

Completing this guide fulfills the following PoC success criteria:

* [SC16]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create additional users
* [SC17]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create additional groups
* [SC20]({{% relref "solutions/engineering_blueprints/ee_poc/poc_success_criteria/#platform-administration" %}}): Create and assign quota to group(s)