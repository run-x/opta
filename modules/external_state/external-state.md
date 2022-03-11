---
title: "external-state"
linkTitle: "external-state"
date: 2021-07-21
draft: false
weight: 1
description: Adds the ability to refer to external, preexisting terraform states in Opta.
---

This module grants users the ability to import outputs from 
[external terraform backends](https://www.terraform.io/language/settings/backends) (e.g. pre-existing
or created outside of Opta, or another Opta service/environment). All the terraform outputs of that state
will be captured and referenceable under the `outputs` output for this module (Opta will error out if 
the desired value is not found in the outputs). 

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
      SOURCE_QUEUE: "${{module.external.outputs.sqs_queue_name}}"
```

The service will now have an environment variables known as SOURCE_BUCKET SOURCE_QUEUE could be the name of the
queue they wish grab data from (assuming IAM permissions are configured externally for simplicity).

{{% alert title="NOTE" color="orange" %}}
Usage is reliant on what the external state outputs and names. Please make sure that the data you seek
is both outputted and has the expected name. If the state is created by Opta you can find the outputs
and name by running opta apply on that state's manifest yaml.
{{% /alert %}}

## How to Properly Configure
This module takes just 2 inputs, `backend_type` and `config`, which directly map to an available terraform
backend name and its configuration. For full details please see [here](https://www.terraform.io/language/settings/backends),
but for convenience we have below some common examples:

For S3 (Opta AWS)
```yaml
  - type: external-state
    name: external
    backend_type: s3
    config:
      bucket: my-bucket-name
      key: my-key
      region: us-east-1
```

For GCS (Opta GCP)
```yaml
  - type: external-state
    name: external
    backend_type: gcs
    config:
      bucket: my-bucket-name
      prefix: my-prefix
```

For Azurerm (Opta Azure)
```yaml
  - type: external-state
    name: external
    backend_type: azurerm
    config:
      storage_account_name: my-storage-account
      container_name: my-container
      key: my-key
```