---
title: "dns"
linkTitle: "dns"
date: 2021-07-21
draft: false
weight: 1
description: Adds dns to your environment
---

This module creates a GCP [managed zone](https://cloud.google.com/dns/docs/zones) for
your given domain. The [k8s-base](/reference/google/modules/gcp-k8s-base) module automatically hooks up the load balancer to it
for the domain and subdomain specified, but in order for this to actually receive traffic you will need to complete
the [dns setup](/features/dns-and-cert/dns/).

## Changing dns domains
Currently, Opta does not support multiple domains (except subdomains) per environment, although that may change
based on user demand. In order for a user to change the domain tied to their environment, they would need to
remove their current dns module, and then add a new one after applying.

Take for example, if we had the current running environment:

```yaml
name: staging
org_name: mycompany
providers:
  google:
    region: us-central1
    project: XXX
modules:
  - type: base
  - type: dns
    domain: mycompany.dev
  - type: k8s-cluster
  - type: k8s-base
```

Supposed we wished to change the domain to "otherdomain.dev". First we would remove the dns module:

```yaml
name: staging
org_name: mycompany
providers:
  google:
    region: us-central1
    project: XXX
modules:
  - type: base
  - type: k8s-cluster
  - type: k8s-base
```

Next we would `opta apply` the new yaml and see that the dns resources have been destroyed.
**Note that your site will be temporarily offline after this step and before the next steps are completed.**
Afterwards we would add the new dns module entry with the new domain like so:

```yaml
name: staging
org_name: mycompany
providers:
  google:
    region: us-central1
    project: XXX
modules:
  - type: base
  - type: dns
    domain: otherdomain.dev
  - type: k8s-cluster
  - type: k8s-base
```

We would opta apply like before and we would now have the new domain. Depending on your set up there may be some
additional steps required:

### What if I had the domain delegated already?
That's fine, the removal of the old domain can proceed with no changes but at the end you would need to do the delegation
steps for the new domain.

### What if I had deployed some services whose public_uri was based off {parent.domain}?
You would need to do a new apply for each of those services as they would not have gotten the memo of the new domain.
You can use the same image, and opta yaml for the service as before-- zero change necessary, all we need is the
new apply.
