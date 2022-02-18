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

## Taints

Opta gives you the option of adding [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
to the nodes created in this nodepool. The official documentation gives an excellent detailed summary, but in short
one can use taints to stop workloads from running in said nodes unless they have a matching toleration. Simply provide 
a list of such taints as inputs like so:
```yaml
  - type: gcp-nodepool
    name: nodepool1
    min_nodes: 1
    max_nodes: 3
    taints:
      - key: instancetype
        value: memoryoptimized
        effect: "NoExecute"
      - key: team
        value: booking
        # Tolerates for default effect of NoSchedule
      - key: highpriority
        # Tolerates for default value of opta
```

For most cases, simply specifying the `key` should do.

{{% alert title="Warning" color="warning" %}}
Adding taints to nodes also forbids most [daemonsets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
from running in said node. This can be a problem with security/monitoring solutions (e.g. Datadog) which typiclly use
daemonsets to run their agents in each node, so please be careful and read their instructions on how to add
[tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
{{% /alert %}}
