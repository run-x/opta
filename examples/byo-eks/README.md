# Bring Your Own Cluster

This is an example of using [Opta](https://github.com/run-x/opta) with an existing EKS cluster.

# What does this do?

If you already have an EKS cluster, and would like to try out Opta, follow these instructions to configure your cluster to work with Opta.

If you don't have an EKS cluster, Opta can also create it, check [Getting Started](https://docs.opta.dev/getting-started/) instead.

# What is included?

By running terraform on an existing EKS cluster, your cluster will be configured to have the target [Network Architecture](https://docs.opta.dev/features/networking/network_overview/).

The following components will be installed:

- [Ingress Nginx](https://github.com/kubernetes/ingress-nginx) to expose services to the public
- [Linkerd](https://linkerd.io/) as the service mesh.
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) to manage the ELB for the Kubernetes cluster.

Here is the break down of the terraform files:

    .
    └── terraform
        ├──aws-lb-iam-policy.json            # The IAM policy for the load balancer
        └──aws-load-balancer-controller.tf   # Create IAM role and install the AWS Load Balancer Controller
        └──data.tf                           # Data fetched from providers
        └──ingress-nginx.tf                  # Install the Nginx Ingres Controller
        └──linkerd.tf                        # Install Linkerd
        └──outputs.tf                        # Terraform outputs
        └──providers.tf                      # Terraform providers
        └──variables.tf                      # Terraform variables

# Requirements

To configure the cluster (this guide), you need to use an AWS user with permissions to create AWS policies and roles, and admin permission on the target EKS cluster.

# Configure the cluster for Opta

This step configures the networking stack (nginx/linkerd/load balancer) on an existing EKS cluster.

- Init terraform
```shell
cd ./terraform
terraform init
```

- [Optional] Configure a Terraform backend. By default, Terraform stores the state as a local file on disk. If you want to use a different backend such as S3, add this file locally.
```terraform
# ./terraform/backend.tf
terraform {
  backend "s3" {
    bucket = "mybucket"
    key    = "path/to/my/key"
    region = "us-east-1"
  }
}
```
Check this [page](https://www.terraform.io/language/settings/backends) for more information or other backends.

- Run terraformm plan
```
terraform plan -var kubeconfig=~/.kube/config -var cluster_name=my-cluster -var oidc_provider_url=https://oidc.eks.... -out=tf.plan

Plan: XX to add, 0 to change, 0 to destroy.
```

For the target EKS cluster:
- For `cluster_name`, run `aws eks list-clusters` to see the availables clusters.
- For `oidc_provider_url`, see `OpenID Connect provider URL` in the EKS cluster page in the AWS console. For more information, check the [official documentation](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html)
- For `kubeconfig`, check the [official documentation](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html) if you don't have one yet.


At this time, nothing was changed yet, you can review what will be created by terraform.

- Run terraformm apply
```
terraform apply tf.plan

Apply complete! Resources: XX added, 0 changed, 0 destroyed.

Outputs:

load_balancer_raw_dns = "xxx"

```

Note the load balancer DNS, this is the public endpoint to access your Kubernetes cluster.

# Additional cluster configuration

These steps are not automated with the terraform step, but you can configure them using these guides.
- Configure DNS
    - Follow this guide: [Routing traffic to an ELB load balancer](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-elb-load-balancer.html)
    - Using the TODO..
- Configure a public certificate:
    - Follow this guide: [Requesting a public certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html)
    - Using the certificate ARN, run the terraform commands with `-var load_balancer_cert_arn=...` 

# Deploy Kubernetes services with Opta

Coming soon.

# Uninstallation

- Run terraformm destroy to remove the configuration added for Opta

```
terraform destroy -var kubeconfig=~/.kube/config -var cluster_name=my-cluster -var oidc_provider_url=https://oidc.eks....
```

