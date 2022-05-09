```bash
# Create Docker Image
$> docker build . -t app:latest
# Run opta apply on primary region
$> opta apply -c ./opta_configs/env-primary.yaml

# Set the DNS Nameservers at required location.
# Set `delegated: true` in env-primary.yaml
# Run opta apply again on primary region
$> opta apply -c ./opta_configs/env-primary.yaml

# Run opta apply on primary region service file.
$> opta deploy -c ./opta_configs/multi-region-primary.yaml -i app:latest

# Get global database id
$> export global_database_id=$(opta output -c ./opta_configs/multi-region-primary.yaml | jq -r .global_database_id)

# Get Master DB's Username, Password and Database Name
$> export DB_USERNAME=$(opta show tf-state -c ./opta_configs/multi-region-primary.yaml | jq .resources | jq -c '.[] | select( .module == "module.db" and  .type == "aws_rds_cluster" and  .name == "db_cluster")' | jq .instances[0] | jq .attributes | jq -r .master_username)
$> export DB_NAME=$(opta show tf-state -c ./opta_configs/multi-region-primary.yaml | jq .resources | jq -c '.[] | select( .module == "module.db" and  .type == "aws_rds_cluster" and  .name == "db_cluster")' | jq .instances[0] | jq .attributes | jq -r .database_name)
$> export DB_PASSWORD=$(opta show tf-state -c ./opta_configs/multi-region-primary.yaml | jq .resources | jq -c '.[] | select( .module == "module.db" and  .type == "aws_rds_cluster" and  .name == "db_cluster")' | jq .instances[0] | jq .attributes | jq -r .master_password)
$> echo "db_db_name=$DB_NAME" >> ./opta_configs/secrets.env
$> echo "db_db_user=$DB_USERNAME" >> ./opta_configs/secrets.env
$> echo "db_db_password=$DB_PASSWORD" >> ./opta_configs/secrets.env

# Run opta apply on secondary region
$> opta apply -c ./opta_configs/env-secondary.yaml

# Set the DNS Nameservers at required location.
# Set `delegated: true` in env-secondary.yaml
# Run opta apply again on secondary region
$> opta apply -c ./opta_configs/env-secondary.yaml

# Set the Secret details retrieved from primary pod.
$> opta secret bulk-update -c ./opta_configs/multi-region-secondary.yaml secrets.env

$> opta deploy -c ./opta_configs/multi-region-secondary.yaml -i app:latest --var global_db_id=$global_database_id
# Run opta apply on secondary region service file.

# Testing Purposes
# Get the Load Balancer DNS Name using the below command.
# opta output -c ./opta_configs/env-primary.yaml | jq -r .load_balancer_raw_dns
# opta output -c ./opta_configs/env-secondary.yaml | jq -r .load_balancer_raw_dns
# Running the Django Post API would work only on the Primary Region, i.e. <load_balancer_from_primary_env>/crud/test_model
# Running the Django GET API would work only on both Primary and Secondary Regions, i.e. <load_balancer_from_primary_env>/crud/test_model and <load_balancer_from_secondary_env>/crud/test_model
```