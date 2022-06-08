---
title: "aws-iam-policy"
linkTitle: "aws-iam-policy"
date: 2022-06-08
draft: false
weight: 1
description: Creates an IAM policy
---

This module can be used to create and manage an AWS IAM policy via opta

### Example

```
  - name: deployer
    type: aws-iam-policy
    file: valid_policy.json
```