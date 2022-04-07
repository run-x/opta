---
title: "global-accelerator"
linkTitle: "global-accelerator"
date: 2021-07-21
draft: false
weight: 1
description: Add an AWS Global Accelerator to your env.
---

This module sets up an [AWS Global Accelerator](https://aws.amazon.com/global-accelerator/) for you. For those new to 
this service, a Global Accelerator can be used as an alternative (or helper to) multi region deployments, "fast 
forwarding" requests across AWS' underlying networks to drastically decrease long-distance network request latencies.
The Global Accelerator is meant to be deployed in front of a load balancer, and exposes a domain and public ip addresses
to which send public traffic. In Opta

```yaml
name: testing-global-accelerator
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXXX
modules:
  - type: base
     # Uncomment to create a DNS with the given domain and all traffic flowing to the cloudfront distribution
#  - type: dns 
#    name: dns
#    domain: staging.startup.com
#    delegated: false # Set to true when ready -- see the "Configure DNS" page
  - type: k8s-cluster
  - type: k8s-base
    name: testbase
    enable_auto_dns: false  # Need this to drive dns traffic to cloudfront
    # Uncomment when enabling dns to get ssl
#    cert_arn: "${{module.dns.cert_arn}}" # Or add your own cert if not using Opta's dns module
  - type: global-accelerator
```

### Domain / DNS
If you are ready to start hosting your site with your domain via the global accelerator, then go ahead and uncomment
the dns modules in the example above, and follow the [configuring dns guide](/features/dns-and-cert/dns). Traffic should
start flowing from your domain to your global acceleratorn and on towards your K8s cluster. You could
also manually configure DNS / SSL from outside of Opta using the following steps:
1. Get an [AWS ACM certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html) for your site.
   Make sure that you get it in region us-east-1. If you already have one at hand in your account (e.g. from another
   active Opta deployment), then feel free to reuse that.
2. [Validate](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html) the certificate by adding the correct CNAME entries in your domain's DNS settings.
3. Create a new separate CNAME record for the domain you wish to use for your app and point it to the value of the `load_balancer_raw_dns` Opta output.
4. Fill in the `cert_arn` field in the k8s-base module.
5Opta apply and you're done!