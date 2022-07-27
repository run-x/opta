# What is this?

This is an example [opta](https://github.com/run-x/opta) configuration file to deploy [Apache Airflow](https://airflow.apache.org/) on AWS.


# What does this do?
It deploys a single container version of airflow on EKS in AWS. It uses AWS managed RDS instances and elasticcache. It also sets up various other resources like VPCs, subnets, load balancers etc.

# Steps to deploy
* Fill in the required variables in the config file
* Run `opta apply -c airflow-aws.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. Airflow is deployed on AWS. You can find the AWS load balancer URL to access the deployment by running `opta output`

To get DNS to work follow the next section

# Getting DNS to work
* Run `opta output -c airflow-aws.yaml` to get the nameservers. You will see a section like this:
```yaml
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `airflow-aws.yaml` file
* Run `opta apply -c airflow-aws.yaml` again to generate the TLS certificate

Your domain should now be pointing to the airflow deployment with secure TLS

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
