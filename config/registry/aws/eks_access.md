---
title: "EKS Access"
linkTitle: "EKS Access"
date: 2022-01-03
draft: false
weight: 1
description: How to access your Opta EKS Cluster 
---

## EKS Access
As each Kubernetes cluster maintains its own cloud-agnostic rbac system to govern its own usage, extra steps
must be taken on each cloud provider to reconcile the given cloud's IAM with the cluster's. For EKS, this is done
via the `aws-auth` [configmap](https://kubernetes.io/docs/concepts/configuration/configmap/) stored in the `kube-system`
namespace (see [here](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html) for the official documentation).
This configmap is essentially a mapping stating "AWS IAM user/role X is in group/has permissions A, B, C" in this cluster.
An admin can view this configmap via this command `kubectl get cm -n kube-system aws-auth -o yaml` and these configmaps
typically look like so:
```yaml
apiVersion: v1
data: # NOTE there are separate sections for AWS IAM Users and AWS IAM roles.
  mapRoles: |
    - groups: ['system:bootstrappers', 'system:nodes']
      rolearn: arn:aws:iam::ACCOUNT_ID:role/opta-live-example-dev-eks-default-node-group
      username: system:node:{{EC2PrivateDNSName}}
    - groups: ['system:bootstrappers', 'system:nodes']
      rolearn: arn:aws:iam::ACCOUNT_ID:role/opta-live-example-dev-eks-nodegroup1-node-group
      username: system:node:{{EC2PrivateDNSName}}
    - groups: ['system:masters']
      rolearn: arn:aws:iam::ACCOUNT_ID:role/live-example-dev-live-example-dev-deployerrole
      username: opta-managed
  mapUsers: |
    - groups: ['system:masters']
      userarn: arn:aws:iam::ACCOUNT_ID:user/live-example-dev-live-example-dev-deployeruser
      username: opta-managed
```

> Note: the IAM user/role who created the cluster is always considered root/admin and does not appear

As you can see, each entry has the following fields:
* rolearn/userarn: the arn of the AWS IAM user/role to link.
* username: the human-friendly distinct name/alias to recognize the rbac request from.
* groups: the list of Kubernetes rbac groups to give the role/user access to.

Please refer to the [official docs](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) for full details, but
note that if you want admin privileges, you simply need the `system:masters` group. For convenience, Opta has exposed a
field in the `k8s-base` module for AWS known as `admin_arns`, which is where users can quickly add IAM users/roles to
add as admins without dealing with Kubernetes directly.

```yaml
name: staging
org_name: my-org
providers:
  aws:
    region: us-east-1
    account_id: XXXX # Your 12 digit AWS account id
modules:
  - type: base
  - type: dns
    domain: staging.startup.com
    subdomains:
      - hello
  - type: k8s-cluster
  - type: k8s-base
    admin_arns:
      - "arn:aws:iam::XXXX:user/my-user"
      - "arn:aws:iam::XXXX:role/my-role"
```

## K8s RBAC Groups
Admittedly, Kubernetes rbac groups are
[currently difficult to view](https://stackoverflow.com/questions/51612976/how-to-view-members-of-subject-with-group-kind),
but you should be able to see details the current ones with the following command (you will need `jq` installed):
`kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.subjects[0].kind=="Group")` and
`kubectl get rolebindings -A -o json | jq -r '.items[] | select(.subjects[0].kind=="Group")` (none for this by default).

Essentially an rbac group is created by creating a ClusterRoleBinding (or RoleBinding for namespace-limited permissions)
between the CluterRole/Role whose permissions you want to give and a new or pre-existing Group to give it to. Take the
following yaml for instace:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: my-cluster-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:discovery
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: my-group
```

For this case, this ClusterRoleBinding says "give all member of the Group named my-group all the permissions of the
ClusterRole named system:discovery on all namespaces" (you can bind to ServiceAccounts as well, please see the docs for
more details).

## Conclusion
So, to summarize:

* If you wish to add an IAM role/user to be an admin in the K8s cluster, go ahead and use the `admin_arns` field for the
  AWS `k8s-base` module
* If you wish to add an IAM role/user to a different set of K8s permissions already found in a pre-existing group, go
  ahead and manually add them in the `aws-auth` configmap on the `kube-system` namespace
* If you wish to create a new K8s group to capture a new set of permissions, go ahead and do so with role binding/cluster role bindings.
