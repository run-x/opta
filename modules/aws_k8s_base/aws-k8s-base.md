---
title: "k8s-base"
linkTitle: "k8s-base"
date: 2021-07-21
draft: false
weight: 1
description: Creates base infrastructure for k8s environments
---

### Features

This module is responsible for all the base infrastructure we package into the Opta K8s environments. This includes:

- [Autoscaler](https://github.com/kubernetes/autoscaler) for scaling up and down the ec2s as needed
- [Ingress Nginx](https://github.com/kubernetes/ingress-nginx) to expose services to the public
- [Metrics server](https://github.com/kubernetes-sigs/metrics-server) for scaling different deployments based on cpu/memory usage
- [Linkerd](https://linkerd.io/) as our service mesh.
- [Cert Manager](https://cert-manager.io/docs/) for internal ssl.
