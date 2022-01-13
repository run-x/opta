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
Opta is an Infrastructure-As-Code framework where you work with high-level constructs
instead of getting lost in low level cloud configuration. Opta gives you a vast library of modules that you
can connect together to build your ideal Infrastructure stack. Best of all, Opta uses Terraform under the 
hood - so you're never locked in. You can always write custom Terraform or even take the Opta generated Terraform
and go your own way!

### Who is it for?
Opta is designed for folks who are not Infrastructure or Devops experts but still want to build amazing,
scalable, secure Infra in the cloud. Opta is used by small and big companies both. Many companies depend on it for 
their production workloads - it's battle tested :)

If you'd like to try it out or have any questions - feel free to join our [Slack](https://slack.opta.dev/)!


<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img width="480" src="https://user-images.githubusercontent.com/855699/149367998-9f00a9f4-abaa-4abf-949c-5b470e7d410c.png"></a>
  </br>
  <span><i>Demo Video</i></span>
  
</p>

# Try out Opta


To use Opta, you first need to create some simple yaml configuration files that describe your needs. You can use:

* Our [magical GUI](https://app.runx.dev/yaml-generator) to help generate these files.

* The [getting started](https://docs.opta.dev/getting-started/) guide and the detailed docs.

* Also, check out more [examples](https://github.com/run-x/opta/tree/main/examples)

# What you get with Opta
* Production ready [Architecture](https://docs.opta.dev/architecture/aws/)
* **SOC2** compliant infrastructure
* Continuous Deployment for containerized workloads
* Hardened network and security configurations
* Support for multiple environments (like Dev/QA/Staging/Prod)
* Integrations with observability tools (like Datadog/LogDNA/Prometheus/SumoLogic)
* Support for non-kubernetes resources like RDS, Cloud SQL, DocumentDB etc
* Built-in auto-scaling and high availability (HA)
* Support for spot instances

# Development
[Dev guide](https://github.com/run-x/opta/blob/main/development.md)
