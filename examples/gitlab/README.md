# What is this?

This is an example [Opta](https://github.com/run-x/opta) configuration file to deploy [Gitlab](https://docs.gitlab.com/charts/) on AWS.


# What does this do?
It deploys a horizontally scalable Gitlab deployment on EKS in AWS. It also sets up various other resources like VPCs, subnets, load balancers etc.

# Steps to deploy
* Fill in the required variables in the config file, gitlab-aws.yaml.
* Run `opta apply -c gitlab-aws.yaml` on the config file
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. Gitlab is deployed on AWS. You can find the AWS load balancer URL to access the deployment by running `opta output` (looks for the field called `load_balancer_raw_dns`).

**Note**: In addition to this, you can also attach RDS and Redis instances, as shown [here](https://docs.gitlab.com/charts/charts/globals.html) by properly integrating Secrets with the Kubernetes.

**NOTE**: DNS and SSL/TLS is currently not set up. To get them to work, follow the next section.

# Getting DNS to work
* Run `opta output -c gitlab-aws.yaml` to get the nameservers. You will see a section like this:
```text
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `gitlab-aws.yaml` file
* Run `opta apply -c gitlab-aws.yaml` again to generate the TLS certificate

Your domain should now be pointing to the Ghost deployment with secure TLS

* The admin dashboard would be available at https://gitlab.{your-domain}/
* To find the password for the root user:
```shell
$> echo $(kubectl get secrets -n gitlab gitlab-gitlab-gitlab-initial-root-password -o json | jq '.data.password')
"dummy_password_base64_encoded"
$> echo "dummy_password_base64_encoded" | base64 -D
dummy_password
```

![Login Screen](gitlab-login.png?raw=true "Login Screen")

![Gitlab Dashboard](gitlab-dashboard.png?raw=true "Gitlab Dashboard")

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
