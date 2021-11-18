---
title: "cloudfront-distribution"
linkTitle: "cloudfront-distribution"
date: 2021-11-16
draft: false
weight: 1
description: Set up a cloudfront distribution to serve static files from your s3 bucket
---

This module sets up a cloudfront distribution for you, tailored towards serving static websites/files from an Opta s3 
bucket (currently just for a single S3, but will expand for more complex usage in the future). Now, hosting your 
static site with opta can be as simple as:

```yaml
name: testing-cloufront
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXXX
modules:
  - type: aws-s3
    name: blah
    bucket_name: "opta-is-testing-cloudfront"
    files: "./my-site-files" # See S3 module for more info about uploading your files t S3
  - type: cloudfront-distribution
    # Uncomment the following and fill in to support your domain with ssl
#    acm_cert_arn: "arn:aws:acm:us-east-1:XXXXXXXXXX:certificate/cert-id"
#    domains:
#      - "your.domain.com"
    links:
      - blah
```

Once you Opta apply, check out the `cloudfront_domain` output and go to the site. You should see the files of your S3
bucket (both those uploaded with Opta and outside of Opta) being served there-- simply refer to them by key name in the
path (e.g. if in your bucket you have hello.txt and subdir/hello.txt, then you should see them via 
https://the.cloudfront.domain/hello.txt and https://the.cloudfront.domain/subdir/hello.txt).

### Cloudfront Caching
While your S3 bucket is the ultimate source of truth about what cloudfront serves, Cloudfronts flagship feature is its
caching capabilities. That means that while delivery speeds are significantly faster, cloudfront may take some time
(~1hr) to reflect changes into your static site deployment. Please keep this in mind when deploying such changes. You
may immediately verify the latest copy by downloading from your S3 bucket directly.

### Using your own domain
If you are ready to start hosting your site with your domain via the cloudfront distribution, then proceed as follows:
1. Get an [AWS ACM certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html) for your site. 
   Make sure that you get it in region us-east-1. If you already have one at hand in your account (e.g. from another 
   active Opta deployment), then feel free to reuse that.
2. In whatever hosted zone you are using to manage the DNS for your domain (or the parent domain), create a new CNAME 
   record for the domain you wish to use for cloudfront and point it at the `cloudfront_domain` gotten above.
3. Set the acm_cert_arn and domains fields in opta accordingly
4. Opta apply and you're done!
