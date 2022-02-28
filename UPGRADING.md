# Upgrading

## Upgrading Opta version

A new Opta version is released every 2 weeks which includes new modules, bug fixes, security improvments and other usability improvements. Sometimes a release might also upgrade older resources with newer ones like better ingress etc. Hence it is recommended to frequently upgrade your infrastructure with latest Opta releases.

In some rare cases, upgrading an Opta version can cause a few minutes of downtime. This would usually be highlighted in the [release notes](https://github.com/run-x/opta/releases). So definitely checkout the release notes before doing upgrades. Whenever in doubt please feel free to reach out to the contributors in our [Slack](https://slack.opta.dev/).

## Upgrading Kubernetes version

### AWS
Checkout our AWS EKS version upgrade guide [here](https://docs.opta.dev/reference/aws/eks_upgrade/)

### GCP
Checkout our GCP GKE version upgrade guide [here](https://docs.opta.dev/reference/google/gke_upgrade/)

## Upgrading database version

For all the database modules, Opta exposes a `version` field which can be used to upgrade the version of the database. But before attempting the upgrade, please make sure to check your cloud provider's guide for that database version upgrade. It will highlight if there will be downtime or any data loss. We are also happy to help answer any questions in our [Slack](https://slack.opta.dev/).
