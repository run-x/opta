# What is this?

This is an example [Opta](https://github.com/run-x/opta) configuration file to deploy [Ghost](https://github.com/TryGhost/Ghost) on AWS.

# What does this do?
It deploys a horizontally scalable Ghost deployment on EKS in AWS. It uses AWS managed for the RDS mysql instance. It also sets up various other resources like VPCs, subnets, load balancers etc.

# Steps to deploy
* Fill in the required variables in the config file, ghost-aws.yaml.
* Run `opta apply -c ghost-aws.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. Ghost is deployed on AWS. You can find the AWS load balancer URL to access the deployment by running `opta output` (looks for the field called `load_balancer_raw_dns`).

**NOTE**: DNS and SSL/TLS is currently not set up. To get them to work, follow the next section.

# Getting DNS to work
* Run `opta output -c ghost-aws.yaml` to get the nameservers. You will see a section like this:
```yaml
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `ghost-aws.yaml` file
* Run `opta apply -c ghost-aws.yaml` again to generate the TLS certificate

Your domain should now be pointing to the Ghost deployment with secure TLS

* The admin dashboard would be available at https://{your-domain}/dashboard/ghost


![Alt text](ghost-dashboard.png?raw=true "What it should look like")

# Getting emails feature to work
* Fill in the `mail__options__service` and `mail__options__auth__user` field in the yaml
* Use the opta secret command to provide the auth password for the email as a secret
```bash
opta secret update -c ghost-aws.yaml mail__options__auth__pass MY_SECRET_EMAIL_PASSWORD
```

That's it, now your ghost app can also send emails from your email


# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
