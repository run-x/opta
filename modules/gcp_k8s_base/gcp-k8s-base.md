---
title: "k8s-base"
linkTitle: "k8s-base"
date: 2021-07-21
draft: false
weight: 1
description: Creates base infrastructure for k8s environments
---

This module is responsible for all the base infrastructure we package into the Opta K8s environments. This includes:

- [Ingress Nginx](https://github.com/kubernetes/ingress-nginx) to expose services to the public
- [Linkerd](https://linkerd.io/) as our service mesh.
- [Cert Manager](https://cert-manager.io/docs/) for internal ssl
- A custom load balancer and dns routing built to handle the Ingress Nginx which we set up.
