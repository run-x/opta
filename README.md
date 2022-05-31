<p align="center"><img src="https://user-images.githubusercontent.com/855699/125824286-149ea52e-ef45-4f41-9579-8dba9bca38ac.png" width="250"><br/>
Automated, secure, scalable cloud infrastructure</p>

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
Opta is a new kind of Infrastructure-as-Code (IaC) framework that lets engineers work with high-level constructs
instead of getting lost in low-level cloud configuration. Opta has a vast library of modules (like EKS, RDS, DynamoDB,
GKE, Cloud SQL, and even third-party services like Datadog) that engineers can compose together to build their ideal
infrastructure stack. It's built on top of Terraform, and designed so engineers aren’t locked in – anyone can write custom Terraform 
or even take the Opta-generated Terraform and work independently.

Opta gives any engineering team, whether it’s a team of 2 or 200, the same infrastructure advantages that companies
like Google or Facebook have, without having to invest in infrastructure or DevOps engineers.

### Why use Opta?
Infrastructure-as-Code (IaC) solutions are now widely accepted as the standard for provisioning and managing cloud 
infrastructure, and Terraform is widely considered to be the best IaC platform on the market – and it is – but Terraform
is also quite complex and requires deep Cloud/infrastructure expertise. We developed Opta to help eliminate this complexity.
Opta is a simpler IaC framework with best practices built-in. It lets users set up automated, scalable and secure infrastructure
on any cloud, without having to be an infrastructure expert, or getting lost in the minutiae of cloud configuration.

We are confident it can drastically reduce the complexity and headaches that come with DevOps and infrastructure at most 
fast moving organizations. Opta is currently being used by dozens of companies of all sizes.

To read more about the vision behind Opta, check out this [blog post](https://blog.runx.dev/infrastructure-as-code-for-everyone-7dad6b813cbc).

If you'd like to try it out or have any questions - feel free to join our [Slack](https://slack.opta.dev/) or explore the [Getting Started Guide](https://docs.opta.dev/getting-started)!


<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img width="480" src="https://user-images.githubusercontent.com/855699/149367998-9f00a9f4-abaa-4abf-949c-5b470e7d410c.png"></a>
  </br>
  <span><i>Deploying a Ruby on Rails application to AWS</i></span>
  
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

Additionally, Opta has cloud and security best practices built in, including:
* [Observability](https://docs.opta.dev/features/observability/) (Datadog, LogDNA)
* [SOC2 compliance](https://docs.opta.dev/compliance/)
* [Continuous Deployment](https://docs.opta.dev/features/continuous_deployment/)
* Hardened network and security configurations ([AWS](https://docs.opta.dev/architecture/aws/), [GCP](https://docs.opta.dev/architecture/gcp/), [Azure](https://docs.opta.dev/architecture/azure))
* Auto-scaling and high availability (HA)


### Coexistence with existing infrastructure
Opta aims to be compatible with your existing infrastructure setup. You can:

* Import existing Terraform infrastructure into Opta
* Write [custom Terraform modules](https://docs.opta.dev/reference/aws/modules/custom-terraform/) (for services that Opta doesn't support yet)
* Run Opta in existing VPCs (WIP)
* Export the generated Terraform

# Try out Opta

Check out the [Getting Started Guide](https://docs.opta.dev/getting-started/).

You can also explore some [examples](https://github.com/run-x/opta/tree/main/examples) to get a better idea of what you can do with Opta.

# Development
We love user contributions! Check out our [Contributing](https://github.com/run-x/opta/blob/main/CONTRIBUTING.md) and [Dev guide](https://github.com/run-x/opta/blob/main/development.md) to get started.

# Important Resources
* [The Opta Team](https://www.runx.dev/about)
* [Check Out The Blog](https://blog.runx.dev/)
* [How Opta delivers upgrades](https://github.com/run-x/opta/blob/main/UPGRADING.md)
* [Bugfix / Feature request policy](https://github.com/run-x/opta/blob/main/CONTRIBUTING.md#bugfix-resolution-time-expectations)
* Comparison with other tools (WIP)
* [Our Public roadmap](https://github.com/orgs/run-x/projects/1/views/1)
* Case studies - [Flyte](https://blog.flyte.org/how-opta-makes-deploying-flyte-much-easier), [Fastbreak Labs](https://blog.runx.dev/how-fast-break-labs-uses-opta-to-bring-basketball-to-the-blockchain-7556353d70ee), [Canvas app](https://blog.runx.dev/how-the-canvas-team-uses-opta-to-make-data-easier-to-explore-f5615647cc43)
