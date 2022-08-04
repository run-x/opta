# Hello Application example

This example shows how to build and deploy a containerized python web server
application using [Opta](https://github.com/run-x/opta).


This directory contains:

    .
    ├── app.py            # HTTP server implementation. It responds to all HTTP requests with a  "Hello, World!" response.
    ├── Dockerfile        # build the Docker image for the application
    ├── env-aws.yaml      # opta environment file for AWS
    ├── env-azure.yaml    # opta environment file for Azure
    ├── env-gcp.yaml      # opta environment file for GCP
    ├── env-local.yaml    # opta environment file for local
    └── hello.yaml        # opta service file

## Build and run locally


1. Build the image
    ```bash
    docker build . -t hello-app:v1
    ```
1. Run the hello app
    ```bash
    docker run -p 80:80 hello-app:v1
    # or use a different port
    docker run -p 8080:8080 -e PORT=8080 hello-app:v1
    ```
1. Test
    ```bash
    curl http://localhost:80/hello
    ```

## Deploy to local Kubernetes using Opta

1. Create the local kubernetes cluster
    ```bash
    opta apply --local --auto-approve -c env-local.yaml
    ```
1. Deploy the service
    ```bash
    opta deploy --image hello-app:v1 --config hello.yaml --auto-approve --env local
    ```
1. Test
    ```bash
    curl http://localhost:8080/hello
    ```
1. Clean up
    ```bash
    opta destroy --auto-approve --local --config hello.yaml
    opta destroy --auto-approve --local --config env-local.yaml
    ```

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
    opta deploy --image hello-app:v1 --config hello.yaml --auto-approve --env $ENV
    ```
4. Test
    ```bash
    curl http://${load_balancer}/hello

    # you can run any kubectl command at this point
    kubectl -n hello get all
    ```
5. Clean up
    ```bash
    opta destroy --auto-approve --config hello.yaml --env $ENV
    opta destroy --auto-approve --config env-${ENV}.yaml
    ```

# References
* [Opta docs](https://docs.opta.dev)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
