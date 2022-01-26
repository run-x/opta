# THIS FILE WILL BE GENERATED

Follow the execution steps in the order defined in this document to allow depending resources to be created in the expected order.

# Check the backend configuration

The main terraform file `service-hello.tf.json` comes pre-configured to point to a local terraform state file. If you want to use a remote state instead, change the section `terraform/backend`. See the [terraform documentation](https://www.terraform.io/language/state/remote) for supported backends.

# Initialize Terraform

```
terraform init
...
Terraform has been successfully initialized!
```

# Execute Terraform for modules base, k8scluster

This step will execute terraform for the modules `base, k8scluster`.

```
terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.base -target=module.k8scluster
...
Plan: 50 to add, 0 to change, 0 to destroy.
```

```
terraform apply -compact-warnings -auto-approve tf.plan
```

# Execute Terraform for modules k8sbase

This step will execute terraform for the modules `k8sbase`.

```
terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.base -target=module.k8scluster -target=module.k8sbase
...
Plan: 23 to add, 0 to change, 0 to destroy.
```

```
terraform apply -compact-warnings -auto-approve tf.plan
```

# Execute Terraform for the managed service

If you have some generated terraform files for services, you can executed them at this stage. 

# Destroy

If you have some services managed by terraform, destroy them first.

To destroy the environment run:
```
terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.base -target=module.k8scluster -target=module.k8sbase -destroy

Plan: 0 to add, 0 to change, 87 to destroy.

terraform apply -compact-warnings -auto-approve tf.plan
```

# Additional information

This file was generated with `opta generate-terraform`.
- Opta version: v0.24.3
- Generated at: 2022-01-26T04:32:34+00:00.
