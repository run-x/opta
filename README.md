How to use
==========
- Clone the runxc repo
- `cd runxc`
- `pipenv install`
- Create your env or service yaml
    - Check out env/opta.yml and service/opta.yml for examples
- To generate main.tf.json: `pipenv run python ./opta/cli.py gen --inp <file>`
- Now you can run `terraform init && terraform apply`

Goals
=====
- Simplicity over customizability
- Try to keep the opta wrapper thin for now. Eventually we'll build plugins to
    wrap terraform cli - so you only need to remember one commmand AND plugins
    to provide a lot more syntactic sugar. But for now, when we're focussed on
    quick iteration, we should keep it simple.

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

Env creation
------------
When you're creating a new env, you should do `pipenv run python ./opta/cli.py
  gen --inp <file> --init && terraform init && terraform apply`. This will 
  create the tf bucket and store state locally.

Then you can do `pipenv run python ./opta/cli.py gen --inp <file> && terraform
init && terraform apply` to generate the full env and move everything to s3/gcs.
