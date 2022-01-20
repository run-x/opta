---
title: "mysql"
linkTitle: "mysql"
date: 2021-07-21
draft: false
weight: 1
description: Creates a MySQL database instance
---

This module creates a MySQL [GCP Cloud SQL](https://cloud.google.com/sql/docs/introduction) database. It is made with
the [private service access](https://cloud.google.com/vpc/docs/private-services-access), ensuring private communication.

### Backups
Opta will provision your database with 7 days of automatic daily backups in the form of
[Cloud SQL Backups](https://cloud.google.com/sql/docs/postgres/backup-recovery/backups).
You can find them either programmatically via the gcloud cli, or through the GCP web console inside your db description
page.

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_db_name`
- `{module_name}_db_host`

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

These values are passed securely into your environment by using a kubernetes secret created by opta within your
k8s-service's isolated k8s namespace.  These secrets are then passed as environment variables directly into your container.
Take note that since opta's AWS/EKS clusters always have the disk encryption enabled, your secret never touches an
unencrypted disk. Furthermore, because of k8's RBAC, no other opta-managed k8s service can access this instance of the
creds as a k8s secret without manual override of the RBAC, nor can any other entities/users unless given "read secret"
permission on this namespace.

To those with the permissions, you can view it via the following command (MANIFEST_NAME is the `name` field in your yaml):

`kubectl get secrets -n MANIFEST_NAME secret -o yaml`
