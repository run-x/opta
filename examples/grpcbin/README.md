# grpcbin example

This example shows how to deploy an [grpcbin](https://github.com/moul/grpcbin)
service using [Opta](https://github.com/run-x/opta).


This directory contains:

    .
    ├── env-aws.yaml      # opta environment file for AWS
    ├── env-azure.yaml    # opta environment file for Azure
    ├── env-gcp.yaml      # opta environment file for GCP
    └── grpcbin.yaml      # opta service file

**NOTE**: Typically, the first step of the example would be to demonstrate how one may deploy the application locally
but currently GRPC with opta does not function locally, and requires [TLS set up](https://docs.opta.dev/tutorials/ingress/#setting-the-domain-for-an-environment-via-domain-delegation)
in the cloud environments to function. If you have pressing need for this feature, please let us know in our
[slack channel](https://slack.opta.dev)

## Deploy to a cloud provider using Opta

1. Select the target environment
    ```bash
    # pick one
    export ENV=[aws/azure/gcp]

    # edit the env file to specify where to deploy (Account information)
    open env-${ENV}.yaml 
    ```
2. Create the environment infrastructure (VPC, Kubernetes...)
    ```bash
    opta apply --auto-approve -c env-${ENV}.yaml
    # when done, find load_balancer_raw_dns or load_balancer_raw_ip in the output and save it
    export load_balancer=[Value from output]
    ```
3. Complete the [TLS and domain set up](https://docs.opta.dev/tutorials/ingress/#setting-the-domain-for-an-environment-via-domain-delegation)
4. Deploy the service: push the image and deploy it to Kubernetes
    ```bash
    opta apply --config grpcbin.yaml --auto-approve --env $ENV
    ```
5. Test
    ```bash
    curl http://${load_balancer}/hello

    # you can run any kubectl command at this point
    kubectl -n grpcbin get all
    ```
6. Clean up
    ```bash
    opta destroy --auto-approve --config grpcbin.yaml --env $ENV
    opta destroy --auto-approve --config env-${ENV}.yaml
    ```   

**NOTE**: We are using `opta apply` as `opta deploy` is only needed when the image is set to AUTO

# References
* [Opta docs](https://docs.opta.dev)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
