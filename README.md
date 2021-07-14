<h1 align="center">Opta</h1>
<p align="center">Supercharge DevOps on any cloud</p>

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
<a href="https://join.slack.com/t/opta-group/shared_invite/zt-r1p9k1iv-4MP1IMZCT9mwwwdJH0HRyA">
    Slack Community
  </a> | <a href="https://runx.dev/">
    Website
  </a> | <a href="mailto:info@runx.dev">
    Email: info@runx.dev
  </a>
  </p>

# Introduction
Opta is a platform for running containerized workloads on the cloud. It
abstracts away the complexity of networking, IAM, kubernetes, and various other
components - giving you a clean cloud agnostic interface to deploy and run your
containers.
It's all configuration driven so you always get a repeatable copy of your
infrastructure.


<p align="center">
  <a href="https://www.youtube.com/watch?v=nja_EfpGexE"><img src="https://img.youtube.com/vi/nja_EfpGexE/0.jpg"></a>
  </br>
  <span><i>Demo Video</i></span>
  
</p>


# Why Opta
Over the last 10 years, our team has built and led DevOps teams at world-class 
companies like Lyft, Twitter, Facebook and Flexport. We have always believed 
that Devops is a force multiplier - a well built infrastructure can empower the 
engineers and greatly accelerate product delivery. Opta was borne out of these 
experiences. 

Opta's goal is to provide a robust production-ready platform for every organization
and introduce radical automation to DevOps.

# Features
* Continuous Deployment for containerized workloads
* Hardened network and security configurations
* Support for multiple environments (like Dev/QA/Staging/Prod)
* Integrations with observability tools (like Datadog/LogDNA/Prometheus/SumoLogic)
* Support for non-kubernetes resources like RDS, Cloud SQL, DocumentDB etc
* Built-in auto-scaling and high availability (HA)
* Support for spot instances


# Quick start
Install: 

`/bin/bash -c "$(curl -fsSL https://docs.opta.dev/install.sh)"`

Create environment:
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
Create service:
```
name: hello-world
environments:
  - name: staging
    path: "staging/opta.yml"
modules:
  - name: app
    type: k8s-service
    port:
      http: 80
    image: docker.io/kennethreitz/httpbin:latest
    healthcheck_path: "/get"
```
Deploy: 

`opta apply`

### Check out more [examples](https://github.com/run-x/opta/tree/main/examples)

# Community Users
* https://github.com/flyteorg/flyte
* https://canvasapp.com/
* https://biocogniv.com/
* ... And many more! Join us in <a href="https://join.slack.com/t/opta-group/shared_invite/zt-r1p9k1iv-4MP1IMZCT9mwwwdJH0HRyA">Slack</a>.

# Development
[Dev guide](https://github.com/run-x/opta/blob/main/development.md)
