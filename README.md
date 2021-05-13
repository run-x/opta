<h1 align="center">Opta</h1>
<p align="center">Run your containerized workloads on any cloud, without devops.</p>

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
  
</p>
<p align="center">
  <a href="https://docs.runx.dev/docs">Documentation</a> |
<a href="https://discord.gg/AyEpG2vY">
    Discord Community
  </a>
  </p>

# Introduction
Opta is a platform for running containerized workloads on the cloud. It
abstracts away the complexity of networking, IAM, kubernetes, and various other
components - giving you a clean cloud agnostic interface to deploy and run your
containers.
It's all configuration driven so you always get a repeatable copy of your
infrastructure.
# Why Opta
* No devops expertise required
* Multi Cloud (AWS, GCP, Azure)
* Progressively configurable
* No lock in
* Complete security
# Quick start
Install: 

`/bin/bash -c "$(curl -fsSL https://docs.runx.dev/install.sh)"`

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
# [WIP] Features
# [WIP] Community
# [WIP] Development
