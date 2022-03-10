---
title: "GKE Upgrade"
linkTitle: "GKE Upgrade"
date: 2022-01-03
draft: false
weight: 2
description: >
  How to upgrade the version of your GKE cluster created by opta.
---

# Upgrading Google Kubernetes Engine Version

The Kubernetes Project releases minor version updates every quarter, and users are expected to update their infrastructure to at least within a few minor versions of the latest Kubernetes release. With Google GKE, Opta relies on GCP's [release channels](https://cloud.google.com/kubernetes-engine/docs/concepts/release-channels) to automatically upgrade the Kubernetes control plane and worker nodes. When Opta installs your GKE cluster, it uses the "regular" GKE channel. Currently (Feb 1, 2022), this channel will install a Kubernetes 1.21.x cluster. You can run the `kubectl version` command and look for the "Server Version" key to know what version your cluster is currently running.

In the next days the GKE regular channel will start updating Kubernetes to 1.22.x; which will mean that your opta-deployed Kubernetes cluster will be automatically upgraded to a 1.22.x version. This version of Kubernetes removes several deprecated Kubernetes APIs (read the GKE deprecation guide [here](https://cloud.google.com/kubernetes-engine/docs/deprecations/apis-1-22)).


Before the upgrade to Kubernetes v1.22.x, you should verify that the Kubernetes API used in Kubernetes v1.22.x version still supports your helm charts and kubernetes manifests. Please refer to [this]( https://kubernetes.io/docs/reference/using-api/deprecation-guide/) Kubernetes API deprecation guide to change your code accordingly; we recommend paying particular attention to the [Ingress changes](https://kubernetes.io/docs/reference/using-api/deprecation-guide/#ingress-v122): `extensions/v1beta1` and `networking.k8s.io/v1beta1` APIs that are removed in Kubernetes v1.22.x; replace these with the corresponding `networking.k8s.io/v1` API objects. You can also use code-scanners such as [Pluto](https://github.com/FairwindsOps/pluto) to help with this process.

Next, you should go ahead and upgrade Opta and your Kubernetes clusters:

1. Update your opta version to v0.25.0 or newer and run `opta apply` on your gcp environment(s). This may cause your ingress resources to be unavailable for about a minute, so we recommend you do this change in a pre-determined change window.
   
2. Run `opta apply` or `opta deploy` on any service opta files you use to deploy Kubernetes deployments (services) or helm charts. Confirm everything works as expected. 

To validate these changes in your dev/staging environment you can upgrade to 1.22 sooner by proceeding to the [gke UI](https://console.cloud.google.com/kubernetes) and click on upgrade cluster master version (See screenshot below); you can choose a 1.22.x version if that is available in the regular channel when you are reading this for example (see screenshot). Opta sets up auto-upgrading nodepools in GKE, so once the cluster upgrade is complete your Kubernetes worker nodes should automatically upgrade (on a rolling basis and without downtime) after a few hours. Watch for any errors and as always, feel free to reach out to us on our [slack](https://slack.opta.dev/).

<p>
<a href="/images/upgrade-gke-1.png" target="_blank">
  <img src="/images/upgrade-gke-1.png" align="center"/>
</p>
