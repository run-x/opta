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
```yaml
  - name: policy
    type: aws-iam-policy
    file: valid_policy.json
```

Note: A valid policy document would look something like this.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "ec2:Describe*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
```
