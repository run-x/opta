---
title: "cloudfront-distribution"
linkTitle: "cloudfront-distribution"
date: 2021-11-16
draft: false
weight: 1
description: Set up a cloudfront distribution
---

This module sets up a cloudfront distribution for you.

1. It can be tailored towards serving static websites/files from an Opta s3 
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
    bucket_name: "a-unique-s3-bucket-name"
    files: "./my-site-files" # See S3 module for more info about uploading your files to S3
    name: testmodule
  - type: dns 
    domain: staging.startup.com
    delegated: false # Set to true when ready -- see the "Configure DNS" page
    linked_module: cloudfront-distribution
  - type: cloudfront-distribution
    links:
      - testmodule
```

Once you Opta apply, run `opta output` to get the value of your `cloudfront_domain`. `index.html` is automatically served at this domain.
2. It can be tailored to serve as a CDN for the Load Balancer for the Cluster.
```yaml
name: testing-cloufront
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXXX
modules:
  - type: base
  - type: dns
    domain: staging.startup.com
    delegated: false # Set to true when ready -- see the "Configure DNS" page
    linked_module: cloudfront-distribution
  - type: k8s-cluster
  - type: k8s-base
    name: testbase
    expose_self_signed_ssl: true
  - type: cloudfront-distribution
    links:
      - testbase
```

### Non-opta S3 bucket handling
If you wish to link to a bucket created outside of opta, then you can manually set the `bucket_name` and 
`origin_access_identity_path` fields to the name of the bucket which you wish to link to, and the path of an
origin access identity that has read permissions to your bucket.

### Cloudfront Caching
While your S3 bucket is the ultimate source of truth about what cloudfront serves, Cloudfronts flagship feature is its
caching capabilities. That means that while delivery speeds are significantly faster, cloudfront may take some time
(~1hr) to reflect changes into your static site deployment. Please keep this in mind when deploying such changes. You
may immediately verify the latest copy by downloading from your S3 bucket directly.

### Domain / DNS
If you are ready to start hosting your site with your domain via the cloudfront distribution, then go ahead and uncomment
the dns modules in the example above, and follow the [configuring dns guide](/features/dns-and-cert/dns). Traffic should
start flowing from your domain to your cloudfront distribution and on towards your S3 bucket / K8s cluster. You could
also manually configure DNS / SSL from outside of Opta using the following steps:
1. Get an [AWS ACM certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html) for your site. 
   Make sure that you get it in region us-east-1. If you already have one at hand in your account (e.g. from another 
   active Opta deployment), then feel free to reuse that.
2. [Validate](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html) the certificate by adding the correct CNAME entries in your domain's DNS settings. 
3. Create a new separate CNAME record for the domain you wish to use for cloudfront and point it at the `cloudfront_domain` gotten above.
4. Fill in the `acm_cert_arn` field with the arn of your cert.
5. In your hosted zone, create either an A record (if it's on the same AWS account) or a CNAME pointing to the cloudfront
   distribution url. Alternatively, if it's a hosted zone on the same AWS account you could pass the `zone_id` to the
   cloudfront module to have Opta automatically take care of this for you.
6. Fill in the `domains` field to include the domains for which you have the certificate for (no need to include wildcard repetition, that's automatic).
7. Opta apply and you're done!
