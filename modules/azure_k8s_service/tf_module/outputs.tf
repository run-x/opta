output "docker_repo_url" {
  value = local.uppercase_image == "AUTO" ? "${var.acr_registry_name}.azurecr.io/${var.layer_name}/${var.module_name}" : ""
}

output "current_image" {
  value = local.image
}
