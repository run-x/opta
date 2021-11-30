---
title: "aws-iam-user"
linkTitle: "aws-iam-user"
date: 2021-07-21
draft: false
weight: 1
description: Creates an IAM user
---

This module can be used to create and manage an AWS IAM user via opta.

### Linking

This module can also be linked to other resource - which will provide it
permission to access them.

### Example

```
  - name: user
    type: aws-iam-user
    extra_iam_policies:
      - "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
    links:
      - s3: ["write"]
      - notifcationsQueue
      - schedulesQueue
      - topic
```