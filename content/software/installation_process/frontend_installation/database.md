---
title: "Manual Installation - Database Setup"
linkTitle: "Database"
date: "2025-02-17"
description:
categories:
pageintoc: "171"
tags:
weight: "2"
---

<a id="database-setup"></a>

The OpenNebula Front-end uses a database to persist the complete state of the cloud. It supports several database solutions and each option is recommended for different use cases. It’s necessary to decide carefully which solution is the best for your needs, as the migration of an existing installation to a different database type is complex or impossible (depending on the backend). The following options are available:

* Default embedded [SQLite]({{% relref "#sqlite-setup" %}}) for small workloads
* Recommended [MySQL/MariaDB]({{% relref "#mysql-setup" %}}) for production

It’s recommended to install the database backend now. Later, while completing the [Front-end Installation]({{% relref "frontend_install" %}}), return back here and only update the OpenNebula configuration for specific backend based tasks (ideally) *prior* to starting OpenNebula for the first time.

<a id="sqlite-setup"></a>

## SQLite Setup

{{< alert title="Note" type="info" >}}
The information about SQLite is only for information, default installation is preconfigured for SQLite and no actions are required!{{< /alert >}} 

The **SQLite** backend is the default database backend. It's not recommended for production use as it doesn’t perform well under load and on bigger infrastructures. For most cases, it’s recommended to use [MySQL/MariaDB]({{% relref "#mysql-setup" %}}).

### Install

No installation is required.

### Configure OpenNebula

No changes are needed. The default OpenNebula configuration already uses SQLite. The following is the relevant part in the [/etc/one/oned.conf]({{% relref "oned#oned-conf" %}}) configuration file:

```default
DB = [ BACKEND = "sqlite",
       TIMEOUT = 2500 ]
```

<a id="database-mysql"></a>

<a id="mysql"></a>

<a id="mysql-setup"></a>

## MySQL/MariaDB Setup

The **MySQL/MariaDB** backend is an alternative to the default SQLite backend. It’s recommended for heavy or production workloads and is fully featured for the best performance. In this guide and in the rest of the documentation and configuration files we refer to this database as MySQL. However, OpenNebula can use either MySQL or MariaDB.

<a id="mysql-installation"></a>

### Install

First of all, you need a working MySQL or MariaDB server. You can either deploy one for the OpenNebula installation following the guides for your operating system or reuse an existing one accessible via the Front-end. We assume you have a working MySQL/MariaDB server installed.

{{< alert title="Note" type="info" >}}
MySQL should be recent enough to support the FULLTEXT indexing used by OpenNebula to implement the VM search feature. For MariaDB, that means at least a late minor version of release 10.0 if you use the default InnoDB.{{< /alert >}} 

### Configure

You need to add a new database user and grant the user privileges on the `opennebula` database. This database doesn’t need to exist already, as OpenNebula will create it the first time it runs. Assuming you are going to use the default values, log in to your MySQL server and issue the following commands while replacing `<thepassword>` with your own secure password:

```shell
mysql -u root -p
```
```default
Enter password:
Welcome to the MySQL monitor. [...]

mysql> CREATE USER 'oneadmin' IDENTIFIED BY '<thepassword>';
Query OK, 0 rows affected (0.00 sec)
mysql> GRANT ALL PRIVILEGES ON opennebula.* TO 'oneadmin';
Query OK, 0 rows affected (0.00 sec)
```

Visit the [MySQL documentation](https://dev.mysql.com/doc/refman/8.4/en/access-control.html) to learn how to manage accounts.

Now, configure the transaction isolation level:

```shell
mysql> SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

### Configure OpenNebula

Before you run OpenNebula for the first time in the next section [Front-end Installation]({{% relref "frontend_installation.md" %}}), you’ll need to set the database backend and connection details in the configuration file [/etc/one/oned.conf]({{% relref "oned#oned-conf" %}}) as follows:

```default
# Sample configuration for MySQL
DB = [ BACKEND = "mysql",
       SERVER  = "localhost",
       PORT    = 0,
       USER    = "oneadmin",
       PASSWD  = "<thepassword>",
       DB_NAME = "opennebula",
       CONNECTIONS = 25,
       COMPARE_BINARY = "no" ]
```

Fields:

- `SERVER` - IP/hostname of the machine running the MySQL server
- `PORT` - port for the connection to the server (default port is used when `0`)
- `USER` - MySQL user-name
- `PASSWD` - MySQL password
- `DB_NAME` - name of the MySQL database OpenNebula will use
- `CONNECTIONS` - max. number of connections
- `COMPARE_BINARY` - compare strings using BINARY clause to make name searches case sensitive

## Next Steps

After installing and configuring the database for your OpenNebula cloud, you can proceed to install the Front-end manually. Prior to installing the Front-end manually, you must first configure the OpenNebula package repositories for your Linux distribution. Please proceed to the repository setup documentation for your OpenNebula edition:

* [Set Up the OpenNebula Repositories for the Community Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ce/" %}})
* [Set Up the OpenNebula Repositories for the Enterprise Edition]({{% relref "software/installation_process/frontend_installation/opennebula_repository_configuration_ee/" %}})
