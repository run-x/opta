# Python Django Rest Framework Todo API

The Python Django Todo API implements a RESTFul HTTP API for a to-do list. It is derived from [this tutorial](https://learndjango.com/tutorials/django-rest-framework-tutorial-todo-api).

In the discussion below we assume you will be choosing Microk8s for installing Kubernetes on your local PC or a virtual machine.

## Notable Code

This is a table of notable links to the Django API code in this directory as well as external links in case you wish to learn about these topics.
| Category | File or Directory  | Description | Notes and External Links |
|---|---|---|---|
| Django | [apis/](apis/) |  Django REST framework application written in Python  |  Learn more about [Django](https://www.djangoproject.com/) and the [Django Rest Framework](https://www.django-rest-framework.org/)|
| Docker | [Dockerfile](Dockerfile)  | Docker file to create docker image.   | Get started with [Docker](https://docs.docker.com/get-started/) |
| Django | [apis/todo/models.py](apis/todo/models.py) | Object relational model (ORM)  for the to-do list API | All about Django ORM [models](https://docs.djangoproject.com/en/3.1/topics/db/models/) |
| Kubernetes | [kubecode/bigbitbus-dj-py-api/](kubecode/bigbitbus-dj-py-api/) | A custom Helm chart to deploy application into a Kubernetes cluster | [Helm](https://helm.sh/docs/topics/charts/), a software packaging system for Kubernetes |
| Kubernetes| [kubecode/bigbitbus-dj-py-api/values.yaml](kubecode/bigbitbus-dj-py-api/values.yaml) | The values file is a method to set parameters in the todo-api application Helm chart | More about Helm [values](https://helm.sh/docs/chart_template_guide/values_files/) |
| Skaffold | [skaffold.yml](skaffold.yml) | This Skaffold file contains instructions on how to deploy the application into Kubernetes | [Skaffold](https://skaffold.dev/) handles the workflow for building, pushing and deploying your application |


## Installation

We assume you have access to a reasonably capable local computer (at least 4 processor cores, 8GB RAM and 50GB of free disk space) with a broadband internet connection capable of downloading multiple gigabytes of data (mostly for Docker images).


**Note: If running on a Windows machine: Use a text editor (ex. VSCode) to change the EOL sequence of the start.sh file from CRLF to LF.**

### Development on your Local PC

Developers may want to iterate through their code as they develop software on their local PC. We will run the to-do Django code on our PC for debugging and connect to a postgres database running on a container. If you use Windows OS or don't have root access on your PC you can consider performing the below steps  inside a Linux virtual machine on your PC.

### Pre-requisite Software

1. [Install Docker](https://docs.docker.com/get-docker/) and [Docker-compose](https://docs.docker.com/compose/install/) on your computer.
2. [Install Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/), the Kubernetes command line interface client, on your computer.
3. [Install Helm](https://helm.sh/docs/intro/install/) package manager client on your computer (version 3 or greater).
4. [Install Skaffold](https://skaffold.dev/docs/install/) on your computer.



Open a terminal and create a virtual environment for Python (Assuming you have already installed Python 3.8 or later on your PC):

```
python3 -m venv .venv
```

Activate this environment
```
source .venv/bin/activate

# If on Windows
.venv\Scripts\activate.bat
```

Install the Python requirements:

```
pip install -r requirements.txt
```

Tell the Django application about the postgres container through environment variables . Export these environment variables on your local PC.

```
export POSTGRES_PORT=5432
export POSTGRES_PASSWORD=B1gB1tBu5
export POSTGRES_DB=todo-postgres-database
export POSTGRES_USER=postgres
export POSTGRES_HOST=localhost

# If on Windows
SET POSTGRES_PORT=5432
SET POSTGRES_PASSWORD=B1gB1tBu5
SET POSTGRES_DB=todo-postgres-database
SET POSTGRES_USER=postgres
SET POSTGRES_HOST=localhost
```

Create the Postgres docker container.

```
docker-compose up -d postgresdb
```

Run the Django API server

```
python manage.py collectstatic
python manage.py migrate
python manage.py runserver 0.0.0.0:8002

```

The API will now be available at `http://localhost:8002/djangoapi/apis/v1/`

Now you can develop the application and Django will "hot-reload" as you change code; this saves a lot of developer time because you do not have to re-build the image to test it every time.

### Run pre-baked image on your Local PC with Docker-compose

Once we are satisfied that the application has been developed to our satisfaction we should test its pre-baked image locally. The pre-baked immutable image is what gets passed from development to qa and finally to production without being changed, so it is quite useful to be able to quickly spin up the pre-baked image on our local PC via docker-compose and test everything works before deploying it to QA and production.

We can use `docker-compose` to run the todo API and the Postgres database on our local PC, like so:

```
# Open a terminal and run these commands
docker-compose build # Build the Docker image with the latest code in this repository
docker-compose up

```
Now you can open a web browser and point it to `http://localhost:8000/djangoapi/apis/v1/` to browse and interact with the todo API backend.

Note we selected port 8000 for this case (not 8002) so you can have both the development and the pre-baked software running in the image on the same machine (albeit interacting with the same database). Make a note that when you try to point the Todo [frontend](../../frontend/todo-vuejs) you will need to set the correct backend server and port in the [.env](../../frontend/todo-vuejs/.env) file there for the `VUE_APP_DJANGO_ENDPOINT` variable.

### Run in Kubernetes

Finally, we are ready to deploy to Kubernetes!

This discussion assumes that you have a your `kubectl` command-line client configured and pointing to the correct Kubernetes cluster.

Verify that kubectl is correctly configured: for Microk8s running this command should give you an output similar to this

```
kubectl get no
NAME                 STATUS   ROLES    AGE   VERSION
<YOUR PC NAME>   Ready    <none>   58d   v1.19.3-34+a56971609ff35a

```

If this doesn't work, debug the local Kubernetes cluster installation befre proceeding based on your Kubernetes installation documentation.

#### Addons for local Kubernetes (Microk8s)

We need to enable some additional add-ons for our local Kubernetes installation. Run these commands.

```
# For Microk8s enable these addons
microk8s.enable rbac
microk8s.enable dns
microk8s.enable storage
microk8s.enable registry
microk8s.enable ingress
```
#### Postgres Database

Create the postgres database via a standard Helm chart; run the following commands in a terminal window.

```
kubectl create namespace pg
cd kubernetes-automation-toolkit/code/k8s-common-code/postgres-db/ # relative to the root directory of this git repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# For microk8s
helm install -n pg pgdb bitnami/postgresql -f pg-values.yaml
```
Useful tip: To recreate the PG database, make sure you delete both the helm installation and the persistent volume claim, like below, otherwise the data will persist into the new helm installation of the postgres database.

```
helm delete -n pg pgdb
kubectl -n pg delete pvc data-pgdb-postgresql-0

```

#### Backend todo API

Then, install the to-do API
```
# Backend
kubectl create namespace be
cd kubernetes-automation-toolkit/code/app-code/api/todo-python-django/

# For microk8s
skaffold run --default-repo localhost:32000
```

You can always make code changes to the frontend and then run the skaffold `run` command again to deploy the changes into the Kubernetes cluster. Learn more about other [skaffold developer and operations workflows](https://skaffold.dev/docs/workflows/).


We have just used Skaffold to deploy the Helm chart of our to-do API into the Kubernetes cluster.

**Side note:** If you are looking to create a Helm chart for your own project we recommend starting from the boiler-plate code generated by [`helm create`](https://helm.sh/docs/helm/helm_create/). This command will create a basic layout that you can then adapt to your application.
## Usage

Once the the backend is installed, we can use the ingress to access the application; ingress routes HTTP traffic to the appropriate services in the Kubernetes cluster (our to-do application in this case).

Point your browser at http://host:[port]/djangoapi/apis/v1/ and check if you can browse the API and add/remove/list items etc.

Now you can point your web browser to `http://localhost/djangoapi/api/v1/` to browse the API.

## Pitfalls, Common Mistakes
TBD

## Clean-up

You can "delete" any Helm chart from the cluster:

```
# Get a list of installed helm charts in all namespaces
helm ls --all-namespaces

# Delete the backend todo API
helm delete be --namespace be



# Delete the Postgres database
helm delete pgdb --namespace pg

```

Deleting the Postgres database Helm chart does not delete the persistent volume (storage). To remove the storage permanently.

```
kubectl -n pg get pvc
kubectl -n pg delete pvc <pvc-name-from-above-command>

# Delete the namespace if you wish
kubectl delete namespace pg

```

### Delete the Kubernetes Cluster

To delete the entire Kubernetes cluster delete the microk8s installation from your PC, like so:

For microk8s, simply uninstall microk8s for the best cleanup. There are some other options to [reset the cluster](https://microk8s.io/docs/commands#heading--microk8s-reset) in case you don't want to completely remove it.


## Further Reading

* The todo Django Python code is derived from the tutorial at [https://learndjango.com/tutorials/django-rest-framework-tutorial-todo-api](https://learndjango.com/tutorials/django-rest-framework-tutorial-todo-api).


## Contributors

* Sachin Agarwal <sachin@bigbitbus.com>
* Simon Yan <simon@bigbitbus.com>

