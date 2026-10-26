---
title: "CernVM-FS Proxy"
linkTitle: "CernVM-FS Proxy"
date: "2026-09-24"
description: ""
categories:
pageintoc: "15"
tags:
type: docs
weight: "2"
---

[CernVM-FS](https://cernvm.cern.ch/fs/), the CernVM File System, is a read-only file system developed at CERN to distribute software to many machines. Each machine mounts it under `/cvmfs` and downloads a file over HTTP only when a program reads it. The [EESSI](https://www.eessi.io/) scientific software catalogue reaches every machine this way.