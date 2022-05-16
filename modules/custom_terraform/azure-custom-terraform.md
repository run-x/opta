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
Suppose you have an opta azure environment written in `azure-env.yaml` and you want to deploy your custom terraform module
"blah" that creates something you want (in our case a vm instance). What you could do is create a service for your
environment which uses custom-terraform to call your module (NOTE: custom-terraform doesn't need to be in an opta 
service-- it can be in the environment too). For our example, let's say that the file structure looks like so:

```
.
├── README.md
├── azure-env.yaml
└── dummy-service
    ├── blah
    │    └── main.tf
    └── opta.yaml
```

The new service is written in `dummy-service/opta.yaml` and looks like this:

```yaml
environments:
  - name: azure-example
    path: "../azure-env.yaml"
name: customtf
modules:
  - type: custom-terraform
    name: vm1
    source: "./blah"
    terraform_inputs:
      env_name: "{env}"
```

You can see that the path to your module is specified by `source` (you can use relative or absolute paths),
as are the expected inputs `hello` and `subnet_self_link`. Note that you can use opta interpolation to use variables or
the outputs of the parent environment or other modules as input.

Lastly, you can use the following as content to the main.tf file of the blah module to complete the example/demo:

```hcl
variable "env_name" {
  type = string
}

variable "prefix" {
  type = string
  default = "placeholder"
}

data "azurerm_resource_group" "opta" {
  name = "opta-${var.env_name}"
}

data "azurerm_subnet" "opta" {
  name                 = "opta-${var.env_name}-subnet"
  virtual_network_name = "opta-${var.env_name}"
  resource_group_name  = data.azurerm_resource_group.opta.name
}

resource "azurerm_network_interface" "main" {
  name                = "${var.prefix}-nic"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name

  ip_configuration {
    name                          = "testconfiguration1"
    subnet_id                     = data.azurerm_subnet.opta.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_virtual_machine" "main" {
  name                  = "${var.prefix}-vm"
  location              = data.azurerm_resource_group.opta.location
  resource_group_name   = data.azurerm_resource_group.opta.name
  network_interface_ids = [azurerm_network_interface.main.id]
  vm_size               = "Standard_DS1_v2"

  storage_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "16.04-LTS"
    version   = "latest"
  }
  storage_os_disk {
    name              = "myosdisk1"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }
  os_profile {
    computer_name  = "hostname"
    admin_username = "testadmin"
    admin_password = "Password1234!"
  }
  os_profile_linux_config {
    disable_password_authentication = false
  }
  tags = {
    environment = "staging"
  }
}
```

Once you opta apply the service you should see your new compute instance up and running in the Azure console and be able
to ssh into it.

## Use a remote terraform module
The `source` input uses terraform's [module source](https://www.terraform.io/language/modules/sources#module-sources)
logic behind the scenes and so follows the same format/limitations. Thus, you can use this for locally available modules,
or modules available remotely.Z

**WARNING** Be very, very, careful about what remote modules you are using, as they leave you wide open to supply chain
attacks, depending on the security and character of the owner of said module. It's highly advised to use either 
[official modules](https://registry.terraform.io/browse/modules) or modules under your company's control.

## Using Outputs from your Custom Terraform Module
Currently you can use outputs of your custom terraform module in the same yaml, like so:
```yaml
environments:
  - name: azure-example
    path: "../azure-env.yaml"
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