# Description

This `opta.yaml` sets up airflow on AWS or GCP.

It uses the airflow helm chart and uses underlying cloud resources for data storage:
- RDS and Elasticcache for AWS
- Cloud SQL and Memorystore for GCP

To use it, just run `opta apply --config <file-name> --env <env-name>`.

Make sure the environment is set up first.
Detailed documentation: https://docs.opta.dev/