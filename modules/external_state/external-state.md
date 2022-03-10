---
title: "external-state"
linkTitle: "external-state"
date: 2021-07-21
draft: false
weight: 1
description: Adds the ability to refer to external, preexisting terraform states in opta.
---

This module grants users the ability to import outputs from 
[external terraform backends](https://www.terraform.io/language/settings/backends) (e.g. pre-existing
or created outside of opta, or another Opta service/environment). All the terraform outputs of that state
will be captured and referenceable under the `outputs` output for this module. 

For instance, you can refer values such as the name of an S3 bucket created in another Opta service like so:
```yaml
environments:
  - name: staging
    path: "./staging.yaml"
    variables:
      max_containers: 5
name: my-service1
modules:
  - type: external-state
    name: external
    backend_type: s3
    config:
      bucket: opta-tf-state-my-org-staging
      key: my-service2
      region: us-east-1
  - name: app
    type: k8s-service
    image: AUTO
    port:
      http: 80
    env_vars:
      blah1: "${{module.external.outputs.s3_bucket_name}}"
```