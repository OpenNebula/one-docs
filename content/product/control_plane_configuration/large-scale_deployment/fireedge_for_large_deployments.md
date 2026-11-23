---
title: "FireEdge for Large Deployments"
date: "2025-02-17"
description:
categories:
pageintoc: "42"
tags:
weight: "3"
---

<a id="fireedge-advance"></a>

<!--# FireEdge for Large Deployments -->

Low-to-medium sized enterprise clouds will typically deploy FireEdge on a single machine with the other OpenNebula Daemons as part. However, this simple deployment can be extended by

- **Improving scalability** of the server for large user pools, usually by deploying FireEdge as a separate application on one or more Hosts.

This guide introduces various deployment options to achieve this. Check also the [API Scalability]({{% relref "scalability#one-scalability-api-tuning" %}}) guide for tips on how to improve FireEdge and OpenNebula Daemon performance.

<a id="fireedge-large-web"></a>

## Deploy in Webserver

Self-contained deployment of [FireEdge]({{% relref "../graphical_user_interface/fireedge_sunstone#fireedge-sunstone" %}}) (using `opennebula-fireedge` system service) is sufficient for small-to-medium installations. This is no longer enough when the service has lots of concurrent users and the number of objects in the system is high (for example, more than 2000 simultaneous Virtual Machines).

The FireEdge server is implemented as a nodejs server. This makes it suitable to run on any server. Also, the service is embedded inside Apache HTTP Server or NGINX. Another advantage is the ability to run FireEdge on multiple servers and balance the load between them.

**Guacamole**

If you want to use Guacamole you need to have it running. You can start this service with the command:

```default
# systemctl enable opennebula-guacd
# systemctl start  opennebula-guacd
```

<a id="fireedge-fs-permissions"></a>

**Filesystem Permissions**

Another thing you have to take into account is the user under which the server will run. The installation sets the permissions for the `oneadmin` user and group, and files like the FireEdge configuration and credentials cannot be read by other users.

```default
# chmod a+x /var
# chmod a+x /var/lib
# chmod a+x /var/lib/one
# chmod a+x /var/lib/one/.one
```

<a id="fireedge-advance-apache-proxy"></a>

### Non-TLS Configuration

If FireEdge is installed and you want to place an apache to forward traffic to FireEdge, you can inside `VirtualHost`. Simply insert the following snippet and **adjust** it to your current configuration.

**Apache**

```default
<VirtualHost *:80>
  ...

  ProxyRequests     off
  ProxyPreserveHost on

  # no proxy for /error/ (Apache HTTPd errors messages)
  ProxyPass /error/ !

  ProxyPass /fireedge http://localhost:2616/fireedge
  ProxyPassReverse /fireedge http://localhost:2616/fireedge

  RewriteEngine on
  RewriteCond %{HTTP:Upgrade} websocket [NC]
  RewriteCond %{HTTP:Connection} upgrade [NC]
  RewriteRule ^/fireedge/?(.*) "ws://localhost:2616/fireedge/$1" [P,L]

  <Location /fireedge>
      Order deny,allow
      Allow from all
  </Location>
</VirtualHost>
```

{{< alert title="Note" type="info" >}}
As you can see in the configuration the **location** is in `/fireedge`, that means that it is a path of your domain `<YOUR_DOMAIN>/fireedge`. If you want the FireEdge to be in the root you must change it to `/`{{< /alert >}} 

**NGINX**

You will need to configure a new virtual Host in NGINX. Depending on the operating system and the method of installation, NGINX loads virtual Host configurations from either `/etc/nginx/conf.d` or `/etc/nginx/sites-enabled`.

- A sample `cloudserver.org` virtual Host is shown below:

```default
# No squealing.
server_tokens off;

#### OpenNebula FireEdge upstream
upstream fire-edge {
        server 127.0.0.1:2616;
}

#### cloudserver.org HTTPS virtual host
server {
        listen 80;
        server_name cloudserver.org;

        ### Proxy requests to upstream

        location /fireedge {
                proxy_pass http://fire-edge/fireedge;
                proxy_redirect off;
                log_not_found off;
                proxy_buffering off;
                proxy_cache_bypass $http_upgrade;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-FOR $proxy_add_x_forwarded_for;
                access_log off;
        }
}
```

{{< alert title="Note" type="info" >}}
As you can see in the configuration the **location** is in `/fireedge`, that means that it is a path of your domain `<YOUR_DOMAIN>/fireedge`. If you want the FireEdge to be in the root you must change it to `/`{{< /alert >}} 

<a id="fireedge-advance-apache-tls-proxy"></a>

### TLS-secured Configuration

We must create the virtual Host that will run our FireEdge. Here is an example:

**Apache**

```default
<VirtualHost *:443>
  ServerName one.example.com

  SSLEngine on
  SSLCertificateKeyFile /etc/ssl/private/opennebula-key.pem
  SSLCertificateFile /etc/ssl/certs/opennebula-certchain.pem

  SSLProtocol All -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
  SSLHonorCipherOrder On
  SSLCompression off
  Header always set Strict-Transport-Security "max-age=15768000"
  SSLCipherSuite 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256'

  RequestHeader set X-Forwarded-Proto "https"

  ProxyRequests     off
  ProxyPreserveHost on

  # no proxy for /error/ (Apache HTTPd errors messages)
  ProxyPass /error/ !

  ProxyPass /fireedge http://localhost:2616/fireedge
  ProxyPassReverse /fireedge http://localhost:2616/fireedge

  RewriteEngine on
  RewriteCond %{HTTP:Upgrade} websocket [NC]
  RewriteCond %{HTTP:Connection} upgrade [NC]
  RewriteRule ^/fireedge/?(.*) "ws://localhost:2616/fireedge/$1" [P,L]

  <Location /fireedge>
      Order deny,allow
      Allow from all
  </Location>
</VirtualHost>
```

Now the configuration should be ready. Restart  or reload the Apache configuration to start the application and point to the virtual Host to check that everything is running.

{{< alert title="Note" type="info" >}}
As you can see in the configuration inside the **location**, **ProxyPass** and **ProxyPassReverse** is in `/fireedge` that means it is a path of your domain `<YOUR_DOMAIN>/fireedge`. If you want the FireEdge to be in the root you must change it to `/`.{{< /alert >}} 

**NGINX**

You will need to configure a new virtual Host in NGINX. Depending on the operating system and the method of installation, NGINX loads virtual Host configurations from either `/etc/nginx/conf.d` or `/etc/nginx/sites-enabled`.

```default
# No squealing.
server_tokens off;

#### OpenNebula FireEdge upstream
upstream fire-edge {
        server 127.0.0.1:2616;
}

#### cloudserver.org HTTP virtual host
server {
        listen 80;
        server_name cloudserver.org;

        ### Permanent redirect to HTTPS (optional)
        return 301 https://$server_name:8443;
}

#### cloudserver.org HTTPS virtual host
server {
        listen 8443;
        server_name cloudserver.org;

        ### SSL Parameters
        ssl on;
        ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
        ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

        location /fireedge {
                proxy_pass http://fire-edge/fireedge;
                proxy_redirect off;
                log_not_found off;
                proxy_buffering off;
                proxy_cache_bypass $http_upgrade;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-FOR $proxy_add_x_forwarded_for;
                access_log off;
        }
}
```

{{< alert title="Note" type="info" >}}
As you can see in the configuration the **location** is in `/fireedge`, that means that it is a path of your domain `<YOUR_DOMAIN>/fireedge`. If you want the FireEdge to be in the root you must change it to `/`{{< /alert >}} 

<a id="xmlrpc-tls-proxy"></a>

<!--# Securing XML-RPC endpoint with TLS -->

#### Securing XML-RPC endpoint with TLS

By default, OpenNebula XML-RPC works in the port 2633 in plain HTTP protocol. To encrypt end-to-end transport a reverse proxy must be configured. This is recommended because otherwise, authentication information (token or username:password) and all other operations, will be transferred unencrypted and can be eavesdropped.

OpenNebula CLI, API bindings (Ruby, Python, etc.), Terraform provider, etc. support TLS access.

**NGINX**

- A sample `onexmlrpc.org` virtual Host is shown below:

```default
# No squealing.
server_tokens off;

#### OpenNebula FireEdge upstream
upstream one-xml-rpc {
        server 127.0.0.1:2633;
}

#### cloudserver.org HTTPS virtual host
#### OpenNebula encrypted XML-RPC access will run on port 8633
server {
        listen 8663;
        server_name cloudserver.org;

        ### SSL Parameters
        ssl on;
        ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
        ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

        location / {
                proxy_pass http://one-xml-rpc;
                proxy_redirect off;
                log_not_found off;
                proxy_buffering off;
                proxy_cache_bypass $http_upgrade;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $http_host;
                proxy_set_header X-Forwarded-FOR $proxy_add_x_forwarded_for;
                access_log off;
        }
}
```

**Apache**

- A sample `onexmlrpc.conf` virtual Host is shown below. It can be placed on the `sites-available` and symlinked to `sites-enabled`, as any other apache site file.

```default
<IfModule ssl_module>
  Listen 8633
</IfModule>

<IfModule mod_gnutls.c>
  Listen 8633
</IfModule>

<VirtualHost *:8633>
  ServerName cloudserver.org

  SSLEngine on
  SSLCertificateKeyFile /etc/ssl/private/opennebula-key.pem
  SSLCertificateFile /etc/ssl/certs/opennebula-certchain.pem

  SSLProtocol All -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
  SSLHonorCipherOrder On
  SSLCompression off
  SSLCipherSuite 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256'

  ProxyRequests     off
  ProxyPreserveHost on

  ProxyPass        / http://localhost:2633/
  ProxyPassReverse / http://localhost:2633/

  <Location />
      Order deny,allow
      Allow from all
  </Location>
</VirtualHost>
```

{{< alert title="Note" type="info" >}}
To use the CLI with the secure endpoint, the client must set up the variable `ONE_XMLRPC` accordingly, i.e. `ONE_XMLRPC="https://cloudserver.org:8633"`
{{< /alert >}}
