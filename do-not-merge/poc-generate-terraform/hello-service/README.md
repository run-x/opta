
# THIS FILE WILL BE GENERATED

Follow the execution steps in the order defined in this document to allow depending resources to be created in the expected order.

# Check that the environment was provisioned

Before executing Terraform for a service make sure that the required infrastucture (VPC, Kubernetes) was previously created.

The main terraform file `service-hello.tf.json` comes pre-configured to point to a local terraform state file. If you want to use a remote state instead, change the section `terraform/backend`. See the [terraform documentation](https://www.terraform.io/language/state/remote) for supported backends.

Also if you are not using Opta to create your Kubernetes cluster:
- You can run `opta generate-terraform env.yaml` to generate the terraform files for an Opta environment.
- Or, you can provide the required input by replacing the variabes starting with `data.terraform_remote_state.parent` with their respective values regarding your existing infrastructure.
    - ex: `data.terraform_remote_state.parent.outputs.k8s_cluster_name` should be replaced with the cluster name.

# Initialize Terraform

```
terraform init
...
Terraform has been successfully initialized!
```

# Execute Terraform for the service hello

This step will execute terraform for the modules `k8s_service` named hello.

```
terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.hello 
...
Plan: 5 to add, 0 to change, 0 to destroy.
```

```
terraform apply -compact-warnings -auto-approve tf.plan
...
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.
```

# Destroy

```
terraform plan -compact-warnings -lock=false -input=false -out=tf.plan -target=module.hello  -destroy

Plan: 0 to add, 0 to change, 5 to destroy.

terraform apply -compact-warnings -auto-approve tf.plan
```

# Additional information

This file was generated with `opta generate-terraform`.
- Opta version: v0.24.3
- Generated at: 2022-01-26T04:32:34+00:00.
