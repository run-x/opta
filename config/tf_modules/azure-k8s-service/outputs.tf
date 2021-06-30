output "docker_repo_url" {
  value = var.image == "AUTO" ? "${var.acr_registry_name}.azurecr.io/${var.layer_name}/${var.module_name}" : ""
}
