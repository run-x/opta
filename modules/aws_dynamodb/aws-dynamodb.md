---
title: "dynamodb-table"
linkTitle: "dynamodb-table"
date: 2021-07-21
draft: false
weight: 1
description: Creates a dynamodb table to use
---

This module creates a dynamodb table as per the specifications in the input.

### Linking

When linked to a k8s-service or IAM role/user, this adds the necessary IAM permissions to publish
notifications to the topic. The current permissions allowed are "read" and "write" (defaults to "write).
Link also grants encrypt/decrypt permission for the table's KMS key.