---
title: "custom-terraform"
linkTitle: "custom-terraform"
date: 2022-01-18
draft: false
weight: 1
description: Allows user to bring in their own custom terraform module
---

This module allows a user to bring in their own custom terraform code into the opta ecosystem, to use in tandem with
their other opta modules, and even reference them. All a user needs to do is specify the
[source](https://www.terraform.io/language/modules/sources#module-sources)
to your module with the `source` input, and the desired inputs to your module (if any) via the
`terraform_inputs` input.

## Use local terraform files

Let's create a AWS EC2 instance using terraform.

Here is the directory structure for this example:

```
.
├── opta.yaml       # the opta environment file for AWS
├── custom-tf.yaml  # define the opta custom-terraform module
└── my-terraform    # place all the terraform files in this directory
    └── main.tf
```


{{< tabs tabTotal="3" >}}
{{< tab tabName="custom-tf.yaml" >}}
```yaml
# custom-tf.yaml
name: customtf
environments:
  - name: staging
    path: "../opta.yaml"
modules:
  - type: custom-terraform
    name: customtf
    # where the terraform files are located
    source: "./my-terraform"
    terraform_inputs:
      # some input variables for terraform
      instance_name: "hello-world"
      # use opta interpolation to use variable from the parent
      private_subnet_ids: "{parent.private_subnet_ids}"
```
{{< /tab >}}

{{< tab tabName="opta.yaml" >}}

```yaml
# opta.yaml
name: staging # name of the environment
org_name: my-org # A unique identifier for your organization
providers:
  aws:
    region: us-east-1
    account_id: XXXX # Your 12 digit AWS account id
modules:
  - type: base
  - type: k8s-cluster
  - type: k8s-base
```

{{< /tab >}}

{{< tab tabName="main.tf" >}}

```
# main.tf

# set by opta in terraform_inputs.private_subnet_ids
variable "private_subnet_ids" {
  description = "Use existing Private subnet ids"
  type        = list(string)
  default     = null
}

# set by opta in terraform_inputs.instance_name
variable "instance_name" {
  description = "Name your instance"
  type        = string
  default     = null
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  # Canonical: Publisher of Ubuntu
  owners = ["099720109477"]
}

resource "aws_instance" "my_instance" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = var.private_subnet_ids[0]

  tags = {
    Name = "${var.instance_name}"
  }

}
```
{{< /tab >}}

{{< /tabs >}}

Run opta apply to create the custom terraform resources:

```bash
opta apply -c custom-tf.yaml
```
```console
╒══════════╤══════════════════════════╤══════════╤════════╤══════════╕
│ module   │ resource                 │ action   │ risk   │ reason   │
╞══════════╪══════════════════════════╪══════════╪════════╪══════════╡
│ customtf │ aws_instance.my_instance │ create   │ LOW    │ creation │
╘══════════╧══════════════════════════╧══════════╧════════╧══════════╛
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

Once you opta apply the service you should see your new EC2 instance up and running in the AWS console and be able to ssh into it.

When done, you can destroy the custom terraform resource:
```bash
opta destroy -c custom-tf.yaml
```

## Use a remote terraform module
The `source` input uses terraform's [module source](https://www.terraform.io/language/modules/sources#module-sources)
logic behind the scenes and so follows the same format/limitations. Thus, you can use this for locally available modules,
or modules available remotely, like so:

```yaml
environments:
  - name: staging
    path: "../opta.yaml"
name: customtf
modules:
  - type: custom-terraform
    name: bucket
    source: "terraform-aws-modules/s3-bucket/aws" # See https://registry.terraform.io/modules/terraform-aws-modules/s3-bucket/aws/latest
    version: "2.13.0" # version needs to be specified for remote registry modules
    terraform_inputs:
      bucket: "dummy-bucket-{aws.account_id}"
      acl: "private"
      versioning: 
        enabled: true
```

**WARNING** Be very, very, careful about what remote modules you are using, as they leave you wide open to supply chain
attacks, depending on the security and character of the owner of said module. It's highly advised to use either
[official modules](https://registry.terraform.io/browse/modules) or modules under your company's control.

## Using Outputs from your Custom Terraform Module
Currently you can use outputs of your custom terraform module in the same yaml, like so:
```yaml
environments:
  - name: staging
    path: "../opta.yaml"
name: customtf
modules:
  - type: custom-terraform
    name: tf1
    source: "./my-terraform-1" # <-- This module has an output called output1
  - type: custom-terraform
    name: tf2
    source: "./my-terraform-2"
    terraform_inputs:
      input1: "${{module.tf1.output1}}" # <-- HERE. Note the ${{}} wrapping
```

These outputs, however, currently can not be used in other yamls (e.g. if you put custom terraform in an environment
yaml its outputs can't be used in the services), and will not show up in the `opta output` command. Work on supporting
this is ongoing.
