---
title: "Market Driver"
date: "2025-02-17"
description:
categories:
pageintoc: "297"
tags:
weight: "7"
---

<a id="devel-market"></a>

<!--# Market Driver -->

The Market Driver is in charge of managing both Marketplaces and Marketplace Apps.

## Marketplace Drivers Structure

The main drivers are located under `/var/lib/one/remotes/market/<market_mad>`. Marketplaces support the following operations:

| Action    | Description                                                                                                                                                                                                                                             |
|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `create`  | Create a new Marketplace.                                                                                                                                                                                                                               |
| `monitor` | This automatic action discovers the available Marketplace Apps and<br/>monitors the available space of the Marketplace.                                                                                                                                 |
| `delete`  | Removes a Marketplace from OpenNebula. For a Public Marketplace,<br/>it will also remove the Marketplace Apps, but for any other type of<br/>Marketplace this will not remove the Marketplace Apps, and will<br/>only work if the Marketplace is empty. |
| *other*   | Generic actions common to OpenNebula resources are also available:<br/>`update`, `chgrp`, `chown`, `chmod` and `rename`.                                                                                                                                |

As for the Marketplace Apps, they support these actions:

| Action     | Description                                                                                                                                   |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `import`   | Upload a local image to the Marketplace. **NOTE:** This<br/>action can only be done with Marketplaces associated with the<br/>current zone.   |
| `export`   | Export the Marketplace App and download it into a local Datastore.                                                                            |
| `delete`   | Removes a Marketplace App.                                                                                                                    |
| `download` | Downloads a Marketplace App to a file.                                                                                                        |
| *other*    | Generic actions common to OpenNebula resources are also available:<br/>`update`, `chgrp`, `chown`, `chmod`, `rename`, `enable` and `disable`. |

### `monitor`

The monitor action is orchestrated by the `/var/lib/one/remotes/market/<market_mad>/monitor` script.

There are two kinds of `monitor` scripts: those that do not require the discovery of Marketplace Apps, since OpenNebula has created them and so already knows about them; and those that include this discovery, like in the case of the `one/monitor` script to monitor the official OpenNebula Systems Marketplace.

**ARGUMENTS**

`driver_dump_xml market_id`. The `driver_dump_xml` is an XML dump of the driver action encoded in Base 64, which contains all the required information: `market_data`.

**RETURNS**

In the case of simple monitoring with no discovery, the `monitor` action must return a report of the available and used space in the Marketplace in OpenNebula-syntax template format:

```default
USED_MD=<USED_MB>
FREE_MB=<FREE_MB>
TOTAL_MB=<TOTAL_MB>
```

In the case of monitoring with discovery, it must also return the information of each Appliance, encoded in Base64 in the following way (the full APP string has been trimmed for legibility):

```default
APP="TkFNRT0idHR5b..."
APP="TkFNRT0idHR5b..."
APP="TkFNRT0iQ2Fya..."
APP="TkFNRT0iVGVzd..."
APP="TkFNRT0iZ1VzZ..."
APP="TkFNRT0iVnlhd..."
APP="TkFNRT0iZ1VTR..."
APP="TkFNRT0iZGVia..."
...
```

If we unpack one of these APPs we will obtain the following:

```default
NAME="ttylinux - kvm"
SOURCE="http://marketplace.opennebula.systems//appliance/4fc76a938fb81d3517000003/download/0"
IMPORT_ID="4fc76a938fb81d3517000003"
ORIGIN_ID="-1"
TYPE="IMAGE"
PUBLISHER="OpenNebula.org"
FORMAT="raw"
DESCRIPTION="This is a very small image that works with OpenNebula. It's already contextualized. The purpose of this image is to test OpenNebula deployments, without wasting network bandwith thanks to the tiny footprint of this image
(40MB)."
VERSION="1.0"
TAGS="linux, ttylinux,  4.8,  4.10"
SIZE="40"
MD5="04c7d00e88fa66d9aaa34d9cf8ad6aaa"
VMTEMPLATE64="Q09OVEVYVCA9IFsgTkVUV09SSyAgPSJZRVMiLFNTSF9QVUJMSUNfS0VZICA9IiRVU0VSW1NTSF9QVUJMSUNfS0VZXSJdCgpDUFUgPSAiMC4xIgpHUkFQSElDUyA9IFsgTElTVEVOICA9IjAuMC4wLjAiLFRZUEUgID0idm5jIl0KCk1FTU9SWSA9ICIxMjgiCkxPR08gPSAiaW1hZ2VzL2xvZ29zL2xpbnV4LnBuZyI="
```

Which is the Marketplace App template in OpenNebula-syntax format.

### `import`

The `import` action is an special action that involves two driver calls chained one after the other. The involved actors are: `/var/lib/one/remotes/datastore/<ds_mad>/export` and `/var/lib/one/remotes/market/<market_mad>/import`. Note they they aren’t piped together: the core will run the `export` action first, collect the output, and use it for the driver message of the `import` action.

`<ds_mad>/export`:

The job of the export is to:

* Return the required `FORMAT` and `SIZE` and, when available, the `MD5` or `SHA1` checksum.
* Generate an `IMPORT_SOURCE` so the `<market_mad>/import` can copy the Image into the Marketplace.
* Return an opaque `DISPOSE_DATA` value if the export creates temporary resources. The Datastore driver's `dispose_export` action receives this value after the Marketplace import finishes, whether it succeeds or fails.

**ARGUMENTS**

`driver_dump_xml image_id`. The `driver_dump_xml` is an XML dump of the driver action encoded in Base 64, which contains all the required information: `image_data` and `ds_data`.

**RETURNS**

It should return an XML document:

```default
<IMPORT_INFO>
    <IMPORT_SOURCE>$IMPORT_SOURCE</IMPORT_SOURCE>
    <FORMAT>$FORMAT</FORMAT>
    <SIZE>$SIZE</SIZE>
    <MD5>$MD5_SUM</MD5>
    <DISPOSE_DATA>$DRIVER_SPECIFIC_DATA</DISPOSE_DATA>
</IMPORT_INFO>
```

`MD5`, `SHA1`, and `DISPOSE_DATA` are optional. If `DISPOSE_DATA` is present, the same Datastore driver must implement an idempotent `dispose_export` action. See the [`IMPORT_INFO` structure and Datastore export operations]({{% relref "sd#sd-export" %}}) for details.

The legacy `DISPOSE` and `DISPOSE_CMD` fields remain supported for existing Marketplace integrations. New Datastore drivers should use `DISPOSE_DATA` and `dispose_export` instead.

`<market_mad>/import`:

The job of the export is to grab the `IMPORT_SOURCE` and dump it to the backend.

**ARGUMENTS**

`driver_dump_xml image_id`. The `driver_dump_xml` is an XML dump of the driver action encoded in Base 64, which contains all the required information: `app_data`, `market_data`, `image_data` and `ds_data`.

**RETURNS**

It should return this OpenNebula syntax template:

```default
SOURCE="<SOURCE>"
MD5="<MD5>"
SIZE="<SIZE_IN_MB>"
FORMAT="<FORMAT>"
```

Note that typically inside the `import` script we will find a call to the `downloader.sh` like this:

```default
${UTILS_PATH}/downloader.sh $IMPORT_SOURCE -
```

Which will be in turn piped to the target destination in the Marketplace, or in some Market Drivers the target file will appear in the `downloader.sh` command as the destination instead of `-`. Note that this might require extending `downloader.sh` to handle a custom new protocol, like: `s3://`, `rbd://`, etc.

### `export`

The `export` job is again two-fold:

* Create a new image by calling `<ds_mad>/cp`.
* Create a new template, if it exists in the Marketplace App (`VMTEPLATE64`)

There is no specific `<market_mad>` driver file associated with this job, it actually calls an already existing driver, the `<ds_mad>/cp`. Please read the [Storage Driver]({{% relref "sd#sd" %}}) guide to learn more about this driver action.

It is worth noting that the Marketplace App’s `IMPORT_SOURCE` field will be used as the `PATH` argument for the `<ds_mad>/cp` action. Therefore, this action must understand that `IMPORT_SOURCE` which in turn means that `downloader.sh` must understand it too.

### `delete`

This job deletes a Marketplace App.

**ARGUMENTS**

`driver_dump_xml image_id`. The `driver_dump_xml` is an XML dump of the driver action encoded in Base 64, which contains all the required information: `market_data` and `marketapp_data`.

**RETURNS**

No return message.
