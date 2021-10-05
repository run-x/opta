---
title: "gcp-nodepool"
linkTitle: "gcp-nodegpool"
date: 2021-07-21
draft: false
weight: 1
description: Creates an additional nodepool for the primary GKE cluster.
---

This module creates an additional nodepool for the primary GKE cluster. Note that the
`gcp-gke` module creates a default nodepool so this should only be used when
you want one more.
