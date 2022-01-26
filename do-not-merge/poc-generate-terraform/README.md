
# POC Terraform Generator

## Goal

- Create a simple AWS stack: base, k8s-cluster, k8s-base, k8s-service
- Use Opta to generate the files (manual)
- Use Terraform to create the infra - not opta

It worked!

## Methodology

First, ran opta apply for an environment file:

```yaml
# opta.yaml
name: staging # name of the environment
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: 248233625043
modules:
  - type: base # Run 1 - only this module
  - type: k8s-cluster # Run 2 - add this module
  - type: k8s-base # Run 3 - add this module
```

Ran starting with one module, and adding one at a time.
For each opta apply, the `main.tf.json` was captured.

Then destroy everything and get it working with terraform.

Second, ran opta apply for a service file:

```yaml
# hello.yaml
name: hello
environments:
  - name: staging
    path: "opta.yaml" # the file we created in previous step
modules:
  - type: k8s-service
    name: hello
    port:
      http: 80
    # from https://github.com/run-x/opta-examples/tree/main/hello-app
    image: ghcr.io/run-x/opta-examples/hello-app:main
    healthcheck_path: "/"
    # path on the load balancer to access this service
    public_uri: "/hello"
```

For opta apply, the `main.tf.json` was captured.

Finally, destroy and provision the service with terraform.


## Examples of terraform files generated

- For a opta environment file: [stagging-env](./stagging-env)
- For a k8s service file: [hello-service](./hello-service)

## Manual changes done

### For environment terraform files

- Used local for terraform backend (instead of remote/S3) 
- Copied modules directories locally (instead of using $HOME/.opta/modules)
- Updated module source to point to local files

### For service terraform files

- Used local (instead of remote/S3) for terraform backend
- Copied modules directories locally (instead of using $HOME/.opta/modules)
- Updated module source to point to local files
- Copied `opta-k8s-service-helm` inside `aws_k8s_service` and update helm_release/chart
- Changed type of `data/terraform_remote_state/parent` to use the local tf state from the environment terraform stack
- Commented a helm condition on `namespace.yaml` to fixed this error when creating the helm release. 
    ```
    │ Error: template: k8s-service/templates/namespace.yaml:2:61: executing "k8s-service/templates/namespace.yaml" at <$existingNamespace.metadata.annotations>: nil pointer evaluating interface {}.annotations
    ```

## Learnings

- For the scope of this POC, all the infra could be deployed with terraform exclusively, no other manual operation was needed. The service was up and the LB endpoint worked.
- The only implicit dependency found was that `aws_k8s_service` requires `opta-k8s-service-helm`.
- The modules `base` and `k8s-cluster` can be provisonned together with AWS - currently we have a _halt_ between them.
- While we might require other changes for other modules, but what we have so far should be enough to cover the getting started example.
- Currently Opta apply is implemented in a way that we require some cloud credentials for TF generation to be done. `generate-terraform` would be able to work without any cloud credentials.
- Our helm deployment for a service doesn't work if the target namespace has not been created yet, it should be an easy fix.

## Remaining questions

- How hard would it be to generate the terraform files outside of opta apply, and without having any cloud credentials.
- How hard would it be to change the generated terraform files. The changes are relatively small, mostly path and changing the terraform backend.
