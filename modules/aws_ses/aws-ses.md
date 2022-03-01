---
title: "aws-ses"
linkTitle: "aws-ses"
date: 2021-07-21
draft: false
weight: 1
description: Sets up AWS SES for sending emails via your root domain
---

### Notes

- It's required to set up the [`aws-dns`]({{< ref "/reference/aws/modules/aws-dns" >}} "aws-dns") module with this.
- Opta also files a ticket with AWS support to get out of SES sandbox mode.
