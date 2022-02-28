---
title: "k8s-cluster"
linkTitle: "k8s-cluster"
date: 2021-07-21
draft: false
weight: 1
description: Creates an EKS cluster and a default nodegroup to host your applications in
---

This module creates an [EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html), and a default
nodegroup to host your applications in. This needs to be added in the environment Opta yml if you wish to deploy services
as Opta services run on Kubernetes.

For information about the default IAM permissions given to the node group please see
[here](/reference/aws/modules/aws-nodegroup).