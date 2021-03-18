[![codecov](https://codecov.io/gh/run-x/runxc/branch/main/graph/badge.svg?token=OA3PXV0HYX)](https://codecov.io/gh/run-x/runxc)

Development
==========
Scripts
----------
- Install pre-commit hook for linting:
  - `cp scripts/pre-commit .git/hooks/pre-commit`

Packaging
=========
- Create a new release with a new tag (0.<x>.<y>)
- This will trigger the `package` github action, which creates the binary and upload it to S3
- Update the `latest` file to point to the new release in the S3 bucket
- In the release, provide the s3 urls and also write a changelog based on the commits since the last release
- Update the docs website to point to this latest release

Concepts
========

Linking
-------
If you use `_link` in a resource, it will map to the outputs of the target
module

Env outputs
-----------
If a module has an input variable with the same name as an env output, it'll
  automatically be connected to the env value

Terminology
-----------
*Module* - A module is a reusable piece of infrastructure currently described as a terraform module

*Block* - A block is a group of modules to be deployed in parallel, depending only on previous blocks

*Layer* - A layer is a set of blocks managed by the same IAM permissions/team (i.e. 1 opta yaml)
