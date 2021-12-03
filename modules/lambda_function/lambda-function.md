---
title: "aws-lambda"
linkTitle: "aws-lambda"
date: 2021-12-02
draft: false
weight: 1
description: Creates a lambda deployment via opta.
---

*NOTE* The lambda module is currently in beta, with only the following functionality. Enhanced features and integrated
will be added in subsequent releases (and expedited as per user need). Please [reach out to the opta team](https://slack.opta.dev/)
for any questions/requests.

Creates an [AWS Lambda](https://docs.aws.amazon.com/lambda/index.html) deployment via opta from the given zip file plus 
much more setup. Currently, it also handles:

* Setting up a cloudwatch log group for your function logs
* Setting up an iam role for your lambda through which to grant permissions to.
* Exposing the lambda to a public uri if you so wish
* Allowing the user to pass in IAM policies to give to the lambda
* Setting up security group and network location if you have the `aws-base` module in your environment.

tl;dr -- this will deploy a hello world lambda
```yaml
name: testing-lambda
org_name: myorg
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXX
modules:
  - type: lambda-function
    expose_via_domain: true
```

## Adding your Own Function
Opta supports the [zip file form](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html) of 
lambda deployments. For this deployment, simply zip up your code into a zip file and pass its location in via the
`filename` input. You should also specify the [runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) 
for your lambda (what language+version you are using). Supposing you created a zip file called baloney.zip, your opta.yml
should look like the following:

```yaml
name: testing-lambda
org_name: myorg
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXX
modules:
  - type: lambda-function
    expose_via_domain: true
    filename: baloney.zip
    runtime: "nodejs14.x"
```

*NOTE* DO NOT add a subdirectory in the zip file-- make its structure flat unless you know what you're doing (this is
a common mistake with lambda)

## Accessing your function logs
As is the standard, all of your function invocation logs are stored in cloudwatch under a new log group. You can
find the log group name and even a helper shortcut url to them in the `opta output`.

## Expose via Public Domain
You can have your lambda be automatically exposed to the world via a public ui by setting the `expose_via_domain` field
to true. This creates a new AWS API Gateway V2 and configures it to pass the request over to your lambda function via
the official integration. Events (lambda inputs) for this use case will have the structure dictated 
[here](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html#apigateway-example-event) and expect
a response format dictated [here](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html#apigateway-types-transforms)

## IAM Permissions
As mentioned, a new IAM role will be created just for your lambda's usage. If you wish to give this role extra permissions,
then you simply need to find (or create) the AWS IAM policy with the desired permissions, and add its ARN to the list of
`extra_iam_policies` like so:

```yaml
name: testing-lambda
org_name: myorg
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXX
modules:
  - type: lambda-function
    .
    .
    .
    extra_iam_policies:
      - "arn:aws:iam::XXXXXXX:policy/my-super-special-policy"
```

## Work within your VPC
The lambda function module will work even if you do not have `aws-base` set up, but if aws-base is added, then it will
create your function in your private subnets. This gives your function added security as well as the ability to access
resources in your vpc like your postgres database or redis cache.

## As a Standalone Environment or Service
As you may have noticed above, the lambda module can be created as its own standalone environment, not requiring any
additional setup, but it is encouraged to treat it as a service so that it can be part of a bigger ecosystem of resources.

```yaml
environments:
  - name: aws-example
    path: "../aws-env.yml"
name: testing-lambda
modules:
  - type: lambda-function
    expose_via_domain: true
    filename: baloney.zip
```