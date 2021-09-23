<p align="center"><img src="https://user-images.githubusercontent.com/855699/125824286-149ea52e-ef45-4f41-9579-8dba9bca38ac.png" width="250"><br/>
Supercharge DevOps on any cloud</p>

<p align="center">
  <a href="https://github.com/run-x/opta/releases/latest">
    <img src="https://img.shields.io/github/release/run-x/opta.svg" alt="Current Release" />
  </a>
  <a href="https://github.com/run-x/opta/actions/workflows/ci.yml">
    <img src="https://github.com/run-x/opta/actions/workflows/ci.yml/badge.svg" alt="Tests" />
  </a>
  <a href="https://codecov.io/gh/run-x/opta">
    <img src="https://codecov.io/gh/run-x/opta/branch/main/graph/badge.svg?token=OA3PXV0HYX">
  </a>
  <a href="http://www.apache.org/licenses/LICENSE-2.0.html">
    <img src="https://img.shields.io/badge/LICENSE-Apache2.0-ff69b4.svg" alt="License" />
  </a>

  <img src="https://img.shields.io/github/commit-activity/w/run-x/opta.svg?style=plastic" alt="Commit Activity" />

  <a href="https://github.com/PyCQA/bandit">
    <img src="https://img.shields.io/badge/security-bandit-yellow.svg" alt="Security" />
  </a>
  
</p>
<p align="center">
  <a href="https://docs.opta.dev/">Documentation</a> |
<a href="https://slack.opta.dev">
    Slack Community
  </a> | <a href="https://runx.dev/">
    Website
  </a> | <a href="mailto:info@runx.dev">
    Email: info@runx.dev
  </a>
  </p>

# What is Opta?
Opta is a new kind of Infrastructure-As-Code framework where you work with high-level constructs
instead of getting lost in low level cloud configuration. Imagine just being able to say that you want
an autoscaling docker container that talks to a RDS database - instead of figuring out the details of VPC,
IAM, Kubernetes, Elastic Load Balancing etc -- that's what Opta does!

### Who is it for?
Opta is designed for folks who are not Infrastructure or Devops experts but still want to build amazing,
scalable, secure Infra in the cloud. Majority of Opta's users are early stage startups who use it for their 
dev/staging/production environments.

If you'd like to try it out or have any questions - feel free to join our [Slack](https://slack.opta.dev/)!

[Try out Opta](#try-out-opta)

[What you get with Opta](#what-you-get-with-opta)

<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img src="https://img.youtube.com/vi/nja_EfpGexE/0.jpg"></a>
  </br>
  <span><i>Demo Video</i></span>
  
</p>

# Try out Opta


To use Opta, you first need to create some simple yaml configuration files that describe your needs. You can use 
our [magical UI](https://app.runx.dev/yaml-generator) to help generate these files or do it manually (described below).

### Four Step Quick Start (<30min)
1. Install the opta CLI

`/bin/bash -c "$(curl -fsSL https://docs.opta.dev/install.sh)"`

2. Create an environment


Before you can deploy your app, you need to first create an environment (like staging, prod etc.)
This will set up the base infrastructure (like network and cluster) that will be the foundation for your app.

> Note that it costs around 5$ per day to run this on AWS. So make sure to destroy it after you're done 
> (opta has a destroy command so it should be easy :))!

Create this file and name it staging.yml
```
name: staging
org_name: <something unique>
providers:
  aws:
    region: us-east-1
    account_id: XXXX
modules:
  - type: base
  - type: k8s-cluster
  - type: k8s-base
```

3. Create the application/service

In this example we are using the popular [httbin](https://httpbin.org/) container as our application

Create this file and name it opta.yml:
```
name: hello-world
environments:
  - name: staging
    path: "staging.yml" # Note that this is the file we created in step 2
modules:
  - name: app
    type: k8s-service
    port:
      http: 80
    image: docker.io/kennethreitz/httpbin:latest
    healthcheck_path: "/get"
```

4. Deploy

Once the files are created, just run `opta apply` and that's all! Now you have a containerized application
running on Kubernetes in a production ready Architecture (described below).

Run `opta output` and note down `load_balancer_raw_dns`. Now you can:

- Access your service at `http://<ip-or-dns>/`
- SSH into the container by running `opta shell`
- See logs by running `opta logs`

### Cleanup
Once you’re finished playing around with this example, you may clean up by running `opta destroy --config staging.yml`.

### Check out more [examples](https://github.com/run-x/opta/tree/main/examples)

# What you get with Opta
* Production ready [Architecture](https://docs.opta.dev/architecture/aws/)
* Continuous Deployment for containerized workloads
* Hardened network and security configurations
* Support for multiple environments (like Dev/QA/Staging/Prod)
* Integrations with observability tools (like Datadog/LogDNA/Prometheus/SumoLogic)
* Support for non-kubernetes resources like RDS, Cloud SQL, DocumentDB etc
* Built-in auto-scaling and high availability (HA)
* Support for spot instances

# Development
[Dev guide](https://github.com/run-x/opta/blob/main/development.md)
