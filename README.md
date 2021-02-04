[![codecov](https://codecov.io/gh/run-x/runxc/branch/main/graph/badge.svg?token=OA3PXV0HYX)](https://codecov.io/gh/run-x/runxc)

How to use (out of date)
==========
- Clone the runxc repo
- `cd runxc`
- `pipenv install`
- Create your env or service yaml
    - Check out env/opta.yml and service/opta.yml for examples
- Now you can run: `pipenv run python ./opta/cli.py apply --inp <file>`

Packaging
=========
- Trigger a new action here and supply a new version number (0.<n>): https://github.com/run-x/runxc/actions?query=workflow%3APackage
- For now version numbers are 0.<n> where n goes up with each release
- This action will build both a macos and linux binary
- Upload the binaries to this s3 bucket with appropriate names (/platform/0.<n>/opta): https://s3.console.aws.amazon.com/s3/buckets/dev-runx-opta-binaries It's in the "runx" aws account. Make sure to mark both binaries public and note down their url.
- Create a new release on github for the sha that the action was run with and set tag=v0.<n>
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
