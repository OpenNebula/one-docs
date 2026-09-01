---
title: "Sunstone Authentication"
linkTitle: "Sunstone"
date: "2025-02-17"
description:
categories:
pageintoc: "126"
tags:
weight: "6"
---

<a id="sunstone-auth"></a>

<!--# Sunstone Authentication -->

By default, Sunstone works with the default `core` authentication method (user and password) although you can configure any authentication mechanism supported by OpenNebula. In this section, you will learn how to enable other authentication.

* Authentication is based on the credentials stored in the OpenNebula database for the user. Depending on the type of these credentials the authentication method can be: `remote` or  `opennebula`.

The following sections explain Sunstone server authentication methods to the user.

<a id="suntone-basic-auth"></a>

## Basic Auth

In the basic mode, username and password are matched to those in OpenNebula’s database in order to authorize the user at the time of login. JWT-based sessions are then used to authenticate and authorize the requests.

```yaml
:auth: opennebula
```

<a id="sunstone-remote-auth"></a>

## Remote Auth

This method performs OpenNebula login based on user extraction and compares it with the password value in the user database.

To update existing users to use remote authentication, change the controller to public and update the password as follows:

The user password has to be changed by running one of the following commands:

```default
$ oneuser chauth johndoe public "johndoe"
```

New users with this authentication method should be created as follows:

```default
$ oneuser create johndoe "johndoe" --driver public
```

To enable this login method, set the `:auth:` option in `/etc/one/fireedge-server.conf` to `remote` and restart FireEdge:

```yaml
:auth: remote
```

The login screen will not display the username and password fields anymore, as all information is fetched from the user certificate:

{{< image
  path="/images/sunstone/auth/light/sunstone_login_remote.jpg"
  alt="Sunstone remote login" align="center" width="50%" mb="20px"
>}}

Note that OpenNebula will not verify that the user holds a valid certificate at the time of login: this is expected to be done by the external container of the Sunstone server (normally Apache), whose job is to tell the user’s browser that the site requires a user certificate and to check that the certificate is consistently signed by the chosen Certificate Authority (CA). The setup with Apache/SAML is the more common and tested. However, it can rely on Apache/Nginx for OIDC.

{{< alert title="Warning" type="warning" >}}
The Sunstone authentication only handles the authentication of the user at the time of login. Authentication of the user certificate is a complementary setup, which can rely on Apache.{{< /alert >}} 

<a id="sunstone-ldap-auth"></a>

## LDAP/AD Auth

This method performs the OpenNebula login by delegating the authentication on a specific LDAP/AD server or several servers.

No special configuration is needed in Sunstone, the authentication method should be kept as ‘opennebula’ like in the [Basic Auth case]({{% relref "#suntone-basic-auth" %}}). However, this needs to be set up in the OpenNebula core side. To set up the ldap configuration this [guide]({{% relref "ldap#ldap" %}}) needs to be followed.

## X.509 Auth

This method performs the login to OpenNebula based on an X.509 certificate’s DN (Distinguished Name). The DN is extracted from the certificate and matched to the password value in the user database.

The user password has to be changed by running one of the following commands:

```default
$ oneuser chauth johndoe x509 "/C=ES/O=ONE/OU=DEV/CN=clouduser"
```

or the same command using a certificate file:

```default
$ oneuser chauth johndoe --x509 --cert /tmp/my_cert.pem
```

New users with this authentication method should be created as follows:

```default
$ oneuser create johndoe "/C=ES/O=ONE/OU=DEV/CN=clouduser" --driver x509
```

or by using a certificate file:

```default
$ oneuser create new_user --x509 --cert /tmp/my_cert.pem
```

To enable this login method, set the `:auth:` option in `/etc/one/fireedge-server.conf` to `x509` and restart FireEdge:

```yaml
auth: x509
```

The login screen will not display the username and password fields anymore, as all information is fetched from the user certificate:

{{< image
  path="/images/sunstone/auth/light/sunstone_login_remote.jpg"
  alt="Sunstone remote login" align="center" width="50%" mb="20px"
>}}

{{< alert title="Note" type="info" >}}
To configure this function it's mandatory to have an [Apache/Nginx]({{% relref "../../control_plane_configuration/large-scale_deployment/index#large-scale-deployment" %}})  Below are the rules for each one{{< /alert >}} 

## SAML Auth

This method logs in to OpenNebula based on the Assertion Consumer Service provided by the SAML service. OpenNebula will validate the assertion and create the user if they do not exist.

To enable this login method, set the `:auth:` option in `/etc/one/fireedge-server.conf` to `saml` and restart FireEdge:

```yaml
:auth: saml
```

To enable the link at the bottom of the Fireedge login, you must configure `:auth_redirect: <SAML_LOGIN_ENDPOINT>` and restart Fireedge. Example: if using Keycloak as a SAML service, the URL must have this pattern:

```yaml
:auth_redirect: ‘http://<URL_SAML_SERVICE>/realms/<REALM>/protocol/saml/clients/<CLIENT>’
```

{{< image
  path="/images/sunstone/auth/light/sunstone_login_remote_saml.png"
  alt="Sunstone remote login" align="center" width="50%" mb="20px"
>}}

In case that the redirection is invalid, please check the `Master SAML Processing URL` on your provider (should be similar to `http(s)://<FIREEDGE_SERVER>/fireedge/api/auth/acs`)

### Apache

```yaml
<VirtualHost *:443>
    ...
    SSLVerifyClient require
    SSLVerifyDepth 1

    RequestHeader set X-Client-Dn "%{SSL_CLIENT_S_DN}s"
    <IfModule mod_ssl.c>
        SSLProxyEngine On
    </IfModule>
</VirtualHost>
```

### Nginx

```yaml
location / {
    ...
    proxy_set_header X-Client-Dn $ssl_client_s_dn;
}
```

<a id="sunstone-2f-auth"></a>

## Two Factor Authentication

You can get an additional authentication level by using a two-factor authentication that not only requests the username and password but also the one-time (or pre-generated security) keys generated by an authenticator application.

{{< image
  path="/images/sunstone/auth/light/sunstone_login_2fa.png"
  alt="Sunstone 2FA login" align="center" width="50%" mb="20px"
>}}

### Enforce globally

Setting the `enforce_2fa` option in the `/etc/one/fireedge/sunstone/sunstone-server.conf` configuration file will enforce tfa authentication across all users.

```yaml
enforce_2fa: true
```

Attempting to log in without a TFA authenticator set will present the following screen, prompting the user to add one.


{{< image
  path="/images/sunstone/auth/light/sunstone_tfa_enforce.jpg"
  alt="Sunstone 2FA enforce" align="center" width="70%" mb="20px"
>}}

### Authenticator App

This method requires a token generated by any of these applications: [Google Authentication](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2&hl=en), [Authy](https://authy.com/download/), or [Microsoft Authentication](https://www.microsoft.com/en-us/p/microsoft-authenticator/9nblgggzmcj6?activetab=pivot:overviewtab).

To enable this, you should follow these steps:

- Log in to Sunstone and select menu **Profile Settings** from the dropdown menu at the lower left corner. Find the section named **Two Factor Authentication**.
- In this section, find and select the button **Register Authenticator App**.

{{< image
  path="/images/sunstone/auth/light/register_auth_app.png"
  alt="Sunstone 2FA register app" align="center" width="90%" mb="20px"
>}}

- Scan the Qr code with the aforementioned apps and enter the verification code.

{{< image
  path="/images/sunstone/auth/light/sunstone_2fa_auth_app.jpg"
  alt="Sunstone 2FA register app" align="center" width="70%" mb="20px"
>}}

Internally Sunstone adds the field `TWO_FACTOR_AUTH_SECRET`.

{{< image
  path="/images/sunstone/auth/light/sunstone_2fa_auth_secret.png"
  alt="Sunstone 2FA auth secret" align="center" width="80%" mb="20px"
>}}

- To disable 2FA, go to the **Settings**, find the section **Two Factor Authentication** and click the **Disable 2FA** button.

{{< image
  path="/images/sunstone/auth/light/sunstone_settings_2fa_disable.png"
  alt="Sunstone 2FA disable" align="center" width="80%" mb="20px"
>}}
