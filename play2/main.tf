provider "google" {
  project = "runxc-test"
  region = "us-central1"
  zone = "us-central1-a"
}

data "terraform_remote_state" "init" {
  backend = "local"

  config = {
    path = "../play/terraform.tfstate"
  }
}

data "google_client_config" "provider" {}

provider "kubernetes" {
  load_config_file = false

  host  = "https://${data.terraform_remote_state.init.outputs.k8s-cluster.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    data.terraform_remote_state.init.outputs.k8s-cluster.master_auth[0].cluster_ca_certificate,
  )
}

module "k8s-service" {
  source = "../k8s-service"
  name = "github-app"
  target_port = 5000
  image = "gcr.io/runxc-test/github-app:latest"
  env_vars = [
    { 
      name = "PG_HOST"
      value = module.gcp-postgres.db_host 
    },
    { 
      name = "PG_USER"
      value = module.gcp-postgres.db_user 
    },
    { 
      name = "PG_PASSWORD"
      value = module.gcp-postgres.db_password 
    },
    { 
      name = "PG_NAME"
      value = module.gcp-postgres.db_name 
    }
  ]
  depends_on = [module.gcp-postgres]
}

module "gcp-postgres" {
  source = "../gcp-postgres"
  name = "github-app"
  tier = "db-f1-micro"
  gcp-network = data.terraform_remote_state.init.outputs.gcp-network
}
