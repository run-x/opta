---
title: "base"
linkTitle: "base"
date: 2021-07-21
draft: false
weight: 1
description: Sets up VPCs, a default KMS key, and the db/cache subnets for your environment
---

The defaults for this module are set to work 99% of the time, assuming no funny networking constraints (you'll know them
if you have them), so in most cases, there is _no need to set any of the fields or know what the outputs do_.

## Bring your own VPC
To use an existing VPC with Opta, instead of having Opta create a new VPC, you must set the `vpc_id`, `public_subnet_ids`, and `private_subnet_ids` fields.
Set `vpc_id` to the ID of the existing VPC you would like Opta to use.
Set `public_subnet_ids` to the list of IDs of the public subnets in the VPC.
Public subnets must have a route that connects to an internet gateway, and must be configured to assign public IP addresses.
Set `private_subnet_ids` to the list of IDs of the private subnets in the VPC.
Private subnets must have a route with a destination of `0.0.0.0/0` that points to a NAT gateway with a public IP address.
If the private subnet routes are not configured correctly, you may see an error output by Terraform that looks like "No routes matching supplied arguments found in Route Table".

IPv6 is not supported on VPCs that you bring.
Those VPCs may work, but we do not verify Opta works properly with IPv6-only or dual-stack VPCs.
