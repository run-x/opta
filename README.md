<p align="center"><img src="https://user-images.githubusercontent.com/4830700/152586743-fe398a3d-641d-4283-8c9e-e2189e5f451d.png"><img src="https://user-images.githubusercontent.com/855699/125824286-149ea52e-ef45-4f41-9579-8dba9bca38ac.png" width="250"><br/>
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

# What is Opta
Opta is an Infrastructure-As-Code framework where you work with high-level constructs
instead of getting lost in low level cloud configuration. Opta gives you a vast library of modules that you
can connect together to build your ideal Infrastructure stack. Best of all, Opta uses Terraform under the 
hood - so you're never locked in. You can always write custom Terraform or even take the Opta generated Terraform
and go your own way!

### Why use Opta
Infrastructure as code (IaC) has rapidly become the standard for provisioning and managing Infrastructure and for the right reasons! 
But the leading IaC tools are still complicated to use and require deep Cloud/Infrastructure expertise. Opta was conceptualized to help address
this complexity. Opta is a simpler IaC framework with best practices built-in. It enables users to set up automated, scalable and secure infrastructure
without being a cloud expert or spending days figuring out cloud minutiae!

We are confident it can drastically reduce the cloud complexity and devops headaches of most fast moving organizations. It is already being used by companies - big and small :)

To read more about the vision behind Opta, check out this [blog post](https://blog.runx.dev/infrastructure-as-code-for-everyone-7dad6b813cbc).

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
* CDN (Content Delivery Network)
* Object storage (S3, GCS)

Additionally, we bake in best practices like:
* [Observability](https://docs.opta.dev/observability/) (Datadog, LogDNA)
* [SOC2 compliance](https://docs.opta.dev/compliance/)
* [Continuous Deployment](https://docs.opta.dev/tutorials/continuous_deployment/)
* Hardened network and security configurations ([AWS](https://docs.opta.dev/architecture/aws/), [GCP](https://docs.opta.dev/architecture/gcp/), [Azure](https://docs.opta.dev/architecture/azure))
* Auto-scaling and high availability (HA)


### Coexistence with existing Infrastructure
Opta aims to be compatible with your existing Infrastructure setup. You can:

* Import existing Terraform infrastructure into Opta
* Write [custom Terraform modules](https://docs.opta.dev/reference/aws/environment_modules/custom-terraform/) (for services that Opta doesn't support yet)
* Run Opta in existing VPCs (WIP)
* Export the generated Terraform (WIP)

# Try out Opta

Check out the [Getting Started Guide](https://docs.opta.dev/getting-started/).

You can also explore some [examples](https://github.com/run-x/opta/tree/main/examples) to get a better idea of what you can do with Opta.

# Development
We love user contributions! Check out our [Dev guide](https://github.com/run-x/opta/blob/main/development.md) to get started.

# Miscellaneous
* [Team behind Opta](https://www.runx.dev/about)
* How Opta delivers upgrades (WIP)
* Bugfix / Feature request policy (WIP)
* Comparison with other tools (WIP)
* Public roadmap (WIP)
* Case studies - [Flyte](https://blog.flyte.org/how-opta-makes-deploying-flyte-much-easier) (More on the way!)
