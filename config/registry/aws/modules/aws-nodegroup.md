---
title: "aws-nodegroup"
linkTitle: "aws-nodegroup"
date: 2021-07-21
draft: false
weight: 1
description: Creates an additional nodegroup for the primary EKS cluster.
---

This module creates an additional nodegroup for the primary EKS cluster. Note that the
`aws-eks` module creates a default nodegroup so this should only be used when
you want one more.
