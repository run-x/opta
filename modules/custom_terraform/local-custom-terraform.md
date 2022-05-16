---
title: "custom-terraform"
linkTitle: "custom-terraform"
date: 2021-12-7
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
Suppose you have an opta k8s service which you wish to write down the name of the current image in a file. For this
you have written a small terraform module just to write down input to a local file. What you could do is create a 
service for your environment which uses custom-terraform to call your module. For our example, let's say that the file 
structure looks like so:

```
.
├── blah
│    └── main.tf
└── opta.yaml
```

The new service is written in `dummy-service/opta.yaml` and looks like this:

```yaml
name: customtf
modules:
  - type: k8s-service
    name: hello
    port:
      http: 80
    image: "ghcr.io/run-x/hello-opta/hello-opta:main"
    healthcheck_path: "/"
    public_uri: "/hello"
  - type: custom-terraform
    name: currentimage
    source: "./blah"
    terraform_inputs:
      to_write: "${{module.hello.current_image}}"
```

You can see that the path to your module is specified by `source` (you can use relative or absolute paths),
as are the expected input `to_write`. Note that you can use opta interpolation to use variables or
the outputs of the parent environment or other modules as input.

Lastly, you can use the following as content to the main.tf file of the blah module to complete the example/demo:

```hcl
variable "to_write" {
  type = string
}

resource "local_file" "foo" {
  content  = "${var.to_write}"
  filename = "${path.module}/foo.bar"
}
```

Once you opta apply the service you should see your new file locally!

## Use a remote terraform module
The `source` input uses terraform's [module source](https://www.terraform.io/language/modules/sources#module-sources)
logic behind the scenes and so follows the same format/limitations. Thus, you can use this for locally available modules,
or modules available remotely.

**WARNING** Be very, very, careful about what remote modules you are using, as they leave you wide open to supply chain
attacks, depending on the security and character of the owner of said module. It's highly advised to use either 
[official modules](https://registry.terraform.io/browse/modules) or modules under your company's control.

## Using Outputs from your Custom Terraform Module
Currently you can use outputs of your custom terraform module in the same yaml, like so:
```yaml
name: customtf
modules:
  - type: custom-terraform
    name: hi1
    source: "./blah1" # <-- This module has an output called output1
  - type: custom-terraform
    name: hi2
    source: "./blah2"
    terraform_inputs:
      input1: "${{module.hi1.output1}}" # <-- HERE. Note the ${{}} wrapping
```

These outputs, however, currently can not be used in other yamls (e.g. if you put custom terraform in an environment 
yaml its outputs can't be used in the services), and will not show up in the `opta output` command. Work on supporting 
this is ongoing.