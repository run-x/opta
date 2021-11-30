---
title: "aws-sqs"
linkTitle: "aws-sqs"
date: 2021-07-21
draft: false
weight: 1
description: Sets up a AWS SQS queue
---

### Linking

When linked to a k8s-service or IAM role/user, this adds the necessary IAM permissions to publish
(e.g. put new messages) and/or subscribe (e.g. read/remove messages) to the given queue.
The current permissions are, "publish" and "subscribe", defaulting to \["publish", "subscribe",] if none specified.
Link also grants encrypt/decrypt permission for the queue's KMS key.
