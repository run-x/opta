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

<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img src="https://img.youtube.com/vi/nja_EfpGexE/0.jpg"></a>
  </br>
  <span><i>Demo Video</i></span>
  
</p>

# Try out Opta


To use Opta, you first need to create some simple yaml configuration files that describe your needs. You can use 
our [magical UI](https://app.runx.dev/yaml-generator) to help generate these files or do it manually.

### Checkout our [Getting started](https://docs.opta.dev/getting-started/) guide.

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
