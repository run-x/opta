Development
==========
- Create db:
  - `brew install postgresql`
  - `psql postgres` and then run in psql console
    - `create role app login createdb;`
    - `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;`
    - `create database app;`

- Setup env:
  - Set up python properly via https://opensource.com/article/19/5/python-3-default-mac#what-to-do
  - `pipenv install --dev`
  - `pipenv shell`

- Run migrations:
  - `cd srv`
  - `flask db migrate`
  - `flask db upgrade`

- Run locally:
  - `cd srv`
  - `FLASK_ENV=development flask run`
  - You might need to set PYTHONPATH to the root dir

WIP BELOW

- Run tests: `coverage run`
- Get coverage report: `coverage report`
- Access production db:
  - List pods `kubectl get pods`
  - Ssh into the prod one `kubectl exec -it <pod-name> -- bash`
  - Open python shell `pipenv run python`
  - Get db creds `from srv.var import get_db_uri; get_db_uri()`
  - Install psql `apt-get update && apt-get install postgresql`
  - Connect to db `psql -h <hostname> -U postgres main`

- Install pre-commit hook for linting:
  - `cp scripts/pre-commit .git/hooks/pre-commit`

Deployment
==========
- Install gcloud
- Authenticate
  - `gcloud auth login`
  - `gcloud config set project catalog-289423`
  - `gcloud container clusters get-credentials prod-main --zone us-central1-c`
  - `gcloud auth configure-docker`
- Build Image
  - `make build-backend`
- Update deployment
  - `IMAGE_VERSION=<version> make deploy-backend`
- Update service (NOTE: this will probably change the loadbalancer IP - current IP: 35.225.143.103)
  - `kubectl apply -f srv/k8s/service.yaml`
