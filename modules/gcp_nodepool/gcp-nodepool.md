---
title: "gcp-nodepool"
linkTitle: "gcp-nodegpool"
date: 2021-07-21
draft: false
weight: 1
description: Creates an additional nodepool for the primary GKE cluster.
---

This module creates an additional nodepool for the primary GKE cluster. Note that the
`gcp-gke` module creates a default nodepool so this should only be used when
you want one more.

## IAM Permissions given to the Nodepool
Along with the nodepool, Opta creates a [GCP IAM service account](https://cloud.google.com/iam/docs/service-accounts)
that is attached to each VM in the pool and handles all of the machine's (and Kubernetes actions done by the kubelet
in the machine like, for example, downloading a gcr image) IAM permissions. Opta gives this service account the
following roles:
* logging.logWriter
* monitoring.metricWriter
* monitoring.viewer
* stackdriver.resourceMetadata.writer
* storage.objectViewer on the project's gcr bucket

The first 4 roles are the default roles/permissions [required by GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster#permissions)
while the last ensures that each VM can pull docker images stored in your project's gcr bucket. If you need more 
permissions, feel free to add them via the `gcloud` cli or gcp web ui console-- assuming you do not destroy/modify the
existing roles attached there should be no problem.

THIS SERVICE ACCOUNT IS NOT THE ONE USED BY YOUR CONTAINERS RUNNING IN THE CLUSTER-- Opta handles creating appropriate
service accounts for each K8s service, but for any non-opta managed workloads in the cluster, please refer to this
[GCP documentation](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity).