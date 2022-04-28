---
title: "aws-vpn"
linkTitle: "aws-vpn"
date: 2022-04-28
draft: false
weight: 1
description: Creates an AWS VPN endpoint for folks to access your private Opta network
---

This module sets up an [AWS Client VPN Endpoint](https://aws.amazon.com/vpn/client-vpn/) for you. For those new to
this service, AWS Client VPN is AWS' implementation of a VPN which natively integrates to their networking solutions.
It follows the OpenVPN specification and can readily be connected to with the [OpenVPN Client](https://openvpn.net/vpn-client/)
(which we recommend).

As with other VPN solutions, this one is used to gain secure access to a private network, in this case the private VPC
subnets Opta provisioned for your environment. This means that when connected you should have the network access needed
to locally connect to your databases, caches, pretty much all resources in your private network that are accepting 
traffic.

## Adding VPN to your Environment
For most cases, it's actually just adding a single line for the VPN module like so:
```yaml
name: testing-vpn
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXXX
modules:
  - type: base
  - type: aws-vpn
  - type: k8s-cluster
  - type: k8s-base
```
For upcoming work, it's best to place it just after the base module instead of at the end.
Run `opta apply` and you should be good to go!

## Setting Up the Client


## Caveats
