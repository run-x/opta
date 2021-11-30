---
title: "local-mongodb"
linkTitle: "local-mongodb"
date: 2021-09-27
draft: false
weight: 1
description: Creates a Mongodb cluster for Local
---

This module creates a Local Mongodb cluster.
### Linking

When linked to a k8s-service, this adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_db_host`

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - db_user: DBUSER
        db_host: DBHOST
        db_password: DBPASS
```

If present, this map must have renames for all 3 fields.

