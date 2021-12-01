---
title: "redis"
linkTitle: "redis"
date: 2021-07-21
draft: false
weight: 1
description: Creates a redis cache via Memorystore
---

This module creates a redis cache via [Memorystore](https://cloud.google.com/memorystore/docs/redis/redis-overview).
It is made with their standard high availability offering, but (unlike in AWS) there is no
[encryption at rest](https://stackoverflow.com/questions/58032778/gcp-cloud-memorystore-data-encryption-at-rest)
and in-transit encryption is not offered as terraform support is in beta. It is made in the with private service access
ensuring private communication.

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables

- `{module_name}_cache_auth_token` -- The auth token/password of the cluster.
- `{module_name}_cache_host` -- The host to contact to access the cluster.

In the [modules reference](/reference), the _{module_name}_ would be replaced with `cache`

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - cache_host: CACHEHOST
        cache_auth_token: CACHEPASS
```

If present, this map must have renames for all 2 fields.
