# What is this?

This is an example [Opta](https://github.com/run-x/opta) configuration file to deploy [NocoDB](https://github.com/nocodb/nocodb) on AWS.


# What does this do?
It deploys a horizontally scalable NocoDB deployment on EKS in AWS. It uses AWS managed the RDS mysql instance. It also sets up various other resources like VPCs, subnets, load balancers etc.

# Steps to deploy
* Fill in the required variables in the config file, nocodb-aws.yaml.
* Run `opta apply -c nocodb-aws.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. NocoDB is deployed on AWS. You can find the AWS load balancer URL to access the deployment by running `opta output` (looks for the field called `load_balancer_raw_dns`).

**NOTE**: DNS and SSL/TLS is currently not set up. To get them to work, follow the next section.

# Getting DNS to work
* Run `opta output -c nocodb-aws.yaml` to get the nameservers. You will see a section like this:
```yaml
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `nocodb-aws.yaml` file
* Run `opta apply -c nocodb-aws.yaml` again to generate the TLS certificate

Your domain should now be pointing to the NocoDB deployment with secure TLS

* Go to https://{your-domain} and login as admin and start working.


![Alt text](nocodb-login.png?raw=true "Login Page")
![Alt text](add-projects.png?raw=true "Add Projects/External DBs")
![Alt text](external-db.png?raw=true "External DB addition and test")

# Working with CloudFront
If you are ready to start hosting your site with your domain via the cloudfront distribution, then proceed as follows:
* Get an [AWS ACM certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html) for your site.
* Set the acm_cert_arn and domains fields in opta accordingly
* Run `opta apply -c nocodb-aws.yaml` and viola.

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
