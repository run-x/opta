data "terraform_remote_state" "remote" {
  backend = var.backend_type

  config = var.config
}