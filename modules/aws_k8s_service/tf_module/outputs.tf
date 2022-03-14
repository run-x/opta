locals {
  get_ecr_repo_url = length(aws_ecr_repository.repo) == 0 ? (
    "Couldn't get the repository URL since no ECR repos were found."
  ) : aws_ecr_repository.repo[0].repository_url
}

output "docker_repo_url" {
  value = local.uppercase_image == "AUTO" ? local.get_ecr_repo_url : ""
}

output "current_image" {
  value = local.image
}