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
    domain: staging.startup.com # Fill in with your desired domain, or remove this whole entry if handling dns outside of Opta
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
    domain: staging.startup.com # Fill in with your desired domain, or remove this whole entry if handling dns outside of Opta
    delegated: false # Set to true when ready -- see the "Configure DNS" page
    linked_module: cloudfront-distribution
  - type: k8s-cluster
  - type: k8s-base
    name: testbase
  - type: cloudfront-distribution
    # Uncomment to add an AWS WAF to your cloudfront distribution
    # web_acl_id: "your_web_acl_id_or_arn"
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
If you are ready to start hosting your site with your domain via the cloudfront distribution, then go ahead and follow 
the [configuring dns guide](/features/dns-and-cert/dns), which will also set up your SSL. Traffic should
start flowing from your domain to your cloudfront distribution and on towards your S3 bucket / K8s cluster. You could
also manually configure DNS / SSL from outside of Opta using the following steps:
1. Remove the dns module entirely from your yaml, if you haven't already.
2. Get an [AWS ACM certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html) for your site. 
   Make sure that you get it in region us-east-1. If you already have one at hand in your account (e.g. from another 
   active Opta deployment), then feel free to reuse that.
3. [Validate](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html) the certificate by adding the correct CNAME entries in your domain's DNS settings. Specific instructions for popular domain providers are [explained here](https://docs.aws.amazon.com/amplify/latest/userguide/custom-domains.html).
4. Fill in the `acm_cert_arn` field for the cloudfront module with the arn of your cert.
5. In your hosted zone, create either an A record (if it's on the same AWS account) or a CNAME pointing to the cloudfront
   distribution url (the `cloudfront_domain` output). Alternatively, if it's a hosted zone on the same AWS account you could pass the `zone_id` to the
   cloudfront module to have Opta automatically take care of this for you.
6. Fill in the `domains` field to include the domains for which you have the certificate for (no need to include wildcard repetition, that's automatic).
7. Opta apply and you're done!

### AWS WAF with Cloudfront

[AWS WAF](https://aws.amazon.com/waf/) is a web application firewall that helps protect your web applications or APIs against common web exploits and bots that may affect availability, compromise security, or consume excessive resources. In this section we explain how to configure AWS WAF with your Cloudfront distribution. 

As a pre-requisite, follow the steps in the previous section (__Using your own domain__) to create a and validate a certificate for the custom domain. After completing those steps, users have the ability to access your services at `https://your-custom-domain`; and because your CNAME record for your custom domain points to the cloudfront distribution URL, traffic will be directed through your cloud-front distribution.

Next, we need to create an AWS WAF to protect our service and cloudfront CDN cache. We do this via the [AWS WAF GUI](https://console.aws.amazon.com/wafv2/homev2).

Here are a few screen shots showing how the WAF GUI values can be configured for a "passthrough" WAF to start with.

We start at the WAF landing page in the AWS Console:

<a href="/reference_images/aws/cloudfront-distribution/aws-waf-1.png" target="_blank">
  <img src="/reference_images/aws/cloudfront-distribution/aws-waf-1.png" align="center"/>
</a>

We configure the WAF to use the cloudfront distribution we created with Opta; this can be selected by selecting the `Cloudfront distribution` radio button and then clicking on the `Add AWS Resources` button to select the cloudfront distribution; you should then end up with something like so:

<a href="/reference_images/aws/cloudfront-distribution/aws-waf-2.png" target="_blank">
  <img src="/reference_images/aws/cloudfront-distribution/aws-waf-2.png" align="center"/>
  </a>

The initial configuration of the WAF allows all traffic:

<a href="/reference_images/aws/cloudfront-distribution/aws-waf-3.png" target="_blank">
  <img src="/reference_images/aws/cloudfront-distribution/aws-waf-3.png" align="center"/>
</a>

Finally, please [configure AWS WAF rules](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html) for your specific application protection needs.


Lastly, make sure to pass your new WAF to Opta by setting the `web_acl_id` input (if you're using WAFv2
set it to the arn of the ACL created, if you used AWS WAF Classic, then use the ACL ID).