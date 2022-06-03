output "docker_repo_url" {
  value = local.uppercase_image == "AUTO" ? "${var.local_registry_name}/${var.layer_name}/${var.module_name}" : ""
}

output "current_image" {
  value = split("@", split(":", local.image)[0])[0]
}

output "current_tag" {
  value = length(regexall("[:]", local.image)) > 0 ? split(":", local.image)[1] : ""
}

output "current_digest" {
  value = length(regexall("[@]", local.image)) > 0 ? split("@", local.image)[1] : ""
}