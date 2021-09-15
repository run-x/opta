---
title: "gcp-service-account"
linkTitle: "gcp-service-account"
date: 2021-07-21
draft: false
weight: 1
description: Creates a GCP service account
---

This module can be used to create and manage a GCP service account via opta, including permissioning and mapping to 
kubernetes service accounts.

### Map to K8s Service Account
You can designate your GCP service account to allow role assumption from a service account in one of your gke clusters.
This is done via the `allowed_k8s_services` field which takes as input a list of entries holding a `namespace` and 
`service_account_name` field, corresponding to a given namespace+service_account to trust.

__Warning__: This trust will be for all clusters in the project, not just the current one of this environment.

For more information, you can read the official GCP docs [here](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)

### Linking

This module can also be linked to other resources, like in the k8s-service. It will then have the desired permissions
for said resources. Currently supported resources:
* GCS Bucket

### Example

```
  - name: deployer
    type: gcp-service-account
    allowed_k8s_services:
      - namespace: "blah"
        service_account_name: "baloney"
```