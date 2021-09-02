---
title: "dns"
linkTitle: "dns"
date: 2021-07-21
draft: false
weight: 1
description: Adds dns to your environment
---

This module creates a GCP [managed zone](https://cloud.google.com/dns/docs/zones) for
your given domain. The [k8s-base]({{< relref "#k8s-base" >}}) module automatically hooks up the load balancer to it
for the domain and subdomain specified, but in order for this to actually receive traffic you will need to complete
the [dns setup](/miscellaneous/ingress).