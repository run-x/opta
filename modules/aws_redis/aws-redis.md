---
title: "redis"
linkTitle: "redis"
date: 2021-07-21
draft: false
weight: 1
description: Creates a redis cache via elasticache
---

This module creates a redis cache via elasticache. It is made with one failover instance across AZs, and is encrypted
at rest with a kms key created in the env setup via the _init_ macro and in transit via tls. It is made in the private
subnets created by the \_init macro and so can only be accessed in the VPC or through some proxy (e.g. VPN).

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables

- `{module_name}_cache_auth_token` -- The auth token/password of the cluster.
- `{module_name}_cache_host` -- The host to contact to access the cluster.

In the [modules reference](/reference), the _{module_name}_ would be replaced with `cache`.

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - cache_host: CACHEHOST
        cache_auth_token: CACHEAUTH
```

If present, this map must have renames for all 2 fields.

### Limitations

Redis CLI will not work against this cluster because redis cli does not
support the TLS transit encryption. There should be no trouble with any of the
language sdks however, as they all support TLS.

These values are passed securely into your environment by using a kubernetes secret created by opta within your
k8s-service's isolated k8s namespace.  These secrets are then passed as environment variables directly into your container.
Take note that since opta's AWS/EKS clusters always have the disk encryption enabled, your secret never touches an
unencrypted disk. Furthermore, because of k8's RBAC, no other opta-managed k8s service can access this instance of the
creds as a k8s secret without manual override of the RBAC, nor can any other entities/users unless given "read secret"
permission on this namespace.

To those with the permissions, you can view it via the following command (MANIFEST_NAME is the `name` field in your yaml):

`kubectl get secrets -n MANIFEST_NAME secret -o yaml`
