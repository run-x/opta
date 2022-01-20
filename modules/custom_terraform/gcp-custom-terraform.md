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
Suppose you have an opta gcp environment written in `gcp-env.yaml` and you want to deploy your custom terraform module
"blah" that creates something you want (in our case a vm instance). What you could do is create a service for your
environment which uses custom-terraform to call your module (NOTE: custom-terraform doesn't need to be in an opta 
service-- it can be in the environment too). For our example, let's say that the file structure looks like so:

```
.
├── README.md
├── gcp-env.yaml
└── dummy-service
    ├── blah
    │    └── main.tf
    └── opta.yaml
```

The new service is written in `dummy-service/opta.yaml` and looks like this:

```yaml
environments:
  - name: gcp-example
    path: "../gcp-env.yaml"
name: customtf
modules:
  - type: custom-terraform
    name: vm1
    source: "./blah"
    terraform_inputs:
      hello: "world"
      subnet_self_link: "{parent.private_subnet_self_link}"
# You can call it multiple times if you like
#  - type: custom-terraform
#    name: vm2
#    source: "./blah"
#    terraform_inputs:
#      hello: "world2"
#      subnet_self_link: "{parent.private_subnet_self_link}"
```

You can see that the path to your module is specified by `source` (you can use relative or absolute paths),
as are the expected inputs `hello` and `subnet_self_link`. Note that you can use opta interpolation to use variables or
the outputs of the parent environment or other modules as input.

Lastly, you can use the following as content to the main.tf file of the blah module to complete the example/demo:

```hcl
variable "hello" {
  type = string
}

variable "subnet_self_link" {
  type = string
}

data "google_compute_subnetwork" "my-subnetwork" {
  self_link = var.subnet_self_link
}

resource "random_string" "suffix" {
  length = 4
  upper = false
  special = false
}

resource "google_service_account" "default" {
  account_id   = "custom-terraform-${random_string.suffix.result}"
  display_name = "Service Account"
}

resource "google_compute_firewall" "k8s_extra_rules" {
  name      = "custom-terraform-${random_string.suffix.result}"
  network   = data.google_compute_subnetwork.my-subnetwork.network
  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["open-to-public-${random_string.suffix.result}"]
}

resource "google_compute_instance" "default" {
  name         = "test-${random_string.suffix.result}"
  machine_type = "n2-standard-4"
  zone         = "us-central1-a"

  tags = ["open-to-public-${random_string.suffix.result}"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  // Local SSD disk
  scratch_disk {
    interface = "SCSI"
  }

  network_interface {
    subnetwork = var.subnet_self_link
    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    foo = "bar"
  }

  metadata_startup_script = "echo ${var.hello} > /test.txt"

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = google_service_account.default.email
    scopes = ["cloud-platform"]
  }
}
```

Once you opta apply the service you should see your new compute instance up and running in the GCP console and be able
to ssh into it.

## Use a remote terraform module
The `source` input uses terraform's [module source](https://www.terraform.io/language/modules/sources#module-sources)
logic behind the scenes and so follows the same format/limitations. Thus, you can use this for locally available modules,
or modules available remotely, like so:

```yaml
environments:
  - name: gcp-example
    path: "../gcp-env.yaml"
name: customtf
modules:
  - type: custom-terraform
    name: buckets
    source: "terraform-google-modules/cloud-storage/google" # See https://registry.terraform.io/modules/terraform-google-modules/cloud-storage/google/latest
    version: "~> 3.1" # version needs to be specified for remote registry modules
    terraform_inputs:
      project_id: "<PROJECT ID>"
      names: ["first", "second"]
      prefix: "my-unique-prefix"
      set_admin_roles: true
      admins: ["group:foo-admins@example.com"]
      versioning: {
          first: true
        }
      bucket_admins: {
        second: "user:spam@example.com,eggs@example.com"
      }
```

**WARNING** Be very, very, careful about what remote modules you are using, as they leave you wide open to supply chain
attacks, depending on the security and character of the owner of said module. It's highly advised to use either 
[official modules](https://registry.terraform.io/browse/modules) or modules under your company's control.

## Using Outputs from your Custom Terraform Module
Currently you can use outputs of your custom terraform module in the same yaml, like so:
```yaml
environments:
  - name: gcp-example
    path: "../gcp-env.yaml"
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