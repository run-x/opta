---
title: "k8s-cluster"
linkTitle: "k8s-cluster"
date: 2021-07-21
draft: false
weight: 1
description: Creates a GKE cluster and a default nodegroup to host your applications in
---

This module creates a [GKE cluster](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview), and a default
node pool to host your applications in. This needs to be added in the environment Opta yml if you wish to deploy services
as Opta services run on Kubernetes.

For information about the default IAM permissions given to the node pool please see 
[here](/reference/google/modules/gcp-nodepool).