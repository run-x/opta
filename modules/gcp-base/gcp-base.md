---
title: "base"
linkTitle: "base"
date: 2021-07-21
draft: false
weight: 1
description: Sets up VPC, private subnet, firewall, default kms key, and private service access. Also activates the container registry
---

This module is the "base" module for creating an environment in gcp. It sets up the VPC, private subnet, firewall,
default kms key, private service access, and activate the container registry. Defaults are set to work 99% of the time, assuming no funny
networking constraints (you'll know them if you have them), so _no need to set any of the fields or know what the outputs do_.
