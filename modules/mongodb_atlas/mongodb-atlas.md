---
title: "mongodb-atlas"
linkTitle: "mongodb-atlas"
date: 2021-10-12
draft: false
weight: 1
description: Creates a Mongodb Atlas database instance
---

This module creates a MondoDB Atlas cluster. Currently only supports AWS and Local providers in Opta.

### Backups
TBD

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_mongodb_connection_string

The permission list can optionally have one entry which should be a map for renaming the default environment variable
names to a user-defined value:

```yaml
links:
  - db:
      - db_user: DBUSER
        db_password: DBPASS
        db_mongodb_connection_string: DBCONNSTRING
```

If present, this map must have renames for all 3 fields.
