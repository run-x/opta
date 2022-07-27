# What is this?

This example shows how Opta can use a remote terraform module to spin up an
[Amazon Redshift](https://docs.aws.amazon.com/redshift/latest/mgmt/welcome.html) instance.


# What does this do?
This manifest begins by deploying an Opta base, which creates a VPC to be used by Redshift. It then
invokes the AWS maintained [Redshift security group submodule](https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/1.24.0/submodules/redshift)
to create a security group on said VPC for Redshift uses. Lastly it calls the actual AWS maintained
[Redshift remote module](https://registry.terraform.io/modules/terraform-aws-modules/redshift/aws/latest), which will
be deployed on the aforementioned VPC with the aforementioned security group.

As demonstrated, Opta is perfectly capable of living in harmony with external modules.

# Steps to deploy
* Fill in the required variables in the config file, redshift.yaml.
* Run `opta apply -c redshift.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. A new Redshift instance is deployed on AWS. 

You can further configure your Redshift instance by referring to the remote module's documentation and updating the 
input fields in the Opta manifest.

![End Result](end_result.png?raw=true "What it should look like")

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
