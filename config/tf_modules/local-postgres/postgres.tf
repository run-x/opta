provider "helm" {
  kubernetes {
    config_path="~/.opta/kind/config"
  }
}

resource "helm_release" "opta-local-postgresql" {
  name       = "opta-local-postgres"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = "10.9.5"


  set {
    name  = "postgresqlUsername"
    value = "postgres"
  }
  set {
    name = "postgresqlPassword"
    value = "postgres"
  }
  set {
    name = "postgresqlDatabase"
    value = "appdb"
}
}



