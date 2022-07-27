# What is this?

This is an example [opta](https://github.com/run-x/opta) configuration file to deploy [Mattermost](https://mattermost.com/) (Team Edition) on AWS.


# What does this do?
It deploys a single container version of Mattermost (Team Edition) on EKS in AWS. It uses AWS managed the RDS mysql instance. It also sets up various other resources like VPCs, subnets, load balancers etc.

# Steps to deploy
* Fill in the required variables in the config file, mattermost-aws.yaml.
* Run `opta apply -c mattermost-aws.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. Mattermost is deployed on AWS. You can find the AWS load balancer URL to access the deployment by running `opta output` (looks for the field called `load_balancer_raw_dns`).

**NOTE**: DNS and SSL/TLS is currently not set up. To get them to work, follow the next section.

# Getting DNS to work
* Run `opta output -c mattermost-aws.yaml` to get the nameservers. You will see a section like this:
```yaml
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `mattermost-aws.yaml` file
* Run `opta apply -c mattermost-aws.yaml` again to generate the TLS certificate

Your domain should now be pointing to the Mattermost deployment with secure TLS

**NOTE**: The root admin is the first person who signs up, so do not delay.

![Alt text](end_result.png?raw=true "What it should look like")

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
