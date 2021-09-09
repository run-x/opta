---
title: "k8s-cluster"
linkTitle: "k8s-cluster"
date: 2021-07-21
draft: false
weight: 1
description: Creates an AKS cluster and a default node pool to host your applications in
---

This module creates an [Kind cluster](https://kind.sigs.k8s.io/docs/user/quick-start/) and a default
node pool to host your applications in. This needs to be added in the environment Opta yml if you wish to deploy services
as Opta services run on Kubernetes locally.
