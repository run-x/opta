output "docker_repo_url" {
  value = local.uppercase_image == "AUTO" ? "${var.local_registry_name}/${var.layer_name}/${var.module_name}" : ""
}

output "current_image" {
  value = local.image
}
