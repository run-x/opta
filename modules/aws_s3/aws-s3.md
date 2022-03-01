---
title: "aws-s3"
linkTitle: "aws-s3"
date: 2021-07-21
draft: false
weight: 1
description: Creates an S3 bucket for storage purposes
---

This module creates an S3 bucket for storage purposes. It is created with server-side AES256 encryption.


### Example

```yaml
  - name: bucky
    type: aws-s3
    bucket_name: dev-runx-bucky
    cors_rule:
      allowed_methods:
        - "PUT"
      max_age_seconds: 3600
      allowed_origins:
        - "runx.dev"
```

### File uploading
To upload files to s3, just set the `files` field to the path (relative to the yaml or absolute) of a local directory. 
On the next apply, all the files and subdirectories will be automatically uploaded to the bucket!


So for example if you called the module like so:
```yaml
  - type: s3
    name: blah
    bucket_name: "opta-is-testing-cloudfront"
    files: "../blah"
```

And the `../blah` directory had the following structure:
```
../blah
├── hello2.html
├── hello2.txt
├── hello3.txt
└── subdir
    └── hello3.html
```

Then Opta would upload 4 files to your S3 bucket, with the S3 keys being `hello2.html`, `hello2.txt`, `hello3.txt` and
`subdir/hello3.html`.

Opta will also catch any changes to the files on the next `opta apply` and will push updates as needed. Opta supports
extensive MIME parsing, so it also makes sure to set the content type correctly.

### Cloudfront
This module can be [linked to Opta's cloudfront module](/reference/aws/modules/cloudfront-distribution/) in order to serve static files.

To securely work with cloudfront, the module additionally creates a Cloudfront Origin Access Identity with read 
privileges to be used by cloudfront to access its contents.

### Linking

When linked to a k8s-service or IAM role/user, this adds the necessary IAM permissions to read
(e.g. list objects and get objects) and/or write (e.g. list, get,
create, destroy, and update objects) to the given s3 bucket.
The current permissions are, "read" and "write", defaulting to "write" if none specified
