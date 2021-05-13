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
# Why Opta
# Quick start
# Features
# Community

Packaging
=========
- Create a new release with a new tag (0.<x>.<y>)
- This will trigger the `package` github action, which creates the binary and upload it to S3
- Update the `latest` file to point to the new release in the S3 bucket
- In the release, provide the s3 urls and also write a changelog based on the commits since the last release
- Update the docs website to point to this latest release
