# What is this?

This example implements a movie search application with Atlas Search and deploys it using Opta. It is based on the [this blog post](https://www.mongodb.com/developer/how-to/build-movie-search-application/); but with some notable differences:

  1. Opta handles the creation of the Atlas database, passing its credentials into the application code

  2. Instead of Atlas Realm, this example uses a Flask API backend and deploys it on to a Kubernetes cluster; don't worry - you won't have to spin up the Kubernetes cluster yourself, Opta will do it for you in the cloud of your choice or even on your local machine!
   
Atlas is currently supported in Local and AWS Opta environments. Feel free to open a Github issue if you would like to see support in GCP or Azure.

Lets get started!

## Setup

Clone this repository and use the Opta files in the `opta` sub-directory as a starting point. You will need your AWS and Atlas API credentials for spinning up a Kubernetes cluster and API keys for the [MongoDB Atlas API](https://docs.atlas.mongodb.com/tutorial/manage-programmatic-access/). You do not need to configure the IP address in the API key, Opta will do that for you.

After you have downloaded these keys from the AWS console and Mongodb Atlas GUIs, set them as environment variables in the terminal shell where you plan to run Opta.

```bash
# Mongodb Atlas
export MONGODB_ATLAS_PUBLIC_KEY="abcdefghij"
export MONGODB_ATLAS_PRIVATE_KEY="1234015e-4503-4f95-f129-543d4e58bsdg"

# AWS 
export AWS_ACCESS_KEY_ID=AXSDFTRFFSDQAZA
export AWS_SECRET_ACCESS_KEY=ASdlksfja234sadfbjsdfgsdfg34SAD34fd
```

Next, we create the Opta environment with the AWS EKS Kubernetes cluster, as [documented here](https://docs.atlas.mongodb.com/tutorial/manage-programmatic-access/).

__Note: If you are only trying this out on your local machine, append the `--local` flag to all the opta commands so that a local Kubernetes cluster is spun up on your machine rather than the AWS EKS cluster. The Atlas Cluster will still be spun up as usual in the cloud__,


Once we have the Kubernetes cluster, we can create the MongoDB application by running opta apply on the `opta/atlasmongodbservice.yaml` file. Remember to set the  `mongodb_atlas_project_id` in this file before running Opta.

First, lets crate the docker image that contains our application code:

```bash
# in the examples directory cloned from Github (https://github.com/run-x/opta.git)
docker build -t mongodbapp:latest ./opta-mongodb-atlas-search
```
Next up, we use Opta to deploy the application's docker image into the Kubernetes cluster that Opta created already:

```bash
# For aws
opta deploy --image=mongodbapp:latest -c opta/examples/opta-mongodb-atlas-search/opta/atlasmongodbservice.yaml
# OR, For local
opta deploy --image=mongodbapp:latest --local -c opta/examples/opta-mongodb-atlas-search/opta/atlasmongodbservice.yaml

```

After a few minutes, the application will be running against the new MongoDB Atlas  cluster.

Before you can use the application, follow [steps 1 and 2](https://www.mongodb.com/developer/how-to/build-movie-search-application/#step-1.-spin-up-atlas-cluster-and-load-movie-data) in the original Mongodb tutorial in order to load the sample data and setup the search index in the Mongodb Atlas database. After you have created the Mongodb Atlas search index, wait for a few minutes before going to the next step as the index is built in Mongodb Atlas.

Once you are done, point your browser to the ELB load balancer (or http://localhost:8080/ in case you are using Opta Local) and search the movie database!

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
