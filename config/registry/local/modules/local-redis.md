---
title: "redis"
linkTitle: "redis"
date: 2021-07-21
draft: false
weight: 1
description: Creates a redis cache locally
---

This module creates a redis cache inside the local Kind Kubernetes cluster. 
### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables

- `{module_name}_cache_host` -- The host to contact to access the cluster.

In the [modules reference](/modules-reference), the _{module_name}_ would be replaced with `cache`

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - cache_host: CACHEHOST
```
