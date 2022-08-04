# httpbin example

This example shows how to deploy an [httpbin](https://httpbin.org/)
service using [Opta](https://github.com/run-x/opta).


This directory contains:

    .
    ├── env-aws.yaml      # opta environment file for AWS
    ├── env-azure.yaml    # opta environment file for Azure
    ├── env-gcp.yaml      # opta environment file for GCP
    ├── env-local.yaml    # opta environment file for local
    └── httpbin.yaml      # opta service file

## Deploy to local Kubernetes using Opta

1. Create the local kubernetes cluster
    ```bash
    opta apply --local --auto-approve -c env-local.yaml
    ```
1. Apply the service
    ```bash
    opta apply --config httpbin.yaml --auto-approve --env local
    ```
1. Test
    ```bash
    curl http://localhost:8080/
    ```
1. Clean up
    ```bash
    opta destroy --auto-approve --local --config hello.yaml
    opta destroy --auto-approve --local --config env-local.yaml
    ```
   
**NOTE**: We are using `opta apply` as `opta deploy` is only needed when the image is set to AUTO

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
3. Deploy the service: push the image and deploy it to Kubernetes
    ```bash
    opta apply --config httpbin.yaml --auto-approve --env $ENV
    ```
4. Test
    ```bash
    curl http://${load_balancer}

    # you can run any kubectl command at this point
    kubectl -n httpbin get all
    ```
5. Clean up
    ```bash
    opta destroy --auto-approve --config httpbin.yaml --env $ENV
    opta destroy --auto-approve --config env-${ENV}.yaml
    ```

# References
* [Opta docs](https://docs.opta.dev)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
