---
title: "postgres"
linkTitle: "postgres"
date: 2021-07-21
draft: false
description: Creates a postgres database
---

This module creates a postgres [Azure Database for PostgreSQL](https://azure.microsoft.com/en-us/services/postgresql/) database. It is made with
the [private link](https://docs.microsoft.com/en-us/azure/postgresql/concepts-data-access-and-security-private-link), ensuring private communication.

### Backups
Opta will provision your database with 7 days of [continuous backups](https://docs.microsoft.com/en-us/azure/postgresql/concepts-backup).

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_db_name`
- `{module_name}_db_host`

In the [modules reference](/reference) example, the _{module_name}_ would be replaced with `rds`

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

If present, this map must have renames for all 4 fields.
