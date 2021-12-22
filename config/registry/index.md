---
title: "References"
linkTitle: "References"
weight: 5
description: >
  Opta config reference
---

# What's an Opta module?

The heart of Opta is a set of "Modules" which basically map to cloud resources that
need to get created. Opta yamls reference these under the `modules` field.

```yaml
name: myapp
environments:
  - name: staging
    path: "../env/opta.yaml"
modules:
  - name: app # This is an instance of the k8-service module type called app
    type: k8s-service
    port:
      http: 80
    image: AUTO
    public_uri: "app.{parent.domain}/app"
    resource_request:
      cpu: 100 # in millicores
      memory: 512 # in megabytes
    healthcheck_path: "/get"
    env_vars:
      ENV: "{env}"
    links:
      - rds
      - cache
  - name: rds # This is an instance of the aws-rds module type called mydatabase
    type: postgres
  - name: cache # This is an instance of the aws-redis module type called myredis
    type: redis
```

You'll note that the module instance can have user-specified names which will come into play later with references.
Opta modules are composed of the following entities/behaviors:

## Fields

You'll note that there can be many, varying, fields per module instance such
as "type", "env*vars", "image" etc... These are called \_fields* and this
is how specific data is passed into the modules.

### Names

All modules have a name field, which is used to create the name of the cloud resources in conjunction with the layer
name (root name of opta.yaml). A user can specify this with the `name` field, but it defaults to the module type (without
the hyphens) if not given.

### Types

All modules have their own list of supported fields, but the one common to all is _type_. The type field is simply
the module reference (e.g. the library/package to use in this "import"). Opta currently comes with its list of valid
modules built in -- future work may allow users to specify their own.

### Linking

The k8s-service module type is the first (but not the last) module to support
special processing. In this case, it's in regard to the _links_ field. The
links field takes as input a list of maps with a single element where the
key is the name of another module in the file, and the value a list of
strings representing resource permissions.

```yaml
name: myapp
environments:
  - name: staging
    path: "../env/opta.yaml"
modules:
  - name: app
    type: k8s-service # This is an instance of the k8-service module type called app
.
.
.
    links:
    - rds
    - redis
    - docdb
    - bucket:
      - write
  - name: rds # This is an instance of the postgres module type called rds
    type: postgres
  - name: redis # This is an instance of the redis module type called redis
    type: redis
  - name: docdb
    type: aws-documentdb
  - name: bucket
    type: aws-s3
    bucket_name: "test-bucket"