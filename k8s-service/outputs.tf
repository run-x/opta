output "docker_repo_url" {
  value = var.image == null ? aws_ecr_repository.repo[0].repository_url : ""
}