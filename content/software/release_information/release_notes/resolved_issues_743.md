---
title: "Resolved Issues in 7.4.3 (EE)"
date: "2026-11-13"
weight: 743
---

<!-- Update verision numbers X.Y.Z, date and milestone number -->

A complete list of solved issues for 7.4.3 are listed in the [project development portal](https://github.com/OpenNebula/one/milestone/97).

## Backported Features

The following new features have been backported to 7.4.3:

<!-- item structure
Include a high level description and a link to the documentation explaining the new feature. Example:

* Add per-VM live migration options through [`MIGRATE_AUTO_CONVERGE` and `MIGRATE_COMPRESSED`]({{% relref "/product/operation_references/configuration_references/template#template-features" %}}) VM template attributes. Administrators can now tune auto-convergence and memory compression only for selected KVM VMs, improving migration reliability and bandwidth usage without changing global driver defaults.
-->

## Resolved Issues

The following issues have been solved in 7.4.3:

* Fix limited visibility of CPU models for non-admin users during VM template creation [#7723](https://github.com/OpenNebula/one/issues/7723).
* Fix disable option for estricted attributes [#8248](https://github.com/OpenNebula/one/issues/8248).
* Fix pagination in VM list mode [#8046](https://github.com/OpenNebula/one/issues/8046).
* Fix Group admin user cannot edit his own group in Sunstone [#8162](https://github.com/OpenNebula/one/issues/8162).
* Fix LDAP authentication and `oneuser login` failures when usernames contain uppercase and special letters [#7377](https://github.com/OpenNebula/one/issues/7377).
* Fix Veeam upload transfers being reported as `transferring` before the OneBEX writer is ready [#8274](https://github.com/OpenNebula/one/issues/8274).
* Fix YAML parsing failures in OneBEX, OneKS, and OneForm with Psych 3.0.2 on SLES 15 SP7 [#8291](https://github.com/OpenNebula/one/issues/8291).
* Fix slow LogDB purges that block Raft replication in high-availability deployments [#8260](https://github.com/OpenNebula/one/issues/8260).
* Fix incremental backups failing when a VM has an unselected RAW disk [#8281](https://github.com/OpenNebula/one/issues/8281).
* Fix Ceph datastore monitoring reporting the metadata pool capacity instead of the erasure-coded data pool capacity [#8234](https://github.com/OpenNebula/one/issues/8234).
* Fix default guad configuration allows overwriting files [#4582](https://github.com/OpenNebula/one-ee/issues/4582).