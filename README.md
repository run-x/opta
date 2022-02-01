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
<img src="https://img.shields.io/badge/downloads-500%2Fweek-blue" />
  <a href="https://github.com/PyCQA/bandit">
    <img src="https://img.shields.io/badge/security-bandit-yellow.svg" alt="Security" />
  </a>
  
</p>
<p align="center">
  <a href="https://docs.opta.dev/">Documentation</a> |
<a href="https://slack.opta.dev">
    Slack Community
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
scalable, secure Infra in the cloud. Opta is used by both small and big companies. Many companies depend on it for 
their production workloads - it's battle tested :)

If you'd like to try it out or have any questions - feel free to join our [Slack](https://slack.opta.dev/) or explore the [Getting Started Guide](https://docs.opta.dev/getting-started)!


<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img width="480" src="https://user-images.githubusercontent.com/855699/149367998-9f00a9f4-abaa-4abf-949c-5b470e7d410c.png"></a>
  </br>
  <span><i>Demo Video</i></span>
  
</p>

# Features

### Cloud services
Opta supports the 3 major clouds - AWS, GCP and Azure. It has modules for the most commonly used services in these clouds like:
* Microservices (powered by [Kubernetes](https://docs.opta.dev/architecture/aws/))
* Databases - Postgres, MySQL, Redis
* Serverless workloads
* Networking - VPCs, Subnets, Load balancers
* Cloudfront
* Object storage (S3, GCS)

Additionally, we bake in best practices like:
* Observability (Datadog, LogDNA)
* [SOC2 compliance](https://docs.opta.dev/compliance/)
* [Continuous Deployment](https://docs.opta.dev/tutorials/continuous_deployment/)
* [Hardened network and security configurations](https://docs.opta.dev/architecture/aws/)
* Auto-scaling and high availability (HA)


### Coexistence with existing Infrastructure
Opta aims to be compatible with your existing Infrastructure setup. You can:

* Import existing Terraform infrastructure into Opta
* Use Opta outputs in Terraform files
* Write [custom Terraform modules](https://docs.opta.dev/reference/aws/environment_modules/custom-terraform/) (for services that Opta doesn't support yet)
* Run Opta in existing VPCs (WIP)

# Try out Opta

The best place to get started is the [Getting Started Guide](https://docs.opta.dev/getting-started/).

You can also check out some [examples](https://github.com/run-x/opta/tree/main/examples) to get a better idea of what you can do with Opta.

# Development
We love user contributions! Check out our [Dev guide](https://github.com/run-x/opta/blob/main/development.md) to get started.

# Miscellaneous
* [Team behind Opta](https://www.runx.dev/about)
* How Opta delivers upgrades (WIP)
* Bugfix / Feature request policy (WIP)
* Comparision with other tools (WIP)
* Public roadmap (WIP)
* Case studies (WIP)
