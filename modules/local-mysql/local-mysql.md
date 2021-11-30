---
title: "mysql"
linkTitle: "mysql"
date: 2021-09-27
draft: false
weight: 1
description: Creates a mysql database as a paas in the local kubernetes cluster
---

This module creates a mysql database instance within the local Kubernetes Kind cluster. 

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_db_name`
- `{module_name}_db_host`

In the [modules reference](/modules-reference) example, the _{module_name}_ would be replaced with `rds`

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - db_user: DBUSER
        db_host: DBHOST
        db_name: DBNAME
        db_password: DBPASS
```

If present, this map must have names for all 4 fields.
