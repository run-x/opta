---
title: "mysql"
linkTitle: "mysql"
date: 2021-07-21
draft: false
weight: 1
description: Creates a MySQL Aurora RDS database instance
---

This module creates a MySQL Aurora RDS database instance. It is made in the
private subnets automatically created during environment setup and so can only be accessed in the
VPC or through some proxy (e.g. VPN).

### Backups
Opta will provision your database with 7 days of automatic daily backups in the form of 
[RDS snapshots](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_CreateSnapshot.html). 
You can find them either programmatically via the aws cli, or through the AWS web console (they will be called
system snapshots, and they have a different tab than the manual ones).

### Performance and Scaling

You can modify the DB instance class with the field `instance_class` in the module configuration.

Storage scaling is automatically managed by AWS Aurora, see the [official documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Managing.Performance.html).

To add replicas to an existing cluser, follow the [official guide](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-replicas-adding.html).

### Linking

When linked to a k8s-service, it adds connection credentials to your container's environment variables as:

- `{module_name}_db_user`
- `{module_name}_db_password`
- `{module_name}_db_name`
- `{module_name}_db_host`

In the [modules reference](/reference) example, the _{module_name}_ would be replaced with `rds`.

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
