---
title: "OneGate Configuration"
linkTitle: "OneGate"
date: "2025-02-17"
description:
categories:
pageintoc: "163"
tags:
weight: "5"
---

<a id="onegate-conf"></a>

<!--# OneGate Configuration -->

The OneGate server allows **Virtual Machines to pull and push information from/to OpenNebula**. It can be used with both the KVM and LXC hypervisors if the guest operating system has preinstalled the OpenNebula [contextualization package]({{% relref "product/virtual_machines_operation/guest_operating_systems/creating_images#os-install" %}}). It’s a dedicated daemon installed by default as part of the [Single Front-end Installation]({{% relref "frontend_install" %}}), but can be deployed independently on a different machine. The server is distributed as an operating system package `opennebula-gate` with the system service `opennebula-gate`.

Read more in [OneGate Usage]({{% relref "product/virtual_machines_operation/multi-vm_workflows/onegate_usage#onegate-usage" %}}).

## Recommended Network Setup

To use the OneGate Service, VMs must have connectivity to the service. We recommend setting up a dedicated Virtual Network, ideally on a separate VLAN, for OneGate access. To accomplish this, simply add a Virtual Network Interface (NIC) to the OneGate Service network for the VMs requiring access to the service. In cases where you’re deploying a multi-tier service, you can just add the virtual router to the OneGate Service network. The recommended network layout is illustrated in the diagram below:

![onegate_net](/images/onegate_net.png)

## Configuration

The OneGate configuration file can be found in `/etc/one/onegate-server.conf` on your Front-end. It uses **YAML** syntax, with the parameters listed in the table below.

{{< alert title="Note" type="info" >}}
After a configuration change, the OneGate server must be [restarted]({{% relref "onegate#onegate-conf-service" %}}) to take effect.{{< /alert >}}

{{< alert title="Tip" type="tip" >}}
For a quick view of any changes in configuration file options in maintenance releases, check the Resolved Issues page in the [Release Notes]({{% relref "../../../software/release_information/release_notes" %}}) for the release. Please note that even in the case of changes (such as a new option available), you do *not* need to update your configuration files unless you wish to change the application’s behavior.{{< /alert >}}

| Parameter                   | Description                                                                                                                                                                                                                                                                                                                                                              |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Server Configuration**    |                                                                                                                                                                                                                                                                                                                                                                          |
| `:one_xmlrpc`               | Endpoint of OpenNebula XML-RPC API                                                                                                                                                                                                                                                                                                                                       |
| `:server`                  | OneGate Sinatra server configuration options |
| `:server` / `:bind`        | Host/IP where OneGate will listen |
| `:server` / `:port`        | Port where OneGate will listen |
| `:ssl_server`               | SSL proxy URL that serves the API (set if is being used)                                                                                                                                                                                                                                                                                                                 |
| **Authentication**          |                                                                                                                                                                                                                                                                                                                                                                          |
| `:auth`                     | Authentication driver for incoming requests.<br/><br/>* `onegate` based on tokens provided in VM context                                                                                                                                                                                                                                                                 |
| `:core_auth`                | Authentication driver to communicate with OpenNebula core<br/><br/>* `cipher` for symmetric cipher encryption of tokens<br/>* `x509` for X.509 certificate encryption of tokens<br/><br/>For more information, visit the [Cloud Server Authentication]({{% relref "software/development/cloud_auth#cloud-auth" %}}) reference. |
| **OneFlow Endpoint**        |                                                                                                                                                                                                                                                                                                                                                                          |
| `:oneflow_server`           | Endpoint where the OneFlow server is listening                                                                                                                                                                                                                                                                                                                           |
| **Permissions**             |                                                                                                                                                                                                                                                                                                                                                                          |
| `:permissions`              | By default OneGate exposes all the available API calls. Each of the actions can be enabled/disabled in the server configuration.                                                                                                                                                                                                                                         |
| `:restricted_attrs`         | Attributes that cannot be modified when updating a VM template                                                                                                                                                                                                                                                                                                           |
| `:restricted_actions`       | Actions that cannot be performed on a VM                                                                                                                                                                                                                                                                                                                                 |
| `:vnet_template_attributes` | Attributes of the Virtual Network template that will be retrieved for Virtual Networks                                                                                                                                                                                                                                                                                   |
| **Logging**                 |                                                                                                                                                                                                                                                                                                                                                                          |
| `:debug_level`              | Logging level. Values: `0` for ERROR level, `1` for WARNING level, `2` for INFO level, `3` for DEBUG level                                                                                                                                                                                                                                                               |
| `:expire_delta`             | Default interval for timestamps. Tokens will be generated using the same timestamp for this interval of time. THIS VALUE CANNOT BE LOWER THAN EXPIRE_MARGIN.                                                                                                                                                                                                             |
| `:expire_margin`            | Tokens will be generated if time > EXPIRE_TIME - EXPIRE_MARGIN                                                                                                                                                                                                                                                                                                           |

The `:server` section is passed directly to the Sinatra OneGate server. Any Sinatra setting supported by the version shipped with OpenNebula can be defined under this key. For example, in addition to `:bind` and `:port`, advanced deployments may configure other Sinatra options in the same section, such as `:host_authorization`:

```yaml
:server:
  :bind: 0.0.0.0
  :port: 5030
  :host_authorization:
    :permitted_hosts:
      - one.example.com
      - 192.168.0.5
```

In the default configuration, the OneGate server will only listen to requests coming from `localhost`. Because the OneGate needs to be accessible remotely from the Virtual Machines, you need to change the `:bind` parameter under `:server` in `/etc/one/onegate-server.conf` to a public IP of your Front-end Host or to `0.0.0.0` (to work on all IP addresses configured on Host).

### Configure OpenNebula

Before Virtual Machines can communicate with OneGate, you need to edit [/etc/one/oned.conf]({{% relref "oned#oned-conf-onegate" %}}) and set the OneGate endpoint in parameter `ONEGATE_ENDPOINT`. This endpoint (IP/hostname) must be reachable from the Virtual Machines over the network!

```default
ONEGATE_ENDPOINT = "http://one.example.com:5030"
```

Restart the OpenNebula service to apply changes.

<a id="onegate-conf-service"></a>

## Service Control and Logs

Change the server running state by managing the operating system service `opennebula-gate`.

To start, restart, or stop the server, execute one of:

```default
# systemctl start   opennebula-gate
# systemctl restart opennebula-gate
# systemctl stop    opennebula-gate
```

To enable or disable automatic start upon Host boot, execute one of:

```default
# systemctl enable  opennebula-gate
# systemctl disable opennebula-gate
```

Server **logs** are located in `/var/log/one` in the following files:

- `/var/log/one/onegate.log`
- `/var/log/one/onegate.error`

Other logs are also available in Journald. Use the following command to show these:

```default
# journalctl -u opennebula-gate.service
```

## Advanced Setup

### Example: Use Transparent OneGate Proxy to Improve Security

Add the following config snippet to the `~oneadmin/remotes/etc/vnm/OpenNebulaNetwork.conf` file on Front-end machines:

```default
:tproxy:
# OneGate service.
- :service_port: 5030
  :remote_addr: 10.11.12.13 # OpenNebula Front-end VIP
  :remote_port: 5030
```

Propagate config to hypervisor Hosts, execute as `oneadmin` on the leader Front-end machine:

```default
$ onehost sync -f
```

Deploy a guest Virtual Machine and test OneGate connectivity from within:

```default
$ onegate vm show
```

Read more in [Transparent Proxies]({{% relref "../../virtual_machines_operation/virtual_machines_networking/tproxy#tproxy" %}}).

<!-- Example: Deployment Behind TLS Proxy
------------------------------------

This is an **example** of how to configure Nginx as an SSL/TLS proxy for OneGate on Ubuntu.

1. Update your package lists and install Nginx:

.. code::

    # apt-get update
    # apt-get -y install nginx

2. Get a trusted SSL/TLS certificate. For testing, we'll generate a self-signed certificate:

.. code::

    # cd /etc/one
    # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/one/cert.key -out /etc/one/cert.crt

3. Use the following content as an Nginx configuration. NOTE: Change the ``one.example.com`` variable for your own domain:

.. code::

    server {
      listen 80;
      return 301 https://$host$request_uri;
    }

    server {
      listen 443;
      server_name ONEGATE_ENDPOINT;

      ssl_certificate           /etc/one/cert.crt;
      ssl_certificate_key       /etc/one/cert.key;

      ssl on;
      ssl_session_cache  builtin:1000  shared:SSL:10m;
      ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
      ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
      ssl_prefer_server_ciphers on;

      access_log            /var/log/nginx/onegate.access.log;

      location / {

        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        # Fix the “It appears that your reverse proxy set up is broken" error.
        proxy_pass          http://localhost:5030;
        proxy_read_timeout  90;

        proxy_redirect      http://localhost:5030 https://ONEGATE_ENDPOINT;
      }
    }

4. Configure OpenNebula (``/etc/one/oned.conf``) with OneGate endpoint, e.g.:

.. code::

    ONEGATE_ENDPOINT = "https://one.example.com"

5. Configure OneGate (``/etc/one/onegate-server.conf``) with new secure OneGate endpoint in ``:ssl_server``, e.g.:

.. code::

    :ssl_server: https://one.example.com

6. Restart all services:

.. code::

    # systemctl restart nginx
    # systemctl restart opennebula
    # systemctl restart opennebula-gate -->
