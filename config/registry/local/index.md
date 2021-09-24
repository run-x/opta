---
title: "local"
linkTitle: "local"
date: 2021-09-10
draft: false
weight: 1
description: Local provider
---

# Opta Local Provider

Use this provider to spin up a local Kubernetes cluster using [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/). This spins up a docker container that runs Kubernetes on the local host. A docker container running docker container registry is also created.

This provider assumes all the [opta requirements](https://docs.opta.dev/installation/) are installed on local host.

## Limitations of the Local Provider

  1. No support for DNS; the locally installed services are accessed via an Nginx ingress at http://localhost:8080/
  2. Limited to single local host, no high-availability
