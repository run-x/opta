---
title: "aws-iam-role"
linkTitle: "aws-iam-role"
date: 2021-06-06
draft: false
weight: 1
description: Creates an IAM policy
---

This module can be used to create and manage an AWS IAM policy via opta

### Example

```
  - name: deployer
    type: aws-iam-role
    extra_iam_policies:
      - "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
    allowed_k8s_services:
      - namespace: "*"
        service_name: "*"
```