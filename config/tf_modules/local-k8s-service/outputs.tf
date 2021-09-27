output "docker_repo_url" {
  value = var.image == "AUTO" ? "${var.local_registry_name}/${var.layer_name}/${var.module_name}" : ""
}
