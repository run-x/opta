---
title: "Deploy to AWS Button"
linkTitle: "Deploy to AWS Button"
date: 2021-07-21
weight: 1
description: >
  Allow your users to fill out their AWS Opta templates with the click of a button.
---

## Overview

Opta's Deploy to AWS button allows users to deploy complex applications using Opta by simply filling out a form, downloading a file, and running `opta deploy`. This button is great to put into README files or on your website.

Below is an example button that deploys an open source tool called Retool.

[![Deploy to AWS Button](https://raw.githubusercontent.com/run-x/opta/main/assets/deploy-to-aws-button.svg)](http://app.runx.dev/deploy-with-aws?url=https%3A%2F%2Fgithub.com%2Frun-x%2Ftest-opta-template%2Fblob%2Fmain%2Fopta%2Ftemplate.yaml&name=Retool)

## Creating a button

### Step 1: Creating an Opta Template File

The first step in creating your button is creating an Opta template. The format of a template is simple: it's a normal opta.yaml, except some parts of replaced with variables. The format of a variable is: `<<variable_name::variable_type::description>>`.

Here is an example of an template file for a service called Retool:

```yaml
name: retool
org_name: <<org_name::org_name::Your Organization Name>>
providers:
  aws:
    region: <<region::aws_region::Your AWS Region>>
    account_id: <<account_id::aws_account_id::Your AWS Account ID>>
modules:
  - type: base
  - type: k8s-cluster
    node_instance_type: t3.medium
    max_nodes: 5
    spot_instances: true
  - type: k8s-base
  - type: dns
    domain: <<domain::string::The dns domain for your Retool deployment>>
    delegated: false
  - name: postgres
    type: postgres
  - type: helm-chart
    name: console
    chart: retool
    repository: https://charts.retool.com
    chart_version: "4.5.0"
    values:
      postgresql:
        enabled: false
      config:
        encryptionKey: abcdefghijklmnopqrstuvwxyz
        jwtSecret: abcdefghijklmnopqrstuvwxyq
        postgresql:
          port: 5432
          user: "${{module.postgres.db_user}}"
          host: "${{module.postgres.db_host}}"
          db: "${{module.postgres.db_name}}"
          password: "${{module.postgres.db_password}}"
      image:
        tag: <<image_tag::string::The docker image to deploy>>
      ingress:
        enabled: true
        apiVersion: "networking.k8s.io/v1beta1"
        hostName: "{module.dns.domain}"
```

You might notice that some of the variable "types" like `org_name`, `aws_region`, and `aws_account_id` in the above template are pretty specific. These types are associated with all sorts of special validations that will help make this deployment process more dummy-proof for your users. You can find the full list of types in the [Types Section](#types) of this page.

Once you're done creating your yaml file, upload it to your public Github repository.

#### Types

Below is a list of all of the types currently available to use in your Opta template.

| Name             | Description                                             |
| ---------------- | ------------------------------------------------------- |
| `org_name`       | The name of an Opta organization                        |
| `aws_region`     | The aws region where an application will be deployed    |
| `aws_account_id` | The ID of an AWS account                                |
| `string`         | A vanilla string with no other special validation rules |

### Step 2: Generating Button HTML and Testing

To create your button, simply go to [our button creation UI](http://app.runx.dev/make-aws-button) and enter what you would like to name your template as well as the URL of your opta template. The UI will render your button. Click on the button and make sure that the resulting form looks like you expect it to.

### Step 3: Putting the button everywhere!

Once you're sure that everything's working as you expected, copy and paste the HTML from the button creation page, and put it whereever you'd like!
