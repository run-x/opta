output "docker_repo_url" {
  value = var.image == "AUTO" ? "${data.google_container_registry_repository.root.repository_url}/${var.layer_name}/${var.module_name}" : ""
}